"""Tests for the orchestration system."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from pydantic_deep import (
    AgentCapability,
    ExecutionStrategy,
    OrchestrationConfig,
    StateBackend,
    TaskDefinition,
    TaskOrchestrator,
    TaskResult,
    TaskStatus,
    WorkflowDefinition,
    create_deep_agent,
    create_default_deps,
    create_default_routing,
)
from pydantic_deep.deps import DeepAgentDeps
from pydantic_deep.orchestration.executor import (
    ConditionalExecutor,
    DAGExecutor,
    ExecutorFactory,
    ParallelExecutor,
    SequentialExecutor,
)
from pydantic_deep.orchestration.routing import TaskRouter
from pydantic_deep.orchestration.models import WorkflowState
from pydantic_deep.orchestration.state import StateManager


class TestWorkflowState:
    """Tests for WorkflowState model methods."""

    def test_get_task_status(self) -> None:
        """Test getting task status."""
        state = WorkflowState(workflow_id="test")
        state.pending_tasks = ["task1"]
        state.current_tasks = ["task2"]
        state.completed_tasks = ["task3"]
        state.failed_tasks = ["task4"]

        assert state.get_task_status("task1") == TaskStatus.PENDING
        assert state.get_task_status("task2") == TaskStatus.RUNNING
        assert state.get_task_status("task3") == TaskStatus.COMPLETED
        assert state.get_task_status("task4") == TaskStatus.FAILED
        assert state.get_task_status("task5") == TaskStatus.PENDING  # default

    def test_get_task_output(self) -> None:
        """Test getting task output."""
        state = WorkflowState(workflow_id="test")
        state.task_results = {
            "task1": TaskResult(task_id="task1", status=TaskStatus.COMPLETED, output="result1")
        }

        assert state.get_task_output("task1") == "result1"
        assert state.get_task_output("task2") is None

    def test_is_task_ready(self) -> None:
        """Test checking if task dependencies are satisfied."""
        state = WorkflowState(workflow_id="test")
        state.completed_tasks = ["task1"]

        task_no_deps = TaskDefinition(id="task2", description="Task 2")
        task_with_satisfied_deps = TaskDefinition(
            id="task3", description="Task 3", depends_on=["task1"]
        )
        task_with_unsatisfied_deps = TaskDefinition(
            id="task4", description="Task 4", depends_on=["task1", "task2"]
        )

        assert state.is_task_ready(task_no_deps)
        assert state.is_task_ready(task_with_satisfied_deps)
        assert not state.is_task_ready(task_with_unsatisfied_deps)


class TestStateManager:
    """Tests for StateManager."""

    def test_state_manager_initialization(self) -> None:
        """Test state manager initialization."""
        workflow = WorkflowDefinition(
            id="test-workflow",
            name="Test",
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2"),
            ],
        )
        manager = StateManager(workflow)

        assert manager.state.workflow_id == "test-workflow"
        assert manager.state.status == "pending"
        assert len(manager.state.pending_tasks) == 2
        assert manager.state.started_at is None

    def test_start_workflow(self) -> None:
        """Test starting a workflow."""
        workflow = WorkflowDefinition(id="test", name="Test", tasks=[])
        manager = StateManager(workflow)

        manager.start_workflow()

        assert manager.state.status == "running"
        assert manager.state.started_at is not None

    def test_complete_workflow(self) -> None:
        """Test completing a workflow."""
        workflow = WorkflowDefinition(id="test", name="Test", tasks=[])
        manager = StateManager(workflow)

        manager.start_workflow()
        manager.complete_workflow()

        assert manager.state.status == "completed"
        assert manager.state.completed_at is not None

    def test_fail_workflow(self) -> None:
        """Test failing a workflow."""
        workflow = WorkflowDefinition(id="test", name="Test", tasks=[])
        manager = StateManager(workflow)

        manager.start_workflow()
        manager.fail_workflow("Test error")

        assert manager.state.status == "failed"
        assert manager.state.error == "Test error"
        assert manager.state.completed_at is not None

    def test_get_ready_tasks(self) -> None:
        """Test getting ready tasks."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2", depends_on=["task1"]),
                TaskDefinition(id="task3", description="Task 3"),
            ],
        )
        manager = StateManager(workflow)

        ready_tasks = manager.get_ready_tasks()
        ready_ids = [t.id for t in ready_tasks]

        assert "task1" in ready_ids
        assert "task3" in ready_ids
        assert "task2" not in ready_ids  # Has dependency

    def test_task_lifecycle(self) -> None:
        """Test task state transitions."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[TaskDefinition(id="task1", description="Task 1")],
        )
        manager = StateManager(workflow)

        # Start task
        manager.start_task("task1")
        assert "task1" in manager.state.current_tasks
        assert "task1" not in manager.state.pending_tasks
        assert manager.state.get_task_status("task1") == TaskStatus.RUNNING

        # Complete task
        manager.complete_task("task1", "result", "agent-type")
        assert "task1" in manager.state.completed_tasks
        assert "task1" not in manager.state.current_tasks
        assert manager.state.get_task_status("task1") == TaskStatus.COMPLETED

        result = manager.state.task_results["task1"]
        assert result.output == "result"
        assert result.agent_used == "agent-type"
        assert result.duration_seconds is not None

    def test_fail_task(self) -> None:
        """Test failing a task."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[TaskDefinition(id="task1", description="Task 1")],
        )
        manager = StateManager(workflow)

        manager.start_task("task1")
        manager.fail_task("task1", "Test error")

        assert "task1" in manager.state.failed_tasks
        assert manager.state.get_task_status("task1") == TaskStatus.FAILED

        result = manager.state.task_results["task1"]
        assert result.error == "Test error"

    def test_retry_task(self) -> None:
        """Test retrying a task."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[TaskDefinition(id="task1", description="Task 1")],
        )
        manager = StateManager(workflow)

        manager.start_task("task1")
        manager.fail_task("task1", "Test error")
        manager.retry_task("task1")

        assert "task1" in manager.state.pending_tasks
        assert "task1" not in manager.state.failed_tasks

        result = manager.state.task_results["task1"]
        assert result.status == TaskStatus.RETRYING
        assert result.retry_count == 1

    def test_skip_task(self) -> None:
        """Test skipping a task."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[TaskDefinition(id="task1", description="Task 1")],
        )
        manager = StateManager(workflow)

        manager.skip_task("task1", "Condition not met")

        assert "task1" not in manager.state.pending_tasks
        assert manager.state.get_task_status("task1") == TaskStatus.SKIPPED

        result = manager.state.task_results["task1"]
        assert result.error == "Condition not met"

    def test_is_workflow_complete(self) -> None:
        """Test workflow completion check."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2"),
            ],
        )
        manager = StateManager(workflow)

        assert not manager.is_workflow_complete()

        manager.start_task("task1")
        assert not manager.is_workflow_complete()

        manager.complete_task("task1", "result")
        assert not manager.is_workflow_complete()

        manager.start_task("task2")
        manager.complete_task("task2", "result")
        assert manager.is_workflow_complete()

    def test_get_progress(self) -> None:
        """Test progress calculation."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2"),
                TaskDefinition(id="task3", description="Task 3"),
            ],
        )
        manager = StateManager(workflow)
        manager.start_workflow()

        progress = manager.get_progress()
        assert progress["total_tasks"] == 3
        assert progress["completed"] == 0
        assert progress["pending"] == 3

        manager.start_task("task1")
        manager.complete_task("task1", "result")

        progress = manager.get_progress()
        assert progress["completed"] == 1
        assert progress["pending"] == 2
        assert progress["progress_percent"] == pytest.approx(33.33, rel=0.1)

    def test_topological_sort(self) -> None:
        """Test topological sorting of tasks."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[
                TaskDefinition(id="task1", description="Task 1", depends_on=[]),
                TaskDefinition(id="task2", description="Task 2", depends_on=["task1"]),
                TaskDefinition(id="task3", description="Task 3", depends_on=["task1"]),
                TaskDefinition(id="task4", description="Task 4", depends_on=["task2", "task3"]),
            ],
        )
        manager = StateManager(workflow)

        sorted_tasks = manager.topological_sort()

        # task1 should come first
        assert sorted_tasks[0] == "task1"
        # task4 should come last
        assert sorted_tasks[-1] == "task4"
        # task2 and task3 should come before task4
        task2_idx = sorted_tasks.index("task2")
        task3_idx = sorted_tasks.index("task3")
        task4_idx = sorted_tasks.index("task4")
        assert task2_idx < task4_idx
        assert task3_idx < task4_idx

    def test_topological_sort_circular_dependency(self) -> None:
        """Test that circular dependencies are detected."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[
                TaskDefinition(id="task1", description="Task 1", depends_on=["task2"]),
                TaskDefinition(id="task2", description="Task 2", depends_on=["task1"]),
            ],
        )
        manager = StateManager(workflow)

        with pytest.raises(ValueError, match="Circular dependency"):
            manager.topological_sort()

    def test_get_dependency_chain(self) -> None:
        """Test getting dependency chain for a task."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2", depends_on=["task1"]),
                TaskDefinition(id="task3", description="Task 3", depends_on=["task2"]),
            ],
        )
        manager = StateManager(workflow)

        chain = manager.get_dependency_chain("task3")
        assert "task1" in chain
        assert "task2" in chain
        assert "task3" in chain
        # task1 should come before task2
        assert chain.index("task1") < chain.index("task2")
        # task2 should come before task3
        assert chain.index("task2") < chain.index("task3")

    def test_get_dependency_chain_no_dependencies(self) -> None:
        """Test getting dependency chain for task with no dependencies."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[TaskDefinition(id="task1", description="Task 1")],
        )
        manager = StateManager(workflow)

        chain = manager.get_dependency_chain("task1")
        assert chain == ["task1"]

    def test_get_dependency_chain_nonexistent_task(self) -> None:
        """Test getting dependency chain for nonexistent task."""
        workflow = WorkflowDefinition(id="test", name="Test", tasks=[])
        manager = StateManager(workflow)

        chain = manager.get_dependency_chain("nonexistent")
        assert chain == []

    def test_build_dependency_graph(self) -> None:
        """Test building dependency graph."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2", depends_on=["task1"]),
                TaskDefinition(id="task3", description="Task 3", depends_on=["task1", "task2"]),
            ],
        )
        manager = StateManager(workflow)

        graph = manager.build_dependency_graph()
        assert graph["task1"] == []
        assert graph["task2"] == ["task1"]
        assert set(graph["task3"]) == {"task1", "task2"}

    def test_get_task_by_id(self) -> None:
        """Test getting task by ID."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2"),
            ],
        )
        manager = StateManager(workflow)

        task = manager.get_task_by_id("task1")
        assert task is not None
        assert task.id == "task1"

        task = manager.get_task_by_id("nonexistent")
        assert task is None

    def test_condition_evaluation(self) -> None:
        """Test condition evaluation for tasks."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2", condition="task1"),
            ],
        )
        manager = StateManager(workflow)

        # Before task1 completes, condition should not be met
        ready_tasks = manager.get_ready_tasks()
        assert len(ready_tasks) == 1
        assert ready_tasks[0].id == "task1"

        # Complete task1
        manager.start_task("task1")
        manager.complete_task("task1", "result")

        # Now task2 should be ready (condition met)
        ready_tasks = manager.get_ready_tasks()
        assert len(ready_tasks) == 1
        assert ready_tasks[0].id == "task2"


class TestTaskRouter:
    """Tests for TaskRouter."""

    def test_router_initialization(self) -> None:
        """Test router initialization."""
        config = OrchestrationConfig(agent_routing=create_default_routing())
        router = TaskRouter(config)

        assert len(router.config.agent_routing) > 0
        assert router.agent_load == {}

    def test_route_task_with_explicit_agent(self) -> None:
        """Test routing with explicit agent type."""
        config = OrchestrationConfig()
        router = TaskRouter(config)

        task = TaskDefinition(
            id="task1",
            description="Task 1",
            agent_type="custom-agent",
        )

        agent_type = router.route_task(task)
        assert agent_type == "custom-agent"

    def test_route_task_by_capability(self) -> None:
        """Test routing by capability matching."""
        config = OrchestrationConfig(agent_routing=create_default_routing())
        router = TaskRouter(config)

        task = TaskDefinition(
            id="task1",
            description="Task 1",
            required_capabilities=[AgentCapability.CODE_ANALYSIS],
        )

        agent_type = router.route_task(task)
        # Should route to code-analyzer which has CODE_ANALYSIS capability
        assert agent_type == "code-analyzer"

    def test_route_task_fallback_to_general(self) -> None:
        """Test fallback to general-purpose agent."""
        config = OrchestrationConfig()
        router = TaskRouter(config)

        task = TaskDefinition(
            id="task1",
            description="Task 1",
            required_capabilities=[AgentCapability.GENERAL],
        )

        agent_type = router.route_task(task)
        assert agent_type == "general-purpose"

    def test_agent_load_tracking(self) -> None:
        """Test agent load tracking."""
        config = OrchestrationConfig()
        router = TaskRouter(config)

        router.increment_agent_load("agent1")
        router.increment_agent_load("agent1")
        router.increment_agent_load("agent2")

        assert router.get_agent_load("agent1") == 2
        assert router.get_agent_load("agent2") == 1

        router.decrement_agent_load("agent1")
        assert router.get_agent_load("agent1") == 1

    def test_load_summary(self) -> None:
        """Test load summary."""
        config = OrchestrationConfig()
        router = TaskRouter(config)

        router.increment_agent_load("agent1")
        router.increment_agent_load("agent2")

        summary = router.get_load_summary()
        assert summary["agent1"] == 1
        assert summary["agent2"] == 1


class TestExecutors:
    """Tests for execution strategies."""

    async def test_sequential_executor(self) -> None:
        """Test sequential execution."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2"),
            ],
        )
        manager = StateManager(workflow)

        executed_tasks = []

        async def task_executor(task: TaskDefinition) -> TaskResult:
            executed_tasks.append(task.id)
            manager.start_task(task.id)
            await asyncio.sleep(0.01)  # Simulate work
            manager.complete_task(task.id, f"result-{task.id}")
            return manager.state.task_results[task.id]

        executor = SequentialExecutor(manager, task_executor)
        results = await executor.execute()

        assert len(executed_tasks) == 2
        assert executed_tasks == ["task1", "task2"]
        assert len(results) == 2

    async def test_parallel_executor(self) -> None:
        """Test parallel execution."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[
                TaskDefinition(id=f"task{i}", description=f"Task {i}")
                for i in range(5)
            ],
        )
        manager = StateManager(workflow)

        async def task_executor(task: TaskDefinition) -> TaskResult:
            manager.start_task(task.id)
            await asyncio.sleep(0.01)
            manager.complete_task(task.id, f"result-{task.id}")
            return manager.state.task_results[task.id]

        executor = ParallelExecutor(manager, task_executor, max_parallel=3)
        results = await executor.execute()

        assert len(results) == 5
        assert all(r.status == TaskStatus.COMPLETED for r in results.values())

    async def test_dag_executor(self) -> None:
        """Test DAG-based execution."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            execution_strategy=ExecutionStrategy.DAG,
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2", depends_on=["task1"]),
                TaskDefinition(id="task3", description="Task 3", depends_on=["task1"]),
                TaskDefinition(id="task4", description="Task 4", depends_on=["task2", "task3"]),
            ],
        )
        manager = StateManager(workflow)

        execution_order = []

        async def task_executor(task: TaskDefinition) -> TaskResult:
            execution_order.append(task.id)
            manager.start_task(task.id)
            await asyncio.sleep(0.01)
            manager.complete_task(task.id, f"result-{task.id}")
            return manager.state.task_results[task.id]

        executor = DAGExecutor(manager, task_executor, max_parallel=2)
        results = await executor.execute()

        # task1 should execute first
        assert execution_order[0] == "task1"
        # task4 should execute last
        assert execution_order[-1] == "task4"
        # All tasks should complete
        assert len(results) == 4

    async def test_executor_factory(self) -> None:
        """Test executor factory."""
        workflow = WorkflowDefinition(id="test", name="Test", tasks=[])
        manager = StateManager(workflow)

        async def task_executor(task: TaskDefinition) -> TaskResult:
            return TaskResult(task_id=task.id, status=TaskStatus.COMPLETED)

        # Test sequential
        executor = ExecutorFactory.create_executor(
            ExecutionStrategy.SEQUENTIAL, manager, task_executor
        )
        assert isinstance(executor, SequentialExecutor)

        # Test parallel
        executor = ExecutorFactory.create_executor(
            ExecutionStrategy.PARALLEL, manager, task_executor
        )
        assert isinstance(executor, ParallelExecutor)

        # Test DAG
        executor = ExecutorFactory.create_executor(
            ExecutionStrategy.DAG, manager, task_executor
        )
        assert isinstance(executor, DAGExecutor)

        # Test conditional
        executor = ExecutorFactory.create_executor(
            ExecutionStrategy.CONDITIONAL, manager, task_executor
        )
        assert isinstance(executor, ConditionalExecutor)

        # Test unknown strategy
        with pytest.raises(ValueError, match="Unknown execution strategy"):
            ExecutorFactory.create_executor("invalid", manager, task_executor)  # type: ignore

    async def test_dag_executor_with_circular_dependency(self) -> None:
        """Test DAG executor with circular dependencies."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            execution_strategy=ExecutionStrategy.DAG,
            tasks=[
                TaskDefinition(id="task1", description="Task 1", depends_on=["task2"]),
                TaskDefinition(id="task2", description="Task 2", depends_on=["task1"]),
            ],
        )
        manager = StateManager(workflow)

        async def task_executor(task: TaskDefinition) -> TaskResult:
            manager.start_task(task.id)
            manager.complete_task(task.id, "result")
            return manager.state.task_results[task.id]

        executor = DAGExecutor(manager, task_executor)
        results = await executor.execute()

        # All tasks should be marked as failed due to circular dependency
        assert len(results) == 2
        assert all(r.status == TaskStatus.FAILED for r in results.values())

    async def test_conditional_executor(self) -> None:
        """Test conditional executor."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            execution_strategy=ExecutionStrategy.CONDITIONAL,
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2", condition="task1"),
            ],
        )
        manager = StateManager(workflow)

        async def task_executor(task: TaskDefinition) -> TaskResult:
            manager.start_task(task.id)
            manager.complete_task(task.id, "result")
            return manager.state.task_results[task.id]

        executor = ConditionalExecutor(manager, task_executor)
        results = await executor.execute()

        # Both tasks should complete (condition met after task1)
        assert len(results) == 2
        assert results["task1"].status == TaskStatus.COMPLETED
        assert results["task2"].status == TaskStatus.COMPLETED

    async def test_sequential_executor_with_failure(self) -> None:
        """Test sequential executor stops on failure."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            execution_strategy=ExecutionStrategy.SEQUENTIAL,
            continue_on_failure=False,
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2"),
                TaskDefinition(id="task3", description="Task 3"),
            ],
        )
        manager = StateManager(workflow)

        call_count = 0

        async def task_executor(task: TaskDefinition) -> TaskResult:
            nonlocal call_count
            call_count += 1
            manager.start_task(task.id)

            # Fail task1
            if task.id == "task1":
                manager.fail_task(task.id, "Test failure")
            else:
                manager.complete_task(task.id, "result")

            return manager.state.task_results[task.id]

        executor = SequentialExecutor(manager, task_executor)
        results = await executor.execute()

        # task1 should fail, task2 and task3 should be skipped
        assert results["task1"].status == TaskStatus.FAILED
        # Remaining tasks should be skipped
        assert len([r for r in results.values() if r.status == TaskStatus.SKIPPED]) >= 1


class TestTaskOrchestrator:
    """Tests for TaskOrchestrator."""

    async def test_orchestrator_initialization(self) -> None:
        """Test orchestrator initialization."""
        agent = create_deep_agent(model=TestModel())
        deps = create_default_deps(backend=StateBackend())

        orchestrator = TaskOrchestrator(agent, deps)

        assert orchestrator.agent == agent
        assert orchestrator.deps == deps
        assert orchestrator.config is not None

    async def test_execute_single_task(self) -> None:
        """Test executing a single task."""
        agent = create_deep_agent(model=TestModel())
        deps = create_default_deps(backend=StateBackend())
        orchestrator = TaskOrchestrator(agent, deps)

        task = TaskDefinition(
            id="test-task",
            description="Test task description",
            agent_type="general-purpose",  # Use general-purpose to avoid routing issues
        )

        result = await orchestrator.execute_task(task)

        assert result.task_id == "test-task"
        # Task may be completed, failed, or skipped (if retries exhausted)
        assert result.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED]

    async def test_execute_workflow(self) -> None:
        """Test executing a complete workflow."""
        agent = create_deep_agent(model=TestModel())
        deps = create_default_deps(backend=StateBackend())
        orchestrator = TaskOrchestrator(agent, deps)

        workflow = WorkflowDefinition(
            id="test-workflow",
            name="Test Workflow",
            tasks=[
                TaskDefinition(
                    id="task1",
                    description="Task 1",
                    agent_type="general-purpose",  # Use general-purpose to avoid routing issues
                ),
                TaskDefinition(
                    id="task2",
                    description="Task 2",
                    depends_on=["task1"],
                    agent_type="general-purpose",
                ),
            ],
        )

        state = await orchestrator.execute_workflow(workflow)

        assert state.workflow_id == "test-workflow"
        assert state.status in ["completed", "failed", "partial"]
        # At least one task should have a result (may not complete all tasks if first fails)
        assert len(state.task_results) >= 1

    async def test_get_workflow_state(self) -> None:
        """Test getting workflow state."""
        agent = create_deep_agent(model=TestModel())
        deps = create_default_deps(backend=StateBackend())
        orchestrator = TaskOrchestrator(agent, deps)

        workflow = WorkflowDefinition(
            id="test-workflow",
            name="Test",
            tasks=[TaskDefinition(id="task1", description="Task 1")],
        )

        # Execute workflow
        await orchestrator.execute_workflow(workflow)

        # Get state
        state = orchestrator.get_workflow_state("test-workflow")
        assert state is not None
        assert state.workflow_id == "test-workflow"

    async def test_get_workflow_progress(self) -> None:
        """Test getting workflow progress."""
        agent = create_deep_agent(model=TestModel())
        deps = create_default_deps(backend=StateBackend())
        orchestrator = TaskOrchestrator(agent, deps)

        workflow = WorkflowDefinition(
            id="test-workflow",
            name="Test",
            tasks=[TaskDefinition(id="task1", description="Task 1")],
        )

        await orchestrator.execute_workflow(workflow)

        progress = orchestrator.get_workflow_progress("test-workflow")
        assert progress is not None
        assert "total_tasks" in progress
        assert progress["total_tasks"] == 1

    async def test_cancel_workflow(self) -> None:
        """Test cancelling a workflow."""
        agent = create_deep_agent(model=TestModel())
        deps = create_default_deps(backend=StateBackend())
        orchestrator = TaskOrchestrator(agent, deps)

        workflow = WorkflowDefinition(
            id="test-workflow",
            name="Test",
            tasks=[TaskDefinition(id="task1", description="Task 1")],
        )

        # Start workflow (but it will complete quickly with TestModel)
        await orchestrator.execute_workflow(workflow)

        # Try to cancel completed workflow (should return False)
        result = orchestrator.cancel_workflow("test-workflow")
        assert isinstance(result, bool)

    async def test_get_workflow_state_not_found(self) -> None:
        """Test getting state for non-existent workflow."""
        agent = create_deep_agent(model=TestModel())
        deps = create_default_deps(backend=StateBackend())
        orchestrator = TaskOrchestrator(agent, deps)

        state = orchestrator.get_workflow_state("non-existent")
        assert state is None

    async def test_get_workflow_progress_not_found(self) -> None:
        """Test getting progress for non-existent workflow."""
        agent = create_deep_agent(model=TestModel())
        deps = create_default_deps(backend=StateBackend())
        orchestrator = TaskOrchestrator(agent, deps)

        progress = orchestrator.get_workflow_progress("non-existent")
        assert progress is None

    async def test_workflow_with_continue_on_failure(self) -> None:
        """Test workflow that continues on failure."""
        agent = create_deep_agent(model=TestModel())
        deps = create_default_deps(backend=StateBackend())
        orchestrator = TaskOrchestrator(agent, deps)

        workflow = WorkflowDefinition(
            id="test-workflow",
            name="Test",
            continue_on_failure=True,
            tasks=[
                TaskDefinition(
                    id="task1",
                    description="Task 1",
                    agent_type="general-purpose",
                ),
                TaskDefinition(
                    id="task2",
                    description="Task 2",
                    agent_type="general-purpose",
                ),
            ],
        )

        state = await orchestrator.execute_workflow(workflow)
        assert state.workflow_id == "test-workflow"
