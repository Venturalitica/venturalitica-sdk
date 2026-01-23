# API Reference

## Core Functions

### quickstart

Run a pre-configured bias audit demo.

```python
import venturalitica as vl

results = vl.quickstart('loan')
```

**Parameters:**
- `scenario` (str): One of `'loan'`, `'hiring'`, `'health'`
- `verbose` (bool): Show detailed output (default: True)

**Returns:** `List[ComplianceResult]`

---

### enforce

Audit data or model predictions for bias.

```python
import venturalitica as vl

# Data audit (pre-training)
vl.enforce(
    data=df,
    target="approved",
    gender="gender",
    policy="policy.yaml"
)

# Model audit (post-training)
vl.enforce(
    data=df,
    target="approved",
    prediction=predictions,
    gender="gender",
    policy="policy.yaml"
)
```

**Parameters:**
- `data` (DataFrame): Your dataset
- `target` (str): Column with ground truth
- `prediction` (str or array): Model predictions (optional for data-only audit)
- `policy` (str): Path to OSCAL policy file
- `**attributes`: Protected attributes (e.g., `gender="col_name"`)

**Returns:** `List[ComplianceResult]`

---

### wrap

Automatically audit on `fit()` and `predict()`.

```python
import venturalitica as vl
from sklearn.ensemble import RandomForestClassifier

model = vl.wrap(RandomForestClassifier(), policy="policy.yaml")

# Auto-audits on fit
model.fit(X_train, y_train, audit_data=df_train)

# Auto-audits on predict
model.predict(X_test, audit_data=df_test)

# Get results
model.last_audit_results
```

**Parameters:**
- `model`: Any sklearn-compatible model
- `policy` (str): Path to OSCAL policy file

**Returns:** `GovernanceWrapper` (behaves like original model)

---

### monitor

Context manager for tracking training.

```python
import venturalitica as vl

with vl.monitor(name="My Training"):
    model.fit(X, y)
```

**Tracks:**
- Duration
- CO2 emissions (if CodeCarbon installed)
- Hardware telemetry

---

## Utility Functions

### list_scenarios

```python
>>> vl.list_scenarios()
{'loan': 'Credit scoring fairness',
 'hiring': 'Recruitment equity',
 'health': 'Clinical diagnosis fairness'}
```

### load_sample

```python
df = vl.load_sample('loan')
```

Loads UCI dataset for the given scenario.
