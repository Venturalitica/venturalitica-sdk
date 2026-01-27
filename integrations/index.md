# MLOps Integrations (The Ops Guide)

This guide focuses on the **MLOps Persona**: the one who automates the pipeline. Venturalítica integrates strictly with your existing tools to ensure that **Evidence (Article 12)** is automatically collected during your CI/CD runs.

______________________________________________________________________

## The Concept

We do not want to replace your MLOps stack. We want to **certify** it.

| Tool                 | Integration        | Benefit                                                              |
| -------------------- | ------------------ | -------------------------------------------------------------------- |
| **MLflow / WandB**   | `vl.wrap()`        | Automatically links Policy `model_policy.yaml` to the run artifacts. |
| **Status Dashboard** | `venturalitica ui` | Provides "Traffic Light" health checks for your compliance pipeline. |

______________________________________________________________________

## 1. Regulatory Versioning

Every time you train a model using `vl.wrap()` or `vl.monitor()`, Venturalítica automatically snapshots your governance policy (`model_policy.yaml`) and uploads it to your active tracking server.

- **Why?** Ensures that your audit trail is strictly reproducible. You can prove exactly *which* rules were active during training (e.g., "Policy v1.2 vs v1.3").
- **Where?** Look for `policy_snapshot` in your MLflow artifacts or WandB files.

______________________________________________________________________

## 2. Setup Guide

### Weights & Biases (Cloud)

Venturalítica automatically detects `wandb` runs.

1. **Configure**: Set `WANDB_API_KEY` in your `.env`.
1. **Run**: Just use `vl.wrap(model)` inside your script.
1. **Verify**: Open `venturalitica ui` -> **Integrations**.

### MLflow (Local/Remote)

Compatible with both local `mlruns` and remote Tracking Servers.

1. **Configure**: Set `MLFLOW_TRACKING_URI` (optional, defaults to `./mlruns`).
1. **Run**: Ensure `mlflow.start_run()` is active when you call `fit()`.
1. **Verify**: The UI will generate deep links to your specific Experiment and Run ID.

______________________________________________________________________

## 3. Example (Loan Scenario)

Here is how you automate the **Article 15 Audit** inside a standard pipeline.

```
import venturalitica as vl
import mlflow
from sklearn.ensemble import RandomForestClassifier

# 1. Define Policy (The Standard)
policy = "model_policy.yaml"

# 2. Start MLOps Run
with mlflow.start_run():

    # 3. Transparent Wrapping (The Governance Layer)
    # This automatically captures the 'model_policy.yaml' snapshot
    model = vl.wrap(RandomForestClassifier(), policy=policy)

    # 4. Train (Evidence & Artifacts auto-uploaded)
    model.fit(
        X_train, y_train,
        audit_data=train_df,
        gender="Attribute9",  # Strict mapping for audit
        age="Attribute13"
    )
```
