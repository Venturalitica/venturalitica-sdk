# Training Tutorial

Integrate fairness and performance checks into your ML workflow.

---

## Overview

| Phase | Check | Function |
|:--|:--|:--|
| Pre-training | Data bias | `enforce(data=train_df)` |
| Post-training | Model fairness + Performance | `enforce(data=test_df, prediction=pred)` |

---

## Step 1: Load Data

```python
from ucimlrepo import fetch_ucirepo
from sklearn.model_selection import train_test_split

# Fetch UCI German Credit
dataset = fetch_ucirepo(id=144)
df = dataset.data.features.copy()
df['class'] = dataset.data.targets

# Split
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
X_train = train_df.drop(columns=['class'])
y_train = train_df['class']
X_test = test_df.drop(columns=['class'])
y_test = test_df['class']
```

---

## Step 2: Pre-Training Audit (Data Bias)

Check training data for bias **before** you train:

```python
import venturalitica as vl

vl.enforce(
    data=train_df,
    target="class",
    gender="Attribute9",
    policy="data-policy.yaml"
)
```

### data-policy.yaml

```yaml
assessment-plan:
  uuid: data-bias-policy
  metadata:
    title: "Training Data Quality"
  reviewed-controls:
    control-selections:
      - include-controls:
        - control-id: class-balance
          description: "Minority class must be >20%"
          props:
            - name: metric_key
              value: minority_ratio
            - name: threshold
              value: "0.2"
            - name: operator
              value: ">"
        - control-id: gender-disparate
          description: "Disparate impact >0.8 (80% rule)"
          props:
            - name: metric_key
              value: disparate_impact
            - name: threshold
              value: "0.8"
            - name: operator
              value: ">"
            - name: "input:dimension"
              value: gender
            - name: "input:target"
              value: target
```

---

## Step 3: Train Model

```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
```

---

## Step 4: Post-Training Audit (Fairness + Performance)

Check model predictions on **test data**:

```python
# Get predictions
predictions = model.predict(X_test)

# Prepare test dataframe
test_df_with_pred = test_df.copy()
test_df_with_pred['prediction'] = predictions

# Audit fairness AND performance
vl.enforce(
    data=test_df_with_pred,
    target="class",
    prediction="prediction",
    gender="Attribute9",
    policy="model-policy.yaml"
)
```

### model-policy.yaml

```yaml
assessment-plan:
  uuid: model-fairness-policy
  metadata:
    title: "Model Fairness & Performance"
  reviewed-controls:
    control-selections:
      - include-controls:
        # Performance checks
        - control-id: accuracy-check
          description: "Model accuracy must be >70%"
          props:
            - name: metric_key
              value: accuracy
            - name: threshold
              value: "0.7"
            - name: operator
              value: ">"
        - control-id: precision-check
          description: "Precision must be >60%"
          props:
            - name: metric_key
              value: precision
            - name: threshold
              value: "0.6"
            - name: operator
              value: ">"
        # Fairness checks
        - control-id: equal-opportunity
          description: "Equal opportunity difference <10%"
          props:
            - name: metric_key
              value: equal_opportunity_diff
            - name: threshold
              value: "0.1"
            - name: operator
              value: "<"
            - name: "input:dimension"
              value: gender
            - name: "input:target"
              value: target
            - name: "input:prediction"
              value: prediction
```

---

## Example Output

```
[Venturalitica] 🛡  Enforcing policy: model-policy.yaml
  ✅ PASS | Controls: 3/3 passed
    ✓ [accuracy-check] Model accuracy... 0.76 (Limit: >0.7)
    ✓ [precision-check] Precision... 0.68 (Limit: >0.6)
    ✓ [equal-opportunity] Equal opportunity... 0.08 (Limit: <0.1)
```

---

## Summary

```
┌─────────────┬─────────────────────┬──────────────────────┐
│ Phase       │ What to Check       │ Policy File          │
├─────────────┼─────────────────────┼──────────────────────┤
│ Pre-train   │ Data bias           │ data-policy.yaml     │
│ Post-train  │ Fairness + Accuracy │ model-policy.yaml    │
└─────────────┴─────────────────────┴──────────────────────┘
```
