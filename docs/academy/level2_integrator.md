# Level 2: The Integrator (GovOps & Visibility) 🟡

**Goal**: Transform MLOps artifacts into Regulatory Evidence with a **GovOps** layer.

**Prerequisite**: [Level 1 (The Engineer)](level1_policy.md)

**Scenario**: `loan-credit-scoring` (Continuing with the clean setup).

---

## 1. The Bottleneck: "It works on my machine"

In Level 1, you fixed the bias locally. But your manager denies it because they can't see the proof.
Emails with screenshots are **not compliance**.

## 2. The Solution: The GovOps Layer

In **GovOps** (Governance over MLOps), we don't treat compliance as a separate manual step. Instead, we use your existing MLOps infrastructure (MLflow, WandB) as an **Evidence Buffer** that automatically harvests the proof of safety during the training process.

### A. The Dashboard (Visual Verification)

Before we automate, let's see what we are shipping.

1.  **Run the UI**:
    ```bash
    uv run venturalitica ui
    ```
2.  **Log Check**: Verify that `.venturalitica/results.json` exists (this is the default output of `enforce`).
3.  **Navigate to "Policy Status"**: Confirm your "Risk Treatment" (the adjusted threshold) is recorded.

**Key Insight**: "The report looks professional, and I didn't write a single word of it."

![Evidence Graph](../assets/academy/dashboard_overview.png)

---

## 3. The Integration: Continuous Governance

In a professional pipeline, governance is a layer that wraps your training. Every time you train a model, you verify its compliance.

### Step 1: Orchestrate Your Workflow

Your experiment tracker now tracks two types of performance: **Accuracy** (Operational) and **Compliance** (Regulatory).

=== "MLflow"

    ```python
    import mlflow
    import venturalitica as vl
    from dataclasses import asdict

    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("loan-credit-scoring")

    # 1. Start the GovOps Session
    with mlflow.start_run(), vl.monitor("train_v1"):
        # 2. Train your model
        # model.fit(X_train, y_train)
        
        # 3. Capture the 'Glass Box' Evidence
        with vl.tracecollector("compliance_audit"):
            results = vl.enforce(
                data=X_test.assign(prediction=model.predict(X_test)),
                target="prediction",
                gender="gender",
                policy="my_policy.yaml"
            )
        
        # 4. Log everything to the Evidence Buffer
        passed = all(r.passed for r in results)
        mlflow.log_metric("val_accuracy", 0.92)
        mlflow.log_metric("compliance_score", 1.0 if passed else 0.0)
        mlflow.log_dict([asdict(r) for r in results], "compliance_results.json")
        
        if not passed:
            print("❌ Model is Biased. Audit Trace generated.")
    ```

    > **Note**: `vl.monitor()` automatically logs CO2, RAM, and GPU usage to your trace, fulfilling **Article 15 (Efficiency)** requirements.

=== "Weights & Biases"

    ```python
    import wandb
    import venturalitica as vl

    wandb.init(project="loan-credit-scoring")

    # 1. Monitor & Train
    with vl.monitor("production_run"):
        # model.fit(X_train, y_train)
        pass

    # 2. Run Enforce with Trace Capture
    with vl.tracecollector("wandb_sync"):
        audit = vl.enforce(
            data=pd.read_csv("val_data.csv"),
            policy="my_policy.yaml",
            target="prediction"
        )

    # 3. Log Compliance Artifacts
    artifact = wandb.Artifact('compliance-bundle', type='evidence')
    artifact.add_file(".venturalitica/results.json")
    artifact.add_file(".venturalitica/trace_wandb_sync.json")
    wandb.log_artifact(artifact)
    
    passed = all(r.passed for r in audit)
    wandb.log({"accuracy": 0.89, "compliance": 1.0 if passed else 0.0})
    ```

### 🧠 Deep Dive: Variable Mapping (The "Integrator" Handshake)
Notice the subtle change in the code above:

- **Level 1 (Data Audit)**: `target="class"` (Checking Ground Truth)
- **Level 2 (Model Audit)**: `target="prediction"` (Checking AI Behavior)

The Policy (`> 0.5`) stayed the same. The **Mapping** changed.
This is the power of decoupling Law from Code. You use the *same standard* to test the Raw Data (Engineering) and the Trained Model (MLOps).


## 4. The Gate (CI/CD)

If `compliance_score == 0`, the build fails.
GitLab CI / GitHub Actions can now block a deployment based on ethics, just like they block on syntax errors.

---

## 5. Take Home Messages 🏠

1.  **GovOps is Native**: Governance isn't an extra step; it's a context manager (`vl.monitor`, `vl.tracecollector`) around your training.
2.  **Telemetry is Evidence**: RAM, CO2, and Hardware stats are not just for cost—they fulfill **Article 15** oversight requirements.
3.  **The Trace File**: Always log the `.json` results to your experiment tracker. It is the raw evidence for your future Technical Documentation.
4.  **Zero Friction**: The Data Scientist continues to use MLflow/WandB. Venturalítica just harvests the evidence behind the scenes.

👉 **[Next: Level 3 (The Auditor & Vision)](level3_auditor.md)**
