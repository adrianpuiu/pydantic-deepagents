#!/usr/bin/env python3
"""BPM Diagram Generation Demo using Natural Language.

This demo shows how to:
1. Define a process using state machines
2. Generate natural language descriptions
3. Generate BPMN diagrams using ProcessPiper syntax
4. Export diagrams to PNG/SVG/BPMN formats

Requirements:
    pip install processpiper
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bpm import (
    StateMachine,
    StateDefinition,
    TransitionDefinition,
    DiagramGenerator,
    render_diagram,
)


def example_1_simple_approval_workflow():
    """Example 1: Simple approval workflow with natural language generation."""
    print("=" * 80)
    print("Example 1: Simple Approval Workflow")
    print("=" * 80)
    print()

    # Step 1: Define the process using state machine
    print("Step 1: Defining process with state machine...")
    machine = StateMachine()

    # Add states
    machine.add_state(StateDefinition(
        name="draft",
        description="Draft Requisition",
    ))

    machine.add_state(StateDefinition(
        name="submitted",
        description="Submitted for Review",
    ))

    machine.add_state(StateDefinition(
        name="approved",
        description="Approved",
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
        to_state="approved",
        name="approve",
    ))

    machine.add_transition(TransitionDefinition(
        from_state="submitted",
        to_state="rejected",
        name="reject",
    ))

    print("✓ State machine defined with 4 states and 3 transitions")
    print()

    # Step 2: Generate natural language description
    print("Step 2: Generating natural language description...")
    print("-" * 80)

    generator = DiagramGenerator(colour_theme="GREENTURTLE")
    description = generator.generate_natural_language_description(machine)

    print(description)
    print()

    # Step 3: Generate ProcessPiper syntax
    print("Step 3: Generating ProcessPiper PiperFlow syntax...")
    print("-" * 80)

    piperflow_syntax = generator.generate_piperflow(
        state_machine=machine,
        process_title="Simple Approval Workflow",
        lane_name="Approval Process",
    )

    print(piperflow_syntax)
    print()

    # Step 4: Render diagram
    print("Step 4: Rendering BPMN diagram...")

    try:
        gen_code, img = render_diagram(
            piperflow_syntax,
            output_file="simple_approval_workflow.png",
            export_bpmn=True,
        )
        print("✓ Diagram generated: simple_approval_workflow.png")
        print("✓ BPMN XML exported: simple_approval_workflow.bpmn")
    except Exception as e:
        print(f"Note: Install processpiper to generate diagrams: pip install processpiper")
        print(f"Syntax generated above can be used with ProcessPiper")

    print()
    print("=" * 80)
    print()


def example_2_procure_to_pay_workflow():
    """Example 2: Procure-to-Pay workflow with pools and lanes."""
    print("=" * 80)
    print("Example 2: Procure-to-Pay Workflow with Pools & Lanes")
    print("=" * 80)
    print()

    # Define P2P state machine
    print("Step 1: Defining Procure-to-Pay process...")
    machine = StateMachine()

    # Requisition phase
    machine.add_state(StateDefinition(name="draft", description="Draft Requisition"))
    machine.add_state(StateDefinition(name="submitted", description="Submitted"))
    machine.add_state(StateDefinition(name="budget_check", description="Budget Check?"))
    machine.add_state(StateDefinition(name="pending_approval", description="Pending Approval"))
    machine.add_state(StateDefinition(name="approved", description="Approved"))

    # Procurement phase
    machine.add_state(StateDefinition(name="po_created", description="PO Created"))
    machine.add_state(StateDefinition(name="vendor_selected", description="Vendor Selected"))
    machine.add_state(StateDefinition(name="goods_received", description="Goods Received"))

    # Invoice phase
    machine.add_state(StateDefinition(name="invoice_received", description="Invoice Received"))
    machine.add_state(StateDefinition(name="invoice_matched", description="Invoice Matched"))

    # Payment phase
    machine.add_state(StateDefinition(name="payment_scheduled", description="Payment Scheduled"))
    machine.add_state(StateDefinition(
        name="paid",
        description="Paid",
        is_terminal=True,
    ))

    # Exception paths
    machine.add_state(StateDefinition(
        name="rejected",
        description="Rejected",
        is_terminal=True,
    ))

    # Add transitions
    transitions = [
        ("draft", "submitted", "submit"),
        ("submitted", "budget_check", "validate"),
        ("budget_check", "pending_approval", "budget approved"),
        ("budget_check", "rejected", "budget exceeded"),
        ("pending_approval", "approved", "approve"),
        ("pending_approval", "rejected", "reject"),
        ("approved", "po_created", "generate PO"),
        ("po_created", "vendor_selected", "select vendor"),
        ("vendor_selected", "goods_received", "deliver"),
        ("goods_received", "invoice_received", "invoice arrives"),
        ("invoice_received", "invoice_matched", "3-way match"),
        ("invoice_matched", "payment_scheduled", "schedule"),
        ("payment_scheduled", "paid", "execute payment"),
    ]

    for from_state, to_state, name in transitions:
        machine.add_transition(TransitionDefinition(
            from_state=from_state,
            to_state=to_state,
            name=name,
        ))

    print("✓ P2P state machine defined with 13 states")
    print()

    # Generate natural language description
    print("Step 2: Natural Language Description")
    print("-" * 80)

    generator = DiagramGenerator(colour_theme="BLUEMOUNTAIN")
    description = generator.generate_natural_language_description(machine)

    print(description)
    print()

    # Generate diagram with pools and lanes
    print("Step 3: Generating diagram with pools and lanes...")
    print("-" * 80)

    pools_and_lanes = {
        "Procurement Department": [
            {
                "name": "Requester",
                "states": ["draft", "submitted"],
            },
            {
                "name": "Budget Office",
                "states": ["budget_check"],
            },
            {
                "name": "Approvers",
                "states": ["pending_approval", "approved", "rejected"],
            },
        ],
        "Purchasing": [
            {
                "name": "Procurement Team",
                "states": ["po_created", "vendor_selected"],
            },
            {
                "name": "Receiving",
                "states": ["goods_received"],
            },
        ],
        "Accounts Payable": [
            {
                "name": "AP Team",
                "states": ["invoice_received", "invoice_matched", "payment_scheduled", "paid"],
            },
        ],
    }

    piperflow_syntax = generator.generate_piperflow_with_pools(
        state_machine=machine,
        process_title="Procure-to-Pay Workflow",
        pools_and_lanes=pools_and_lanes,
        footer="Generated from BPM State Machine",
    )

    print(piperflow_syntax)
    print()

    # Render diagram
    print("Step 4: Rendering P2P diagram...")

    try:
        gen_code, img = render_diagram(
            piperflow_syntax,
            output_file="procure_to_pay_workflow.png",
            export_bpmn=True,
        )
        print("✓ Diagram generated: procure_to_pay_workflow.png")
        print("✓ BPMN XML exported: procure_to_pay_workflow.bpmn")
    except Exception as e:
        print(f"Note: Install processpiper to generate diagrams: pip install processpiper")

    print()
    print("=" * 80)
    print()


def example_3_custom_piperflow_syntax():
    """Example 3: Writing custom PiperFlow syntax directly."""
    print("=" * 80)
    print("Example 3: Custom PiperFlow Syntax (Natural Language)")
    print("=" * 80)
    print()

    # Write natural language PiperFlow syntax
    print("Writing process using natural language PiperFlow syntax...")
    print("-" * 80)

    piperflow_syntax = """
title: Purchase Order Approval Process
colourtheme: ORANGEPEEL

pool: Purchasing Department
    lane: Requester
        (start) as start
        [Create Requisition] as create_req
        [Enter Item Details] as enter_details
        (end) as end

    lane: Manager
        [Review Request] as review
        <Approve?> as approve_decision
        [Sign Approval] as sign

    lane: Finance
        [Check Budget] as check_budget
        <Budget Available?> as budget_decision

pool: Procurement System
    lane: Automated Workflow
        [@subprocess Generate PO] as generate_po
        (@message Send to Vendor) as send_vendor

start->create_req->enter_details->review->approve_decision
approve_decision->check_budget: Yes
approve_decision->end: No
check_budget->budget_decision
budget_decision->sign: Available
budget_decision->end: Not Available
sign->generate_po->send_vendor->end

footer: Created using Natural Language PiperFlow
"""

    print(piperflow_syntax)
    print()

    print("This natural language syntax describes:")
    print("  • 2 pools (Purchasing Department, Procurement System)")
    print("  • 4 lanes across the pools")
    print("  • Multiple element types:")
    print("    - (start) and (end) = Start/End events")
    print("    - [Task Name] = Activities/Tasks")
    print("    - <Question?> = Decision gateways")
    print("    - [@subprocess Name] = Subprocess")
    print("    - (@message Name) = Message event")
    print("  • Connections with labels (e.g., -> Yes, -> No)")
    print()

    # Render
    print("Rendering diagram...")
    try:
        gen_code, img = render_diagram(
            piperflow_syntax,
            output_file="custom_po_approval.png",
            export_bpmn=True,
        )
        print("✓ Diagram generated: custom_po_approval.png")
        print("✓ BPMN XML exported: custom_po_approval.bpmn")
    except Exception as e:
        print(f"Note: Install processpiper to generate diagrams: pip install processpiper")

    print()
    print("=" * 80)
    print()


def example_4_interactive_diagram_builder():
    """Example 4: Interactive natural language diagram builder."""
    print("=" * 80)
    print("Example 4: Building Diagrams Interactively with Natural Language")
    print("=" * 80)
    print()

    print("You can build BPMN diagrams interactively using simple English:")
    print()

    # Show step-by-step building
    print("Step 1: Start with a title and theme")
    print("-" * 40)
    print("title: My Process")
    print("colourtheme: PURPLERAIN")
    print()

    print("Step 2: Add a lane")
    print("-" * 40)
    print("lane: Customer Service")
    print()

    print("Step 3: Add start event")
    print("-" * 40)
    print("    (start) as start")
    print()

    print("Step 4: Add tasks")
    print("-" * 40)
    print("    [Receive Customer Request] as receive_request")
    print("    [Process Request] as process")
    print()

    print("Step 5: Add decision gateway")
    print("-" * 40)
    print("    <Is Urgent?> as is_urgent")
    print()

    print("Step 6: Add more tasks")
    print("-" * 40)
    print("    [Escalate to Manager] as escalate")
    print("    [Handle Normally] as handle_normal")
    print()

    print("Step 7: Add end event")
    print("-" * 40)
    print("    (end) as end")
    print()

    print("Step 8: Connect elements")
    print("-" * 40)
    print("    start->receive_request->process->is_urgent")
    print("    is_urgent->escalate: Yes")
    print("    is_urgent->handle_normal: No")
    print("    escalate->end")
    print("    handle_normal->end")
    print()

    print("Step 9: Add footer")
    print("-" * 40)
    print("footer: Generated by ProcessPiper")
    print()

    # Build complete syntax
    complete_syntax = """
title: My Process
colourtheme: PURPLERAIN

lane: Customer Service
    (start) as start
    [Receive Customer Request] as receive_request
    [Process Request] as process
    <Is Urgent?> as is_urgent
    [Escalate to Manager] as escalate
    [Handle Normally] as handle_normal
    (end) as end

start->receive_request->process->is_urgent
is_urgent->escalate: Yes
is_urgent->handle_normal: No
escalate->end
handle_normal->end

footer: Generated by ProcessPiper
"""

    print()
    print("Complete PiperFlow syntax:")
    print("=" * 80)
    print(complete_syntax)
    print("=" * 80)
    print()

    try:
        gen_code, img = render_diagram(
            complete_syntax,
            output_file="interactive_example.png",
        )
        print("✓ Diagram generated: interactive_example.png")
    except Exception as e:
        print(f"Note: Install processpiper to generate diagrams: pip install processpiper")

    print()
    print("=" * 80)
    print()


def main():
    """Run all examples."""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "BPM DIAGRAM GENERATION WITH NATURAL LANGUAGE" + " " * 19 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    print("This demo shows how to generate BPMN diagrams using natural language.")
    print()
    print("Available examples:")
    print("  1. Simple approval workflow (state machine → diagram)")
    print("  2. Procure-to-Pay workflow with pools & lanes")
    print("  3. Custom PiperFlow syntax (pure natural language)")
    print("  4. Interactive diagram building")
    print()

    # Run all examples
    example_1_simple_approval_workflow()
    example_2_procure_to_pay_workflow()
    example_3_custom_piperflow_syntax()
    example_4_interactive_diagram_builder()

    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 30 + "DEMO COMPLETE!" + " " * 33 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    print("Key Takeaways:")
    print("  ✓ Generate diagrams from state machines automatically")
    print("  ✓ Write natural language PiperFlow syntax")
    print("  ✓ Support multiple pools and lanes")
    print("  ✓ Export to PNG, SVG, and BPMN XML formats")
    print("  ✓ Build diagrams interactively with simple English")
    print()

    print("Next Steps:")
    print("  • Install ProcessPiper: pip install processpiper")
    print("  • Try modifying the examples above")
    print("  • Generate diagrams for your own processes")
    print("  • Use different colour themes: GREENTURTLE, BLUEMOUNTAIN, ORANGEPEEL, etc.")
    print()


if __name__ == "__main__":
    main()
