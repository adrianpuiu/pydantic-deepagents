"""Automatic execution strategy selection.

This module provides utilities for automatically selecting the optimal
execution strategy based on workflow characteristics.
"""

from __future__ import annotations

from pydantic_deep.orchestration.models import ExecutionStrategy, WorkflowDefinition


def analyze_workflow(workflow: WorkflowDefinition) -> dict[str, bool | int]:
    """Analyze workflow characteristics.

    Args:
        workflow: Workflow to analyze.

    Returns:
        Dictionary with workflow characteristics.
    """
    has_dependencies = any(len(task.depends_on) > 0 for task in workflow.tasks)
    has_conditions = any(task.condition is not None for task in workflow.tasks)

    # Calculate dependency graph complexity
    total_deps = sum(len(task.depends_on) for task in workflow.tasks)
    avg_deps_per_task = total_deps / len(workflow.tasks) if workflow.tasks else 0

    # Check for independent tasks
    independent_tasks = sum(1 for task in workflow.tasks if len(task.depends_on) == 0)

    # Check if tasks can run in parallel
    can_parallelize = independent_tasks > 1 or (has_dependencies and independent_tasks > 0)

    return {
        "task_count": len(workflow.tasks),
        "has_dependencies": has_dependencies,
        "has_conditions": has_conditions,
        "total_dependencies": total_deps,
        "avg_dependencies_per_task": avg_deps_per_task,
        "independent_tasks": independent_tasks,
        "can_parallelize": can_parallelize,
    }


def recommend_strategy(workflow: WorkflowDefinition) -> ExecutionStrategy:
    """Recommend optimal execution strategy for a workflow.

    Decision logic:
    1. If workflow has conditions → CONDITIONAL
    2. If no dependencies and multiple tasks → PARALLEL
    3. If has dependencies → DAG
    4. Otherwise → SEQUENTIAL (simple, safe default)

    Args:
        workflow: Workflow to analyze.

    Returns:
        Recommended execution strategy.
    """
    if not workflow.tasks:
        return ExecutionStrategy.SEQUENTIAL

    analysis = analyze_workflow(workflow)

    # Priority 1: Conditional execution if conditions present
    if analysis["has_conditions"]:
        return ExecutionStrategy.CONDITIONAL

    # Priority 2: No dependencies = pure parallel execution
    if not analysis["has_dependencies"]:
        if analysis["task_count"] > 1:
            return ExecutionStrategy.PARALLEL
        else:
            return ExecutionStrategy.SEQUENTIAL

    # Priority 3: Has dependencies = DAG for optimal parallelism
    if analysis["has_dependencies"]:
        return ExecutionStrategy.DAG

    # Default: Sequential (safest)
    return ExecutionStrategy.SEQUENTIAL


def auto_select_strategy(workflow: WorkflowDefinition) -> ExecutionStrategy:
    """Automatically select execution strategy if not explicitly set.

    This function checks if the workflow has an explicitly set strategy.
    If the strategy is set to AUTO (or None in future versions), it will
    analyze the workflow and recommend the optimal strategy.

    Args:
        workflow: Workflow definition.

    Returns:
        Selected execution strategy.
    """
    # If already explicitly set, use that
    if workflow.execution_strategy != ExecutionStrategy.DAG:
        # User has made an explicit choice (not default)
        return workflow.execution_strategy

    # Otherwise, analyze and recommend
    return recommend_strategy(workflow)


def explain_strategy_choice(workflow: WorkflowDefinition) -> str:
    """Generate human-readable explanation of strategy choice.

    Args:
        workflow: Workflow to analyze.

    Returns:
        Explanation string.
    """
    analysis = analyze_workflow(workflow)
    recommended = recommend_strategy(workflow)

    explanation_parts = [
        f"Workflow '{workflow.name}' analysis:",
        f"  - Tasks: {analysis['task_count']}",
        f"  - Independent tasks: {analysis['independent_tasks']}",
        f"  - Has dependencies: {analysis['has_dependencies']}",
        f"  - Has conditions: {analysis['has_conditions']}",
        f"\nRecommended strategy: {recommended.value}",
    ]

    # Add reasoning
    if recommended == ExecutionStrategy.CONDITIONAL:
        explanation_parts.append(
            "  Reason: Workflow contains conditional tasks that require runtime evaluation"
        )
    elif recommended == ExecutionStrategy.PARALLEL:
        explanation_parts.append(
            "  Reason: All tasks are independent and can run concurrently"
        )
    elif recommended == ExecutionStrategy.DAG:
        explanation_parts.append(
            "  Reason: Workflow has dependencies - DAG enables optimal parallel execution"
        )
    else:
        explanation_parts.append(
            "  Reason: Simple workflow best suited for sequential execution"
        )

    return "\n".join(explanation_parts)
