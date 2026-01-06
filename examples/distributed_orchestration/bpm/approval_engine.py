"""Approval Engine for BPM Workflows.

This module handles multi-level approval workflows with routing,
auto-approval rules, escalations, and delegation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable


class ApprovalDecisionType(Enum):
    """Type of approval decision."""

    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    DELEGATED = "delegated"


class ApprovalStatus(Enum):
    """Status of an approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    EXPIRED = "expired"


@dataclass
class ApprovalStep:
    """Defines an approval requirement."""

    approver_role: str
    description: str
    auto_approve_rule: Callable[[dict[str, Any]], bool] | None = None
    sla_hours: int = 24
    escalation_path: list[str] = field(default_factory=list)
    is_parallel: bool = False  # Can be approved in parallel with other steps
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ApprovalDecision:
    """Records an approval decision."""

    process_id: str
    step_index: int
    approver: str
    decision: ApprovalDecisionType
    timestamp: datetime
    comments: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ApprovalRequest:
    """Represents an active approval request."""

    process_id: str
    step: ApprovalStep
    step_index: int
    created_at: datetime
    deadline: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    decisions: list[ApprovalDecision] = field(default_factory=list)
    escalation_count: int = 0


class ApprovalChain:
    """Represents a chain of approval steps."""

    def __init__(self, steps: list[ApprovalStep]):
        """Initialize approval chain.

        Args:
            steps: List of approval steps in order.
        """
        self.steps = steps
        self.current_step_index = 0

    def get_current_step(self) -> ApprovalStep | None:
        """Get the current approval step.

        Returns:
            Current approval step or None if chain is complete.
        """
        if self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def advance(self) -> bool:
        """Advance to the next step in the chain.

        Returns:
            True if advanced, False if chain is complete.
        """
        if self.current_step_index < len(self.steps) - 1:
            self.current_step_index += 1
            return True
        return False

    def is_complete(self) -> bool:
        """Check if approval chain is complete.

        Returns:
            True if all steps are complete.
        """
        return self.current_step_index >= len(self.steps)


class ApprovalEngine:
    """Manages approval workflows for business processes.

    The approval engine handles:
    - Multi-level approval chains
    - Auto-approval based on business rules
    - SLA tracking and escalations
    - Parallel and sequential approvals
    - Approval delegation

    Example:
        >>> engine = ApprovalEngine()
        >>> chain = ApprovalChain([
        ...     ApprovalStep(approver_role="manager", description="Manager approval"),
        ...     ApprovalStep(approver_role="finance", description="Finance approval"),
        ... ])
        >>> request_id = engine.create_approval_request("process_123", chain)
    """

    def __init__(self):
        """Initialize the approval engine."""
        self.active_requests: dict[str, list[ApprovalRequest]] = {}
        self.approval_history: dict[str, list[ApprovalDecision]] = {}
        self.approval_chains: dict[str, ApprovalChain] = {}

    def create_approval_request(
        self,
        process_id: str,
        approval_chain: ApprovalChain,
        context: dict[str, Any] | None = None,
    ) -> list[str]:
        """Create approval requests for a process.

        Args:
            process_id: Process instance ID.
            approval_chain: Approval chain definition.
            context: Optional context for auto-approval evaluation.

        Returns:
            List of created request IDs.
        """
        self.approval_chains[process_id] = approval_chain
        self.active_requests[process_id] = []

        # Create request for first step(s)
        return self._create_next_requests(process_id, context or {})

    def _create_next_requests(
        self, process_id: str, context: dict[str, Any]
    ) -> list[str]:
        """Create requests for the next approval step(s).

        Args:
            process_id: Process instance ID.
            context: Context data for evaluation.

        Returns:
            List of created request IDs.
        """
        chain = self.approval_chains[process_id]
        step = chain.get_current_step()

        if not step:
            return []

        # Check auto-approval rule
        if step.auto_approve_rule and step.auto_approve_rule(context):
            # Auto-approve and move to next step
            self._record_auto_approval(process_id, chain.current_step_index, step)
            chain.advance()
            return self._create_next_requests(process_id, context)

        # Create approval request
        now = datetime.now()
        deadline = now + timedelta(hours=step.sla_hours)

        request = ApprovalRequest(
            process_id=process_id,
            step=step,
            step_index=chain.current_step_index,
            created_at=now,
            deadline=deadline,
        )

        if process_id not in self.active_requests:
            self.active_requests[process_id] = []

        self.active_requests[process_id].append(request)

        return [f"{process_id}_step_{chain.current_step_index}"]

    def _record_auto_approval(
        self, process_id: str, step_index: int, step: ApprovalStep
    ) -> None:
        """Record an auto-approval decision.

        Args:
            process_id: Process instance ID.
            step_index: Step index.
            step: Approval step.
        """
        decision = ApprovalDecision(
            process_id=process_id,
            step_index=step_index,
            approver="SYSTEM",
            decision=ApprovalDecisionType.APPROVED,
            timestamp=datetime.now(),
            comments="Auto-approved by business rule",
        )

        if process_id not in self.approval_history:
            self.approval_history[process_id] = []

        self.approval_history[process_id].append(decision)

    def approve(
        self,
        process_id: str,
        approver: str,
        comments: str = "",
        metadata: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        """Approve a pending request.

        Args:
            process_id: Process instance ID.
            approver: Approver identifier.
            comments: Optional approval comments.
            metadata: Optional metadata.
            context: Optional context for next step evaluation.

        Returns:
            Tuple of (success, message).
        """
        return self._make_decision(
            process_id,
            approver,
            ApprovalDecisionType.APPROVED,
            comments,
            metadata or {},
            context or {},
        )

    def reject(
        self,
        process_id: str,
        approver: str,
        comments: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        """Reject a pending request.

        Args:
            process_id: Process instance ID.
            approver: Approver identifier.
            comments: Optional rejection comments.
            metadata: Optional metadata.

        Returns:
            Tuple of (success, message).
        """
        return self._make_decision(
            process_id,
            approver,
            ApprovalDecisionType.REJECTED,
            comments,
            metadata or {},
            {},
        )

    def _make_decision(
        self,
        process_id: str,
        approver: str,
        decision_type: ApprovalDecisionType,
        comments: str,
        metadata: dict[str, Any],
        context: dict[str, Any],
    ) -> tuple[bool, str]:
        """Make an approval decision.

        Args:
            process_id: Process instance ID.
            approver: Approver identifier.
            decision_type: Type of decision.
            comments: Decision comments.
            metadata: Decision metadata.
            context: Context for next step.

        Returns:
            Tuple of (success, message).
        """
        # Find active request
        if process_id not in self.active_requests:
            return False, f"No active approval request for process {process_id}"

        requests = self.active_requests[process_id]
        if not requests:
            return False, f"No pending approval requests for process {process_id}"

        # Get current request (first pending)
        request = requests[0]

        # Record decision
        decision = ApprovalDecision(
            process_id=process_id,
            step_index=request.step_index,
            approver=approver,
            decision=decision_type,
            timestamp=datetime.now(),
            comments=comments,
            metadata=metadata,
        )

        request.decisions.append(decision)

        if process_id not in self.approval_history:
            self.approval_history[process_id] = []

        self.approval_history[process_id].append(decision)

        # Update request status
        if decision_type == ApprovalDecisionType.APPROVED:
            request.status = ApprovalStatus.APPROVED
            # Remove from active requests
            self.active_requests[process_id].remove(request)

            # Advance chain and create next requests
            chain = self.approval_chains[process_id]
            if chain.advance():
                self._create_next_requests(process_id, context)
                return True, f"Approved by {approver}. Advanced to next approval step."
            else:
                return True, f"Approved by {approver}. All approvals complete."

        elif decision_type == ApprovalDecisionType.REJECTED:
            request.status = ApprovalStatus.REJECTED
            # Remove from active requests
            self.active_requests[process_id].remove(request)
            return True, f"Rejected by {approver}"

        return True, "Decision recorded"

    def escalate(self, process_id: str) -> tuple[bool, str]:
        """Escalate an approval request to next level.

        Args:
            process_id: Process instance ID.

        Returns:
            Tuple of (success, message).
        """
        if process_id not in self.active_requests:
            return False, f"No active approval request for process {process_id}"

        requests = self.active_requests[process_id]
        if not requests:
            return False, "No pending approval requests"

        request = requests[0]
        request.escalation_count += 1

        # Check if there's an escalation path
        if not request.step.escalation_path:
            return False, "No escalation path defined for this step"

        if request.escalation_count > len(request.step.escalation_path):
            return False, "Escalation path exhausted"

        # Record escalation
        decision = ApprovalDecision(
            process_id=process_id,
            step_index=request.step_index,
            approver="SYSTEM",
            decision=ApprovalDecisionType.ESCALATED,
            timestamp=datetime.now(),
            comments=f"Escalated to level {request.escalation_count}",
        )

        request.decisions.append(decision)
        request.status = ApprovalStatus.ESCALATED

        next_approver = request.step.escalation_path[request.escalation_count - 1]
        return True, f"Escalated to {next_approver}"

    def check_sla_violations(self) -> list[tuple[str, ApprovalRequest]]:
        """Check for SLA violations in active requests.

        Returns:
            List of (process_id, request) tuples for violations.
        """
        violations = []
        now = datetime.now()

        for process_id, requests in self.active_requests.items():
            for request in requests:
                if request.status == ApprovalStatus.PENDING and now > request.deadline:
                    violations.append((process_id, request))

        return violations

    def get_pending_approvals(
        self, approver_role: str | None = None
    ) -> list[ApprovalRequest]:
        """Get all pending approval requests.

        Args:
            approver_role: Optional filter by approver role.

        Returns:
            List of pending approval requests.
        """
        pending = []

        for requests in self.active_requests.values():
            for request in requests:
                if request.status == ApprovalStatus.PENDING:
                    if approver_role is None or request.step.approver_role == approver_role:
                        pending.append(request)

        return pending

    def get_approval_status(self, process_id: str) -> dict[str, Any]:
        """Get approval status for a process.

        Args:
            process_id: Process instance ID.

        Returns:
            Dictionary with approval status information.
        """
        chain = self.approval_chains.get(process_id)
        history = self.approval_history.get(process_id, [])
        active = self.active_requests.get(process_id, [])

        return {
            "process_id": process_id,
            "total_steps": len(chain.steps) if chain else 0,
            "current_step": chain.current_step_index if chain else -1,
            "is_complete": chain.is_complete() if chain else False,
            "decisions_count": len(history),
            "pending_requests": len(active),
            "history": [
                {
                    "step": d.step_index,
                    "approver": d.approver,
                    "decision": d.decision.value,
                    "timestamp": d.timestamp.isoformat(),
                    "comments": d.comments,
                }
                for d in history
            ],
        }
