"""Example demonstrating result caching and DAG visualization.

This example shows how to:
1. Enable result caching for performance
2. Configure different cache strategies
3. Visualize workflows in multiple formats
4. Monitor cache performance
5. Use caching with templates
"""

import asyncio

from pydantic_ai.models import TestModel

from pydantic_deep import (
    CacheConfig,
    CacheStrategy,
    DAGVisualizer,
    TaskDefinition,
    TaskOrchestrator,
    VisualizationFormat,
    WorkflowDefinition,
    create_deep_agent,
    create_default_deps,
    create_etl_pipeline,
    visualize_workflow,
)


async def example_basic_caching() -> None:
    """Demonstrate basic result caching."""
    print("=" * 70)
    print("BASIC RESULT CACHING")
    print("=" * 70)

    agent = create_deep_agent(model=TestModel())
    deps = create_default_deps()

    # Create orchestrator with caching enabled (default: memory cache)
    orchestrator = TaskOrchestrator(agent, deps)

    workflow = WorkflowDefinition(
        id="cached-workflow",
        name="Workflow with Caching",
        tasks=[
            TaskDefinition(
                id="expensive-task",
                description="This is an expensive computation",
                parameters={"input": "data"},
            ),
            TaskDefinition(
                id="another-task",
                description="Another expensive task",
                depends_on=["expensive-task"],
            ),
        ],
    )

    print("\n🚀 First execution (cache miss)...")
    await orchestrator.execute_workflow(workflow)

    # Get cache stats
    stats = orchestrator.get_cache_stats()
    print(f"\n📊 Cache Stats after first run:")
    print(f"   Hits: {stats['hits']}")
    print(f"   Misses: {stats['misses']}")
    print(f"   Hit Rate: {stats['hit_rate']}")

    print("\n🚀 Second execution (should use cache)...")
    await orchestrator.execute_workflow(workflow)

    # Get updated cache stats
    stats = orchestrator.get_cache_stats()
    print(f"\n📊 Cache Stats after second run:")
    print(f"   Hits: {stats['hits']}")
    print(f"   Misses: {stats['misses']}")
    print(f"   Hit Rate: {stats['hit_rate']}")
    print(f"\n   ✓ Cache hit! Task results retrieved instantly from cache")


async def example_cache_strategies() -> None:
    """Demonstrate different cache strategies."""
    print("\n\n" + "=" * 70)
    print("CACHE STRATEGIES")
    print("=" * 70)

    agent = create_deep_agent(model=TestModel())
    deps = create_default_deps()

    workflow = WorkflowDefinition(
        id="test",
        name="Test",
        tasks=[TaskDefinition(id="task1", description="Test task")],
    )

    # Strategy 1: Memory cache (default)
    print("\n1️⃣  MEMORY CACHE (fast, volatile)")
    cache_config = CacheConfig(
        strategy=CacheStrategy.MEMORY,
        max_size=1000,
    )
    orchestrator = TaskOrchestrator(agent, deps, cache_config=cache_config)
    await orchestrator.execute_workflow(workflow)
    print("   ✓ Results cached in memory")
    print("   ✓ Fast retrieval")
    print("   ✗ Lost when process ends")

    # Strategy 2: Disk cache
    print("\n2️⃣  DISK CACHE (persistent)")
    cache_config = CacheConfig(
        strategy=CacheStrategy.DISK,
        cache_dir=None,  # Uses default ~/.pydantic-deep/cache
    )
    orchestrator = TaskOrchestrator(agent, deps, cache_config=cache_config)
    await orchestrator.execute_workflow(workflow)
    print("   ✓ Results persisted to disk")
    print("   ✓ Survives process restarts")
    print("   ✗ Slower than memory")

    # Strategy 3: Hybrid cache
    print("\n3️⃣  HYBRID CACHE (best of both)")
    cache_config = CacheConfig(
        strategy=CacheStrategy.HYBRID,
        max_size=100,  # Memory cache limit
    )
    orchestrator = TaskOrchestrator(agent, deps, cache_config=cache_config)
    await orchestrator.execute_workflow(workflow)
    print("   ✓ Frequently used results in memory")
    print("   ✓ All results on disk")
    print("   ✓ Best performance + persistence")

    # Strategy 4: No cache
    print("\n4️⃣  NO CACHE (disabled)")
    cache_config = CacheConfig(strategy=CacheStrategy.NONE)
    orchestrator = TaskOrchestrator(agent, deps, cache_config=cache_config)
    await orchestrator.execute_workflow(workflow)
    print("   ✓ No caching overhead")
    print("   ✗ Always re-executes tasks")


async def example_cache_ttl() -> None:
    """Demonstrate cache TTL (time-to-live)."""
    print("\n\n" + "=" * 70)
    print("CACHE TTL (TIME-TO-LIVE)")
    print("=" * 70)

    agent = create_deep_agent(model=TestModel())
    deps = create_default_deps()

    # Cache with 5 second TTL
    cache_config = CacheConfig(
        strategy=CacheStrategy.MEMORY,
        ttl_seconds=5.0,
    )
    orchestrator = TaskOrchestrator(agent, deps, cache_config=cache_config)

    workflow = WorkflowDefinition(
        id="ttl-test",
        name="TTL Test",
        tasks=[TaskDefinition(id="task1", description="Task with TTL")],
    )

    print("\n🚀 First execution...")
    await orchestrator.execute_workflow(workflow)

    print("\n⏱️  Cache entry valid for 5 seconds")
    print("   ✓ Subsequent executions within 5s will use cache")
    print("   ✗ After 5s, cache entry expires and task re-executes")

    stats = orchestrator.get_cache_stats()
    print(f"\n📊 Cache Stats:")
    print(f"   Strategy: {stats['strategy']}")
    print(f"   Cache Size: {stats['cache_size']}")


async def example_cache_invalidation() -> None:
    """Demonstrate cache invalidation."""
    print("\n\n" + "=" * 70)
    print("CACHE INVALIDATION")
    print("=" * 70)

    agent = create_deep_agent(model=TestModel())
    deps = create_default_deps()
    orchestrator = TaskOrchestrator(agent, deps)

    workflow = WorkflowDefinition(
        id="invalidation-test",
        name="Invalidation Test",
        tasks=[
            TaskDefinition(id="task1", description="First task"),
            TaskDefinition(id="task2", description="Second task"),
        ],
    )

    # Execute and cache
    await orchestrator.execute_workflow(workflow)
    print("\n✓ Workflow executed and cached")

    stats = orchestrator.get_cache_stats()
    print(f"   Cache size: {stats['cache_size']}")

    # Invalidate specific task
    count = orchestrator.invalidate_cache("task1")
    print(f"\n🗑️  Invalidated {count} cache entries for 'task1'")

    # Clear entire cache
    orchestrator.clear_cache()
    print("🗑️  Cleared entire cache")

    stats = orchestrator.get_cache_stats()
    print(f"   Cache size: {stats['cache_size']}")


async def example_dag_visualization() -> None:
    """Demonstrate DAG visualization."""
    print("\n\n" + "=" * 70)
    print("DAG VISUALIZATION")
    print("=" * 70)

    # Create a complex workflow
    workflow = create_etl_pipeline(
        workflow_id="etl-viz",
        source_configs=[
            {"type": "csv", "path": "data.csv"},
            {"type": "api", "url": "https://api.example.com"},
        ],
        transformation_steps=["clean", "normalize"],
    )

    print(f"\n📋 Workflow: {workflow.name}")
    print(f"   Tasks: {len(workflow.tasks)}")

    # Format 1: Mermaid (for markdown/documentation)
    print("\n1️⃣  MERMAID FORMAT (for markdown)")
    print("=" * 70)
    mermaid = visualize_workflow(workflow, format=VisualizationFormat.MERMAID)
    print(mermaid)

    # Format 2: ASCII (for terminal)
    print("\n2️⃣  ASCII FORMAT (for terminal)")
    print("=" * 70)
    ascii_diagram = visualize_workflow(workflow, format=VisualizationFormat.ASCII)
    print(ascii_diagram)

    # Format 3: Graphviz/DOT
    print("\n3️⃣  GRAPHVIZ/DOT FORMAT")
    print("=" * 70)
    graphviz = visualize_workflow(workflow, format=VisualizationFormat.GRAPHVIZ)
    print(graphviz[:500] + "...")  # Show first 500 chars

    # Format 4: JSON (for custom rendering)
    print("\n4️⃣  JSON FORMAT (for custom rendering)")
    print("=" * 70)
    json_viz = visualize_workflow(workflow, format=VisualizationFormat.JSON)
    print(json_viz[:500] + "...")  # Show first 500 chars


async def example_visualization_with_state() -> None:
    """Demonstrate visualization with execution state."""
    print("\n\n" + "=" * 70)
    print("VISUALIZATION WITH EXECUTION STATE")
    print("=" * 70)

    agent = create_deep_agent(model=TestModel())
    deps = create_default_deps()
    orchestrator = TaskOrchestrator(agent, deps)

    workflow = WorkflowDefinition(
        id="state-viz",
        name="Workflow with State",
        tasks=[
            TaskDefinition(id="task1", description="First task"),
            TaskDefinition(id="task2", description="Second task", depends_on=["task1"]),
            TaskDefinition(id="task3", description="Third task", depends_on=["task1"]),
        ],
    )

    # Execute workflow
    print("\n🚀 Executing workflow...")
    result = await orchestrator.execute_workflow(workflow)

    # Visualize with execution state
    print("\n📊 ASCII Visualization with Status:")
    print("=" * 70)
    ascii_with_state = visualize_workflow(
        workflow,
        result,
        format=VisualizationFormat.ASCII,
        include_metrics=False,
    )
    print(ascii_with_state)

    # Visualize with metrics
    print("\n📊 ASCII Visualization with Metrics:")
    print("=" * 70)
    ascii_with_metrics = visualize_workflow(
        workflow,
        result,
        format=VisualizationFormat.ASCII,
        include_metrics=True,
    )
    print(ascii_with_metrics)

    # Mermaid with status coloring
    print("\n📊 Mermaid with Status Coloring:")
    print("=" * 70)
    mermaid_with_state = visualize_workflow(
        workflow,
        result,
        format=VisualizationFormat.MERMAID,
        include_metrics=True,
    )
    print(mermaid_with_state)


async def example_caching_with_templates() -> None:
    """Demonstrate caching with workflow templates."""
    print("\n\n" + "=" * 70)
    print("CACHING WITH WORKFLOW TEMPLATES")
    print("=" * 70)

    agent = create_deep_agent(model=TestModel())
    deps = create_default_deps()

    # Enable caching with hybrid strategy
    cache_config = CacheConfig(
        strategy=CacheStrategy.HYBRID,
        ttl_seconds=300,  # 5 minute TTL
    )
    orchestrator = TaskOrchestrator(agent, deps, cache_config=cache_config)

    # Use ETL template
    workflow = create_etl_pipeline(
        workflow_id="cached-etl",
        source_configs=[{"type": "csv", "path": "data.csv"}],
        transformation_steps=["clean", "validate"],
    )

    print(f"\n📋 Workflow: {workflow.name}")
    print(f"   Tasks: {len(workflow.tasks)}")

    # First run
    print("\n🚀 First execution (populating cache)...")
    result1 = await orchestrator.execute_workflow(workflow)

    stats1 = orchestrator.get_cache_stats()
    print(f"\n📊 After first run:")
    print(f"   Cache hits: {stats1['hits']}")
    print(f"   Cache misses: {stats1['misses']}")
    print(f"   Cache size: {stats1['cache_size']}")

    # Second run (should use cache)
    print("\n🚀 Second execution (using cache)...")
    result2 = await orchestrator.execute_workflow(workflow)

    stats2 = orchestrator.get_cache_stats()
    print(f"\n📊 After second run:")
    print(f"   Cache hits: {stats2['hits']}")
    print(f"   Cache misses: {stats2['misses']}")
    print(f"   Hit rate: {stats2['hit_rate']}")

    improvement = (
        (result1.completed_at - result1.started_at).total_seconds()
        if result1.started_at and result1.completed_at
        else 0
    )
    print(f"\n⚡ Performance improvement from caching:")
    print(f"   First run: {improvement:.2f}s")
    print(f"   Second run: Near instant (cached)")


async def example_visualizer_class_usage() -> None:
    """Demonstrate using DAGVisualizer class directly."""
    print("\n\n" + "=" * 70)
    print("USING DAGVisualizer CLASS DIRECTLY")
    print("=" * 70)

    workflow = WorkflowDefinition(
        id="viz-class",
        name="Visualizer Class Example",
        tasks=[
            TaskDefinition(id="start", description="Start"),
            TaskDefinition(id="process", description="Process", depends_on=["start"]),
            TaskDefinition(id="finish", description="Finish", depends_on=["process"]),
        ],
    )

    # Create visualizer
    visualizer = DAGVisualizer(workflow)

    print("\n📊 Generate multiple formats from same visualizer:")

    # Generate different formats
    formats = [
        (VisualizationFormat.MERMAID, "Mermaid"),
        (VisualizationFormat.ASCII, "ASCII"),
        (VisualizationFormat.GRAPHVIZ, "Graphviz"),
        (VisualizationFormat.JSON, "JSON"),
    ]

    for format, name in formats:
        diagram = visualizer.visualize(format)
        print(f"\n{name}:")
        print(f"   Length: {len(diagram)} characters")
        print(f"   Preview: {diagram[:100]}...")


async def main() -> None:
    """Run all caching and visualization examples."""
    print("=" * 70)
    print("CACHING & VISUALIZATION EXAMPLES")
    print("=" * 70)
    print("\nThis example demonstrates:")
    print("1. Result caching for performance")
    print("2. Different cache strategies")
    print("3. Cache TTL and invalidation")
    print("4. DAG visualization in multiple formats")
    print("5. Visualization with execution state")
    print("6. Combining caching with templates\n")

    # Run all examples
    await example_basic_caching()
    await example_cache_strategies()
    await example_cache_ttl()
    await example_cache_invalidation()
    await example_dag_visualization()
    await example_visualization_with_state()
    await example_caching_with_templates()
    await example_visualizer_class_usage()

    print("\n" + "=" * 70)
    print("✅ ALL EXAMPLES COMPLETED")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("• Caching dramatically improves performance for repeated workflows")
    print("• Choose cache strategy based on your needs (memory/disk/hybrid)")
    print("• Use TTL to auto-expire stale cache entries")
    print("• Visualize workflows to understand structure and debug issues")
    print("• Multiple visualization formats for different use cases")
    print("• Combine caching + visualization for optimal workflow management")


if __name__ == "__main__":
    asyncio.run(main())
