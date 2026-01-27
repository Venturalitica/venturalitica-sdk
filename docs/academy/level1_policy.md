# Level 1: The Engineer (Policy & Configuration) 🟢

**Goal**: Learn how to write the "Law" and **Detect Risk**.
**Prerequisite**: [Zero to Pro (Index)](index.md)

---

## 1. The Scenario: "The Age Bias"

In the [Zero to Pro](index.md) quickstart, `vl.quickstart('loan')` FAILED.

```text
credit-age-disparate   Age disparity          0.361      > 0.5      ❌ FAIL
```

**What happened?**
The "Law" (OSCAL Policy) said: "Age Disparity must be > 0.5".
The "Reality" (Data) was: `0.361`.

In **ISO 42001** terms, you have identified a **Risk**.
Your instinct is to "fix" it by lowering the threshold to 0.3.
**STOP.** 🛑

> **Rule #1**: Developers measure Risk. Compliance Officers accept Risk.
> If you lower the bar to make the test pass, you are hiding the risk, not treating it.

## 2. Anatomy of a Policy (OSCAL)

Your job is to translate the "Law" into Code. 
Create a file named `my_policy.yaml`. Keep the threshold at **0.5 (The Standard)**.

```yaml
assessment-plan:
  uuid: my-policy-001
  metadata:
    title: "Corporate Fairness Standard"
  reviewed-controls:
    control-selections:
      - include-controls:
        # 🟢 Control 1: The Bias Check
        - control-id: age-check
          description: "Age Disparity must be standard (> 0.5)"
          props:
            - name: metric_key
              value: disparate_impact_ratio # The Python metric to run
            - name: "input:dimension"
              value: age                    # The abstract concept
            - name: operator
              value: ">"
            - name: threshold
              value: "0.5"                  # 🔒 DO NOT CHANGE THIS
```

## 3. Run Your Custom Policy

Now, let's run the audit again with *your* configuration. Observe how we map the abstract `age` concept to your specific data column.

```python
import venturalitica as vl
from ucimlrepo import fetch_ucirepo

# 1. Get Data (Messy CSV)
dataset = fetch_ucirepo(id=144)
df = dataset.data.features
df['class'] = dataset.data.targets

# 2. Run Audit (The Mapping)
try:
    vl.enforce(
        data=df,
        target="class",
        age="Attribute13",    # 🗝️ MAPPING: 'age' is actually 'Attribute13'
        policy="my_policy.yaml"
    )
    print("✅ Audit Passed!")
except Exception as e:
    print(f"❌ BLOCKED: {e}")
    print("👉 Action: Push trace.json to SaaS for Compliance Officer review.")
```

### 🤝 The "Translation" Handshake

Notice what just happened.

-   **Legal**: "Be fair (> 0.5)." (Defined in your YAML)
-   **Dev**: "This column `Attribute13` is `age`." (Defined in your Python)

This mapping is the **Handshake**. You bridge the gap between messy Data and rigid Law. This is how you implement **ISO 42001** without losing your mind in spreadsheets.

## 4. The "Aha!" Moment

When you run this, it will **FAIL** in your terminal. And that is **GOOD**.
But compliance is not just about terminal logs. 

To see the professional report and visualization of this failure, run the local dashboard:

```bash
uv run venturalitica ui
```

Navigate to the **Policy** tab. You will see the visual proof of your identified risk:

![Policy Failure](../assets/academy/policy_status_fail.png)

You have successfully prevented a non-compliant AI from reaching production by measuring risk against a verifiable standard.

## 4. Take Home Messages 🏠

1.  **Policy as Code**: Governance is just a `.yaml` file. Version control it.
2.  **Separation of Duties**: You define the *Mapping* (`age`=`Attribute13`). The Officer defines the *Threshold* (`> 0.5`).
3.  **The Handshake**: The failure is the signal. In Level 2, we will send this signal to the people who can fix it.

---

**Next Step**: The build failed locally. How do we tell the Compliance Officer?
👉 **[Go to Level 2: The Integrator (MLOps)](level2_integrator.md)**
