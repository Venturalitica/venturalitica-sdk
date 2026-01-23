# API Reference

## quickstart

Run a pre-configured bias audit demo.

```python
import venturalitica as vl

results = vl.quickstart('loan')
```

**Parameters:**
- `scenario` (str): One of `'loan'`, `'hiring'`, `'health'`
- `verbose` (bool): Show detailed output (default: True)

**Returns:** List of compliance results

---

## enforce

Audit your own data for bias.

```python
import venturalitica as vl
import pandas as pd

df = pd.read_csv("my_data.csv")

results = vl.enforce(
    data=df,
    target="approved",
    gender="gender",
    policy="policy.yaml"
)
```

**Parameters:**
- `data` (DataFrame): Your dataset
- `target` (str): Column with the outcome variable
- `policy` (str): Path to OSCAL policy file
- `**attributes`: Protected attributes to check (e.g., `gender="col_name"`)

**Returns:** List of compliance results

---

## list_scenarios

List available quickstart scenarios.

```python
>>> vl.list_scenarios()
{'loan': 'Detect bias in loan approval decisions',
 'hiring': 'Multi-attribute fairness in recruitment',
 'health': 'Healthcare diagnosis fairness'}
```
