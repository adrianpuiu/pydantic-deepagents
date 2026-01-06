"""Distributed Agent Orchestration System.

This package provides a distributed agent orchestration framework that
enables multiple specialized worker agents to collaborate on complex tasks.

Main components:
- DistributedOrchestrator: Main coordinator for task distribution
- Worker configurations: Specialized agents for different domains
- Task management: Queue, priority, and status tracking
- Result aggregation: Intelligent combination of worker outputs

Quick start:
    >>> from distributed_orchestration import DistributedOrchestrator
    >>> orchestrator = DistributedOrchestrator()
    >>> result = await orchestrator.execute("Your complex task here")
"""

from .orchestrator import (
    DistributedOrchestrator,
    Task,
    TaskPriority,
    TaskStatus,
    WorkerStatus,
)

__all__ = [
    "DistributedOrchestrator",
    "Task",
    "TaskPriority",
    "TaskStatus",
    "WorkerStatus",
]
