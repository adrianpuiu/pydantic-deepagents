"""DAG visualization for orchestration workflows.

This module provides multiple visualization formats for workflow DAGs,
making it easy to understand complex workflows and debug execution issues.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any

from pydantic_deep.orchestration.models import (
    TaskDefinition,
    TaskStatus,
    WorkflowDefinition,
    WorkflowState,
)


class VisualizationFormat(str, Enum):
    """Supported visualization formats."""

    MERMAID = "mermaid"  # Mermaid markdown diagram
    GRAPHVIZ = "graphviz"  # Graphviz DOT format
    ASCII = "ascii"  # ASCII art for terminal
    JSON = "json"  # JSON structure for custom rendering


class DAGVisualizer:
    """Generates visual representations of workflow DAGs."""

    def __init__(
        self,
        workflow: WorkflowDefinition,
        state: WorkflowState | None = None,
    ) -> None:
        """Initialize DAG visualizer.

        Args:
            workflow: Workflow definition to visualize.
            state: Optional workflow state for execution status.
        """
        self.workflow = workflow
        self.state = state

    def visualize(
        self,
        format: VisualizationFormat = VisualizationFormat.MERMAID,
        include_metrics: bool = False,
    ) -> str:
        """Generate visualization in specified format.

        Args:
            format: Output format for visualization.
            include_metrics: Whether to include execution metrics.

        Returns:
            Visualization as string.
        """
        if format == VisualizationFormat.MERMAID:
            return self._generate_mermaid(include_metrics)
        elif format == VisualizationFormat.GRAPHVIZ:
            return self._generate_graphviz(include_metrics)
        elif format == VisualizationFormat.ASCII:
            return self._generate_ascii(include_metrics)
        elif format == VisualizationFormat.JSON:
            return self._generate_json(include_metrics)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_mermaid(self, include_metrics: bool) -> str:
        """Generate Mermaid diagram.

        Args:
            include_metrics: Whether to include execution metrics.

        Returns:
            Mermaid markdown string.
        """
        lines = ["```mermaid", "graph TD"]

        # Add nodes
        for task in self.workflow.tasks:
            node_id = self._sanitize_id(task.id)
            label = task.id

            # Add metrics if available
            if include_metrics and self.state:
                result = self.state.task_results.get(task.id)
                if result:
                    duration = f"{result.duration_seconds:.1f}s" if result.duration_seconds else "?"
                    label = f"{task.id}<br/>{duration}"

            # Style based on status
            status = self._get_task_status(task.id)
            node_style = self._get_mermaid_style(status)

            lines.append(f"    {node_id}[{label}]{node_style}")

        # Add edges (dependencies)
        for task in self.workflow.tasks:
            node_id = self._sanitize_id(task.id)
            for dep_id in task.depends_on:
                dep_node_id = self._sanitize_id(dep_id)
                lines.append(f"    {dep_node_id} --> {node_id}")

        # Add styling
        lines.extend(
            [
                "",
                "    classDef completed fill:#90EE90,stroke:#006400,stroke-width:2px",
                "    classDef failed fill:#FFB6C1,stroke:#8B0000,stroke-width:2px",
                "    classDef running fill:#87CEEB,stroke:#00008B,stroke-width:2px",
                "    classDef pending fill:#F0E68C,stroke:#8B8B00,stroke-width:2px",
                "```",
            ]
        )

        return "\n".join(lines)

    def _generate_graphviz(self, include_metrics: bool) -> str:
        """Generate Graphviz DOT format.

        Args:
            include_metrics: Whether to include execution metrics.

        Returns:
            DOT format string.
        """
        lines = [
            "digraph Workflow {",
            "    rankdir=TB;",
            "    node [shape=box, style=rounded];",
            "",
        ]

        # Add nodes
        for task in self.workflow.tasks:
            node_id = self._sanitize_id(task.id)
            label = task.id

            # Add metrics
            if include_metrics and self.state:
                result = self.state.task_results.get(task.id)
                if result and result.duration_seconds:
                    label = f"{task.id}\\n{result.duration_seconds:.1f}s"

            # Style based on status
            status = self._get_task_status(task.id)
            color, fillcolor = self._get_graphviz_colors(status)

            lines.append(
                f'    {node_id} [label="{label}", color="{color}", '
                f'fillcolor="{fillcolor}", style="filled,rounded"];'
            )

        lines.append("")

        # Add edges
        for task in self.workflow.tasks:
            node_id = self._sanitize_id(task.id)
            for dep_id in task.depends_on:
                dep_node_id = self._sanitize_id(dep_id)
                lines.append(f"    {dep_node_id} -> {node_id};")

        lines.append("}")

        return "\n".join(lines)

    def _generate_ascii(self, include_metrics: bool) -> str:
        """Generate ASCII art diagram.

        Args:
            include_metrics: Whether to include execution metrics.

        Returns:
            ASCII art string.
        """
        lines = [
            f"Workflow: {self.workflow.name}",
            f"Strategy: {self.workflow.execution_strategy}",
            "=" * 70,
            "",
        ]

        # Group tasks by level (topological ordering)
        levels = self._compute_task_levels()

        for level, task_ids in enumerate(levels):
            if level > 0:
                lines.append("    ↓")

            lines.append(f"Level {level}:")
            for task_id in task_ids:
                task = next(t for t in self.workflow.tasks if t.id == task_id)
                status = self._get_task_status(task_id)
                status_symbol = self._get_ascii_symbol(status)

                line = f"  {status_symbol} {task.id}"

                # Add metrics
                if include_metrics and self.state:
                    result = self.state.task_results.get(task_id)
                    if result and result.duration_seconds:
                        line += f" ({result.duration_seconds:.1f}s)"

                # Add dependencies
                if task.depends_on:
                    line += f" [depends: {', '.join(task.depends_on)}]"

                lines.append(line)

        lines.append("")
        lines.append("Legend:")
        lines.append("  ✓ Completed")
        lines.append("  ✗ Failed")
        lines.append("  ⟳ Running")
        lines.append("  ○ Pending")

        return "\n".join(lines)

    def _generate_json(self, include_metrics: bool) -> str:
        """Generate JSON representation.

        Args:
            include_metrics: Whether to include execution metrics.

        Returns:
            JSON string.
        """
        nodes = []
        edges = []

        for task in self.workflow.tasks:
            node = {
                "id": task.id,
                "description": task.description,
                "capabilities": [str(c) for c in task.required_capabilities],
                "skills": task.required_skills,
                "priority": task.priority,
            }

            # Add status
            status = self._get_task_status(task.id)
            if status:
                node["status"] = status

            # Add metrics
            if include_metrics and self.state:
                result = self.state.task_results.get(task.id)
                if result:
                    node["metrics"] = {
                        "duration_seconds": result.duration_seconds,
                        "retry_count": result.retry_count,
                        "agent_used": result.agent_used,
                    }
                    if result.error:
                        node["error"] = result.error

            nodes.append(node)

            # Add edges
            for dep_id in task.depends_on:
                edges.append({"from": dep_id, "to": task.id})

        data = {
            "workflow": {
                "id": self.workflow.id,
                "name": self.workflow.name,
                "strategy": self.workflow.execution_strategy,
            },
            "nodes": nodes,
            "edges": edges,
        }

        if self.state:
            data["workflow"]["status"] = self.state.status
            if self.state.started_at:
                data["workflow"]["started_at"] = self.state.started_at.isoformat()
            if self.state.completed_at:
                data["workflow"]["completed_at"] = self.state.completed_at.isoformat()

        return json.dumps(data, indent=2)

    def _get_task_status(self, task_id: str) -> str | None:
        """Get status of a task.

        Args:
            task_id: ID of the task.

        Returns:
            Task status string or None.
        """
        if not self.state:
            return None

        result = self.state.task_results.get(task_id)
        if result:
            return result.status

        # Check if task is in various lists
        if task_id in self.state.completed_tasks:
            return TaskStatus.COMPLETED
        elif task_id in self.state.failed_tasks:
            return TaskStatus.FAILED
        elif task_id in self.state.pending_tasks:
            return TaskStatus.PENDING
        elif task_id in self.state.running_tasks:
            return TaskStatus.RUNNING

        return TaskStatus.PENDING

    def _get_mermaid_style(self, status: str | None) -> str:
        """Get Mermaid style class for status.

        Args:
            status: Task status.

        Returns:
            Mermaid class directive.
        """
        if not status:
            return ""

        if status == TaskStatus.COMPLETED:
            return ":::completed"
        elif status == TaskStatus.FAILED:
            return ":::failed"
        elif status == TaskStatus.RUNNING:
            return ":::running"
        else:
            return ":::pending"

    def _get_graphviz_colors(self, status: str | None) -> tuple[str, str]:
        """Get Graphviz colors for status.

        Args:
            status: Task status.

        Returns:
            Tuple of (border_color, fill_color).
        """
        if not status:
            return ("black", "white")

        if status == TaskStatus.COMPLETED:
            return ("darkgreen", "lightgreen")
        elif status == TaskStatus.FAILED:
            return ("darkred", "lightpink")
        elif status == TaskStatus.RUNNING:
            return ("darkblue", "lightblue")
        else:
            return ("goldenrod", "lightyellow")

    def _get_ascii_symbol(self, status: str | None) -> str:
        """Get ASCII symbol for status.

        Args:
            status: Task status.

        Returns:
            ASCII symbol character.
        """
        if not status:
            return "○"

        if status == TaskStatus.COMPLETED:
            return "✓"
        elif status == TaskStatus.FAILED:
            return "✗"
        elif status == TaskStatus.RUNNING:
            return "⟳"
        else:
            return "○"

    def _sanitize_id(self, task_id: str) -> str:
        """Sanitize task ID for use in diagrams.

        Args:
            task_id: Task ID to sanitize.

        Returns:
            Sanitized ID.
        """
        # Replace characters that might cause issues
        return task_id.replace("-", "_").replace(".", "_").replace(" ", "_")

    def _compute_task_levels(self) -> list[list[str]]:
        """Compute task levels for topological visualization.

        Returns:
            List of task ID lists, grouped by execution level.
        """
        # Build dependency graph
        deps = {task.id: set(task.depends_on) for task in self.workflow.tasks}
        all_tasks = {task.id for task in self.workflow.tasks}

        levels: list[list[str]] = []
        assigned = set()

        while len(assigned) < len(all_tasks):
            # Find tasks with all dependencies satisfied
            current_level = []
            for task_id in all_tasks:
                if task_id in assigned:
                    continue
                if not deps[task_id] or deps[task_id].issubset(assigned):
                    current_level.append(task_id)

            if not current_level:
                # Circular dependency or error
                remaining = all_tasks - assigned
                levels.append(list(remaining))
                break

            levels.append(sorted(current_level))
            assigned.update(current_level)

        return levels


def visualize_workflow(
    workflow: WorkflowDefinition,
    state: WorkflowState | None = None,
    format: VisualizationFormat = VisualizationFormat.MERMAID,
    include_metrics: bool = False,
) -> str:
    """Quick function to visualize a workflow.

    Args:
        workflow: Workflow to visualize.
        state: Optional workflow execution state.
        format: Visualization format.
        include_metrics: Whether to include execution metrics.

    Returns:
        Visualization string.

    Example:
        ```python
        from pydantic_deep import visualize_workflow, WorkflowDefinition

        # Visualize workflow
        diagram = visualize_workflow(workflow, format="mermaid")
        print(diagram)

        # Visualize with execution state
        diagram = visualize_workflow(workflow, state, include_metrics=True)
        ```
    """
    visualizer = DAGVisualizer(workflow, state)
    return visualizer.visualize(format, include_metrics)


__all__ = [
    "DAGVisualizer",
    "VisualizationFormat",
    "visualize_workflow",
]
