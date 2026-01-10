"""Tests for orchestration metrics collection and analysis."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from pydantic_deep.orchestration.metrics import (
    MetricsCollector,
    TaskMetrics,
    WorkflowMetrics,
)
from pydantic_deep.orchestration.models import TaskResult, TaskStatus, WorkflowState


def test_task_metrics_creation():
    """Test creating task metrics."""
    now = datetime.now()
    later = now + timedelta(seconds=5.5)

    metrics = TaskMetrics(
        task_id="test-task",
        status=TaskStatus.COMPLETED,
        duration_seconds=5.5,
        started_at=now,
        completed_at=later,
        retry_count=0,
        agent_used="general-purpose",
    )

    assert metrics.task_id == "test-task"
    assert metrics.status == TaskStatus.COMPLETED
    assert metrics.duration_seconds == 5.5
    assert metrics.retry_count == 0
    assert metrics.agent_used == "general-purpose"
    assert metrics.succeeded
    assert not metrics.failed


def test_task_metrics_failed():
    """Test task metrics for failed task."""
    now = datetime.now()
    later = now + timedelta(seconds=2.0)

    metrics = TaskMetrics(
        task_id="failed-task",
        status=TaskStatus.FAILED,
        duration_seconds=2.0,
        started_at=now,
        completed_at=later,
        retry_count=3,
        error="Task execution failed",
    )

    assert metrics.failed
    assert not metrics.succeeded
    assert metrics.retry_count == 3
    assert metrics.error == "Task execution failed"


def test_workflow_metrics_from_state():
    """Test creating workflow metrics from workflow state."""
    workflow_id = "test-workflow"
    started_at = datetime.now()
    completed_at = started_at + timedelta(seconds=10.0)

    # Create workflow state with task results
    state = WorkflowState(
        workflow_id=workflow_id,
        status="completed",
        started_at=started_at,
        completed_at=completed_at,
        task_results={
            "task1": TaskResult(
                task_id="task1",
                status=TaskStatus.COMPLETED,
                output="Result 1",
                started_at=started_at,
                completed_at=started_at + timedelta(seconds=3.0),
                duration_seconds=3.0,
                retry_count=0,
                agent_used="general-purpose",
            ),
            "task2": TaskResult(
                task_id="task2",
                status=TaskStatus.COMPLETED,
                output="Result 2",
                started_at=started_at + timedelta(seconds=3.0),
                completed_at=started_at + timedelta(seconds=7.0),
                duration_seconds=4.0,
                retry_count=1,
                agent_used="code-analyst",
            ),
            "task3": TaskResult(
                task_id="task3",
                status=TaskStatus.FAILED,
                error="Task failed",
                started_at=started_at + timedelta(seconds=7.0),
                completed_at=started_at + timedelta(seconds=10.0),
                duration_seconds=3.0,
                retry_count=3,
                agent_used="general-purpose",
            ),
        },
        completed_tasks=["task1", "task2"],
        failed_tasks=["task3"],
    )

    metrics = WorkflowMetrics.from_workflow_state(state, "Test Workflow")

    assert metrics.workflow_id == workflow_id
    assert metrics.workflow_name == "Test Workflow"
    assert metrics.status == "completed"
    assert metrics.total_tasks == 3
    assert metrics.completed_tasks == 2
    assert metrics.failed_tasks == 1
    assert metrics.total_retries == 4  # 0 + 1 + 3
    assert metrics.success_rate == pytest.approx(66.67, abs=0.1)
    assert metrics.retry_rate == pytest.approx(1.33, abs=0.01)


def test_workflow_metrics_calculations():
    """Test workflow metrics calculations."""
    workflow_id = "metrics-test"
    started_at = datetime.now()
    completed_at = started_at + timedelta(seconds=15.0)

    state = WorkflowState(
        workflow_id=workflow_id,
        status="completed",
        started_at=started_at,
        completed_at=completed_at,
        task_results={
            "fast": TaskResult(
                task_id="fast",
                status=TaskStatus.COMPLETED,
                output="Fast result",
                started_at=started_at,
                completed_at=started_at + timedelta(seconds=2.0),
                duration_seconds=2.0,
                retry_count=0,
            ),
            "slow": TaskResult(
                task_id="slow",
                status=TaskStatus.COMPLETED,
                output="Slow result",
                started_at=started_at + timedelta(seconds=2.0),
                completed_at=started_at + timedelta(seconds=12.0),
                duration_seconds=10.0,
                retry_count=0,
            ),
            "medium": TaskResult(
                task_id="medium",
                status=TaskStatus.COMPLETED,
                output="Medium result",
                started_at=started_at + timedelta(seconds=12.0),
                completed_at=started_at + timedelta(seconds=15.0),
                duration_seconds=3.0,
                retry_count=0,
            ),
        },
        completed_tasks=["fast", "slow", "medium"],
        failed_tasks=[],
    )

    metrics = WorkflowMetrics.from_workflow_state(state)

    # Check timing metrics
    assert metrics.total_duration_seconds == 15.0
    assert metrics.average_task_duration == pytest.approx(5.0, abs=0.1)  # (2 + 10 + 3) / 3

    # Check slowest and fastest
    assert metrics.slowest_task is not None
    assert metrics.slowest_task.task_id == "slow"
    assert metrics.slowest_task.duration_seconds == 10.0

    assert metrics.fastest_task is not None
    assert metrics.fastest_task.task_id == "fast"
    assert metrics.fastest_task.duration_seconds == 2.0

    # Check success metrics
    assert metrics.success_rate == 100.0
    assert metrics.retry_rate == 0.0


def test_workflow_metrics_get_bottleneck():
    """Test identifying workflow bottleneck."""
    workflow_id = "bottleneck-test"
    started_at = datetime.now()

    state = WorkflowState(
        workflow_id=workflow_id,
        status="completed",
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=20.0),
        task_results={
            "task1": TaskResult(
                task_id="task1",
                status=TaskStatus.COMPLETED,
                output="Result",
                started_at=started_at,
                completed_at=started_at + timedelta(seconds=5.0),
                duration_seconds=5.0,
            ),
            "bottleneck": TaskResult(
                task_id="bottleneck",
                status=TaskStatus.COMPLETED,
                output="Result",
                started_at=started_at + timedelta(seconds=5.0),
                completed_at=started_at + timedelta(seconds=20.0),
                duration_seconds=15.0,
            ),
        },
        completed_tasks=["task1", "bottleneck"],
        failed_tasks=[],
    )

    metrics = WorkflowMetrics.from_workflow_state(state)
    bottleneck = metrics.get_bottleneck()

    assert bottleneck is not None
    assert bottleneck.task_id == "bottleneck"
    assert bottleneck.duration_seconds == 15.0


def test_workflow_metrics_get_task_metrics():
    """Test getting metrics for specific task."""
    workflow_id = "task-lookup-test"
    started_at = datetime.now()

    state = WorkflowState(
        workflow_id=workflow_id,
        status="completed",
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=5.0),
        task_results={
            "task1": TaskResult(
                task_id="task1",
                status=TaskStatus.COMPLETED,
                output="Result",
                started_at=started_at,
                completed_at=started_at + timedelta(seconds=5.0),
                duration_seconds=5.0,
            ),
        },
        completed_tasks=["task1"],
        failed_tasks=[],
    )

    metrics = WorkflowMetrics.from_workflow_state(state)

    task_metrics = metrics.get_task_metrics("task1")
    assert task_metrics is not None
    assert task_metrics.task_id == "task1"

    missing_metrics = metrics.get_task_metrics("nonexistent")
    assert missing_metrics is None


def test_workflow_metrics_get_failed_tasks():
    """Test getting failed task metrics."""
    workflow_id = "failed-tasks-test"
    started_at = datetime.now()

    state = WorkflowState(
        workflow_id=workflow_id,
        status="failed",
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=10.0),
        task_results={
            "success": TaskResult(
                task_id="success",
                status=TaskStatus.COMPLETED,
                output="Result",
                started_at=started_at,
                completed_at=started_at + timedelta(seconds=5.0),
                duration_seconds=5.0,
            ),
            "fail1": TaskResult(
                task_id="fail1",
                status=TaskStatus.FAILED,
                error="Error 1",
                started_at=started_at + timedelta(seconds=5.0),
                completed_at=started_at + timedelta(seconds=8.0),
                duration_seconds=3.0,
            ),
            "fail2": TaskResult(
                task_id="fail2",
                status=TaskStatus.FAILED,
                error="Error 2",
                started_at=started_at + timedelta(seconds=8.0),
                completed_at=started_at + timedelta(seconds=10.0),
                duration_seconds=2.0,
            ),
        },
        completed_tasks=["success"],
        failed_tasks=["fail1", "fail2"],
    )

    metrics = WorkflowMetrics.from_workflow_state(state)
    failed = metrics.get_failed_tasks()

    assert len(failed) == 2
    assert all(t.failed for t in failed)
    assert {t.task_id for t in failed} == {"fail1", "fail2"}


def test_workflow_metrics_get_summary():
    """Test getting workflow metrics summary."""
    workflow_id = "summary-test"
    started_at = datetime.now()

    state = WorkflowState(
        workflow_id=workflow_id,
        status="completed",
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=10.0),
        task_results={
            "task1": TaskResult(
                task_id="task1",
                status=TaskStatus.COMPLETED,
                output="Result",
                started_at=started_at,
                completed_at=started_at + timedelta(seconds=10.0),
                duration_seconds=10.0,
                retry_count=1,
            ),
        },
        completed_tasks=["task1"],
        failed_tasks=[],
    )

    metrics = WorkflowMetrics.from_workflow_state(state, "Test Workflow")
    summary = metrics.get_summary()

    assert summary["workflow_id"] == workflow_id
    assert summary["workflow_name"] == "Test Workflow"
    assert summary["status"] == "completed"
    assert summary["total_duration_seconds"] == 10.0
    assert summary["total_tasks"] == 1
    assert summary["completed_tasks"] == 1
    assert summary["failed_tasks"] == 0
    assert summary["success_rate"] == "100.0%"
    assert summary["total_retries"] == 1


def test_workflow_metrics_get_performance_report():
    """Test generating performance report."""
    workflow_id = "report-test"
    started_at = datetime.now()

    state = WorkflowState(
        workflow_id=workflow_id,
        status="completed",
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=15.0),
        task_results={
            "task1": TaskResult(
                task_id="task1",
                status=TaskStatus.COMPLETED,
                output="Result 1",
                started_at=started_at,
                completed_at=started_at + timedelta(seconds=5.0),
                duration_seconds=5.0,
            ),
            "task2": TaskResult(
                task_id="task2",
                status=TaskStatus.COMPLETED,
                output="Result 2",
                started_at=started_at + timedelta(seconds=5.0),
                completed_at=started_at + timedelta(seconds=15.0),
                duration_seconds=10.0,
            ),
        },
        completed_tasks=["task1", "task2"],
        failed_tasks=[],
    )

    metrics = WorkflowMetrics.from_workflow_state(state, "Performance Test")
    report = metrics.get_performance_report()

    assert "Performance Test" in report
    assert "completed" in report
    assert "15.00s" in report
    assert "Total Tasks: 2" in report
    assert "Completed: 2" in report
    assert "100.0%" in report


def test_metrics_collector_record_workflow():
    """Test recording workflow metrics."""
    collector = MetricsCollector()
    workflow_id = "collector-test"
    started_at = datetime.now()

    state = WorkflowState(
        workflow_id=workflow_id,
        status="completed",
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=5.0),
        task_results={
            "task1": TaskResult(
                task_id="task1",
                status=TaskStatus.COMPLETED,
                output="Result",
                started_at=started_at,
                completed_at=started_at + timedelta(seconds=5.0),
                duration_seconds=5.0,
            ),
        },
        completed_tasks=["task1"],
        failed_tasks=[],
    )

    metrics = collector.record_workflow(state, "Test Workflow")

    assert metrics.workflow_id == workflow_id
    assert metrics.workflow_name == "Test Workflow"
    assert len(collector.workflow_metrics) == 1


def test_metrics_collector_get_workflow_metrics():
    """Test retrieving workflow metrics from collector."""
    collector = MetricsCollector()
    workflow_id = "retrieval-test"
    started_at = datetime.now()

    state = WorkflowState(
        workflow_id=workflow_id,
        status="completed",
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=5.0),
        task_results={},
        completed_tasks=[],
        failed_tasks=[],
    )

    collector.record_workflow(state)

    # Retrieve metrics
    metrics = collector.get_workflow_metrics(workflow_id)
    assert metrics is not None
    assert metrics.workflow_id == workflow_id

    # Try non-existent workflow
    missing = collector.get_workflow_metrics("nonexistent")
    assert missing is None


def test_metrics_collector_get_all_metrics():
    """Test getting all workflow metrics."""
    collector = MetricsCollector()
    started_at = datetime.now()

    # Record multiple workflows
    for i in range(3):
        state = WorkflowState(
            workflow_id=f"workflow-{i}",
            status="completed",
            started_at=started_at,
            completed_at=started_at + timedelta(seconds=5.0),
            task_results={},
            completed_tasks=[],
            failed_tasks=[],
        )
        collector.record_workflow(state, f"Workflow {i}")

    all_metrics = collector.get_all_metrics()
    assert len(all_metrics) == 3
    assert {m.workflow_id for m in all_metrics} == {"workflow-0", "workflow-1", "workflow-2"}


def test_metrics_collector_get_aggregate_stats():
    """Test getting aggregate statistics."""
    collector = MetricsCollector()
    started_at = datetime.now()

    # Record workflows with varying success
    for i in range(3):
        completed_tasks = [] if i == 2 else [f"task-{i}"]
        failed_tasks = [f"task-{i}"] if i == 2 else []

        task_results = {}
        if i != 2:
            task_results[f"task-{i}"] = TaskResult(
                task_id=f"task-{i}",
                status=TaskStatus.COMPLETED,
                output="Result",
                started_at=started_at,
                completed_at=started_at + timedelta(seconds=5.0),
                duration_seconds=5.0,
            )
        else:
            task_results[f"task-{i}"] = TaskResult(
                task_id=f"task-{i}",
                status=TaskStatus.FAILED,
                error="Failed",
                started_at=started_at,
                completed_at=started_at + timedelta(seconds=5.0),
                duration_seconds=5.0,
            )

        state = WorkflowState(
            workflow_id=f"workflow-{i}",
            status="completed" if i != 2 else "failed",
            started_at=started_at,
            completed_at=started_at + timedelta(seconds=5.0),
            task_results=task_results,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
        )
        collector.record_workflow(state)

    stats = collector.get_aggregate_stats()

    assert stats["total_workflows"] == 3
    assert stats["total_tasks"] == 3
    assert stats["total_completed"] == 2
    assert stats["total_failed"] == 1


def test_metrics_collector_clear():
    """Test clearing metrics."""
    collector = MetricsCollector()
    started_at = datetime.now()

    state = WorkflowState(
        workflow_id="test",
        status="completed",
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=5.0),
        task_results={},
        completed_tasks=[],
        failed_tasks=[],
    )

    collector.record_workflow(state)
    assert len(collector.workflow_metrics) == 1

    collector.clear()
    assert len(collector.workflow_metrics) == 0


def test_metrics_collector_empty_aggregate_stats():
    """Test aggregate stats with no workflows."""
    collector = MetricsCollector()
    stats = collector.get_aggregate_stats()

    assert stats["total_workflows"] == 0
    assert stats["total_tasks"] == 0
    assert stats["average_success_rate"] == 0.0
    assert stats["average_duration"] == 0.0
