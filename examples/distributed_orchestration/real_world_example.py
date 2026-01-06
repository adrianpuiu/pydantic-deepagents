#!/usr/bin/env python3
"""Real-world distributed orchestration example.

This example demonstrates a realistic scenario: building a complete
REST API for a blogging platform using distributed agent orchestration.

The orchestrator coordinates multiple specialized workers to:
1. Design the API architecture
2. Implement the backend code
3. Write comprehensive tests
4. Create API documentation
5. Review for security and quality
6. Generate deployment configurations
"""

import asyncio

from orchestrator import DistributedOrchestrator, TaskPriority
from configs.worker_configs import (
    API_DESIGNER,
    CODE_REVIEWER,
    CODE_WRITER,
    DATABASE_SPECIALIST,
    DEVOPS_ENGINEER,
    DOC_WRITER,
    SECURITY_AUDITOR,
    TEST_WRITER,
)


async def main():
    print("=" * 80)
    print("Real-World Example: Building a Blogging Platform REST API")
    print("=" * 80)
    print()

    # Create orchestrator with specialized workers for this project
    print("Setting up orchestration team...")
    orchestrator = DistributedOrchestrator(
        model="openai:gpt-4o-mini",
        custom_workers=[
            API_DESIGNER,
            CODE_WRITER,
            TEST_WRITER,
            DOC_WRITER,
            CODE_REVIEWER,
            SECURITY_AUDITOR,
            DATABASE_SPECIALIST,
            DEVOPS_ENGINEER,
        ],
        max_concurrent_workers=4,
    )

    print(f"✓ Orchestrator ready with {len(orchestrator.worker_configs)} specialized workers")
    print()

    # Project requirements
    print("Project Requirements:")
    print("-" * 80)
    requirements = """
Build a RESTful API for a blogging platform with:

Features:
- User authentication (register, login, logout)
- Blog post CRUD operations
- Comments on posts
- User profiles
- Post categories and tags
- Search functionality
- Pagination

Technical Requirements:
- Python with FastAPI framework
- PostgreSQL database
- JWT authentication
- Input validation
- Error handling
- API documentation
- Unit and integration tests
- Docker deployment
"""
    print(requirements)
    print()

    # Phase 1: Architecture and Design (Parallel)
    print("Phase 1: Architecture and Design")
    print("=" * 80)
    print()

    design_tasks = [
        """Design the RESTful API architecture for a blogging platform.

Include:
- Endpoint structure and naming
- HTTP methods and status codes
- Request/response formats
- Authentication flow
- Rate limiting strategy
- Versioning approach

Provide a complete API specification outline.""",
        """Design the database schema for a blogging platform.

Tables needed:
- users
- posts
- comments
- categories
- tags
- post_tags (many-to-many)

Include:
- Column definitions with types
- Primary and foreign keys
- Indexes for performance
- Constraints and validations

Provide SQL DDL statements.""",
    ]

    print("Running API design and database design in parallel...")
    design_results = await orchestrator.execute_parallel(design_tasks, priority=TaskPriority.HIGH)

    api_design = design_results[0]
    db_schema = design_results[1]

    print("✓ API architecture designed")
    print("✓ Database schema designed")
    print()

    # Phase 2: Core Implementation (Parallel)
    print("Phase 2: Core Implementation")
    print("=" * 80)
    print()

    implementation_tasks = [
        f"""Implement the FastAPI application for the blogging platform.

Based on this API design:
{api_design[:500]}...

Create:
- Main FastAPI app with CORS
- User authentication endpoints (register, login)
- Blog post CRUD endpoints
- Comment endpoints
- Proper error handling
- Input validation with Pydantic

Include all necessary imports and dependencies.""",
        f"""Implement the database models and repository layer.

Based on this schema:
{db_schema[:500]}...

Create:
- SQLAlchemy models for all tables
- Database connection setup
- Repository classes for data access
- Database migrations (Alembic)

Use best practices for ORM usage.""",
    ]

    print("Implementing application and database layer in parallel...")
    impl_results = await orchestrator.execute_parallel(implementation_tasks)

    app_code = impl_results[0]
    db_code = impl_results[1]

    print("✓ FastAPI application implemented")
    print("✓ Database layer implemented")
    print()

    # Phase 3: Security Review
    print("Phase 3: Security Review")
    print("=" * 80)
    print()

    security_review_task = f"""Conduct a security audit of the blogging platform API.

Review this implementation:
{app_code[:500]}...

Check for:
- Authentication vulnerabilities
- SQL injection risks
- XSS vulnerabilities
- CSRF protection
- Rate limiting
- Input validation
- Sensitive data exposure

Provide severity ratings and remediation steps."""

    print("Running security audit...")
    security_report = await orchestrator.execute(security_review_task, priority=TaskPriority.URGENT)

    print("✓ Security audit completed")
    print()

    # Phase 4: Testing and Documentation (Parallel)
    print("Phase 4: Testing and Documentation")
    print("=" * 80)
    print()

    test_and_doc_tasks = [
        f"""Generate comprehensive tests for the blogging platform API.

For this implementation:
{app_code[:500]}...

Create:
- Unit tests for all endpoints
- Integration tests for workflows
- Authentication tests
- Edge case tests
- Error handling tests

Use pytest and fixtures.""",
        f"""Write comprehensive API documentation.

Based on:
{api_design[:500]}...

Include:
- API overview and features
- Authentication guide
- Endpoint reference with examples
- Request/response schemas
- Error codes and messages
- Rate limiting information
- Quickstart guide

Format as Markdown.""",
    ]

    print("Generating tests and documentation in parallel...")
    test_doc_results = await orchestrator.execute_parallel(test_and_doc_tasks)

    tests = test_doc_results[0]
    documentation = test_doc_results[1]

    print("✓ Tests generated")
    print("✓ Documentation created")
    print()

    # Phase 5: Deployment Configuration
    print("Phase 5: Deployment Configuration")
    print("=" * 80)
    print()

    deployment_task = """Create Docker deployment configuration for the blogging platform.

Include:
- Dockerfile for the FastAPI app
- docker-compose.yml with app and PostgreSQL
- Environment variable configuration
- Health checks
- Volume mounts for persistence
- Network configuration

Make it production-ready."""

    print("Creating deployment configuration...")
    deployment_config = await orchestrator.execute(deployment_task)

    print("✓ Deployment configuration created")
    print()

    # Phase 6: Code Review and Final Report
    print("Phase 6: Final Code Review")
    print("=" * 80)
    print()

    code_review_task = f"""Conduct a comprehensive code review of the blogging platform.

Review:
- Application code
- Database models
- Tests
- Documentation

Focus on:
- Code quality and maintainability
- Best practices
- Performance considerations
- Completeness

Provide an executive summary and detailed findings."""

    print("Running final code review...")
    code_review = await orchestrator.execute(code_review_task)

    print("✓ Code review completed")
    print()

    # Generate final project report
    print("=" * 80)
    print("Generating Final Project Report")
    print("=" * 80)
    print()

    all_deliverables = [
        ("API Design", api_design),
        ("Database Schema", db_schema),
        ("Application Code", app_code),
        ("Database Code", db_code),
        ("Security Audit", security_report),
        ("Tests", tests),
        ("Documentation", documentation),
        ("Deployment Config", deployment_config),
        ("Code Review", code_review),
    ]

    report = "# Blogging Platform REST API - Final Report\n\n"
    report += "## Project Summary\n\n"
    report += f"Successfully completed all {len(all_deliverables)} deliverables using distributed orchestration.\n\n"
    report += "## Deliverables\n\n"

    for title, content in all_deliverables:
        report += f"### {title}\n\n"
        # Show first 300 chars of each deliverable
        preview = content[:300].strip()
        report += f"{preview}...\n\n"
        report += "---\n\n"

    print(report)

    # Show orchestration metrics
    print("=" * 80)
    print("Orchestration Metrics")
    print("=" * 80)
    print()

    metrics = orchestrator.get_metrics()
    print(f"Total tasks executed: {metrics['total_tasks']}")
    print(f"Successfully completed: {metrics['completed_tasks']}")
    print(f"Failed: {metrics['failed_tasks']}")
    print(f"Success rate: {metrics['success_rate']:.1%}")
    print()

    print("Worker Utilization:")
    for worker_name, stats in metrics["workers"].items():
        total = stats["tasks_completed"] + stats["tasks_failed"]
        if total > 0:
            print(f"  {worker_name}: {stats['tasks_completed']} tasks")
    print()

    # Show task breakdown
    print("Task Execution Details:")
    all_tasks = orchestrator.get_all_tasks()
    for task_id, task in all_tasks.items():
        if task.started_at and task.completed_at:
            duration = (task.completed_at - task.started_at).total_seconds()
            print(f"  {task.id}:")
            print(f"    Priority: {task.priority.name}")
            print(f"    Status: {task.status.value}")
            print(f"    Duration: {duration:.2f}s")
    print()

    print("=" * 80)
    print("✓ Project completed successfully!")
    print("=" * 80)
    print()

    print("Next Steps:")
    print("1. Review the generated code and documentation")
    print("2. Address any security findings from the audit")
    print("3. Run the test suite to verify functionality")
    print("4. Deploy using the provided Docker configuration")
    print("5. Monitor and iterate based on usage")


if __name__ == "__main__":
    asyncio.run(main())
