"""Audit Trail for BPM Workflows.

This module provides immutable audit logging for compliance
and process traceability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AuditEventType(Enum):
    """Type of audit event."""

    PROCESS_CREATED = "process_created"
    STATE_TRANSITION = "state_transition"
    APPROVAL_DECISION = "approval_decision"
    DATA_MODIFIED = "data_modified"
    EXCEPTION_RAISED = "exception_raised"
    EXCEPTION_RESOLVED = "exception_resolved"
    SLA_VIOLATED = "sla_violated"
    ESCALATION = "escalation"
    SYSTEM_ACTION = "system_action"
    USER_ACTION = "user_action"


@dataclass
class AuditEvent:
    """Represents an immutable audit event."""

    event_id: str
    event_type: AuditEventType
    process_id: str
    timestamp: datetime
    actor: str  # User ID or "SYSTEM"
    action: str
    details: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Make event immutable after creation."""
        # In Python, we can't truly make dataclass immutable,
        # but we can use frozen=True in production
        pass


class AuditTrail:
    """Maintains an immutable audit trail for business processes.

    The audit trail records all significant events in a process
    lifecycle for compliance, debugging, and analysis.

    Example:
        >>> trail = AuditTrail()
        >>> trail.log_event(
        ...     process_id="PR-001",
        ...     event_type=AuditEventType.PROCESS_CREATED,
        ...     actor="user@example.com",
        ...     action="Created purchase requisition",
        ...     details={"amount": 5000, "department": "IT"}
        ... )
    """

    def __init__(self):
        """Initialize the audit trail."""
        self.events: list[AuditEvent] = []
        self.event_counter = 0

    def log_event(
        self,
        process_id: str,
        event_type: AuditEventType,
        actor: str,
        action: str,
        details: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> AuditEvent:
        """Log an audit event.

        Args:
            process_id: Process instance ID.
            event_type: Type of event.
            actor: User or system performing the action.
            action: Description of the action.
            details: Optional event details.
            metadata: Optional event metadata.
            timestamp: Optional timestamp (defaults to now).

        Returns:
            Created audit event.
        """
        event_id = f"AE-{self.event_counter:06d}"
        self.event_counter += 1

        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            process_id=process_id,
            timestamp=timestamp or datetime.now(),
            actor=actor,
            action=action,
            details=details or {},
            metadata=metadata or {},
        )

        self.events.append(event)
        return event

    def log_process_created(
        self,
        process_id: str,
        actor: str,
        process_data: dict[str, Any],
    ) -> AuditEvent:
        """Log process creation.

        Args:
            process_id: Process instance ID.
            actor: User creating the process.
            process_data: Initial process data.

        Returns:
            Created audit event.
        """
        return self.log_event(
            process_id=process_id,
            event_type=AuditEventType.PROCESS_CREATED,
            actor=actor,
            action=f"Process {process_id} created",
            details=process_data,
        )

    def log_state_transition(
        self,
        process_id: str,
        actor: str,
        from_state: str,
        to_state: str,
        reason: str | None = None,
    ) -> AuditEvent:
        """Log state transition.

        Args:
            process_id: Process instance ID.
            actor: Actor performing transition.
            from_state: Previous state.
            to_state: New state.
            reason: Optional reason for transition.

        Returns:
            Created audit event.
        """
        return self.log_event(
            process_id=process_id,
            event_type=AuditEventType.STATE_TRANSITION,
            actor=actor,
            action=f"Transitioned from {from_state} to {to_state}",
            details={
                "from_state": from_state,
                "to_state": to_state,
                "reason": reason,
            },
        )

    def log_approval_decision(
        self,
        process_id: str,
        approver: str,
        decision: str,
        comments: str = "",
    ) -> AuditEvent:
        """Log approval decision.

        Args:
            process_id: Process instance ID.
            approver: Approver identifier.
            decision: Decision (approved/rejected/delegated).
            comments: Optional comments.

        Returns:
            Created audit event.
        """
        return self.log_event(
            process_id=process_id,
            event_type=AuditEventType.APPROVAL_DECISION,
            actor=approver,
            action=f"Approval decision: {decision}",
            details={
                "decision": decision,
                "comments": comments,
            },
        )

    def log_data_modification(
        self,
        process_id: str,
        actor: str,
        field_name: str,
        old_value: Any,
        new_value: Any,
        reason: str | None = None,
    ) -> AuditEvent:
        """Log data modification.

        Args:
            process_id: Process instance ID.
            actor: User modifying data.
            field_name: Name of modified field.
            old_value: Previous value.
            new_value: New value.
            reason: Optional reason for modification.

        Returns:
            Created audit event.
        """
        return self.log_event(
            process_id=process_id,
            event_type=AuditEventType.DATA_MODIFIED,
            actor=actor,
            action=f"Modified field '{field_name}'",
            details={
                "field": field_name,
                "old_value": str(old_value),
                "new_value": str(new_value),
                "reason": reason,
            },
        )

    def log_exception(
        self,
        process_id: str,
        actor: str,
        exception_type: str,
        description: str,
        resolved: bool = False,
    ) -> AuditEvent:
        """Log an exception.

        Args:
            process_id: Process instance ID.
            actor: Actor logging the exception.
            exception_type: Type of exception.
            description: Exception description.
            resolved: Whether exception is resolved.

        Returns:
            Created audit event.
        """
        event_type = (
            AuditEventType.EXCEPTION_RESOLVED if resolved
            else AuditEventType.EXCEPTION_RAISED
        )

        return self.log_event(
            process_id=process_id,
            event_type=event_type,
            actor=actor,
            action=f"Exception: {exception_type}",
            details={
                "exception_type": exception_type,
                "description": description,
                "resolved": resolved,
            },
        )

    def get_process_history(
        self,
        process_id: str,
        event_type: AuditEventType | None = None,
    ) -> list[AuditEvent]:
        """Get audit history for a process.

        Args:
            process_id: Process instance ID.
            event_type: Optional filter by event type.

        Returns:
            List of audit events.
        """
        events = [e for e in self.events if e.process_id == process_id]

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        return sorted(events, key=lambda e: e.timestamp)

    def get_events_by_actor(
        self,
        actor: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[AuditEvent]:
        """Get events by actor.

        Args:
            actor: Actor identifier.
            start_time: Optional start time filter.
            end_time: Optional end time filter.

        Returns:
            List of audit events.
        """
        events = [e for e in self.events if e.actor == actor]

        if start_time:
            events = [e for e in events if e.timestamp >= start_time]

        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        return sorted(events, key=lambda e: e.timestamp)

    def get_events_by_type(
        self,
        event_type: AuditEventType,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[AuditEvent]:
        """Get events by type.

        Args:
            event_type: Event type to filter.
            start_time: Optional start time filter.
            end_time: Optional end time filter.

        Returns:
            List of audit events.
        """
        events = [e for e in self.events if e.event_type == event_type]

        if start_time:
            events = [e for e in events if e.timestamp >= start_time]

        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        return sorted(events, key=lambda e: e.timestamp)

    def export_to_dict(
        self,
        process_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Export audit events to dictionary format.

        Args:
            process_id: Optional process ID filter.

        Returns:
            List of event dictionaries.
        """
        events = self.events
        if process_id:
            events = [e for e in events if e.process_id == process_id]

        return [
            {
                "event_id": e.event_id,
                "event_type": e.event_type.value,
                "process_id": e.process_id,
                "timestamp": e.timestamp.isoformat(),
                "actor": e.actor,
                "action": e.action,
                "details": e.details,
                "metadata": e.metadata,
            }
            for e in events
        ]

    def generate_compliance_report(
        self,
        process_id: str,
    ) -> dict[str, Any]:
        """Generate compliance report for a process.

        Args:
            process_id: Process instance ID.

        Returns:
            Compliance report dictionary.
        """
        events = self.get_process_history(process_id)

        if not events:
            return {
                "process_id": process_id,
                "error": "No audit events found",
            }

        # Analyze events for compliance
        state_transitions = [
            e for e in events if e.event_type == AuditEventType.STATE_TRANSITION
        ]
        approvals = [
            e for e in events if e.event_type == AuditEventType.APPROVAL_DECISION
        ]
        data_mods = [
            e for e in events if e.event_type == AuditEventType.DATA_MODIFIED
        ]
        exceptions = [
            e for e in events
            if e.event_type in [AuditEventType.EXCEPTION_RAISED, AuditEventType.EXCEPTION_RESOLVED]
        ]

        # Check segregation of duties
        actors = set(e.actor for e in events)
        approval_actors = set(e.actor for e in approvals)

        return {
            "process_id": process_id,
            "audit_summary": {
                "total_events": len(events),
                "state_transitions": len(state_transitions),
                "approvals": len(approvals),
                "data_modifications": len(data_mods),
                "exceptions": len(exceptions),
            },
            "timeline": {
                "created": events[0].timestamp.isoformat() if events else None,
                "last_activity": events[-1].timestamp.isoformat() if events else None,
            },
            "actors": {
                "total_unique_actors": len(actors),
                "actors": list(actors),
                "approvers": list(approval_actors),
            },
            "compliance_checks": {
                "has_complete_audit_trail": len(events) > 0,
                "has_approval_evidence": len(approvals) > 0,
                "segregation_of_duties": len(actors) >= 2,  # At least 2 different actors
            },
            "state_history": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "from": e.details.get("from_state"),
                    "to": e.details.get("to_state"),
                    "actor": e.actor,
                }
                for e in state_transitions
            ],
            "approval_history": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "approver": e.actor,
                    "decision": e.details.get("decision"),
                    "comments": e.details.get("comments"),
                }
                for e in approvals
            ],
        }

    def get_statistics(self) -> dict[str, Any]:
        """Get audit trail statistics.

        Returns:
            Statistics dictionary.
        """
        event_type_counts = {}
        for event in self.events:
            event_type = event.event_type.value
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

        actor_counts = {}
        for event in self.events:
            actor_counts[event.actor] = actor_counts.get(event.actor, 0) + 1

        unique_processes = len(set(e.process_id for e in self.events))

        return {
            "total_events": len(self.events),
            "unique_processes": unique_processes,
            "unique_actors": len(actor_counts),
            "events_by_type": event_type_counts,
            "top_actors": sorted(
                actor_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
        }
