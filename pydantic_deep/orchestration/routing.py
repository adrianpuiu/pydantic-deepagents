"""Dynamic task routing and agent assignment.

This module provides intelligent routing of tasks to appropriate agents
based on capabilities, priorities, and current load.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic_deep.orchestration.models import (
    AgentCapability,
    AgentRouting,
    TaskDefinition,
)

if TYPE_CHECKING:
    from pydantic_deep.orchestration.models import OrchestrationConfig


class TaskRouter:
    """Routes tasks to appropriate agents based on capabilities and load."""

    def __init__(self, config: OrchestrationConfig) -> None:
        """Initialize task router.

        Args:
            config: Orchestration configuration with agent routing rules.
        """
        self.config = config
        self.agent_load: dict[str, int] = {}  # Track current load per agent

    def route_task(self, task: TaskDefinition) -> str:
        """Route a task to the most appropriate agent.

        Args:
            task: Task definition to route.

        Returns:
            Agent type identifier to use for the task.

        Raises:
            ValueError: If no suitable agent found for task requirements.
        """
        # If task specifies explicit agent type, use it
        if task.agent_type:
            return task.agent_type

        # Find agents that match required capabilities
        suitable_agents = self._find_suitable_agents(task)

        if not suitable_agents:
            # Fall back to general-purpose agent
            return "general-purpose"

        # Select best agent based on priority and current load
        best_agent = self._select_best_agent(suitable_agents, task)

        return best_agent.agent_type

    def _find_suitable_agents(self, task: TaskDefinition) -> list[AgentRouting]:
        """Find all agents that can handle the task.

        Args:
            task: Task definition.

        Returns:
            List of suitable agent routing configurations.
        """
        suitable = []
        for agent_routing in self.config.agent_routing:
            if self._agent_matches_capabilities(agent_routing, task.required_capabilities):
                suitable.append(agent_routing)
        return suitable

    def _agent_matches_capabilities(
        self, agent_routing: AgentRouting, required_capabilities: list[AgentCapability]
    ) -> bool:
        """Check if agent provides all required capabilities.

        Args:
            agent_routing: Agent routing configuration.
            required_capabilities: Required capabilities.

        Returns:
            True if agent provides all required capabilities.
        """
        agent_caps = set(agent_routing.capabilities)
        required_caps = set(required_capabilities)

        # Check if agent has all required capabilities
        return required_caps.issubset(agent_caps)

    def _select_best_agent(
        self, suitable_agents: list[AgentRouting], task: TaskDefinition
    ) -> AgentRouting:
        """Select the best agent from suitable candidates.

        Selection criteria (in order):
        1. Agent with least current load (if below max_concurrent_tasks)
        2. Highest routing priority
        3. Most specific capability match

        Args:
            suitable_agents: List of suitable agents.
            task: Task definition.

        Returns:
            Best agent routing configuration.
        """
        # Filter agents that haven't reached max capacity
        available_agents = [
            agent
            for agent in suitable_agents
            if self.agent_load.get(agent.agent_type, 0) < agent.max_concurrent_tasks
        ]

        # If all agents at capacity, use any suitable agent
        if not available_agents:
            available_agents = suitable_agents

        # Sort by:
        # 1. Current load (ascending)
        # 2. Priority (descending)
        # 3. Capability specificity (descending - more specific is better)
        def sort_key(agent: AgentRouting) -> tuple[int, int, int]:
            load = self.agent_load.get(agent.agent_type, 0)
            priority = agent.priority
            specificity = len(agent.capabilities)
            return (load, -priority, -specificity)

        available_agents.sort(key=sort_key)

        return available_agents[0]

    def increment_agent_load(self, agent_type: str) -> None:
        """Increment the current load for an agent.

        Args:
            agent_type: Agent type identifier.
        """
        self.agent_load[agent_type] = self.agent_load.get(agent_type, 0) + 1

    def decrement_agent_load(self, agent_type: str) -> None:
        """Decrement the current load for an agent.

        Args:
            agent_type: Agent type identifier.
        """
        current_load = self.agent_load.get(agent_type, 0)
        self.agent_load[agent_type] = max(0, current_load - 1)

    def get_agent_load(self, agent_type: str) -> int:
        """Get current load for an agent.

        Args:
            agent_type: Agent type identifier.

        Returns:
            Current number of tasks assigned to agent.
        """
        return self.agent_load.get(agent_type, 0)

    def reset_load(self) -> None:
        """Reset all agent load counters to zero."""
        self.agent_load.clear()

    def get_load_summary(self) -> dict[str, int]:
        """Get summary of current load across all agents.

        Returns:
            Dictionary mapping agent types to current load.
        """
        return self.agent_load.copy()


def create_default_routing() -> list[AgentRouting]:
    """Create default agent routing configuration.

    Returns:
        List of default agent routing configurations.
    """
    return [
        AgentRouting(
            agent_type="general-purpose",
            capabilities=[AgentCapability.GENERAL],
            priority=5,
            max_concurrent_tasks=3,
        ),
        AgentRouting(
            agent_type="code-analyzer",
            capabilities=[
                AgentCapability.CODE_ANALYSIS,
                AgentCapability.DEBUGGING,
                AgentCapability.GENERAL,
            ],
            priority=7,
            max_concurrent_tasks=2,
        ),
        AgentRouting(
            agent_type="code-generator",
            capabilities=[
                AgentCapability.CODE_GENERATION,
                AgentCapability.GENERAL,
            ],
            priority=7,
            max_concurrent_tasks=2,
        ),
        AgentRouting(
            agent_type="test-specialist",
            capabilities=[
                AgentCapability.TESTING,
                AgentCapability.CODE_ANALYSIS,
                AgentCapability.GENERAL,
            ],
            priority=6,
            max_concurrent_tasks=2,
        ),
        AgentRouting(
            agent_type="doc-writer",
            capabilities=[
                AgentCapability.DOCUMENTATION,
                AgentCapability.GENERAL,
            ],
            priority=6,
            max_concurrent_tasks=2,
        ),
        AgentRouting(
            agent_type="data-processor",
            capabilities=[
                AgentCapability.DATA_PROCESSING,
                AgentCapability.FILE_OPERATIONS,
                AgentCapability.GENERAL,
            ],
            priority=6,
            max_concurrent_tasks=2,
        ),
        AgentRouting(
            agent_type="researcher",
            capabilities=[
                AgentCapability.RESEARCH,
                AgentCapability.GENERAL,
            ],
            priority=5,
            max_concurrent_tasks=3,
        ),
    ]
