#!/usr/bin/env python3
"""Real-World Example: Data Pipeline ETL Processing.

This example demonstrates a complete ETL (Extract, Transform, Load) pipeline
using distributed agent orchestration for processing multiple data sources,
transforming data, analyzing results, and generating reports.

Business Scenario:
A retail company needs to process sales data from multiple sources (CSV files,
APIs, databases), clean and transform the data, perform analytics, and generate
executive reports - all automated and running in parallel where possible.

Components:
1. Data Extraction - Parallel extraction from multiple sources
2. Data Validation - Quality checks and cleaning
3. Data Transformation - Normalization and enrichment
4. Analytics - Statistical analysis and insights
5. Report Generation - Executive dashboards and summaries
"""

import asyncio
from datetime import datetime

from pydantic_deep import StateBackend
from pydantic_deep.types import SubAgentConfig

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orchestrator import DistributedOrchestrator, TaskPriority


# Define specialized ETL workers
ETL_WORKERS = [
    SubAgentConfig(
        name="data-extractor",
        description="Extracts data from various sources (CSV, JSON, APIs)",
        instructions="""You are a data extraction specialist.

Your responsibilities:
1. Read data from multiple sources (files, APIs, databases)
2. Handle different data formats (CSV, JSON, XML, Parquet)
3. Implement retry logic for API calls
4. Log extraction metadata (rows, columns, source)
5. Handle pagination and rate limiting

Output format:
- Extracted data in standardized format
- Extraction metadata (source, timestamp, record count)
- Any errors or warnings encountered""",
    ),
    SubAgentConfig(
        name="data-validator",
        description="Validates and cleans data quality",
        instructions="""You are a data quality specialist.

Your responsibilities:
1. Validate data types and formats
2. Check for missing values and outliers
3. Detect duplicate records
4. Verify referential integrity
5. Flag data quality issues

Quality checks:
- Completeness (missing values)
- Accuracy (data type validation)
- Consistency (format standardization)
- Uniqueness (duplicate detection)

Output format:
- Validation report with pass/fail status
- List of data quality issues found
- Cleaned/corrected data
- Recommendations for data improvement""",
    ),
    SubAgentConfig(
        name="data-transformer",
        description="Transforms and enriches data",
        instructions="""You are a data transformation expert.

Your responsibilities:
1. Normalize data to standard formats
2. Apply business logic transformations
3. Aggregate and summarize data
4. Join data from multiple sources
5. Create derived columns and calculations

Transformations:
- Date/time standardization
- Currency conversion
- Unit normalization
- Categorical encoding
- Feature engineering

Output format:
- Transformed dataset
- Transformation log (operations applied)
- Data lineage information
- Summary statistics""",
    ),
    SubAgentConfig(
        name="analytics-engine",
        description="Performs statistical analysis and generates insights",
        instructions="""You are a data analytics expert.

Your responsibilities:
1. Perform descriptive statistics
2. Identify trends and patterns
3. Calculate KPIs and metrics
4. Detect anomalies
5. Generate actionable insights

Analysis types:
- Time series analysis
- Cohort analysis
- Segmentation analysis
- Correlation analysis
- Trend detection

Output format:
- Key metrics and KPIs
- Trend analysis with visualizations
- Anomalies and outliers
- Business insights and recommendations""",
    ),
    SubAgentConfig(
        name="report-generator",
        description="Creates executive reports and dashboards",
        instructions="""You are a business intelligence specialist.

Your responsibilities:
1. Create executive summaries
2. Generate visual dashboards (describe charts)
3. Write data-driven narratives
4. Highlight key insights
5. Provide actionable recommendations

Report sections:
- Executive Summary
- Key Performance Indicators
- Trend Analysis
- Insights and Findings
- Recommendations and Next Steps

Output format:
- Markdown formatted report
- Chart/visualization descriptions
- Clear, non-technical language
- Action items for stakeholders""",
    ),
]


async def main():
    print("=" * 80)
    print("Real-World Use Case: Data Pipeline ETL Processing")
    print("=" * 80)
    print()

    # Create orchestrator with ETL workers
    print("Initializing ETL Pipeline Orchestrator...")
    orchestrator = DistributedOrchestrator(
        model="openai:gpt-4o-mini",
        custom_workers=ETL_WORKERS,
        max_concurrent_workers=5,
    )
    print(f"✓ Orchestrator ready with {len(ETL_WORKERS)} specialized workers")
    print()

    # Simulate sample data sources
    print("Setting up sample data sources...")

    # Upload sample CSV data
    sales_data_q1 = """date,product_id,product_name,quantity,unit_price,customer_id,region
2024-01-15,P001,Laptop,2,999.99,C123,North
2024-01-16,P002,Mouse,5,29.99,C124,South
2024-01-17,P001,Laptop,1,999.99,C125,East
2024-01-18,P003,Keyboard,3,79.99,C123,North
2024-01-19,P002,Mouse,10,29.99,C126,West
2024-01-20,P004,Monitor,2,349.99,C127,South"""

    sales_data_q2 = """date,product_id,product_name,quantity,unit_price,customer_id,region
2024-04-15,P001,Laptop,3,999.99,C128,North
2024-04-16,P005,Tablet,4,599.99,C129,East
2024-04-17,P003,Keyboard,6,79.99,C130,South
2024-04-18,P002,Mouse,8,29.99,C131,West
2024-04-19,P004,Monitor,1,349.99,C132,North
2024-04-20,P001,Laptop,2,999.99,C133,East"""

    # Upload data to backend
    orchestrator.deps.backend.write("/data/sources/sales_q1.csv", sales_data_q1)
    orchestrator.deps.backend.write("/data/sources/sales_q2.csv", sales_data_q2)

    print("✓ Sample data sources created:")
    print("  - /data/sources/sales_q1.csv")
    print("  - /data/sources/sales_q2.csv")
    print()

    # ============================================================================
    # PHASE 1: DATA EXTRACTION (Parallel)
    # ============================================================================
    print("PHASE 1: Data Extraction")
    print("=" * 80)
    print("Extracting data from multiple sources in parallel...")
    print()

    extraction_tasks = [
        """Extract data from /data/sources/sales_q1.csv

        Parse the CSV file and provide:
        1. Total number of records
        2. Column names and data types
        3. Date range covered
        4. Any parsing errors or warnings

        Save extracted data to /data/extracted/sales_q1.json""",

        """Extract data from /data/sources/sales_q2.csv

        Parse the CSV file and provide:
        1. Total number of records
        2. Column names and data types
        3. Date range covered
        4. Any parsing errors or warnings

        Save extracted data to /data/extracted/sales_q2.json""",
    ]

    extraction_results = await orchestrator.execute_parallel(
        extraction_tasks,
        priority=TaskPriority.HIGH
    )

    print("✓ Data extraction completed")
    for i, result in enumerate(extraction_results, 1):
        print(f"\nSource {i} Extraction:")
        print(result[:300] + "..." if len(result) > 300 else result)
    print()

    # ============================================================================
    # PHASE 2: DATA VALIDATION (Parallel)
    # ============================================================================
    print("PHASE 2: Data Validation & Quality Checks")
    print("=" * 80)
    print("Validating data quality in parallel...")
    print()

    validation_tasks = [
        """Validate the extracted Q1 sales data:

        Check for:
        1. Missing values in critical columns (date, product_id, quantity, unit_price)
        2. Invalid data types (e.g., negative quantities or prices)
        3. Duplicate records
        4. Date format consistency
        5. Outliers in quantity or price

        Provide a validation report with pass/fail status and data quality score.""",

        """Validate the extracted Q2 sales data:

        Check for:
        1. Missing values in critical columns (date, product_id, quantity, unit_price)
        2. Invalid data types (e.g., negative quantities or prices)
        3. Duplicate records
        4. Date format consistency
        5. Outliers in quantity or price

        Provide a validation report with pass/fail status and data quality score.""",
    ]

    validation_results = await orchestrator.execute_parallel(validation_tasks)

    print("✓ Data validation completed")
    for i, result in enumerate(validation_results, 1):
        print(f"\nQ{i} Validation Report:")
        print(result[:300] + "..." if len(result) > 300 else result)
    print()

    # ============================================================================
    # PHASE 3: DATA TRANSFORMATION
    # ============================================================================
    print("PHASE 3: Data Transformation")
    print("=" * 80)
    print("Transforming and enriching data...")
    print()

    transformation_task = """Transform the combined Q1 and Q2 sales data:

    Transformations needed:
    1. Combine Q1 and Q2 datasets into a single dataset
    2. Calculate total_revenue (quantity * unit_price) for each record
    3. Standardize date format to YYYY-MM-DD
    4. Add quarter column (Q1, Q2)
    5. Add month column
    6. Create product_category based on product_name
    7. Calculate running totals by region

    Additional enrichment:
    - Add fiscal_year column
    - Calculate discount percentage (if applicable)
    - Add customer_segment based on purchase patterns

    Save transformed data to /data/transformed/sales_combined.json
    Provide transformation summary with record counts and new columns added."""

    transformation_result = await orchestrator.execute(
        transformation_task,
        priority=TaskPriority.HIGH
    )

    print("✓ Data transformation completed")
    print("\nTransformation Summary:")
    print(transformation_result[:400] + "..." if len(transformation_result) > 400 else transformation_result)
    print()

    # ============================================================================
    # PHASE 4: ANALYTICS (Parallel)
    # ============================================================================
    print("PHASE 4: Analytics & Insights Generation")
    print("=" * 80)
    print("Running analytics on transformed data...")
    print()

    analytics_tasks = [
        """Perform revenue analysis on the combined sales data:

        Analysis required:
        1. Total revenue by quarter (Q1 vs Q2)
        2. Revenue growth rate from Q1 to Q2
        3. Top 5 products by revenue
        4. Revenue by region
        5. Average order value
        6. Revenue trend over time

        Identify:
        - Best performing regions
        - Products with highest growth
        - Any concerning trends

        Provide insights and recommendations.""",

        """Perform customer analysis on the combined sales data:

        Analysis required:
        1. Total unique customers
        2. New customers in Q2 vs returning from Q1
        3. Customer retention rate
        4. Average purchases per customer
        5. Customer distribution by region
        6. High-value customers (top 20% by revenue)

        Identify:
        - Customer loyalty trends
        - Geographic customer concentration
        - Opportunities for customer growth

        Provide insights and recommendations.""",

        """Perform product analysis on the combined sales data:

        Analysis required:
        1. Total SKUs sold
        2. Best sellers by quantity
        3. Best sellers by revenue
        4. Product mix changes Q1 to Q2
        5. Average price points
        6. Inventory turnover indicators

        Identify:
        - Product portfolio health
        - Cross-selling opportunities
        - Slow-moving products

        Provide insights and recommendations.""",
    ]

    analytics_results = await orchestrator.execute_parallel(
        analytics_tasks,
        priority=TaskPriority.NORMAL
    )

    print("✓ Analytics completed")
    print("\nAnalytics Results:")
    for i, (title, result) in enumerate([
        ("Revenue Analysis", analytics_results[0]),
        ("Customer Analysis", analytics_results[1]),
        ("Product Analysis", analytics_results[2]),
    ], 1):
        print(f"\n{i}. {title}:")
        print(result[:350] + "..." if len(result) > 350 else result)
    print()

    # ============================================================================
    # PHASE 5: REPORT GENERATION
    # ============================================================================
    print("PHASE 5: Executive Report Generation")
    print("=" * 80)
    print("Generating executive report...")
    print()

    report_task = f"""Create an executive report for the sales data analysis.

    Input data:
    - Extraction summary: {len(extraction_results)} data sources processed
    - Validation: Data quality checks completed
    - Transformation: Combined Q1 and Q2 data
    - Analytics completed:
      * Revenue Analysis: {analytics_results[0][:200]}...
      * Customer Analysis: {analytics_results[1][:200]}...
      * Product Analysis: {analytics_results[2][:200]}...

    Report structure:
    1. Executive Summary
       - Key highlights and top-line metrics
       - Quarter-over-quarter performance

    2. Revenue Performance
       - Total revenue and growth
       - Revenue by region and product
       - Trends and patterns

    3. Customer Insights
       - Customer acquisition and retention
       - Customer segmentation
       - Regional distribution

    4. Product Performance
       - Top performers
       - Product mix analysis
       - Inventory insights

    5. Key Findings
       - Major trends identified
       - Areas of concern
       - Opportunities discovered

    6. Recommendations
       - Strategic recommendations
       - Tactical action items
       - Next steps

    Format: Professional markdown with clear sections and bullet points.
    Save report to /data/reports/executive_summary_{datetime.now().strftime("%Y%m%d")}.md"""

    report_result = await orchestrator.execute(
        report_task,
        priority=TaskPriority.URGENT
    )

    print("✓ Executive report generated")
    print("\n" + "=" * 80)
    print("EXECUTIVE REPORT")
    print("=" * 80)
    print(report_result)
    print()

    # ============================================================================
    # PIPELINE SUMMARY
    # ============================================================================
    print("=" * 80)
    print("ETL Pipeline Execution Summary")
    print("=" * 80)

    metrics = orchestrator.get_metrics()

    print(f"\nPipeline Statistics:")
    print(f"  Total tasks executed: {metrics['total_tasks']}")
    print(f"  Successfully completed: {metrics['completed_tasks']}")
    print(f"  Failed tasks: {metrics['failed_tasks']}")
    print(f"  Success rate: {metrics['success_rate']:.1%}")
    print()

    print("Worker Utilization:")
    for worker_name, stats in metrics['workers'].items():
        total = stats['tasks_completed'] + stats['tasks_failed']
        if total > 0:
            print(f"  {worker_name}: {stats['tasks_completed']} tasks completed")
    print()

    # Show task breakdown
    all_tasks = orchestrator.get_all_tasks()
    total_time = 0
    print("Task Execution Timeline:")
    for task_id, task in all_tasks.items():
        if task.started_at and task.completed_at:
            duration = (task.completed_at - task.started_at).total_seconds()
            total_time += duration
            print(f"  {task.id}:")
            print(f"    Priority: {task.priority.name}")
            print(f"    Status: {task.status.value}")
            print(f"    Duration: {duration:.2f}s")

    print(f"\nTotal pipeline execution time: {total_time:.2f}s")
    print()

    print("=" * 80)
    print("✓ ETL Pipeline completed successfully!")
    print("=" * 80)
    print()

    print("Key Benefits Demonstrated:")
    print("  ✓ Parallel data extraction (2x faster)")
    print("  ✓ Automated data validation and quality checks")
    print("  ✓ Coordinated transformation pipeline")
    print("  ✓ Multi-dimensional analytics (revenue, customer, product)")
    print("  ✓ Automated executive reporting")
    print("  ✓ Full audit trail and lineage tracking")
    print()

    print("Business Value:")
    print("  • Reduced manual processing time from hours to minutes")
    print("  • Improved data quality through automated validation")
    print("  • Faster insights for business decision-making")
    print("  • Scalable to handle multiple data sources")
    print("  • Reproducible and auditable process")


if __name__ == "__main__":
    asyncio.run(main())
