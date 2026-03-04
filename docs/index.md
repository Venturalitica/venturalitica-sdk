# Venturalítica

**The Glass Box for High-Risk AI.**

Venturalítica transforms your Python code into **Legal Evidence**. It automatically maps your technical metrics, data audits, and execution logs to the **EU AI Act (Articles 9-15)** without leaving your local environment.

---

## Quickstart in 60 Seconds

```bash
pip install venturalitica
```

Detect bias in your datasets or models with one line of code:

```python
import venturalitica as vl

# Run a full audit on the built-in loan scenario
results = vl.quickstart('loan')
```

Then launch the **Glass Box Dashboard** to explore results:

```bash
venturalitica ui
```

---

## Key Features

| Feature | Description |
| :--- | :--- |
| **`enforce()`** | Audit datasets and models against OSCAL policies with 35+ built-in metrics. |
| **`monitor()`** | Wrap training runs with automatic evidence collection (BOM, hardware, carbon). |
| **Glass Box Dashboard** | 4-phase regulatory workflow: Identity, Policy, Verify, Report. |
| **Policy as Code** | Define assurance rules in OSCAL `assessment-plan` format. |
| **Column Binding** | Decouple policies from schemas via synonym-based column resolution. |
| **Local Sovereignty** | Zero-cloud dependency. All enforcement runs locally. |
| **Annex IV** | Auto-draft technical documentation from local traces. |

---

## Documentation

| Guide | Description |
| :--- | :--- |
| **[Quickstart](quickstart.md)** | Run a full compliance scan in 2 minutes. |
| **[API Reference](api.md)** | `enforce()`, `monitor()`, `wrap()`, `quickstart()`, `PolicyManager`. |
| **[Metrics Reference](metrics.md)** | All 35+ metrics across 7 categories. |
| **[Policy Authoring](policy-authoring.md)** | Write OSCAL policies from scratch. |
| **[Dashboard Guide](dashboard.md)** | The Glass Box 4-phase workflow. |
| **[Column Binding](column-binding.md)** | Map abstract names to DataFrame columns. |
| **[Probes Reference](probes.md)** | 7 evidence probes for EU AI Act compliance. |
| **[Experimental Features](experimental.md)** | CLI `login`/`pull`/`push` (SaaS preview). |

### Academy (Step-by-Step Learning)

| Level | Role | Focus |
| :--- | :--- | :--- |
| **[Level 1](academy/level1_policy.md)** | Policy Author | Write your first OSCAL policy for the loan scenario. |
| **[Level 2](academy/level2_integrator.md)** | Integrator | Add `enforce()` to your ML pipeline. |
| **[Level 3](academy/level3_auditor.md)** | Auditor | Review evidence and interpret results. |
| **[Level 4](academy/level4_annex_iv.md)** | Compliance Lead | Generate Annex IV technical documentation. |

### Tutorials

- **[Writing Code-First Policy](tutorials/01_writing_policy.md)** -- Translate legal requirements into OSCAL controls.

---

## Installation

```bash
pip install venturalitica
```

Requires Python 3.9+. For the Dashboard, the optional `dashboard` extra is included by default.

---

## Links

[Quickstart Guide](quickstart.md) | [API Reference](api.md) | [GitHub](https://github.com/venturalitica/venturalitica-sdk)

*   **Found a bug or want to propose a feature?** Open a **[GitHub Issue](https://github.com/venturalitica/venturalitica-sdk/issues/new)**.

(c) 2026 Venturalítica | Built for Responsible AI
