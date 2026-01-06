# Distributed Agent Orchestration System

A comprehensive example demonstrating how to build a distributed agent orchestration system using pydantic-deepagents. This system enables multiple specialized agents to work together on complex tasks through intelligent coordination, load balancing, and result aggregation.

## Overview

The distributed orchestration system consists of:

- **Orchestrator**: The main coordinator that distributes tasks, monitors progress, and aggregates results
- **Worker Agents**: Specialized agents for different types of tasks (data analysis, code generation, testing, documentation, etc.)
- **Task Queue**: Manages task distribution and prioritization
- **Result Aggregator**: Collects and combines results from multiple workers
- **Status Monitor**: Tracks agent status, performance metrics, and health

## Architecture

```
┌─────────────────────────────────────────┐
│         Orchestrator Agent              │
│  (Coordinates & Aggregates Results)     │
└────────────┬────────────────────────────┘
             │
             │ Distributes Tasks
             │
     ┌───────┴───────┬───────────┬──────────┐
     ▼               ▼           ▼          ▼
┌─────────┐    ┌─────────┐  ┌────────┐  ┌────────┐
│ Data    │    │  Code   │  │ Test   │  │  Doc   │
│ Analyst │    │ Writer  │  │ Writer │  │ Writer │
│ Agent   │    │ Agent   │  │ Agent  │  │ Agent  │
└─────────┘    └─────────┘  └────────┘  └────────┘
```

## Features

### 1. Task Distribution
- Intelligent routing based on agent capabilities
- Load balancing across available workers
- Priority queue for urgent tasks
- Parallel execution support

### 2. Worker Specialization
- **Data Analyst**: Handles data processing, analysis, and visualization tasks
- **Code Writer**: Generates code based on specifications
- **Test Writer**: Creates comprehensive unit tests
- **Documentation Writer**: Produces clear technical documentation
- **Code Reviewer**: Reviews code for quality and security
- **General Purpose**: Handles miscellaneous tasks

### 3. Result Aggregation
- Collects outputs from multiple workers
- Combines results intelligently
- Handles partial failures gracefully
- Provides unified response to user

### 4. Monitoring & Status
- Real-time agent status tracking
- Performance metrics collection
- Task completion monitoring
- Error handling and reporting

## Quick Start

### Basic Usage

```python
import asyncio
from distributed_orchestration import DistributedOrchestrator

async def main():
    # Create orchestrator with default worker agents
    orchestrator = DistributedOrchestrator()

    # Submit a complex task
    result = await orchestrator.execute(
        "Analyze sales data, generate report code, write tests, and document the API"
    )

    print(result)

asyncio.run(main())
```

### Running Examples

```bash
# Run the basic orchestration demo
python examples/distributed_orchestration/basic_demo.py

# Run parallel processing demo
python examples/distributed_orchestration/parallel_demo.py

# Run the full orchestration example
python examples/distributed_orchestration/full_demo.py

# Run with custom workers
python examples/distributed_orchestration/custom_workers_demo.py
```

## Examples

### Example 1: Parallel Data Processing

Process multiple datasets in parallel and aggregate results:

```python
from distributed_orchestration import DistributedOrchestrator

orchestrator = DistributedOrchestrator()

# Process multiple datasets concurrently
tasks = [
    "Analyze Q1 sales data and identify trends",
    "Analyze Q2 sales data and identify trends",
    "Analyze Q3 sales data and identify trends",
    "Analyze Q4 sales data and identify trends",
]

results = await orchestrator.execute_parallel(tasks)
annual_summary = await orchestrator.aggregate_results(results)
```

### Example 2: Full Software Development Pipeline

Coordinate multiple agents to build a complete feature:

```python
# Define a complex task
task = """
Build a REST API for user management with:
1. User CRUD operations
2. Authentication
3. Unit tests
4. API documentation
"""

# Orchestrator will:
# 1. Route code generation to Code Writer agent
# 2. Route testing to Test Writer agent
# 3. Route documentation to Doc Writer agent
# 4. Route final review to Code Reviewer agent
# 5. Aggregate all outputs into cohesive result

result = await orchestrator.execute(task)
```

### Example 3: Custom Worker Configuration

Define and use custom specialized workers:

```python
from pydantic_deep.types import SubAgentConfig

# Define custom workers
custom_workers = [
    SubAgentConfig(
        name="api-designer",
        description="Designs RESTful API architectures",
        instructions="""You are an API design expert.
        Focus on RESTful principles, proper HTTP methods,
        status codes, and API versioning.""",
    ),
    SubAgentConfig(
        name="security-auditor",
        description="Audits code for security vulnerabilities",
        instructions="""You are a security expert.
        Check for OWASP top 10 vulnerabilities,
        authentication issues, and data validation.""",
    ),
]

orchestrator = DistributedOrchestrator(custom_workers=custom_workers)
```

## Project Structure

```
distributed_orchestration/
├── README.md                 # This file
├── orchestrator.py          # Main orchestrator implementation
├── task_queue.py            # Task queue and distribution logic
├── result_aggregator.py     # Result aggregation logic
├── monitor.py               # Status monitoring and metrics
├── configs/
│   ├── worker_configs.py    # Default worker configurations
│   └── custom_configs.py    # Example custom configurations
├── basic_demo.py            # Simple orchestration example
├── parallel_demo.py         # Parallel processing example
├── full_demo.py             # Complete orchestration demo
└── custom_workers_demo.py   # Custom worker configuration demo
```

## Key Concepts

### Task Routing

The orchestrator analyzes each task and routes it to the most appropriate worker based on:
- Task type and requirements
- Worker capabilities and specialization
- Current worker load
- Task priority

### Load Balancing

Tasks are distributed across workers to:
- Maximize throughput
- Minimize response time
- Prevent worker overload
- Enable parallel execution

### Result Aggregation

Multiple worker outputs are combined through:
- Intelligent merging of results
- Conflict resolution
- Quality validation
- Unified formatting

### Error Handling

The system handles failures gracefully:
- Retry failed tasks
- Fallback to alternative workers
- Partial result recovery
- Detailed error reporting

## Advanced Features

### Dynamic Worker Scaling

Add or remove workers at runtime:

```python
# Add a new specialized worker
orchestrator.add_worker(worker_config)

# Remove a worker
orchestrator.remove_worker("worker-name")
```

### Task Prioritization

Set task priorities for urgent work:

```python
result = await orchestrator.execute(
    task="Fix critical security bug",
    priority="high"
)
```

### Custom Aggregation Strategies

Define how results should be combined:

```python
orchestrator.set_aggregation_strategy(
    lambda results: custom_merge_logic(results)
)
```

## Performance Considerations

- **Parallel Execution**: Workers run concurrently for maximum throughput
- **Token Management**: Each worker maintains independent context
- **Caching**: Frequently used workers are cached for faster execution
- **Resource Limits**: Configure max concurrent workers to manage resources

## Use Cases

1. **Software Development**: Coordinate code generation, testing, and documentation
2. **Data Pipeline**: Process multiple datasets in parallel
3. **Content Generation**: Create multi-part content (articles, reports, presentations)
4. **Code Review**: Distribute review tasks across multiple specialized reviewers
5. **Research**: Parallel literature review and analysis
6. **Testing**: Run different test suites concurrently

## Best Practices

1. **Define Clear Worker Roles**: Each worker should have a specific, well-defined purpose
2. **Use Appropriate Granularity**: Break tasks into chunks that can be parallelized
3. **Handle Dependencies**: Ensure tasks are ordered correctly when dependencies exist
4. **Monitor Performance**: Track metrics to identify bottlenecks
5. **Implement Retries**: Handle transient failures with retry logic
6. **Validate Results**: Check worker outputs before aggregation

## Troubleshooting

### Workers not executing in parallel
- Check that tasks are truly independent
- Verify async/await usage is correct
- Ensure sufficient resources available

### Result aggregation issues
- Validate worker output formats
- Check for missing or partial results
- Review aggregation strategy logic

### Performance degradation
- Monitor token usage per worker
- Check for worker overload
- Consider caching frequently used agents

## Contributing

To extend this system:

1. Add new worker types in `configs/worker_configs.py`
2. Implement custom routing logic in `orchestrator.py`
3. Create new aggregation strategies in `result_aggregator.py`
4. Add monitoring metrics in `monitor.py`

## License

This example is part of the pydantic-deepagents project and follows the same license.
