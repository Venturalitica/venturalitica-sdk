# Training Tutorial

Integrate fairness and performance checks into your ML workflow.

---

## Overview

| Phase | Check | Function |
|:--|:--|:--|
| Pre-training | Data bias | `enforce(data=train_df)` |
| Post-training | Model fairness + Performance | `enforce(data=test_df, prediction=pred)` |

---

## Step 1: Load and Prepare Data

Since the German Credit dataset contains categorical strings, we must encode them before training.

```python
from ucimlrepo import fetch_ucirepo
from sklearn.model_selection import train_test_split
import pandas as pd

# Fetch UCI German Credit
dataset = fetch_ucirepo(id=144)
df = dataset.data.features.copy()
df['class'] = dataset.data.targets

# Split raw data for the audit
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

# Encode data for Scikit-Learn training
df_encoded = pd.get_dummies(df.drop(columns=['class']))
X_train, X_test, y_train, y_test = train_test_split(
    df_encoded, 
    df['class'].values.ravel(), 
    test_size=0.2, 
    random_state=42
)
```

---

## Step 2: Pre-Training Audit (Data Bias)

Check your training data for bias **before** starting the compute-heavy training phase.

```python
import venturalitica as vl

vl.enforce(
    data=train_df,
    target="class",
    gender="Attribute9",  # Gender/Status column
    age="Attribute13",    # Age column
    policy="loan-policy.yaml"
)
```

**Real Output:**
```
[Venturalitica] 🛡 Enforcing policy: loan-policy.yaml
  ❌ FAIL | Controls: 2/3 passed
    ✓ [imbalance] Minority ratio... 0.429 (Limit: >0.2)
    ✓ [gender-bias] Disparate impact... 0.818 (Limit: >0.8)
    ✗ [age-bias] Age disparity... 0.286 (Limit: >0.5)
```

---

## Step 3: Train and Evaluate

```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Get predictions on test set
predictions = model.predict(X_test)
```

---

## Step 4: Post-Training Audit (Fairness + Performance)

Audit the model's behavior on unseen data.

```python
# Create audit dataframe (raw features + predictions)
test_audit_df = df.iloc[test_df.index].copy()
test_audit_df['prediction'] = predictions

vl.enforce(
    data=test_audit_df,
    target="class",
    prediction="prediction",
    gender="Attribute9",
    age="Attribute13",
    policy="loan-policy.yaml"
)
```

**Real Output:**
```
[Venturalitica] 🛡 Enforcing policy: loan-policy.yaml
  ❌ FAIL | Controls: 1/3 passed
    ✓ [imbalance] Minority ratio... 0.418 (Limit: >0.2)
    ✗ [gender-bias] Disparate impact... 0.703 (Limit: >0.8)
    ✗ [age-bias] Age disparity... 0.000 (Limit: >0.5)
```

> [!WARNING]
> While the training data passed the Gender check (0.81), the model amplified the bias in its predictions (0.70). This is a clear signal to retrain with fairness constraints.

> [!IMPORTANT]
> **Why 0.286 vs 1.000?** 
> If you see a perfect `1.000` but expect bias, check your column binding. If a column is missing or mismatched, Venturalitica may default to 1.0. Always verify your column names (like `Attribute9` vs `gender`) in the `enforce()` call.

---

## Step 5: Including Performance Metrics

It makes perfect sense to audit performance alongside fairness. If you "fix" bias but destroy the model's utility (e.g., 20% accuracy), the system is still failing.

You can define performance thresholds in the same policy:

```yaml
- control-id: accuracy-threshold
  description: "Model must achieve at least 75% accuracy"
  props:
    - name: metric_key
      value: accuracy
    - name: threshold
      value: "0.75"
    - name: operator
      value: gt
```

Venturalitica supports: `accuracy`, `precision`, `recall`, and `f1`.
