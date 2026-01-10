"""Example demonstrating execution strategy selection.

This example shows:
1. Manual strategy selection (explicit control)
2. Automatic strategy selection (intelligent defaults)
3. Strategy recommendation and explanation
"""

import asyncio

from pydantic_ai_backends import StateBackend

from pydantic_deep import (
    ExecutionStrategy,
    TaskDefinition,
    TaskOrchestrator,
    WorkflowDefinition,
    create_deep_agent,
    create_default_deps,
)
from pydantic_deep.orchestration import (
    explain_strategy_choice,
    recommend_strategy,
)


async def manual_strategy_example() -> None:
    """Example of manually specifying execution strategy."""
    print("=" * 60)
    print("MANUAL STRATEGY SELECTION")
    print("=" * 60)

    agent = create_deep_agent(model="openai:gpt-4o-mini")
    deps = create_default_deps(backend=StateBackend())
    orchestrator = TaskOrchestrator(agent, deps)

    # Explicitly specify SEQUENTIAL strategy
    workflow = WorkflowDefinition(
        id="manual-sequential",
        name="Manual Sequential Workflow",
        execution_strategy=ExecutionStrategy.SEQUENTIAL,  # ← Explicit choice
        tasks=[
            TaskDefinition(id="task1", description="First task"),
            TaskDefinition(id="task2", description="Second task"),
            TaskDefinition(id="task3", description="Third task"),
        ],
    )

    print(f"\n✓ Created workflow with EXPLICIT strategy: {workflow.execution_strategy.value}")
    print(f"  Tasks will execute one by one in order\n")

    result = await orchestrator.execute_workflow(workflow)
    print(f"✓ Workflow completed: {result.status}")


async def automatic_strategy_example() -> None:
    """Example of automatic strategy selection."""
    print("\n" + "=" * 60)
    print("AUTOMATIC STRATEGY SELECTION")
    print("=" * 60)

    agent = create_deep_agent(model="openai:gpt-4o-mini")
    deps = create_default_deps(backend=StateBackend())
    orchestrator = TaskOrchestrator(agent, deps)

    # Define workflow WITHOUT explicit strategy (or use default)
    workflow = WorkflowDefinition(
        id="auto-workflow",
        name="Auto-Selected Workflow",
        # No execution_strategy specified - will use default (DAG)
        # But we'll use auto_strategy=True to analyze and optimize
        tasks=[
            TaskDefinition(id="task1", description="Independent task 1"),
            TaskDefinition(id="task2", description="Independent task 2"),
            TaskDefinition(id="task3", description="Independent task 3"),
            TaskDefinition(id="task4", description="Independent task 4"),
        ],
    )

    # Get recommendation
    recommended = recommend_strategy(workflow)
    print(f"\n📊 Analyzing workflow characteristics...")
    print(f"   All tasks are independent (no dependencies)")
    print(f"   Recommended strategy: {recommended.value}")
    print(f"   Reason: Can run all tasks in parallel for faster execution\n")

    # Execute with automatic strategy selection
    result = await orchestrator.execute_workflow(workflow, auto_strategy=True)
    print(f"✓ Workflow completed: {result.status}")


async def strategy_explanation_example() -> None:
    """Example showing strategy explanation for different workflow types."""
    print("\n" + "=" * 60)
    print("STRATEGY RECOMMENDATIONS & EXPLANATIONS")
    print("=" * 60)

    # Example 1: Independent tasks → PARALLEL
    workflow1 = WorkflowDefinition(
        id="parallel-workflow",
        name="Data Processing Pipeline",
        tasks=[
            TaskDefinition(id=f"process-{i}", description=f"Process dataset {i}")
            for i in range(5)
        ],
    )

    print("\n" + "-" * 60)
    print("Workflow 1: Independent Data Processing Tasks")
    print("-" * 60)
    print(explain_strategy_choice(workflow1))

    # Example 2: Tasks with dependencies → DAG
    workflow2 = WorkflowDefinition(
        id="dag-workflow",
        name="Build Pipeline",
        tasks=[
            TaskDefinition(id="setup", description="Setup environment"),
            TaskDefinition(
                id="compile",
                description="Compile code",
                depends_on=["setup"],
            ),
            TaskDefinition(
                id="test",
                description="Run tests",
                depends_on=["setup"],
            ),
            TaskDefinition(
                id="package",
                description="Create package",
                depends_on=["compile", "test"],
            ),
        ],
    )

    print("\n" + "-" * 60)
    print("Workflow 2: Build Pipeline with Dependencies")
    print("-" * 60)
    print(explain_strategy_choice(workflow2))

    # Example 3: Conditional tasks → CONDITIONAL
    workflow3 = WorkflowDefinition(
        id="conditional-workflow",
        name="Quality Check Workflow",
        tasks=[
            TaskDefinition(id="analyze", description="Analyze code quality"),
            TaskDefinition(
                id="fix",
                description="Fix issues",
                condition="analyze",  # ← Conditional execution
                depends_on=["analyze"],
            ),
            TaskDefinition(
                id="verify",
                description="Verify fixes",
                depends_on=["fix"],
            ),
        ],
    )

    print("\n" + "-" * 60)
    print("Workflow 3: Quality Check with Conditions")
    print("-" * 60)
    print(explain_strategy_choice(workflow3))

    # Example 4: Single task → SEQUENTIAL
    workflow4 = WorkflowDefinition(
        id="single-workflow",
        name="Simple Task",
        tasks=[
            TaskDefinition(id="single-task", description="A single task"),
        ],
    )

    print("\n" + "-" * 60)
    print("Workflow 4: Single Task")
    print("-" * 60)
    print(explain_strategy_choice(workflow4))


async def comparison_example() -> None:
    """Compare manual vs automatic strategy selection."""
    print("\n" + "=" * 60)
    print("MANUAL vs AUTOMATIC COMPARISON")
    print("=" * 60)

    agent = create_deep_agent(model="openai:gpt-4o-mini")
    deps = create_default_deps(backend=StateBackend())
    orchestrator = TaskOrchestrator(agent, deps)

    # Create a workflow that would benefit from parallel execution
    tasks = [
        TaskDefinition(id=f"analyze-{i}", description=f"Analyze module {i}")
        for i in range(3)
    ]

    # Test 1: Manual SEQUENTIAL (suboptimal for this case)
    workflow_sequential = WorkflowDefinition(
        id="manual-seq",
        name="Manual Sequential",
        execution_strategy=ExecutionStrategy.SEQUENTIAL,
        tasks=tasks,
    )

    print("\n📝 Test 1: Manual SEQUENTIAL strategy")
    print("   (Suboptimal - tasks could run in parallel)")
    result1 = await orchestrator.execute_workflow(workflow_sequential)
    print(f"   ✓ Completed in {(result1.completed_at - result1.started_at).total_seconds():.2f}s" if result1.completed_at and result1.started_at else "   ✓ Completed")

    # Test 2: Automatic selection (will choose PARALLEL)
    workflow_auto = WorkflowDefinition(
        id="auto-sel",
        name="Auto Selected",
        tasks=tasks,
    )

    print("\n🤖 Test 2: Automatic strategy selection")
    recommended = recommend_strategy(workflow_auto)
    print(f"   Recommended: {recommended.value}")
    print(f"   (Optimal - recognizes independent tasks)")
    result2 = await orchestrator.execute_workflow(workflow_auto, auto_strategy=True)
    print(f"   ✓ Completed in {(result2.completed_at - result2.started_at).total_seconds():.2f}s" if result2.completed_at and result2.started_at else "   ✓ Completed")


async def main() -> None:
    """Run all strategy selection examples."""
    # Example 1: Manual strategy
    await manual_strategy_example()

    # Example 2: Automatic strategy
    await automatic_strategy_example()

    # Example 3: Strategy explanations
    await strategy_explanation_example()

    # Example 4: Comparison
    await comparison_example()

    print("\n" + "=" * 60)
    print("📚 KEY TAKEAWAYS")
    print("=" * 60)
    print("""
1. MANUAL SELECTION (Default):
   - Full control over execution strategy
   - Specify: execution_strategy=ExecutionStrategy.XXX
   - Best when you know the optimal approach

2. AUTOMATIC SELECTION:
   - System analyzes workflow characteristics
   - Use: auto_strategy=True when executing
   - Best for dynamic workflows or quick prototyping

3. STRATEGY TYPES:
   - SEQUENTIAL: One task at a time (safe default)
   - PARALLEL: All tasks concurrently (independent tasks)
   - DAG: Dependency-aware parallel (complex workflows)
   - CONDITIONAL: Runtime condition-based (conditional tasks)

4. RECOMMENDATION:
   - Start with auto_strategy=True during development
   - Profile and optimize with explicit strategies in production
   - Use explain_strategy_choice() to understand recommendations
    """)


if __name__ == "__main__":
    asyncio.run(main())
