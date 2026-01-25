# 🛠️ Model Training Integration (Venturalítica)

Integrate fairness and performance checks into your ML workflow with Venturalítica.

---

## Overview

!!! info "Interactive Version"
    You can run this tutorial in a Jupyter Notebook: [01-training-tutorial.ipynb](https://github.com/Venturalítica/venturalitica-sdk/blob/main/notebooks/01-training-tutorial.ipynb)

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

!!! tip "Why do we need `tracecollector`?"
    Compliance requires proof. Use `vl.tracecollector` to record the "Code Story" (BOM, Headers) along with the audit results. This is required for Annex IV generation.

```python
import venturalitica as vl

# Start the 'evidence recorder'
with vl.tracecollector("training_audit"):
    
    # Run the Data Audit
    vl.enforce(
        data=train_df,
        target="class",
        gender="Attribute9",  # Gender/Status column
        age="Attribute13",    # Age column
        policy="loan-policy.yaml"
    )
```

**Real Output:**
```text
[Venturalítica {{ version }}] 🚀 TraceCollector [training_audit] starting...
[Venturalítica {{ version }}] 🛡  Enforcing policy: loan-policy.yaml

  CONTROL                DESCRIPTION                            ACTUAL     LIMIT      RESULT
  ────────────────────────────────────────────────────────────────────────────────────────────────
  imbalance              Minority ratio                         0.431      > 0.2      ✅ PASS
  gender-bias            Disparate impact                       0.836      > 0.8      ✅ PASS
  age-bias               Age disparity                          0.361      > 0.5      ❌ FAIL
  ────────────────────────────────────────────────────────────────────────────────────────────────
  Audit Summary: ❌ VIOLATION | 2/3 controls passed
  
  ✅ TraceCollector [training_audit] evidence saved to .venturalitica/trace_training_audit.json
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

Audit the model's behavior on unseen data. We reuse the same trace collector (or start a new one) to capture this phase.

```python
# Create audit dataframe (raw features + predictions)
test_audit_df = df.iloc[test_df.index].copy()
test_audit_df['prediction'] = predictions

with vl.tracecollector("model_eval"):
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
```text
[Venturalítica {{ version }}] 🛡  Enforcing policy: loan-policy.yaml

  CONTROL                DESCRIPTION                            ACTUAL     LIMIT      RESULT
  ────────────────────────────────────────────────────────────────────────────────────────────────
  imbalance              Minority ratio                         0.418      > 0.2      ✅ PASS
  gender-bias            Disparate impact                       0.905      > 0.8      ✅ PASS
  age-bias               Age disparity                          0.600      > 0.5      ✅ PASS
  ────────────────────────────────────────────────────────────────────────────────────────────────
  Audit Summary: ✅ POLICY MET | 3/3 controls passed
```

!!! warning
    While the training data failed the Age check (**0.361**), the model's predictions on the test set (**0.600**) managed to pass the policy limit (>0.5). However, this improvement should be closely monitored to ensure it generalizes beyond this specific test slice.

!!! info "**Why 0.361 vs 1.000?**"
    If you see a perfect `1.000` but expect bias, check your column binding. If a column is missing or mismatched, Venturalítica may default to 1.0. Always verify your column names (like `Attribute9` vs `gender`) in the `enforce()` call. {{ version }} also includes a minimum support filter (N>=5) to ensure statistical significance, which contributes to the precise **0.361** reading.

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

Venturalítica supports: `accuracy`, `precision`, `recall`, and `f1`.

**Example Output with Performance:**
```text
[Venturalítica {{ version }}] 🛡  Enforcing policy: tutorial_policy.yaml

  CONTROL                DESCRIPTION                            ACTUAL     LIMIT      RESULT
  ────────────────────────────────────────────────────────────────────────────────────────────────
  gender-disparate       Gender fairness (DI > 0.8)             0.905      > 0.8      ✅ PASS
  age-disparate          Age fairness (DI > 0.5)                0.600      > 0.5      ✅ PASS
  accuracy-check         Accuracy > 70%                         0.795      > 0.7      ✅ PASS
  ────────────────────────────────────────────────────────────────────────────────────────────────
  Audit Summary: ✅ POLICY MET | 3/3 controls passed
```

---

## Step 6: Automatic Governance with `vl.wrap` (Experimental)

!!! warning "**Experimental Feature**"
    `vl.wrap` is currently in preview. Its API and behavior may change in future versions. Use with caution.

If you are using **Scikit-Learn**, you can automate the entire audit process by wrapping your model. This ensures that every `.fit()` and `.predict()` call is audited against your policy.

```python
# Wrap your model
base_model = RandomForestClassifier(n_estimators=100, random_state=42)
governed_model = vl.wrap(base_model, policy="loan-policy.yaml") # Venturalítica Governance

# Audits are automated! 
# Just provide the raw data for attribution mapping (e.g., gender, age)
governed_model.fit(
    X_train, y_train, 
    audit_data=train_df, 
    gender="Attribute9", 
    age="Attribute13"
)

# Predict also triggers the fairness + performance audit
predictions = governed_model.predict(
    X_test, 
    audit_data=test_df, 
    gender="Attribute9", 
    age="Attribute13"
)
```

This pattern reduces boilerplate and guarantees that no model goes to production without a verified audit trail.

---

## Step 7: View Evidence in Dashboard
Now that you have run the training and evaluation with `tracecollector`, you have generated the artifacts required for the **EU AI Act**.

Inspect them in the Glass Box Dashboard:

```bash
venturalitica ui
```

This will launch the local server where you can see:

*   **Article 9**: Your Fairness & Performance Audit results.
*   **Article 13**: The BOM of your training environment.
*   **Generation**: The draft of your technical documentation.
