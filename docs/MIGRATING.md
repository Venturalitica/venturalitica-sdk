# Migrating to v0.6.4

Companion to the IEEE Computer paper *"An OSCAL Profile for AI Assurance"*. Listing 1 of the paper is corrected in `docs/papers/ieee-computer-2026/ERRATUM.md` (venturalitica monorepo) — the substantive 16-property AI Assurance profile is unchanged; only the document wrapper is now canonical NIST OSCAL v1.2.2.

## Why this version

The platform produces and consumes **canonical NIST OSCAL v1.2.2** wherever it serialises an OSCAL document:

| Direction | Envelope |
|---|---|
| SaaS → SQS → fairness gate (policy descriptor) | **`component-definition`** |
| SaaS → SDK `vl pull` (policy descriptor) | **`component-definition`** |
| SDK `vl push` → SaaS `/api/push` (evidence) | **`assessment-results`** |

Both envelopes validate against the official NIST schemas vendored in `venturalitica/packages/oscal-types/schemas/v1.2.2/`. Every emitter calls `validateComponentDefinition` / `validateAssessmentResults` from `@venturalitica/oscal-types` before sending; every consumer calls the same on receipt. Schema-invalid documents never cross a process boundary.

The prior non-canonical envelope (`assessment-plan + control-implementations[]`, used through April 2026) is **no longer accepted** anywhere in the platform.

## Breaking changes (0.6.4)

### 1. Pulled policy envelope is `component-definition`

`vl pull` now requires the SaaS to return:

```yaml
component-definition:
  uuid: <uuid-v5>
  metadata:
    title: ...
    last-modified: <iso8601>
    version: "1"
    oscal-version: "1.2.2"
  components:
    - uuid: <uuid-v5>
      type: software
      title: <ai-system-slug> v<version>
      description: ...
      control-implementations:
        - uuid: <uuid-v5>
          source: "#vl-ai-assurance-profile-2026"
          description: ...
          implemented-requirements:
            - uuid: <uuid-v5>
              control-id: ...
              description: ...
              props: [ ... 16 AI Assurance props ... ]
```

Legacy `assessment-plan + control-implementations[]` responses raise `ValueError` immediately.

### 2. Input-binding prop names use `.` (not `:`)

NIST `prop.name` regex `^(\p{L}|_)(\p{L}|\p{N}|[.\-_])*$` rejects `:`. The canonical form is `input.<slot>`:

```yaml
props:
  - { name: input.target,    value: y_true }
  - { name: input.prediction, value: y_pred }
  - { name: input.dimension, value: gender }
```

The SDK loader, `cli/sync.py`, and the quality-metric kwargs (`calc_class_imbalance`, `calc_group_min_positive_rate`, `calc_provenance_completeness`) all read `input.<slot>` only.

### 3. SDK loader root keys

`OSCALPolicyLoader` accepts canonical NIST roots only:

- `catalog`
- `profile`
- `component-definition`
- `system-security-plan`

The non-canonical `assessment-plan + control-implementations[]` root is rejected.

### 4. UUIDs in emitted OSCAL are RFC 4122 v5 (not prefixed cuids)

Every `uuid` field in documents the SaaS emits is a **deterministic UUID v5** derived from the source identifier via a fixed Venturalítica namespace. Same input → same UUID across runs, so external systems can correlate documents over time.

## Recommended upgrade steps

```bash
pip install --upgrade venturalitica==0.6.4
rm -f .venturalitica/policy.oscal.json     # cached legacy envelope
rm -f .venturalitica/model_policy.oscal.yaml .venturalitica/data_policy.oscal.yaml  # if any
vl pull                                    # fetches canonical component-definition
```

Update any tooling that parses local OSCAL artefacts:

- `assessment_plan.oscal.yaml` still exists as the cached file name (preserved for back-compat with shell scripts that look it up by name) but its **contents** are now a `component-definition` envelope.
- `.venturalitica/policy.oscal.json` is the JSON twin.

## Authoring custom policy YAMLs

If you hand-write `.oscal.yaml` files (instead of pulling from the SaaS), use a canonical NIST root. The simplest shape:

```yaml
component-definition:
  metadata:
    title: My policy
    version: "1"
  components:
    - control-implementations:
        - implemented-requirements:
            - control-id: my-control
              props:
                - { name: metric_key, value: accuracy_score }
                - { name: threshold,  value: "0.85" }
                - { name: operator,   value: ">=" }
                - { name: input.target,    value: y_true }
                - { name: input.prediction, value: y_pred }
```

## References

- Live contract: `CLAUDE.md` *"OSCAL Policy Format (non-negotiable)"* in the venturalitica monorepo.
- Corrigendum to IEEE Computer Listing 1: `docs/papers/ieee-computer-2026/ERRATUM.md`.
- Vendored NIST schemas + TS types: `venturalitica/packages/oscal-types/`.
- Changelog: [`CHANGELOG.md`](../CHANGELOG.md).
