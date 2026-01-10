"""Tests for orchestration workflow templates."""

from __future__ import annotations

import pytest

from pydantic_deep.orchestration.models import ExecutionStrategy
from pydantic_deep.orchestration.templates import (
    create_ci_cd_pipeline,
    create_code_review_workflow,
    create_documentation_workflow,
    create_etl_pipeline,
)


def test_create_ci_cd_pipeline_basic():
    """Test creating basic CI/CD pipeline."""
    workflow = create_ci_cd_pipeline()

    assert workflow.id == "ci-cd-pipeline"
    assert workflow.name == "CI/CD Pipeline"
    assert workflow.execution_strategy == ExecutionStrategy.DAG
    assert len(workflow.tasks) >= 4  # At least lint, format, test, build


def test_create_ci_cd_pipeline_with_security():
    """Test CI/CD pipeline with security scan."""
    workflow = create_ci_cd_pipeline(run_security_scan=True)

    task_ids = [t.id for t in workflow.tasks]
    assert "security-scan" in task_ids
    assert "lint-code" in task_ids
    assert "check-formatting" in task_ids
    assert "run-tests" in task_ids
    assert "build-artifacts" in task_ids


def test_create_ci_cd_pipeline_without_security():
    """Test CI/CD pipeline without security scan."""
    workflow = create_ci_cd_pipeline(run_security_scan=False)

    task_ids = [t.id for t in workflow.tasks]
    assert "security-scan" not in task_ids
    assert "lint-code" in task_ids
    assert "run-tests" in task_ids
    assert "build-artifacts" in task_ids


def test_create_ci_cd_pipeline_with_deploy():
    """Test CI/CD pipeline with deployment."""
    workflow = create_ci_cd_pipeline(
        deploy_target="production",
        run_security_scan=True,
    )

    task_ids = [t.id for t in workflow.tasks]
    assert "deploy" in task_ids

    # Find deploy task and check dependencies
    deploy_task = next(t for t in workflow.tasks if t.id == "deploy")
    assert "build-artifacts" in deploy_task.depends_on
    assert deploy_task.parameters["deploy_target"] == "production"


def test_create_ci_cd_pipeline_without_deploy():
    """Test CI/CD pipeline without deployment."""
    workflow = create_ci_cd_pipeline(deploy_target=None)

    task_ids = [t.id for t in workflow.tasks]
    assert "deploy" not in task_ids


def test_create_ci_cd_pipeline_custom_commands():
    """Test CI/CD pipeline with custom commands."""
    workflow = create_ci_cd_pipeline(
        test_command="npm test",
        build_command="npm run build",
        repository_path="/path/to/repo",
    )

    # Find test task
    test_task = next(t for t in workflow.tasks if t.id == "run-tests")
    assert test_task.parameters["test_command"] == "npm test"

    # Find build task
    build_task = next(t for t in workflow.tasks if t.id == "build-artifacts")
    assert build_task.parameters["build_command"] == "npm run build"


def test_create_ci_cd_pipeline_dependencies():
    """Test CI/CD pipeline task dependencies."""
    workflow = create_ci_cd_pipeline(
        run_security_scan=True,
        deploy_target="staging",
    )

    # Test task should depend on lint and format
    test_task = next(t for t in workflow.tasks if t.id == "run-tests")
    assert "lint-code" in test_task.depends_on
    assert "check-formatting" in test_task.depends_on

    # Security should depend on tests
    security_task = next(t for t in workflow.tasks if t.id == "security-scan")
    assert "run-tests" in security_task.depends_on

    # Build should depend on security (when enabled)
    build_task = next(t for t in workflow.tasks if t.id == "build-artifacts")
    assert "security-scan" in build_task.depends_on

    # Deploy should depend on build
    deploy_task = next(t for t in workflow.tasks if t.id == "deploy")
    assert "build-artifacts" in deploy_task.depends_on


def test_create_etl_pipeline_basic():
    """Test creating basic ETL pipeline."""
    workflow = create_etl_pipeline()

    assert workflow.id == "etl-pipeline"
    assert workflow.name == "ETL Pipeline"
    assert workflow.execution_strategy == ExecutionStrategy.DAG
    assert len(workflow.tasks) >= 4  # Extract, validate, transform, load, verify


def test_create_etl_pipeline_multiple_sources():
    """Test ETL pipeline with multiple data sources."""
    workflow = create_etl_pipeline(
        source_configs=[
            {"type": "csv", "path": "data1.csv"},
            {"type": "json", "path": "data2.json"},
            {"type": "api", "url": "https://api.example.com"},
        ]
    )

    # Should have 3 extract tasks
    extract_tasks = [t for t in workflow.tasks if t.id.startswith("extract-")]
    assert len(extract_tasks) == 3

    # Check task IDs
    task_ids = [t.id for t in extract_tasks]
    assert "extract-csv-0" in task_ids
    assert "extract-json-1" in task_ids
    assert "extract-api-2" in task_ids


def test_create_etl_pipeline_with_validation():
    """Test ETL pipeline with data validation."""
    workflow = create_etl_pipeline(
        source_configs=[{"type": "csv", "path": "data.csv"}],
        validate_data=True,
    )

    task_ids = [t.id for t in workflow.tasks]
    assert "validate-extracted-data" in task_ids

    # Validate should depend on extract
    validate_task = next(t for t in workflow.tasks if t.id == "validate-extracted-data")
    assert "extract-csv-0" in validate_task.depends_on


def test_create_etl_pipeline_without_validation():
    """Test ETL pipeline without validation."""
    workflow = create_etl_pipeline(
        source_configs=[{"type": "csv", "path": "data.csv"}],
        validate_data=False,
    )

    task_ids = [t.id for t in workflow.tasks]
    assert "validate-extracted-data" not in task_ids

    # First transform should depend directly on extract
    transform_task = next(t for t in workflow.tasks if t.id == "transform-step-1")
    assert "extract-csv-0" in transform_task.depends_on


def test_create_etl_pipeline_transformations():
    """Test ETL pipeline with multiple transformation steps."""
    workflow = create_etl_pipeline(
        source_configs=[{"type": "csv", "path": "data.csv"}],
        transformation_steps=["clean", "normalize", "aggregate"],
        validate_data=False,
    )

    # Should have 3 transform tasks
    transform_tasks = [t for t in workflow.tasks if t.id.startswith("transform-step-")]
    assert len(transform_tasks) == 3

    # Check sequential dependencies
    step1 = next(t for t in workflow.tasks if t.id == "transform-step-1")
    assert "extract-csv-0" in step1.depends_on

    step2 = next(t for t in workflow.tasks if t.id == "transform-step-2")
    assert "transform-step-1" in step2.depends_on

    step3 = next(t for t in workflow.tasks if t.id == "transform-step-3")
    assert "transform-step-2" in step3.depends_on


def test_create_etl_pipeline_load_and_verify():
    """Test ETL pipeline load and verification."""
    workflow = create_etl_pipeline(
        source_configs=[{"type": "csv", "path": "data.csv"}],
        transformation_steps=["clean"],
        destination_config={"type": "database", "table": "output"},
    )

    # Check load task
    load_task = next(t for t in workflow.tasks if t.id == "load-to-destination")
    assert "transform-step-1" in load_task.depends_on
    assert load_task.parameters["destination_config"]["type"] == "database"

    # Check verify task
    verify_task = next(t for t in workflow.tasks if t.id == "verify-load")
    assert "load-to-destination" in verify_task.depends_on


def test_create_etl_pipeline_parallel_extraction():
    """Test that ETL pipeline allows parallel extraction."""
    workflow = create_etl_pipeline(
        source_configs=[
            {"type": "source1"},
            {"type": "source2"},
            {"type": "source3"},
        ]
    )

    # max_parallel_tasks should match number of sources for parallel extraction
    assert workflow.max_parallel_tasks == 3


def test_create_code_review_workflow_basic():
    """Test creating basic code review workflow."""
    workflow = create_code_review_workflow()

    assert workflow.id == "code-review"
    assert workflow.name == "Code Review Workflow"
    assert workflow.execution_strategy == ExecutionStrategy.DAG
    assert workflow.continue_on_failure is True  # Should continue even if some checks fail


def test_create_code_review_workflow_default_tasks():
    """Test code review workflow has default review tasks."""
    workflow = create_code_review_workflow()

    task_ids = [t.id for t in workflow.tasks]
    assert "analyze-code-structure" in task_ids
    assert "check-code-quality" in task_ids


def test_create_code_review_workflow_with_security():
    """Test code review workflow with security focus."""
    workflow = create_code_review_workflow(
        review_focus=["security", "quality"]
    )

    task_ids = [t.id for t in workflow.tasks]
    assert "security-review" in task_ids
    assert "check-code-quality" in task_ids


def test_create_code_review_workflow_with_documentation():
    """Test code review workflow with documentation review."""
    workflow = create_code_review_workflow(
        review_focus=["documentation", "quality"]
    )

    task_ids = [t.id for t in workflow.tasks]
    assert "review-documentation" in task_ids


def test_create_code_review_workflow_with_testing():
    """Test code review workflow with test evaluation."""
    workflow = create_code_review_workflow(
        review_focus=["testing", "quality"]
    )

    task_ids = [t.id for t in workflow.tasks]
    assert "evaluate-test-coverage" in task_ids


def test_create_code_review_workflow_with_report():
    """Test code review workflow with report generation."""
    workflow = create_code_review_workflow(
        review_focus=["security", "quality"],
        generate_report=True,
    )

    task_ids = [t.id for t in workflow.tasks]
    assert "generate-review-report" in task_ids

    # Report should depend on all analysis tasks
    report_task = next(t for t in workflow.tasks if t.id == "generate-review-report")
    assert "analyze-code-structure" in report_task.depends_on
    assert "check-code-quality" in report_task.depends_on
    assert "security-review" in report_task.depends_on


def test_create_code_review_workflow_without_report():
    """Test code review workflow without report."""
    workflow = create_code_review_workflow(generate_report=False)

    task_ids = [t.id for t in workflow.tasks]
    assert "generate-review-report" not in task_ids


def test_create_code_review_workflow_with_auto_fix():
    """Test code review workflow with auto-fix enabled."""
    workflow = create_code_review_workflow(
        generate_report=True,
        auto_fix=True,
    )

    task_ids = [t.id for t in workflow.tasks]
    assert "apply-auto-fixes" in task_ids
    assert "verify-fixes" in task_ids

    # Auto-fix should depend on report
    fix_task = next(t for t in workflow.tasks if t.id == "apply-auto-fixes")
    assert "generate-review-report" in fix_task.depends_on

    # Verify should depend on auto-fix
    verify_task = next(t for t in workflow.tasks if t.id == "verify-fixes")
    assert "apply-auto-fixes" in verify_task.depends_on


def test_create_code_review_workflow_auto_fix_without_report():
    """Test code review workflow with auto-fix but no report."""
    workflow = create_code_review_workflow(
        generate_report=False,
        auto_fix=True,
    )

    task_ids = [t.id for t in workflow.tasks]
    assert "apply-auto-fixes" in task_ids

    # Auto-fix should depend on analysis tasks when no report
    fix_task = next(t for t in workflow.tasks if t.id == "apply-auto-fixes")
    assert "analyze-code-structure" in fix_task.depends_on
    assert "check-code-quality" in fix_task.depends_on


def test_create_code_review_workflow_target_files():
    """Test code review workflow with specific target files."""
    workflow = create_code_review_workflow(
        repository_path="/path/to/repo",
        target_files=["file1.py", "file2.py"],
    )

    # Check that tasks have target files in parameters
    structure_task = next(t for t in workflow.tasks if t.id == "analyze-code-structure")
    assert structure_task.parameters["target_files"] == ["file1.py", "file2.py"]
    assert structure_task.parameters["repository_path"] == "/path/to/repo"


def test_create_documentation_workflow_basic():
    """Test creating basic documentation workflow."""
    workflow = create_documentation_workflow()

    assert workflow.id == "documentation-generation"
    assert workflow.name == "Documentation Generation"
    assert workflow.execution_strategy == ExecutionStrategy.DAG


def test_create_documentation_workflow_analyze_codebase():
    """Test documentation workflow starts with codebase analysis."""
    workflow = create_documentation_workflow()

    task_ids = [t.id for t in workflow.tasks]
    assert "analyze-codebase" in task_ids

    # Other tasks should depend on analyze
    for task in workflow.tasks:
        if task.id != "analyze-codebase" and task.id != "build-documentation":
            assert "analyze-codebase" in task.depends_on


def test_create_documentation_workflow_api_docs():
    """Test documentation workflow with API docs."""
    workflow = create_documentation_workflow(
        doc_types=["api"],
        output_format="markdown",
    )

    task_ids = [t.id for t in workflow.tasks]
    assert "generate-api-docs" in task_ids

    api_task = next(t for t in workflow.tasks if t.id == "generate-api-docs")
    assert api_task.parameters["output_format"] == "markdown"


def test_create_documentation_workflow_user_guide():
    """Test documentation workflow with user guide."""
    workflow = create_documentation_workflow(
        doc_types=["guide"],
        output_format="rst",
    )

    task_ids = [t.id for t in workflow.tasks]
    assert "write-user-guide" in task_ids

    guide_task = next(t for t in workflow.tasks if t.id == "write-user-guide")
    assert guide_task.parameters["output_format"] == "rst"


def test_create_documentation_workflow_tutorial():
    """Test documentation workflow with tutorial."""
    workflow = create_documentation_workflow(
        doc_types=["tutorial"],
        output_format="html",
    )

    task_ids = [t.id for t in workflow.tasks]
    assert "create-tutorial" in task_ids


def test_create_documentation_workflow_multiple_doc_types():
    """Test documentation workflow with multiple doc types."""
    workflow = create_documentation_workflow(
        doc_types=["api", "guide", "tutorial"],
    )

    task_ids = [t.id for t in workflow.tasks]
    assert "generate-api-docs" in task_ids
    assert "write-user-guide" in task_ids
    assert "create-tutorial" in task_ids


def test_create_documentation_workflow_with_examples():
    """Test documentation workflow with examples."""
    workflow = create_documentation_workflow(
        doc_types=["api"],
        include_examples=True,
    )

    task_ids = [t.id for t in workflow.tasks]
    assert "generate-examples" in task_ids


def test_create_documentation_workflow_without_examples():
    """Test documentation workflow without examples."""
    workflow = create_documentation_workflow(
        doc_types=["api"],
        include_examples=False,
    )

    task_ids = [t.id for t in workflow.tasks]
    assert "generate-examples" not in task_ids


def test_create_documentation_workflow_build_dependencies():
    """Test documentation workflow build dependencies."""
    workflow = create_documentation_workflow(
        doc_types=["api", "guide"],
        include_examples=True,
    )

    # Build should depend on all doc generation tasks
    build_task = next(t for t in workflow.tasks if t.id == "build-documentation")
    assert "generate-api-docs" in build_task.depends_on
    assert "write-user-guide" in build_task.depends_on
    assert "generate-examples" in build_task.depends_on


def test_create_documentation_workflow_custom_repository():
    """Test documentation workflow with custom repository."""
    workflow = create_documentation_workflow(
        repository_path="/custom/path",
        doc_types=["api"],
    )

    analyze_task = next(t for t in workflow.tasks if t.id == "analyze-codebase")
    assert analyze_task.parameters["repository_path"] == "/custom/path"


def test_all_templates_return_workflow_definition():
    """Test that all templates return valid WorkflowDefinition."""
    from pydantic_deep.orchestration.models import WorkflowDefinition

    templates = [
        create_ci_cd_pipeline(),
        create_etl_pipeline(),
        create_code_review_workflow(),
        create_documentation_workflow(),
    ]

    for workflow in templates:
        assert isinstance(workflow, WorkflowDefinition)
        assert workflow.id
        assert workflow.name
        assert len(workflow.tasks) > 0
        assert workflow.execution_strategy in ExecutionStrategy


def test_all_templates_accept_custom_workflow_kwargs():
    """Test that all templates accept custom workflow parameters."""
    custom_kwargs = {
        "default_timeout_seconds": 300.0,
        "max_parallel_tasks": 10,
        "continue_on_failure": True,
        "metadata": {"custom": "value"},
    }

    workflows = [
        create_ci_cd_pipeline(**custom_kwargs),
        create_etl_pipeline(**custom_kwargs),
        create_code_review_workflow(**custom_kwargs),
        create_documentation_workflow(**custom_kwargs),
    ]

    for workflow in workflows:
        assert workflow.default_timeout_seconds == 300.0
        assert workflow.max_parallel_tasks == 10
        assert workflow.metadata == {"custom": "value"}
