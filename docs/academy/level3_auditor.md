# Level 3: The Auditor (Glass Box Trace) 🟠

**Goal**: Verify your policy visually and cryptographically using the **Glass Box** method.

**Prerequisite**: [Level 2 (The Integrator)](level2_integrator.md)

---

## 1. The Problem: "It passed, but can we trust the process?"

In Level 2, you logged the compliance score. But for **High-Risk AI** (like Credit Scoring), metrics aren't enough.
An Auditor asks: *"Did you test on the real dataset, or did you filter out the rejected loans?"* and *"Can you prove this code was actually run?"*

## 2. The Solution: The "Glass Box" Trace

As per our **Strategic Audit Docs**, professional auditing requires more than just results—it requires **Provenance**.

Venturalítica uses a `monitor()` context manager to record everything:

-   **The Code**: AST analysis of your script.
-   **The Data**: Row count and column schema.
-   **The Hardware**: Memory, CPU, and Carbon stats (Article 15).
-   **The Seal**: A cryptographic SHA-256 hash of the entire session.

### The Upgrade

We continue working on the same project. No new setup required.

### Run with the Native Monitor

Wrap your execution in `vl.monitor()`. This context manager captures the "Handshake" between your code and the policy by harvesting both physical and logical metadata.

### 🔍 Deep Dive: Glass Box vs Black Box
### 🔍 Deep Dive: Glass Box vs Black Box

| Feature | ⬛ Black Box (Standard) | 🪟 **Glass Box (Venturalítica)** |
| :--- | :--- | :--- |
| **Logic** | "Trust me, I ran the code." | **AST Analysis**: We record *which* function mapped code to policy. |
| **Data** | "Here is the CSV." | **Fingerprint**: We record the SHA-256 of the dataset at runtime. |
| **Scope** | Code | Code + Environment + Hardware Stats |

> 💡 **Full Code**: See the professional audit lifecycle in the [01_governance_audit.ipynb](https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/scenarios/loan-credit-scoring/01_governance_audit.ipynb) notebook.

```python
import venturalitica as vl
from ucimlrepo import fetch_ucirepo

# 1. Load Data (The Real Deal)
dataset = fetch_ucirepo(id=144)
df = dataset.data.features
df['class'] = dataset.data.targets

# 1. Start the Multimodal Monitor (The Glass Box)
with vl.monitor("loan_audit_v1"):
    # This block is now being watched by the Auditor
    df = vl.load_sample("loan")
    
    # Download data_policy.oscal.yaml: https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/scenarios/loan-credit-scoring/policies/loan/data_policy.oscal.yaml
    results = vl.enforce(
        data=df,
        target="class",       # Checking Ground Truth
        age="Attribute13",    # Mapping Age
        policy="data_policy.oscal.yaml"
    )
    # The session trace file (.venturalitica/trace_loan_audit_v1.json) 
    # will prove NOT just the result, but HOW it was computed.
```


## 3. The "Digital Seal" Verification

After running the audit, launch the UI:

```bash
uv run venturalitica ui
```

Navigate to **"Article 13: Transparency"**.

### Finding the Evidence Hash
Look for the **Evidence Hash** in the dashboard.
`Evidence Hash: 89fbf...`

This hash is your **"Digital Seal"**. If you change *one pixel* in the dataset or *one line* in the policy, this hash changes. You can now prove to a regulator exactly what happened during the audit.

## 4. The Compliance Map

The Dashboard translates JSON evidence into the language of the **EU AI Act**.

| Law | Dashboard Tab | What to Answer |
| :--- | :--- | :--- |
| **Art 9** | Risk Management | "Did we verify bias < 0.1?" (Your Policy) |
| **Art 10** | Data Governance | "Is the training data representative?" |
| **Art 13** | Transparency | "What libraries (BOM) are we using?" |

## 5. Take Home Messages 🏠

1.  **Don't Trust, Verify**: The **Trace File** (captured automatically via `monitor()`) is the source of truth for the entire execution context.
2.  **Glass Box Audit**: Compliance isn't a "pass/fail" boolean; it's a verifiable history of execution.
3.  **Immutable Proof**: The Evidence Hash allows you to prove the integrity of the audit process.

---

**Next Step**: You have the Code (Level 1), the Ops (Level 2), and the Proof (Level 3). Now generate the Legal Documents.
👉 **[Go to Level 4: The Architect](level4_annex_iv.md)**
