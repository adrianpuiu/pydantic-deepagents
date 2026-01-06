#!/usr/bin/env python3
"""Parallel execution demo.

This example demonstrates:
- Executing multiple independent tasks in parallel
- Load balancing across workers
- Result aggregation from parallel execution
- Performance comparison with sequential execution
"""

import asyncio
import time

from orchestrator import DistributedOrchestrator, TaskPriority


async def main():
    print("=" * 70)
    print("Parallel Execution Demo")
    print("=" * 70)
    print()

    # Create orchestrator
    print("Creating orchestrator...")
    orchestrator = DistributedOrchestrator(
        model="openai:gpt-4o-mini",
        max_concurrent_workers=5,  # Allow up to 5 parallel tasks
    )
    print(f"✓ {orchestrator}")
    print()

    # Example 1: Parallel data processing
    print("Example 1: Parallel Data Analysis")
    print("-" * 70)
    print("Processing quarterly sales data in parallel...")
    print()

    quarterly_tasks = [
        "Analyze Q1 sales data: Revenue $125K, Customers 450, Growth +12%. Identify key trends.",
        "Analyze Q2 sales data: Revenue $148K, Customers 520, Growth +18%. Identify key trends.",
        "Analyze Q3 sales data: Revenue $132K, Customers 480, Growth -11%. Identify key trends.",
        "Analyze Q4 sales data: Revenue $167K, Customers 580, Growth +27%. Identify key trends.",
    ]

    start_time = time.time()
    results = await orchestrator.execute_parallel(quarterly_tasks)
    parallel_time = time.time() - start_time

    print(f"Completed {len(results)} analyses in {parallel_time:.2f} seconds")
    print()

    for i, result in enumerate(results, 1):
        print(f"Q{i} Analysis:")
        print(result)
        print()

    # Aggregate the quarterly results
    print("Aggregating quarterly results...")
    annual_summary = await orchestrator.aggregate_results(results)
    print("Annual Summary:")
    print(annual_summary)
    print()

    # Example 2: Parallel code generation
    print("Example 2: Parallel Code Generation")
    print("-" * 70)
    print("Generating multiple code modules in parallel...")
    print()

    code_tasks = [
        "Write a Python function to validate email addresses with regex",
        "Write a Python function to parse and validate phone numbers",
        "Write a Python function to validate URLs",
    ]

    results = await orchestrator.execute_parallel(code_tasks)

    for i, result in enumerate(results, 1):
        print(f"Module {i}:")
        print(result)
        print()

    # Example 3: Parallel testing and review
    print("Example 3: Parallel Review and Testing")
    print("-" * 70)
    print("Running code review and test generation in parallel...")
    print()

    sample_code = """
def divide(a, b):
    return a / b
"""

    review_and_test_tasks = [
        f"Review this code for issues: {sample_code}",
        f"Generate comprehensive pytest tests for: {sample_code}",
    ]

    results = await orchestrator.execute_parallel(
        review_and_test_tasks, priority=TaskPriority.HIGH
    )

    print("Review Results:")
    print(results[0])
    print()

    print("Generated Tests:")
    print(results[1])
    print()

    # Example 4: Large-scale parallel processing
    print("Example 4: Large-Scale Parallel Processing")
    print("-" * 70)
    print("Processing 10 tasks with max 5 concurrent workers...")
    print()

    batch_tasks = [
        f"Task {i}: Analyze sample data point {i * 100} and provide a brief summary"
        for i in range(1, 11)
    ]

    start_time = time.time()
    batch_results = await orchestrator.execute_parallel(batch_tasks)
    batch_time = time.time() - start_time

    print(f"✓ Completed {len(batch_results)} tasks in {batch_time:.2f} seconds")
    print(f"✓ Average time per task: {batch_time / len(batch_results):.2f} seconds")
    print()

    # Show metrics
    print("=" * 70)
    print("Orchestration Metrics")
    print("=" * 70)
    metrics = orchestrator.get_metrics()
    print(f"Total tasks executed: {metrics['total_tasks']}")
    print(f"Completed: {metrics['completed_tasks']}")
    print(f"Failed: {metrics['failed_tasks']}")
    print(f"Success rate: {metrics['success_rate']:.1%}")
    print()

    print("Worker Statistics:")
    for worker_name, stats in metrics["workers"].items():
        print(f"  {worker_name}:")
        print(f"    Completed: {stats['tasks_completed']}")
        print(f"    Failed: {stats['tasks_failed']}")
        print(f"    Busy: {stats['busy']}")
    print()

    print("✓ Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
