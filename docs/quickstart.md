# 60-Second Quickstart

**Goal**: Your first bias audit in under 60 seconds.

---

## Step 1: Install

```bash
pip install venturalitica
```

---

## Step 2: Run Your First Audit

```python
import venturalitica as vl

vl.quickstart('loan')
```

**Output:**

```text
[Venturalitica v0.2.4] 🎓 Scenario: Credit Scoring Fairness
[Venturalitica v0.2.4] 📊 Loaded: UCI Dataset #144 (1000 samples)

  CONTROL                DESCRIPTION                            ACTUAL     LIMIT      RESULT
  ────────────────────────────────────────────────────────────────────────────────────────────────
  credit-data-imbalance  Data Quality                           0.431      > 0.2      ✅ PASS
  credit-data-bias       Disparate impact                       0.836      > 0.8      ✅ PASS
  credit-age-disparate   Age disparity                          0.361      > 0.5      ❌ FAIL
  ────────────────────────────────────────────────────────────────────────────────────────────────
  Audit Summary: ❌ VIOLATION | 2/3 controls passed
```

> 💡 The audit detected age-based bias in the UCI German Credit dataset.

---

## Step 3: What's Happening Under the Hood

The `quickstart()` function is a wrapper that:

1. **Downloads data** from UCI Machine Learning Repository
2. **Loads a policy** that defines fairness rules
3. **Calls `enforce()`** to run the audit

Here's the equivalent code:

```python
from ucimlrepo import fetch_ucirepo
import venturalitica as vl

# 1. Load UCI German Credit dataset
dataset = fetch_ucirepo(id=144)
df = dataset.data.features
df['class'] = dataset.data.targets

# 2. Run audit with policy
vl.enforce(
    data=df,
    target="class",
    gender="Attribute9",
    age="Attribute13",
    policy="risks.oscal.yaml"
)
```

### The Policy File

The policy (`risks.oscal.yaml`) defines the rules:

```yaml
assessment-plan:
  uuid: credit-risk-policy
  metadata:
    title: "Credit Scoring Fairness"
  reviewed-controls:
    control-selections:
      - include-controls:
        - control-id: credit-data-bias
          description: "Disparate impact ratio must be > 0.8 (80% rule)"
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

Each control defines:
- **metric_key**: What to measure (`disparate_impact`)
- **threshold**: The limit (`0.8`)
- **operator**: How to compare (`>`)
- **inputs**: Which columns to use

---

## What's Next?

- **[API Reference](api.md)** - Full documentation
- **Create your own policy** - Copy the YAML above and modify thresholds
