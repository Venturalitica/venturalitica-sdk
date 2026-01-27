# Level 3: The Auditor (Vision & Evidence) 🟠

**Goal**: Verify your policy visually and cryptographically on complex data using the Glass Box method.

**Prerequisite**: [Level 2 (The Integrator)](level2_integrator.md)

---

## 1. The Problem: "It passed, but can we trust the process?"

In Level 2, you logged the compliance score. But for **High-Risk AI** (like Computer Vision), metrics aren't enough.
An Auditor asks: *"Did you test on a balanced dataset, or did you cherry-pick images?"* and *"Can you prove this code was actually run?"*

## 2. The Solution: The "Glass Box" Trace

As per our **Strategic Audit Docs**, professional auditing requires more than just results—it requires **Provenance**. 

Venturalítica uses a `tracecollector` to record everything:
-   **The Code**: AST analysis of your script.
-   **The Data**: Row count and column schema.
-   **The Seal**: A cryptographic SHA-256 hash of the entire session.

### Clone the Samples (The "Pro" Way)

Since `quickstart` is for skeptics, true Auditors work with the full source. Clone the samples repository to get the High-Risk Vision dataset:

```bash
git clone https://github.com/venturalitica/venturalitica-sdk-samples.git
cd venturalitica-sdk-samples/scenarios/vision-fairness
```

### Run with Trace Capture

Wrap your execution in a `tracecollector`. This context manager captures the "Handshake" between your code and the policy.

### 🔍 Deep Dive: Glass Box vs Black Box
| Feature | ⬛ Black Box (Standard) | 🪟 **Glass Box (Venturalítica)** |
| :--- | :--- | :--- |
| **Logic** | "Trust me, I ran the code." | **AST Analysis**: We record *which* function mapped code to policy. |
| **Data** | "Here is the CSV." | **Fingerprint**: We record the SHA-256 of the dataset at runtime. |
| **Scope** | Code | Code + Environment + Hardware Stats |

```python
import venturalitica as vl
import pandas as pd

# Load the High-Risk Vision sample
df = pd.read_csv("datasets/fairface_sample.csv")

# Start the Trace Session (The Glass Box)
with vl.tracecollector("audit_session_v1"):
    # This block is now being watched by the Auditor
    results = vl.enforce(
        data=df,
        policy="policies/fairness.oscal.yaml",
        target="prediction",
        race="race",
        gender="gender"
    )
    # The 'trace.json' will prove NOT just the result, but HOW it was computed.
```

### 🛡️ Public Trust: The Compliance Badge
Developers love README badges. Auditors love Transparency (Article 13).
Venturalítica bridges this gap.

```python
# Generate a verifiable SVG badge for your README
vl.generate_compliance_badge(
    results, 
    output_path="compliance_badge.svg"
)
```

Now you can add this to your GitHub repo to show the world (and the regulator) that your model is safe.

## 3. The "Digital Seal" Verification

After running the audit, launch the UI:

```bash
uv run venturalitica ui
```

Navigate to **"Article 13: Transparency"**.

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

1.  **Don't Trust, Verify**: The `trace.json` (captured via `tracecollector`) is the source of truth.
2.  **Glass Box Audit**: Compliance isn't a "pass/fail" boolean; it's a verifiable history of execution.
3.  **Immutable Proof**: The Evidence Hash allows you to prove the integrity of the audit process.

---

**Next Step**: You have the Code (Level 1), the Ops (Level 2), and the Proof (Level 3). Now generate the Legal Documents.
👉 **[Go to Level 4: The Architect](level4_annex_iv.md)**
