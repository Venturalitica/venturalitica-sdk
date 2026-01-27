# Zero to Pro: The 5-Minute Journey 🚀

**Goal**: Transform from "Python Developer" to "AI Governance Engineer" in 3 steps.

---

## The Philosophy: Compliance as Code

You are used to `pytest` for checking if your function adds 2+2 correctly.
But how do you test if your AI model respects **Human Rights**?

Venturalítica treats "Governance" as a dependency. Instead of vague legal advice, you define stricter **Policies (OSCAL)**. Your CI/CD pipeline enforces them just like linter rules.

### The Curriculum

| Level | Role | Goal | Project |
| :--- | :--- | :--- | :--- |
| **[Start Here](#step-1-install)** | **Developer** | Run your first audit in < 60s. | `loan-credit-scoring` |
| **[Level 1](level1_policy.md)** | **Engineer** | **Implement Controls** for identified Risks. | Custom Policy |
| **[Level 2](level2_integrator.md)** | **Integrator** | **Viz & MLOps**: "Compliance as Metadata". | MLOps / Dashboard |
| **[Level 3](level3_auditor.md)** | **Auditor** | Proof: "Trust the Hash". | `vision-fairness` |
| **[Level 4](level4_annex_iv.md)** | **Architect** | GenAI Docs: "Annex IV". | `medical-spine` |

---

## Step 1: Install
We recommend **uv** for blazing speed, or standard `pip`.

```bash
uv pip install git+https://github.com/Venturalitica/venturalitica-sdk.git
# OR
pip install git+https://github.com/Venturalitica/venturalitica-sdk.git
```

## Step 2: Running Your First Audit ⚡

Run this single line of code. It downloads a dataset, loads a policy, and audits a model.

```python
import venturalitica as vl

# Run the 'loan' scenario
vl.quickstart('loan')
```

**Output:**

```text
  CONTROL                DESCRIPTION                            RESULT
  ──────────────────────────────────────────────────────────────────────
  credit-data-bias       Disparate impact ratio > 0.8           ✅ PASS
  credit-age-disparate   Age disparity ratio > 0.5              ❌ FAIL
  ──────────────────────────────────────────────────────────────────────
  Audit Summary: ❌ VIOLATION | 1/2 controls passed
```

### 💡 Take Home Message
> **"Compliance transforms vague Principles into verifiable Engineering constraints."**
>
> *   **The Policy**: `ratio > 0.5` (The Law).
> *   **The Reality**: `0.361` (Your Code).
> *   **The Verdict**: `❌ FAIL` (The Compliance Gap).

You didn't need a lawyer. You just needed a visible test failure.

## Step 3: Choose Your Path

Now that you've seen the failure, learn how to fix it and verify it.

<div class="grid cards" markdown>

-   :material-shield-check: **[Level 1: The Engineer](level1_policy.md)**
    ---
    Learn how to implement **Controls** that mitigate identified Risks. **Detect & Block** non-compliant models.

-   :material-chart-bar: **[Level 2: The Integrator](level2_integrator.md)**
    ---
    Log outcomes to MLOps tools and verify results visually in the **Dashboard**.

-   :material-fingerprint: **[Level 3: The Auditor](level3_auditor.md)**
    ---
    Learn how to perform a "Deep Dive" audit on complex data (Vision/Images) and generate cryptographic proofs.

-   :material-hospital-box: **[Level 4: The Architect](level4_annex_iv.md)**
    ---
    The Boss Level. Train a high-risk medical model and generate the massive Technical Documentation required by the EU AI Act.

</div>

---

## 📚 External References

- **EU AI Act**: [Full Legal Text (EUR-Lex)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52021PC0206)
- **ISO 42001**: [Artificial Intelligence Management System (AIMS)](https://www.iso.org/standard/81230.html)
- **NIST AI RMF**: [Risk Management Framework 1.0](https://www.nist.gov/itl/ai-risk-management-framework)
