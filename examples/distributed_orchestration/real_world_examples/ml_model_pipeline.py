#!/usr/bin/env python3
"""Real-World Example: ML Model Development Pipeline.

This example demonstrates using distributed agents to orchestrate the complete
machine learning model development lifecycle from data preparation through
deployment.

Business Scenario:
A data science team needs to develop and deploy an ML model for customer churn
prediction. The process involves:
- Data exploration and profiling
- Feature engineering
- Model selection and training
- Hyperparameter tuning
- Model evaluation and validation
- Model explanation and interpretability
- Deployment preparation
- Documentation and monitoring setup

This pipeline automates and coordinates all stages of ML development.
"""

import asyncio

from pydantic_deep import StateBackend
from pydantic_deep.types import SubAgentConfig

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orchestrator import DistributedOrchestrator, TaskPriority


# Define specialized ML development workers
ML_WORKERS = [
    SubAgentConfig(
        name="data-analyst",
        description="Performs exploratory data analysis and profiling",
        instructions="""You are a data analysis specialist for ML projects.

Responsibilities:
1. Exploratory data analysis (EDA)
2. Data profiling and statistics
3. Missing value analysis
4. Distribution analysis
5. Correlation analysis
6. Outlier detection
7. Data quality assessment

Analysis deliverables:
- Dataset overview (shape, types)
- Statistical summary
- Missing data report
- Distribution plots description
- Correlation insights
- Data quality issues
- Recommendations for preprocessing""",
    ),
    SubAgentConfig(
        name="feature-engineer",
        description="Creates and optimizes features for ML models",
        instructions="""You are a feature engineering expert.

Responsibilities:
1. Feature creation and transformation
2. Encoding categorical variables
3. Scaling numerical features
4. Feature selection
5. Dimensionality reduction
6. Feature interaction creation
7. Temporal feature engineering

Techniques:
- One-hot encoding, label encoding
- StandardScaler, MinMaxScaler
- Polynomial features
- Binning and discretization
- Feature importance analysis
- PCA, t-SNE for dimensionality

Output: Engineered feature set with rationale""",
    ),
    SubAgentConfig(
        name="model-architect",
        description="Designs and selects appropriate ML models",
        instructions="""You are an ML model architecture specialist.

Responsibilities:
1. Problem formulation
2. Model selection (classification, regression, clustering)
3. Algorithm recommendations
4. Architecture design for deep learning
5. Ensemble strategies
6. Model complexity vs performance tradeoffs

Considerations:
- Problem type and constraints
- Data size and quality
- Interpretability requirements
- Inference latency needs
- Training time constraints
- Deployment environment

Output: Model architecture recommendations with rationale""",
    ),
    SubAgentConfig(
        name="model-trainer",
        description="Trains and tunes ML models",
        instructions="""You are an ML model training specialist.

Responsibilities:
1. Model training implementation
2. Cross-validation strategy
3. Hyperparameter tuning
4. Training optimization
5. Early stopping and callbacks
6. Handling class imbalance
7. Regularization techniques

Training strategies:
- K-fold cross-validation
- Grid search, random search
- Bayesian optimization
- Learning rate scheduling
- Data augmentation
- Transfer learning

Output: Trained model with training logs and metrics""",
    ),
    SubAgentConfig(
        name="model-evaluator",
        description="Evaluates model performance and validates results",
        instructions="""You are an ML model evaluation specialist.

Responsibilities:
1. Performance metrics calculation
2. Model comparison
3. Statistical significance testing
4. Bias and fairness analysis
5. Robustness testing
6. Validation strategies
7. A/B testing design

Evaluation metrics:
- Classification: accuracy, precision, recall, F1, ROC-AUC
- Regression: MSE, RMSE, MAE, R²
- Business metrics
- Confusion matrix analysis
- Performance across segments

Output: Comprehensive evaluation report with recommendations""",
    ),
    SubAgentConfig(
        name="ml-explainer",
        description="Provides model interpretability and explanations",
        instructions="""You are an ML interpretability specialist.

Responsibilities:
1. Model explanation (SHAP, LIME)
2. Feature importance analysis
3. Decision tree visualization
4. Partial dependence plots
5. Individual prediction explanations
6. Bias detection
7. Fairness metrics

Interpretability techniques:
- SHAP values
- LIME explanations
- Permutation importance
- Feature ablation
- Attention visualization
- Counterfactual explanations

Output: Model interpretability report for stakeholders""",
    ),
    SubAgentConfig(
        name="mlops-specialist",
        description="Prepares model for deployment and monitoring",
        instructions="""You are an MLOps specialist.

Responsibilities:
1. Model serialization and versioning
2. API endpoint design
3. Deployment strategy
4. Monitoring setup
5. A/B testing framework
6. Model retraining pipeline
7. Performance tracking

Deployment considerations:
- Model serving (REST, gRPC)
- Containerization (Docker)
- Scalability requirements
- Latency constraints
- Model versioning
- Rollback strategy
- Monitoring dashboards

Output: Deployment package with monitoring plan""",
    ),
]


async def main():
    print("=" * 80)
    print("Real-World Use Case: ML Model Development Pipeline")
    print("=" * 80)
    print()

    print("Initializing ML Development Pipeline...")
    orchestrator = DistributedOrchestrator(
        model="openai:gpt-4o-mini",
        custom_workers=ML_WORKERS,
        max_concurrent_workers=5,
    )
    print(f"✓ Orchestrator ready with {len(ML_WORKERS)} ML specialists")
    print()

    # Sample customer churn dataset metadata
    dataset_info = """
    Dataset: Customer Churn Prediction
    Target: churn (binary: 0=retained, 1=churned)
    Samples: 10,000 customers
    Features: 20

    Features:
    - customer_id: unique identifier
    - tenure: months as customer (0-72)
    - monthly_charges: monthly fee ($19.99-$118.75)
    - total_charges: total amount charged
    - contract_type: Month-to-month, One year, Two year
    - payment_method: Electronic check, Mailed check, Bank transfer, Credit card
    - internet_service: DSL, Fiber optic, No
    - online_security: Yes, No, No internet service
    - tech_support: Yes, No, No internet service
    - streaming_tv: Yes, No, No internet service
    - streaming_movies: Yes, No, No internet service
    - senior_citizen: 0 or 1
    - partner: Yes, No
    - dependents: Yes, No
    - phone_service: Yes, No
    - multiple_lines: Yes, No, No phone service
    - paperless_billing: Yes, No
    - gender: Male, Female

    Target distribution: 73.5% retained, 26.5% churned
    """

    orchestrator.deps.backend.write("/data/dataset_info.txt", dataset_info)
    print("✓ Customer churn dataset loaded")
    print(dataset_info)
    print()

    # ============================================================================
    # PHASE 1: DATA ANALYSIS & FEATURE ENGINEERING (Parallel)
    # ============================================================================
    print("PHASE 1: Data Analysis & Feature Engineering")
    print("=" * 80)
    print("Analyzing data and engineering features in parallel...")
    print()

    data_prep_tasks = [
        f"""Perform exploratory data analysis on the customer churn dataset

        Dataset information:
        {dataset_info}

        Analysis required:
        1. Dataset shape and feature types
        2. Statistical summary (mean, std, min, max)
        3. Missing value analysis
        4. Target variable distribution (class imbalance)
        5. Numerical feature distributions
        6. Categorical feature distributions
        7. Correlation analysis with target
        8. Outlier detection

        Provide insights on:
        - Data quality issues
        - Class imbalance concerns
        - Important features (initial assessment)
        - Preprocessing recommendations

        Output: EDA report with actionable insights""",

        f"""Design feature engineering strategy

        Based on dataset:
        {dataset_info}

        Feature engineering tasks:
        1. Encode categorical variables (contract_type, payment_method, etc.)
        2. Scale numerical features (tenure, monthly_charges, total_charges)
        3. Create interaction features (tenure × monthly_charges)
        4. Create ratio features (total_charges / tenure)
        5. Bin continuous variables (tenure bins: 0-12, 13-24, 25-48, 49+)
        6. Create aggregate features
        7. Handle missing values strategy

        Considerations:
        - Interpretability for business
        - Avoiding data leakage
        - Feature importance

        Output: Feature engineering plan with code guidelines""",
    ]

    data_prep_results = await orchestrator.execute_parallel(
        data_prep_tasks,
        priority=TaskPriority.HIGH
    )

    eda_report = data_prep_results[0]
    feature_plan = data_prep_results[1]

    print("✓ Data analysis and feature engineering planning completed")
    print("\nEDA Report:")
    print(eda_report[:400] + "..." if len(eda_report) > 400 else eda_report)
    print("\nFeature Engineering Plan:")
    print(feature_plan[:400] + "..." if len(feature_plan) > 400 else feature_plan)
    print()

    # ============================================================================
    # PHASE 2: MODEL ARCHITECTURE & TRAINING STRATEGY
    # ============================================================================
    print("PHASE 2: Model Architecture & Training Strategy")
    print("=" * 80)
    print("Designing model architecture and training approach...")
    print()

    model_design_task = f"""Design ML model architecture for customer churn prediction

    Problem: Binary classification (churn prediction)
    Dataset: {dataset_info[:300]}
    EDA insights: {eda_report[:300]}
    Features: {feature_plan[:300]}

    Requirements:
    1. Recommend 3-5 candidate models with rationale
    2. Consider interpretability (business stakeholders need explanations)
    3. Handle class imbalance (73.5% / 26.5%)
    4. Optimize for recall (minimize false negatives)
    5. Fast inference (<100ms)

    Model candidates to consider:
    - Logistic Regression (baseline, interpretable)
    - Random Forest (good performance, feature importance)
    - Gradient Boosting (XGBoost, LightGBM, CatBoost)
    - Neural Network (if needed for complex patterns)

    For each model provide:
    - Pros and cons
    - Hyperparameter tuning strategy
    - Expected performance range
    - Training time estimate
    - Interpretability level

    Output: Model architecture recommendations with training strategy"""

    model_architecture = await orchestrator.execute(
        model_design_task,
        priority=TaskPriority.HIGH
    )

    print("✓ Model architecture designed")
    print("\nModel Architecture:")
    print(model_architecture[:500] + "..." if len(model_architecture) > 500 else model_architecture)
    print()

    # ============================================================================
    # PHASE 3: MODEL TRAINING & TUNING (Parallel for multiple models)
    # ============================================================================
    print("PHASE 3: Model Training & Hyperparameter Tuning")
    print("=" * 80)
    print("Training multiple models in parallel...")
    print()

    training_tasks = [
        f"""Train and tune Logistic Regression model

        Based on architecture plan:
        {model_architecture[:200]}

        Training requirements:
        1. Handle class imbalance (use class_weight='balanced')
        2. 5-fold cross-validation
        3. Tune regularization parameter C
        4. Select penalty type (l1, l2, elasticnet)
        5. Optimize for recall while maintaining precision

        Provide:
        - Training procedure (pseudo-code)
        - Hyperparameter grid
        - Cross-validation results
        - Best parameters found
        - Performance metrics (accuracy, precision, recall, F1, ROC-AUC)
        - Feature coefficients (top 10)

        Output: Trained Logistic Regression report""",

        f"""Train and tune Random Forest model

        Based on architecture plan:
        {model_architecture[:200]}

        Training requirements:
        1. Handle class imbalance (balanced class weights)
        2. 5-fold cross-validation
        3. Tune: n_estimators, max_depth, min_samples_split, min_samples_leaf
        4. Feature importance extraction
        5. Optimize for recall

        Hyperparameters to tune:
        - n_estimators: [100, 200, 300]
        - max_depth: [10, 20, 30, None]
        - min_samples_split: [2, 5, 10]
        - min_samples_leaf: [1, 2, 4]

        Provide:
        - Training procedure
        - Best hyperparameters
        - CV performance
        - Feature importance (top 15)
        - Out-of-bag score

        Output: Trained Random Forest report""",

        f"""Train and tune Gradient Boosting (XGBoost) model

        Based on architecture plan:
        {model_architecture[:200]}

        Training requirements:
        1. Handle class imbalance (scale_pos_weight)
        2. 5-fold cross-validation
        3. Early stopping (50 rounds)
        4. Tune learning_rate, max_depth, n_estimators, subsample
        5. Optimize for recall with AUC monitoring

        Hyperparameters to tune:
        - learning_rate: [0.01, 0.05, 0.1]
        - max_depth: [3, 5, 7]
        - n_estimators: [100, 200, 300]
        - subsample: [0.8, 1.0]
        - colsample_bytree: [0.8, 1.0]

        Provide:
        - Training procedure with early stopping
        - Best hyperparameters
        - Learning curves
        - Feature importance (SHAP or gain)
        - Final performance metrics

        Output: Trained XGBoost report""",
    ]

    training_results = await orchestrator.execute_parallel(training_tasks)

    print("✓ All models trained and tuned")
    print("\nTraining Results:")
    model_types = ["Logistic Regression", "Random Forest", "XGBoost"]
    for i, (model_type, result) in enumerate(zip(model_types, training_results), 1):
        print(f"\n{i}. {model_type}:")
        print(result[:400] + "..." if len(result) > 400 else result)
    print()

    # ============================================================================
    # PHASE 4: MODEL EVALUATION & EXPLAINABILITY (Parallel)
    # ============================================================================
    print("PHASE 4: Model Evaluation & Explainability")
    print("=" * 80)
    print("Evaluating models and generating explanations...")
    print()

    eval_explain_tasks = [
        f"""Compare and evaluate all trained models

        Models to compare:
        1. Logistic Regression: {training_results[0][:200]}
        2. Random Forest: {training_results[1][:200]}
        3. XGBoost: {training_results[2][:200]}

        Evaluation requirements:
        1. Compare performance metrics (accuracy, precision, recall, F1, AUC)
        2. Analyze confusion matrices
        3. Assess performance on class imbalance
        4. Evaluate inference latency
        5. Test statistical significance of differences
        6. Check for overfitting (train vs validation)
        7. Assess robustness (performance across different segments)

        Business considerations:
        - Minimize false negatives (missing churners)
        - Balance precision (avoid false alarms)
        - Model interpretability for stakeholders
        - Deployment simplicity

        Output: Model comparison report with recommendation""",

        f"""Generate model explanations and interpretability analysis

        Focus on best-performing model from:
        {training_results[0][:150]}
        {training_results[1][:150]}
        {training_results[2][:150]}

        Explainability requirements:
        1. Global feature importance (top 15 features)
        2. SHAP summary (if applicable)
        3. Partial dependence plots (key features)
        4. Individual prediction examples (5 examples)
        5. Business insights from model
        6. Actionable recommendations for retention

        For each important feature explain:
        - Impact on churn probability
        - Direction of relationship
        - Business interpretation

        Output: Model explainability report for business stakeholders""",
    ]

    eval_explain_results = await orchestrator.execute_parallel(eval_explain_tasks)

    model_comparison = eval_explain_results[0]
    model_explanations = eval_explain_results[1]

    print("✓ Evaluation and explainability completed")
    print("\nModel Comparison:")
    print(model_comparison[:500] + "..." if len(model_comparison) > 500 else model_comparison)
    print("\nModel Explanations:")
    print(model_explanations[:500] + "..." if len(model_explanations) > 500 else model_explanations)
    print()

    # ============================================================================
    # PHASE 5: DEPLOYMENT PREPARATION
    # ============================================================================
    print("PHASE 5: Deployment Preparation & MLOps")
    print("=" * 80)
    print("Preparing model for production deployment...")
    print()

    deployment_task = f"""Prepare ML model for production deployment

    Selected model based on evaluation:
    {model_comparison[:300]}

    Model characteristics:
    {model_explanations[:200]}

    Deployment requirements:
    1. Model serialization (pickle/joblib)
    2. Model versioning strategy
    3. REST API endpoint design (FastAPI/Flask)
    4. Input validation schema
    5. Prediction response format
    6. Docker containerization
    7. Monitoring and logging setup
    8. A/B testing strategy
    9. Model retraining triggers
    10. Rollback plan

    Technical specifications:
    - Latency requirement: <100ms
    - Throughput: 100 req/s
    - Availability: 99.9%
    - Model drift detection
    - Feature drift monitoring

    Deliverables:
    - API specification (OpenAPI)
    - Deployment manifest (Kubernetes)
    - Monitoring dashboard config
    - Model registry setup
    - CI/CD pipeline integration
    - Production readiness checklist

    Output: Complete deployment package with MLOps setup"""

    deployment_package = await orchestrator.execute(
        deployment_task,
        priority=TaskPriority.URGENT
    )

    print("✓ Deployment package created")
    print("\nDeployment Package:")
    print(deployment_package[:600] + "..." if len(deployment_package) > 600 else deployment_package)
    print()

    # ============================================================================
    # PHASE 6: FINAL ML PROJECT REPORT
    # ============================================================================
    print("PHASE 6: ML Project Documentation")
    print("=" * 80)
    print("Generating comprehensive ML project report...")
    print()

    report_task = f"""Create comprehensive ML project documentation

    Compile all project phases:
    1. EDA: {eda_report[:200]}
    2. Features: {feature_plan[:200]}
    3. Models: {model_architecture[:200]}
    4. Training: {training_results[0][:150]}...
    5. Evaluation: {model_comparison[:200]}
    6. Explanations: {model_explanations[:200]}
    7. Deployment: {deployment_package[:200]}

    Documentation structure:
    1. Executive Summary
       - Business problem
       - Solution approach
       - Model performance
       - Expected business impact

    2. Data Analysis
       - Dataset characteristics
       - Key insights from EDA
       - Data quality findings

    3. Feature Engineering
       - Features created
       - Encoding strategies
       - Feature selection results

    4. Model Development
       - Models evaluated
       - Training approach
       - Hyperparameter tuning
       - Final model selection

    5. Model Performance
       - Metrics and benchmarks
       - Comparison with baseline
       - Performance across segments

    6. Model Interpretability
       - Key drivers of churn
       - Feature importance
       - Business insights

    7. Deployment Plan
       - Architecture overview
       - API specifications
       - Monitoring strategy
       - Maintenance plan

    8. Recommendations
       - Retention strategies
       - Model improvements
       - Next steps

    Format: Professional ML project report"""

    final_report = await orchestrator.execute(
        report_task,
        priority=TaskPriority.URGENT
    )

    print("✓ ML project report generated")
    print("\n" + "=" * 80)
    print("ML PROJECT REPORT")
    print("=" * 80)
    print(final_report)
    print()

    # ============================================================================
    # PIPELINE SUMMARY
    # ============================================================================
    print("=" * 80)
    print("ML Development Pipeline Summary")
    print("=" * 80)

    metrics = orchestrator.get_metrics()

    print(f"\nPipeline Statistics:")
    print(f"  Total tasks: {metrics['total_tasks']}")
    print(f"  Completed: {metrics['completed_tasks']}")
    print(f"  Success rate: {metrics['success_rate']:.1%}")
    print()

    print("ML Specialist Utilization:")
    for worker_name, stats in metrics['workers'].items():
        if stats['tasks_completed'] > 0:
            print(f"  {worker_name}: {stats['tasks_completed']} tasks")
    print()

    print("=" * 80)
    print("✓ ML Model Development Pipeline completed!")
    print("=" * 80)
    print()

    print("ML Pipeline Stages:")
    print("  ✓ Data exploration and profiling")
    print("  ✓ Feature engineering and selection")
    print("  ✓ Model architecture design")
    print("  ✓ Multi-model training and tuning")
    print("  ✓ Comprehensive evaluation")
    print("  ✓ Model interpretability analysis")
    print("  ✓ Production deployment preparation")
    print()

    print("Business Value:")
    print("  • Accelerated model development (weeks → days)")
    print("  • Systematic evaluation of multiple approaches")
    print("  • Built-in interpretability for stakeholders")
    print("  • Production-ready deployment package")
    print("  • Comprehensive documentation")
    print("  • Reproducible ML pipeline")
    print("  • Expected 15-20% reduction in customer churn")


if __name__ == "__main__":
    asyncio.run(main())
