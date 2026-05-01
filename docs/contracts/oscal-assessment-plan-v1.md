# OSCAL `assessment-plan` — Venturalítica v1 canonical contract

**Status:** normative (non-negotiable).
**Applies to:** every component that produces, transports or consumes a Venturalítica OSCAL Assessment Plan document — SaaS-style emitters, the `venturalitica` Python SDK, any downstream runtime proxy or enforcement gate that parses the envelope, and policy template fixtures.
**Source:** arXiv preprint *Making AI Compliance Evidence Machine-Readable* ([arXiv:2604.13767](https://arxiv.org/abs/2604.13767)) Listing 1 (§5 + §6).
**Invariants:**
1. Only `assessment-plan` is emitted by Venturalítica components.
2. Compliant parsers MAY accept `system-security-plan` for externally-authored policies (backwards compatibility) but no Venturalítica component emits it.
3. Every property listed below is preserved across the full round-trip (emitter → transport → SDK → re-emit).

---

## 1. Envelope

```json
{
  "assessment-plan": {
    "uuid": "<string; stable per (ai_system_version, declaration_timestamp)>",
    "metadata": {
      "title": "<human-readable policy title>",
      "oscal-version": "1.1.2",
      "published": "<ISO-8601 optional>",
      "last-modified": "<ISO-8601>"
    },
    "import-ssp": { "href": "<optional reference to an SSP if one exists>" },
    "control-implementations": [
      {
        "component-uuid": "<stable per AISystemVersion>",
        "description": "<e.g. 'AssuranceMeasure guardrails dispatched at DEPLOY time'>",
        "implemented-requirements": [ /* see §2 */ ]
      }
    ]
  }
}
```

No other roots appear in any SaaS/SDK-emitted file.

## 2. `implemented-requirements[]` — one per AssuranceMeasure

```json
{
  "uuid": "<AssuranceMeasure.id>",
  "control-id": "<OSCAL control id, e.g. A.6.2.4>",
  "description": "<human description of the measure>",
  "props": [ /* see §3 */ ]
}
```

## 3. `props[]` — the 16-property extension (paper Listing 1)

Required on every `implemented-requirement`:

| `name`                | Values (exhaustive)                                      | Semantics / paper reference |
|-----------------------|----------------------------------------------------------|-----------------------------|
| `metric_key`          | string (e.g. `demographic_parity_diff`, `auc_score`)     | Names the metric function in the SDK registry. |
| `operator`            | `<`, `<=`, `>`, `>=`, `==` (word aliases `lt/le/gt/ge/eq` accepted in) | Comparison against `threshold`. |
| `threshold`           | stringified number                                       | Acceptance bound. |
| `severity`            | `block` \| `warn` \| `info`                              | Failure criticality. |
| `enforcement_mode`    | `block` \| `warn` \| `monitor`                           | Runtime action on failure (Rust side). Legacy aliases `gate→block`, `audit→warn` accepted by parser but NEVER emitted. |
| `evaluation_method`   | `automated` \| `human` \| `hybrid`                       | Decides SDK `vl.enforce` vs proxy HITL. |
| `evaluation_window`   | `per-run` \| `periodic` \| `sliding-window`              | Consumed by the runtime proxy; defaults to `per-run`. |
| `target_type`         | `system` \| `dataset` \| `system_and_dataset`            | Which pipeline stage owns the check. |
| `lifecycle_phase`     | `design` \| `data_preparation` \| `training` \| `validation` \| `production` \| `monitoring` (repeat the prop for each applicable phase) | Selects which consumer (SDK or proxy) enforces. |

Optional (traceability — paper §5.4):

| `name`                      | Value                                             | Semantics |
|-----------------------------|---------------------------------------------------|-----------|
| `risk_id`                   | `<IdentifiedRisk.id>`                             | Links to the risk register. |
| `risk_title`                | string                                            | Denormalized for reading convenience. |
| `treatment_id`              | `<RiskTreatment.id>`                              | Which treatment the measure implements. |
| `policy_id`                 | `<Policy.id>`                                     | Which policy authorised this measure. |
| `objective_id`              | `<AIObjective.id>`                                | Which AI objective is served. |
| `threshold_justification`   | string                                            | Normative source for the threshold value (e.g. "EEOC Four-Fifths Rule"). |
| `risk_acceptance_criteria`  | string                                            | Residual-risk bound after treatment. |

Input bindings (paper §6.3):

| `name`                        | Value                                        | Semantics |
|-------------------------------|----------------------------------------------|-----------|
| `input:<key>`                 | column name in the request payload           | Maps the measure's metric input slots to columns. Example: `{"name":"input:protected","value":"gender"}`. Multiple `input:*` props per requirement are allowed. |

## 4. Case, canonicalization, and determinism

- Prop names lowercase with underscores (`enforcement_mode`, not `enforcementMode`).
- Prop values: lowercase for enums, verbatim for identifiers.
- Emitters MUST emit `operator` in symbolic form (`<`, `<=`, `>`, `>=`, `==`). Word aliases are parser-only.
- Emitters MUST emit `enforcement_mode` in the canonical triple (`block`/`warn`/`monitor`). Legacy aliases (`gate`, `audit`) are parser-only.
- Property order within `props[]` is stable: metric_key, operator, threshold, severity, enforcement_mode, evaluation_method, evaluation_window, target_type, lifecycle_phase*, risk_id, risk_title, treatment_id, policy_id, objective_id, threshold_justification, risk_acceptance_criteria, input:*. Stable order makes diffs reviewable.
- `uuid` values are stable across regeneration where possible (AssuranceMeasure.id, AISystemVersion.id, Organization.id). The top-level `assessment-plan.uuid` MAY change per declaration — it identifies the document, not the policy.

## 5. Consumer split

| Consumer                              | Phases consumed                       | Props consumed                                   |
|---------------------------------------|---------------------------------------|--------------------------------------------------|
| SDK training-time enforcer (`vl.enforce`) | `design`, `data_preparation`, `training`, `validation` | metric_key, operator, threshold, severity, enforcement_mode, input:* |
| Runtime enforcement proxy             | `production`, `monitoring`            | all of §3 (uses evaluation_window + evaluation_method for HITL routing) |
| Governance platform (SaaS)            | all phases (for UI + traceability)    | all of §3 |

Unknown props are ignored by every consumer (forward compatibility per paper §5.3).

## 6. What is NOT allowed

- Emitting a `system-security-plan` root from any SaaS or SDK code path. Downstream proxy parsers MAY retain a `system-security-plan` code branch **only** to accept externally-authored policies for backwards compatibility.
- Wrapping the policy in `{ "measures": [...] }`, `{ "controls": [...] }`, or any other native shortcut. There is one envelope (`assessment-plan`) and one per-measure shape (`implemented-requirement` with `props[]`).
- Emitting the legacy `gate` / `audit` enforcement values.
- Camel-case prop names (`enforcementMode`, `evaluationMethod`, …). These are application-internal and MUST be mapped to the snake-case OSCAL prop names at the edge.

## 7. Round-trip guarantee

Given any AssuranceMeasure row persisted by the SaaS, the round-trip is:

```
SaaS emit (assessment-plan) → SDK `vl pull` parse → SDK local representation
     → SDK `vl push` re-emit (assessment-plan subset if applicable)
     → SaaS parse → every prop from §3 is preserved byte-for-byte
```

This is enforced by `packages/venturalitica-sdk/tests/test_oscal_roundtrip.py` against the canonical fixture at `packages/venturalitica-sdk/tests/fixtures/oscal/assessment-plan.canonical.json`.

## 8. Fixtures

- **Canonical:** `tests/fixtures/oscal/assessment-plan.canonical.json` (in this SDK repository) — one measure per extension prop family; used as the round-trip reference. Downstream parsers (in any language) are encouraged to consume the same fixture for parity testing.
- **Rejection cases:** any compliant parser MUST refuse documents whose root is neither `assessment-plan` nor `system-security-plan`. The SDK exercises this guard in `tests/test_oscal_roundtrip.py::test_no_system_security_plan_leakage`.

## 9. Versioning

This document is `v1`. Any property addition/removal requires:
1. A new `oscal-assessment-plan-v<N>.md` superseding this file.
2. A migration note + back-compat policy: downstream parsers MUST accept both the previous and the new contract versions for at least one release cycle.
3. An entry in the SDK `CHANGELOG.md`.

`oscal-version` inside the metadata is pinned at `1.1.2` (NIST OSCAL schema version, independent of this contract's version).
