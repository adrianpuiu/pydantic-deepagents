# Composite Backend Example

Combine multiple backends with path-based routing.

## Source Code

:material-file-code: `examples/composite_backend.py`

## Overview

This example demonstrates:

- Combining multiple backends (memory + filesystem)
- Routing operations by path prefix
- Using persistent and ephemeral storage together
- Practical use cases for mixed storage

## When to Use CompositeBackend

CompositeBackend is useful when:

- Some files should persist (project files) while others are temporary (scratch)
- Different paths need different storage characteristics
- You want to isolate certain operations (e.g., uploads vs workspace)
- Testing requires mixing real files with in-memory state

## Full Example

```python
"""Example using CompositeBackend for mixed storage."""

import asyncio
import tempfile
from pathlib import Path

from pydantic_deep import (
    CompositeBackend,
    DeepAgentDeps,
    FilesystemBackend,
    StateBackend,
    create_deep_agent,
)


async def main():
    # Create a temporary directory for persistent storage
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        print(f"Persistent storage: {workspace}")

        # Create backends:
        # - StateBackend for temporary/scratch files
        # - FilesystemBackend for persistent project files
        memory_backend = StateBackend()
        fs_backend = FilesystemBackend(workspace, virtual_mode=True)

        # Create composite backend with routing rules
        backend = CompositeBackend(
            default=memory_backend,  # Default to memory for unmatched paths
            routes={
                "/project/": fs_backend,    # Project files go to disk
                "/workspace/": fs_backend,  # Workspace files go to disk
            },
        )

        # Create the agent
        agent = create_deep_agent(
            model="openai:gpt-4.1",
            instructions="""
            You are a project assistant.

            File organization:
            - /project/ - Persistent project files (saved to disk)
            - /workspace/ - Working files (saved to disk)
            - /temp/ or /scratch/ - Temporary files (in memory only)

            Use the appropriate location based on whether files should persist.
            """,
        )

        deps = DeepAgentDeps(backend=backend)

        # Run the agent
        result = await agent.run(
            """Create a small Python project:
            1. Create /project/src/app.py with a simple Flask app
            2. Create /project/requirements.txt with dependencies
            3. Create /scratch/notes.txt with implementation notes (temporary)
            4. Create /project/README.md with project description
            """,
            deps=deps,
        )

        print("Agent output:")
        print(result.output)

        # Show what's in memory (temporary files)
        print("\nTemporary files (in memory):")
        for path in sorted(memory_backend.files.keys()):
            print(f"  {path}")

        # Show what's on disk (persistent files)
        print("\nPersistent files (on disk):")
        for path in workspace.rglob("*"):
            if path.is_file():
                rel_path = path.relative_to(workspace)
                print(f"  {rel_path}")

        # Read a persistent file
        readme = workspace / "project" / "README.md"
        if readme.exists():
            print("\nContent of README.md:")
            print(readme.read_text())


if __name__ == "__main__":
    asyncio.run(main())
```

## Running the Example

```bash
export OPENAI_API_KEY=your-api-key
uv run python examples/composite_backend.py
```

## Expected Output

```
Persistent storage: /tmp/tmpxyz123

Agent output:
I've created the Python project with the following structure:

- /project/src/app.py - Flask application
- /project/requirements.txt - Dependencies (Flask)
- /project/README.md - Project documentation
- /scratch/notes.txt - Implementation notes (temporary)

Temporary files (in memory):
  /scratch/notes.txt

Persistent files (on disk):
  project/README.md
  project/requirements.txt
  project/src/app.py

Content of README.md:
# Flask App

A simple Flask application.

## Installation
pip install -r requirements.txt

## Usage
python src/app.py
```

## Key Concepts

### Route Configuration

```python
backend = CompositeBackend(
    default=memory_backend,     # Fallback for unmatched paths
    routes={
        "/project/": fs_backend,    # Paths starting with /project/
        "/workspace/": fs_backend,  # Paths starting with /workspace/
        "/uploads/": uploads_backend,
    },
)
```

Routes are matched by prefix. The first matching route wins.

### How Routing Works

```python
# These go to fs_backend (match /project/ prefix)
backend.write("/project/src/main.py", "...")
backend.read("/project/config.json")

# These go to memory_backend (default, no route matches)
backend.write("/scratch/temp.txt", "...")
backend.read("/notes.md")
```

### Virtual Mode for FilesystemBackend

```python
# virtual_mode=True: paths are relative to root
fs_backend = FilesystemBackend(workspace, virtual_mode=True)

# Write to /project/app.py -> workspace/project/app.py on disk
backend.write("/project/app.py", "...")
```

## Variations

### Three-Way Split

```python
backend = CompositeBackend(
    default=StateBackend(),  # Scratch space
    routes={
        "/project/": FilesystemBackend(project_dir, virtual_mode=True),
        "/cache/": FilesystemBackend(cache_dir, virtual_mode=True),
        "/uploads/": StateBackend(),  # In-memory uploads
    },
)
```

### Docker + Local Hybrid

```python
from pydantic_deep import DockerSandbox

backend = CompositeBackend(
    default=DockerSandbox(image="python:3.12-slim"),  # Isolated execution
    routes={
        "/local/": FilesystemBackend(local_dir, virtual_mode=True),  # Local access
    },
)
```

### Read-Only Source + Writable Workspace

```python
# Source files are read-only (from real filesystem)
source_backend = FilesystemBackend(source_dir, virtual_mode=True)

# Workspace for agent modifications
workspace_backend = StateBackend()

backend = CompositeBackend(
    default=workspace_backend,
    routes={
        "/src/": source_backend,  # Read-only source
    },
)
```

## Common Patterns

### 1. Development Environment

```python
backend = CompositeBackend(
    default=StateBackend(),
    routes={
        "/project/": FilesystemBackend(project_root, virtual_mode=True),
        "/tests/": FilesystemBackend(project_root / "tests", virtual_mode=True),
    },
)
```

### 2. Upload Processing

```python
backend = CompositeBackend(
    default=StateBackend(),  # Working memory
    routes={
        "/uploads/": StateBackend(),  # Uploaded files
        "/output/": FilesystemBackend(output_dir, virtual_mode=True),  # Results
    },
)
```

### 3. Multi-Project Setup

```python
backend = CompositeBackend(
    default=StateBackend(),
    routes={
        "/frontend/": FilesystemBackend(frontend_dir, virtual_mode=True),
        "/backend/": FilesystemBackend(backend_dir, virtual_mode=True),
        "/shared/": FilesystemBackend(shared_dir, virtual_mode=True),
    },
)
```

## Best Practices

1. **Clear path conventions** - Document which paths go where
2. **Use virtual_mode** - Keeps paths consistent across backends
3. **Default to memory** - Safe fallback for unexpected paths
4. **Consider persistence needs** - What should survive restarts?

## Next Steps

- [Filesystem Example](filesystem.md) - Single backend usage
- [Docker Sandbox](docker-sandbox.md) - Isolated execution
- [Concepts: Backends](../concepts/backends.md) - Deep dive
