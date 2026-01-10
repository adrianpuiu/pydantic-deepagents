"""Metrics collection and analysis for orchestration workflows.

This module provides comprehensive metrics tracking for workflow and task execution,
including performance, cost, and resource utilization metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from pydantic_deep.orchestration.models import TaskResult, TaskStatus, WorkflowState


@dataclass
class TaskMetrics:
    """Metrics for a single task execution."""

    task_id: str
    status: TaskStatus
    duration_seconds: float
    started_at: datetime
    completed_at: datetime
    retry_count: int = 0
    agent_used: str | None = None
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        """Check if task succeeded."""
        return self.status == TaskStatus.COMPLETED

    @property
    def failed(self) -> bool:
        """Check if task failed."""
        return self.status == TaskStatus.FAILED


@dataclass
class WorkflowMetrics:
    """Comprehensive metrics for workflow execution."""

    workflow_id: str
    workflow_name: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None

    # Task metrics
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    skipped_tasks: int = 0
    total_retries: int = 0

    # Timing metrics
    total_duration_seconds: float = 0.0
    task_metrics: list[TaskMetrics] = field(default_factory=list)

    # Performance metrics
    slowest_task: TaskMetrics | None = None
    fastest_task: TaskMetrics | None = None
    average_task_duration: float = 0.0
    critical_path_duration: float = 0.0

    # Success metrics
    success_rate: float = 0.0
    retry_rate: float = 0.0

    @classmethod
    def from_workflow_state(cls, state: WorkflowState, workflow_name: str = "") -> WorkflowMetrics:
        """Create metrics from workflow state.

        Args:
            state: Workflow execution state.
            workflow_name: Optional workflow name.

        Returns:
            Workflow metrics instance.
        """
        metrics = cls(
            workflow_id=state.workflow_id,
            workflow_name=workflow_name,
            status=state.status,
            started_at=state.started_at or datetime.now(),
            completed_at=state.completed_at,
        )

        # Convert task results to metrics
        task_metrics_list = []
        for task_result in state.task_results.values():
            if task_result.started_at and task_result.completed_at:
                task_metrics = TaskMetrics(
                    task_id=task_result.task_id,
                    status=task_result.status,
                    duration_seconds=task_result.duration_seconds or 0.0,
                    started_at=task_result.started_at,
                    completed_at=task_result.completed_at,
                    retry_count=task_result.retry_count,
                    agent_used=task_result.agent_used,
                    error=task_result.error,
                )
                task_metrics_list.append(task_metrics)

        metrics.task_metrics = task_metrics_list

        # Calculate aggregate metrics
        metrics._calculate_metrics()

        return metrics

    def _calculate_metrics(self) -> None:
        """Calculate aggregate metrics from task metrics."""
        if not self.task_metrics:
            return

        # Count tasks by status
        self.total_tasks = len(self.task_metrics)
        self.completed_tasks = sum(1 for t in self.task_metrics if t.succeeded)
        self.failed_tasks = sum(1 for t in self.task_metrics if t.failed)
        self.skipped_tasks = sum(1 for t in self.task_metrics if t.status == TaskStatus.SKIPPED)
        self.total_retries = sum(t.retry_count for t in self.task_metrics)

        # Calculate timing metrics
        if self.started_at and self.completed_at:
            self.total_duration_seconds = (self.completed_at - self.started_at).total_seconds()

        completed_tasks = [t for t in self.task_metrics if t.succeeded]
        if completed_tasks:
            # Find slowest and fastest
            self.slowest_task = max(completed_tasks, key=lambda t: t.duration_seconds)
            self.fastest_task = min(completed_tasks, key=lambda t: t.duration_seconds)

            # Calculate average
            total_duration = sum(t.duration_seconds for t in completed_tasks)
            self.average_task_duration = total_duration / len(completed_tasks)

        # Calculate success metrics
        if self.total_tasks > 0:
            self.success_rate = self.completed_tasks / self.total_tasks * 100
            self.retry_rate = self.total_retries / self.total_tasks

    def get_bottleneck(self) -> TaskMetrics | None:
        """Get the task that is the biggest bottleneck (slowest).

        Returns:
            Slowest task metrics or None.
        """
        return self.slowest_task

    def get_task_metrics(self, task_id: str) -> TaskMetrics | None:
        """Get metrics for a specific task.

        Args:
            task_id: ID of the task.

        Returns:
            Task metrics or None if not found.
        """
        for metrics in self.task_metrics:
            if metrics.task_id == task_id:
                return metrics
        return None

    def get_failed_tasks(self) -> list[TaskMetrics]:
        """Get metrics for all failed tasks.

        Returns:
            List of failed task metrics.
        """
        return [t for t in self.task_metrics if t.failed]

    def get_summary(self) -> dict[str, Any]:
        """Get summary of workflow metrics.

        Returns:
            Dictionary with key metrics.
        """
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "status": self.status,
            "total_duration_seconds": self.total_duration_seconds,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "skipped_tasks": self.skipped_tasks,
            "success_rate": f"{self.success_rate:.1f}%",
            "average_task_duration": f"{self.average_task_duration:.2f}s",
            "slowest_task": {
                "task_id": self.slowest_task.task_id,
                "duration": f"{self.slowest_task.duration_seconds:.2f}s",
            }
            if self.slowest_task
            else None,
            "total_retries": self.total_retries,
            "retry_rate": f"{self.retry_rate:.2f}",
        }

    def get_performance_report(self) -> str:
        """Generate human-readable performance report.

        Returns:
            Formatted performance report.
        """
        lines = [
            f"Workflow Performance Report: {self.workflow_name or self.workflow_id}",
            "=" * 70,
            f"Status: {self.status}",
            f"Total Duration: {self.total_duration_seconds:.2f}s",
            "",
            "Task Summary:",
            f"  Total Tasks: {self.total_tasks}",
            f"  Completed: {self.completed_tasks} ({self.success_rate:.1f}%)",
            f"  Failed: {self.failed_tasks}",
            f"  Skipped: {self.skipped_tasks}",
            f"  Total Retries: {self.total_retries} (avg {self.retry_rate:.2f} per task)",
            "",
            "Performance:",
            f"  Average Task Duration: {self.average_task_duration:.2f}s",
        ]

        if self.slowest_task:
            lines.extend(
                [
                    f"  Slowest Task: {self.slowest_task.task_id} ({self.slowest_task.duration_seconds:.2f}s)",
                ]
            )

        if self.fastest_task:
            lines.extend(
                [
                    f"  Fastest Task: {self.fastest_task.task_id} ({self.fastest_task.duration_seconds:.2f}s)",
                ]
            )

        # Add failed tasks section if any
        failed = self.get_failed_tasks()
        if failed:
            lines.extend(["", "Failed Tasks:"])
            for task in failed:
                lines.append(f"  - {task.task_id}: {task.error}")

        return "\n".join(lines)


class MetricsCollector:
    """Collects and stores metrics for multiple workflow executions."""

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self.workflow_metrics: dict[str, WorkflowMetrics] = {}

    def record_workflow(self, state: WorkflowState, workflow_name: str = "") -> WorkflowMetrics:
        """Record metrics for a workflow execution.

        Args:
            state: Workflow execution state.
            workflow_name: Optional workflow name.

        Returns:
            Workflow metrics.
        """
        metrics = WorkflowMetrics.from_workflow_state(state, workflow_name)
        self.workflow_metrics[state.workflow_id] = metrics
        return metrics

    def get_workflow_metrics(self, workflow_id: str) -> WorkflowMetrics | None:
        """Get metrics for a specific workflow.

        Args:
            workflow_id: Workflow ID.

        Returns:
            Workflow metrics or None.
        """
        return self.workflow_metrics.get(workflow_id)

    def get_all_metrics(self) -> list[WorkflowMetrics]:
        """Get metrics for all workflows.

        Returns:
            List of all workflow metrics.
        """
        return list(self.workflow_metrics.values())

    def get_aggregate_stats(self) -> dict[str, Any]:
        """Get aggregate statistics across all workflows.

        Returns:
            Dictionary with aggregate statistics.
        """
        if not self.workflow_metrics:
            return {
                "total_workflows": 0,
                "total_tasks": 0,
                "average_success_rate": 0.0,
                "average_duration": 0.0,
            }

        total_workflows = len(self.workflow_metrics)
        total_tasks = sum(m.total_tasks for m in self.workflow_metrics.values())
        avg_success_rate = sum(m.success_rate for m in self.workflow_metrics.values()) / total_workflows
        avg_duration = (
            sum(m.total_duration_seconds for m in self.workflow_metrics.values()) / total_workflows
        )

        return {
            "total_workflows": total_workflows,
            "total_tasks": total_tasks,
            "average_success_rate": f"{avg_success_rate:.1f}%",
            "average_duration": f"{avg_duration:.2f}s",
            "total_completed": sum(m.completed_tasks for m in self.workflow_metrics.values()),
            "total_failed": sum(m.failed_tasks for m in self.workflow_metrics.values()),
            "total_retries": sum(m.total_retries for m in self.workflow_metrics.values()),
        }

    def clear(self) -> None:
        """Clear all collected metrics."""
        self.workflow_metrics.clear()
