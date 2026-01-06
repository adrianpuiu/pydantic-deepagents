"""BPM Framework for Distributed Orchestration.

This package provides Business Process Management capabilities including:
- State machine workflow engine
- Multi-level approval workflows
- Business rules engine
- SLA tracking and escalations
- Immutable audit trail for compliance
"""

from .approval_engine import (
    ApprovalChain,
    ApprovalDecision,
    ApprovalDecisionType,
    ApprovalEngine,
    ApprovalRequest,
    ApprovalStatus,
    ApprovalStep,
)
from .audit_trail import AuditEvent, AuditEventType, AuditTrail
from .business_rules import (
    BusinessRule,
    RuleAction,
    RuleEvaluationResult,
    RulesEngine,
    all_of,
    amount_between,
    amount_greater_than,
    any_of,
    category_equals,
    not_condition,
)
from .sla_tracker import (
    SLADefinition,
    SLAInstance,
    SLAStatus,
    SLATracker,
    SLAViolation,
)
from .state_machine import (
    ProcessState,
    StateDefinition,
    StateMachine,
    StateTransitionEvent,
    TransitionDefinition,
    TransitionResult,
)

__all__ = [
    # State Machine
    "StateMachine",
    "StateDefinition",
    "TransitionDefinition",
    "ProcessState",
    "StateTransitionEvent",
    "TransitionResult",
    # Approval Engine
    "ApprovalEngine",
    "ApprovalChain",
    "ApprovalStep",
    "ApprovalRequest",
    "ApprovalDecision",
    "ApprovalDecisionType",
    "ApprovalStatus",
    # Business Rules
    "RulesEngine",
    "BusinessRule",
    "RuleAction",
    "RuleEvaluationResult",
    "amount_greater_than",
    "amount_between",
    "category_equals",
    "any_of",
    "all_of",
    "not_condition",
    # SLA Tracker
    "SLATracker",
    "SLADefinition",
    "SLAInstance",
    "SLAStatus",
    "SLAViolation",
    # Audit Trail
    "AuditTrail",
    "AuditEvent",
    "AuditEventType",
]
