"""Main orchestration coordinator.

This module provides the central TaskOrchestrator class that coordinates
workflow execution, task routing, and error handling.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Protocol

from pydantic_ai import Agent

from pydantic_deep.deps import DeepAgentDeps
from pydantic_deep.orchestration.executor import ExecutorFactory
from pydantic_deep.orchestration.models import (
    OrchestrationConfig,
    RetryConfig,
    TaskDefinition,
    TaskResult,
    TaskStatus,
    WorkflowDefinition,
    WorkflowState,
)
from pydantic_deep.orchestration.routing import TaskRouter, create_default_routing
from pydantic_deep.orchestration.state import StateManager
from pydantic_deep.orchestration.strategy_selector import (
    auto_select_strategy,
    explain_strategy_choice,
)


class TaskExecutor(Protocol):
    """Protocol for task executor function."""

    async def __call__(self, task: TaskDefinition) -> TaskResult:
        """Execute a task.

        Args:
            task: Task to execute.

        Returns:
            Task execution result.
        """
        ...


class TaskOrchestrator:
    """Main orchestrator for managing workflow execution."""

    def __init__(
        self,
        agent: Agent[DeepAgentDeps, str],
        deps: DeepAgentDeps,
        config: OrchestrationConfig | None = None,
    ) -> None:
        """Initialize task orchestrator.

        Args:
            agent: The main pydantic-ai agent to use for task execution.
            deps: Agent dependencies.
            config: Orchestration configuration. If None, uses default config.
        """
        self.agent = agent
        self.deps = deps

        # Initialize config with defaults if not provided
        if config is None:
            config = OrchestrationConfig(agent_routing=create_default_routing())
        self.config = config

        # Initialize router
        self.router = TaskRouter(config)

        # Track active workflows
        self.workflows: dict[str, StateManager] = {}

    async def execute_workflow(
        self,
        workflow: WorkflowDefinition,
        progress_callback: Callable[[WorkflowState], None] | None = None,
        auto_strategy: bool = False,
    ) -> WorkflowState:
        """Execute a complete workflow.

        Args:
            workflow: Workflow definition to execute.
            progress_callback: Optional callback for progress updates.
            auto_strategy: If True, automatically select optimal execution strategy
                based on workflow characteristics. Default is False (use explicit strategy).

        Returns:
            Final workflow state with all task results.
        """
        # Create state manager
        state_manager = StateManager(workflow)
        self.workflows[workflow.id] = state_manager

        # Select execution strategy
        if auto_strategy:
            selected_strategy = auto_select_strategy(workflow)
        else:
            selected_strategy = workflow.execution_strategy

        # Start workflow
        state_manager.start_workflow()

        try:
            # Create executor based on strategy
            executor = ExecutorFactory.create_executor(
                selected_strategy,
                state_manager,
                self._create_task_executor(state_manager, progress_callback),
                workflow.max_parallel_tasks,
            )

            # Execute workflow with timeout if specified
            if workflow.default_timeout_seconds:
                await asyncio.wait_for(
                    executor.execute(),
                    timeout=workflow.default_timeout_seconds,
                )
            else:
                await executor.execute()

            # Complete workflow
            if state_manager.has_failed_tasks() and not workflow.continue_on_failure:
                state_manager.fail_workflow("One or more tasks failed")
            else:
                state_manager.complete_workflow()

        except asyncio.TimeoutError:
            state_manager.fail_workflow("Workflow execution timed out")
        except Exception as e:
            state_manager.fail_workflow(f"Workflow execution error: {e}")

        # Final progress callback
        if progress_callback:
            progress_callback(state_manager.state)

        return state_manager.state

    def _create_task_executor(
        self,
        state_manager: StateManager,
        progress_callback: Callable[[WorkflowState], None] | None,
    ) -> TaskExecutor:
        """Create task executor function.

        Args:
            state_manager: State manager for the workflow.
            progress_callback: Optional callback for progress updates.

        Returns:
            Task executor function.
        """

        async def execute_task(task: TaskDefinition) -> TaskResult:
            """Execute a single task with retry logic.

            Args:
                task: Task to execute.

            Returns:
                Task execution result.
            """
            # Route task to appropriate agent
            agent_type = self.router.route_task(task)
            self.router.increment_agent_load(agent_type)

            # Start task
            state_manager.start_task(task.id)
            if progress_callback:
                progress_callback(state_manager.state)

            retry_count = 0
            max_retries = task.retry_config.max_retries
            delay = task.retry_config.initial_delay

            while retry_count <= max_retries:
                try:
                    # Execute task
                    result = await self._execute_single_task(task, agent_type, state_manager)

                    # Complete task
                    state_manager.complete_task(task.id, result, agent_type)
                    self.router.decrement_agent_load(agent_type)

                    if progress_callback:
                        progress_callback(state_manager.state)

                    return state_manager.state.task_results[task.id]

                except Exception as e:
                    error_msg = str(e)

                    # Check if we should retry
                    if retry_count < max_retries:
                        retry_count += 1
                        state_manager.retry_task(task.id)

                        if progress_callback:
                            progress_callback(state_manager.state)

                        # Exponential backoff
                        await asyncio.sleep(delay)
                        delay = min(
                            delay * task.retry_config.backoff_multiplier,
                            task.retry_config.max_delay,
                        )
                    else:
                        # Max retries exceeded
                        state_manager.fail_task(task.id, error_msg)
                        self.router.decrement_agent_load(agent_type)

                        if progress_callback:
                            progress_callback(state_manager.state)

                        return state_manager.state.task_results[task.id]

            # Should not reach here
            state_manager.fail_task(task.id, "Unexpected error in retry logic")
            self.router.decrement_agent_load(agent_type)
            return state_manager.state.task_results[task.id]

        return execute_task

    async def _execute_single_task(
        self,
        task: TaskDefinition,
        agent_type: str,
        state_manager: StateManager,
    ) -> Any:
        """Execute a single task using appropriate agent.

        Args:
            task: Task to execute.
            agent_type: Agent type to use.
            state_manager: State manager for accessing previous results.

        Returns:
            Task output.

        Raises:
            Exception: If task execution fails.
        """
        # Build task prompt with context
        prompt = self._build_task_prompt(task, state_manager)

        # Clone deps for isolation (subagents get clean state)
        task_deps = self.deps.clone_for_subagent()

        # Execute using subagent if not general-purpose
        if agent_type != "general-purpose" and agent_type in self.deps.subagents:
            # Use existing subagent
            subagent = self.deps.subagents[agent_type]
            result = await subagent.run(prompt, deps=task_deps)
            return result.data
        else:
            # Use main agent
            result = await self.agent.run(prompt, deps=task_deps)
            return result.data

    def _build_task_prompt(
        self,
        task: TaskDefinition,
        state_manager: StateManager,
    ) -> str:
        """Build prompt for task execution.

        Args:
            task: Task definition.
            state_manager: State manager for accessing previous results.

        Returns:
            Complete prompt for task execution.
        """
        parts = [f"Task: {task.description}"]

        # Add task parameters if present
        if task.parameters:
            parts.append("\nParameters:")
            for key, value in task.parameters.items():
                parts.append(f"- {key}: {value}")

        # Add context from dependencies
        if task.depends_on:
            parts.append("\nContext from previous tasks:")
            for dep_id in task.depends_on:
                dep_result = state_manager.state.task_results.get(dep_id)
                if dep_result and dep_result.status == TaskStatus.COMPLETED:
                    parts.append(f"\n{dep_id}:")
                    parts.append(f"  Output: {dep_result.output}")

        # Add expected output format if specified
        if task.expected_output_type:
            parts.append(f"\nExpected output format: {task.expected_output_type}")

        return "\n".join(parts)

    async def execute_task(
        self,
        task: TaskDefinition,
        workflow_id: str = "adhoc",
    ) -> TaskResult:
        """Execute a single task outside of a workflow.

        Args:
            task: Task to execute.
            workflow_id: Optional workflow ID for tracking.

        Returns:
            Task execution result.
        """
        # Create minimal workflow
        workflow = WorkflowDefinition(
            id=workflow_id,
            name="Ad-hoc Task",
            tasks=[task],
        )

        # Execute workflow
        state = await self.execute_workflow(workflow)

        # Return task result
        return state.task_results[task.id]

    def get_workflow_state(self, workflow_id: str) -> WorkflowState | None:
        """Get current state of a workflow.

        Args:
            workflow_id: ID of the workflow.

        Returns:
            Workflow state or None if not found.
        """
        state_manager = self.workflows.get(workflow_id)
        if state_manager:
            return state_manager.state
        return None

    def get_workflow_progress(self, workflow_id: str) -> dict[str, Any] | None:
        """Get progress information for a workflow.

        Args:
            workflow_id: ID of the workflow.

        Returns:
            Progress information or None if not found.
        """
        state_manager = self.workflows.get(workflow_id)
        if state_manager:
            return state_manager.get_progress()
        return None

    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow.

        Args:
            workflow_id: ID of the workflow to cancel.

        Returns:
            True if workflow was cancelled, False if not found or already complete.
        """
        state_manager = self.workflows.get(workflow_id)
        if state_manager and state_manager.state.status == "running":
            state_manager.fail_workflow("Workflow cancelled by user")
            return True
        return False


def create_orchestrator(
    agent: Agent[DeepAgentDeps, str],
    deps: DeepAgentDeps,
    config: OrchestrationConfig | None = None,
) -> TaskOrchestrator:
    """Create a task orchestrator instance.

    Args:
        agent: The main pydantic-ai agent.
        deps: Agent dependencies.
        config: Optional orchestration configuration.

    Returns:
        Configured TaskOrchestrator instance.
    """
    return TaskOrchestrator(agent, deps, config)
