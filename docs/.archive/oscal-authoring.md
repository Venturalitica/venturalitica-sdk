# OSCAL Policy Authoring Guide

How to write, extend, and validate OSCAL policies for Venturalitica governance checks.

## 1) Minimal Policy Template

Venturalitica uses the OSCAL `assessment-plan` shape. The smallest runnable policy looks like:

```yaml
assessment-plan:
  metadata:
    title: "Credit Risk Assessment"
    version: "1.0.0"

  control-implementations:
    - description: "Post-training fairness controls"
      implemented-requirements:
        - control-id: credit-disparate-impact
          description: "EEOC Four-Fifths Rule: selection rate must be ≥ 0.8"
          props:
            - name: metric_key
              value: disparate_impact
            - name: threshold
              value: "0.8"
            - name: operator
              value: gte
            - name: "input:target"
              value: target
            - name: "input:dimension"
              value: gender
```

Key fields:
- `control-id`: unique, kebab-case identifier
- `metric_key`: which Venturalitica metric to run
- `threshold` + `operator`: pass/fail rule
- `input:*`: semantic bindings (columns in your data)

## 2) Common Metrics

| Category | metric_key | What it checks | Typical threshold |
| --- | --- | --- | --- |
| Data quality | `class_imbalance` | Minority class share | `>= 0.2` |
| Fairness | `disparate_impact` | Four-Fifths Rule ratio | `>= 0.8` |
| Fairness | `demographic_parity` | Absolute gap in positive rate | `< 0.1` |
| Fairness | `equal_opportunity` | TPR gap | `< 0.05` |
| Performance | `accuracy` | Overall accuracy | `>= 0.75` |
| Performance | `f1_score` | Harmonic mean of precision/recall | `>= 0.70` |

## 3) Operators

| Value | Meaning |
| --- | --- |
| `gt`, `gte` | greater than (or equal) |
| `lt`, `lte` | less than (or equal) |
| `eq` | equal |

Use strings for thresholds: `value: "0.8"`.

## 4) Semantic Bindings (`input:*`)

- `input:target`: ground-truth label column (e.g., `approved`, `hired`)
- `input:dimension`: protected attribute (e.g., `gender`, `race`, `age`)
- `input:predictions`: model outputs when auditing predictions
- `input:features`: optional feature list for explainability

Example:
```yaml
- name: "input:target"
  value: "loan_approved"
- name: "input:dimension"
  value: "gender"
```

## 5) Pre-training vs Post-training

- **Pre-training (data-only)**: metrics like `class_imbalance`, `representation_parity`
- **Post-training (model)**: metrics like `disparate_impact`, `equal_opportunity`, `f1_score`

## 6) Full Example (Credit Scoring)

```yaml
assessment-plan:
  metadata:
    title: "Credit Risk Policy"
    version: "1.1"

  control-implementations:
    - description: "Data quality"
      implemented-requirements:
        - control-id: credit-class-balance
          description: "Rejected loans must be ≥20%"
          props:
            - name: metric_key
              value: class_imbalance
            - name: threshold
              value: "0.2"
            - name: operator
              value: gte
            - name: "input:target"
              value: target

    - description: "Post-training fairness"
      implemented-requirements:
        - control-id: credit-disparate-impact
          description: "EEOC 80% Rule on gender"
          props:
            - name: metric_key
              value: disparate_impact
            - name: threshold
              value: "0.8"
            - name: operator
              value: gte
            - name: "input:target"
              value: target
            - name: "input:dimension"
              value: gender
```

## 7) Validation Checklist

- Unique `control-id` per control
- Thresholds are strings
- Operators use `gt|gte|lt|lte|eq`
- Required bindings present (`input:dimension` for fairness)
- Policy passes schema check: `uv run venturalitica validate-policy path/to/policy.yaml`

## 8) Troubleshooting

- **Missing metric**: check `metric_key` spelling and availability in the SDK registry
- **Binding error**: add `input:dimension` for fairness metrics
- **Duplicate control-id**: rename to a unique identifier

## 9) Regulatory Mapping Tips

Add props to record legal context:

```yaml
- name: regulation
  value: "EU-AI-Act-Art-10"
- name: standard
  value: "80-percent-rule"
```

This keeps audit logs self-explanatory for compliance teams.
