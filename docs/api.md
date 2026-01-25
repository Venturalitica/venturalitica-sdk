# API Reference

Venturalítica provides a simple, unified interface for AI governance.

---

## 🚀 Core Functions

### `quickstart(scenario, verbose=True)`

Run a pre-configured bias audit demo on a standard dataset.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `scenario` | `str` | Predefined scenario: `'loan'`, `'hiring'`, `'health'`. |
| `verbose` | `bool` | Whether to print the structured table report to the console. |

**Returns:** `List[ComplianceResult]`

---

### `enforce(data, target, prediction=None, policy=None, **attributes)`

The main entry point for auditing datasets and models.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `data` | `DataFrame` | Pandas DataFrame containing features, targets, and optionally predictions. |
| `target` | `str` | Name of the column with ground truth labels. |
| `prediction` | `str\|array` | (Optional) Column name or array of model predictions. |
| `policy` | `str` | Path to the OSCAL/YAML policy file. |
| `**attributes` | `str` | Mappings for protected variables (e.g., `gender="attr9"`, `age="age_col"`). |

**Returns:** `List[ComplianceResult]`

!!! note
    If `prediction` is omitted, fairness metrics automatically fall back to using `target` to audit data bias.

---

### `wrap(model, policy)` (Experimental)

!!! danger "PREVIEW"
    This function is experimental and its API might change.

Transparently audit your model during Scikit-Learn standard workflows.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `model` | `object` | Any Scikit-learn compatible classifier or regressor. |
| `policy` | `str` | Path to the policy for evaluation. |

**Returns:** `GovernanceWrapper` (Preserves original API like `.fit()` and `.predict()`).

---

### `monitor(name)`

A context manager to track training metrics, hardware health, and environmental impact.

```python
with vl.monitor(name="CreditModel-v1"):
    model.fit(X, y)
```

**Collected Telemetry:**

- **⏱ Duration**: Execution time of the block.
- **🌱 Emissions**: Carbon footprint (requires `codecarbon`).
- **🛡 Stability**: Model fingerprinting and integrity verification.

---

## 🛠 Utility Functions

### `list_scenarios()`
Returns a dictionary of available scenarios and their descriptions.

### `load_sample(scenario)`
Loads the corresponding UCI dataset for a scenario as a Pandas DataFrame.
