#!/usr/bin/env python3
"""Simple Procure-to-Pay Demo.

This demo shows a basic P2P workflow with:
- Purchase requisition creation
- Budget validation
- Approval routing based on amount
- State transitions
- Audit trail

This is a simplified demo focusing on the BPM framework capabilities.
"""

import asyncio
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from bpm import (
    StateMachine,
    StateDefinition,
    TransitionDefinition,
    ApprovalChain,
    ApprovalStep,
    RulesEngine,
    SLADefinition,
)
from bpm.bpm_orchestrator import BPMOrchestrator, ProcessDefinition
from p2p_workers import FORM_VALIDATOR, BUDGET_VALIDATOR, APPROVAL_ROUTER
from p2p_rules import create_approval_rules


def create_simple_p2p_workflow() -> ProcessDefinition:
    """Create a simplified P2P workflow.

    States:
    - draft: Initial requisition entry
    - submitted: Requisition submitted for validation
    - budget_check: Checking budget availability
    - pending_approval: Waiting for approvals
    - approved: Fully approved
    - rejected: Rejected at any stage

    Returns:
        Process definition for simple P2P workflow.
    """
    # Create state machine
    machine = StateMachine()

    # Add states
    machine.add_state(StateDefinition(
        name="draft",
        description="Draft requisition",
        is_terminal=False,
    ))

    machine.add_state(StateDefinition(
        name="submitted",
        description="Submitted for validation",
        is_terminal=False,
    ))

    machine.add_state(StateDefinition(
        name="budget_check",
        description="Budget validation in progress",
        is_terminal=False,
    ))

    machine.add_state(StateDefinition(
        name="pending_approval",
        description="Awaiting approvals",
        is_terminal=False,
    ))

    machine.add_state(StateDefinition(
        name="approved",
        description="Fully approved",
        is_terminal=True,
    ))

    machine.add_state(StateDefinition(
        name="rejected",
        description="Rejected",
        is_terminal=True,
    ))

    # Add transitions
    machine.add_transition(TransitionDefinition(
        from_state="draft",
        to_state="submitted",
        name="submit",
    ))

    machine.add_transition(TransitionDefinition(
        from_state="submitted",
        to_state="budget_check",
        name="validate",
    ))

    machine.add_transition(TransitionDefinition(
        from_state="budget_check",
        to_state="pending_approval",
        name="budget_approved",
    ))

    machine.add_transition(TransitionDefinition(
        from_state="budget_check",
        to_state="rejected",
        name="budget_rejected",
    ))

    machine.add_transition(TransitionDefinition(
        from_state="pending_approval",
        to_state="approved",
        name="approve",
    ))

    machine.add_transition(TransitionDefinition(
        from_state="pending_approval",
        to_state="rejected",
        name="reject",
    ))

    # Create rules engine with approval rules
    rules_engine = RulesEngine()
    for rule in create_approval_rules():
        rules_engine.add_rule(rule)

    # Create process definition
    process_def = ProcessDefinition(
        name="simple_p2p",
        description="Simplified Procure-to-Pay workflow",
        state_machine=machine,
        workers=[FORM_VALIDATOR, BUDGET_VALIDATOR, APPROVAL_ROUTER],
        initial_state="draft",
        rules_engine=rules_engine,
    )

    return process_def


async def run_demo():
    """Run the simple P2P demo."""
    print("=" * 80)
    print("Simple Procure-to-Pay Workflow Demo")
    print("=" * 80)
    print()

    # Create workflow definition
    print("Creating P2P workflow definition...")
    process_def = create_simple_p2p_workflow()
    print(f"✓ Workflow created with {len(process_def.state_machine.states)} states")
    print()

    # Create BPM orchestrator
    print("Initializing BPM orchestrator...")
    orchestrator = BPMOrchestrator(
        process_definition=process_def,
        model="openai:gpt-4o-mini",
    )

    # Set up SLA definitions
    orchestrator.sla_tracker.add_sla_definition(
        SLADefinition(state_name="pending_approval", target_hours=24)
    )
    print("✓ BPM orchestrator ready")
    print()

    # ==================================================================
    # SCENARIO 1: Small Purchase ($750) - Simple Approval
    # ==================================================================
    print("SCENARIO 1: Small Purchase Requisition")
    print("=" * 80)

    requisition_data = {
        "title": "Office Supplies - Standing Desks",
        "description": "Two adjustable standing desks for engineering team",
        "category": "Office Furniture",
        "quantity": 2,
        "estimated_unit_cost": 375.00,
        "amount": 750.00,
        "requester": "john.doe@company.com",
        "department": "Engineering",
        "cost_center": "ENG-2024",
        "budget_balance": 50000.00,  # Plenty of budget available
        "business_justification": "Ergonomic workstations to reduce back strain",
    }

    print("Requisition Details:")
    print(f"  Item: {requisition_data['title']}")
    print(f"  Amount: ${requisition_data['amount']:,.2f}")
    print(f"  Requester: {requisition_data['requester']}")
    print()

    # Start process
    print("Step 1: Creating requisition...")
    process = await orchestrator.start_process(
        process_type="purchase_requisition",
        initial_data=requisition_data,
        created_by=requisition_data["requester"],
    )
    print(f"✓ Process created: {process.process_id}")
    print(f"✓ Initial state: {process.state.state_name}")
    print()

    # Submit requisition
    print("Step 2: Submitting requisition...")
    success, msg = await orchestrator.transition_state(
        process_id=process.process_id,
        to_state="submitted",
        actor=requisition_data["requester"],
        reason="Ready for review",
    )
    print(f"✓ {msg}")
    print()

    # Budget validation
    print("Step 3: Budget validation...")
    success, msg = await orchestrator.transition_state(
        process_id=process.process_id,
        to_state="budget_check",
        actor="SYSTEM",
        reason="Initiating budget check",
    )
    print(f"✓ {msg}")

    # Simulate budget check (in real scenario, this would call the budget-validator worker)
    print("  Checking budget availability...")
    print(f"  Budget balance: ${requisition_data['budget_balance']:,.2f}")
    print(f"  Requested amount: ${requisition_data['amount']:,.2f}")
    print(f"  Remaining after: ${requisition_data['budget_balance'] - requisition_data['amount']:,.2f}")
    print("  Result: APPROVED ✓")
    print()

    success, msg = await orchestrator.transition_state(
        process_id=process.process_id,
        to_state="pending_approval",
        actor="SYSTEM",
        reason="Budget check passed",
    )
    print(f"✓ {msg}")
    print()

    # Determine approval chain using business rules
    print("Step 4: Determining approval chain...")
    context = {"amount": requisition_data["amount"], "category": requisition_data["category"]}
    rule_result = orchestrator.rules_engine.evaluate(context)

    if rule_result:
        print(f"✓ Matched rule: {rule_result.rule_name}")
        approval_chain = ApprovalChain(steps=rule_result.action_value)
        print(f"✓ Approval chain: {len(approval_chain.steps)} step(s)")
        for i, step in enumerate(approval_chain.steps, 1):
            print(f"  {i}. {step.approver_role} ({step.sla_hours}hr SLA)")
    print()

    # Request approval
    print("Step 5: Requesting approvals...")
    await orchestrator.request_approval(
        process_id=process.process_id,
        approval_chain=approval_chain,
        context=context,
    )
    print("✓ Approval request created")
    print()

    # Manager approval
    print("Step 6: Manager approval...")
    success, msg = await orchestrator.approve(
        process_id=process.process_id,
        approver="manager@company.com",
        comments="Approved. Desks needed for new hires.",
        context=context,
    )
    print(f"✓ {msg}")
    print()

    # Check if all approvals complete
    approval_status = orchestrator.approval_engine.get_approval_status(process.process_id)
    if approval_status["is_complete"]:
        print("All approvals complete! Finalizing...")
        success, msg = await orchestrator.transition_state(
            process_id=process.process_id,
            to_state="approved",
            actor="SYSTEM",
            reason="All approvals obtained",
        )
        print(f"✓ {msg}")
        print()

    # ==================================================================
    # SHOW PROCESS STATUS
    # ==================================================================
    print("=" * 80)
    print("Process Status")
    print("=" * 80)
    status = orchestrator.get_process_status(process.process_id)
    print(f"Process ID: {status['process_id']}")
    print(f"Current State: {status['current_state']}")
    print(f"Created: {status['created_at']}")
    print(f"Is Complete: {status['is_complete']}")
    print()

    print("State History:")
    for i, transition in enumerate(status['state_history'], 1):
        print(f"  {i}. {transition['from_state']} → {transition['to_state']}")
        print(f"     Actor: {transition['actor']}")
        print(f"     Time: {transition['timestamp']}")
    print()

    print("Approval History:")
    for i, decision in enumerate(status['approval']['history'], 1):
        print(f"  {i}. {decision['approver']}: {decision['decision']}")
        print(f"     Comments: {decision['comments']}")
        print(f"     Time: {decision['timestamp']}")
    print()

    # ==================================================================
    # SHOW AUDIT TRAIL
    # ==================================================================
    print("=" * 80)
    print("Audit Trail")
    print("=" * 80)
    audit_events = orchestrator.get_audit_trail(process.process_id)
    print(f"Total audit events: {len(audit_events)}")
    print()

    for i, event in enumerate(audit_events[:10], 1):  # Show first 10
        print(f"{i}. [{event['event_type']}] {event['action']}")
        print(f"   Actor: {event['actor']}")
        print(f"   Time: {event['timestamp']}")
        if event['details']:
            print(f"   Details: {event['details']}")
        print()

    # ==================================================================
    # SHOW COMPLIANCE REPORT
    # ==================================================================
    print("=" * 80)
    print("Compliance Report")
    print("=" * 80)
    compliance = orchestrator.generate_compliance_report(process.process_id)
    print(f"Process: {compliance['process_id']}")
    print()

    print("Audit Summary:")
    for key, value in compliance['audit_summary'].items():
        print(f"  {key}: {value}")
    print()

    print("Compliance Checks:")
    for key, value in compliance['compliance_checks'].items():
        status = "✓" if value else "✗"
        print(f"  {status} {key}: {value}")
    print()

    # ==================================================================
    # SHOW METRICS
    # ==================================================================
    print("=" * 80)
    print("BPM Metrics")
    print("=" * 80)
    metrics = orchestrator.get_bpm_metrics()

    print("Processes:")
    print(f"  Active: {metrics['processes']['total_active']}")
    print(f"  State distribution: {metrics['processes']['state_distribution']}")
    print()

    print("SLA Performance:")
    print(f"  Active SLAs: {metrics['sla']['active_slas']}")
    print(f"  Violations: {metrics['sla']['total_violations']}")
    print(f"  Compliance: {metrics['sla']['compliance_rate']}%")
    print()

    print("Audit Statistics:")
    print(f"  Total events: {metrics['audit']['total_events']}")
    print(f"  Unique processes: {metrics['audit']['unique_processes']}")
    print(f"  Unique actors: {metrics['audit']['unique_actors']}")
    print()

    print("✓ Demo completed successfully!")
    print()


if __name__ == "__main__":
    asyncio.run(run_demo())
