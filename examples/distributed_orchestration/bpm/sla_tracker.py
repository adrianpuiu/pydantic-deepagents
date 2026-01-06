"""SLA Tracker for BPM Workflows.

This module tracks Service Level Agreements (SLAs) for process states,
monitors deadlines, and triggers escalations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class SLAStatus(Enum):
    """SLA compliance status."""

    WITHIN_SLA = "within_sla"
    WARNING = "warning"  # Approaching deadline
    VIOLATED = "violated"
    ESCALATED = "escalated"


@dataclass
class SLADefinition:
    """Defines an SLA for a process state."""

    state_name: str
    target_hours: int
    warning_threshold_pct: float = 0.8  # Warn at 80% of time elapsed
    escalation_enabled: bool = True
    escalation_hours: int | None = None  # Auto-escalate after this many hours
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SLAInstance:
    """Tracks SLA for a specific process instance."""

    process_id: str
    state_name: str
    entered_at: datetime
    deadline: datetime
    warning_at: datetime
    escalation_at: datetime | None
    status: SLAStatus = SLAStatus.WITHIN_SLA
    escalation_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SLAViolation:
    """Records an SLA violation."""

    process_id: str
    state_name: str
    deadline: datetime
    actual_completion: datetime | None
    violation_hours: float
    escalated: bool = False


class SLATracker:
    """Tracks and monitors SLAs for business processes.

    The SLA tracker manages deadlines for process states,
    monitors compliance, and triggers escalations.

    Example:
        >>> tracker = SLATracker()
        >>> tracker.add_sla_definition(
        ...     SLADefinition(state_name="approval_pending", target_hours=24)
        ... )
        >>> tracker.start_sla("process_123", "approval_pending")
        >>> violations = tracker.check_violations()
    """

    def __init__(self):
        """Initialize the SLA tracker."""
        self.sla_definitions: dict[str, SLADefinition] = {}
        self.active_slas: dict[str, SLAInstance] = {}
        self.violation_history: list[SLAViolation] = []

    def add_sla_definition(self, definition: SLADefinition) -> None:
        """Add an SLA definition for a state.

        Args:
            definition: SLA definition to add.
        """
        self.sla_definitions[definition.state_name] = definition

    def start_sla(
        self,
        process_id: str,
        state_name: str,
        entered_at: datetime | None = None,
    ) -> SLAInstance | None:
        """Start tracking SLA for a process entering a state.

        Args:
            process_id: Process instance ID.
            state_name: State name.
            entered_at: Optional entry timestamp (defaults to now).

        Returns:
            Created SLA instance or None if no SLA defined for state.
        """
        definition = self.sla_definitions.get(state_name)
        if not definition:
            return None

        entered = entered_at or datetime.now()
        deadline = entered + timedelta(hours=definition.target_hours)

        # Calculate warning threshold
        total_seconds = (deadline - entered).total_seconds()
        warning_seconds = total_seconds * definition.warning_threshold_pct
        warning_at = entered + timedelta(seconds=warning_seconds)

        # Calculate escalation time if enabled
        escalation_at = None
        if definition.escalation_enabled and definition.escalation_hours:
            escalation_at = entered + timedelta(hours=definition.escalation_hours)

        instance = SLAInstance(
            process_id=process_id,
            state_name=state_name,
            entered_at=entered,
            deadline=deadline,
            warning_at=warning_at,
            escalation_at=escalation_at,
        )

        self.active_slas[process_id] = instance
        return instance

    def complete_sla(
        self,
        process_id: str,
        completed_at: datetime | None = None,
    ) -> tuple[bool, SLAStatus]:
        """Mark an SLA as complete.

        Args:
            process_id: Process instance ID.
            completed_at: Optional completion timestamp (defaults to now).

        Returns:
            Tuple of (was_within_sla, final_status).
        """
        if process_id not in self.active_slas:
            return True, SLAStatus.WITHIN_SLA

        instance = self.active_slas[process_id]
        completed = completed_at or datetime.now()

        # Check if violated
        if completed > instance.deadline:
            violation_hours = (completed - instance.deadline).total_seconds() / 3600
            violation = SLAViolation(
                process_id=process_id,
                state_name=instance.state_name,
                deadline=instance.deadline,
                actual_completion=completed,
                violation_hours=violation_hours,
                escalated=instance.escalation_count > 0,
            )
            self.violation_history.append(violation)

            # Remove from active tracking
            del self.active_slas[process_id]
            return False, SLAStatus.VIOLATED

        # Completed within SLA
        del self.active_slas[process_id]
        return True, SLAStatus.WITHIN_SLA

    def check_sla_status(
        self,
        process_id: str,
        current_time: datetime | None = None,
    ) -> SLAStatus:
        """Check current SLA status for a process.

        Args:
            process_id: Process instance ID.
            current_time: Optional current time (defaults to now).

        Returns:
            Current SLA status.
        """
        if process_id not in self.active_slas:
            return SLAStatus.WITHIN_SLA

        instance = self.active_slas[process_id]
        now = current_time or datetime.now()

        # Check if violated
        if now > instance.deadline:
            instance.status = SLAStatus.VIOLATED
            return SLAStatus.VIOLATED

        # Check if should escalate
        if instance.escalation_at and now > instance.escalation_at:
            instance.status = SLAStatus.ESCALATED
            return SLAStatus.ESCALATED

        # Check if in warning period
        if now > instance.warning_at:
            instance.status = SLAStatus.WARNING
            return SLAStatus.WARNING

        instance.status = SLAStatus.WITHIN_SLA
        return SLAStatus.WITHIN_SLA

    def check_violations(
        self,
        current_time: datetime | None = None,
    ) -> list[tuple[str, SLAInstance]]:
        """Check for SLA violations across all active processes.

        Args:
            current_time: Optional current time (defaults to now).

        Returns:
            List of (process_id, instance) tuples for violations.
        """
        now = current_time or datetime.now()
        violations = []

        for process_id, instance in self.active_slas.items():
            if now > instance.deadline:
                violations.append((process_id, instance))

        return violations

    def check_warnings(
        self,
        current_time: datetime | None = None,
    ) -> list[tuple[str, SLAInstance]]:
        """Check for SLA warnings (approaching deadline).

        Args:
            current_time: Optional current time (defaults to now).

        Returns:
            List of (process_id, instance) tuples for warnings.
        """
        now = current_time or datetime.now()
        warnings = []

        for process_id, instance in self.active_slas.items():
            if instance.warning_at < now < instance.deadline:
                warnings.append((process_id, instance))

        return warnings

    def check_escalations(
        self,
        current_time: datetime | None = None,
    ) -> list[tuple[str, SLAInstance]]:
        """Check for processes needing escalation.

        Args:
            current_time: Optional current time (defaults to now).

        Returns:
            List of (process_id, instance) tuples needing escalation.
        """
        now = current_time or datetime.now()
        escalations = []

        for process_id, instance in self.active_slas.items():
            if instance.escalation_at and now > instance.escalation_at:
                escalations.append((process_id, instance))

        return escalations

    def escalate(self, process_id: str) -> bool:
        """Mark a process as escalated.

        Args:
            process_id: Process instance ID.

        Returns:
            True if escalated, False if process not found.
        """
        if process_id not in self.active_slas:
            return False

        instance = self.active_slas[process_id]
        instance.escalation_count += 1
        instance.status = SLAStatus.ESCALATED

        return True

    def get_time_remaining(
        self,
        process_id: str,
        current_time: datetime | None = None,
    ) -> timedelta | None:
        """Get time remaining until SLA deadline.

        Args:
            process_id: Process instance ID.
            current_time: Optional current time (defaults to now).

        Returns:
            Time remaining or None if process not found.
        """
        if process_id not in self.active_slas:
            return None

        instance = self.active_slas[process_id]
        now = current_time or datetime.now()

        return instance.deadline - now

    def get_aging_report(
        self,
        current_time: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Generate aging report for all active SLAs.

        Args:
            current_time: Optional current time (defaults to now).

        Returns:
            List of aging report entries.
        """
        now = current_time or datetime.now()
        report = []

        for process_id, instance in self.active_slas.items():
            age_hours = (now - instance.entered_at).total_seconds() / 3600
            remaining_hours = (instance.deadline - now).total_seconds() / 3600
            pct_elapsed = age_hours / (age_hours + max(remaining_hours, 0)) * 100

            report.append({
                "process_id": process_id,
                "state_name": instance.state_name,
                "age_hours": round(age_hours, 2),
                "remaining_hours": round(remaining_hours, 2),
                "pct_elapsed": round(pct_elapsed, 1),
                "status": instance.status.value,
                "escalation_count": instance.escalation_count,
            })

        # Sort by percentage elapsed (most aged first)
        report.sort(key=lambda x: x["pct_elapsed"], reverse=True)

        return report

    def get_metrics(self) -> dict[str, Any]:
        """Get SLA performance metrics.

        Returns:
            Dictionary with SLA metrics.
        """
        total_violations = len(self.violation_history)
        total_completed = total_violations + len([
            s for s in self.active_slas.values()
            if s.status == SLAStatus.WITHIN_SLA
        ])

        compliance_rate = (
            (total_completed - total_violations) / total_completed
            if total_completed > 0
            else 1.0
        )

        avg_violation_hours = (
            sum(v.violation_hours for v in self.violation_history) / total_violations
            if total_violations > 0
            else 0
        )

        return {
            "active_slas": len(self.active_slas),
            "total_violations": total_violations,
            "compliance_rate": round(compliance_rate * 100, 2),
            "avg_violation_hours": round(avg_violation_hours, 2),
            "violations_by_state": self._violations_by_state(),
        }

    def _violations_by_state(self) -> dict[str, int]:
        """Get violation counts by state."""
        counts: dict[str, int] = {}
        for violation in self.violation_history:
            counts[violation.state_name] = counts.get(violation.state_name, 0) + 1
        return counts
