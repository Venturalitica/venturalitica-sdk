# Venturalitica SDK Tutorial

This tutorial covers all features of the Venturalitica SDK, from basic policy enforcement to advanced MLOps integrations.

## Table of Contents

1. [Installation](#installation)
2. [Core Concepts](#core-concepts)
3. [Basic Usage: Policy Enforcement](#basic-usage-policy-enforcement)
4. [Role-Based Binding](#role-based-binding)
5. [OSCAL Policy Authoring](#oscal-policy-authoring)
6. [MLOps Integrations](#mlops-integrations)
7. [CLI Tools](#cli-tools)
8. [Advanced Features](#advanced-features)

---

## Installation

### Basic Installation

```bash
pip install venturalitica-sdk
```

### With Optional Dependencies

```bash
# For MLflow integration
pip install "venturalitica-sdk[mlflow]"

# For Weights & Biases integration
pip install "venturalitica-sdk[wandb]"

# For ClearML integration
pip install "venturalitica-sdk[clearml]"

# All integrations
pip install "venturalitica-sdk[all]"
```

---

## Core Concepts

### The Three-Tier Mapping System

The SDK uses a semantic binding architecture that decouples policies from training code:

```
Functional Roles (Metrics) → Semantic Variables (Policy) → Physical Columns (DataFrame)
     ↓                              ↓                            ↓
  "dimension"                    "gender"                    "sex_col"
  "target"                       "target"                    "approved"
  "prediction"                   "prediction"                <model output>
```

**Why this matters:**
- Policies can evolve independently of your training scripts
- Same policy can be reused across different datasets
- Clear audit trail showing exactly which column was used for each metric

### Educational Audit Logs

Every control includes educational context explaining *why* it matters:

```
Evaluating Control 'credit-data-imbalance': Data Quality: Minority class 
(rejected loans) should represent at least 20% of the dataset to avoid 
biased training due to severe Class Imbalance.
  ✓ PASS: class_imbalance = 0.30 >= 0.20
```

---

## Basic Usage: Policy Enforcement

### 1. Simple Metric Enforcement

If you already have computed metrics:

```python
from venturalitica import enforce

# Your pre-computed metrics
metrics = {
    "accuracy": 0.95,
    "precision": 0.92,
    "recall": 0.89
}

# Enforce policy
enforce(
    metrics=metrics,
    policy="governance-baseline.oscal.yaml"
)
```

### 2. Automatic Metric Computation

Let the SDK compute metrics from your data:

```python
import pandas as pd
from venturalitica import enforce

# Your training data and predictions
df = pd.read_csv("loan_data.csv")
predictions = model.predict(df[features])

# SDK computes and evaluates metrics automatically
enforce(
    data=df,
    target="approved",           # Column name for ground truth
    prediction=predictions,      # Model predictions
    policy="risks.oscal.yaml"
)
```

### 3. Multi-Policy Enforcement

Enforce multiple policies in a single call:

```python
enforce(
    data=df,
    target="approved",
    prediction=predictions,
    gender="gender",
    policy=[
        "policies/risks.oscal.yaml",
        "policies/governance-baseline.oscal.yaml"
    ]
)
```

---

## Role-Based Binding

### Understanding Functional Roles

Metrics expect specific inputs with **functional roles**:

- `target`: Ground truth labels
- `prediction`: Model predictions
- `dimension`: Protected attribute for fairness metrics (e.g., gender, age)

### Semantic Binding in Practice

**Your DataFrame:**
```python
df.columns
# ['customer_id', 'sex_col', 'age_cat', 'approved', ...]
```

**Your Training Script:**
```python
enforce(
    data=df,
    target="approved",        # Maps 'target' role to 'approved' column
    prediction=predictions,   # Maps 'prediction' role to model output
    gender="sex_col",         # Maps 'gender' semantic variable to 'sex_col'
    age="age_cat"            # Maps 'age' semantic variable to 'age_cat'
)
```

**Your Policy (OSCAL):**
```yaml
- control-id: fair-gender
  props:
    - name: "input:dimension"
      value: gender           # Policy expects 'gender' semantic variable
    - name: "input:target"
      value: target
    - name: "input:prediction"
      value: prediction
```

**Audit Trail:**
```
[Binding] Virtual Role 'dimension' bound to Variable 'gender' (Column: 'sex_col')
[Binding] Virtual Role 'target' bound to Variable 'target' (Column: 'approved')
[Binding] Virtual Role 'prediction' bound to Variable 'prediction' (Column: <predictions>)
```

### Multi-Attribute Governance

Monitor multiple protected attributes simultaneously:

```python
enforce(
    data=df,
    target="approved",
    prediction=predictions,
    gender="sex_col",         # First dimension
    age="age_group",          # Second dimension
    policy="multi-attribute-policy.oscal.yaml"
)
```

---

## OSCAL Policy Authoring

### Policy Structure

```yaml
assessment-plan:
  uuid: unique-policy-identifier
  metadata:
    title: "Human-Readable Policy Name"
    version: "1.0.0"
  
  reviewed-controls:
    control-selections:
      - include-controls:
        - control-id: unique-control-id
          description: "Educational description explaining WHY this control matters"
          props:
            - name: metric_key
              value: demographic_parity_diff
            - name: threshold
              value: "0.10"
            - name: operator
              value: "<"
            - name: "input:dimension"
              value: gender
            - name: "input:target"
              value: target
            - name: "input:prediction"
              value: prediction
```

### Available Metrics

#### Performance Metrics
- `accuracy` - Overall classification accuracy
- `precision` - Positive predictive value
- `recall` - True positive rate
- `f1` - Harmonic mean of precision and recall

#### Fairness Metrics
- `demographic_parity_diff` - Difference in positive prediction rates across groups
- `equal_opportunity_diff` - Difference in true positive rates across groups
- `disparate_impact` - Ratio of positive prediction rates (80% Rule)

#### Data Quality Metrics
- `class_imbalance` - Proportion of minority class

### Operators

- `<` - Less than
- `<=` - Less than or equal
- `>` - Greater than
- `>=` - Greater than or equal
- `==` - Equal to
- `!=` - Not equal to

### Pre-training vs Post-training Controls

**Pre-training** (data-only audits):
```yaml
- control-id: data-quality-check
  description: "Class Imbalance check before training"
  props:
    - name: metric_key
      value: class_imbalance
    - name: threshold
      value: "0.20"
    - name: operator
      value: ">="
    - name: "input:target"
      value: target
```

**Post-training** (model fairness audits):
```yaml
- control-id: fairness-check
  description: "Demographic Parity after training"
  props:
    - name: metric_key
      value: demographic_parity_diff
    - name: threshold
      value: "0.10"
    - name: operator
      value: "<"
    - name: "input:dimension"
      value: gender
    - name: "input:target"
      value: target
    - name: "input:prediction"
      value: prediction
```

### Educational Descriptions

Make your policies self-documenting:

```yaml
- control-id: credit-data-bias
  description: "Pre-training Fairness: Disparate impact ratio should follow the standard '80% Rule' (Four-Fifths Rule), ensuring favorable loan outcomes are representative across groups."
```

---

## MLOps Integrations

The SDK automatically detects and logs to active MLOps frameworks.

### MLflow Integration

```python
import mlflow
from venturalitica import enforce

mlflow.start_run()

# Train your model
model.fit(X_train, y_train)
predictions = model.predict(X_test)

# SDK automatically logs to MLflow
enforce(
    data=df_test,
    target="approved",
    prediction=predictions,
    gender="gender",
    policy="risks.oscal.yaml"
)

mlflow.end_run()
```

**What gets logged:**
- Metrics: `governance.{control_id}.score` (1.0 for pass, 0.0 for fail)
- Tags: `governance.{control_id}` (PASS/FAIL)
- Tag: `governance.overall` (PASS/FAIL)
- Artifact: `governance_report.md` (full compliance report)

### Weights & Biases Integration

```python
import wandb
from venturalitica import enforce

wandb.init(project="loan-fairness")

# Train your model
model.fit(X_train, y_train)
predictions = model.predict(X_test)

# SDK automatically logs to WandB
enforce(
    data=df_test,
    target="approved",
    prediction=predictions,
    gender="gender",
    policy="risks.oscal.yaml"
)

wandb.finish()
```

**What gets logged:**
- Metrics: `governance.{control_id}.score`
- Summary: `governance.{control_id}` (PASS/FAIL)
- Summary: `governance.overall` (PASS/FAIL)
- Artifact: `governance_report` (markdown report)

### ClearML Integration

```python
from clearml import Task
from venturalitica import enforce

task = Task.init(project_name="loan-fairness", task_name="training")

# Train your model
model.fit(X_train, y_train)
predictions = model.predict(X_test)

# SDK automatically logs to ClearML
enforce(
    data=df_test,
    target="approved",
    prediction=predictions,
    gender="gender",
    policy="risks.oscal.yaml"
)
```

**What gets logged:**
- Tags: `governance.{control_id}:PASS/FAIL`
- Tag: `governance.overall:PASS/FAIL`
- Console logs: Governance report text

---

## CLI Tools

### 1. Project Scanning

Generate a CycloneDX ML-BOM (Machine Learning Bill of Materials):

```bash
venturalitica scan --target ./my-ml-project
```

**Output:** `bom.json` containing:
- Python dependencies
- Detected ML frameworks
- Model files
- Dataset references

### 2. Compliance Dashboard

Launch a local Streamlit dashboard for governance management:

```bash
venturalitica ui
```

**Features:**
- **Technical Check**: Validates code quality, dependencies, and carbon footprint
- **Governance**: High-level risk overview
- **Documentation**: Generates EU AI Act Annex IV technical documentation draft

---

## Advanced Features

### 1. Programmatic Report Generation

```python
from venturalitica import enforce
from venturalitica.integrations import generate_report

results = enforce(
    data=df,
    target="approved",
    prediction=predictions,
    gender="gender",
    policy="risks.oscal.yaml"
)

# Generate markdown report
report_md = generate_report(results)
with open("compliance_report.md", "w") as f:
    f.write(report_md)
```

### 2. Custom Storage Backends

```python
from venturalitica.storage import LocalFileSystemStorage
from venturalitica.core import GovernanceValidator

# Use custom policy storage location
storage = LocalFileSystemStorage(base_path="/custom/policies")
validator = GovernanceValidator("risks.oscal.yaml", storage=storage)
```

### 3. Handling Missing Columns

The SDK gracefully handles missing columns (e.g., during pre-training audits):

```python
# Pre-training: no predictions yet
enforce(
    data=df_train,
    target="approved",
    gender="gender",
    policy="risks.oscal.yaml"  # Will skip controls requiring 'prediction'
)

# Post-training: full audit
enforce(
    data=df_test,
    target="approved",
    prediction=predictions,
    gender="gender",
    policy="risks.oscal.yaml"  # All controls evaluated
)
```

### 4. Accessing Raw Results

```python
from venturalitica.core import ComplianceResult

results: List[ComplianceResult] = enforce(
    data=df,
    target="approved",
    prediction=predictions,
    gender="gender",
    policy="risks.oscal.yaml"
)

for result in results:
    print(f"Control: {result.control_id}")
    print(f"Passed: {result.passed}")
    print(f"Metric: {result.metric_key} = {result.actual_value:.4f}")
    print(f"Threshold: {result.operator} {result.threshold}")
```

---

## Complete Example: Loan Approval Scenario

See the [venturalitica-sdk-samples](https://github.com/venturalitica/venturalitica-sdk-samples) repository for complete, runnable examples:

```bash
git clone https://github.com/venturalitica/venturalitica-sdk-samples.git
cd venturalitica-sdk-samples/scenarios/loan-mlflow-sklearn
uv run python train.py
```

**What this demonstrates:**
- Pre-training data quality checks
- Post-training fairness audits
- Multi-attribute governance (gender + age)
- MLflow integration
- Educational audit logs

---

## Next Steps

1. **Explore Samples**: Check out [venturalitica-sdk-samples](https://github.com/venturalitica/venturalitica-sdk-samples) for real-world examples
2. **Create Custom Policies**: Author OSCAL policies for your specific compliance requirements
3. **Integrate with CI/CD**: Add governance checks to your ML pipeline
4. **Join the Community**: Contribute to the SDK or share your use cases

---

## Resources

- [SDK Repository](https://github.com/venturalitica/venturalitica-sdk)
- [Samples Repository](https://github.com/venturalitica/venturalitica-sdk-samples)
- [OSCAL Documentation](https://pages.nist.gov/OSCAL/)
- [EU AI Act](https://artificialintelligenceact.eu/)
- [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework)
