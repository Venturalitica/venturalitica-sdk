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

### Risk-Driven Governance

Venturalitica shifts the focus from "checking boxes" to **managing risks**. Our approach links technical metrics to regulatory requirements:

| Risk Area | Regulation | Metric | Goal |
| :--- | :--- | :--- | :--- |
| **Data Quality** | EU AI Act Art. 10 | `class_imbalance` | Avoid training on unrepresentative data |
| **Fairness** | ECOA / EU AI Act | `disparate_impact` | Detect discrimination in historical data |
| **Bias Audit** | EU AI Act Art. 10 | `demographic_parity` | Ensure model outputs are fair across groups |
| **Accuracy** | EU AI Act Art. 15 | `recall` / `accuracy` | Ensure model performance meets thresholds |
| **Green AI** | EU AI Act Art. 11 | Carbon Emissions | Track and report environmental impact |

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

The SDK provides two powerful CLI commands for project analysis and compliance management.

### 1. BOM Scanner: `venturalitica scan`

Generate a **CycloneDX ML-BOM** (Machine Learning Bill of Materials) for your project.

#### What is an ML-BOM?

An ML-BOM is a standardized inventory of all components in your ML system:
- **Dependencies**: Python packages and versions
- **ML Models**: Detected model classes (scikit-learn, PyTorch, TensorFlow)
- **Frameworks**: MLOps tools (MLflow, WandB, ClearML)
- **Datasets**: Referenced data files

This is critical for:
- **Supply Chain Security**: Track vulnerable dependencies
- **Reproducibility**: Document exact versions used
- **Compliance**: EU AI Act Article 11 (Technical Documentation)
- **Auditing**: Provide evidence of system composition

#### Usage

```bash
# Scan current directory
venturalitica scan

# Scan specific project
venturalitica scan --target ./my-ml-project
```

#### Output: `bom.json`

```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.5",
  "components": [
    {
      "type": "library",
      "name": "scikit-learn",
      "version": "1.3.0"
    },
    {
      "type": "machine-learning-model",
      "name": "RandomForestClassifier",
      "description": "Detected in train.py"
    },
    {
      "type": "library",
      "name": "mlflow",
      "version": "2.9.0"
    }
  ]
}
```

#### What Gets Detected

**Dependencies:**
- `requirements.txt` parsing
- `pyproject.toml` (PEP 621) parsing
- Extracts package names and versions

**ML Models:**
Automatically detects instantiation of:
- **scikit-learn**: `RandomForestClassifier`, `LogisticRegression`, `SVC`, etc.
- **XGBoost**: `XGBClassifier`
- **LightGBM**: `LGBMClassifier`
- **CatBoost**: `CatBoostClassifier`
- **PyTorch**: `Sequential`, `Module`
- **TensorFlow/Keras**: `resnet18`, `resnet50`

**Detection Method:**
Uses Python AST (Abstract Syntax Tree) parsing to find model instantiations in `.py` files:

```python
# This will be detected:
model = RandomForestClassifier(n_estimators=100)

# This will also be detected:
from sklearn.ensemble import RandomForestClassifier
clf = RandomForestClassifier()
```

#### Integration with Compliance Workflows

The BOM is used by the dashboard (see below) to:
1. Populate the "Technical Check" tab
2. Generate EU AI Act Annex IV Section 2 (System Elements)
3. Identify security vulnerabilities in dependencies

---

### 2. Compliance Dashboard: `venturalitica ui`

Launch a **local Streamlit dashboard** for interactive compliance management.

#### Usage

```bash
venturalitica ui
```

Opens a web interface at `http://localhost:8501`

#### Dashboard Features

The dashboard has **three tabs** designed around a "PLG Strategy" (Product-Led Growth):

##### Tab 1: ✅ Technical Check (Easy Mode)

**Purpose**: Validate technical aspects independently of organizational policy.

**Features:**

1.  **Bill of Materials Viewer**
    - Displays the `bom.json` generated by `venturalitica scan`
    - Shows all detected components with versions
    - Interactive JSON explorer

2.  **Green AI / Carbon Footprint Tracking**
    - Reads `emissions.csv` (generated by `codecarbon`)
    - Displays:
      - CO₂ emissions (kgCO₂)
      - Training duration
      - Energy consumed (kWh)
    - Provides integration code snippet if not detected

**Example Integration with CodeCarbon:**

```python
from codecarbon import EmissionsTracker

tracker = EmissionsTracker()
tracker.start()

# Your training code
model.fit(X_train, y_train)

tracker.stop()  # Writes to emissions.csv
```

**Why This Matters:**
- **EU AI Act Article 11**: Environmental impact documentation
- **Green AI**: Track and reduce ML carbon footprint
- **Transparency**: Show stakeholders the environmental cost

##### Tab 2: 🏛️ Governance & Risks (Pain Mode)

**Purpose**: Highlight governance gaps to drive SaaS upsell.

**Features:**

1.  **Risk Identification**
    - Lists EU AI Act compliance risks:
      - Fundamental Rights Impact (bias)
      - Human Oversight gaps
      - Data Governance issues

2.  **Mitigation Gap Analysis**
    - Shows missing mitigation plans in OSCAL policies
    - Compares two approaches:
      - **Option A (Local)**: Manually edit 500+ line YAML files
      - **Option B (SaaS)**: Push to Venturalitica Platform for guided mitigation

3.  **Upsell Mechanism**
    - "Push to SaaS" button demonstrates the value proposition
    - Creates "pain" around manual OSCAL editing
    - Positions SaaS as the "easy" solution

**Why This Design:**
- **PLG Strategy**: Free SDK creates demand for paid SaaS
- **Pain-Driven Adoption**: Users experience the complexity of manual compliance
- **Handshake Moment**: Transition from local SDK to cloud platform

##### Tab 3: 📄 Documentation (Gap Analysis)

**Purpose**: Generate EU AI Act Annex IV technical documentation draft.

**Features:**

1.  **System Elements (Section 2)**
    - Auto-populated from `bom.json`
    - Lists all components with versions
    - Fulfills Article 11 requirements

2.  **Incomplete Status Warning**
    - Shows that Section 3 (Risk System) is missing
    - Drives need for full compliance workflow

**Example Output:**

```markdown
### 2. System Elements

- **scikit-learn** (1.3.0): library
- **RandomForestClassifier** (unknown): machine-learning-model
- **mlflow** (2.9.0): library
- **pandas** (2.0.0): library
```

#### Dashboard Configuration

**Sidebar Controls:**
- **Project Root**: Path to scan (defaults to current directory)
- **Run Scan**: Triggers BOM generation

**Session State:**
- BOM results persist across tab navigation
- Scan results cached for performance

#### Use Cases

1.  **Pre-Demo Preparation**
    ```bash
    venturalitica scan
    venturalitica ui
    # Show stakeholders the BOM and carbon footprint
    ```

2.  **Documentation Generation**
    ```bash
    venturalitica scan
    venturalitica ui
    # Export Section 2 of Annex IV from Tab 3
    ```

3.  **Carbon Footprint Monitoring**
    ```python
    # In training script
    from codecarbon import EmissionsTracker
    tracker = EmissionsTracker()
    tracker.start()
    model.fit(X, y)
    tracker.stop()
    ```
    ```bash
    # Then view in dashboard
    venturalitica ui
    ```

#### Technical Architecture

**Dashboard Stack:**
- **Streamlit**: Web UI framework
- **CycloneDX**: BOM standard
- **AST Parsing**: Model detection
- **pandas**: CSV reading (emissions)

**File Dependencies:**
- `bom.json` (generated by scanner)
- `emissions.csv` (generated by codecarbon)
- `risks.oscal.yaml` (referenced in Tab 2)

---

### CLI Best Practices

1.  **Run `scan` before `ui`**: Generate BOM first for full dashboard functionality
2.  **Integrate CodeCarbon**: Add emissions tracking to see Green AI metrics
3.  **Version Control BOM**: Commit `bom.json` for reproducibility
4.  **CI/CD Integration**: Run `venturalitica scan` in pipelines to detect dependency changes

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

For a deep dive into a real-world scenario, check out our **[Loan Approval Fairness Tutorial](scenarios/loan-fairness.md)**.

**What you'll learn:**
- **The Problem**: Real-world bias (Apple Card case study)
- **The Risks**: Mapping EU AI Act and ECOA to technical controls
- **The Solution**: Implementing pre-training and post-training audits
- **Green AI**: Tracking carbon footprint during model training
- **Resolution**: How to fix fairness and accuracy failures

**Quick Start:**
```bash
git clone https://github.com/venturalitica/venturalitica-sdk-samples.git
cd venturalitica-sdk-samples/scenarios/loan-mlflow-sklearn
uv run python train.py
```

---

## Next Steps

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
