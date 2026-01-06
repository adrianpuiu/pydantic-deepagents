"""Procure-to-Pay Business Rules.

This module defines business rules for approval routing, budget validation,
policy compliance, and other P2P decision logic.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from bpm.business_rules import (
    BusinessRule,
    RuleAction,
    amount_between,
    amount_greater_than,
    all_of,
    any_of,
    category_equals,
)
from bpm.approval_engine import ApprovalStep


# ============================================================================
# APPROVAL ROUTING RULES
# ============================================================================

def create_approval_rules() -> list[BusinessRule]:
    """Create approval routing business rules.

    Returns:
        List of approval routing rules.
    """
    return [
        # Small purchases - manager only
        BusinessRule(
            name="small_purchase_approval",
            description="Purchases under $1,000 require only manager approval",
            condition=lambda ctx: ctx.get("amount", 0) < 1000,
            action_type=RuleAction.SET_APPROVAL_CHAIN,
            action_value=[
                ApprovalStep(
                    approver_role="manager",
                    description="Manager approval",
                    sla_hours=24,
                ),
            ],
            priority=10,
        ),

        # Medium purchases - manager + department head
        BusinessRule(
            name="medium_purchase_approval",
            description="Purchases $1K-$10K require manager and department head",
            condition=amount_between(1000, 9999.99),
            action_type=RuleAction.SET_APPROVAL_CHAIN,
            action_value=[
                ApprovalStep(
                    approver_role="manager",
                    description="Manager approval",
                    sla_hours=24,
                ),
                ApprovalStep(
                    approver_role="department_head",
                    description="Department head approval",
                    sla_hours=24,
                ),
            ],
            priority=20,
        ),

        # Large purchases - manager + dept head + finance
        BusinessRule(
            name="large_purchase_approval",
            description="Purchases $10K-$50K require manager, dept head, and finance",
            condition=amount_between(10000, 49999.99),
            action_type=RuleAction.SET_APPROVAL_CHAIN,
            action_value=[
                ApprovalStep(
                    approver_role="manager",
                    description="Manager approval",
                    sla_hours=24,
                ),
                ApprovalStep(
                    approver_role="department_head",
                    description="Department head approval",
                    sla_hours=24,
                ),
                ApprovalStep(
                    approver_role="finance_director",
                    description="Finance director approval",
                    sla_hours=24,
                ),
            ],
            priority=30,
        ),

        # Very large purchases - full chain including CFO
        BusinessRule(
            name="xlarge_purchase_approval",
            description="Purchases over $50K require full approval chain including CFO",
            condition=amount_greater_than(50000),
            action_type=RuleAction.SET_APPROVAL_CHAIN,
            action_value=[
                ApprovalStep(
                    approver_role="manager",
                    description="Manager approval",
                    sla_hours=24,
                ),
                ApprovalStep(
                    approver_role="department_head",
                    description="Department head approval",
                    sla_hours=24,
                ),
                ApprovalStep(
                    approver_role="finance_director",
                    description="Finance director approval",
                    sla_hours=24,
                ),
                ApprovalStep(
                    approver_role="cfo",
                    description="CFO approval",
                    sla_hours=48,
                ),
            ],
            priority=40,
        ),

        # IT purchases over $5K require CTO approval
        BusinessRule(
            name="it_purchase_cto_approval",
            description="IT purchases over $5K require CTO approval",
            condition=all_of(
                category_equals("IT"),
                amount_greater_than(5000),
            ),
            action_type=RuleAction.SET_APPROVAL_CHAIN,
            action_value=[
                ApprovalStep(
                    approver_role="manager",
                    description="Manager approval",
                    sla_hours=24,
                ),
                ApprovalStep(
                    approver_role="cto",
                    description="CTO approval for IT purchase",
                    sla_hours=48,
                ),
            ],
            priority=5,  # Higher priority than amount-based rules
        ),

        # Legal services require General Counsel approval
        BusinessRule(
            name="legal_services_approval",
            description="Legal services require General Counsel approval",
            condition=category_equals("Legal"),
            action_type=RuleAction.SET_APPROVAL_CHAIN,
            action_value=[
                ApprovalStep(
                    approver_role="manager",
                    description="Manager approval",
                    sla_hours=24,
                ),
                ApprovalStep(
                    approver_role="general_counsel",
                    description="General Counsel approval",
                    sla_hours=48,
                ),
            ],
            priority=5,
        ),
    ]


# ============================================================================
# BUDGET VALIDATION RULES
# ============================================================================

def create_budget_rules() -> list[BusinessRule]:
    """Create budget validation rules.

    Returns:
        List of budget validation rules.
    """
    return [
        BusinessRule(
            name="budget_available",
            description="Approve if sufficient budget available",
            condition=lambda ctx: (
                ctx.get("budget_balance", 0) >= ctx.get("amount", 0)
            ),
            action_type=RuleAction.ROUTE_TO_STATE,
            action_value="budget_approved",
            priority=10,
        ),

        BusinessRule(
            name="budget_exceeded",
            description="Route to exception if budget exceeded",
            condition=lambda ctx: (
                ctx.get("budget_balance", 0) < ctx.get("amount", 0)
            ),
            action_type=RuleAction.RAISE_EXCEPTION,
            action_value="BUDGET_EXCEEDED",
            priority=20,
        ),
    ]


# ============================================================================
# POLICY COMPLIANCE RULES
# ============================================================================

def create_policy_rules() -> list[BusinessRule]:
    """Create policy compliance rules.

    Returns:
        List of policy compliance rules.
    """
    return [
        BusinessRule(
            name="preferred_vendor_required",
            description="Purchases over $5K must use preferred vendor",
            condition=all_of(
                amount_greater_than(5000),
                lambda ctx: not ctx.get("is_preferred_vendor", False),
            ),
            action_type=RuleAction.RAISE_EXCEPTION,
            action_value="NON_PREFERRED_VENDOR",
            priority=10,
        ),

        BusinessRule(
            name="competitive_bidding_required",
            description="Purchases over $10K require competitive bidding",
            condition=all_of(
                amount_greater_than(10000),
                lambda ctx: ctx.get("num_quotes", 0) < 3,
            ),
            action_type=RuleAction.RAISE_EXCEPTION,
            action_value="INSUFFICIENT_QUOTES",
            priority=10,
        ),

        BusinessRule(
            name="sole_source_justification",
            description="Single source purchases over $5K need justification",
            condition=all_of(
                amount_greater_than(5000),
                lambda ctx: ctx.get("num_vendors", 1) == 1,
                lambda ctx: not ctx.get("has_sole_source_justification", False),
            ),
            action_type=RuleAction.RAISE_EXCEPTION,
            action_value="MISSING_SOLE_SOURCE_JUSTIFICATION",
            priority=15,
        ),
    ]


# ============================================================================
# 3-WAY MATCHING RULES
# ============================================================================

def create_matching_rules() -> list[BusinessRule]:
    """Create invoice matching rules.

    Returns:
        List of matching rules.
    """
    return [
        # Perfect match
        BusinessRule(
            name="perfect_match",
            description="Invoice matches PO and receipt exactly",
            condition=lambda ctx: (
                ctx.get("quantity_variance_pct", 100) == 0
                and ctx.get("price_variance_pct", 100) == 0
            ),
            action_type=RuleAction.ROUTE_TO_STATE,
            action_value="matched",
            priority=10,
        ),

        # Within tolerance
        BusinessRule(
            name="tolerance_match",
            description="Variances within acceptable tolerance",
            condition=lambda ctx: (
                abs(ctx.get("quantity_variance_pct", 100)) <= 5
                and abs(ctx.get("price_variance_pct", 100)) <= 2
            ),
            action_type=RuleAction.ROUTE_TO_STATE,
            action_value="matched",
            priority=20,
        ),

        # Price mismatch
        BusinessRule(
            name="price_mismatch",
            description="Price variance exceeds tolerance",
            condition=lambda ctx: abs(ctx.get("price_variance_pct", 0)) > 2,
            action_type=RuleAction.RAISE_EXCEPTION,
            action_value="PRICE_MISMATCH",
            priority=30,
        ),

        # Quantity mismatch
        BusinessRule(
            name="quantity_mismatch",
            description="Quantity variance exceeds tolerance",
            condition=lambda ctx: abs(ctx.get("quantity_variance_pct", 0)) > 5,
            action_type=RuleAction.RAISE_EXCEPTION,
            action_value="QUANTITY_MISMATCH",
            priority=40,
        ),
    ]


# ============================================================================
# PAYMENT SCHEDULING RULES
# ============================================================================

def create_payment_rules() -> list[BusinessRule]:
    """Create payment scheduling rules.

    Returns:
        List of payment scheduling rules.
    """
    return [
        # Always take early payment discounts
        BusinessRule(
            name="take_early_payment_discount",
            description="Schedule payment to capture early payment discount",
            condition=lambda ctx: ctx.get("discount_available", False),
            action_type=RuleAction.CUSTOM,
            action_value="schedule_for_discount_date",
            priority=10,
        ),

        # Strategic vendors get priority
        BusinessRule(
            name="strategic_vendor_priority",
            description="Pay strategic vendors early to maintain relationship",
            condition=lambda ctx: ctx.get("is_strategic_vendor", False),
            action_type=RuleAction.CUSTOM,
            action_value="schedule_early",
            priority=20,
        ),

        # Standard payment timing
        BusinessRule(
            name="standard_payment_timing",
            description="Schedule 2-3 days before due date",
            condition=lambda ctx: True,  # Default rule
            action_type=RuleAction.CUSTOM,
            action_value="schedule_standard",
            priority=100,  # Lowest priority (default)
        ),
    ]


# ============================================================================
# AUTO-APPROVAL RULES
# ============================================================================

def create_auto_approval_conditions():
    """Create auto-approval condition functions.

    Returns:
        Dict mapping approval types to auto-approval conditions.
    """
    return {
        # Auto-approve small purchases from authorized buyers
        "small_purchase_auto": lambda ctx: (
            ctx.get("amount", 0) < 500
            and ctx.get("requester_authorized", False)
        ),

        # Auto-approve budget if significantly under limit
        "budget_auto": lambda ctx: (
            ctx.get("amount", 0) < ctx.get("budget_balance", 0) * 0.1
        ),

        # Auto-approve payment if perfectly matched
        "payment_auto": lambda ctx: (
            ctx.get("match_status") == "PERFECT_MATCH"
            and ctx.get("amount", 0) < 5000
        ),
    }
