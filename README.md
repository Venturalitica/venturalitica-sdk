# Venturalitica SDK

**Frictionless Governance for AI Systems.**

This SDK allows Data Scientists and ML Engineers to integrate Compliance and Risk Management directly into their workflow, enforcing policies defined in **OSCAL** standard.

## Features
- **Governance as Code**: Define policies in `risks.oscal.yaml`.
- **Frictionless Integration**: Works with `sklearn`, `pytorch`, `pandas`.
- **Green AI**: Track training carbon footprint with `codecarbon` integration.
- **MLOps Agnostic**: Native adapters for **MLflow** and **Weights & Biases**.
- **Local Compliance Assistant**: A CLI/UI to manage technical documentation locally.

## Installation
```bash
pip install venturalitica-sdk
# with metric support
pip install "venturalitica-sdk[metrics]"
# with Green AI support
pip install "venturalitica-sdk[green]"
```

## Quick Start (CLI)
Venturalitica includes a local dashboard to help you generate Technical Documentation (EU AI Act Annex IV).

1. **Scan your project**
   ```bash
   venturalitica scan --target ./my-project
   ```
   This generates a `bom.json` (CycloneDX) with your dependencies and detected models.

2. **Launch the Dashboard**
   ```bash
   venturalitica ui
   ```
   Open `http://localhost:8501`. You will see three tabs:
   - **Technical Check**: Validates code, metrics, and **Carbon Footprint**.
   - **Governance**: Shows high-level risks (requiring mitigation).
   - **Documentation**: Generates the Technical Declaration draft.

## Python API
```python
from venturalitica import enforce

# In your training script
accuracy = 0.95
enforce(
    metrics={"accuracy": accuracy},
    policy_path="risks.oscal.yaml"
)
```
