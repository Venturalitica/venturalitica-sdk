# Venturalítica SDK

![coverage](https://img.shields.io/badge/coverage-73%25-yellow)
[![PyPI](https://img.shields.io/pypi/v/venturalitica)](https://pypi.org/project/venturalitica/)
[![Python](https://img.shields.io/pypi/pyversions/venturalitica)](https://pypi.org/project/venturalitica/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
[![Discord](https://img.shields.io/discord/P4RURqRm?label=Discord&logo=discord)](https://discord.gg/P4RURqRm)

**Frictionless Governance for AI Systems.**

The Venturalítica SDK enables Data Scientists and ML Engineers to integrate compliance and risk management directly into their training workflows. Built on the **OSCAL** (Open Security Controls Assessment Language) standard, it provides semantic policy enforcement with educational audit trails.

**[Join our Discord community](https://discord.gg/P4RURqRm)** — Get help, share your use case, and discuss EU AI Act compliance with other engineers.

## ✨ Key Features

- **Glass Box Governance**: Sequential regulatory mapping (Art 9-15) for total transparency.
- **Strict Mode**: Auto-enforcement of compliance checks in CI/CD environments.
- **Deep Provenance**: Trace data lineage across Files, SQL, and S3 using `ArtifactProbe`.
- **Local Sovereignty**: Zero-cloud dependency. All enforcement runs locally.
- **TraceCollector Architecture**: Unified evidence gathering for BOM, metrics, anlogs.
- **Educational Audits**: Control descriptions that explain *why* metrics matter.
- **Deep Integrations**: Seamless "Glass Box" syncing with MLflow & WandB.
- **OSCAL-Native**: Policy-as-Code using standard NIST formats.
- **Annex IV Ready**: Auto-draft technical documentation from local traces.

## 📦 Installation

```bash
pip install venturalitica
```

## ⚙️ Configuration

The SDK supports the following Environment Variables. We recommend using a `.env` file (but **never commit it**!).

| Variable | Description | Default | Required? |
| :--- | :--- | :--- | :--- |
| `MISTRAL_API_KEY` | [Get a Free Key](https://console.mistral.ai/). Used for Cloud Fallback if local Ollama fails. | None | **Recommended** |
| `VENTURALITICA_LLM_PRO` | Set to `true` to use Mistral even if Ollama is available (Higher Quality). | `false` | No |
| `VENTURALITICA_STRICT` | Set to `true` to enforce strict compliance checks (fail on missing metrics). | `false` | No |
| `MLFLOW_TRACKING_URI` | If set, `monitor()` will auto-log audits to MLflow. | None | No |

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

- **[Quickstart Guide](docs/quickstart.md)**: Get started in 60 seconds
- **[Full Lifecycle Walkthrough](docs/full-lifecycle.md)**: Zero to Annex IV in one page
- **[Policy Authoring](docs/policy-authoring.md)**: Write OSCAL policies for your AI systems
- **[Compliance Dashboard](docs/dashboard.md)**: Understanding the Glass Box Dashboard (Art 9-15)
- **[Evidence Probes](docs/probes.md)**: Automated evidence collection for audits
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

### BOM & Supply Chain

The SDK automatically generates a **CycloneDX ML-BOM** during execution via `vl.monitor()`.

**Detects:**
- Python dependencies (`requirements.txt`, `pyproject.toml`)
- ML models (scikit-learn, PyTorch, TensorFlow, XGBoost, etc.)
- MLOps frameworks (MLflow, WandB, ClearML)

**Output:** `bom` key within your audit trace JSON.

### Compliance Dashboard

Launch the **Local Regulatory Map** to interpret your evidence:

```bash
venturalitica ui
```

**[Read the Guide: Understanding the Dashboard](docs/dashboard.md)**

**Features:**
*   **Article 9-15 Walk**: A sequential check of Risk, Data, Transparency, and Oversight.
*   **Sequential Verification**: See exactly which technical artifact satisfies which legal article.
*   **Annex IV Draft**: Generate the PDF-ready markdown file with `venturalitica doc`.

**Integrates with:**
*   `trace_*.json` (from `vl.monitor()`)
*   `emissions.csv` (from CodeCarbon)
*   OSCAL policies



## 📡 Telemetry & Privacy

Venturalítica collects **anonymous usage data** to help us improve the SDK.
- **What we track**: Command usage (`login`, `pull`, `push`), SDK execution times, and errors.
- **What we DO NOT track**: Your datasets, PII, IP addresses, or any code content.
- **Privacy First**: We host our analytics in the **EU** and strictly disable IP tracking (`disable_geoip=True`).

**Opt-Out:**
To disable telemetry completely, set the environment variable:
```bash
export VENTURALITICA_NO_ANALYTICS=1
```
Or follow the standard [DO_NOT_TRACK](https://consoledonottrack.com/) specification.

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
- **Join the waitlist**: [www.venturalitica.ai](http://www.venturalitica.ai) *(coming soon)*
- **Enterprise inquiries**: [Contact us](http://www.venturalitica.ai) for pilot programs

The SDK will always remain **free and open-source** under Apache 2.0. The cloud platform will offer additional enterprise features for teams managing EU AI Act and ISO 42001 compliance at scale.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md).

## 📄 License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## 🔗 Links

- [Samples Repository](https://github.com/venturalitica/venturalitica-sdk-samples)
- [Documentation](docs/)
- [OSCAL Standard](https://pages.nist.gov/OSCAL/)
