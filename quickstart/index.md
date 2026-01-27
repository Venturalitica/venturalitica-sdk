# 60-Second Quickstart

**Goal**: Your first bias audit in under 60 seconds.

______________________________________________________________________

## The Fundamentals: From Risk to Code

Building High-Risk AI requires a fundamental shift in how we approach testing. It is no longer enough to check for technical accuracy (e.g., F1 Score); we must now mathematically prove that the system respects fundamental rights, such as non-discrimination or data quality, as mandated by the **EU AI Act**.

Venturalítica automates this by treating "Governance" as a dependency. Instead of vague legal requirements, you define strict policies (OSCAL) that your model must pass before it can be deployed. This turns compliance into a deterministic engineering problem.

Is my System High-Risk?

According to [**Article 6**](https://artificialintelligenceact.eu/es/article/6/) of EU AI Act, a system is High-Risk if it is covered by [**Annex I**](https://artificialintelligenceact.eu/es/annex/1/) (Safety Components like machinery/medical devices) or listed in [**Annex III**](https://artificialintelligenceact.eu/es/annex/3/) (Biometrics, Critical Infrastructure, Education, Employment, Essential Services, Law Enforcement, Migration, Justice/Democracy).

**The Translation Layer:**

1. **Fundamental Risk**: "The model must not discriminate against protected groups" (Art 9).
1. **Policy Control**: "Disparate Impact Ratio must be > 0.8".
1. **Code Assertion**: `assert calculated_metric > 0.8`.

When you run `quickstart()`, you are technically running a **Unit Test for Ethics**.

______________________________________________________________________

## Step 1: Install

```
pip install git+https://github.com/Venturalitica/venturalitica-sdk.git
```

______________________________________________________________________

## Step 2: Run Your First Audit

```
import venturalitica as vl

vl.quickstart('loan')
```

**Output:**

```
[Venturalítica v0.4.1] 🎓 Scenario: Credit Scoring Fairness
[Venturalítica v0.4.1] 📊 Loaded: UCI Dataset #144 (1000 samples)

  CONTROL                DESCRIPTION                            ACTUAL     LIMIT      RESULT
  ────────────────────────────────────────────────────────────────────────────────────────────────
  credit-data-imbalance  Data Quality                           0.431      > 0.2      ✅ PASS
  credit-data-bias       Disparate impact                       0.836      > 0.8      ✅ PASS
  credit-age-disparate   Age disparity                          0.361      > 0.5      ❌ FAIL
  ────────────────────────────────────────────────────────────────────────────────────────────────
  Audit Summary: ❌ VIOLATION | 2/3 controls passed
```

Info

The audit detected age-based bias in the UCI German Credit dataset.

## Step 3: What's Happening Under the Hood

The `quickstart()` function is a wrapper that performs the full compliance lifecycle in one go:

1. **Downloads Data**: Fetches the UCI German Credit dataset.
1. **Loads Policy**: Reads `risks.oscal.yaml` which defines the fairness rules.
1. **Enforces**: Runs the audit (`vl.enforce`).
1. **Records**: Captures the evidence (`trace.json`) for the dashboard.

Here's the equivalent "manual" code:

```
from ucimlrepo import fetch_ucirepo
import venturalitica as vl

# 1. Load Data (The "Risk Source")
dataset = fetch_ucirepo(id=144)
df = dataset.data.features
df['class'] = dataset.data.targets

# 2. Define the Policy (The "Law")
# We load a pre-defined policies/risks.oscal.yaml

# 3. Run the Audit (The "Test")
# This automatically generates the Evidence Bill of Materials (BOM)
with vl.monitor("manual_audit"):
    vl.enforce(
        data=df,
        target="class",          # The outcome (True/False)
        gender="Attribute9",     # Protected Group A
        age="Attribute13",       # Protected Group B
        policy="risks.oscal.yaml"
    )
```

### The Policy Logic

The policy (`risks.oscal.yaml`) is the bridge. It tells the SDK *what* to check so you don't have to hardcode it.

```
# ... inside the OSCAL YAML ...
- control-id: credit-data-bias
  description: "Disparate impact ratio must be > 0.8 (80% rule)"
  props:
    - name: metric_key
      value: disparate_impact   # <--- The Python Function to call
    - name: threshold
      value: "0.8"              # <--- The Limit to enforce
    - name: operator
      value: ">"                # <--- The Logic (> 0.8)
    - name: "input:dimension"
      value: gender             # <--- Maps to "Attribute9"
```

This design decouples **Governance** (the policy file) from **Engineering** (the python code).

______________________________________________________________________

## Why This Matters

Without this mechanism, your AI model is a legal "Black Box":

- **Liability**: You cannot prove you checked for bias *before* deployment (Art 9).
- **Fragility**: Compliance is a manual checklist, easily forgotten or skipped.
- **Opacity**: Auditors cannot see the link between your code and the law.

By running `quickstart()`, you have just generated an immutable **Compliance Artifact**. Even if the laws change, your evidence remains.

## Step 4: The "Glass Box" Dashboard 📊

Now that we have the evidence (the "Black Box" recording), let's inspect it in the **Regulatory Map**.

```
venturalitica ui
```

Navigate through the **Compliance Map** tabs:

- **Article 9 (Risk)**: See the failed `credit-age-disparate` control. This is your technical evidence of "Risk Monitoring".
- **Article 10 (Data)**: See the data distribution and quality checks.
- **Article 13 (Transparency)**: Review the "Transparency Feed" to see your Python dependencies (BOM).

______________________________________________________________________

## Step 5: Generate Documentation (Annex IV) 📝

The final step is to turn this evidence into a legal document.

1. In the Dashboard, go to the **"Generation"** tab.
1. Select **"English"** (or Spanish/Catalan/Euskera).
1. Click **"Generate Annex IV"**.

Venturalítica will draft a technical document that references your specific run:

> *"As evidenced in `trace_quickstart_loan.json`, the system was audited against* *[OSCAL Policy: Credit Scoring Fairness]\*\*. A deviation was detected in Age Disparity (0.36), identifying a potential risk of bias..."*

### References

- **Policy Used**: [`loan/risks.oscal.yaml`](https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/policies/loan/risks.oscal.yaml)
- **Legal Basis**:
  - [EU AI Act Article 9 (Risk Management)](https://artificialintelligenceact.eu/article/9/)
  - [EU AI Act Article 11 (Technical Documentation)](https://artificialintelligenceact.eu/article/11/)

## What's Next?

- **[API Reference](https://venturalitica.github.io/venturalitica-sdk/api/index.md)** - Full documentation
- **Create your own policy** - Copy the YAML above and modify thresholds
