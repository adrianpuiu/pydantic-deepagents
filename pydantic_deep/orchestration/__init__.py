"""Dynamic orchestration system for multi-agent workflows.

This module provides comprehensive orchestration capabilities for coordinating
multiple agents working together on complex workflows.

Key Features:
- Task definition with dependencies and priorities
- Dynamic agent routing based on capabilities
- Multiple execution strategies (sequential, parallel, DAG-based)
- Automatic retry with exponential backoff
- Workflow state management and progress tracking
- Integration with existing pydantic-deep toolsets

Example:
    ```python
    from pydantic_deep import create_deep_agent, create_default_deps
    from pydantic_deep.orchestration import (
        TaskOrchestrator,
        WorkflowDefinition,
        TaskDefinition,
        AgentCapability,
        ExecutionStrategy,
    )

    # Create agent and deps
    agent = create_deep_agent(model="openai:gpt-4")
    deps = create_default_deps()

    # Create orchestrator
    orchestrator = TaskOrchestrator(agent, deps)

    # Define workflow
    workflow = WorkflowDefinition(
        id="data-analysis",
        name="Data Analysis Pipeline",
        tasks=[
            TaskDefinition(
                id="collect",
                description="Collect data from sources",
                required_capabilities=[AgentCapability.DATA_PROCESSING],
            ),
            TaskDefinition(
                id="analyze",
                description="Analyze collected data",
                depends_on=["collect"],
                required_capabilities=[AgentCapability.CODE_ANALYSIS],
            ),
            TaskDefinition(
                id="report",
                description="Generate analysis report",
                depends_on=["analyze"],
                required_capabilities=[AgentCapability.DOCUMENTATION],
            ),
        ],
        execution_strategy=ExecutionStrategy.DAG,
    )

    # Execute workflow
    result = await orchestrator.execute_workflow(workflow)
    ```
"""

from pydantic_deep.orchestration.coordinator import (
    TaskOrchestrator,
    create_orchestrator,
)
from pydantic_deep.orchestration.models import (
    AgentCapability,
    AgentRouting,
    ExecutionStrategy,
    OrchestrationConfig,
    RetryConfig,
    TaskDefinition,
    TaskResult,
    TaskStatus,
    WorkflowDefinition,
    WorkflowState,
)
from pydantic_deep.orchestration.routing import TaskRouter, create_default_routing
from pydantic_deep.orchestration.state import StateManager
from pydantic_deep.orchestration.strategy_selector import (
    auto_select_strategy,
    explain_strategy_choice,
    recommend_strategy,
)

__all__ = [
    # Main orchestrator
    "TaskOrchestrator",
    "create_orchestrator",
    # Models
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
    # Routing
    "TaskRouter",
    "create_default_routing",
    # State management
    "StateManager",
    # Strategy selection
    "auto_select_strategy",
    "recommend_strategy",
    "explain_strategy_choice",
]
