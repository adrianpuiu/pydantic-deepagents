"""Distributed Agent Orchestrator.

This module provides the main orchestrator for coordinating multiple
specialized worker agents to complete complex tasks through intelligent
task distribution, parallel execution, and result aggregation.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from pydantic_deep import DeepAgentDeps, StateBackend, create_deep_agent
from pydantic_deep.types import SubAgentConfig


class TaskPriority(Enum):
    """Task priority levels."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class TaskStatus(Enum):
    """Status of a distributed task."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Represents a task to be executed by a worker."""

    id: str
    description: str
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    assigned_worker: str | None = None
    result: str | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkerStatus:
    """Status of a worker agent."""

    name: str
    busy: bool = False
    tasks_completed: int = 0
    tasks_failed: int = 0
    current_task: str | None = None
    total_execution_time: float = 0.0


class DistributedOrchestrator:
    """Orchestrates multiple worker agents for distributed task execution.

    The orchestrator manages a pool of specialized worker agents, distributes
    tasks among them, monitors execution, and aggregates results.

    Features:
    - Intelligent task routing based on worker capabilities
    - Parallel execution of independent tasks
    - Load balancing across workers
    - Result aggregation from multiple workers
    - Status monitoring and metrics
    - Error handling and retries

    Example:
        >>> orchestrator = DistributedOrchestrator()
        >>> result = await orchestrator.execute(
        ...     "Analyze data, generate code, and write tests"
        ... )
    """

    def __init__(
        self,
        model: str = "openai:gpt-4o-mini",
        custom_workers: list[SubAgentConfig] | None = None,
        backend: Any | None = None,
        max_concurrent_workers: int = 5,
        enable_monitoring: bool = True,
    ):
        """Initialize the distributed orchestrator.

        Args:
            model: Model to use for orchestrator and workers.
            custom_workers: Optional custom worker configurations.
            backend: Backend for file operations (defaults to StateBackend).
            max_concurrent_workers: Maximum workers executing concurrently.
            enable_monitoring: Whether to enable status monitoring.
        """
        self.model = model
        self.backend = backend or StateBackend()
        self.max_concurrent_workers = max_concurrent_workers
        self.enable_monitoring = enable_monitoring

        # Worker configurations
        self.worker_configs = self._create_default_workers()
        if custom_workers:
            self.worker_configs.extend(custom_workers)

        # Task management
        self.tasks: dict[str, Task] = {}
        self.task_counter = 0

        # Worker status tracking
        self.worker_status: dict[str, WorkerStatus] = {
            config["name"]: WorkerStatus(name=config["name"]) for config in self.worker_configs
        }

        # Create the main orchestrator agent
        self.orchestrator = create_deep_agent(
            model=model,
            instructions=self._get_orchestrator_instructions(),
            subagents=self.worker_configs,
            include_general_purpose_subagent=True,
        )

        # Dependencies
        self.deps = DeepAgentDeps(backend=self.backend)

        # Result aggregation strategy
        self.aggregation_strategy: Callable[[list[str]], str] = self._default_aggregation

    def _create_default_workers(self) -> list[SubAgentConfig]:
        """Create default worker agent configurations."""
        return [
            SubAgentConfig(
                name="data-analyst",
                description="Analyzes data, identifies patterns, generates insights and visualizations",
                instructions="""You are a data analysis expert.

Your responsibilities:
1. Analyze datasets and identify trends, patterns, and anomalies
2. Perform statistical analysis and calculations
3. Generate insights and recommendations
4. Create data visualizations when appropriate
5. Validate data quality and completeness

Always provide clear, actionable insights with supporting evidence.""",
            ),
            SubAgentConfig(
                name="code-writer",
                description="Generates high-quality code based on specifications",
                instructions="""You are an expert software developer.

Your responsibilities:
1. Write clean, efficient, well-documented code
2. Follow best practices and design patterns
3. Implement proper error handling
4. Consider edge cases and security
5. Write production-ready code

Always include clear comments and docstrings.""",
            ),
            SubAgentConfig(
                name="test-writer",
                description="Creates comprehensive unit and integration tests",
                instructions="""You are a test engineering specialist.

Your responsibilities:
1. Write thorough unit tests with pytest
2. Cover happy paths and edge cases
3. Test error handling and exceptions
4. Create meaningful test assertions
5. Ensure high test coverage

Write clear, maintainable test code that serves as documentation.""",
            ),
            SubAgentConfig(
                name="doc-writer",
                description="Produces clear, comprehensive technical documentation",
                instructions="""You are a technical documentation specialist.

Your responsibilities:
1. Write clear, well-structured documentation
2. Include usage examples and API references
3. Explain complex concepts simply
4. Provide code samples and diagrams
5. Follow documentation best practices

Make documentation accessible to both beginners and experts.""",
            ),
            SubAgentConfig(
                name="code-reviewer",
                description="Reviews code for quality, security, and best practices",
                instructions="""You are a senior code reviewer.

Your responsibilities:
1. Review code for bugs and logical errors
2. Check security vulnerabilities (OWASP top 10)
3. Verify proper error handling
4. Assess code quality and maintainability
5. Suggest improvements and best practices

Provide constructive, specific feedback with examples.""",
            ),
        ]

    def _get_orchestrator_instructions(self) -> str:
        """Get instructions for the main orchestrator agent."""
        worker_list = "\n".join(f"- {w['name']}: {w['description']}" for w in self.worker_configs)

        return f"""You are the main orchestrator coordinating multiple specialized worker agents.

Your role:
1. Analyze complex tasks and break them into subtasks
2. Route subtasks to the most appropriate specialized workers
3. Coordinate parallel execution when tasks are independent
4. Aggregate results from multiple workers
5. Ensure all requirements are met

Available workers:
{worker_list}

Guidelines:
- Delegate tasks to specialists rather than doing work yourself
- Execute independent tasks in parallel for efficiency
- Combine worker outputs into cohesive final results
- Handle errors gracefully and retry when appropriate
- Provide clear status updates on progress

Always use the task tool to delegate work to specialized workers."""
    )

    def _default_aggregation(self, results: list[str]) -> str:
        """Default strategy for aggregating multiple results.

        Args:
            results: List of result strings from workers.

        Returns:
            Aggregated result string.
        """
        if not results:
            return "No results to aggregate."

        if len(results) == 1:
            return results[0]

        # Combine results with clear sections
        aggregated = "# Aggregated Results\n\n"
        for i, result in enumerate(results, 1):
            aggregated += f"## Result {i}\n\n{result}\n\n"

        return aggregated

    def set_aggregation_strategy(self, strategy: Callable[[list[str]], str]) -> None:
        """Set custom result aggregation strategy.

        Args:
            strategy: Function that takes list of results and returns aggregated result.
        """
        self.aggregation_strategy = strategy

    async def execute(
        self,
        task_description: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Execute a task using the orchestrator.

        The orchestrator will analyze the task, delegate to appropriate workers,
        and aggregate the results.

        Args:
            task_description: Description of the task to execute.
            priority: Task priority level.
            metadata: Optional task metadata.

        Returns:
            Final aggregated result.
        """
        # Create task record
        task_id = f"task_{self.task_counter}"
        self.task_counter += 1

        task = Task(
            id=task_id,
            description=task_description,
            priority=priority,
            metadata=metadata or {},
        )
        self.tasks[task_id] = task

        # Update task status
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()

        try:
            # Execute through orchestrator
            result = await self.orchestrator.run(task_description, deps=self.deps)

            # Update task status
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = str(result.output)

            return str(result.output)

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = str(e)
            raise

    async def execute_parallel(
        self,
        task_descriptions: list[str],
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> list[str]:
        """Execute multiple independent tasks in parallel.

        Args:
            task_descriptions: List of task descriptions to execute.
            priority: Priority level for all tasks.

        Returns:
            List of results corresponding to input tasks.
        """
        # Create tasks concurrently with semaphore for rate limiting
        semaphore = asyncio.Semaphore(self.max_concurrent_workers)

        async def execute_with_limit(desc: str) -> str:
            async with semaphore:
                return await self.execute(desc, priority=priority)

        results = await asyncio.gather(*[execute_with_limit(desc) for desc in task_descriptions])

        return list(results)

    async def aggregate_results(self, results: list[str]) -> str:
        """Aggregate multiple results using configured strategy.

        Args:
            results: List of results to aggregate.

        Returns:
            Aggregated result.
        """
        return self.aggregation_strategy(results)

    def get_worker_status(self, worker_name: str) -> WorkerStatus | None:
        """Get status of a specific worker.

        Args:
            worker_name: Name of the worker.

        Returns:
            Worker status or None if not found.
        """
        return self.worker_status.get(worker_name)

    def get_all_worker_status(self) -> dict[str, WorkerStatus]:
        """Get status of all workers.

        Returns:
            Dictionary mapping worker names to their status.
        """
        return self.worker_status.copy()

    def get_task_status(self, task_id: str) -> Task | None:
        """Get status of a specific task.

        Args:
            task_id: Task identifier.

        Returns:
            Task object or None if not found.
        """
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> dict[str, Task]:
        """Get all tasks.

        Returns:
            Dictionary mapping task IDs to Task objects.
        """
        return self.tasks.copy()

    def get_metrics(self) -> dict[str, Any]:
        """Get orchestration metrics.

        Returns:
            Dictionary containing performance metrics.
        """
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": completed_tasks / total_tasks if total_tasks > 0 else 0,
            "workers": {
                name: {
                    "tasks_completed": status.tasks_completed,
                    "tasks_failed": status.tasks_failed,
                    "busy": status.busy,
                }
                for name, status in self.worker_status.items()
            },
        }

    def add_worker(self, worker_config: SubAgentConfig) -> None:
        """Add a new worker at runtime.

        Args:
            worker_config: Configuration for the new worker.
        """
        self.worker_configs.append(worker_config)
        self.worker_status[worker_config["name"]] = WorkerStatus(name=worker_config["name"])

        # Recreate orchestrator with new worker
        self.orchestrator = create_deep_agent(
            model=self.model,
            instructions=self._get_orchestrator_instructions(),
            subagents=self.worker_configs,
            include_general_purpose_subagent=True,
        )

    def remove_worker(self, worker_name: str) -> bool:
        """Remove a worker.

        Args:
            worker_name: Name of worker to remove.

        Returns:
            True if worker was removed, False if not found.
        """
        # Find and remove worker config
        for i, config in enumerate(self.worker_configs):
            if config["name"] == worker_name:
                self.worker_configs.pop(i)
                self.worker_status.pop(worker_name, None)

                # Recreate orchestrator without this worker
                self.orchestrator = create_deep_agent(
                    model=self.model,
                    instructions=self._get_orchestrator_instructions(),
                    subagents=self.worker_configs,
                    include_general_purpose_subagent=True,
                )
                return True

        return False

    def __repr__(self) -> str:
        """String representation of orchestrator."""
        return (
            f"DistributedOrchestrator("
            f"workers={len(self.worker_configs)}, "
            f"tasks={len(self.tasks)}, "
            f"max_concurrent={self.max_concurrent_workers})"
        )
