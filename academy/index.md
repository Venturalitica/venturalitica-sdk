# Zero to Pro: The 5-Minute Journey 🚀

**Goal**: Transform from "Python Developer" to "AI Governance Engineer" in 3 steps.

______________________________________________________________________

## The Philosophy: Compliance as Code

You are used to `pytest` for checking if your function adds 2+2 correctly. But how do you test if your AI model respects **Human Rights**?

Venturalítica treats "Governance" as a dependency. Instead of vague legal advice, you define stricter **Policies (OSCAL)**. Your CI/CD pipeline enforces them just like linter rules.

### The Curriculum

| Level                                                                                               | Role           | Goal                                         | Project                                                                                                                                                   |
| --------------------------------------------------------------------------------------------------- | -------------- | -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **[Start Here](#step-1-install)**                                                                   | **Developer**  | Run your first audit in < 60s.               | [loan-credit-scoring](https://github.com/venturalitica/venturalitica-sdk-samples/tree/main/scenarios/loan-credit-scoring)                                 |
| **[Level 1](https://venturalitica.github.io/venturalitica-sdk/academy/level1_policy/index.md)**     | **Engineer**   | **Implement Controls** for identified Risks. | [00_engineer_policy.ipynb](https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/scenarios/loan-credit-scoring/00_engineer_policy.ipynb)   |
| **[Level 2](https://venturalitica.github.io/venturalitica-sdk/academy/level2_integrator/index.md)** | **Integrator** | **Viz & MLOps**: "Compliance as Metadata".   | [03_mlops_integration.py](https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/scenarios/loan-credit-scoring/03_mlops_integration.py)     |
| **[Level 3](https://venturalitica.github.io/venturalitica-sdk/academy/level3_auditor/index.md)**    | **Auditor**    | Proof: "Trust the Glass Box".                | [01_governance_audit.ipynb](https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/scenarios/loan-credit-scoring/01_governance_audit.ipynb) |
| **[Level 4](https://venturalitica.github.io/venturalitica-sdk/academy/level4_annex_iv/index.md)**   | **Architect**  | GenAI Docs: "Annex IV".                      | `loan-credit-scoring` (Annex IV)                                                                                                                          |

______________________________________________________________________

## Step 1: Install

We recommend **uv** for blazing speed, or standard `pip`.

```
uv pip install git+https://github.com/Venturalitica/venturalitica-sdk.git
# OR
pip install git+https://github.com/Venturalitica/venturalitica-sdk.git
```

## Step 2: Get the Code 📦

To follow the **Academy**, clone the samples repository. This will be your working directory for all levels.

```
git clone https://github.com/venturalitica/venturalitica-sdk-samples.git
cd venturalitica-sdk-samples/scenarios/loan-credit-scoring
```

## Step 3: Run Your First Audit ⚡

Run this single line of code. It downloads a dataset, loads a policy, and audits a model.

```
import venturalitica as vl

# Run the 'loan' scenario
vl.quickstart('loan')
```

**Output:**

```
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
> - **The Policy**: `ratio > 0.5` (The Law).
> - **The Reality**: `0.361` (Your Code).
> - **The Verdict**: `❌ FAIL` (The Compliance Gap).

You didn't need a lawyer. You just needed a visible test failure.

## Step 4: Choose Your Path

Now that you've seen the failure, learn how to fix it and verify it.

- ## **[Level 1: The Engineer](https://venturalitica.github.io/venturalitica-sdk/academy/level1_policy/index.md)**
  Learn how to implement **Controls** that mitigate identified Risks. **Detect & Block** non-compliant models.
- ## **[Level 2: The Integrator](https://venturalitica.github.io/venturalitica-sdk/academy/level2_integrator/index.md)**
  Log outcomes to MLOps tools and verify results visually in the **Dashboard**.
- ## **[Level 3: The Auditor](https://venturalitica.github.io/venturalitica-sdk/academy/level3_auditor/index.md)**
  Learn how to perform a "Glass Box" audit on the loan model and generate cryptographic proofs.
- ## **[Level 4: The Architect](https://venturalitica.github.io/venturalitica-sdk/academy/level4_annex_iv/index.md)**
  The Boss Level. Train a high-risk financial model and generate the massive Technical Documentation required by the EU AI Act.

______________________________________________________________________

## 📚 External References

- **EU AI Act**: [Full Legal Text (EUR-Lex)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52021PC0206)
- **ISO 42001**: [Artificial Intelligence Management System (AIMS)](https://www.iso.org/standard/81230.html)
- **NIST AI RMF**: [Risk Management Framework 1.0](https://www.nist.gov/itl/ai-risk-management-framework)
