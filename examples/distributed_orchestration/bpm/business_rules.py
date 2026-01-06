"""Business Rules Engine for BPM Workflows.

This module provides a rules engine for encoding business logic
that determines routing, approvals, and process behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class RuleAction(Enum):
    """Type of action a rule can trigger."""

    ROUTE_TO_STATE = "route_to_state"
    ROUTE_TO_WORKER = "route_to_worker"
    SET_APPROVAL_CHAIN = "set_approval_chain"
    SET_VARIABLE = "set_variable"
    RAISE_EXCEPTION = "raise_exception"
    CUSTOM = "custom"


@dataclass
class BusinessRule:
    """Defines a business rule.

    A business rule consists of:
    - A condition that evaluates to True/False
    - An action to take when the condition is True
    - A priority for rule ordering
    """

    name: str
    description: str
    condition: Callable[[dict[str, Any]], bool]
    action_type: RuleAction
    action_value: Any
    priority: int = 100  # Lower number = higher priority
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuleEvaluationResult:
    """Result of evaluating a rule."""

    rule_name: str
    matched: bool
    action_type: RuleAction | None = None
    action_value: Any = None
    error: str | None = None


class RulesEngine:
    """Business rules engine for process workflow logic.

    The rules engine evaluates business rules in priority order
    and returns the action from the first matching rule.

    Example:
        >>> engine = RulesEngine()
        >>> engine.add_rule(BusinessRule(
        ...     name="high_value_approval",
        ...     description="Route high-value requisitions to CFO",
        ...     condition=lambda ctx: ctx.get("amount", 0) > 50000,
        ...     action_type=RuleAction.SET_APPROVAL_CHAIN,
        ...     action_value=["manager", "finance", "cfo"],
        ...     priority=10,
        ... ))
        >>> result = engine.evaluate({"amount": 75000})
    """

    def __init__(self):
        """Initialize the rules engine."""
        self.rules: list[BusinessRule] = []

    def add_rule(self, rule: BusinessRule) -> None:
        """Add a business rule to the engine.

        Args:
            rule: Business rule to add.
        """
        self.rules.append(rule)
        # Keep rules sorted by priority
        self.rules.sort(key=lambda r: r.priority)

    def remove_rule(self, rule_name: str) -> bool:
        """Remove a rule by name.

        Args:
            rule_name: Name of rule to remove.

        Returns:
            True if rule was removed, False if not found.
        """
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                self.rules.pop(i)
                return True
        return False

    def enable_rule(self, rule_name: str) -> bool:
        """Enable a rule.

        Args:
            rule_name: Name of rule to enable.

        Returns:
            True if rule was found, False otherwise.
        """
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = True
                return True
        return False

    def disable_rule(self, rule_name: str) -> bool:
        """Disable a rule without removing it.

        Args:
            rule_name: Name of rule to disable.

        Returns:
            True if rule was found, False otherwise.
        """
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = False
                return True
        return False

    def evaluate(self, context: dict[str, Any]) -> RuleEvaluationResult | None:
        """Evaluate rules against context and return first match.

        Args:
            context: Context data for rule evaluation.

        Returns:
            Result of first matching rule, or None if no rules match.
        """
        for rule in self.rules:
            if not rule.enabled:
                continue

            try:
                if rule.condition(context):
                    return RuleEvaluationResult(
                        rule_name=rule.name,
                        matched=True,
                        action_type=rule.action_type,
                        action_value=rule.action_value,
                    )
            except Exception as e:
                return RuleEvaluationResult(
                    rule_name=rule.name,
                    matched=False,
                    error=f"Error evaluating rule: {e}",
                )

        return None

    def evaluate_all(self, context: dict[str, Any]) -> list[RuleEvaluationResult]:
        """Evaluate all rules and return all matches.

        Args:
            context: Context data for rule evaluation.

        Returns:
            List of all evaluation results (both matches and non-matches).
        """
        results = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            try:
                matched = rule.condition(context)
                results.append(
                    RuleEvaluationResult(
                        rule_name=rule.name,
                        matched=matched,
                        action_type=rule.action_type if matched else None,
                        action_value=rule.action_value if matched else None,
                    )
                )
            except Exception as e:
                results.append(
                    RuleEvaluationResult(
                        rule_name=rule.name,
                        matched=False,
                        error=f"Error evaluating rule: {e}",
                    )
                )

        return results

    def get_rule(self, rule_name: str) -> BusinessRule | None:
        """Get a rule by name.

        Args:
            rule_name: Name of the rule.

        Returns:
            Business rule or None if not found.
        """
        for rule in self.rules:
            if rule.name == rule_name:
                return rule
        return None

    def list_rules(self, enabled_only: bool = False) -> list[BusinessRule]:
        """List all rules.

        Args:
            enabled_only: If True, only return enabled rules.

        Returns:
            List of business rules.
        """
        if enabled_only:
            return [r for r in self.rules if r.enabled]
        return self.rules.copy()


# Pre-built rule conditions for common scenarios


def amount_greater_than(threshold: float) -> Callable[[dict[str, Any]], bool]:
    """Create a condition that checks if amount exceeds threshold.

    Args:
        threshold: Amount threshold.

    Returns:
        Condition function.
    """
    return lambda ctx: ctx.get("amount", 0) > threshold


def amount_between(min_val: float, max_val: float) -> Callable[[dict[str, Any]], bool]:
    """Create a condition that checks if amount is in range.

    Args:
        min_val: Minimum value (inclusive).
        max_val: Maximum value (inclusive).

    Returns:
        Condition function.
    """
    return lambda ctx: min_val <= ctx.get("amount", 0) <= max_val


def category_equals(category: str) -> Callable[[dict[str, Any]], bool]:
    """Create a condition that checks if category matches.

    Args:
        category: Category value to match.

    Returns:
        Condition function.
    """
    return lambda ctx: ctx.get("category") == category


def any_of(*conditions: Callable[[dict[str, Any]], bool]) -> Callable[[dict[str, Any]], bool]:
    """Create a condition that is True if any sub-condition is True.

    Args:
        *conditions: Conditions to OR together.

    Returns:
        Combined condition function.
    """
    return lambda ctx: any(cond(ctx) for cond in conditions)


def all_of(*conditions: Callable[[dict[str, Any]], bool]) -> Callable[[dict[str, Any]], bool]:
    """Create a condition that is True if all sub-conditions are True.

    Args:
        *conditions: Conditions to AND together.

    Returns:
        Combined condition function.
    """
    return lambda ctx: all(cond(ctx) for cond in conditions)


def not_condition(condition: Callable[[dict[str, Any]], bool]) -> Callable[[dict[str, Any]], bool]:
    """Create a condition that negates another condition.

    Args:
        condition: Condition to negate.

    Returns:
        Negated condition function.
    """
    return lambda ctx: not condition(ctx)
