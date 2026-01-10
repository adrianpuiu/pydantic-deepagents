# Dynamic Orchestration System

A comprehensive orchestration framework for coordinating multi-agent workflows in the pydantic-deepagents library.

## Overview

The orchestration system provides powerful capabilities for defining, executing, and monitoring complex workflows that involve multiple agents working together. It handles task dependencies, dynamic routing, parallel execution, error handling, and progress tracking.

## Key Features

### 1. **Task Definition & Dependencies**
- Define tasks with explicit dependencies
- Support for complex dependency graphs (DAGs)
- Automatic topological sorting
- Circular dependency detection

### 2. **Dynamic Agent Routing**
- Route tasks to appropriate agents based on capabilities
- Load balancing across agents
- Priority-based agent selection
- Support for explicit agent assignment

### 3. **Multiple Execution Strategies**
- **Sequential**: Execute tasks one by one in order
- **Parallel**: Execute independent tasks concurrently
- **DAG**: Execute based on dependency graph with parallel execution
- **Conditional**: Execute tasks based on runtime conditions

### 4. **Error Handling & Resilience**
- Automatic retry with exponential backoff
- Configurable retry policies
- Continue-on-failure mode
- Comprehensive error tracking

### 5. **State Management**
- Real-time workflow state tracking
- Progress monitoring
- Task result aggregation
- Workflow history

### 6. **Agent Capabilities**
Predefined agent capabilities for intelligent routing:
- General purpose
- Code analysis
- Code generation
- Testing
- Debugging
- Documentation
- Data processing
- File operations
- API integration
- Research

### 7. **Skill Integration** ✨
- Automatic skill discovery and loading
- Tasks can specify required skills
- Skills auto-loaded when tasks execute
- Skills provide domain-specific expertise
- Seamless integration with existing skill system

## Architecture

### Core Components

#### 1. **TaskDefinition**
Defines a single task in a workflow:
```python
TaskDefinition(
    id="analyze-code",
    description="Analyze the codebase for potential issues",
    required_capabilities=[AgentCapability.CODE_ANALYSIS],
    required_skills=["python-code-review"],  # Auto-loaded skills
    depends_on=["setup"],  # Task dependencies
    priority=8,  # 1-10, higher is more important
    retry_config=RetryConfig(max_retries=3),
    parameters={"focus": "security"}  # Custom parameters
)
```

#### 2. **WorkflowDefinition**
Defines a complete workflow:
```python
WorkflowDefinition(
    id="ci-pipeline",
    name="Continuous Integration Pipeline",
    tasks=[task1, task2, task3],
    execution_strategy=ExecutionStrategy.DAG,
    max_parallel_tasks=5,
    continue_on_failure=False
)
```

#### 3. **TaskOrchestrator**
Main coordinator that executes workflows:
```python
orchestrator = TaskOrchestrator(agent, deps, config)
state = await orchestrator.execute_workflow(workflow)
```

#### 4. **StateManager**
Manages workflow execution state:
- Tracks task status (pending, running, completed, failed, skipped)
- Manages dependencies
- Provides progress information

#### 5. **TaskRouter**
Routes tasks to appropriate agents:
- Capability-based routing
- Load balancing
- Priority handling

#### 6. **Execution Strategies**
Different strategies for task execution:
- `SequentialExecutor`: One task at a time
- `ParallelExecutor`: All tasks concurrently (with limit)
- `DAGExecutor`: Dependency-aware parallel execution
- `ConditionalExecutor`: Condition-based execution

## Usage Examples

### Basic Workflow

```python
from pydantic_deep import (
    create_deep_agent,
    create_default_deps,
    TaskOrchestrator,
    WorkflowDefinition,
    TaskDefinition,
    ExecutionStrategy,
)

# Create agent
agent = create_deep_agent(model="openai:gpt-4")
deps = create_default_deps()

# Create orchestrator
orchestrator = TaskOrchestrator(agent, deps)

# Define workflow
workflow = WorkflowDefinition(
    id="simple-workflow",
    name="Simple Task Workflow",
    execution_strategy=ExecutionStrategy.SEQUENTIAL,
    tasks=[
        TaskDefinition(
            id="task1",
            description="Analyze requirements",
        ),
        TaskDefinition(
            id="task2",
            description="Generate implementation plan",
            depends_on=["task1"],
        ),
        TaskDefinition(
            id="task3",
            description="Create documentation",
            depends_on=["task2"],
        ),
    ],
)

# Execute workflow
result = await orchestrator.execute_workflow(workflow)
print(f"Workflow status: {result.status}")
print(f"Completed tasks: {len(result.completed_tasks)}")
```

### Parallel Execution

```python
workflow = WorkflowDefinition(
    id="parallel-analysis",
    name="Parallel Data Analysis",
    execution_strategy=ExecutionStrategy.PARALLEL,
    max_parallel_tasks=5,
    tasks=[
        TaskDefinition(
            id=f"analyze-{i}",
            description=f"Analyze dataset {i}",
            required_capabilities=[AgentCapability.DATA_PROCESSING],
        )
        for i in range(10)
    ],
)

result = await orchestrator.execute_workflow(workflow)
```

### Complex DAG Workflow

```python
workflow = WorkflowDefinition(
    id="web-app-dev",
    name="Web Application Development",
    execution_strategy=ExecutionStrategy.DAG,
    max_parallel_tasks=3,
    tasks=[
        # Phase 1: Requirements
        TaskDefinition(
            id="requirements",
            description="Define application requirements",
            priority=10,
        ),

        # Phase 2: Parallel development
        TaskDefinition(
            id="backend",
            description="Develop backend API",
            depends_on=["requirements"],
            required_capabilities=[AgentCapability.CODE_GENERATION],
            priority=8,
        ),
        TaskDefinition(
            id="frontend",
            description="Develop frontend UI",
            depends_on=["requirements"],
            required_capabilities=[AgentCapability.CODE_GENERATION],
            priority=8,
        ),

        # Phase 3: Integration
        TaskDefinition(
            id="integration",
            description="Integrate frontend and backend",
            depends_on=["backend", "frontend"],
            priority=7,
        ),

        # Phase 4: Testing
        TaskDefinition(
            id="testing",
            description="Run comprehensive tests",
            depends_on=["integration"],
            required_capabilities=[AgentCapability.TESTING],
            priority=6,
        ),

        # Phase 5: Documentation
        TaskDefinition(
            id="docs",
            description="Generate documentation",
            depends_on=["testing"],
            required_capabilities=[AgentCapability.DOCUMENTATION],
            priority=5,
        ),
    ],
)
```

### With Progress Tracking

```python
def progress_callback(state: WorkflowState):
    progress = orchestrator.get_workflow_progress(workflow.id)
    print(f"Progress: {progress['completed']}/{progress['total_tasks']} tasks")
    print(f"Status: {progress['status']}")

result = await orchestrator.execute_workflow(workflow, progress_callback)
```

### Custom Agent Routing

```python
from pydantic_deep.orchestration import (
    OrchestrationConfig,
    AgentRouting,
    create_default_routing,
)

config = OrchestrationConfig(
    agent_routing=[
        AgentRouting(
            agent_type="senior-developer",
            capabilities=[
                AgentCapability.CODE_GENERATION,
                AgentCapability.CODE_ANALYSIS,
                AgentCapability.DEBUGGING,
            ],
            priority=10,
            max_concurrent_tasks=2,
        ),
        AgentRouting(
            agent_type="junior-developer",
            capabilities=[AgentCapability.CODE_GENERATION],
            priority=5,
            max_concurrent_tasks=5,
        ),
        *create_default_routing(),  # Include default agents
    ],
    enable_parallel_execution=True,
)

orchestrator = TaskOrchestrator(agent, deps, config)
```

### Retry Configuration

```python
TaskDefinition(
    id="flaky-task",
    description="Task that might fail temporarily",
    retry_config=RetryConfig(
        max_retries=5,
        backoff_multiplier=2.0,
        initial_delay=1.0,
        max_delay=30.0,
    ),
)
```

### Conditional Execution

```python
WorkflowDefinition(
    id="conditional-workflow",
    name="Workflow with Conditional Tasks",
    execution_strategy=ExecutionStrategy.CONDITIONAL,
    tasks=[
        TaskDefinition(
            id="analyze",
            description="Analyze code quality",
        ),
        TaskDefinition(
            id="fix-issues",
            description="Fix issues found in analysis",
            condition="analyze",  # Only run if analyze completes
            depends_on=["analyze"],
        ),
        TaskDefinition(
            id="verify",
            description="Verify fixes",
            depends_on=["fix-issues"],
        ),
    ],
)
```

## API Reference

### TaskDefinition

**Parameters:**
- `id` (str): Unique task identifier
- `description` (str): Human-readable task description
- `task_type` (str | None): Optional type classification
- `depends_on` (list[str]): List of task IDs this task depends on
- `required_capabilities` (list[AgentCapability]): Required agent capabilities
- `priority` (int): Task priority (1-10, higher is more important)
- `timeout_seconds` (float | None): Maximum execution time
- `retry_config` (RetryConfig): Retry configuration
- `parameters` (dict): Task-specific parameters
- `expected_output_type` (str | None): Expected output format
- `agent_type` (str | None): Specific agent type (overrides routing)
- `condition` (str | None): Condition expression for execution

### WorkflowDefinition

**Parameters:**
- `id` (str): Unique workflow identifier
- `name` (str): Human-readable workflow name
- `description` (str): Workflow description
- `tasks` (list[TaskDefinition]): List of tasks
- `execution_strategy` (ExecutionStrategy): Execution strategy
- `default_timeout_seconds` (float | None): Default timeout for tasks
- `max_parallel_tasks` (int): Maximum concurrent tasks
- `continue_on_failure` (bool): Continue if a task fails
- `metadata` (dict): Additional metadata

### TaskOrchestrator

**Methods:**

- `execute_workflow(workflow, progress_callback=None) -> WorkflowState`
  - Execute a complete workflow
  - Returns final workflow state

- `execute_task(task, workflow_id="adhoc") -> TaskResult`
  - Execute a single task outside a workflow
  - Returns task result

- `get_workflow_state(workflow_id) -> WorkflowState | None`
  - Get current state of a workflow
  - Returns state or None if not found

- `get_workflow_progress(workflow_id) -> dict | None`
  - Get progress information for a workflow
  - Returns progress dict or None

- `cancel_workflow(workflow_id) -> bool`
  - Cancel a running workflow
  - Returns True if cancelled

## Best Practices

### 1. Task Granularity
- Keep tasks focused on a single responsibility
- Break complex operations into smaller tasks
- Use dependencies to coordinate multi-step processes

### 2. Error Handling
- Set appropriate retry policies for transient failures
- Use `continue_on_failure` for non-critical workflows
- Monitor task results for failures

### 3. Resource Management
- Set `max_parallel_tasks` based on available resources
- Use capability-based routing to balance load
- Configure agent concurrency limits

### 4. Monitoring
- Use progress callbacks for real-time tracking
- Check workflow state after execution
- Log task results for debugging

### 5. Testing
- Test workflows with simple tasks first
- Validate dependency graphs before execution
- Use conditional execution for complex scenarios

## Performance Considerations

### Parallel Execution
- DAG strategy provides best parallelism with dependencies
- Limit `max_parallel_tasks` to avoid resource exhaustion
- Consider agent capacity when routing tasks

### Retries
- Configure appropriate backoff to avoid thundering herd
- Set reasonable max_delay to prevent long waits
- Monitor retry counts for persistent failures

### State Management
- Workflow state is kept in memory during execution
- Large workflows may consume significant memory
- Consider breaking very large workflows into smaller ones

## Error Handling

### Task Failures
- Tasks can fail and be retried automatically
- Failed tasks are tracked in `workflow.failed_tasks`
- Use `continue_on_failure=True` to proceed despite failures

### Circular Dependencies
- Detected automatically during execution
- Workflow fails with descriptive error message
- Check dependency graph before execution

### Timeouts
- Configure per-task or workflow-level timeouts
- Timeout results in task/workflow failure
- Use appropriate values for long-running tasks

## Skill Integration

### Overview

The orchestration system fully integrates with the pydantic-deep skill system, allowing tasks to automatically load and use domain-specific skills when needed.

### How It Works

1. **Skill Discovery**: The orchestrator automatically discovers skills from configured directories
2. **Task Requirements**: Tasks specify which skills they need via `required_skills` parameter
3. **Automatic Loading**: Skills are auto-loaded when tasks execute
4. **Seamless Integration**: Skills are injected into agent dependencies transparently

### Using Skills in Tasks

```python
from pydantic_deep import TaskDefinition, AgentCapability

# Define task with required skills
task = TaskDefinition(
    id="code-review",
    description="Review Python code for quality and best practices",
    required_capabilities=[AgentCapability.CODE_ANALYSIS],
    required_skills=["python-code-review"],  # ← Auto-loads this skill
)
```

### Creating an Orchestrator with Skills

```python
from pydantic_deep import TaskOrchestrator, create_deep_agent, create_default_deps
from pydantic_deep.types import SkillDirectory

# Create orchestrator with skill directories
orchestrator = TaskOrchestrator(
    agent=create_deep_agent(model="openai:gpt-4"),
    deps=create_default_deps(),
    skill_directories=[
        {"path": "~/.pydantic-deep/skills", "recursive": True},
        {"path": "./project-skills", "recursive": False},
    ]
)
```

### Complete Example

```python
from pydantic_deep import (
    TaskOrchestrator,
    WorkflowDefinition,
    TaskDefinition,
    AgentCapability,
    ExecutionStrategy,
)

# Create workflow with skill-based tasks
workflow = WorkflowDefinition(
    id="quality-pipeline",
    name="Code Quality Pipeline",
    execution_strategy=ExecutionStrategy.DAG,
    tasks=[
        TaskDefinition(
            id="api-design",
            description="Design RESTful API",
            required_skills=["api-design"],
        ),
        TaskDefinition(
            id="implementation",
            description="Implement the API",
            depends_on=["api-design"],
            required_capabilities=[AgentCapability.CODE_GENERATION],
        ),
        TaskDefinition(
            id="code-review",
            description="Review implementation quality",
            depends_on=["implementation"],
            required_skills=["python-code-review"],
        ),
        TaskDefinition(
            id="test-strategy",
            description="Design test strategy",
            depends_on=["implementation"],
            required_skills=["test-strategy"],
        ),
    ],
)

# Execute - skills auto-loaded as needed
result = await orchestrator.execute_workflow(workflow)
```

### Skill Discovery

Skills are discovered automatically from configured directories:

```python
# Skills are discovered when workflow starts
orchestrator.skill_manager.discover_skills()

# Get all available skills
skills = orchestrator.skill_manager.get_all_skills()
for skill in skills:
    print(f"{skill['name']}: {skill['description']}")

# Get specific skill
skill = orchestrator.skill_manager.get_skill("python-code-review")
```

### Skill Requirements

Tasks can require multiple skills:

```python
TaskDefinition(
    id="comprehensive-review",
    description="Full code quality review",
    required_skills=[
        "python-code-review",
        "security-audit",
        "performance-analysis"
    ]
)
```

### Error Handling

If a required skill is not found, the orchestrator raises a clear error:

```python
# ValueError: Required skill 'nonexistent-skill' not found.
# Available skills: ['python-code-review', 'api-design', 'test-strategy']
```

### Best Practices

1. **Organize Skills**: Keep skills in dedicated directories
2. **Name Clearly**: Use descriptive skill names (e.g., "python-code-review", not "review")
3. **Specify Requirements**: Only require skills that are actually needed
4. **Version Skills**: Use skill versioning for stability
5. **Document Skills**: Ensure each skill has clear description and tags

### Benefits

- **Domain Expertise**: Skills provide specialized knowledge
- **Consistency**: Same skill used across multiple tasks
- **Modularity**: Skills can be reused across workflows
- **Auto-Loading**: No manual skill management
- **Flexibility**: Easy to add/update skills

## Integration with pydantic-deep

The orchestration system integrates seamlessly with existing pydantic-deep features:

- **TodoToolset**: Tasks can be synced with todo list
- **SubAgentToolset**: Automatic subagent creation and routing
- **FilesystemToolset**: File operations within tasks
- **SkillsToolset**: Skills available to all tasks
- **Backends**: All backend types supported (State, Filesystem, Docker)

## Examples

See example files for comprehensive demonstrations:

**`examples/orchestration_example.py`**:
- Basic workflow execution
- Parallel data processing
- Conditional task execution
- Complex DAG workflows
- Progress tracking
- Error handling

**`examples/orchestration_with_skills_example.py`**:
- Skill integration with workflows
- Auto-loading skills for tasks
- Multiple tasks using different skills
- Skill discovery and management

**`examples/strategy_selection_example.py`**:
- Manual strategy selection
- Automatic strategy selection
- Strategy recommendations
- Performance comparisons

## Future Enhancements

Potential future additions:
- Workflow templates and reusable patterns
- Visual workflow designer
- Performance metrics and analytics
- Distributed execution across multiple nodes
- Workflow persistence and resumption
- Event-driven workflow triggers
- Resource constraints and quotas
- Advanced condition expressions
