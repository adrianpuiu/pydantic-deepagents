"""pydantic-deep: Deep agent framework built on pydantic-ai.

This library provides a deep agent framework with:
- Planning via TodoToolset
- Filesystem operations via FilesystemToolset
- Subagent delegation via SubAgentToolset
- Multiple backend options for file storage
- Structured output support via output_type
- History processing/summarization for long conversations

Example:
    ```python
    from pydantic import BaseModel
    from pydantic_deep import create_deep_agent, DeepAgentDeps, StateBackend
    from pydantic_deep.processors import create_summarization_processor

    # Create agent with all capabilities
    agent = create_deep_agent(
        model="openai:gpt-4.1",
        instructions="You are a helpful coding assistant",
        interrupt_on={"execute": True},
    )

    # With structured output
    class Analysis(BaseModel):
        summary: str
        issues: list[str]

    agent = create_deep_agent(
        output_type=Analysis,
        history_processors=[
            create_summarization_processor(
                trigger=("tokens", 100000),
                keep=("messages", 20),
            )
        ],
    )

    # Create dependencies
    deps = DeepAgentDeps(backend=StateBackend())

    # Run agent
    result = await agent.run("Create a Python script", deps=deps)
    print(result.output)
    ```
"""

from pydantic_ai_backends import (
    BUILTIN_RUNTIMES,
    BackendProtocol,
    BaseSandbox,
    CompositeBackend,
    DockerSandbox,
    EditResult,
    ExecuteResponse,
    FileData,
    FileInfo,
    FilesystemBackend,
    GrepMatch,
    LocalSandbox,
    RuntimeConfig,
    SandboxProtocol,
    SessionManager,
    StateBackend,
    WriteResult,
    get_runtime,
)

from pydantic_deep.agent import create_deep_agent, create_default_deps, run_with_files
from pydantic_deep.deps import DeepAgentDeps
from pydantic_deep.orchestration import (
    AgentCapability,
    AgentRouting,
    CacheConfig,
    CacheStrategy,
    DAGVisualizer,
    ExecutionStrategy,
    MetricsCollector,
    OrchestrationConfig,
    ResultCache,
    RetryConfig,
    SkillManager,
    StateManager,
    TaskDefinition,
    TaskMetrics,
    TaskOrchestrator,
    TaskResult,
    TaskRouter,
    TaskStatus,
    VisualizationFormat,
    WorkflowDefinition,
    WorkflowMetrics,
    WorkflowState,
    auto_select_strategy,
    create_ci_cd_pipeline,
    create_code_review_workflow,
    create_default_routing,
    create_documentation_workflow,
    create_etl_pipeline,
    create_orchestrator,
    explain_strategy_choice,
    recommend_strategy,
    visualize_workflow,
)
from pydantic_deep.processors import (
    SummarizationProcessor,
    create_summarization_processor,
)
from pydantic_deep.toolsets import FilesystemToolset, SkillsToolset, SubAgentToolset, TodoToolset
from pydantic_deep.types import (
    CompiledSubAgent,
    ResponseFormat,
    Skill,
    SkillDirectory,
    SkillFrontmatter,
    SubAgentConfig,
    Todo,
    UploadedFile,
)

__version__ = "0.1.0"

__all__ = [
    # Main entry points
    "create_deep_agent",
    "create_default_deps",
    "run_with_files",
    "DeepAgentDeps",
    # Backends
    "BackendProtocol",
    "SandboxProtocol",
    "StateBackend",
    "FilesystemBackend",
    "CompositeBackend",
    "BaseSandbox",
    "DockerSandbox",
    "LocalSandbox",
    # Runtimes
    "RuntimeConfig",
    "BUILTIN_RUNTIMES",
    "get_runtime",
    # Session Management
    "SessionManager",
    # Toolsets
    "TodoToolset",
    "FilesystemToolset",
    "SubAgentToolset",
    "SkillsToolset",
    # Processors
    "SummarizationProcessor",
    "create_summarization_processor",
    # Orchestration
    "TaskOrchestrator",
    "create_orchestrator",
    "TaskDefinition",
    "WorkflowDefinition",
    "TaskResult",
    "WorkflowState",
    "TaskStatus",
    "ExecutionStrategy",
    "AgentCapability",
    "AgentRouting",
    "OrchestrationConfig",
    "RetryConfig",
    "TaskRouter",
    "create_default_routing",
    "StateManager",
    "SkillManager",
    # Strategy Selection
    "auto_select_strategy",
    "recommend_strategy",
    "explain_strategy_choice",
    # Metrics
    "MetricsCollector",
    "TaskMetrics",
    "WorkflowMetrics",
    # Templates
    "create_ci_cd_pipeline",
    "create_etl_pipeline",
    "create_code_review_workflow",
    "create_documentation_workflow",
    # Caching
    "ResultCache",
    "CacheConfig",
    "CacheStrategy",
    # Visualization
    "DAGVisualizer",
    "VisualizationFormat",
    "visualize_workflow",
    # Types
    "FileData",
    "FileInfo",
    "WriteResult",
    "EditResult",
    "ExecuteResponse",
    "GrepMatch",
    "Todo",
    "SubAgentConfig",
    "CompiledSubAgent",
    "Skill",
    "SkillDirectory",
    "SkillFrontmatter",
    "UploadedFile",
    "ResponseFormat",
]
