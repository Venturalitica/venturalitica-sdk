# 🛠️ Model Training (The Builder)

This guide focuses on the **Builder Persona**: the Data Scientist who trains the model.
In the **Venturalítica** workflow, your job is to "manufacture" the AI system according to the specifications defined by the **Engineer** (Level 1).

---

## The Two-Policy Handshake

Compliance is not a single step. It is a handshake between **Data** (Article 10) and **Model** (Article 15).

| Phase | Policy | Article (EU AI Act) | Function |
|:--|:--|:--|:--|
| **1. Data Audit** | `data_policy.yaml` | **Art. 10**: Data Governance | `vl.enforce(data=train_df)` |
| **2. Model Audit** | `model_policy.yaml` | **Art. 15**: Accuracy & Robustness | `vl.enforce(data=test_df, prediction=pred)` |

---

## Step 1: Load Data & Split

We use the standard **Loan Credit Scoring** dataset.

```python
from ucimlrepo import fetch_ucirepo
from sklearn.model_selection import train_test_split
import pandas as pd

# 1. Fetch Data
dataset = fetch_ucirepo(id=144)
df = dataset.data.features.copy()
df['class'] = dataset.data.targets

# 2. Split (Train/Test)
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

# 3. Encode for Training (One-Hot)
df_encoded = pd.get_dummies(df.drop(columns=['class']))
X_train, X_test, y_train, y_test = train_test_split(
    df_encoded, 
    df['class'].values.ravel(), 
    test_size=0.2, 
    random_state=42
)
```

---

## Step 2: Pre-Training Audit (Article 10)

Before you invest compute time, verify the raw material.

```python
import venturalitica as vl

# Start the 'evidence recorder' for the Training Phase
with vl.monitor("training_run_v1"):
    
    # 🔍 AUDIT 1: DATA GOVERNANCE (The Ingredients)
    print("🛡️ Auditing Data (Article 10)...")
    vl.enforce(
        data=train_df,
        target="class",
        gender="Attribute9",  # Mapping strictly defined by policy
        age="Attribute13",
        policy="data_policy.yaml"
    )
```

**Real Output:**
```text
[Venturalítica {{ version }}] 🛡  Enforcing policy: data_policy.yaml

  CONTROL                DESCRIPTION                            ACTUAL     LIMIT      RESULT
  ────────────────────────────────────────────────────────────────────────────────────────────────
  imbalance              Minority ratio                         0.431      > 0.2      ✅ PASS
  gender-bias            Disparate impact                       0.836      > 0.8      ✅ PASS
  ────────────────────────────────────────────────────────────────────────────────────────────────
```

---

## Step 3: Train the Model

If the data passes, proceed to manufacture the model.

```python
    # 🏭 MANUFACTURE: Train the Model
    from sklearn.ensemble import RandomForestClassifier
    
    print("🤖 Training Model...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Generate predictions for the next audit
    predictions = model.predict(X_test)
```

---

## Step 4: Post-Training Audit (Article 15)

Now verify the finished product against the performance requirements.

```python
    # 🔍 AUDIT 2: MODEL ACCURACY & FAIRNESS (The Product)
    print("🛡️ Auditing Model (Article 15)...")
    
    # Prepare audit dataframe
    audit_df = df.iloc[test_df.index].copy()
    audit_df['prediction'] = predictions
    
    vl.enforce(
        data=audit_df,
        target="class",
        prediction="prediction", # Now we evaluate the OUTPUT using the same sensitive attributes
        gender="Attribute9",
        age="Attribute13",
        policy="model_policy.yaml"
    )
```

**Real Output:**
```text
[Venturalítica {{ version }}] 🛡  Enforcing policy: model_policy.yaml

  CONTROL                DESCRIPTION                            ACTUAL     LIMIT      RESULT
  ────────────────────────────────────────────────────────────────────────────────────────────────
  accuracy-check         Minimum Accuracy                       0.760      > 0.7      ✅ PASS
  recall-check           Recall (Risk Aversion)                 0.720      > 0.6      ✅ PASS
  ────────────────────────────────────────────────────────────────────────────────────────────────
  Audit Summary: ✅ POLICY MET | 2/2 controls passed
  
  ✅ TraceCollector [training_run_v1] evidence saved to .venturalitica/trace_training_run_v1.json
```

---

## Step 5: View Evidence

You have now completed the **Builder's Job**.
Run the dashboard to see your "Glass Box".

```bash
venturalitica ui
```
