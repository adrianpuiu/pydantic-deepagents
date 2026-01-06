"""BPM Orchestrator - Enhanced orchestrator with BPM capabilities.

This module extends the distributed orchestrator with business process
management features including state machines, approvals, and SLA tracking.
"""

from __future__ import annotations

import sys
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orchestrator import DistributedOrchestrator, Task, TaskPriority, TaskStatus
from pydantic_deep.types import SubAgentConfig

from .approval_engine import ApprovalChain, ApprovalEngine
from .audit_trail import AuditEventType, AuditTrail
from .business_rules import RulesEngine
from .sla_tracker import SLATracker
from .state_machine import ProcessState, StateMachine


@dataclass
class ProcessInstance:
    """Represents an active business process instance."""

    process_id: str
    process_type: str
    state: ProcessState
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "SYSTEM"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessDefinition:
    """Defines a business process workflow."""

    name: str
    description: str
    state_machine: StateMachine
    workers: list[SubAgentConfig]
    initial_state: str
    rules_engine: RulesEngine | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BPMOrchestrator(DistributedOrchestrator):
    """BPM-enhanced orchestrator with workflow, approval, and compliance features.

    Extends the base orchestrator with:
    - State machine workflow execution
    - Multi-level approval routing
    - Business rules evaluation
    - SLA tracking and escalations
    - Immutable audit trail

    Example:
        >>> from bpm import StateMachine, StateDefinition, TransitionDefinition
        >>>
        >>> # Define state machine
        >>> machine = StateMachine()
        >>> machine.add_state(StateDefinition(name="draft", description="Draft"))
        >>> machine.add_state(StateDefinition(name="submitted", description="Submitted"))
        >>> machine.add_transition(
        ...     TransitionDefinition(from_state="draft", to_state="submitted", name="submit")
        ... )
        >>>
        >>> # Create process definition
        >>> process_def = ProcessDefinition(
        ...     name="simple_approval",
        ...     description="Simple approval workflow",
        ...     state_machine=machine,
        ...     workers=[],
        ...     initial_state="draft"
        ... )
        >>>
        >>> # Create orchestrator
        >>> orchestrator = BPMOrchestrator(process_definition=process_def)
        >>> process = await orchestrator.start_process(
        ...     process_type="simple_approval",
        ...     initial_data={"title": "Test", "amount": 1000},
        ...     created_by="user@example.com"
        ... )
    """

    def __init__(
        self,
        process_definition: ProcessDefinition,
        model: str = "openai:gpt-4o-mini",
        **kwargs,
    ):
        """Initialize the BPM orchestrator.

        Args:
            process_definition: Process workflow definition.
            model: Model to use for orchestrator and workers.
            **kwargs: Additional arguments for base orchestrator.
        """
        # Initialize base orchestrator with process-specific workers
        super().__init__(
            model=model,
            custom_workers=process_definition.workers,
            **kwargs,
        )

        self.process_definition = process_definition

        # BPM components
        self.state_machine = process_definition.state_machine
        self.approval_engine = ApprovalEngine()
        self.rules_engine = process_definition.rules_engine or RulesEngine()
        self.sla_tracker = SLATracker()
        self.audit_trail = AuditTrail()

        # Process instance management
        self.active_processes: dict[str, ProcessInstance] = {}
        self.process_counter = 0

    async def start_process(
        self,
        process_type: str,
        initial_data: dict[str, Any],
        created_by: str = "SYSTEM",
        metadata: dict[str, Any] | None = None,
    ) -> ProcessInstance:
        """Start a new process instance.

        Args:
            process_type: Type of process to start.
            initial_data: Initial process data.
            created_by: User starting the process.
            metadata: Optional process metadata.

        Returns:
            Created process instance.
        """
        # Generate process ID
        process_id = f"{process_type.upper()}-{self.process_counter:04d}"
        self.process_counter += 1

        # Create initial process state
        process_state = ProcessState(
            state_name=self.process_definition.initial_state,
            state_data=initial_data.copy(),
        )

        # Create process instance
        instance = ProcessInstance(
            process_id=process_id,
            process_type=process_type,
            state=process_state,
            created_by=created_by,
            metadata=metadata or {},
        )

        self.active_processes[process_id] = instance

        # Log creation in audit trail
        self.audit_trail.log_process_created(
            process_id=process_id,
            actor=created_by,
            process_data=initial_data,
        )

        # Start SLA tracking if defined for initial state
        self.sla_tracker.start_sla(process_id, self.process_definition.initial_state)

        return instance

    async def transition_state(
        self,
        process_id: str,
        to_state: str,
        actor: str = "SYSTEM",
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        """Transition a process to a new state.

        Args:
            process_id: Process instance ID.
            to_state: Target state name.
            actor: Actor performing the transition.
            reason: Optional reason for transition.
            metadata: Optional transition metadata.

        Returns:
            Tuple of (success, message).
        """
        if process_id not in self.active_processes:
            return False, f"Process {process_id} not found"

        instance = self.active_processes[process_id]
        current_state = instance.state.state_name

        # Complete SLA for current state
        self.sla_tracker.complete_sla(process_id)

        # Perform state transition
        result, message = self.state_machine.transition(
            instance.state,
            to_state,
            actor=actor,
            reason=reason,
            metadata=metadata,
        )

        if result.name == "SUCCESS":
            # Log in audit trail
            self.audit_trail.log_state_transition(
                process_id=process_id,
                actor=actor,
                from_state=current_state,
                to_state=to_state,
                reason=reason,
            )

            # Start SLA for new state
            self.sla_tracker.start_sla(process_id, to_state)

            return True, message

        return False, message

    async def execute_step(
        self,
        process_id: str,
        step_name: str,
        step_input: str,
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> str:
        """Execute a process step using the orchestrator.

        Args:
            process_id: Process instance ID.
            step_name: Name of the step.
            step_input: Input for the step.
            priority: Task priority.

        Returns:
            Step execution result.
        """
        if process_id not in self.active_processes:
            raise ValueError(f"Process {process_id} not found")

        # Execute using base orchestrator
        result = await self.execute(
            task_description=step_input,
            priority=priority,
            metadata={"process_id": process_id, "step_name": step_name},
        )

        # Log in audit trail
        self.audit_trail.log_event(
            process_id=process_id,
            event_type=AuditEventType.SYSTEM_ACTION,
            actor="SYSTEM",
            action=f"Executed step: {step_name}",
            details={"step_name": step_name, "result_length": len(result)},
        )

        return result

    async def request_approval(
        self,
        process_id: str,
        approval_chain: ApprovalChain,
        context: dict[str, Any] | None = None,
    ) -> list[str]:
        """Request approvals for a process.

        Args:
            process_id: Process instance ID.
            approval_chain: Approval chain definition.
            context: Optional context for auto-approval rules.

        Returns:
            List of created approval request IDs.
        """
        if process_id not in self.active_processes:
            raise ValueError(f"Process {process_id} not found")

        request_ids = self.approval_engine.create_approval_request(
            process_id=process_id,
            approval_chain=approval_chain,
            context=context or {},
        )

        # Log in audit trail
        self.audit_trail.log_event(
            process_id=process_id,
            event_type=AuditEventType.SYSTEM_ACTION,
            actor="SYSTEM",
            action="Approval requested",
            details={
                "approval_steps": len(approval_chain.steps),
                "request_ids": request_ids,
            },
        )

        return request_ids

    async def approve(
        self,
        process_id: str,
        approver: str,
        comments: str = "",
        metadata: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        """Approve a pending approval request.

        Args:
            process_id: Process instance ID.
            approver: Approver identifier.
            comments: Optional approval comments.
            metadata: Optional metadata.
            context: Optional context for next step evaluation.

        Returns:
            Tuple of (success, message).
        """
        success, message = self.approval_engine.approve(
            process_id=process_id,
            approver=approver,
            comments=comments,
            metadata=metadata,
            context=context,
        )

        if success:
            # Log in audit trail
            self.audit_trail.log_approval_decision(
                process_id=process_id,
                approver=approver,
                decision="approved",
                comments=comments,
            )

        return success, message

    async def reject(
        self,
        process_id: str,
        approver: str,
        comments: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        """Reject a pending approval request.

        Args:
            process_id: Process instance ID.
            approver: Approver identifier.
            comments: Optional rejection comments.
            metadata: Optional metadata.

        Returns:
            Tuple of (success, message).
        """
        success, message = self.approval_engine.reject(
            process_id=process_id,
            approver=approver,
            comments=comments,
            metadata=metadata,
        )

        if success:
            # Log in audit trail
            self.audit_trail.log_approval_decision(
                process_id=process_id,
                approver=approver,
                decision="rejected",
                comments=comments,
            )

        return success, message

    def get_process_status(self, process_id: str) -> dict[str, Any]:
        """Get comprehensive process status.

        Args:
            process_id: Process instance ID.

        Returns:
            Process status dictionary.
        """
        if process_id not in self.active_processes:
            return {"error": f"Process {process_id} not found"}

        instance = self.active_processes[process_id]

        # Get component statuses
        approval_status = self.approval_engine.get_approval_status(process_id)
        sla_status = self.sla_tracker.check_sla_status(process_id)
        time_remaining = self.sla_tracker.get_time_remaining(process_id)

        return {
            "process_id": process_id,
            "process_type": instance.process_type,
            "current_state": instance.state.state_name,
            "created_at": instance.created_at.isoformat(),
            "created_by": instance.created_by,
            "process_data": instance.state.state_data,
            "state_history": [
                {
                    "from_state": e.from_state,
                    "to_state": e.to_state,
                    "timestamp": e.timestamp.isoformat(),
                    "actor": e.actor,
                }
                for e in instance.state.history
            ],
            "approval": approval_status,
            "sla": {
                "status": sla_status.value,
                "time_remaining_hours": (
                    time_remaining.total_seconds() / 3600 if time_remaining else None
                ),
            },
            "is_complete": self.state_machine.is_terminal_state(instance.state.state_name),
        }

    def get_audit_trail(self, process_id: str) -> list[dict[str, Any]]:
        """Get audit trail for a process.

        Args:
            process_id: Process instance ID.

        Returns:
            List of audit events.
        """
        return self.audit_trail.export_to_dict(process_id=process_id)

    def generate_compliance_report(self, process_id: str) -> dict[str, Any]:
        """Generate compliance report for a process.

        Args:
            process_id: Process instance ID.

        Returns:
            Compliance report.
        """
        return self.audit_trail.generate_compliance_report(process_id)

    def check_sla_violations(self) -> list[tuple[str, Any]]:
        """Check for SLA violations across all processes.

        Returns:
            List of (process_id, instance) tuples for violations.
        """
        return self.sla_tracker.check_violations()

    def get_bpm_metrics(self) -> dict[str, Any]:
        """Get comprehensive BPM metrics.

        Returns:
            BPM metrics dictionary.
        """
        base_metrics = self.get_metrics()
        sla_metrics = self.sla_tracker.get_metrics()
        audit_stats = self.audit_trail.get_statistics()

        # Process state distribution
        state_distribution = {}
        for instance in self.active_processes.values():
            state = instance.state.state_name
            state_distribution[state] = state_distribution.get(state, 0) + 1

        return {
            "orchestration": base_metrics,
            "processes": {
                "total_active": len(self.active_processes),
                "state_distribution": state_distribution,
            },
            "sla": sla_metrics,
            "audit": audit_stats,
        }
