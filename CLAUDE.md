# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Core Development Tasks

- **Install dependencies**: `make install` (requires uv and pre-commit)
- **Run all checks**: `make all` or `pre-commit run --all-files`
- **Run tests**: `make test`
- **Run tests with HTML coverage**: `make testcov` (generates htmlcov/ directory)
- **Format code**: `make format` (runs ruff format and auto-fixes)
- **Lint code**: `make lint` (runs ruff format check and linting)
- **Type check**: `make typecheck` (Pyright) or `make typecheck-both` (Pyright + MyPy)
- **Build docs**: `make docs` or `make docs-serve` (local development)

### Single Test Commands

- **Run specific test**: `uv run pytest tests/test_agent.py::test_function_name -v`
- **Run test file**: `uv run pytest tests/test_agent.py -v`
- **Run with debug**: `uv run pytest tests/test_agent.py -v -s`

## Project Architecture

### Relationship to pydantic-ai

pydantic-deep is built on top of [pydantic-ai](https://github.com/pydantic/pydantic-ai) and extends it with:
- **Toolsets**: Pre-built tool collections (todo, filesystem, subagents, skills)
- **Backends**: Pluggable file storage (in-memory, filesystem, Docker, composite)
- **SubAgents**: Task delegation to specialized agents
- **Skills**: Modular skill packages loaded from markdown files
- **History Processors**: Conversation summarization for token management

The core `Agent` class from pydantic-ai is wrapped by `create_deep_agent()` which configures the agent with these extensions. All pydantic-ai features (models, tools, result types) work with pydantic-deep agents.

### Core Components

**Agent Factory (`pydantic_deep/agent.py`)**
- `create_deep_agent()`: Main factory function for creating configured agents
- `create_default_deps()`: Helper for creating DeepAgentDeps with sensible defaults
- Built on top of pydantic-ai's Agent class

**Dependencies (`pydantic_deep/deps.py`)**
- `DeepAgentDeps`: Dataclass holding agent dependencies (backend, working_dir, skills_dirs, subagents)
- Passed to agent.run() for runtime configuration

**Backends (`pydantic_deep/backends/`)**
- `BackendProtocol`: Interface for file storage backends
- `StateBackend`: In-memory file storage (for testing, ephemeral use)
- `FilesystemBackend`: Real filesystem operations
- `DockerSandbox`: Isolated Docker container execution
- `CompositeBackend`: Combines multiple backends with routing

**Toolsets (`pydantic_deep/toolsets/`)**
- `TodoToolset`: Task planning and tracking tools (read_todos, write_todos)
- `FilesystemToolset`: File operations (read, write, edit, glob, grep, mkdir, execute)
- `SubAgentToolset`: Spawn and delegate to subagents
- `SkillsToolset`: Load and use skill definitions from markdown files

**Processors (`pydantic_deep/processors/`)**
- `SummarizationProcessor`: Automatic conversation summarization for token management
- `create_summarization_processor()`: Factory function for creating summarization processors

**Types (`pydantic_deep/types.py`)**
- Pydantic models for all data structures
- `FileData`, `FileInfo`, `WriteResult`, `EditResult`, `GrepMatch`
- `Todo`, `SubAgentConfig`, `CompiledSubAgent`
- `Skill`, `SkillDirectory`, `SkillFrontmatter`
- `ResponseFormat`: Alias for structured output specification

### Key Design Patterns

**Backend Abstraction**
```python
from pydantic_deep import StateBackend, FilesystemBackend, CompositeBackend

# In-memory for testing
backend = StateBackend()

# Real filesystem
backend = FilesystemBackend(root="/path/to/workspace")

# Combined backends
backend = CompositeBackend(backends=[StateBackend(), FilesystemBackend()])
```

**Toolset Registration**
```python
from pydantic_deep import create_deep_agent, DeepAgentDeps
from pydantic_deep.toolsets import TodoToolset, FilesystemToolset

agent = create_deep_agent(
    model="openai:gpt-4.1",
    toolsets=[TodoToolset(), FilesystemToolset()],
)
```

**Skills System**
```python
# Skills are markdown files with YAML frontmatter
# Located in skills_dirs specified in DeepAgentDeps
deps = DeepAgentDeps(
    backend=StateBackend(),
    skills_dirs=["/path/to/skills"],
)

# Or pass to create_deep_agent
agent = create_deep_agent(
    model="openai:gpt-4.1",
    skill_directories=[
        {"path": "/path/to/skills", "recursive": True}
    ],
)
```

Skills are markdown files in a directory structure:
```
skills/
├── code-review/
│   └── SKILL.md
└── test-generator/
    └── SKILL.md
```

Each `SKILL.md` file has YAML frontmatter:
```yaml
---
name: code-review
description: Reviews code for quality and security
tags: [code, review, security]
version: "1.0"
---

# Code Review Skill

Instructions for the agent when this skill is loaded...
```

The agent can use the `list_skills` tool to see available skills and `load_skill` to access their instructions.

**Structured Output**
```python
from pydantic import BaseModel
from pydantic_deep import create_deep_agent

class TaskResult(BaseModel):
    status: str
    details: str

# Agent returns TaskResult instead of str
agent = create_deep_agent(output_type=TaskResult)
```

**Context Management / Summarization**
```python
from pydantic_deep import create_deep_agent
from pydantic_deep.processors import create_summarization_processor

# Automatically summarize when reaching token limits
processor = create_summarization_processor(
    trigger=("tokens", 100000),  # or ("messages", 50) or ("fraction", 0.8)
    keep=("messages", 20),       # Keep last N messages after summarization
)

agent = create_deep_agent(history_processors=[processor])
```

**SubAgents and Distributed Orchestration**
```python
from pydantic_deep.types import SubAgentConfig

# Define specialized subagents
subagents = [
    SubAgentConfig(
        name="code-reviewer",
        description="Reviews code for bugs and best practices",
        instructions="You are an expert code reviewer...",
    ),
    SubAgentConfig(
        name="test-writer",
        description="Generates comprehensive unit tests",
        instructions="You are a test engineering expert...",
    ),
]

# Create agent that can delegate to subagents
agent = create_deep_agent(
    model="openai:gpt-4.1",
    subagents=subagents,
)

# Agent can use the 'task' tool to delegate work
result = await agent.run(
    "Review the code in /app.py and generate tests for it",
    deps=deps
)
```

For advanced distributed orchestration, see `examples/distributed_orchestration/`.

**Creating Custom Toolsets**
```python
from pydantic_ai import RunContext
from pydantic_ai.toolsets import FunctionToolset
from pydantic_deep import DeepAgentDeps

# Create a custom toolset
toolset: FunctionToolset[DeepAgentDeps] = FunctionToolset(id="my-toolset")

@toolset.tool
async def my_custom_tool(ctx: RunContext[DeepAgentDeps], param: str) -> str:
    """Tool description for the agent."""
    # Access backend via ctx.deps.backend
    files = ctx.deps.backend.glob("*.py")
    return f"Found {len(files)} Python files"

# Use the custom toolset
agent = create_deep_agent(
    model="openai:gpt-4.1",
    toolsets=[toolset],
)
```

## Examples Organization

The `examples/` directory contains comprehensive examples organized by use case:

**Basic Examples**
- `basic_usage.py`: Simple agent creation and usage
- `interactive_chat.py`: Interactive chat interface
- `simple_deepagent_example.py`: Streamlit app with all features
- `streaming.py`: Streaming responses
- `human_in_the_loop.py`: Interactive approval workflows

**Backend Examples**
- `filesystem_backend.py`: Real filesystem operations
- `composite_backend.py`: Combining multiple backends
- `docker_sandbox.py`: Isolated Docker execution

**Feature Examples**
- `custom_tools.py`: Adding custom tools to agents
- `file_uploads.py`: Handling file uploads
- `skills_usage.py`: Using the skills system
- `subagents.py`: Task delegation to subagents

**Advanced Examples**
- `full_app/`: Complete Streamlit application with GitHub integration
- `distributed_orchestration/`: Multi-agent orchestration system for complex tasks

The distributed orchestration example (`examples/distributed_orchestration/`) demonstrates:
- Coordinating multiple specialized worker agents
- Parallel task execution with load balancing
- Custom worker configurations for different domains (e-commerce, data science, DevOps)
- Task priority and status tracking
- Dynamic worker management
- Real-world scenarios (building a complete REST API)

## Testing Strategy

- **Unit tests**: `tests/` directory with comprehensive coverage
- **Test models**: Use `TestModel` from pydantic-ai for deterministic testing
- **Async testing**: pytest-asyncio with `asyncio_mode = "auto"`
- **Coverage requirement**: 100% coverage is required for all PRs

## Key Configuration Files

- **`pyproject.toml`**: Main configuration (dependencies, tools, coverage)
- **`Makefile`**: Development task automation
- **`mkdocs.yml`**: Documentation configuration
- **`.pre-commit-config.yaml`**: Pre-commit hook configuration

## Important Implementation Notes

- **Backend Protocol**: All backends implement `BackendProtocol` for consistent file operations
- **Async-First**: Most operations are async, use `await` appropriately
- **Type Safety**: Full type annotations with Pyright strict mode
- **Sandbox Support**: DockerSandbox requires `docker` optional dependency

## Documentation Development

- **Local docs**: `make docs-serve` (serves at http://localhost:8000)
- **Docs source**: `docs/` directory (MkDocs with Material theme)
- **API reference**: Auto-generated from docstrings using mkdocstrings

## Dependencies Management

- **Package manager**: uv (fast Python package manager)
- **Lock file**: `uv.lock` (commit this file)
- **Sync command**: `make sync` to update dependencies
- **Optional extras**: sandbox, cli, dev

## Best Practices

### Coverage

Every pull request MUST have 100% coverage. You can check the coverage by running `make test`.

Use `# pragma: no cover` for legitimately untestable code (e.g., platform-specific branches).

### Type Annotations

All code must pass both Pyright and MyPy strict checking:
- `make typecheck` for Pyright
- `make typecheck-mypy` for MyPy

### Writing Documentation

Always reference Python objects with backticks and link to API reference:

```markdown
The [`create_deep_agent`][pydantic_deep.agent.create_deep_agent] function creates a configured agent.
```

### Rename a Class

When renaming a class, add deprecation warning:

```python
from typing_extensions import deprecated

class NewClass: ...

@deprecated("Use `NewClass` instead.")
class OldClass(NewClass): ...
```
