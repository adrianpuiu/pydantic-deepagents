"""Example demonstrating metrics collection and workflow templates.

This example shows how to:
1. Use pre-built workflow templates
2. Collect metrics automatically during workflow execution
3. Analyze performance with metrics
4. Generate performance reports
"""

import asyncio

from pydantic_ai.models import TestModel

from pydantic_deep import (
    TaskOrchestrator,
    create_ci_cd_pipeline,
    create_code_review_workflow,
    create_deep_agent,
    create_default_deps,
    create_documentation_workflow,
    create_etl_pipeline,
)


async def example_ci_cd_with_metrics() -> None:
    """Demonstrate CI/CD pipeline template with metrics collection."""
    print("=" * 70)
    print("CI/CD PIPELINE WITH METRICS")
    print("=" * 70)

    # Create agent and orchestrator
    agent = create_deep_agent(model=TestModel())
    deps = create_default_deps()
    orchestrator = TaskOrchestrator(agent, deps)

    # Create CI/CD pipeline using template
    workflow = create_ci_cd_pipeline(
        workflow_id="my-ci-cd",
        repository_path="/path/to/my/project",
        test_command="pytest",
        build_command="python -m build",
        deploy_target="staging",
        run_security_scan=True,
    )

    print(f"\n📋 Created workflow: {workflow.name}")
    print(f"   Strategy: {workflow.execution_strategy}")
    print(f"   Tasks: {len(workflow.tasks)}")

    # Execute workflow (metrics are collected automatically)
    print("\n🚀 Executing workflow...")
    result = await orchestrator.execute_workflow(workflow)

    # Get metrics for the workflow
    metrics = orchestrator.get_workflow_metrics(workflow.id)

    print("\n📊 WORKFLOW METRICS")
    print("=" * 70)
    if metrics:
        print(f"Total Duration: {metrics.total_duration_seconds:.2f}s")
        print(f"Total Tasks: {metrics.total_tasks}")
        print(f"Completed: {metrics.completed_tasks}")
        print(f"Failed: {metrics.failed_tasks}")
        print(f"Success Rate: {metrics.success_rate:.1f}%")
        print(f"Average Task Duration: {metrics.average_task_duration:.2f}s")

        if metrics.slowest_task:
            print(f"\n🐌 Bottleneck: {metrics.slowest_task.task_id}")
            print(f"   Duration: {metrics.slowest_task.duration_seconds:.2f}s")

        # Generate performance report
        print("\n📈 PERFORMANCE REPORT")
        print("=" * 70)
        print(metrics.get_performance_report())


async def example_etl_with_metrics() -> None:
    """Demonstrate ETL pipeline template with metrics collection."""
    print("\n\n" + "=" * 70)
    print("ETL PIPELINE WITH METRICS")
    print("=" * 70)

    # Create agent and orchestrator
    agent = create_deep_agent(model=TestModel())
    deps = create_default_deps()
    orchestrator = TaskOrchestrator(agent, deps)

    # Create ETL pipeline using template
    workflow = create_etl_pipeline(
        workflow_id="my-etl",
        source_configs=[
            {"type": "csv", "path": "data/sales.csv"},
            {"type": "json", "path": "data/customers.json"},
            {"type": "api", "url": "https://api.example.com/products"},
        ],
        transformation_steps=[
            "clean null values",
            "normalize column names",
            "merge datasets on customer_id",
            "aggregate by date",
        ],
        destination_config={"type": "database", "table": "analytics"},
        validate_data=True,
    )

    print(f"\n📋 Created workflow: {workflow.name}")
    print(f"   Strategy: {workflow.execution_strategy}")
    print(f"   Tasks: {len(workflow.tasks)}")
    print(f"   Sources: 3 (CSV, JSON, API)")
    print(f"   Transformations: 4 steps")

    # Execute workflow
    print("\n🚀 Executing workflow...")
    result = await orchestrator.execute_workflow(workflow)

    # Get metrics
    metrics = orchestrator.get_workflow_metrics(workflow.id)

    if metrics:
        print("\n📊 ETL METRICS")
        print("=" * 70)
        print(f"Success Rate: {metrics.success_rate:.1f}%")
        print(f"Total Duration: {metrics.total_duration_seconds:.2f}s")

        # Analyze failed tasks
        failed_tasks = metrics.get_failed_tasks()
        if failed_tasks:
            print(f"\n❌ Failed Tasks: {len(failed_tasks)}")
            for task in failed_tasks:
                print(f"   - {task.task_id}: {task.error}")


async def example_code_review_with_metrics() -> None:
    """Demonstrate code review workflow template with metrics."""
    print("\n\n" + "=" * 70)
    print("CODE REVIEW WORKFLOW WITH METRICS")
    print("=" * 70)

    # Create agent and orchestrator
    agent = create_deep_agent(model=TestModel())
    deps = create_default_deps()
    orchestrator = TaskOrchestrator(agent, deps)

    # Create code review workflow using template
    workflow = create_code_review_workflow(
        workflow_id="my-review",
        repository_path="/path/to/project",
        review_focus=["security", "quality", "documentation", "testing"],
        generate_report=True,
        auto_fix=False,  # Don't auto-fix in this example
    )

    print(f"\n📋 Created workflow: {workflow.name}")
    print(f"   Strategy: {workflow.execution_strategy}")
    print(f"   Tasks: {len(workflow.tasks)}")
    print(f"   Review Focus: security, quality, documentation, testing")

    # Execute workflow
    print("\n🚀 Executing workflow...")
    result = await orchestrator.execute_workflow(workflow)

    # Get metrics
    metrics = orchestrator.get_workflow_metrics(workflow.id)

    if metrics:
        print("\n📊 REVIEW METRICS")
        print("=" * 70)

        # Get summary
        summary = metrics.get_summary()
        print(f"Status: {summary['status']}")
        print(f"Total Tasks: {summary['total_tasks']}")
        print(f"Completed: {summary['completed_tasks']}")
        print(f"Failed: {summary['failed_tasks']}")
        print(f"Skipped: {summary['skipped_tasks']}")
        print(f"Success Rate: {summary['success_rate']}")

        if summary["slowest_task"]:
            print(f"\nSlowest Review: {summary['slowest_task']['task_id']}")
            print(f"Duration: {summary['slowest_task']['duration']}")


async def example_multiple_workflows_aggregate_stats() -> None:
    """Demonstrate aggregate statistics across multiple workflows."""
    print("\n\n" + "=" * 70)
    print("AGGREGATE STATISTICS ACROSS WORKFLOWS")
    print("=" * 70)

    # Create agent and orchestrator
    agent = create_deep_agent(model=TestModel())
    deps = create_default_deps()
    orchestrator = TaskOrchestrator(agent, deps)

    # Execute multiple workflows
    workflows = [
        create_ci_cd_pipeline(workflow_id="ci-cd-1", run_security_scan=False),
        create_etl_pipeline(workflow_id="etl-1"),
        create_code_review_workflow(workflow_id="review-1", generate_report=False),
        create_documentation_workflow(workflow_id="docs-1"),
    ]

    print("\n🚀 Executing 4 different workflows...\n")

    for workflow in workflows:
        print(f"   Executing: {workflow.name}...")
        await orchestrator.execute_workflow(workflow)

    # Get aggregate statistics
    print("\n📊 AGGREGATE STATISTICS")
    print("=" * 70)

    stats = orchestrator.get_aggregate_stats()
    print(f"Total Workflows: {stats['total_workflows']}")
    print(f"Total Tasks: {stats['total_tasks']}")
    print(f"Total Completed: {stats['total_completed']}")
    print(f"Total Failed: {stats['total_failed']}")
    print(f"Total Retries: {stats['total_retries']}")
    print(f"Average Success Rate: {stats['average_success_rate']}")
    print(f"Average Duration: {stats['average_duration']}")

    # Show individual workflow metrics
    print("\n📋 INDIVIDUAL WORKFLOW METRICS")
    print("=" * 70)

    all_metrics = orchestrator.get_all_metrics()
    for metrics in all_metrics:
        print(f"\n{metrics.workflow_name}:")
        print(f"  Tasks: {metrics.total_tasks}")
        print(f"  Success Rate: {metrics.success_rate:.1f}%")
        print(f"  Duration: {metrics.total_duration_seconds:.2f}s")


async def example_performance_comparison() -> None:
    """Compare performance across different workflow configurations."""
    print("\n\n" + "=" * 70)
    print("PERFORMANCE COMPARISON")
    print("=" * 70)

    agent = create_deep_agent(model=TestModel())
    deps = create_default_deps()
    orchestrator = TaskOrchestrator(agent, deps)

    # Test CI/CD with and without security scan
    print("\n🔬 Testing CI/CD configurations...\n")

    workflow_with_security = create_ci_cd_pipeline(
        workflow_id="ci-cd-with-security",
        run_security_scan=True,
        deploy_target=None,
    )
    workflow_without_security = create_ci_cd_pipeline(
        workflow_id="ci-cd-without-security",
        run_security_scan=False,
        deploy_target=None,
    )

    print("   Running with security scan...")
    await orchestrator.execute_workflow(workflow_with_security)

    print("   Running without security scan...")
    await orchestrator.execute_workflow(workflow_without_security)

    # Compare metrics
    metrics_with = orchestrator.get_workflow_metrics("ci-cd-with-security")
    metrics_without = orchestrator.get_workflow_metrics("ci-cd-without-security")

    print("\n📊 COMPARISON")
    print("=" * 70)

    if metrics_with and metrics_without:
        print(f"\nWith Security Scan:")
        print(f"  Tasks: {metrics_with.total_tasks}")
        print(f"  Duration: {metrics_with.total_duration_seconds:.2f}s")

        print(f"\nWithout Security Scan:")
        print(f"  Tasks: {metrics_without.total_tasks}")
        print(f"  Duration: {metrics_without.total_duration_seconds:.2f}s")

        time_diff = metrics_with.total_duration_seconds - metrics_without.total_duration_seconds
        print(f"\n⏱️  Time Difference: {time_diff:.2f}s")
        print(f"   Security scan adds {(time_diff / metrics_without.total_duration_seconds * 100):.1f}% overhead")


async def example_metrics_driven_optimization() -> None:
    """Use metrics to identify and optimize bottlenecks."""
    print("\n\n" + "=" * 70)
    print("METRICS-DRIVEN OPTIMIZATION")
    print("=" * 70)

    agent = create_deep_agent(model=TestModel())
    deps = create_default_deps()
    orchestrator = TaskOrchestrator(agent, deps)

    # Execute a workflow
    workflow = create_etl_pipeline(
        workflow_id="optimization-test",
        source_configs=[
            {"type": "csv", "path": "large_dataset.csv"},
        ],
        transformation_steps=[
            "clean data",
            "transform schema",
            "enrich with external data",
            "aggregate results",
        ],
    )

    print("\n🚀 Executing workflow...")
    await orchestrator.execute_workflow(workflow)

    # Analyze metrics to find bottleneck
    metrics = orchestrator.get_workflow_metrics(workflow.id)

    if metrics:
        print("\n🔍 IDENTIFYING BOTTLENECKS")
        print("=" * 70)

        bottleneck = metrics.get_bottleneck()
        if bottleneck:
            print(f"\n⚠️  Bottleneck Found: {bottleneck.task_id}")
            print(f"   Duration: {bottleneck.duration_seconds:.2f}s")
            print(f"   % of Total: {(bottleneck.duration_seconds / metrics.total_duration_seconds * 100):.1f}%")

            if bottleneck.retry_count > 0:
                print(f"   Retries: {bottleneck.retry_count} (consider improving reliability)")

            print("\n💡 OPTIMIZATION SUGGESTIONS:")
            print("   1. Optimize the bottleneck task implementation")
            print("   2. Consider parallelizing if possible")
            print("   3. Add caching for repeated operations")
            print("   4. Review retry configuration if applicable")

        # Show task breakdown
        print("\n📊 TASK BREAKDOWN")
        print("=" * 70)
        for task_metrics in sorted(metrics.task_metrics, key=lambda t: t.duration_seconds, reverse=True):
            pct = (task_metrics.duration_seconds / metrics.total_duration_seconds * 100)
            print(f"{task_metrics.task_id:30s} {task_metrics.duration_seconds:6.2f}s ({pct:5.1f}%)")


async def main() -> None:
    """Run all examples."""
    print("=" * 70)
    print("METRICS & TEMPLATES EXAMPLES")
    print("=" * 70)
    print("\nThis example demonstrates:")
    print("1. Using pre-built workflow templates")
    print("2. Automatic metrics collection")
    print("3. Performance analysis and reporting")
    print("4. Bottleneck identification")
    print("5. Workflow optimization\n")

    # Run all examples
    await example_ci_cd_with_metrics()
    await example_etl_with_metrics()
    await example_code_review_with_metrics()
    await example_multiple_workflows_aggregate_stats()
    await example_performance_comparison()
    await example_metrics_driven_optimization()

    print("\n" + "=" * 70)
    print("✅ ALL EXAMPLES COMPLETED")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("• Templates make it easy to create standard workflows")
    print("• Metrics are collected automatically for all workflows")
    print("• Use metrics to identify bottlenecks and optimize performance")
    print("• Compare different configurations to find optimal setup")
    print("• Aggregate statistics help understand overall system performance")


if __name__ == "__main__":
    asyncio.run(main())
