# Venturalitica SDK

**Frictionless Governance for AI Systems.**

The Venturalitica SDK enables Data Scientists and ML Engineers to integrate compliance and risk management directly into their training workflows. Built on the **OSCAL** (Open Security Controls Assessment Language) standard, it provides semantic policy enforcement with educational audit trails.

## ✨ Key Features

- **Role-Based Policy Binding**: Semantic mapping from policy definitions to your DataFrame columns
- **Educational Audit Logs**: Control descriptions that explain *why* metrics matter (e.g., "80% Rule", "Class Imbalance")
- **OSCAL-Native**: Industry-standard policy definitions compatible with NIST frameworks
- **MLOps Agnostic**: Native adapters for **MLflow**, **Weights & Biases**, and **ClearML**
- **Pre-training & Post-training Audits**: Validate data quality before training and model fairness after
- **Robust Metric Execution**: Gracefully handles missing columns for flexible audit scenarios

## 📦 Installation

```bash
pip install venturalitica-sdk
```

## 🚀 Quick Start

### 1. Define Your Policy (OSCAL)

Create a `risks.oscal.yaml` file:

```yaml
assessment-plan:
  uuid: loan-risk-policy
  metadata:
    title: "Loan Approval Fairness Policy"
  reviewed-controls:
    control-selections:
      - include-controls:
        - control-id: fair-gender
          description: "Demographic parity for gender must be under 10%"
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

### 2. Enforce in Your Training Script

```python
import pandas as pd
import venturalitica as vl
from sklearn.ensemble import RandomForestClassifier

# Load your data
df = pd.read_csv("loan_data.csv")
X = df.drop(columns=["approved", "gender"])
y = df["approved"]

# Start transparent tracking
with vl.monitor(name="Training Loan Model"):
    model = RandomForestClassifier()
    model.fit(X, y)

predictions = model.predict(X)

# Enforce governance policies
vl.enforce(
    data=df,
    target="approved",           # Physical column name for target
    prediction=predictions,      # Model predictions
    gender="gender",             # Semantic binding: gender -> physical column
    policy="risks.oscal.yaml"
)
```

### 3. Review the Audit Log

```
[Venturalitica] Policy: Loan Approval Fairness Policy
[Binding] Virtual Role 'dimension' bound to Variable 'gender' (Column: 'gender')
[Binding] Virtual Role 'target' bound to Variable 'target' (Column: 'approved')
[Binding] Virtual Role 'prediction' bound to Variable 'prediction' (Column: <predictions>)

Evaluating Control 'fair-gender': Demographic parity for gender must be under 10%
  ✓ PASS: demographic_parity_diff = 0.08 < 0.10
```

## 📚 Documentation

- **[Tutorial](docs/tutorial.md)**: Comprehensive guide to SDK features
- **[Quickstart](docs/quickstart.md)**: Get started in 5 minutes
- **[Green AI](docs/green-ai.md)**: Transparent carbon tracking
- **[Samples Repository](https://github.com/venturalitica/venturalitica-sdk-samples)**: Real-world examples with datasets

## 🎯 Core Concepts

### Role-Based Binding

The SDK uses a three-tier mapping system:

1. **Functional Roles** (defined by metrics): `target`, `prediction`, `dimension`
2. **Semantic Variables** (defined in policies): `gender`, `age_group`, `income`
3. **Physical Columns** (in your DataFrame): `sex_col`, `age_cat`, `salary`

This decoupling allows policies to evolve independently of your training code.

### Educational Audits

Control descriptions include regulatory context:

```yaml
- control-id: data-quality-check
  description: "Data Quality: Minority class should represent at least 20% to avoid Class Imbalance"
```

## 🔗 MLOps Integration

The SDK integrates seamlessly with popular MLOps platforms:

```python
import mlflow
import venturalitica as vl

# Automatic logging to MLflow
vl.enforce(
    data=df,
    target="approved",
    prediction=predictions,
    gender="gender",
    policy="risks.oscal.yaml"
)
```

**Supported Platforms:**
- ✅ **MLflow** - Metrics, tags, and artifact logging
- ✅ **Weights & Biases** - Experiment tracking with governance summaries
- ✅ **ClearML** - Healthcare/regulated industry MLOps

## 🛠️ CLI Tools

### BOM Scanner

Generate a **CycloneDX ML-BOM** (Machine Learning Bill of Materials):

```bash
venturalitica scan --target ./my-ml-project
```

**Detects:**
- Python dependencies (`requirements.txt`, `pyproject.toml`)
- ML models (scikit-learn, PyTorch, TensorFlow, XGBoost, etc.)
- MLOps frameworks (MLflow, WandB, ClearML)

**Output:** `bom.json` - Standardized inventory for supply chain security and EU AI Act compliance.

### Compliance Dashboard

Launch a local **Streamlit dashboard** for interactive governance:

```bash
venturalitica ui
```

**Features:**
- **Technical Check**: BOM viewer + Green AI carbon footprint tracking
- **Governance & Risks**: EU AI Act compliance gap analysis
- **Documentation**: Auto-generate Annex IV technical documentation

**Integrates with:**
- `bom.json` (from scanner)
- `emissions.csv` (from CodeCarbon)
- OSCAL policies

## ☁️ Venturalitica Cloud (Coming Soon)

**Enterprise-grade EU AI Act & ISO 42001 compliance management**

While the SDK provides frictionless local enforcement, **Venturalitica Cloud** will offer a complete compliance lifecycle management platform for **EU AI Act** and **ISO 42001**:

### What's Coming

- **Visual Policy Builder**: Create OSCAL policies mapped to EU AI Act Articles 9-15 & ISO 42001 controls
- **Team Collaboration**: Centralized policy management across organizations
- **Compliance Dashboard**: Real-time status for EU AI Act & ISO 42001 requirements
- **Annex IV Generator**: Auto-generate complete EU AI Act technical documentation
- **Risk Assessment**: Guided workflows for high-risk AI system classification
- **Audit Trail**: Immutable compliance history for regulatory inspections
- **Integration Hub**: Connect with your existing MLOps and governance tools

### Early Access

Interested in early access to Venturalitica Cloud?
- **Join the waitlist**: [venturalitica.com/cloud](https://venturalitica.com/cloud) *(coming soon)*
- **Enterprise inquiries**: Contact us for pilot programs

The SDK will always remain **free and open-source** under Apache 2.0. The cloud platform will offer additional enterprise features for teams managing EU AI Act and ISO 42001 compliance at scale.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md).

## 📄 License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## 🔗 Links

- [Samples Repository](https://github.com/venturalitica/venturalitica-sdk-samples)
- [Documentation](docs/)
- [OSCAL Standard](https://pages.nist.gov/OSCAL/)
