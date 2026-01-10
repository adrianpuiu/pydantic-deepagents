"""Example demonstrating the dynamic orchestration system.

This example shows how to use the orchestration system to coordinate
multiple agents working together on a complex workflow.
"""

import asyncio
from typing import Any

from pydantic_ai_backends import StateBackend

from pydantic_deep import (
    AgentCapability,
    ExecutionStrategy,
    TaskDefinition,
    TaskOrchestrator,
    WorkflowDefinition,
    WorkflowState,
    create_deep_agent,
    create_default_deps,
    create_default_routing,
)
from pydantic_deep.orchestration import OrchestrationConfig


async def main() -> None:
    """Run orchestration example."""
    print("=== Dynamic Orchestration Example ===\n")

    # Create main agent
    agent = create_deep_agent(
        model="openai:gpt-4o-mini",
        instructions="You are a helpful assistant that can coordinate multiple specialized agents.",
    )

    # Create dependencies with StateBackend for testing
    deps = create_default_deps(backend=StateBackend())

    # Create orchestration config with agent routing
    config = OrchestrationConfig(
        agent_routing=create_default_routing(),
        enable_parallel_execution=True,
    )

    # Create orchestrator
    orchestrator = TaskOrchestrator(agent, deps, config)

    # Define a complex workflow: Build a simple web application
    workflow = WorkflowDefinition(
        id="web-app-development",
        name="Web Application Development Pipeline",
        description="Complete workflow for building a simple web application",
        execution_strategy=ExecutionStrategy.DAG,
        max_parallel_tasks=3,
        continue_on_failure=False,
        tasks=[
            # Phase 1: Planning and setup
            TaskDefinition(
                id="requirements",
                description="Define the requirements for a simple todo list web application",
                required_capabilities=[AgentCapability.GENERAL],
                priority=10,
            ),
            # Phase 2: Backend development (parallel)
            TaskDefinition(
                id="backend-api",
                description="Design the RESTful API endpoints for the todo list application based on requirements",
                depends_on=["requirements"],
                required_capabilities=[AgentCapability.CODE_GENERATION],
                priority=8,
            ),
            TaskDefinition(
                id="database-schema",
                description="Design the database schema for storing todos based on requirements",
                depends_on=["requirements"],
                required_capabilities=[AgentCapability.DATA_PROCESSING],
                priority=8,
            ),
            # Phase 3: Frontend development (depends on backend design)
            TaskDefinition(
                id="frontend-ui",
                description="Design the user interface components for the todo list application",
                depends_on=["backend-api"],
                required_capabilities=[AgentCapability.CODE_GENERATION],
                priority=7,
            ),
            # Phase 4: Integration and testing (depends on both backend and frontend)
            TaskDefinition(
                id="integration",
                description="Create integration plan for connecting frontend to backend API",
                depends_on=["backend-api", "frontend-ui", "database-schema"],
                required_capabilities=[AgentCapability.CODE_ANALYSIS],
                priority=6,
            ),
            TaskDefinition(
                id="testing-strategy",
                description="Design comprehensive testing strategy for the application",
                depends_on=["integration"],
                required_capabilities=[AgentCapability.TESTING],
                priority=5,
            ),
            # Phase 5: Documentation
            TaskDefinition(
                id="documentation",
                description="Create user and developer documentation for the todo list application",
                depends_on=["testing-strategy"],
                required_capabilities=[AgentCapability.DOCUMENTATION],
                priority=4,
            ),
        ],
    )

    # Progress callback to track execution
    def progress_callback(state: WorkflowState) -> None:
        progress = orchestrator.get_workflow_progress(workflow.id)
        if progress:
            print(f"\n📊 Progress: {progress['completed']}/{progress['total_tasks']} tasks completed")
            print(f"   Status: {progress['status']}")
            print(f"   Running: {progress['running']}, Pending: {progress['pending']}, Failed: {progress['failed']}")

    # Execute workflow
    print("🚀 Starting workflow execution...\n")
    result = await orchestrator.execute_workflow(workflow, progress_callback)

    # Display results
    print("\n" + "=" * 60)
    print("📋 Workflow Execution Complete!")
    print("=" * 60)
    print(f"Status: {result.status}")
    print(f"Duration: {(result.completed_at - result.started_at).total_seconds():.2f}s" if result.completed_at and result.started_at else "N/A")
    print(f"\nTasks completed: {len(result.completed_tasks)}")
    print(f"Tasks failed: {len(result.failed_tasks)}")

    # Display task results
    print("\n" + "=" * 60)
    print("📝 Task Results:")
    print("=" * 60)
    for task_id, task_result in result.task_results.items():
        print(f"\n{task_id}:")
        print(f"  Status: {task_result.status}")
        print(f"  Agent: {task_result.agent_used or 'N/A'}")
        if task_result.duration_seconds:
            print(f"  Duration: {task_result.duration_seconds:.2f}s")
        if task_result.output:
            output_preview = str(task_result.output)[:200]
            print(f"  Output: {output_preview}...")
        if task_result.error:
            print(f"  Error: {task_result.error}")

    # Demonstrate individual task execution
    print("\n" + "=" * 60)
    print("🔧 Executing Individual Task")
    print("=" * 60)

    single_task = TaskDefinition(
        id="code-review",
        description="Review the Python code quality in the current project",
        required_capabilities=[AgentCapability.CODE_ANALYSIS],
    )

    task_result = await orchestrator.execute_task(single_task)
    print(f"\nTask: {single_task.id}")
    print(f"Status: {task_result.status}")
    print(f"Output: {task_result.output}")


async def demonstrate_parallel_execution() -> None:
    """Demonstrate parallel execution of independent tasks."""
    print("\n\n" + "=" * 60)
    print("⚡ Parallel Execution Example")
    print("=" * 60 + "\n")

    # Create agent and orchestrator
    agent = create_deep_agent(model="openai:gpt-4o-mini")
    deps = create_default_deps(backend=StateBackend())
    orchestrator = TaskOrchestrator(agent, deps)

    # Define workflow with independent parallel tasks
    workflow = WorkflowDefinition(
        id="data-analysis",
        name="Parallel Data Analysis",
        execution_strategy=ExecutionStrategy.PARALLEL,
        max_parallel_tasks=5,
        tasks=[
            TaskDefinition(
                id=f"analyze-dataset-{i}",
                description=f"Analyze dataset {i} and extract key insights",
                required_capabilities=[AgentCapability.DATA_PROCESSING],
            )
            for i in range(5)
        ],
    )

    result = await orchestrator.execute_workflow(workflow)
    print(f"\n✅ Completed {len(result.completed_tasks)}/5 parallel tasks")
    print(f"Total duration: {(result.completed_at - result.started_at).total_seconds():.2f}s" if result.completed_at and result.started_at else "N/A")


async def demonstrate_conditional_workflow() -> None:
    """Demonstrate conditional task execution."""
    print("\n\n" + "=" * 60)
    print("🔀 Conditional Execution Example")
    print("=" * 60 + "\n")

    # Create agent and orchestrator
    agent = create_deep_agent(model="openai:gpt-4o-mini")
    deps = create_default_deps(backend=StateBackend())
    orchestrator = TaskOrchestrator(agent, deps)

    # Define workflow with conditional tasks
    workflow = WorkflowDefinition(
        id="quality-check",
        name="Code Quality Check with Conditional Fixes",
        execution_strategy=ExecutionStrategy.CONDITIONAL,
        tasks=[
            TaskDefinition(
                id="analyze-code",
                description="Analyze code quality and identify issues",
                required_capabilities=[AgentCapability.CODE_ANALYSIS],
            ),
            TaskDefinition(
                id="fix-critical",
                description="Fix critical issues found in code analysis",
                depends_on=["analyze-code"],
                condition="analyze-code",  # Only if analysis completed
                required_capabilities=[AgentCapability.CODE_GENERATION],
            ),
            TaskDefinition(
                id="run-tests",
                description="Run tests after fixes are applied",
                depends_on=["fix-critical"],
                required_capabilities=[AgentCapability.TESTING],
            ),
        ],
    )

    result = await orchestrator.execute_workflow(workflow)
    print(f"\n✅ Workflow completed with status: {result.status}")
    print(f"Completed tasks: {len(result.completed_tasks)}")
    print(f"Skipped tasks: {len([r for r in result.task_results.values() if r.status == 'skipped'])}")


if __name__ == "__main__":
    # Run main example
    asyncio.run(main())

    # Uncomment to run additional examples:
    # asyncio.run(demonstrate_parallel_execution())
    # asyncio.run(demonstrate_conditional_workflow())
