"""Data models for the dynamic orchestration system.

This module defines the core types used for orchestrating multi-agent workflows,
including task definitions, workflow configurations, and execution results.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Status of a task in the workflow."""

    PENDING = "pending"
    READY = "ready"  # Dependencies satisfied, ready to execute
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class ExecutionStrategy(str, Enum):
    """Execution strategy for workflow tasks."""

    SEQUENTIAL = "sequential"  # Execute tasks one by one in order
    PARALLEL = "parallel"  # Execute all independent tasks in parallel
    CONDITIONAL = "conditional"  # Execute based on conditions
    DAG = "dag"  # Execute based on dependency graph (topological sort)


class AgentCapability(str, Enum):
    """Agent capabilities for task routing."""

    GENERAL = "general"
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    TESTING = "testing"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    DATA_PROCESSING = "data_processing"
    FILE_OPERATIONS = "file_operations"
    API_INTEGRATION = "api_integration"
    RESEARCH = "research"


class RetryConfig(BaseModel):
    """Configuration for task retry behavior."""

    max_retries: int = Field(default=3, ge=0, description="Maximum number of retry attempts")
    backoff_multiplier: float = Field(default=2.0, ge=1.0, description="Exponential backoff multiplier")
    initial_delay: float = Field(default=1.0, ge=0.1, description="Initial delay in seconds")
    max_delay: float = Field(default=60.0, ge=1.0, description="Maximum delay in seconds")


class TaskDefinition(BaseModel):
    """Definition of a single task in a workflow."""

    id: str = Field(description="Unique identifier for the task")
    description: str = Field(description="Human-readable description of what the task should do")
    task_type: str | None = Field(default=None, description="Optional type classification for the task")
    depends_on: list[str] = Field(default_factory=list, description="List of task IDs this task depends on")
    required_capabilities: list[AgentCapability] = Field(
        default_factory=lambda: [AgentCapability.GENERAL],
        description="Required agent capabilities for this task",
    )
    required_skills: list[str] = Field(
        default_factory=list,
        description="List of skill names required for this task (auto-loaded when task executes)",
    )
    priority: int = Field(default=5, ge=1, le=10, description="Task priority (1-10, higher is more important)")
    timeout_seconds: float | None = Field(default=None, ge=1.0, description="Maximum execution time in seconds")
    retry_config: RetryConfig = Field(default_factory=RetryConfig, description="Retry configuration")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Task-specific parameters")
    expected_output_type: str | None = Field(default=None, description="Expected output type/format")
    agent_type: str | None = Field(
        default=None, description="Specific agent type to use (overrides capability-based routing)"
    )
    condition: str | None = Field(default=None, description="Condition expression for conditional execution")


class TaskResult(BaseModel):
    """Result of a task execution."""

    task_id: str = Field(description="ID of the executed task")
    status: TaskStatus = Field(description="Final status of the task")
    output: Any = Field(default=None, description="Task output/result")
    error: str | None = Field(default=None, description="Error message if failed")
    started_at: datetime | None = Field(default=None, description="Task start timestamp")
    completed_at: datetime | None = Field(default=None, description="Task completion timestamp")
    duration_seconds: float | None = Field(default=None, description="Execution duration in seconds")
    retry_count: int = Field(default=0, description="Number of retries attempted")
    agent_used: str | None = Field(default=None, description="Agent type that executed the task")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class WorkflowDefinition(BaseModel):
    """Definition of a complete workflow."""

    id: str = Field(description="Unique identifier for the workflow")
    name: str = Field(description="Human-readable workflow name")
    description: str = Field(default="", description="Workflow description")
    tasks: list[TaskDefinition] = Field(description="List of tasks in the workflow")
    execution_strategy: ExecutionStrategy = Field(
        default=ExecutionStrategy.DAG, description="Strategy for executing tasks"
    )
    default_timeout_seconds: float | None = Field(
        default=None, ge=1.0, description="Default timeout for tasks without specific timeout"
    )
    max_parallel_tasks: int = Field(default=5, ge=1, description="Maximum number of tasks to run in parallel")
    continue_on_failure: bool = Field(
        default=False, description="Whether to continue workflow execution if a task fails"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional workflow metadata")


class WorkflowState(BaseModel):
    """Current state of a workflow execution."""

    workflow_id: str = Field(description="ID of the workflow being executed")
    status: Literal["pending", "running", "completed", "failed", "partial"] = Field(
        description="Overall workflow status"
    )
    task_results: dict[str, TaskResult] = Field(default_factory=dict, description="Results of executed tasks")
    current_tasks: list[str] = Field(default_factory=list, description="IDs of currently executing tasks")
    pending_tasks: list[str] = Field(default_factory=list, description="IDs of pending tasks")
    completed_tasks: list[str] = Field(default_factory=list, description="IDs of completed tasks")
    failed_tasks: list[str] = Field(default_factory=list, description="IDs of failed tasks")
    started_at: datetime | None = Field(default=None, description="Workflow start timestamp")
    completed_at: datetime | None = Field(default=None, description="Workflow completion timestamp")
    error: str | None = Field(default=None, description="Overall workflow error if failed")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional state metadata")

    def get_task_status(self, task_id: str) -> TaskStatus:
        """Get the status of a specific task."""
        if task_id in self.task_results:
            return self.task_results[task_id].status
        elif task_id in self.current_tasks:
            return TaskStatus.RUNNING
        elif task_id in self.pending_tasks:
            return TaskStatus.PENDING
        elif task_id in self.completed_tasks:
            return TaskStatus.COMPLETED
        elif task_id in self.failed_tasks:
            return TaskStatus.FAILED
        return TaskStatus.PENDING

    def get_task_output(self, task_id: str) -> Any:
        """Get the output of a completed task."""
        if task_id in self.task_results:
            return self.task_results[task_id].output
        return None

    def is_task_ready(self, task: TaskDefinition) -> bool:
        """Check if a task's dependencies are satisfied."""
        for dep_id in task.depends_on:
            dep_status = self.get_task_status(dep_id)
            if dep_status != TaskStatus.COMPLETED:
                return False
        return True


class AgentRouting(BaseModel):
    """Configuration for agent routing based on capabilities."""

    agent_type: str = Field(description="Agent type identifier")
    capabilities: list[AgentCapability] = Field(description="Capabilities this agent provides")
    priority: int = Field(default=5, ge=1, le=10, description="Routing priority (higher is preferred)")
    max_concurrent_tasks: int = Field(default=1, ge=1, description="Maximum concurrent tasks for this agent")


class OrchestrationConfig(BaseModel):
    """Configuration for the orchestration system."""

    agent_routing: list[AgentRouting] = Field(
        default_factory=list, description="Agent routing configurations"
    )
    enable_parallel_execution: bool = Field(default=True, description="Enable parallel task execution")
    default_retry_config: RetryConfig = Field(
        default_factory=RetryConfig, description="Default retry configuration"
    )
    max_workflow_duration_seconds: float | None = Field(
        default=None, ge=1.0, description="Maximum workflow execution time"
    )
    enable_task_monitoring: bool = Field(default=True, description="Enable detailed task monitoring")
