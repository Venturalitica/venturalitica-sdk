# Deep Integrations (Glass Box v2.0)

Venturalítica v0.4.0 introduces **Deep Integrations**, designed to make AI Governance a seamless part of your existing MLOps workflow. We call this "Glass Box 2.0": complete visibility into both the code and the regulatory artifacts that governed it.

## Features

### 1. Regulatory Versioning
Every time you train a model using `vl.wrap()`, Venturalítica automatically snapshots your governance policy (`oscal.yaml`) and uploads it to your active tracking server.

-   **Why?** Ensures that your audit trail is strictly reproducible. You can prove exactly *which* rules were active during training.
-   **Where?** Look for `policy_snapshot` in your MLflow artifacts or WandB files.

### 2. Integrations Status Tab
The new **Integrations** tab in `venturalitica ui` provides a real-time health check of your governance ecosystem.

-   **Traffic Light System**: Instantly see if your local MLflow or Cloud WandB are connected.
-   **Deep Links**: One-click navigation to the *exact* run in your MLOps tool that produced the evidence.

## Setup

### Weights & Biases (Cloud)
Venturalítica automatically detects `wandb` runs.

1.  **Configure**: Set `WANDB_API_KEY` in your `.env`.
2.  **Run**: Just use `vl.wrap(model)` inside your script.
3.  **Verify**: Open `venturalitica ui` -> **Integrations**.

### MLflow (Local/Remote)
Compatible with both local `mlruns` and remote Tracking Servers.

1.  **Configure**: Set `MLFLOW_TRACKING_URI` (optional, defaults to `./mlruns`).
2.  **Run**: Ensure `mlflow.start_run()` is active when you call `fit()`.
3.  **Verify**: The UI will generate deep links to your specific Experiment and Run ID.

## Example

```python
import venturalitica as vl
import mlflow

# 1. Define Policy
policy = "risks.oscal.yaml"

# 2. Start MLOps Run
with mlflow.start_run():
    # 3. Transparent Wrapping
    model = vl.wrap(RandomForestClassifier(), policy=policy)
    
    # 4. Train (Artifacts auto-uploaded)
    model.fit(X_train, y_train) 
```
