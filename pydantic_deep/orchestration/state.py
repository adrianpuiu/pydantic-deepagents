"""Workflow state management for the orchestration system.

This module provides utilities for managing workflow execution state,
including state transitions, task tracking, and result aggregation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic_deep.orchestration.models import (
    TaskDefinition,
    TaskResult,
    TaskStatus,
    WorkflowDefinition,
    WorkflowState,
)


class StateManager:
    """Manages workflow execution state and transitions."""

    def __init__(self, workflow: WorkflowDefinition) -> None:
        """Initialize state manager for a workflow.

        Args:
            workflow: The workflow definition to manage state for.
        """
        self.workflow = workflow
        self.state = WorkflowState(
            workflow_id=workflow.id,
            status="pending",
            pending_tasks=[task.id for task in workflow.tasks],
        )

    def start_workflow(self) -> None:
        """Mark workflow as started."""
        self.state.status = "running"
        self.state.started_at = datetime.now(timezone.utc)

    def complete_workflow(self) -> None:
        """Mark workflow as completed."""
        self.state.status = "completed"
        self.state.completed_at = datetime.now(timezone.utc)

    def fail_workflow(self, error: str) -> None:
        """Mark workflow as failed.

        Args:
            error: Error message describing the failure.
        """
        self.state.status = "failed"
        self.state.error = error
        self.state.completed_at = datetime.now(timezone.utc)

    def get_ready_tasks(self) -> list[TaskDefinition]:
        """Get all tasks that are ready to execute.

        A task is ready if:
        - It's in the pending list
        - All its dependencies are completed
        - It's not currently running

        Returns:
            List of ready task definitions.
        """
        ready_tasks = []
        for task in self.workflow.tasks:
            if task.id in self.state.pending_tasks and self.state.is_task_ready(task):
                # Check condition if present
                if task.condition:
                    if not self._evaluate_condition(task.condition):
                        # Skip task if condition not met
                        self.skip_task(task.id, "Condition not met")
                        continue
                ready_tasks.append(task)
        return ready_tasks

    def start_task(self, task_id: str) -> None:
        """Mark a task as started.

        Args:
            task_id: ID of the task to start.
        """
        if task_id in self.state.pending_tasks:
            self.state.pending_tasks.remove(task_id)
        if task_id not in self.state.current_tasks:
            self.state.current_tasks.append(task_id)

        # Initialize task result
        if task_id not in self.state.task_results:
            self.state.task_results[task_id] = TaskResult(
                task_id=task_id,
                status=TaskStatus.RUNNING,
                started_at=datetime.now(timezone.utc),
            )
        else:
            # Update existing result (e.g., for retries)
            self.state.task_results[task_id].status = TaskStatus.RUNNING
            self.state.task_results[task_id].started_at = datetime.now(timezone.utc)

    def complete_task(self, task_id: str, output: Any, agent_used: str | None = None) -> None:
        """Mark a task as completed.

        Args:
            task_id: ID of the completed task.
            output: Task output/result.
            agent_used: Agent type that executed the task.
        """
        if task_id in self.state.current_tasks:
            self.state.current_tasks.remove(task_id)
        if task_id not in self.state.completed_tasks:
            self.state.completed_tasks.append(task_id)

        # Update result
        result = self.state.task_results.get(task_id)
        if result:
            result.status = TaskStatus.COMPLETED
            result.output = output
            result.agent_used = agent_used
            result.completed_at = datetime.now(timezone.utc)
            if result.started_at:
                result.duration_seconds = (result.completed_at - result.started_at).total_seconds()

    def fail_task(self, task_id: str, error: str) -> None:
        """Mark a task as failed.

        Args:
            task_id: ID of the failed task.
            error: Error message.
        """
        if task_id in self.state.current_tasks:
            self.state.current_tasks.remove(task_id)
        if task_id not in self.state.failed_tasks:
            self.state.failed_tasks.append(task_id)

        # Update result
        result = self.state.task_results.get(task_id)
        if result:
            result.status = TaskStatus.FAILED
            result.error = error
            result.completed_at = datetime.now(timezone.utc)
            if result.started_at:
                result.duration_seconds = (result.completed_at - result.started_at).total_seconds()

    def retry_task(self, task_id: str) -> None:
        """Mark a task for retry.

        Args:
            task_id: ID of the task to retry.
        """
        if task_id in self.state.failed_tasks:
            self.state.failed_tasks.remove(task_id)
        if task_id not in self.state.pending_tasks:
            self.state.pending_tasks.append(task_id)

        # Update result
        result = self.state.task_results.get(task_id)
        if result:
            result.status = TaskStatus.RETRYING
            result.retry_count += 1

    def skip_task(self, task_id: str, reason: str) -> None:
        """Mark a task as skipped.

        Args:
            task_id: ID of the task to skip.
            reason: Reason for skipping.
        """
        if task_id in self.state.pending_tasks:
            self.state.pending_tasks.remove(task_id)

        # Create or update result
        if task_id not in self.state.task_results:
            self.state.task_results[task_id] = TaskResult(
                task_id=task_id,
                status=TaskStatus.SKIPPED,
                error=reason,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )
        else:
            result = self.state.task_results[task_id]
            result.status = TaskStatus.SKIPPED
            result.error = reason

    def is_workflow_complete(self) -> bool:
        """Check if workflow execution is complete.

        Returns:
            True if workflow is complete (all tasks done or failed).
        """
        return (
            len(self.state.pending_tasks) == 0
            and len(self.state.current_tasks) == 0
        )

    def has_failed_tasks(self) -> bool:
        """Check if any tasks have failed.

        Returns:
            True if any tasks have failed.
        """
        return len(self.state.failed_tasks) > 0

    def get_progress(self) -> dict[str, Any]:
        """Get workflow progress information.

        Returns:
            Dictionary with progress statistics.
        """
        total_tasks = len(self.workflow.tasks)
        completed = len(self.state.completed_tasks)
        failed = len(self.state.failed_tasks)
        running = len(self.state.current_tasks)
        pending = len(self.state.pending_tasks)

        return {
            "total_tasks": total_tasks,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending,
            "progress_percent": (completed / total_tasks * 100) if total_tasks > 0 else 0,
            "status": self.state.status,
        }

    def get_task_by_id(self, task_id: str) -> TaskDefinition | None:
        """Get task definition by ID.

        Args:
            task_id: ID of the task to retrieve.

        Returns:
            Task definition or None if not found.
        """
        for task in self.workflow.tasks:
            if task.id == task_id:
                return task
        return None

    def _evaluate_condition(self, condition: str) -> bool:
        """Evaluate a task condition expression.

        Args:
            condition: Condition expression to evaluate.

        Returns:
            True if condition is met, False otherwise.

        Note:
            This is a simple implementation that checks if referenced
            task IDs are completed. More complex condition evaluation
            could be added in the future.
        """
        # Simple condition evaluation: check if task ID mentioned is completed
        # Format: "task_id == 'completed'" or "task_id.output.success"
        for task_id in self.state.completed_tasks:
            if task_id in condition:
                return True
        return False

    def get_dependency_chain(self, task_id: str) -> list[str]:
        """Get the complete dependency chain for a task.

        Args:
            task_id: ID of the task.

        Returns:
            List of task IDs in dependency order (dependencies first).
        """
        task = self.get_task_by_id(task_id)
        if not task:
            return []

        chain = []
        visited = set()

        def _traverse(tid: str) -> None:
            if tid in visited:
                return
            visited.add(tid)

            t = self.get_task_by_id(tid)
            if t:
                for dep_id in t.depends_on:
                    _traverse(dep_id)
                chain.append(tid)

        _traverse(task_id)
        return chain

    def build_dependency_graph(self) -> dict[str, list[str]]:
        """Build a dependency graph for all tasks.

        Returns:
            Dictionary mapping task IDs to their dependencies.
        """
        graph: dict[str, list[str]] = {}
        for task in self.workflow.tasks:
            graph[task.id] = task.depends_on.copy()
        return graph

    def topological_sort(self) -> list[str]:
        """Perform topological sort on workflow tasks.

        Returns:
            List of task IDs in topological order.

        Raises:
            ValueError: If circular dependency detected.
        """
        graph = self.build_dependency_graph()
        in_degree = {task.id: 0 for task in self.workflow.tasks}

        # Calculate in-degrees
        for task_id, deps in graph.items():
            for dep in deps:
                in_degree[dep] = in_degree.get(dep, 0)
            for dep in deps:
                in_degree[task_id] += 1

        # Find all nodes with no incoming edges
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            task_id = queue.pop(0)
            result.append(task_id)

            # Remove edges from this node
            for other_id, deps in graph.items():
                if task_id in deps:
                    in_degree[other_id] -= 1
                    if in_degree[other_id] == 0:
                        queue.append(other_id)

        if len(result) != len(self.workflow.tasks):
            raise ValueError("Circular dependency detected in workflow")

        return result
