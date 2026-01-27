# Evidence Collection: The Black Box Recorder

While **Policies** (the Enforcer) stop bad models from reaching production, **Evidence Collection** (the Recorder) ensures you can prove exactly what happened during training. This is your "Black Box" flight recorder for AI.

In Venturalítica, evidence collection is distinct from policy enforcement. You can record evidence without blocking a deployment, or enforce strictly without saving traces. However, for full EU AI Act compliance (Article 12: Record-Keeping), you need both.

## Two Ways to Record

### 1. The Automatic Wrapper (`vl.wrap`)

The easiest way to collect evidence is to wrap your estimator. This automatically hooks into `.fit()` and `.predict()` to capture inputs, outputs, and metadata.

```
import venturalitica as vl
from sklearn.ensemble import RandomForestClassifier

# 1. Wrap the model
model = vl.wrap(RandomForestClassifier(), policy="model_policy.yaml")

# 2. Train as usual (Evidence is auto-collected)
model.fit(X_train, y_train, audit_data=train_df, gender="Attribute9")
```

**What is recorded?** * **Timestamp**: Precise start/end times. * **Model Config**: Hyperparameters (`n_estimators`, `max_depth`, etc.). * **Data Shape**: Number of rows/columns used. * **Code Context**: The filename and AST analysis of the script that called `fit`.

### 2. The Multimodal Monitor (`vl.monitor`)

For custom training loops (e.g., PyTorch, TensorFlow) or complex pipelines where `fit()` isn't enough, use the context manager.

```
import venturalitica as vl

# Start the recording session
with vl.monitor("training_run_v1"):
    # Your custom logic here
    model = train_custom_model(data)
    evaluate_model(model)

# Evidence is saved to .venturalitica/trace_training_run_v1.json
```

## Where does the evidence go?

All evidence is secured locally in the `.venturalitica/` directory:

- **`results.json`**: The outcome of your policy audits (Pass/Fail).
- **`trace_{name}.json`**: The execution metadata (timestamps, code analysis).
- **`bom.json`**: The software supply chain inventory (dependencies).

## Compliance Impact

For **Article 12 (EU AI Act)**, this evidence is mandatory. The Venturalítica Dashboard reads these files to prove:

1. **Traceability**: "We know exactly which code and data produced Model v1.0."
1. **Integrity**: "The evidence has not been tampered with" (via SHA-256 anchoring).

View Your Traces

After running your training script, launch the dashboard (`venturalitica ui`) to visualize these traces in the **Article 12** section.
