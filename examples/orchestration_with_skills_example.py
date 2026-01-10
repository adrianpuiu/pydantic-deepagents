"""Example demonstrating skill integration with orchestration.

This example shows how to:
1. Define tasks that require specific skills
2. Auto-load skills when tasks execute
3. Use skills across multiple tasks in a workflow
"""

import asyncio
import tempfile
from pathlib import Path

from pydantic_ai_backends import StateBackend

from pydantic_deep import (
    AgentCapability,
    ExecutionStrategy,
    TaskDefinition,
    TaskOrchestrator,
    WorkflowDefinition,
    create_deep_agent,
    create_default_deps,
)


async def create_example_skills() -> Path:
    """Create example skills for demonstration.

    Returns:
        Path to temporary skills directory.
    """
    skills_dir = Path(tempfile.mkdtemp()) / "skills"
    skills_dir.mkdir(exist_ok=True)

    # Skill 1: Python Code Review
    python_review_dir = skills_dir / "python-code-review"
    python_review_dir.mkdir()

    python_review_skill = """---
name: python-code-review
description: Expert Python code review and best practices
tags:
  - python
  - code-review
  - quality
version: 1.0
author: example
---

# Python Code Review Skill

You are an expert Python code reviewer. When analyzing Python code, focus on:

## Code Quality
- PEP 8 style compliance
- Proper naming conventions
- Code organization and structure

## Best Practices
- Proper error handling
- Type hints usage
- Documentation quality
- Security considerations

## Performance
- Algorithm efficiency
- Memory usage
- Potential bottlenecks

## Recommendations
Provide specific, actionable recommendations for improvement.
Format your review as:
1. Summary of findings
2. Specific issues (with line references if available)
3. Recommendations for improvement
4. Overall quality score (1-10)
"""
    (python_review_dir / "SKILL.md").write_text(python_review_skill)

    # Skill 2: API Design
    api_design_dir = skills_dir / "api-design"
    api_design_dir.mkdir()

    api_design_skill = """---
name: api-design
description: RESTful API design and best practices
tags:
  - api
  - rest
  - design
version: 1.0
author: example
---

# API Design Skill

You are an expert in RESTful API design. When designing APIs, follow:

## REST Principles
- Resource-based URLs
- Proper HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Stateless operations
- Hypermedia (HATEOAS where appropriate)

## Best Practices
- Consistent naming conventions
- Versioning strategy
- Proper status codes
- Clear error messages
- Pagination for lists
- Filtering and sorting options

## Documentation
- Clear endpoint descriptions
- Request/response examples
- Authentication requirements
- Rate limiting information

Provide comprehensive API designs with:
1. Endpoint definitions
2. Request/response schemas
3. Status codes
4. Example requests
"""
    (api_design_dir / "SKILL.md").write_text(api_design_skill)

    # Skill 3: Test Strategy
    test_strategy_dir = skills_dir / "test-strategy"
    test_strategy_dir.mkdir()

    test_strategy_skill = """---
name: test-strategy
description: Comprehensive testing strategy development
tags:
  - testing
  - quality
  - tdd
version: 1.0
author: example
---

# Test Strategy Skill

You are an expert in software testing. When developing test strategies:

## Test Types
- Unit tests (individual components)
- Integration tests (component interactions)
- End-to-end tests (user workflows)
- Performance tests (load, stress)
- Security tests (vulnerabilities)

## Coverage
- Code coverage targets (aim for 80%+)
- Edge cases and error conditions
- Boundary value testing
- Negative testing

## Best Practices
- Test independence
- Fast test execution
- Clear test names and descriptions
- Proper setup/teardown
- Mock external dependencies

## Deliverables
Provide:
1. Test coverage plan
2. Test case examples
3. Testing tools recommendations
4. CI/CD integration approach
"""
    (test_strategy_dir / "SKILL.md").write_text(test_strategy_skill)

    return skills_dir


async def main() -> None:
    """Run orchestration with skills example."""
    print("=" * 70)
    print("ORCHESTRATION WITH SKILLS INTEGRATION")
    print("=" * 70)

    # Create example skills
    skills_dir = await create_example_skills()
    print(f"\n✓ Created example skills in: {skills_dir}\n")

    # Create agent and deps
    agent = create_deep_agent(model="openai:gpt-4o-mini")
    deps = create_default_deps(backend=StateBackend())

    # Create orchestrator with skills directory
    orchestrator = TaskOrchestrator(
        agent,
        deps,
        skill_directories=[{"path": str(skills_dir), "recursive": True}]
    )

    print("📚 Available skills:")
    orchestrator.skill_manager.discover_skills()
    all_skills = orchestrator.skill_manager.get_all_skills()
    for skill in all_skills:
        print(f"  - {skill['name']}: {skill['description']}")
    print()

    # Define workflow with tasks requiring specific skills
    workflow = WorkflowDefinition(
        id="code-quality-pipeline",
        name="Code Quality Pipeline with Skills",
        execution_strategy=ExecutionStrategy.DAG,
        tasks=[
            TaskDefinition(
                id="api-design",
                description="Design RESTful API for a todo list application",
                required_capabilities=[AgentCapability.CODE_GENERATION],
                required_skills=["api-design"],  # ← Auto-loads this skill
                priority=10,
            ),
            TaskDefinition(
                id="implementation",
                description="Implement the API endpoints in Python based on the design",
                depends_on=["api-design"],
                required_capabilities=[AgentCapability.CODE_GENERATION],
                priority=8,
            ),
            TaskDefinition(
                id="code-review",
                description="Review the implemented Python code for quality and best practices",
                depends_on=["implementation"],
                required_capabilities=[AgentCapability.CODE_ANALYSIS],
                required_skills=["python-code-review"],  # ← Auto-loads this skill
                priority=7,
            ),
            TaskDefinition(
                id="test-strategy",
                description="Develop comprehensive testing strategy for the API",
                depends_on=["implementation"],
                required_capabilities=[AgentCapability.TESTING],
                required_skills=["test-strategy"],  # ← Auto-loads this skill
                priority=6,
            ),
        ],
    )

    # Execute workflow with progress tracking
    def progress_callback(state):
        progress = orchestrator.get_workflow_progress(workflow.id)
        if progress:
            print(f"\n📊 Progress: {progress['completed']}/{progress['total_tasks']} tasks")
            print(f"   Running: {progress['running']}, Pending: {progress['pending']}")

    print("🚀 Executing workflow with auto-loaded skills...\n")
    result = await orchestrator.execute_workflow(workflow, progress_callback)

    # Display results
    print("\n" + "=" * 70)
    print("📋 WORKFLOW RESULTS")
    print("=" * 70)
    print(f"Status: {result.status}")
    print(f"Completed tasks: {len(result.completed_tasks)}")
    print(f"Failed tasks: {len(result.failed_tasks)}")

    print("\n" + "=" * 70)
    print("📝 TASK DETAILS")
    print("=" * 70)

    for task_id, task_result in result.task_results.items():
        # Get task definition to show required skills
        task_def = next((t for t in workflow.tasks if t.id == task_id), None)

        print(f"\n{task_id}:")
        print(f"  Status: {task_result.status}")

        if task_def and task_def.required_skills:
            print(f"  Skills used: {', '.join(task_def.required_skills)}")

        if task_result.duration_seconds:
            print(f"  Duration: {task_result.duration_seconds:.2f}s")

        if task_result.output:
            output_preview = str(task_result.output)[:300]
            print(f"  Output preview: {output_preview}...")

    print("\n" + "=" * 70)
    print("💡 KEY FEATURES DEMONSTRATED")
    print("=" * 70)
    print("""
1. ✅ AUTOMATIC SKILL LOADING
   - Tasks specify required_skills parameter
   - Skills are auto-loaded when task executes
   - No manual skill management required

2. ✅ SKILL DISCOVERY
   - Orchestrator discovers all available skills
   - Skills loaded from configured directories
   - Skills cached for efficient reuse

3. ✅ SKILL INTEGRATION
   - Skills automatically available to agents
   - Multiple tasks can use same skill
   - Skills provide domain expertise

4. ✅ WORKFLOW COORDINATION
   - Tasks with dependencies execute in order
   - Skills enhance task execution quality
   - Progress tracking shows skill usage
    """)

    # Cleanup
    import shutil
    shutil.rmtree(skills_dir.parent)
    print(f"\n✓ Cleaned up temporary skills directory")


async def demonstrate_skill_summary() -> None:
    """Demonstrate skill summary for tasks."""
    print("\n\n" + "=" * 70)
    print("SKILL SUMMARY DEMONSTRATION")
    print("=" * 70)

    skills_dir = await create_example_skills()

    agent = create_deep_agent(model="openai:gpt-4o-mini")
    deps = create_default_deps(backend=StateBackend())

    orchestrator = TaskOrchestrator(
        agent,
        deps,
        skill_directories=[{"path": str(skills_dir), "recursive": True}]
    )

    # Discover skills
    orchestrator.skill_manager.discover_skills()

    # Create task with skills
    task = TaskDefinition(
        id="quality-check",
        description="Comprehensive quality check",
        required_skills=["python-code-review", "test-strategy"],
    )

    # Get skill summary
    summary = orchestrator.skill_manager.get_skill_summary(task)
    print(f"\n{summary}\n")

    # Cleanup
    import shutil
    shutil.rmtree(skills_dir.parent)


if __name__ == "__main__":
    # Run main example
    asyncio.run(main())

    # Run skill summary demo
    asyncio.run(demonstrate_skill_summary())
