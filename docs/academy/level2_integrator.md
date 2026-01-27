# Level 2: The Integrator (MLOps & Visibility) 🟡

**Goal**: Move compliance from "Local Machine" to "Shared Metadata".

**Prerequisite**: [Level 1 (The Engineer)](level1_policy.md)

**Scenario**: `loan-credit-scoring` (Continuing with the clean setup).

---

## 1. The Bottleneck: "It works on my machine"

In Level 1, you fixed the bias locally. But your manager denies it because they can't see the proof.
Emails with screenshots are **not compliance**.

## 2. The Solution: Compliance as Metadata

We will treat Compliance exactly like Accuracy or Loss: as a metric to be logged.

### A. The Dashboard (Visual Verification)

Before we automate, let's see what we are shipping.

1.  **Run the UI**:
    ```bash
    uv run venturalitica ui
    ```
2.  **Navigate to "Evidence Graph"**: See your `trace.json` visualized.
3.  **Check "Policy Status"**: Confirm your "Risk Treatment" (the adjusted threshold) is recorded.

**Key Insight**: "The report looks professional, and I didn't write a single word of it."

![Evidence Graph](../assets/academy/dashboard_overview.png)

---

## 3. The Integration: MLflow / WandB

Now, let's make this automatic for every run.

### Step 1: Choose Your Tracker

Compliance data matches your existing workflow.

=== "MLflow"

    ```python
    import mlflow
    import venturalitica as vl

    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("loan-credit-scoring")

    with mlflow.start_run():
        # ... training code ...
        # model = train(X_train, y_train)
        
        # Run Audit on PREDICTIONS
        results = vl.enforce(
            data=X_test.assign(prediction=model.predict(X_test)),
            target="prediction",  # 🧠 MAPPING SHIFT: Now checking the Model, not just Data
            gender="gender",
            policy="my_policy.yaml"
        )
        
        # Log Compliance as Metrics
        mlflow.log_dict(results.to_dict(), "compliance_trace.json")
        mlflow.log_metric("compliance_score", 1.0 if results.passed else 0.0)
        
        if not results.passed:
            print("❌ Model is Biased. Do not deploy.")
    ```

### 🧠 Deep Dive: Variable Mapping (The "Integrator" Handshake)
Notice the subtle change in the code above:
- **Level 1 (Data Audit)**: `target="class"` (Checking Ground Truth)
- **Level 2 (Model Audit)**: `target="prediction"` (Checking AI Behavior)

### 🍃 Green AI & Oversight (Article 15)

The EU AI Act requires human oversight of resources. Use `vl.monitor()` to track energy and hardware automatically.

```python
# 1. Start the Monitor (Green AI)
with vl.monitor("training_run_v1"):
    model.fit(X_train, y_train)
# Automatically logs CO2, RAM, and GPU usage.
```

The Policy (`> 0.5`) stayed the same. The **Mapping** changed.
This is the power of decoupling Law from Code. You use the *same standard* to test the Raw Data (Engineering) and the Trained Model (MLOps).

=== "Weights & Biases"

    ```python
    import wandb
    import venturalitica as vl

    wandb.init(project="loan-credit-scoring")

    # ... training code ...

    # Run Audit
    audit = vl.scan(project_root=".")

    # Log Compliance as Artifacts
    artifact = wandb.Artifact('compliance-trace', type='compliance')
    artifact.add_file(".venturalitica/trace_latest.json")
    wandb.log_artifact(artifact)
    
    wandb.log({"compliance_score": 1.0 if audit.passed else 0.0})
    ```

## 4. The Gate (CI/CD)

If `compliance_score == 0`, the build fails.
GitLab CI / GitHub Actions can now block a deployment based on ethics, just like they block on syntax errors.

---

## 5. Take Home Messages 🏠

1.  **Compliance is Metadata**: It belongs in your experiment tracker (`mlruns`), not in a PDF on your desktop.
2.  **Visibility creates Trust**: By logging the `trace.json`, you prove *exactly* which policy version was used.
3.  **Zero Friction**: The Data Scientist doesn't change their workflow. They just add 2 lines of logging.

👉 **[Next: Level 3 (The Auditor & Vision)](level3_auditor.md)**
