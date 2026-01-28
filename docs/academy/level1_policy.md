# Level 1: The Engineer (Policy & Configuration) 🟢

**Goal**: Learn how to implement **Controls** that mitigate **Risks**.

**Prerequisite**: [Zero to Pro (Index)](index.md)

---

## 1. The Scenario: From Risk to Control

In a formal Management System (**ISO 42001**), governance follows a top-down flow:

1.  **Risk Assessment**: The Compliance Officer (CO) identifies a business risk (e.g., *"Our lending AI might discriminate against elderly applicants, causing legal and reputational damage"*).
2.  **Control Definition**: To mitigate this risk, the CO sets a **Control** (e.g., *"The Age Disparity Ratio must always be > 0.5"*).
3.  **Technical Implementation**: That's your job. You take the CO's requirement and turn it into the technical "Law" (**Article 10: Data Governance**).

In the [Zero to Pro](index.md) quickstart, `vl.quickstart('loan')` FAILED:

```text
credit-age-disparate   Age disparity          0.361      > 0.5      ❌ FAIL
```

### What happened?
The **Control** successfully detected a **Compliance Gap**. The "Reality" of the data (`0.361`) violated the requirement set to mitigate the "Age Bias" risk.

> **Rule #1: The Handshake of Responsibility**.
> Compliance Officers identify **Risks** and establish **Controls**. 
> Engineers implement and **Verify** those controls using Evidence.

If you lower the threshold to 0.3 just to make the test "pass," you aren't fixing the code—you are **bypassing a security control** and exposing the company to the original risk.

## 2. Anatomy of a Control (OSCAL)

Your job is to translate the CO's requirement into Code. 
Create a file named `data_policy.oscal.yaml` (or [download it from GitHub](https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/scenarios/loan-credit-scoring/policies/loan/data_policy.oscal.yaml)). Keep the threshold at **0.5 (The Organizational Standard)**.

```yaml
assessment-plan:
  metadata:
    title: "Article 10: Data Governance Standard"
  control-implementations:
    - description: "Fairness Monitoring"
      implemented-requirements:
        # 🟢 Control 1: The Bias Check
        - control-id: age-check
          description: "Age Disparity must be standard (> 0.5)"
          props:
            - name: metric_key
              value: disparate_impact        # The Python metric to run
            - name: "input:dimension"
              value: age                    # The abstract concept
            - name: operator
              value: gt                     # Greater Than
            - name: threshold
              value: "0.5"                  # 🔒 DO NOT CHANGE THIS
```

## 3. Run Your Custom Policy

Now, let's run the audit again with *your* configuration. Observe how we map the abstract `age` concept to your specific data column.

> 💡 **Full Code**: You can find the complete, ready-to-run notebook for this level here: [00_engineer_policy.ipynb](https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/scenarios/loan-credit-scoring/00_engineer_policy.ipynb)

```python
import venturalitica as vl
from ucimlrepo import fetch_ucirepo

# 1. Get Data (Messy CSV)
dataset = fetch_ucirepo(id=144)
df = dataset.data.features
df['class'] = dataset.data.targets

# 2. Run Audit (The Mapping)
results = vl.enforce(
    data=df,
    target="class",
    age="Attribute13",    # 🗝️ MAPPING: 'age' is actually 'Attribute13'
    policy="data_policy.oscal.yaml"
)

# 3. Check Results
if all(r.passed for r in results):
    print("✅ Audit Passed!")
else:
    print("❌ BLOCKED: Compliance Violation detected.")
    print("👉 Action: Push trace.json to SaaS for Compliance Officer review.")
```

### 🤝 The "Translation" Handshake

Notice what just happened.

-   **Legal**: "Be fair (> 0.5)." (Defined in your YAML)
-   **Dev**: "This column `Attribute13` is `age`." (Defined in your Python)

This mapping is the **Handshake**. You bridge the gap between messy Data and rigid Law. This is how you implement **ISO 42001** without losing your mind in spreadsheets.

## 4. Visual Verification

When you run this, it will **FAIL** in your terminal. And that is **GOOD**.
But compliance is not just about terminal logs.

To see the professional report and visualization of this failure, run the local dashboard:

```bash
uv run venturalitica ui
```

Navigate to the **Policy** tab. You will see the visual proof of your identified risk:

![Policy Failure](../assets/academy/policy_status_fail.png)

You have successfully prevented a non-compliant AI from reaching production by measuring risk against a verifiable standard.

## 5. Take Home Messages 🏠

1.  **Policy as Code**: Governance is just a `.yaml` file. It defines the **Control**.
2.  **The Handshake**: You define the *Mapping* (`age`=`Attribute13`). The Officer defines the *Requirement* (`> 0.5`).
3.  **Treatment starts with Detection**: The local failure is the signal necessary to start a formal ISO 42001 risk treatment plan.

---

**Next Step**: The build failed locally. How do we tell the Compliance Officer?
👉 **[Go to Level 2: The Integrator (MLOps)](level2_integrator.md)**
