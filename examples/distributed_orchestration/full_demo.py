#!/usr/bin/env python3
"""Full distributed orchestration demo.

This comprehensive example demonstrates:
- All major orchestration features
- Custom worker configuration
- Dynamic worker management
- Custom aggregation strategies
- Advanced task coordination
- Complete software development pipeline
"""

import asyncio

from orchestrator import DistributedOrchestrator, TaskPriority
from pydantic_deep.types import SubAgentConfig


def custom_aggregation(results: list[str]) -> str:
    """Custom aggregation strategy that creates a structured report."""
    report = "# Development Pipeline Report\n\n"
    report += f"Generated {len(results)} deliverables:\n\n"

    sections = [
        "## Implementation",
        "## Tests",
        "## Documentation",
        "## Review",
    ]

    for section, result in zip(sections, results):
        report += f"{section}\n\n{result}\n\n"
        report += "---\n\n"

    return report


async def main():
    print("=" * 70)
    print("Full Distributed Orchestration Demo")
    print("=" * 70)
    print()

    # Create orchestrator with custom configuration
    print("Step 1: Creating orchestrator with custom configuration...")
    orchestrator = DistributedOrchestrator(
        model="openai:gpt-4o-mini",
        max_concurrent_workers=4,
    )

    # Set custom aggregation strategy
    orchestrator.set_aggregation_strategy(custom_aggregation)

    print(f"✓ {orchestrator}")
    print(f"✓ Available workers: {len(orchestrator.worker_configs)}")
    print()

    # Scenario: Complete Software Development Pipeline
    print("=" * 70)
    print("Scenario: Complete Software Development Pipeline")
    print("=" * 70)
    print()

    print("Building a user authentication module...")
    print()

    # Step 1: Design and implement
    print("Phase 1: Implementation")
    print("-" * 70)

    implementation_task = """
Create a Python user authentication module with the following features:
1. User registration with email and password
2. Password hashing using bcrypt
3. Login functionality
4. Session management
5. Proper error handling

Include the complete implementation with all necessary imports.
"""

    implementation = await orchestrator.execute(
        implementation_task, priority=TaskPriority.HIGH
    )
    print("✓ Implementation completed")
    print()

    # Step 2: Parallel test generation and documentation
    print("Phase 2: Testing and Documentation (Parallel)")
    print("-" * 70)

    parallel_tasks = [
        """
Generate comprehensive pytest tests for the user authentication module.
Include tests for:
- User registration (happy path and errors)
- Password hashing validation
- Login success and failure
- Session management
- Edge cases and security scenarios

Use fixtures and parametrize where appropriate.
""",
        """
Write comprehensive documentation for the user authentication module.
Include:
- Overview and features
- Installation and setup
- Usage examples for each feature
- API reference
- Security best practices
- Troubleshooting guide
""",
    ]

    results = await orchestrator.execute_parallel(parallel_tasks)
    tests = results[0]
    documentation = results[1]

    print("✓ Tests generated")
    print("✓ Documentation created")
    print()

    # Step 3: Code review
    print("Phase 3: Code Review")
    print("-" * 70)

    review_task = f"""
Review the following user authentication implementation for:
- Security vulnerabilities
- Best practices compliance
- Error handling
- Code quality
- Performance considerations

Implementation:
{implementation[:500]}...
"""

    review = await orchestrator.execute(review_task)
    print("✓ Code review completed")
    print()

    # Aggregate all results
    print("Phase 4: Report Generation")
    print("-" * 70)

    final_report = await orchestrator.aggregate_results(
        [implementation, tests, documentation, review]
    )

    print("Final Development Report:")
    print("=" * 70)
    print(final_report)
    print()

    # Demonstrate dynamic worker management
    print("=" * 70)
    print("Dynamic Worker Management Demo")
    print("=" * 70)
    print()

    # Add a custom worker at runtime
    print("Adding custom 'performance-optimizer' worker...")
    performance_worker = SubAgentConfig(
        name="performance-optimizer",
        description="Optimizes code for performance and efficiency",
        instructions="""You are a performance optimization expert.

Analyze code and suggest optimizations for:
- Algorithm efficiency
- Memory usage
- Database query optimization
- Caching strategies
- Async/await improvements

Provide specific, actionable optimization suggestions.""",
    )

    orchestrator.add_worker(performance_worker)
    print(f"✓ Worker added. Total workers: {len(orchestrator.worker_configs)}")
    print()

    # Use the new worker
    print("Using the new performance-optimizer worker...")
    optimization_task = """
Review the user authentication module for performance optimizations.
Focus on database queries, password hashing, and session management.
"""

    optimization = await orchestrator.execute(optimization_task)
    print("Performance Optimization Report:")
    print(optimization)
    print()

    # Demonstrate task status tracking
    print("=" * 70)
    print("Task Status Tracking")
    print("=" * 70)
    print()

    all_tasks = orchestrator.get_all_tasks()
    print(f"Total tasks executed: {len(all_tasks)}")
    print()

    for task_id, task in all_tasks.items():
        duration = (
            (task.completed_at - task.started_at).total_seconds()
            if task.completed_at and task.started_at
            else 0
        )
        print(f"Task: {task.id}")
        print(f"  Status: {task.status.value}")
        print(f"  Priority: {task.priority.name}")
        print(f"  Duration: {duration:.2f}s")
        print()

    # Final metrics
    print("=" * 70)
    print("Final Orchestration Metrics")
    print("=" * 70)
    metrics = orchestrator.get_metrics()

    print(f"Total tasks: {metrics['total_tasks']}")
    print(f"Completed: {metrics['completed_tasks']}")
    print(f"Failed: {metrics['failed_tasks']}")
    print(f"Success rate: {metrics['success_rate']:.1%}")
    print()

    print("Worker Performance:")
    for worker_name, stats in metrics["workers"].items():
        total = stats["tasks_completed"] + stats["tasks_failed"]
        if total > 0:
            print(f"  {worker_name}: {total} tasks")
    print()

    print("=" * 70)
    print("✓ Full demo completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
