# Compliance Mapping: EU AI Act & ISO 42001

This document maps Venturalitica SDK capabilities to the **EU AI Act** articles and **ISO/IEC 42001** controls relevant to high-risk AI systems.

---

## EU AI Act Article Mapping

### Article 9: Risk Management System

**Requirement**: Establish a risk management system throughout the AI system lifecycle.

| SDK Capability | How It Fulfills Art 9 |
| :--- | :--- |
| OSCAL policy files | Risk controls codified as machine-readable rules |
| `enforce()` | Automated risk evaluation against defined controls |
| Dashboard Phase 1 | System identity and risk context documentation |
| Dashboard Phase 2 | Visual policy editor for risk control definition |

**Example**: Define a risk control that checks age disparity:

```yaml
- control-id: credit-age-disparate
  description: "Age disparate impact ratio > 0.5"
  props:
    - name: metric_key
      value: disparate_impact
    - name: threshold
      value: "0.50"
    - name: operator
      value: gt
    - name: "input:dimension"
      value: age
```

---

### Article 10: Data and Data Governance

**Requirement**: Training, validation, and testing data sets shall be relevant, representative, free of errors, and complete.

| SDK Capability | How It Fulfills Art 10 |
| :--- | :--- |
| `class_imbalance` metric | Checks minority class representation |
| `disparate_impact` metric | Checks group-level selection rates |
| `data_completeness` metric | Measures missing values |
| `k_anonymity`, `l_diversity`, `t_closeness` | Privacy-preserving data quality |
| Data policy pattern | Separate `data_policy.oscal.yaml` for pre-training checks |

**Key metrics for Art 10**:

| Metric | Art 10 Clause | Purpose |
| :--- | :--- | :--- |
| `class_imbalance` | 10.3 (representative) | Ensure minority classes are not erased |
| `disparate_impact` | 10.2.f (bias examination) | Four-Fifths Rule across groups |
| `data_completeness` | 10.3 (free of errors) | Detect missing data |
| `group_min_positive_rate` | 10.3 (representative) | Minimum positive rate per group |

---

### Article 11: Technical Documentation (Annex IV)

**Requirement**: Technical documentation shall be drawn up before the AI system is placed on the market.

| SDK Capability | How It Fulfills Art 11 |
| :--- | :--- |
| `monitor()` trace files | Automatic evidence collection (code, data, hardware) |
| Evidence hash (SHA-256) | Cryptographic proof of execution integrity |
| Dashboard Phase 4 | Annex IV document generation via LLM |
| BOM probe | Software bill of materials for reproducibility |

**Evidence files produced**:

```text
.venturalitica/
  trace_<session>.json    # Execution trace with AST analysis
  results.json            # Compliance results per control
  Annex_IV.md             # Generated documentation (Phase 4)
```

---

### Article 13: Transparency

**Requirement**: High-risk AI systems shall be designed to ensure their operation is sufficiently transparent.

| SDK Capability | How It Fulfills Art 13 |
| :--- | :--- |
| Glass Box method | Full execution trace, not just results |
| AST code analysis | Records which functions were called |
| Data fingerprinting | SHA-256 of input data at runtime |
| Artifact probe | Hash of policy files used |

---

### Article 15: Accuracy, Robustness, and Cybersecurity

**Requirement**: High-risk AI systems shall achieve an appropriate level of accuracy, robustness, and cybersecurity.

| SDK Capability | How It Fulfills Art 15 |
| :--- | :--- |
| `accuracy_score`, `precision_score`, `recall_score`, `f1_score` | Performance metrics |
| `demographic_parity_diff`, `equal_opportunity_diff` | Fairness metrics on model predictions |
| Model policy pattern | Separate `model_policy.oscal.yaml` for post-training checks |
| Hardware probe | CPU, RAM, GPU monitoring for robustness evidence |
| Carbon probe | Energy consumption tracking |

**Key metrics for Art 15**:

| Metric | Art 15 Clause | Purpose |
| :--- | :--- | :--- |
| `accuracy_score` | 15.1 (accuracy) | Model achieves minimum accuracy |
| `demographic_parity_diff` | 15.3 (non-discrimination) | Prediction rates are fair |
| `equalized_odds_ratio` | 15.3 (non-discrimination) | Error rates are equitable |
| `counterfactual_fairness` | 15.3 (non-discrimination) | Causal fairness analysis |

---

## ISO/IEC 42001 Mapping

ISO 42001 defines an **AI Management System (AIMS)** framework. Venturalitica maps to the following control areas:

### Annex A Controls

| ISO 42001 Control | Description | SDK Mapping |
| :--- | :--- | :--- |
| **A.2** AI Policy | Organization-level AI policy | OSCAL policy files define machine-readable policies |
| **A.4** AI Risk Assessment | Identify and assess AI risks | `enforce()` evaluates controls; Dashboard Phase 2 visualizes risks |
| **A.5** AI Risk Treatment | Implement controls to mitigate risks | OSCAL controls with thresholds implement risk treatment |
| **A.6** AI System Impact Assessment | Assess impact on individuals/groups | Fairness metrics (`disparate_impact`, `demographic_parity_diff`) |
| **A.7** Data for AI Systems | Data quality management | Data policy pattern + data quality metrics |
| **A.8** AI System Documentation | Document AI system lifecycle | `monitor()` traces + Dashboard Phase 4 (Annex IV generation) |
| **A.9** AI System Performance | Monitor system performance | Performance metrics + `monitor()` evidence collection |
| **A.10** Third-party and Customer Relations | Supply chain transparency | BOM probe captures all dependencies |

### Clause 6: Planning

| ISO 42001 Clause | Description | SDK Mapping |
| :--- | :--- | :--- |
| 6.1 Risk assessment | Determine risks and opportunities | OSCAL policy defines measurable risk thresholds |
| 6.2 AI objectives | Set measurable objectives | Each OSCAL control is a measurable objective with pass/fail |

### Clause 9: Performance Evaluation

| ISO 42001 Clause | Description | SDK Mapping |
| :--- | :--- | :--- |
| 9.1 Monitoring | Monitor AI system performance | `enforce()` + `monitor()` provide continuous evaluation |
| 9.2 Internal audit | Audit the AIMS | Evidence traces provide audit trail |
| 9.3 Management review | Review AIMS effectiveness | Dashboard provides visual review interface |

### Clause 10: Improvement

| ISO 42001 Clause | Description | SDK Mapping |
| :--- | :--- | :--- |
| 10.1 Nonconformity | Handle control failures | `enforce()` flags failures; `strict=True` raises exceptions |
| 10.2 Continual improvement | Improve the AIMS | Version policies, re-run audits, track improvement over time |

---

## HUDERIA: Council of Europe Framework Convention on AI

**HUDERIA** (Human Rights, Democracy and Rule of Law Impact Assessment) is a non-binding Council of Europe methodology for evaluating AI impact on fundamental rights, published February 2026. It complements the EU AI Act and GDPR with a human rights lens.

HUDERIA defines the **COBRA** (Context-Based Risk Analysis) methodology with three resources:
- **Resource A**: Application context (non-metrizable organizational declarations)
- **Resource B**: Design & development context (pre-training and post-training)
- **Resource C**: Deployment context (pre-promotion gates in model registries)

The Venturalitica SDK implements **Resource B** (Gate G2: post-training evaluation) and **Resource C** (Gate G3: pre-promotion gates), which map directly to CI/CD compliance checkpoints.

### HUDERIA COBRA Resource B: Design & Development

Gate G2 (post-training, pre-release) evaluates design and development risks. SDK metrics are mapped as follows:

| COBRA Control | Description | SDK Metric | Configured in |
| :--- | :--- | :--- | :--- |
| **B.5.1** Data Quality | Completeness and representativeness | `data_completeness` | `huderia-cobra-design.oscal.yaml` |
| **B.5.1** Class Balance | Training set imbalance indicator | `class_imbalance` | `huderia-cobra-design.oscal.yaml` |
| **B.5.2** Privacy Protection | Quasi-identifier group anonymization | `k_anonymity` | `huderia-cobra-design.oscal.yaml` |
| **B.5.3** Data Integrity | Provenance and audit trail completeness | `provenance_completeness` | `huderia-cobra-design.oscal.yaml` |
| **B.6.1** Bias: Causal | Causal pathways to protected attribute bias | `causal_fairness_diagnostic` | `huderia-cobra-design.oscal.yaml` |
| **B.6.1** Bias: Output Parity | Favorable outcome rate disparity | `disparate_impact` | `huderia-cobra-design.oscal.yaml` |
| **B.6.1** Bias: Counterfactual | Causal independence of predictions | `counterfactual_fairness` | `huderia-cobra-design.oscal.yaml` |
| **B.6.3** Eval: Demographic Parity | Positive outcome rate difference across groups | `demographic_parity_diff` | `huderia-cobra-design.oscal.yaml` |
| **B.6.3** Eval: Equal Opportunity | True positive rate difference across groups | `equal_opportunity_diff` | `huderia-cobra-design.oscal.yaml` |
| **B.6.3** Eval: Equalized Odds | Both TPR and FPR equalization | `equalized_odds_ratio` | `huderia-cobra-design.oscal.yaml` |
| **B.6.3** Eval: Predictive Parity | Precision (PPV) parity across groups | `predictive_parity` | `huderia-cobra-design.oscal.yaml` |
| **B.6.5** Model Performance | Minimum model effectiveness threshold | `f1_score`, `accuracy_score` | `huderia-cobra-design.oscal.yaml` |

**Usage**: Enforce HUDERIA B controls during post-training evaluation:

```bash
VENTURALITICA_STRICT=true uv run venturalitica enforce \
    --data eval_dataset.csv \
    --policy src/venturalitica/policies/templates/huderia-cobra-design.oscal.yaml \
    --target target_column \
    --prediction prediction_column
```

### HUDERIA COBRA Resource C: Deployment (Pre-Release)

Gate G3 (pre-promotion in model registries, e.g., SageMaker, MLflow) evaluates deployment-readiness risks with stronger privacy guarantees:

| COBRA Control | Description | SDK Metric | Configured in |
| :--- | :--- | :--- | :--- |
| **C.1.1** Privacy: L-Diversity | Minimum distinct sensitive values per QI group | `l_diversity` | `huderia-cobra-prerelease.oscal.yaml` |
| **C.1.1** Privacy: T-Closeness | Maximum distribution divergence (stronger than l-diversity) | `t_closeness` | `huderia-cobra-prerelease.oscal.yaml` |
| **C.1.2** Data Minimization | Proportion of sensitive vs. non-sensitive features | `data_minimization` | `huderia-cobra-prerelease.oscal.yaml` |
| **C.2.1** Non-Discrimination: Odds | Equalized odds ratio across groups | `equalized_odds_ratio` | `huderia-cobra-prerelease.oscal.yaml` |
| **C.2.1** Non-Discrimination: Impact | Disparate impact ratio across groups | `disparate_impact` | `huderia-cobra-prerelease.oscal.yaml` |
| **C.2.1** Non-Discrimination: Causal | Counterfactual fairness (protected attr. independence) | `counterfactual_fairness` | `huderia-cobra-prerelease.oscal.yaml` |

**Usage**: Gate model promotion with HUDERIA C controls:

```bash
VENTURALITICA_STRICT=true uv run venturalitica enforce \
    --data test_dataset.csv \
    --policy src/venturalitica/policies/templates/huderia-cobra-prerelease.oscal.yaml \
    --target target_column \
    --prediction prediction_column
```

### Template Configuration

Both HUDERIA templates ship with `null` thresholds. Organizations must configure thresholds based on:
- **Regulatory context** (e.g., GDPR-regulated EU public sector: k≥20; internal R&D: k≥5)
- **Protected attributes** (e.g., gender, race, age)
- **Sensitive attributes** (e.g., diagnosis, income)
- **Risk tolerance** (high-risk systems require stricter fairness thresholds)

See [full scenario example](../../../venturalitica-scenario-huderia-cobra-public-sector/) for concrete threshold configuration.

---

## The Two-Policy Pattern and Regulatory Mapping

Venturalitica's two-policy pattern maps directly to the regulatory structure:

```text
Regulation          Policy File               SDK Function          Phase
-----------         ---------------           ----------------      -----
Art 10 (Data)   --> data_policy.oscal.yaml --> enforce(target=...)  Pre-training
Art 15 (Model)  --> model_policy.oscal.yaml-> enforce(prediction=..) Post-training
Art 11 (Docs)   --> (generated)            --> Dashboard Phase 4    Reporting
Art 9 (Risk)    --> (both policies)        --> All of the above     Continuous
```

---

## Audit Evidence Chain

A complete compliance audit produces the following evidence chain:

| Evidence | EU AI Act | ISO 42001 | File |
| :--- | :--- | :--- | :--- |
| Policy definition | Art 9 | A.2, A.5 | `*.oscal.yaml` |
| Data quality results | Art 10 | A.7 | `results.json` |
| Model fairness results | Art 15 | A.6, A.9 | `results.json` |
| Execution trace | Art 13 | A.8 | `trace_*.json` |
| Software BOM | Art 15 | A.10 | `trace_*.json` (BOM section) |
| Hardware/carbon metrics | Art 15 | A.9 | `trace_*.json` (probes) |
| Technical documentation | Art 11 / Annex IV | A.8 | `Annex_IV.md` |

---

## Related

- **[Full Lifecycle](full-lifecycle.md)** -- Step-by-step guide implementing this mapping
- **[Policy Authoring](policy-authoring.md)** -- Write OSCAL controls for each article
- **[Metrics Reference](metrics.md)** -- All available metrics by category
- **[Probes Reference](probes.md)** -- Evidence probes mapped to EU AI Act articles
- **[Dashboard Guide](dashboard.md)** -- 4-phase workflow aligned with regulatory requirements
