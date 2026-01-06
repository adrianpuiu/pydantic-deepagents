"""State Machine Engine for BPM Workflows.

This module provides a flexible state machine implementation for managing
business process states and transitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class TransitionResult(Enum):
    """Result of a state transition attempt."""

    SUCCESS = "success"
    INVALID_TRANSITION = "invalid_transition"
    CONDITION_FAILED = "condition_failed"
    ERROR = "error"


@dataclass
class StateDefinition:
    """Defines a state in the process."""

    name: str
    description: str
    is_terminal: bool = False
    on_enter: Callable[[dict[str, Any]], None] | None = None
    on_exit: Callable[[dict[str, Any]], None] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TransitionDefinition:
    """Defines a valid state transition."""

    from_state: str
    to_state: str
    name: str
    condition: Callable[[dict[str, Any]], bool] | None = None
    action: Callable[[dict[str, Any]], dict[str, Any]] | None = None
    requires_approval: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessState:
    """Current state of a process instance."""

    state_name: str
    state_data: dict[str, Any] = field(default_factory=dict)
    entered_at: datetime = field(default_factory=datetime.now)
    history: list[StateTransitionEvent] = field(default_factory=list)


@dataclass
class StateTransitionEvent:
    """Records a state transition event."""

    from_state: str
    to_state: str
    transition_name: str
    timestamp: datetime
    actor: str | None = None
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class StateMachine:
    """State machine for managing process workflow states.

    The state machine enforces valid transitions, evaluates conditions,
    and executes actions during state changes.

    Example:
        >>> machine = StateMachine()
        >>> machine.add_state(StateDefinition(name="draft", description="Draft state"))
        >>> machine.add_transition(
        ...     TransitionDefinition(from_state="draft", to_state="submitted", name="submit")
        ... )
    """

    def __init__(self):
        """Initialize the state machine."""
        self.states: dict[str, StateDefinition] = {}
        self.transitions: list[TransitionDefinition] = []

    def add_state(self, state: StateDefinition) -> None:
        """Add a state definition to the machine.

        Args:
            state: State definition to add.
        """
        self.states[state.name] = state

    def add_transition(self, transition: TransitionDefinition) -> None:
        """Add a transition definition to the machine.

        Args:
            transition: Transition definition to add.

        Raises:
            ValueError: If from_state or to_state don't exist.
        """
        if transition.from_state not in self.states:
            raise ValueError(f"State '{transition.from_state}' does not exist")
        if transition.to_state not in self.states:
            raise ValueError(f"State '{transition.to_state}' does not exist")

        self.transitions.append(transition)

    def get_valid_transitions(self, from_state: str) -> list[TransitionDefinition]:
        """Get all valid transitions from a given state.

        Args:
            from_state: Current state name.

        Returns:
            List of valid transition definitions.
        """
        return [t for t in self.transitions if t.from_state == from_state]

    def can_transition(
        self, from_state: str, to_state: str, context: dict[str, Any] | None = None
    ) -> tuple[bool, str]:
        """Check if a transition is valid.

        Args:
            from_state: Current state.
            to_state: Target state.
            context: Optional context data for condition evaluation.

        Returns:
            Tuple of (is_valid, reason).
        """
        # Find matching transition
        matching_transitions = [
            t
            for t in self.transitions
            if t.from_state == from_state and t.to_state == to_state
        ]

        if not matching_transitions:
            return False, f"No transition defined from '{from_state}' to '{to_state}'"

        # Check condition if present
        transition = matching_transitions[0]
        if transition.condition:
            ctx = context or {}
            try:
                if not transition.condition(ctx):
                    return False, "Transition condition not satisfied"
            except Exception as e:
                return False, f"Error evaluating transition condition: {e}"

        return True, "Transition is valid"

    def transition(
        self,
        process_state: ProcessState,
        to_state: str,
        actor: str | None = None,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[TransitionResult, str]:
        """Execute a state transition.

        Args:
            process_state: Current process state (will be modified in-place).
            to_state: Target state name.
            actor: Optional actor performing the transition.
            reason: Optional reason for transition.
            metadata: Optional metadata for the transition.

        Returns:
            Tuple of (result, message).
        """
        current_state = process_state.state_name

        # Check if transition is valid
        is_valid, message = self.can_transition(
            current_state, to_state, process_state.state_data
        )
        if not is_valid:
            return TransitionResult.INVALID_TRANSITION, message

        # Find the transition
        transition = next(
            t
            for t in self.transitions
            if t.from_state == current_state and t.to_state == to_state
        )

        try:
            # Execute exit action for current state
            current_state_def = self.states[current_state]
            if current_state_def.on_exit:
                current_state_def.on_exit(process_state.state_data)

            # Execute transition action
            if transition.action:
                process_state.state_data = transition.action(process_state.state_data)

            # Record the transition event
            event = StateTransitionEvent(
                from_state=current_state,
                to_state=to_state,
                transition_name=transition.name,
                timestamp=datetime.now(),
                actor=actor,
                reason=reason,
                metadata=metadata or {},
            )
            process_state.history.append(event)

            # Update current state
            process_state.state_name = to_state
            process_state.entered_at = datetime.now()

            # Execute entry action for new state
            new_state_def = self.states[to_state]
            if new_state_def.on_enter:
                new_state_def.on_enter(process_state.state_data)

            return (
                TransitionResult.SUCCESS,
                f"Transitioned from '{current_state}' to '{to_state}'",
            )

        except Exception as e:
            return TransitionResult.ERROR, f"Error during transition: {e}"

    def is_terminal_state(self, state_name: str) -> bool:
        """Check if a state is terminal (process complete).

        Args:
            state_name: State name to check.

        Returns:
            True if state is terminal.
        """
        state = self.states.get(state_name)
        return state.is_terminal if state else False

    def get_state_definition(self, state_name: str) -> StateDefinition | None:
        """Get the definition for a state.

        Args:
            state_name: Name of the state.

        Returns:
            State definition or None if not found.
        """
        return self.states.get(state_name)

    def visualize(self) -> str:
        """Generate a text representation of the state machine.

        Returns:
            String representation showing states and transitions.
        """
        lines = ["State Machine Diagram", "=" * 50, ""]

        # List states
        lines.append("States:")
        for state in self.states.values():
            terminal = " [TERMINAL]" if state.is_terminal else ""
            lines.append(f"  - {state.name}: {state.description}{terminal}")

        lines.append("")
        lines.append("Transitions:")

        # List transitions
        for transition in self.transitions:
            approval = " [REQUIRES APPROVAL]" if transition.requires_approval else ""
            lines.append(
                f"  {transition.from_state} --[{transition.name}]--> {transition.to_state}{approval}"
            )

        return "\n".join(lines)
