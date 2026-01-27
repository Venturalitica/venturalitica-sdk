# Tutorial: Writing Your First Policy (OSCAL)

Venturalítica uses **OSCAL (Open Security Controls Assessment Language)** to define governance rules. This "Policy-as-Code" approach allows you to version control your compliance requirements alongside your software.

## 1. The Structure of a Policy

A policy file (`.yaml`) tells the SDK **what** to measure (metrics) and **why** (control descriptions).

```yaml
assessment-plan:
  uuid: policy-v1
  metadata:
    title: "EU AI Act - High Risk Audit"
  reviewed-controls:
    control-selections:
      - include-controls:
        # CONTROL BLOCK 1
        - control-id: gender-fairness
          description: "Article 10: Data Governance. Examination of possible biases."
          props:
            - name: metric_key
              value: demographic_parity_diff
            - name: threshold
              value: "0.10"
            - name: operator
              value: "<"
```

## 2. Defining Controls

Each `control-id` represents a specific check.

### A. Bias Check (Fairness)
Ensure your model treats groups equally.

```yaml
- control-id: check-gender-bias
  props:
    - name: metric_key
      value: demographic_parity_diff
    - name: threshold
      value: "0.10"  # Fail if difference > 10%
    - name: operator
      value: "<"
```

### B. Data Quality
Check for class imbalance or missing values.

```yaml
- control-id: check-imbalance
  props:
    - name: metric_key
      value: min_class_ratio
    - name: threshold
      value: "0.20"  # Fail if minority class < 20%
    - name: operator
      value: ">"
```

## 3. Supported Metrics

All metrics from `venturalitica.metrics` are supported. Common keys:

| Key | Description |
| :--- | :--- |
| `demographic_parity_diff` | Difference in acceptance rates (Fairness). |
| `disparate_impact_ratio` | Ratio of acceptance rates (Fairness). |
| `accuracy_score` | Overall model accuracy (Performance). |
| `f1_score` | Harmonic mean of precision/recall (Performance). |
| `missing_values_ratio` | Percentage of empty cells (Quality). |

## 4. How to Run It

Once you have your `policy.yaml`, apply it to your dataframe:

```python
import venturalitica as vl
import pandas as pd

df = pd.read_csv("data/loan_applications.csv")

vl.enforce(
    data=df,
    target="approved",       # The column to predict
    gender="applicant_sex",  # The protected attribute
    policy="policy.yaml"     # Your OSCAL file
)
```

The SDK will evaluate every control in the YAML against your data. If any control fails (and `blocking: true`), it raises an `AuditFailure` exception, stopping the pipeline.
