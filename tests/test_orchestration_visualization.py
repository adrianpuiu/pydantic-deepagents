"""Tests for orchestration DAG visualization."""

from __future__ import annotations

from datetime import datetime

import pytest

from pydantic_deep.orchestration.models import (
    ExecutionStrategy,
    TaskDefinition,
    TaskResult,
    TaskStatus,
    WorkflowDefinition,
    WorkflowState,
)
from pydantic_deep.orchestration.visualization import (
    DAGVisualizer,
    VisualizationFormat,
    visualize_workflow,
)


def create_simple_workflow() -> WorkflowDefinition:
    """Create a simple workflow for testing."""
    return WorkflowDefinition(
        id="test-workflow",
        name="Test Workflow",
        execution_strategy=ExecutionStrategy.DAG,
        tasks=[
            TaskDefinition(id="task1", description="First task"),
            TaskDefinition(
                id="task2",
                description="Second task",
                depends_on=["task1"],
            ),
            TaskDefinition(
                id="task3",
                description="Third task",
                depends_on=["task1"],
            ),
            TaskDefinition(
                id="task4",
                description="Fourth task",
                depends_on=["task2", "task3"],
            ),
        ],
    )


def create_workflow_state(workflow: WorkflowDefinition) -> WorkflowState:
    """Create workflow state with some completed tasks."""
    now = datetime.now()

    return WorkflowState(
        workflow_id=workflow.id,
        status="running",
        started_at=now,
        task_results={
            "task1": TaskResult(
                task_id="task1",
                status=TaskStatus.COMPLETED,
                output="Result 1",
                started_at=now,
                completed_at=now,
                duration_seconds=2.5,
            ),
            "task2": TaskResult(
                task_id="task2",
                status=TaskStatus.RUNNING,
                output=None,
                started_at=now,
            ),
            "task3": TaskResult(
                task_id="task3",
                status=TaskStatus.FAILED,
                error="Task failed",
                started_at=now,
                completed_at=now,
                duration_seconds=1.0,
            ),
        },
        completed_tasks=["task1"],
        failed_tasks=["task3"],
        running_tasks=["task2"],
        pending_tasks=["task4"],
    )


def test_visualizer_initialization():
    """Test DAGVisualizer initialization."""
    workflow = create_simple_workflow()
    visualizer = DAGVisualizer(workflow)

    assert visualizer.workflow == workflow
    assert visualizer.state is None


def test_visualizer_with_state():
    """Test DAGVisualizer with workflow state."""
    workflow = create_simple_workflow()
    state = create_workflow_state(workflow)
    visualizer = DAGVisualizer(workflow, state)

    assert visualizer.state == state


def test_mermaid_generation():
    """Test Mermaid diagram generation."""
    workflow = create_simple_workflow()
    visualizer = DAGVisualizer(workflow)

    diagram = visualizer.visualize(VisualizationFormat.MERMAID)

    assert "```mermaid" in diagram
    assert "graph TD" in diagram
    assert "task1" in diagram
    assert "task2" in diagram
    assert "task3" in diagram
    assert "task4" in diagram
    # Check dependencies
    assert "task1 --> task2" in diagram
    assert "task1 --> task3" in diagram
    assert "task2 --> task4" in diagram
    assert "task3 --> task4" in diagram


def test_mermaid_with_status_styling():
    """Test Mermaid diagram includes status styling."""
    workflow = create_simple_workflow()
    state = create_workflow_state(workflow)
    visualizer = DAGVisualizer(workflow, state)

    diagram = visualizer.visualize(VisualizationFormat.MERMAID)

    # Should include style classes
    assert ":::completed" in diagram or "classDef completed" in diagram
    assert "classDef failed" in diagram
    assert "classDef running" in diagram
    assert "classDef pending" in diagram


def test_mermaid_with_metrics():
    """Test Mermaid diagram includes metrics."""
    workflow = create_simple_workflow()
    state = create_workflow_state(workflow)
    visualizer = DAGVisualizer(workflow, state)

    diagram = visualizer.visualize(VisualizationFormat.MERMAID, include_metrics=True)

    # Should include task durations
    assert "2.5s" in diagram  # task1 duration
    assert "1.0s" in diagram  # task3 duration


def test_graphviz_generation():
    """Test Graphviz DOT format generation."""
    workflow = create_simple_workflow()
    visualizer = DAGVisualizer(workflow)

    diagram = visualizer.visualize(VisualizationFormat.GRAPHVIZ)

    assert "digraph Workflow" in diagram
    assert "rankdir=TB" in diagram
    assert "task1" in diagram
    assert "task2" in diagram
    assert "task1 -> task2" in diagram
    assert "task2 -> task4" in diagram


def test_graphviz_with_status_colors():
    """Test Graphviz diagram includes status colors."""
    workflow = create_simple_workflow()
    state = create_workflow_state(workflow)
    visualizer = DAGVisualizer(workflow, state)

    diagram = visualizer.visualize(VisualizationFormat.GRAPHVIZ)

    # Should include color specifications
    assert "color=" in diagram
    assert "fillcolor=" in diagram
    assert "lightgreen" in diagram  # completed
    assert "lightpink" in diagram  # failed
    assert "lightblue" in diagram  # running


def test_graphviz_with_metrics():
    """Test Graphviz includes metrics in labels."""
    workflow = create_simple_workflow()
    state = create_workflow_state(workflow)
    visualizer = DAGVisualizer(workflow, state)

    diagram = visualizer.visualize(VisualizationFormat.GRAPHVIZ, include_metrics=True)

    # Should include durations in labels
    assert "2.5s" in diagram
    assert "1.0s" in diagram


def test_ascii_generation():
    """Test ASCII art generation."""
    workflow = create_simple_workflow()
    visualizer = DAGVisualizer(workflow)

    diagram = visualizer.visualize(VisualizationFormat.ASCII)

    assert "Workflow: Test Workflow" in diagram
    assert "Strategy: ExecutionStrategy.DAG" in diagram
    assert "Level 0:" in diagram
    assert "Level 1:" in diagram
    assert "task1" in diagram
    assert "task2" in diagram
    assert "task4" in diagram


def test_ascii_with_status_symbols():
    """Test ASCII diagram includes status symbols."""
    workflow = create_simple_workflow()
    state = create_workflow_state(workflow)
    visualizer = DAGVisualizer(workflow, state)

    diagram = visualizer.visualize(VisualizationFormat.ASCII)

    # Should include status symbols
    assert "✓" in diagram  # completed
    assert "✗" in diagram  # failed
    assert "⟳" in diagram  # running
    assert "○" in diagram  # pending

    # Should include legend
    assert "Legend:" in diagram


def test_ascii_with_metrics():
    """Test ASCII includes metrics."""
    workflow = create_simple_workflow()
    state = create_workflow_state(workflow)
    visualizer = DAGVisualizer(workflow, state)

    diagram = visualizer.visualize(VisualizationFormat.ASCII, include_metrics=True)

    # Should include durations
    assert "(2.5s)" in diagram
    assert "(1.0s)" in diagram


def test_ascii_with_dependencies():
    """Test ASCII shows dependencies."""
    workflow = create_simple_workflow()
    visualizer = DAGVisualizer(workflow)

    diagram = visualizer.visualize(VisualizationFormat.ASCII)

    # Should show dependencies
    assert "[depends: task1]" in diagram or "depends" in diagram


def test_json_generation():
    """Test JSON format generation."""
    workflow = create_simple_workflow()
    visualizer = DAGVisualizer(workflow)

    diagram = visualizer.visualize(VisualizationFormat.JSON)

    import json

    data = json.loads(diagram)

    assert "workflow" in data
    assert data["workflow"]["id"] == "test-workflow"
    assert data["workflow"]["name"] == "Test Workflow"

    assert "nodes" in data
    assert len(data["nodes"]) == 4

    assert "edges" in data
    # Should have 4 edges (task1->task2, task1->task3, task2->task4, task3->task4)
    assert len(data["edges"]) == 4


def test_json_with_status():
    """Test JSON includes task status."""
    workflow = create_simple_workflow()
    state = create_workflow_state(workflow)
    visualizer = DAGVisualizer(workflow, state)

    diagram = visualizer.visualize(VisualizationFormat.JSON)

    import json

    data = json.loads(diagram)

    # Check that nodes have status
    task1_node = next(n for n in data["nodes"] if n["id"] == "task1")
    assert task1_node["status"] == TaskStatus.COMPLETED

    task3_node = next(n for n in data["nodes"] if n["id"] == "task3")
    assert task3_node["status"] == TaskStatus.FAILED


def test_json_with_metrics():
    """Test JSON includes metrics."""
    workflow = create_simple_workflow()
    state = create_workflow_state(workflow)
    visualizer = DAGVisualizer(workflow, state)

    diagram = visualizer.visualize(VisualizationFormat.JSON, include_metrics=True)

    import json

    data = json.loads(diagram)

    task1_node = next(n for n in data["nodes"] if n["id"] == "task1")
    assert "metrics" in task1_node
    assert task1_node["metrics"]["duration_seconds"] == 2.5


def test_json_with_workflow_timestamps():
    """Test JSON includes workflow timestamps."""
    workflow = create_simple_workflow()
    state = create_workflow_state(workflow)
    visualizer = DAGVisualizer(workflow, state)

    diagram = visualizer.visualize(VisualizationFormat.JSON)

    import json

    data = json.loads(diagram)

    assert "started_at" in data["workflow"]
    assert data["workflow"]["status"] == "running"


def test_task_level_computation():
    """Test topological level computation."""
    workflow = create_simple_workflow()
    visualizer = DAGVisualizer(workflow)

    levels = visualizer._compute_task_levels()

    # task1 should be level 0
    assert "task1" in levels[0]

    # task2 and task3 should be level 1
    assert "task2" in levels[1]
    assert "task3" in levels[1]

    # task4 should be level 2
    assert "task4" in levels[2]


def test_task_level_computation_no_dependencies():
    """Test level computation with no dependencies."""
    workflow = WorkflowDefinition(
        id="simple",
        name="Simple",
        execution_strategy=ExecutionStrategy.PARALLEL,
        tasks=[
            TaskDefinition(id="task1", description="Task 1"),
            TaskDefinition(id="task2", description="Task 2"),
            TaskDefinition(id="task3", description="Task 3"),
        ],
    )

    visualizer = DAGVisualizer(workflow)
    levels = visualizer._compute_task_levels()

    # All tasks should be at level 0 (no dependencies)
    assert len(levels[0]) == 3


def test_sanitize_id():
    """Test ID sanitization for diagram formats."""
    workflow = WorkflowDefinition(
        id="test",
        name="Test",
        execution_strategy=ExecutionStrategy.SEQUENTIAL,
        tasks=[
            TaskDefinition(id="task-with-dashes", description="Task"),
            TaskDefinition(id="task.with.dots", description="Task"),
            TaskDefinition(id="task with spaces", description="Task"),
        ],
    )

    visualizer = DAGVisualizer(workflow)

    # Test sanitization
    assert visualizer._sanitize_id("task-with-dashes") == "task_with_dashes"
    assert visualizer._sanitize_id("task.with.dots") == "task_with_dots"
    assert visualizer._sanitize_id("task with spaces") == "task_with_spaces"


def test_visualize_workflow_function():
    """Test the quick visualize_workflow function."""
    workflow = create_simple_workflow()

    # Test without state
    diagram = visualize_workflow(workflow, format=VisualizationFormat.MERMAID)
    assert "```mermaid" in diagram

    # Test with state
    state = create_workflow_state(workflow)
    diagram = visualize_workflow(workflow, state, format=VisualizationFormat.ASCII)
    assert "Workflow: Test Workflow" in diagram


def test_visualize_workflow_with_metrics():
    """Test visualize_workflow with metrics."""
    workflow = create_simple_workflow()
    state = create_workflow_state(workflow)

    diagram = visualize_workflow(
        workflow,
        state,
        format=VisualizationFormat.MERMAID,
        include_metrics=True,
    )

    assert "2.5s" in diagram


def test_complex_dag_visualization():
    """Test visualization of complex DAG."""
    workflow = WorkflowDefinition(
        id="complex",
        name="Complex Workflow",
        execution_strategy=ExecutionStrategy.DAG,
        tasks=[
            TaskDefinition(id="start", description="Start"),
            TaskDefinition(id="a", description="A", depends_on=["start"]),
            TaskDefinition(id="b", description="B", depends_on=["start"]),
            TaskDefinition(id="c", description="C", depends_on=["a", "b"]),
            TaskDefinition(id="d", description="D", depends_on=["a"]),
            TaskDefinition(id="e", description="E", depends_on=["c", "d"]),
        ],
    )

    visualizer = DAGVisualizer(workflow)

    # Test all formats work
    mermaid = visualizer.visualize(VisualizationFormat.MERMAID)
    assert "start" in mermaid
    assert "graph TD" in mermaid

    graphviz = visualizer.visualize(VisualizationFormat.GRAPHVIZ)
    assert "start" in graphviz
    assert "digraph" in graphviz

    ascii = visualizer.visualize(VisualizationFormat.ASCII)
    assert "start" in ascii
    assert "Level" in ascii

    json_str = visualizer.visualize(VisualizationFormat.JSON)
    import json

    data = json.loads(json_str)
    assert len(data["nodes"]) == 6


def test_visualization_with_error_information():
    """Test that visualization includes error information."""
    workflow = create_simple_workflow()
    state = create_workflow_state(workflow)
    visualizer = DAGVisualizer(workflow, state)

    # JSON should include error
    json_str = visualizer.visualize(VisualizationFormat.JSON, include_metrics=True)
    import json

    data = json.loads(json_str)

    task3_node = next(n for n in data["nodes"] if n["id"] == "task3")
    assert "error" in task3_node
    assert task3_node["error"] == "Task failed"


def test_unsupported_format_raises_error():
    """Test that unsupported format raises ValueError."""
    workflow = create_simple_workflow()
    visualizer = DAGVisualizer(workflow)

    with pytest.raises(ValueError, match="Unsupported format"):
        visualizer.visualize("unsupported")  # type: ignore
