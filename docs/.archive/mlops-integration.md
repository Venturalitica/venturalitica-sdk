# MLOps Integrations

Venturalitica SDK is designed to fit seamlessly into your existing machine learning workflow. It automatically detects and logs governance results to popular MLOps frameworks.

## Automatic Framework Detection

When you call `enforce()`, the SDK checks for active runs in common MLOps tools and automatically logs metrics, tags, and reports.

## MLflow Integration

If you have an active MLflow run, the SDK will log compliance results as metrics and tags.

```python
import mlflow
from venturalitica import enforce

mlflow.start_run()

# Your training code
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

### What gets logged to MLflow:
- **Metrics**: `governance.{control_id}.score` (1.0 for PASS, 0.0 for FAIL)
- **Tags**: `governance.{control_id}` (set to "PASS" or "FAIL")
- **Tags**: `governance.overall` (set to "PASS" or "FAIL")
- **Artifacts**: `governance_report.md` (the full markdown compliance report)

---

## Weights & Biases (WandB) Integration

```python
import wandb
from venturalitica import enforce

wandb.init(project="loan-fairness")

# Your training code
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

### What gets logged to WandB:
- **Metrics**: `governance.{control_id}.score`
- **Summary**: `governance.{control_id}` (PASS/FAIL status)
- **Summary**: `governance.overall` (overall status)
- **Artifacts**: `governance_report` (the full markdown report saved as a run artifact)

---

## ClearML Integration

```python
from clearml import Task
from venturalitica import enforce

task = Task.init(project_name="loan-fairness", task_name="training")

# Your training code
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

### What gets logged to ClearML:
- **Tags**: `governance.{control_id}:PASS/FAIL`
- **Tags**: `governance.overall:PASS/FAIL`
- **Console Logs**: The full governance report is printed to the task's console log.

## Selective Logging

If you want to disable automatic logging for a specific run, you can pass `log_to_mlops=False` to the `enforce()` function:

```python
enforce(..., log_to_mlops=False)
```
