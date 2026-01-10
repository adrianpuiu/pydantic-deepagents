# Execution Strategy Selection Guide

This guide explains how to select the optimal execution strategy for your workflows.

## Overview

The orchestration system supports **two approaches** for strategy selection:

1. **Manual Selection** (Default) - You explicitly specify the strategy
2. **Automatic Selection** - The system analyzes your workflow and recommends the optimal strategy

## Quick Comparison

| Approach | Control | Flexibility | Best For |
|----------|---------|-------------|----------|
| **Manual** | Full control | Fixed strategy | Production, known patterns |
| **Automatic** | System decides | Adapts to workflow | Development, prototyping |

---

## 1. Manual Strategy Selection (Default)

### How It Works

You explicitly specify the execution strategy when creating a workflow:

```python
workflow = WorkflowDefinition(
    id="my-workflow",
    name="My Workflow",
    execution_strategy=ExecutionStrategy.DAG,  # ← Explicit choice
    tasks=[...]
)
```

### Available Strategies

#### `ExecutionStrategy.SEQUENTIAL`
**When to use:**
- Simple workflows with 1-3 tasks
- Tasks must run in exact order
- Safety is more important than speed
- Debugging complex workflows

**Characteristics:**
- Tasks execute one at a time
- Guaranteed order
- Lowest resource usage
- Easiest to debug

**Example:**
```python
workflow = WorkflowDefinition(
    id="deploy",
    name="Deployment Pipeline",
    execution_strategy=ExecutionStrategy.SEQUENTIAL,
    tasks=[
        TaskDefinition(id="backup", description="Backup current version"),
        TaskDefinition(id="deploy", description="Deploy new version"),
        TaskDefinition(id="verify", description="Verify deployment"),
    ],
)
```

---

#### `ExecutionStrategy.PARALLEL`
**When to use:**
- All tasks are independent (no dependencies)
- Want maximum parallelism
- Processing multiple similar items
- Resource-intensive tasks that benefit from concurrency

**Characteristics:**
- All tasks start simultaneously
- Respects `max_parallel_tasks` limit
- Fastest for independent tasks
- Higher resource usage

**Example:**
```python
workflow = WorkflowDefinition(
    id="data-processing",
    name="Parallel Data Processing",
    execution_strategy=ExecutionStrategy.PARALLEL,
    max_parallel_tasks=10,
    tasks=[
        TaskDefinition(id=f"process-{i}", description=f"Process file {i}")
        for i in range(100)
    ],
)
```

---

#### `ExecutionStrategy.DAG` (Default)
**When to use:**
- Tasks have dependencies
- Want optimal parallelism with dependencies
- Complex workflows
- **Most common choice** - good default

**Characteristics:**
- Respects task dependencies
- Parallel execution where possible
- Automatic topological sorting
- Detects circular dependencies

**Example:**
```python
workflow = WorkflowDefinition(
    id="build",
    name="Build Pipeline",
    execution_strategy=ExecutionStrategy.DAG,
    tasks=[
        TaskDefinition(id="setup", description="Setup environment"),
        TaskDefinition(
            id="compile",
            description="Compile code",
            depends_on=["setup"],
        ),
        TaskDefinition(
            id="test",
            description="Run tests",
            depends_on=["setup"],
        ),
        TaskDefinition(
            id="package",
            description="Package application",
            depends_on=["compile", "test"],
        ),
    ],
)
```

---

#### `ExecutionStrategy.CONDITIONAL`
**When to use:**
- Tasks have runtime conditions
- Need branching logic
- Skip tasks based on previous results
- Adaptive workflows

**Characteristics:**
- Evaluates conditions at runtime
- Skips tasks with unmet conditions
- More flexible but slower
- Best for decision-based workflows

**Example:**
```python
workflow = WorkflowDefinition(
    id="quality-check",
    name="Code Quality Workflow",
    execution_strategy=ExecutionStrategy.CONDITIONAL,
    tasks=[
        TaskDefinition(
            id="analyze",
            description="Analyze code quality",
        ),
        TaskDefinition(
            id="fix",
            description="Fix issues if found",
            condition="analyze",  # Only run if analyze completes
            depends_on=["analyze"],
        ),
        TaskDefinition(
            id="verify",
            description="Verify fixes",
            depends_on=["fix"],
        ),
    ],
)
```

---

## 2. Automatic Strategy Selection

### How It Works

The system analyzes your workflow and recommends the optimal strategy:

```python
# Option 1: Get recommendation
recommended = recommend_strategy(workflow)
print(f"Recommended: {recommended}")

# Option 2: Execute with automatic selection
result = await orchestrator.execute_workflow(
    workflow,
    auto_strategy=True  # ← System chooses optimal strategy
)

# Option 3: Get detailed explanation
explanation = explain_strategy_choice(workflow)
print(explanation)
```

### Decision Logic

The system follows this logic:

```
1. Has conditional tasks?
   └─ YES → CONDITIONAL
   └─ NO → Continue

2. Has dependencies?
   └─ NO → Multiple tasks?
       └─ YES → PARALLEL
       └─ NO → SEQUENTIAL
   └─ YES → DAG

3. Default → SEQUENTIAL (safest)
```

### Example

```python
from pydantic_deep.orchestration import (
    recommend_strategy,
    explain_strategy_choice,
)

# Define workflow (no explicit strategy)
workflow = WorkflowDefinition(
    id="auto-workflow",
    name="Auto-Selected Workflow",
    tasks=[
        TaskDefinition(id="task1", description="Process data"),
        TaskDefinition(id="task2", description="Generate report"),
        TaskDefinition(id="task3", description="Send notification"),
    ],
)

# Get recommendation
recommended = recommend_strategy(workflow)
print(f"Recommended: {recommended.value}")
# Output: "parallel" (no dependencies, can run concurrently)

# Get explanation
print(explain_strategy_choice(workflow))
# Output:
# Workflow 'Auto-Selected Workflow' analysis:
#   - Tasks: 3
#   - Independent tasks: 3
#   - Has dependencies: False
#   - Has conditions: False
#
# Recommended strategy: parallel
#   Reason: All tasks are independent and can run concurrently

# Execute with automatic selection
result = await orchestrator.execute_workflow(workflow, auto_strategy=True)
```

---

## Decision Matrix

Use this table to choose the right strategy:

| Scenario | Dependencies | Conditions | Recommended Strategy |
|----------|--------------|------------|---------------------|
| Single task | N/A | No | SEQUENTIAL |
| Multiple independent tasks | No | No | PARALLEL |
| Tasks with dependencies | Yes | No | DAG |
| Conditional logic | Maybe | Yes | CONDITIONAL |
| Simple ordered workflow | Maybe | No | SEQUENTIAL |
| Complex workflow | Yes | No | DAG |

---

## Performance Considerations

### SEQUENTIAL
- **Speed**: Slowest (one task at a time)
- **Resources**: Lowest usage
- **Best for**: 1-3 tasks, strict ordering

### PARALLEL
- **Speed**: Fastest for independent tasks
- **Resources**: Highest usage
- **Best for**: Many independent tasks
- **Limit**: Use `max_parallel_tasks` to control

### DAG
- **Speed**: Fast (parallel where possible)
- **Resources**: Medium usage
- **Best for**: Most workflows (good default)
- **Limit**: Respects dependencies

### CONDITIONAL
- **Speed**: Variable (depends on conditions)
- **Resources**: Medium usage
- **Best for**: Branching workflows
- **Note**: Slower due to condition evaluation

---

## Best Practices

### 1. Start with Automatic, Optimize Manually

```python
# Development: Use automatic
result = await orchestrator.execute_workflow(workflow, auto_strategy=True)

# Profile and analyze
print(explain_strategy_choice(workflow))

# Production: Use explicit strategy based on profiling
workflow.execution_strategy = ExecutionStrategy.DAG
result = await orchestrator.execute_workflow(workflow)
```

### 2. Use Explanations for Learning

```python
# Understand why a strategy is recommended
explanation = explain_strategy_choice(workflow)
print(explanation)

# Helps you learn to choose strategies manually
```

### 3. Override When Needed

```python
# System recommends PARALLEL, but you want SEQUENTIAL for debugging
workflow = WorkflowDefinition(
    id="debug-workflow",
    name="Debug Workflow",
    execution_strategy=ExecutionStrategy.SEQUENTIAL,  # Override
    tasks=[...],
)
```

### 4. Set Concurrency Limits

```python
# Important for PARALLEL and DAG
workflow = WorkflowDefinition(
    execution_strategy=ExecutionStrategy.PARALLEL,
    max_parallel_tasks=5,  # Don't overwhelm system
    tasks=[...],
)
```

---

## Common Patterns

### Pattern 1: Data Processing Pipeline
```python
# Independent data chunks → PARALLEL
workflow = WorkflowDefinition(
    execution_strategy=ExecutionStrategy.PARALLEL,
    tasks=[
        TaskDefinition(id=f"chunk-{i}", description=f"Process chunk {i}")
        for i in range(100)
    ],
)
```

### Pattern 2: Build Pipeline
```python
# Dependencies → DAG
workflow = WorkflowDefinition(
    execution_strategy=ExecutionStrategy.DAG,
    tasks=[
        TaskDefinition(id="compile", ...),
        TaskDefinition(id="test", depends_on=["compile"]),
        TaskDefinition(id="package", depends_on=["test"]),
    ],
)
```

### Pattern 3: Quality Check
```python
# Conditional logic → CONDITIONAL
workflow = WorkflowDefinition(
    execution_strategy=ExecutionStrategy.CONDITIONAL,
    tasks=[
        TaskDefinition(id="check", ...),
        TaskDefinition(id="fix", condition="check", ...),
    ],
)
```

---

## Summary

| Feature | Manual Selection | Automatic Selection |
|---------|------------------|---------------------|
| **Control** | Full control | System decides |
| **Ease of use** | Requires knowledge | Just works |
| **Best for** | Production | Development |
| **Performance** | Optimal (if chosen correctly) | Good (usually optimal) |
| **Flexibility** | Fixed | Adapts to changes |

**Recommendation**: Start with `auto_strategy=True` during development, then optimize with explicit strategies in production based on profiling and requirements.
