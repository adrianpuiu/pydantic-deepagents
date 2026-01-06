#!/usr/bin/env python3
"""Basic distributed orchestration demo.

This example demonstrates the simplest use case:
- Creating an orchestrator with default workers
- Executing a single task that gets delegated to appropriate workers
- Viewing the aggregated result
"""

import asyncio

from orchestrator import DistributedOrchestrator


async def main():
    print("=" * 70)
    print("Basic Distributed Orchestration Demo")
    print("=" * 70)
    print()

    # Create orchestrator with default configuration
    print("Creating orchestrator with default worker agents...")
    orchestrator = DistributedOrchestrator(
        model="openai:gpt-4o-mini",  # Using a cost-effective model
    )
    print(f"✓ {orchestrator}")
    print(f"✓ Workers: {', '.join(w['name'] for w in orchestrator.worker_configs)}")
    print()

    # Example 1: Simple task that will be delegated
    print("Example 1: Code Review Task")
    print("-" * 70)

    task1 = """Review this Python function for potential issues:

def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)
"""

    print(f"Task: {task1[:80]}...")
    print()

    result1 = await orchestrator.execute(task1)
    print("Result:")
    print(result1)
    print()

    # Example 2: Data analysis task
    print("Example 2: Data Analysis Task")
    print("-" * 70)

    task2 = """Analyze this sample data and provide insights:

Sales data:
Q1: $125,000
Q2: $148,000
Q3: $132,000
Q4: $167,000

Identify trends and provide recommendations.
"""

    print(f"Task: {task2[:80]}...")
    print()

    result2 = await orchestrator.execute(task2)
    print("Result:")
    print(result2)
    print()

    # Example 3: Documentation task
    print("Example 3: Documentation Task")
    print("-" * 70)

    task3 = """Write documentation for a function that validates email addresses.

The function should:
- Take a string as input
- Return True if valid email, False otherwise
- Handle edge cases like empty strings, missing @ symbol, etc.
"""

    print(f"Task: {task3[:80]}...")
    print()

    result3 = await orchestrator.execute(task3)
    print("Result:")
    print(result3)
    print()

    # Show orchestration metrics
    print("=" * 70)
    print("Orchestration Metrics")
    print("=" * 70)
    metrics = orchestrator.get_metrics()
    print(f"Total tasks executed: {metrics['total_tasks']}")
    print(f"Completed: {metrics['completed_tasks']}")
    print(f"Failed: {metrics['failed_tasks']}")
    print(f"Success rate: {metrics['success_rate']:.1%}")
    print()

    print("✓ Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
