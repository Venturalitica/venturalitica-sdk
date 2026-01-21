# 5-Minute Quickstart

**Goal**: Enforce your first governance policy in < 5 minutes.

This quickstart is designed to give you an **Aha! Moment** in under 5 minutes with zero friction.

---

## Step 1: Install (30 seconds)

```bash
pip install venturalitica-sdk
```

That's it. No config files, no setup wizards.

---

## Step 2: Get a Sample Policy (30 seconds)

Download a pre-made OSCAL policy:

```bash
curl -O https://raw.githubusercontent.com/venturalitica/venturalitica-sdk-samples/main/policies/loan/risks.oscal.yaml
```

Or use this minimal example (`risks.oscal.yaml`):

```yaml
assessment-plan:
  uuid: quickstart-policy
  metadata:
    title: "Quickstart Fairness Policy"
  reviewed-controls:
    control-selections:
      - include-controls:
        - control-id: accuracy-check
          description: "Model must achieve at least 80% accuracy"
          props:
            - name: metric_key
              value: accuracy
            - name: threshold
              value: "0.80"
            - name: operator
              value: ">="
```

---

## Step 3: Enforce in Your Training Script (2 minutes)

Add **one line** to your existing training code:

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
import venturalitica as vl  # ← Add this

# Your existing training code
X, y = make_classification(n_samples=1000, n_features=20, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = RandomForestClassifier()
model.fit(X_train, y_train)

# ← Add this one line
vl.enforce(
    metrics={"accuracy": model.score(X_test, y_test)},
    policy="risks.oscal.yaml"
)
```

---

## Step 4: Run and See the Magic (1 minute)

```bash
python train.py
```

**Output:**

```
[Venturalitica] 🛡  Enforcing policy: risks.oscal.yaml

Evaluating Control 'accuracy-check': Model must achieve at least 80% accuracy
  ✓ PASS: accuracy = 0.85 >= 0.80

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Compliance Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ PASSED: 1/1 controls
Policy: Quickstart Fairness Policy
```

---

## 🎉 Aha! Moment

You just:
1. ✅ Enforced a governance policy
2. ✅ Got an educational audit log
3. ✅ Didn't change your workflow

**Time elapsed**: ~4 minutes

---

## What Just Happened?

The SDK:
1. Loaded your OSCAL policy (`risks.oscal.yaml`)
2. Evaluated your accuracy metric against the threshold
3. Printed a human-readable compliance report
4. **Auto-logged to MLflow/WandB/ClearML** (if you're using them)

**Zero config. Zero friction.**

---

## Next Steps

### Option A: Add More Metrics (Developer Path)

```python
from sklearn.metrics import precision_score, recall_score

predictions = model.predict(X_test)

vl.enforce(
    metrics={
        "accuracy": model.score(X_test, y_test),
        "precision": precision_score(y_test, predictions),
        "recall": recall_score(y_test, predictions)
    },
    policy="risks.oscal.yaml"
)
```

### Option B: Auto-Compute Metrics (Even Easier)

Let the SDK compute metrics for you:

```python
import pandas as pd

# Convert to DataFrame
df_test = pd.DataFrame(X_test)
df_test['target'] = y_test

vl.enforce(
    data=df_test,
    target='target',
    prediction=model.predict(X_test),
    policy="risks.oscal.yaml"
)
```

The SDK will automatically compute:
- Accuracy
- Precision
- Recall
- F1-Score

### Option C: Add Fairness Checks

```python
# Add a protected attribute
df_test['gender'] = ['M', 'F'] * (len(df_test) // 2)

vl.enforce(
    data=df_test,
    target='target',
    prediction=model.predict(X_test),
    gender='gender',  # ← Semantic binding
    policy="fairness-policy.oscal.yaml"
)
```

Now the SDK will also check:
- Demographic Parity
- Equal Opportunity
- Disparate Impact (80% Rule)

---

## 🔥 Power User Tip: MLOps Auto-Logging

If you're using MLflow, WandB, or ClearML, the SDK **automatically logs** compliance results:

```python
import mlflow

mlflow.start_run()

# SDK auto-logs to MLflow
vl.enforce(
    metrics={"accuracy": model.score(X_test, y_test)},
    policy="risks.oscal.yaml"
)

mlflow.end_run()
```

**What gets logged:**
- Metrics: `governance.accuracy-check.score = 1.0`
- Tags: `governance.accuracy-check = PASS`
- Artifact: `governance_report.md`

**Zero extra code.**

---

## 📚 What's Next?

You've completed the quickstart! Choose your next tutorial:

- **[MLOps Integration](mlops-integration.md)** - Deep dive into MLflow/WandB/ClearML
- **[Green AI Guide](green-ai.md)** - Add carbon footprint tracking
- **[Core Concepts](core-concepts.md)** - Understand Role-Based Binding
- **[OSCAL Authoring](oscal-authoring.md)** - Write custom policies

