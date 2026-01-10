"""Reusable workflow templates for common patterns.

This module provides pre-built workflow templates for common use cases,
making it easy to create standard workflows without manually defining tasks.
"""

from __future__ import annotations

from typing import Any

from pydantic_deep.orchestration.models import (
    AgentCapability,
    ExecutionStrategy,
    RetryConfig,
    TaskDefinition,
    WorkflowDefinition,
)


def create_ci_cd_pipeline(
    workflow_id: str = "ci-cd-pipeline",
    repository_path: str | None = None,
    test_command: str = "pytest",
    build_command: str = "python -m build",
    deploy_target: str | None = None,
    run_security_scan: bool = True,
    **workflow_kwargs: Any,
) -> WorkflowDefinition:
    """Create a comprehensive CI/CD pipeline workflow.

    This template creates a workflow that:
    1. Validates code quality (linting, formatting)
    2. Runs tests
    3. Performs security scanning (optional)
    4. Builds artifacts
    5. Deploys to target environment (optional)

    Args:
        workflow_id: Unique workflow identifier.
        repository_path: Path to code repository. If None, uses current directory.
        test_command: Command to run tests. Default: "pytest".
        build_command: Command to build artifacts. Default: "python -m build".
        deploy_target: Deployment target (e.g., "staging", "production"). If None, skips deploy.
        run_security_scan: Whether to include security scanning step. Default: True.
        **workflow_kwargs: Additional workflow configuration parameters.

    Returns:
        Configured CI/CD workflow definition.

    Example:
        ```python
        from pydantic_deep.orchestration import TaskOrchestrator, create_ci_cd_pipeline

        orchestrator = TaskOrchestrator(agent, deps)
        workflow = create_ci_cd_pipeline(
            repository_path="/path/to/repo",
            deploy_target="staging"
        )
        result = await orchestrator.execute_workflow(workflow)
        ```
    """
    tasks = [
        # Phase 1: Code Quality
        TaskDefinition(
            id="lint-code",
            description=f"Run linting checks on code in {repository_path or 'current directory'}",
            required_capabilities=[AgentCapability.CODE_ANALYSIS],
            priority=10,
            parameters={"repository_path": repository_path},
        ),
        TaskDefinition(
            id="check-formatting",
            description=f"Verify code formatting in {repository_path or 'current directory'}",
            required_capabilities=[AgentCapability.CODE_ANALYSIS],
            priority=10,
            parameters={"repository_path": repository_path},
        ),
        # Phase 2: Testing
        TaskDefinition(
            id="run-tests",
            description=f"Run test suite using command: {test_command}",
            depends_on=["lint-code", "check-formatting"],
            required_capabilities=[AgentCapability.TESTING],
            priority=9,
            parameters={
                "test_command": test_command,
                "repository_path": repository_path,
            },
            retry_config=RetryConfig(max_retries=2),
        ),
    ]

    # Phase 3: Security (optional)
    if run_security_scan:
        tasks.append(
            TaskDefinition(
                id="security-scan",
                description=f"Run security vulnerability scan on {repository_path or 'current directory'}",
                depends_on=["run-tests"],
                required_capabilities=[AgentCapability.CODE_ANALYSIS],
                priority=8,
                parameters={"repository_path": repository_path},
            )
        )

    # Phase 4: Build
    build_deps = ["security-scan"] if run_security_scan else ["run-tests"]
    tasks.append(
        TaskDefinition(
            id="build-artifacts",
            description=f"Build project artifacts using command: {build_command}",
            depends_on=build_deps,
            required_capabilities=[AgentCapability.CODE_GENERATION],
            priority=7,
            parameters={
                "build_command": build_command,
                "repository_path": repository_path,
            },
            retry_config=RetryConfig(max_retries=1),
        )
    )

    # Phase 5: Deploy (optional)
    if deploy_target:
        tasks.append(
            TaskDefinition(
                id="deploy",
                description=f"Deploy artifacts to {deploy_target} environment",
                depends_on=["build-artifacts"],
                required_capabilities=[AgentCapability.FILE_OPERATIONS],
                priority=6,
                parameters={
                    "deploy_target": deploy_target,
                    "repository_path": repository_path,
                },
                retry_config=RetryConfig(max_retries=3, initial_delay=2.0),
            )
        )

    # Create workflow with DAG strategy for parallel execution where possible
    return WorkflowDefinition(
        id=workflow_id,
        name="CI/CD Pipeline",
        description="Automated continuous integration and deployment pipeline",
        tasks=tasks,
        execution_strategy=ExecutionStrategy.DAG,
        max_parallel_tasks=3,
        continue_on_failure=False,
        **workflow_kwargs,
    )


def create_etl_pipeline(
    workflow_id: str = "etl-pipeline",
    source_configs: list[dict[str, Any]] | None = None,
    transformation_steps: list[str] | None = None,
    destination_config: dict[str, Any] | None = None,
    validate_data: bool = True,
    **workflow_kwargs: Any,
) -> WorkflowDefinition:
    """Create an ETL (Extract, Transform, Load) data pipeline workflow.

    This template creates a workflow that:
    1. Extracts data from multiple sources
    2. Validates extracted data (optional)
    3. Applies transformation steps
    4. Loads data into destination
    5. Verifies load success

    Args:
        workflow_id: Unique workflow identifier.
        source_configs: List of source configurations for data extraction.
            Each config should specify the source type and connection details.
        transformation_steps: List of transformation descriptions to apply.
        destination_config: Configuration for data destination.
        validate_data: Whether to validate data after extraction. Default: True.
        **workflow_kwargs: Additional workflow configuration parameters.

    Returns:
        Configured ETL workflow definition.

    Example:
        ```python
        from pydantic_deep.orchestration import TaskOrchestrator, create_etl_pipeline

        orchestrator = TaskOrchestrator(agent, deps)
        workflow = create_etl_pipeline(
            source_configs=[
                {"type": "csv", "path": "data/input.csv"},
                {"type": "api", "url": "https://api.example.com/data"}
            ],
            transformation_steps=["clean nulls", "normalize values", "aggregate by date"],
            destination_config={"type": "database", "table": "processed_data"}
        )
        result = await orchestrator.execute_workflow(workflow)
        ```
    """
    source_configs = source_configs or [{"type": "default", "path": "data/"}]
    transformation_steps = transformation_steps or ["clean and normalize data"]
    destination_config = destination_config or {"type": "file", "path": "output/"}

    tasks = []

    # Phase 1: Extract - Create parallel extraction tasks for each source
    for idx, source_config in enumerate(source_configs):
        source_type = source_config.get("type", "unknown")
        tasks.append(
            TaskDefinition(
                id=f"extract-{source_type}-{idx}",
                description=f"Extract data from {source_type} source: {source_config}",
                required_capabilities=[AgentCapability.DATA_PROCESSING],
                priority=10,
                parameters={"source_config": source_config},
                retry_config=RetryConfig(max_retries=3, initial_delay=1.0),
            )
        )

    # Collect extraction task IDs
    extract_task_ids = [f"extract-{src.get('type', 'unknown')}-{i}" for i, src in enumerate(source_configs)]

    # Phase 2: Validate (optional)
    if validate_data:
        tasks.append(
            TaskDefinition(
                id="validate-extracted-data",
                description="Validate extracted data for completeness and quality",
                depends_on=extract_task_ids,
                required_capabilities=[AgentCapability.DATA_PROCESSING],
                priority=9,
                parameters={"validation_rules": "standard"},
            )
        )
        previous_step = ["validate-extracted-data"]
    else:
        previous_step = extract_task_ids

    # Phase 3: Transform - Apply transformation steps sequentially
    for idx, transform_step in enumerate(transformation_steps):
        task_id = f"transform-step-{idx + 1}"
        tasks.append(
            TaskDefinition(
                id=task_id,
                description=f"Transform data: {transform_step}",
                depends_on=previous_step,
                required_capabilities=[AgentCapability.DATA_PROCESSING],
                priority=8 - idx,  # Decreasing priority for sequential steps
                parameters={"transformation": transform_step},
            )
        )
        previous_step = [task_id]

    # Phase 4: Load
    tasks.append(
        TaskDefinition(
            id="load-to-destination",
            description=f"Load transformed data to destination: {destination_config}",
            depends_on=previous_step,
            required_capabilities=[AgentCapability.DATA_PROCESSING],
            priority=5,
            parameters={"destination_config": destination_config},
            retry_config=RetryConfig(max_retries=3, initial_delay=2.0),
        )
    )

    # Phase 5: Verify
    tasks.append(
        TaskDefinition(
            id="verify-load",
            description="Verify data was successfully loaded to destination",
            depends_on=["load-to-destination"],
            required_capabilities=[AgentCapability.DATA_PROCESSING],
            priority=4,
            parameters={"destination_config": destination_config},
        )
    )

    return WorkflowDefinition(
        id=workflow_id,
        name="ETL Pipeline",
        description="Extract, Transform, Load data pipeline",
        tasks=tasks,
        execution_strategy=ExecutionStrategy.DAG,
        max_parallel_tasks=len(source_configs),  # Parallel extraction
        continue_on_failure=False,
        **workflow_kwargs,
    )


def create_code_review_workflow(
    workflow_id: str = "code-review",
    repository_path: str | None = None,
    target_files: list[str] | None = None,
    review_focus: list[str] | None = None,
    generate_report: bool = True,
    auto_fix: bool = False,
    **workflow_kwargs: Any,
) -> WorkflowDefinition:
    """Create a comprehensive code review workflow.

    This template creates a workflow that:
    1. Analyzes code structure and quality
    2. Checks for security vulnerabilities
    3. Reviews documentation completeness
    4. Evaluates test coverage
    5. Generates review report (optional)
    6. Suggests or applies fixes (optional)

    Args:
        workflow_id: Unique workflow identifier.
        repository_path: Path to code repository. If None, uses current directory.
        target_files: Specific files to review. If None, reviews all files.
        review_focus: Specific areas to focus on (e.g., ["security", "performance", "maintainability"]).
        generate_report: Whether to generate a comprehensive review report. Default: True.
        auto_fix: Whether to automatically apply fixes for simple issues. Default: False.
        **workflow_kwargs: Additional workflow configuration parameters.

    Returns:
        Configured code review workflow definition.

    Example:
        ```python
        from pydantic_deep.orchestration import TaskOrchestrator, create_code_review_workflow

        orchestrator = TaskOrchestrator(agent, deps)
        workflow = create_code_review_workflow(
            repository_path="/path/to/repo",
            review_focus=["security", "performance"],
            generate_report=True
        )
        result = await orchestrator.execute_workflow(workflow)
        ```
    """
    review_focus = review_focus or ["quality", "security", "documentation", "testing"]
    target_description = f"files: {target_files}" if target_files else "all files"

    tasks = [
        # Phase 1: Parallel analysis tasks
        TaskDefinition(
            id="analyze-code-structure",
            description=f"Analyze code structure and organization in {repository_path or 'current directory'} ({target_description})",
            required_capabilities=[AgentCapability.CODE_ANALYSIS],
            priority=10,
            parameters={
                "repository_path": repository_path,
                "target_files": target_files,
                "focus": "structure",
            },
        ),
        TaskDefinition(
            id="check-code-quality",
            description=f"Review code quality and best practices in {repository_path or 'current directory'} ({target_description})",
            required_capabilities=[AgentCapability.CODE_ANALYSIS],
            priority=10,
            parameters={
                "repository_path": repository_path,
                "target_files": target_files,
                "focus": "quality",
            },
        ),
    ]

    # Add focused review tasks
    if "security" in review_focus:
        tasks.append(
            TaskDefinition(
                id="security-review",
                description=f"Analyze code for security vulnerabilities in {repository_path or 'current directory'}",
                required_capabilities=[AgentCapability.CODE_ANALYSIS],
                priority=10,
                parameters={
                    "repository_path": repository_path,
                    "target_files": target_files,
                    "focus": "security",
                },
            )
        )

    if "documentation" in review_focus:
        tasks.append(
            TaskDefinition(
                id="review-documentation",
                description=f"Review documentation completeness and quality in {repository_path or 'current directory'}",
                required_capabilities=[AgentCapability.DOCUMENTATION],
                priority=9,
                parameters={
                    "repository_path": repository_path,
                    "target_files": target_files,
                },
            )
        )

    if "testing" in review_focus:
        tasks.append(
            TaskDefinition(
                id="evaluate-test-coverage",
                description=f"Evaluate test coverage and quality in {repository_path or 'current directory'}",
                required_capabilities=[AgentCapability.TESTING],
                priority=9,
                parameters={
                    "repository_path": repository_path,
                    "target_files": target_files,
                },
            )
        )

    # Collect analysis task IDs
    analysis_task_ids = [t.id for t in tasks]

    # Phase 2: Generate report (optional)
    if generate_report:
        tasks.append(
            TaskDefinition(
                id="generate-review-report",
                description="Generate comprehensive code review report with findings and recommendations",
                depends_on=analysis_task_ids,
                required_capabilities=[AgentCapability.DOCUMENTATION],
                priority=7,
                parameters={
                    "repository_path": repository_path,
                    "review_focus": review_focus,
                },
            )
        )

    # Phase 3: Auto-fix (optional)
    if auto_fix:
        fix_depends_on = ["generate-review-report"] if generate_report else analysis_task_ids
        tasks.append(
            TaskDefinition(
                id="apply-auto-fixes",
                description="Apply automatic fixes for simple issues identified in review",
                depends_on=fix_depends_on,
                required_capabilities=[AgentCapability.CODE_GENERATION],
                priority=6,
                parameters={
                    "repository_path": repository_path,
                    "target_files": target_files,
                },
            )
        )

        # Verify fixes
        tasks.append(
            TaskDefinition(
                id="verify-fixes",
                description="Verify that applied fixes are correct and don't break functionality",
                depends_on=["apply-auto-fixes"],
                required_capabilities=[AgentCapability.TESTING],
                priority=5,
                parameters={
                    "repository_path": repository_path,
                },
            )
        )

    return WorkflowDefinition(
        id=workflow_id,
        name="Code Review Workflow",
        description="Comprehensive automated code review",
        tasks=tasks,
        execution_strategy=ExecutionStrategy.DAG,
        max_parallel_tasks=4,  # Parallel review tasks
        continue_on_failure=True,  # Continue even if some checks fail
        **workflow_kwargs,
    )


def create_documentation_workflow(
    workflow_id: str = "documentation-generation",
    repository_path: str | None = None,
    doc_types: list[str] | None = None,
    output_format: str = "markdown",
    include_examples: bool = True,
    **workflow_kwargs: Any,
) -> WorkflowDefinition:
    """Create a documentation generation workflow.

    This template creates a workflow that:
    1. Analyzes codebase structure
    2. Generates API documentation
    3. Creates usage examples (optional)
    4. Writes user guides
    5. Builds final documentation

    Args:
        workflow_id: Unique workflow identifier.
        repository_path: Path to code repository. If None, uses current directory.
        doc_types: Types of documentation to generate (e.g., ["api", "guide", "tutorial"]).
        output_format: Format for documentation (e.g., "markdown", "rst", "html"). Default: "markdown".
        include_examples: Whether to generate code examples. Default: True.
        **workflow_kwargs: Additional workflow configuration parameters.

    Returns:
        Configured documentation workflow definition.
    """
    doc_types = doc_types or ["api", "guide"]

    tasks = [
        TaskDefinition(
            id="analyze-codebase",
            description=f"Analyze codebase structure in {repository_path or 'current directory'}",
            required_capabilities=[AgentCapability.CODE_ANALYSIS],
            priority=10,
            parameters={"repository_path": repository_path},
        ),
    ]

    # Generate different documentation types in parallel
    doc_task_ids = []
    if "api" in doc_types:
        doc_task_ids.append("generate-api-docs")
        tasks.append(
            TaskDefinition(
                id="generate-api-docs",
                description=f"Generate API documentation in {output_format} format",
                depends_on=["analyze-codebase"],
                required_capabilities=[AgentCapability.DOCUMENTATION],
                priority=9,
                parameters={
                    "repository_path": repository_path,
                    "output_format": output_format,
                },
            )
        )

    if "guide" in doc_types:
        doc_task_ids.append("write-user-guide")
        tasks.append(
            TaskDefinition(
                id="write-user-guide",
                description=f"Write user guide in {output_format} format",
                depends_on=["analyze-codebase"],
                required_capabilities=[AgentCapability.DOCUMENTATION],
                priority=9,
                parameters={
                    "repository_path": repository_path,
                    "output_format": output_format,
                },
            )
        )

    if "tutorial" in doc_types:
        doc_task_ids.append("create-tutorial")
        tasks.append(
            TaskDefinition(
                id="create-tutorial",
                description=f"Create step-by-step tutorial in {output_format} format",
                depends_on=["analyze-codebase"],
                required_capabilities=[AgentCapability.DOCUMENTATION],
                priority=9,
                parameters={
                    "repository_path": repository_path,
                    "output_format": output_format,
                },
            )
        )

    if include_examples:
        tasks.append(
            TaskDefinition(
                id="generate-examples",
                description="Generate code examples and usage snippets",
                depends_on=["analyze-codebase"],
                required_capabilities=[AgentCapability.CODE_GENERATION],
                priority=9,
                parameters={"repository_path": repository_path},
            )
        )
        doc_task_ids.append("generate-examples")

    # Build final documentation
    tasks.append(
        TaskDefinition(
            id="build-documentation",
            description=f"Build final documentation in {output_format} format",
            depends_on=doc_task_ids,
            required_capabilities=[AgentCapability.FILE_OPERATIONS],
            priority=8,
            parameters={
                "repository_path": repository_path,
                "output_format": output_format,
            },
        )
    )

    return WorkflowDefinition(
        id=workflow_id,
        name="Documentation Generation",
        description="Automated documentation generation workflow",
        tasks=tasks,
        execution_strategy=ExecutionStrategy.DAG,
        max_parallel_tasks=4,
        **workflow_kwargs,
    )


__all__ = [
    "create_ci_cd_pipeline",
    "create_etl_pipeline",
    "create_code_review_workflow",
    "create_documentation_workflow",
]
