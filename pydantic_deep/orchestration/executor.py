"""Task execution strategies for the orchestration system.

This module provides different strategies for executing workflow tasks,
including sequential, parallel, and DAG-based execution.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Callable

from pydantic_deep.orchestration.models import (
    ExecutionStrategy,
    TaskDefinition,
    TaskResult,
    TaskStatus,
)
from pydantic_deep.orchestration.state import StateManager

if TYPE_CHECKING:
    from pydantic_deep.orchestration.coordinator import TaskExecutor


class SequentialExecutor:
    """Executes tasks sequentially in order."""

    def __init__(self, state_manager: StateManager, task_executor: TaskExecutor) -> None:
        """Initialize sequential executor.

        Args:
            state_manager: Workflow state manager.
            task_executor: Function to execute individual tasks.
        """
        self.state_manager = state_manager
        self.task_executor = task_executor

    async def execute(self) -> dict[str, TaskResult]:
        """Execute all tasks sequentially.

        Returns:
            Dictionary mapping task IDs to their results.
        """
        workflow = self.state_manager.workflow

        for task in workflow.tasks:
            # Check if we should stop on failure
            if (
                not workflow.continue_on_failure
                and self.state_manager.has_failed_tasks()
            ):
                # Skip remaining tasks
                self.state_manager.skip_task(task.id, "Previous task failed")
                continue

            # Execute task
            await self.task_executor(task)

        return self.state_manager.state.task_results


class ParallelExecutor:
    """Executes independent tasks in parallel."""

    def __init__(
        self,
        state_manager: StateManager,
        task_executor: TaskExecutor,
        max_parallel: int = 5,
    ) -> None:
        """Initialize parallel executor.

        Args:
            state_manager: Workflow state manager.
            task_executor: Function to execute individual tasks.
            max_parallel: Maximum number of tasks to run concurrently.
        """
        self.state_manager = state_manager
        self.task_executor = task_executor
        self.max_parallel = max_parallel

    async def execute(self) -> dict[str, TaskResult]:
        """Execute tasks in parallel with concurrency limit.

        Returns:
            Dictionary mapping task IDs to their results.
        """
        workflow = self.state_manager.workflow
        semaphore = asyncio.Semaphore(self.max_parallel)

        async def execute_with_semaphore(task: TaskDefinition) -> None:
            async with semaphore:
                await self.task_executor(task)

        # Create all tasks and execute with semaphore
        tasks = [execute_with_semaphore(task) for task in workflow.tasks]
        await asyncio.gather(*tasks, return_exceptions=True)

        return self.state_manager.state.task_results


class DAGExecutor:
    """Executes tasks based on dependency graph (DAG)."""

    def __init__(
        self,
        state_manager: StateManager,
        task_executor: TaskExecutor,
        max_parallel: int = 5,
    ) -> None:
        """Initialize DAG executor.

        Args:
            state_manager: Workflow state manager.
            task_executor: Function to execute individual tasks.
            max_parallel: Maximum number of tasks to run concurrently.
        """
        self.state_manager = state_manager
        self.task_executor = task_executor
        self.max_parallel = max_parallel

    async def execute(self) -> dict[str, TaskResult]:
        """Execute tasks respecting dependencies with parallel execution.

        This executor:
        1. Identifies tasks with no pending dependencies
        2. Executes them in parallel (up to max_parallel)
        3. As tasks complete, identifies newly ready tasks
        4. Continues until all tasks are complete or failed

        Returns:
            Dictionary mapping task IDs to their results.
        """
        workflow = self.state_manager.workflow

        # Validate no circular dependencies
        try:
            self.state_manager.topological_sort()
        except ValueError as e:
            # Mark all tasks as failed
            for task in workflow.tasks:
                self.state_manager.fail_task(task.id, str(e))
            return self.state_manager.state.task_results

        # Execute tasks as they become ready
        active_tasks: set[asyncio.Task[None]] = set()

        while not self.state_manager.is_workflow_complete():
            # Get ready tasks
            ready_tasks = self.state_manager.get_ready_tasks()

            # Check if we should continue
            if (
                not workflow.continue_on_failure
                and self.state_manager.has_failed_tasks()
            ):
                # Mark all pending tasks as skipped
                for task in ready_tasks:
                    self.state_manager.skip_task(task.id, "Previous task failed")
                # Wait for active tasks to complete
                if active_tasks:
                    await asyncio.wait(active_tasks)
                break

            # Launch ready tasks up to max_parallel limit
            while ready_tasks and len(active_tasks) < self.max_parallel:
                task = ready_tasks.pop(0)
                task_coroutine = self._execute_task_wrapper(task)
                active_task = asyncio.create_task(task_coroutine)
                active_tasks.add(active_task)

            # Wait for at least one task to complete if we have active tasks
            if active_tasks:
                done, active_tasks = await asyncio.wait(
                    active_tasks, return_when=asyncio.FIRST_COMPLETED
                )
                # Process completed tasks (errors already handled in wrapper)
                for task_future in done:
                    try:
                        await task_future
                    except Exception:
                        # Already handled in wrapper
                        pass
            elif not ready_tasks:
                # No ready tasks and no active tasks - break to avoid infinite loop
                break

        return self.state_manager.state.task_results

    async def _execute_task_wrapper(self, task: TaskDefinition) -> None:
        """Wrapper to execute task and handle exceptions.

        Args:
            task: Task to execute.
        """
        try:
            await self.task_executor(task)
        except Exception as e:
            # Ensure task is marked as failed even if executor doesn't handle it
            if self.state_manager.state.get_task_status(task.id) == TaskStatus.RUNNING:
                self.state_manager.fail_task(task.id, str(e))


class ConditionalExecutor:
    """Executes tasks based on conditions and previous results."""

    def __init__(self, state_manager: StateManager, task_executor: TaskExecutor) -> None:
        """Initialize conditional executor.

        Args:
            state_manager: Workflow state manager.
            task_executor: Function to execute individual tasks.
        """
        self.state_manager = state_manager
        self.task_executor = task_executor

    async def execute(self) -> dict[str, TaskResult]:
        """Execute tasks conditionally based on previous results.

        Returns:
            Dictionary mapping task IDs to their results.
        """
        workflow = self.state_manager.workflow

        for task in workflow.tasks:
            # Check dependencies
            if not self.state_manager.state.is_task_ready(task):
                self.state_manager.skip_task(task.id, "Dependencies not satisfied")
                continue

            # Check condition if present
            if task.condition:
                if not self._evaluate_condition(task.condition):
                    self.state_manager.skip_task(task.id, "Condition not met")
                    continue

            # Check if we should stop on failure
            if (
                not workflow.continue_on_failure
                and self.state_manager.has_failed_tasks()
            ):
                self.state_manager.skip_task(task.id, "Previous task failed")
                continue

            # Execute task
            await self.task_executor(task)

        return self.state_manager.state.task_results

    def _evaluate_condition(self, condition: str) -> bool:
        """Evaluate a task condition.

        Args:
            condition: Condition expression.

        Returns:
            True if condition is met.
        """
        # This could be enhanced with a proper expression evaluator
        # For now, use simple state manager evaluation
        return self.state_manager._evaluate_condition(condition)


class ExecutorFactory:
    """Factory for creating task executors."""

    @staticmethod
    def create_executor(
        strategy: ExecutionStrategy,
        state_manager: StateManager,
        task_executor: TaskExecutor,
        max_parallel: int = 5,
    ) -> (
        SequentialExecutor
        | ParallelExecutor
        | DAGExecutor
        | ConditionalExecutor
    ):
        """Create an executor based on strategy.

        Args:
            strategy: Execution strategy to use.
            state_manager: Workflow state manager.
            task_executor: Function to execute individual tasks.
            max_parallel: Maximum parallel tasks for parallel/DAG executors.

        Returns:
            Appropriate executor instance.

        Raises:
            ValueError: If strategy is unknown.
        """
        if strategy == ExecutionStrategy.SEQUENTIAL:
            return SequentialExecutor(state_manager, task_executor)
        elif strategy == ExecutionStrategy.PARALLEL:
            return ParallelExecutor(state_manager, task_executor, max_parallel)
        elif strategy == ExecutionStrategy.DAG:
            return DAGExecutor(state_manager, task_executor, max_parallel)
        elif strategy == ExecutionStrategy.CONDITIONAL:
            return ConditionalExecutor(state_manager, task_executor)
        else:
            raise ValueError(f"Unknown execution strategy: {strategy}")
