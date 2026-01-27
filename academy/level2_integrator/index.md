# Level 2: The Integrator (GovOps & Visibility) 🟡

**Goal**: Transform MLOps artifacts into Regulatory Evidence with a **GovOps** layer.

**Prerequisite**: [Level 1 (The Engineer)](https://venturalitica.github.io/venturalitica-sdk/academy/level1_policy/index.md)

**Context**: Continuing with "The Project" (Loan Credit Scoring).

______________________________________________________________________

## 1. The Bottleneck: "It works on my machine"

In Level 1, you fixed the bias locally. But your manager denies it because they can't see the proof. Emails with screenshots are **not compliance**.

## 2. The Solution: The GovOps Layer

In **GovOps** (Governance over MLOps), we don't treat compliance as a separate manual step. Instead, we use your existing MLOps infrastructure (MLflow, WandB) as an **Evidence Buffer** that automatically harvests the proof of safety during the training process.

### A. The Integration (Implicit Governance)

In a professional pipeline, governance is a layer that wraps your training. Every time you train a model, you verify its compliance.

Your experiment tracker now tracks two types of performance: **Accuracy** (Operational) and **Compliance** (Regulatory).

```
import mlflow
import venturalitica as vl
from dataclasses import asdict

mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("loan-credit-scoring")

# 1. Start the GovOps Session (Implicitly captures 'Audit Trace')
with mlflow.start_run(), vl.monitor("train_v1"):
    # 2. Train your model
    # model.fit(X_train, y_train)

    # 3. Enforce Compliance (Article 15: Human Oversight)
    results = vl.enforce(
        data=X_test.assign(prediction=model.predict(X_test)),
        target="prediction",               # 🧠 Checking Model Behavior
        gender="gender",
        policy="model_policy.yaml"         # 🗝️ New policy for Model Governance
    )

    # 4. Log everything to the Evidence Buffer
    passed = all(r.passed for r in results)
    mlflow.log_metric("val_accuracy", 0.92)
    mlflow.log_metric("compliance_score", 1.0 if passed else 0.0)
    mlflow.log_dict([asdict(r) for r in results], "compliance_results.json")

    if not passed:
        # 🛑 CRITICAL: Block the pipeline if the model is unethical
        raise ValueError("Model failed ISO 42001 compliance check. See audit trace.")
```

> **Note**: `vl.monitor()` now captures **Multimodal Evidence**: hardware/carbon metrics AND the logical execution trace (AST code story).

```
import wandb
import venturalitica as vl

wandb.init(project="loan-credit-scoring")

# 1. Open a Monitor Context
with vl.monitor("wandb_sync"):
    # model.fit(X_train, y_train)

    # 2. Run Enforce (Article 15)
    audit = vl.enforce(
        data=pd.read_csv("val_data.csv"),
        policy="model_policy.yaml",
        target="prediction"
    )

# 3. Log Compliance Artifacts
artifact = wandb.Artifact('compliance-bundle', type='evidence')
artifact.add_file(".venturalitica/results.json")
artifact.add_file(".venturalitica/trace_wandb_sync.json")
wandb.log_artifact(artifact)

passed = all(r.passed for r in audit)
wandb.log({"accuracy": 0.89, "compliance": 1.0 if passed else 0.0})

if not passed:
    raise ValueError("Model rejected by GovOps policy.")
```

### B. The Verification (Dashboard)

Now that the code has run, let's verify what we shipped.

1. **Run the UI**:

   ```
   uv run venturalitica ui
   ```

1. **Log Check**: Verify that `.venturalitica/results.json` exists (this is the default output of `enforce`).

1. **Navigate to "Policy Status"**: Confirm your "Risk Treatment" (the adjusted threshold) is recorded.

**Key Insight**: "The report looks professional, and I didn't write a single word of it."

______________________________________________________________________

## 3. Deep Dive: The Two-Policy Handshake (Art 10 vs 15)

Professional GovOps requires a separation of concerns. You are now managing two distinct governance layers:

1. **Level 1 (Article 10)**: Checked the **Raw Data** against `data_policy.yaml`. The goal was to prove the dataset itself was fair before wasting energy on training.
1. **Level 2 (Article 15)**: Checks the **Model Behavior** against `model_policy.yaml`. The goal is to prove the AI makes fair decisions in a "Glass Box" execution.

| Stage           | Variable Mapping      | Policy File         | Mandatory Requirement            |
| --------------- | --------------------- | ------------------- | -------------------------------- |
| **Data Audit**  | `target="class"`      | `data_policy.yaml`  | **Article 10** (Data Governance) |
| **Model Audit** | `target="prediction"` | `model_policy.yaml` | **Article 15** (Human Oversight) |

This decoupling is the core of the **Handshake**. Even if the Law (`> 0.5`) stays the same, the *subject* of the law changes from **Data** to **Math**.

## 4. The Gate (CI/CD)

If `compliance_score == 0`, the build fails. GitLab CI / GitHub Actions can now block a deployment based on ethics, just like they block on syntax errors.

______________________________________________________________________

## 5. Take Home Messages 🏠

1. **GovOps is Native**: Governance isn't an extra step; it's a context manager (`vl.monitor`) around your training.
1. **Telemetry is Evidence**: RAM, CO2, and Trace results are not just for metrics—they fulfill **Article 15** oversight.
1. **Unified Trace**: `vl.monitor()` captures everything from hardware usage to AST code analysis in a single `.json` file.
1. **Zero Friction**: The Data Scientist continues to use MLflow/WandB, while the SDK harvests the evidence.

👉 **[Next: Level 3 (The Auditor)](https://venturalitica.github.io/venturalitica-sdk/academy/level3_auditor/index.md)**
