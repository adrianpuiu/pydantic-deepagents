#!/usr/bin/env python3
"""Custom worker configuration demo.

This example demonstrates:
- Creating custom specialized workers
- Using worker groups for specific domains
- Customizing worker instructions
- Domain-specific orchestration
"""

import asyncio

from orchestrator import DistributedOrchestrator
from pydantic_deep.types import SubAgentConfig


async def main():
    print("=" * 70)
    print("Custom Worker Configuration Demo")
    print("=" * 70)
    print()

    # Scenario 1: E-commerce Development Team
    print("Scenario 1: E-commerce Development Team")
    print("-" * 70)
    print()

    # Define specialized workers for e-commerce
    ecommerce_workers = [
        SubAgentConfig(
            name="product-catalog-specialist",
            description="Specializes in product catalog and inventory management",
            instructions="""You are an e-commerce product catalog expert.

Your expertise:
- Product data modeling and schema design
- Search and filtering optimization
- Category and taxonomy management
- Inventory tracking systems
- Product recommendations

Focus on scalability and user experience.""",
        ),
        SubAgentConfig(
            name="payment-integration-specialist",
            description="Handles payment processing and financial transactions",
            instructions="""You are a payment integration expert.

Your expertise:
- Payment gateway integration (Stripe, PayPal, etc.)
- PCI compliance and security
- Transaction handling and validation
- Refund and dispute management
- Multi-currency support

Always prioritize security and compliance.""",
        ),
        SubAgentConfig(
            name="order-management-specialist",
            description="Manages order processing and fulfillment",
            instructions="""You are an order management expert.

Your expertise:
- Order processing workflows
- Fulfillment automation
- Shipping integration
- Order tracking and notifications
- Returns and exchanges

Focus on reliability and customer experience.""",
        ),
    ]

    print("Creating e-commerce orchestrator with custom workers...")
    ecommerce_orchestrator = DistributedOrchestrator(
        model="openai:gpt-4o-mini",
        custom_workers=ecommerce_workers,
    )

    print(f"✓ {ecommerce_orchestrator}")
    print(
        f"✓ Specialized workers: {', '.join(w['name'] for w in ecommerce_workers)}"
    )
    print()

    # Use the e-commerce orchestrator
    ecommerce_task = """
Design a complete e-commerce checkout flow including:
1. Cart management
2. Payment processing with Stripe
3. Order creation and confirmation
4. Email notifications

Provide implementation guidance for each component.
"""

    result = await ecommerce_orchestrator.execute(ecommerce_task)
    print("E-commerce Checkout Design:")
    print(result)
    print()

    # Scenario 2: Data Science Team
    print("Scenario 2: Data Science Team")
    print("-" * 70)
    print()

    # Define specialized workers for data science
    data_science_workers = [
        SubAgentConfig(
            name="ml-engineer",
            description="Builds and trains machine learning models",
            instructions="""You are a machine learning engineer.

Your expertise:
- Model selection and architecture design
- Feature engineering
- Model training and validation
- Hyperparameter tuning
- Model deployment

Use scikit-learn, TensorFlow, or PyTorch as appropriate.""",
        ),
        SubAgentConfig(
            name="data-engineer",
            description="Designs and builds data pipelines",
            instructions="""You are a data engineer.

Your expertise:
- ETL pipeline design
- Data warehousing
- Stream processing
- Data quality validation
- Pipeline orchestration (Airflow, Prefect)

Focus on scalability and reliability.""",
        ),
        SubAgentConfig(
            name="visualization-specialist",
            description="Creates data visualizations and dashboards",
            instructions="""You are a data visualization expert.

Your expertise:
- Interactive visualizations
- Dashboard design
- Chart type selection
- Color theory and accessibility
- Tools: Plotly, Matplotlib, Seaborn

Make data insights accessible and actionable.""",
        ),
    ]

    print("Creating data science orchestrator...")
    ds_orchestrator = DistributedOrchestrator(
        model="openai:gpt-4o-mini",
        custom_workers=data_science_workers,
    )

    print(f"✓ {ds_orchestrator}")
    print(
        f"✓ Specialized workers: {', '.join(w['name'] for w in data_science_workers)}"
    )
    print()

    # Use the data science orchestrator
    ds_task = """
Build a customer churn prediction system including:
1. Data pipeline to collect and process customer data
2. Machine learning model to predict churn
3. Interactive dashboard to visualize predictions

Provide architecture and implementation details.
"""

    result = await ds_orchestrator.execute(ds_task)
    print("Churn Prediction System Design:")
    print(result)
    print()

    # Scenario 3: DevOps Team
    print("Scenario 3: DevOps and Infrastructure Team")
    print("-" * 70)
    print()

    devops_workers = [
        SubAgentConfig(
            name="kubernetes-specialist",
            description="Expert in Kubernetes orchestration and deployment",
            instructions="""You are a Kubernetes expert.

Your expertise:
- Deployment configurations
- Service mesh setup
- Autoscaling strategies
- Security policies
- Monitoring and logging

Focus on reliability and security.""",
        ),
        SubAgentConfig(
            name="terraform-specialist",
            description="Infrastructure as Code expert using Terraform",
            instructions="""You are a Terraform expert.

Your expertise:
- Infrastructure provisioning
- Module design
- State management
- Cloud provider integration (AWS, GCP, Azure)
- Best practices and patterns

Write reusable, maintainable infrastructure code.""",
        ),
        SubAgentConfig(
            name="cicd-specialist",
            description="CI/CD pipeline design and optimization",
            instructions="""You are a CI/CD expert.

Your expertise:
- Pipeline design (GitHub Actions, GitLab CI, Jenkins)
- Build optimization
- Testing automation
- Deployment strategies (blue-green, canary)
- Security scanning integration

Optimize for speed and reliability.""",
        ),
    ]

    print("Creating DevOps orchestrator...")
    devops_orchestrator = DistributedOrchestrator(
        model="openai:gpt-4o-mini",
        custom_workers=devops_workers,
    )

    print(f"✓ {devops_orchestrator}")
    print(
        f"✓ Specialized workers: {', '.join(w['name'] for w in devops_workers)}"
    )
    print()

    # Use the DevOps orchestrator
    devops_task = """
Design a complete deployment pipeline for a microservices application:
1. Kubernetes deployment manifests
2. Terraform infrastructure code for cloud resources
3. GitHub Actions CI/CD pipeline

Include testing, security scanning, and monitoring.
"""

    result = await devops_orchestrator.execute(devops_task)
    print("Deployment Pipeline Design:")
    print(result)
    print()

    # Scenario 4: Dynamic Worker Addition
    print("Scenario 4: Dynamic Worker Management")
    print("-" * 70)
    print()

    print("Starting with basic orchestrator...")
    dynamic_orchestrator = DistributedOrchestrator(model="openai:gpt-4o-mini")
    print(f"Initial workers: {len(dynamic_orchestrator.worker_configs)}")
    print()

    # Add domain-specific workers as needed
    print("Adding mobile development specialist...")
    mobile_worker = SubAgentConfig(
        name="mobile-dev-specialist",
        description="Expert in iOS and Android mobile development",
        instructions="""You are a mobile development expert.

Your expertise:
- React Native and Flutter
- Native iOS (Swift) and Android (Kotlin)
- Mobile UI/UX best practices
- App store deployment
- Performance optimization

Focus on cross-platform solutions when possible.""",
    )

    dynamic_orchestrator.add_worker(mobile_worker)
    print(f"Updated workers: {len(dynamic_orchestrator.worker_configs)}")
    print()

    # Use the newly added worker
    mobile_task = """
Design a mobile app for the e-commerce platform with:
- Product browsing
- Cart management
- Checkout flow
- Order tracking

Use React Native for cross-platform development.
"""

    result = await dynamic_orchestrator.execute(mobile_task)
    print("Mobile App Design:")
    print(result)
    print()

    # Show final metrics
    print("=" * 70)
    print("Demo Metrics")
    print("=" * 70)
    print()

    all_orchestrators = [
        ("E-commerce", ecommerce_orchestrator),
        ("Data Science", ds_orchestrator),
        ("DevOps", devops_orchestrator),
        ("Dynamic", dynamic_orchestrator),
    ]

    for name, orch in all_orchestrators:
        metrics = orch.get_metrics()
        print(f"{name} Orchestrator:")
        print(f"  Tasks: {metrics['total_tasks']}")
        print(f"  Success rate: {metrics['success_rate']:.1%}")
        print(f"  Workers: {len(orch.worker_configs)}")
        print()

    print("✓ Custom workers demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
