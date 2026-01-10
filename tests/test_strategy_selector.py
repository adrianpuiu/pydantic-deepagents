"""Tests for automatic strategy selection."""

from pydantic_deep.orchestration.models import ExecutionStrategy, TaskDefinition, WorkflowDefinition
from pydantic_deep.orchestration.strategy_selector import (
    analyze_workflow,
    auto_select_strategy,
    explain_strategy_choice,
    recommend_strategy,
)


class TestAnalyzeWorkflow:
    """Tests for workflow analysis."""

    def test_analyze_empty_workflow(self) -> None:
        """Test analyzing empty workflow."""
        workflow = WorkflowDefinition(id="test", name="Test", tasks=[])
        analysis = analyze_workflow(workflow)

        assert analysis["task_count"] == 0
        assert not analysis["has_dependencies"]
        assert not analysis["has_conditions"]
        assert analysis["total_dependencies"] == 0

    def test_analyze_independent_tasks(self) -> None:
        """Test analyzing workflow with independent tasks."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2"),
                TaskDefinition(id="task3", description="Task 3"),
            ],
        )
        analysis = analyze_workflow(workflow)

        assert analysis["task_count"] == 3
        assert not analysis["has_dependencies"]
        assert not analysis["has_conditions"]
        assert analysis["independent_tasks"] == 3
        assert analysis["can_parallelize"]

    def test_analyze_tasks_with_dependencies(self) -> None:
        """Test analyzing workflow with dependencies."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2", depends_on=["task1"]),
                TaskDefinition(id="task3", description="Task 3", depends_on=["task1", "task2"]),
            ],
        )
        analysis = analyze_workflow(workflow)

        assert analysis["task_count"] == 3
        assert analysis["has_dependencies"]
        assert analysis["total_dependencies"] == 3
        assert analysis["independent_tasks"] == 1
        assert analysis["can_parallelize"]

    def test_analyze_tasks_with_conditions(self) -> None:
        """Test analyzing workflow with conditions."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2", condition="task1"),
            ],
        )
        analysis = analyze_workflow(workflow)

        assert analysis["task_count"] == 2
        assert analysis["has_conditions"]


class TestRecommendStrategy:
    """Tests for strategy recommendation."""

    def test_recommend_empty_workflow(self) -> None:
        """Test recommendation for empty workflow."""
        workflow = WorkflowDefinition(id="test", name="Test", tasks=[])
        strategy = recommend_strategy(workflow)

        assert strategy == ExecutionStrategy.SEQUENTIAL

    def test_recommend_single_task(self) -> None:
        """Test recommendation for single task."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[TaskDefinition(id="task1", description="Task 1")],
        )
        strategy = recommend_strategy(workflow)

        assert strategy == ExecutionStrategy.SEQUENTIAL

    def test_recommend_independent_tasks(self) -> None:
        """Test recommendation for independent tasks."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2"),
                TaskDefinition(id="task3", description="Task 3"),
            ],
        )
        strategy = recommend_strategy(workflow)

        assert strategy == ExecutionStrategy.PARALLEL

    def test_recommend_tasks_with_dependencies(self) -> None:
        """Test recommendation for tasks with dependencies."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2", depends_on=["task1"]),
                TaskDefinition(id="task3", description="Task 3", depends_on=["task1"]),
            ],
        )
        strategy = recommend_strategy(workflow)

        assert strategy == ExecutionStrategy.DAG

    def test_recommend_conditional_tasks(self) -> None:
        """Test recommendation for conditional tasks."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2", condition="task1"),
            ],
        )
        strategy = recommend_strategy(workflow)

        assert strategy == ExecutionStrategy.CONDITIONAL


class TestAutoSelectStrategy:
    """Tests for automatic strategy selection."""

    def test_auto_select_with_explicit_strategy(self) -> None:
        """Test that explicit strategy is respected."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            execution_strategy=ExecutionStrategy.SEQUENTIAL,
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2"),
            ],
        )
        strategy = auto_select_strategy(workflow)

        # Should use explicit strategy
        assert strategy == ExecutionStrategy.SEQUENTIAL

    def test_auto_select_with_default_strategy(self) -> None:
        """Test that default strategy is analyzed."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            # Default is DAG, so auto-select will analyze
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2"),
            ],
        )
        strategy = auto_select_strategy(workflow)

        # Should recommend PARALLEL for independent tasks
        assert strategy == ExecutionStrategy.PARALLEL


class TestExplainStrategyChoice:
    """Tests for strategy explanation."""

    def test_explain_independent_tasks(self) -> None:
        """Test explanation for independent tasks."""
        workflow = WorkflowDefinition(
            id="test",
            name="Test Workflow",
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2"),
            ],
        )
        explanation = explain_strategy_choice(workflow)

        assert "Test Workflow" in explanation
        assert "Tasks: 2" in explanation
        assert "PARALLEL" in explanation or "parallel" in explanation

    def test_explain_tasks_with_dependencies(self) -> None:
        """Test explanation for tasks with dependencies."""
        workflow = WorkflowDefinition(
            id="test",
            name="Build Pipeline",
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2", depends_on=["task1"]),
            ],
        )
        explanation = explain_strategy_choice(workflow)

        assert "Build Pipeline" in explanation
        assert "Has dependencies: True" in explanation
        assert "DAG" in explanation or "dag" in explanation

    def test_explain_conditional_tasks(self) -> None:
        """Test explanation for conditional tasks."""
        workflow = WorkflowDefinition(
            id="test",
            name="Conditional Workflow",
            tasks=[
                TaskDefinition(id="task1", description="Task 1"),
                TaskDefinition(id="task2", description="Task 2", condition="task1"),
            ],
        )
        explanation = explain_strategy_choice(workflow)

        assert "Conditional Workflow" in explanation
        assert "Has conditions: True" in explanation
        assert "CONDITIONAL" in explanation or "conditional" in explanation
