# Venturalítica SDK

![coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)

**Frictionless Governance for AI Systems.**

The Venturalítica SDK enables Data Scientists and ML Engineers to integrate compliance and risk management directly into their training workflows. Built on the **OSCAL** (Open Security Controls Assessment Language) standard, it provides semantic policy enforcement with educational audit trails.

## ✨ Key Features

- **Glass Box Governance**: Sequential regulatory mapping (Art 9-15) for total transparency.
- **Local Sovereignty**: Zero-cloud dependency. All enforcement runs locally.
- **TraceCollector Architecture**: Unified evidence gathering for BOM, metrics, and logs.
- **Educational Audits**: Control descriptions that explain *why* metrics matter.
- **Deep Integrations**: Seamless "Glass Box" syncing with MLflow & WandB.
- **OSCAL-Native**: Policy-as-Code using standard NIST formats.
- **Annex IV Ready**: Auto-draft technical documentation from local traces.

## 📦 Installation

```bash
pip install git+https://github.com/Venturalitica/venturalitica-sdk.git
```

## ⚙️ Configuration

The SDK supports the following Environment Variables. We recommend using a `.env` file (but **never commit it**!).

| Variable | Description | Default | Required? |
| :--- | :--- | :--- | :--- |
| `MISTRAL_API_KEY` | [Get a Free Key](https://console.mistral.ai/). Used for Cloud Fallback if local Ollama fails. | None | **Recommended** |
| `VENTURALITICA_LLM_PRO` | Set to `true` to use Mistral even if Ollama is available (Higher Quality). | `false` | No |
| `MLFLOW_TRACKING_URI` | If set, `tracecollector` will auto-log audits to MLflow. | None | No |

## 📋 Prerequisites

*   **Python:** 3.11+
*   **Local LLM (Optional):**
    *   **Ollama**: (Recommended for standard local use).
    *   **ALIA (Experimental)**: Native Spanish Sovereign model (Requires High-End GPU).
    *   *Note: If you cannot run local models, please set `MISTRAL_API_KEY` for cloud generation.*

## 🚀 Quick Start

### 60-Second Demo

```python
import venturalitica as vl

# Auto-downloads UCI German Credit and runs bias audit
results = vl.quickstart('loan')
```

**Output:**
```
[📊] Loaded: UCI Dataset #144 (1000 samples)
[✅] PASSED: 3/3 fairness controls

🎉 Dataset passes bias checks!
```

### Analyze Your Own Data

First, create a **policy file** (`fairness.yaml`) that defines what to check:

```yaml
assessment-plan:
  uuid: my-policy
  metadata:
    title: "Fairness Policy"
  reviewed-controls:
    control-selections:
      - include-controls:
        - control-id: gender-check
          description: "Approval rates must be similar across genders"
          props:
            - name: metric_key
              value: demographic_parity_diff
            - name: threshold
              value: "0.10"
            - name: operator
              value: "<"
```

Then run the audit:

```python
import pandas as pd
import venturalitica as vl

df = pd.read_csv("my_data.csv")

vl.enforce(
    data=df,
    target="approved",
    gender="gender",
    policy="fairness.yaml"
)
```

## 📚 Documentation

- **[Tutorial: Zero-Setup Audit](docs/tutorials/local-audit.md)**: "Hello World" - Scan & Visualize in 2 minutes
- **[Tutorial: Training Integration](docs/training.md)**: Add compliance checks to your Python code
- **[Concept: The Regulatory Map](docs/compliance-dashboard.md)**: Understanding the Dashboard (Art 9-15)
- **[Concept: Evidence Collection](docs/evidence-collection.md)**: How to record your audits
- **[Samples Repository](https://github.com/venturalitica/venturalitica-sdk-samples)**: Real-world examples

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

Launch the **Local Regulatory Map** to interpret your evidence:

```bash
venturalitica ui
```

**[Read the Guide: Understanding the Dashboard](docs/compliance-dashboard.md)**

**Features:**
*   **Article 9-15 Walk**: A sequential check of Risk, Data, Transparency, and Oversight.
*   **Sequential Verification**: See exactly which technical artifact satisfies which legal article.
*   **Annex IV Draft**: Generate the PDF-ready markdown file with `venturalitica doc`.

**Integrates with:**
*   `bom.json` (from scanner)
*   `emissions.csv` (from CodeCarbon)
*   OSCAL policies

## 🔒 Data Sovereignty & Privacy

Venturalítica follows a strict **Local-First** architecture.

*   **No Cloud Uploads**: `vl.enforce()` and `vl.quickstart()` run entirely on your local machine. Your datasets never leave your environment.
*   **Telemetry**: Usage metrics (if enabled) are strictly metadata (e.g., performance, error rates) and contain **NO PII**.
*   **Compliance Data**: All evidence (`trace_*.json`) is stored locally in `.venturalitica/`. You own your compliance data.

## ☁️ Venturalítica Cloud (Coming Soon)

**Enterprise-grade EU AI Act & ISO 42001 compliance management**

While the SDK provides frictionless local enforcement, **Venturalítica Cloud** will offer a complete compliance lifecycle management platform for **EU AI Act** and **ISO 42001**:

### What's Coming

- **Visual Policy Builder**: Create OSCAL policies mapped to EU AI Act Articles 9-15 & ISO 42001 controls
- **Team Collaboration**: Centralized policy management across organizations
- **Compliance Dashboard**: Real-time status for EU AI Act & ISO 42001 requirements
- **Annex IV Generator**: Auto-generate complete EU AI Act technical documentation
- **Risk Assessment**: Guided workflows for high-risk AI system classification
- **Audit Trail**: Immutable compliance history for regulatory inspections
- **Integration Hub**: Connect with your existing MLOps and governance tools

### Early Access

Interested in early access to Venturalítica Cloud?
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
