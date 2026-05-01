# Cross-component smoke — paper Listing 1 envelope

The OSCAL `assessment-plan` envelope from the arXiv preprint (arXiv:2604.13767)
(Listing 1) is consumed by three components. This document describes how
to verify they all stay in lock-step against the canonical fixture and
against each other.

## Components

| Component | Role | Entry point |
|---|---|---|
| SaaS (TypeScript) | Emit | `buildAssessmentPlan()` at `venturalitica/codegen/entities/assurance-measure/_generated/oscal-sidecar.ts` (imported via `@codegen/entities/assurance-measure/_generated/oscal-sidecar`) |
| SaaS REST API | Transport | `GET /api/pull?format=oscal` (route file: `venturalitica/src/app/api/pull/route.ts`) |
| SDK Python | Parse + execute | `venturalitica.cli.sync` (`vl pull`) at `packages/venturalitica-sdk/src/venturalitica/cli/sync.py` and `venturalitica.loader` |
| Proxy Rust (vl-fairness-gate) | Parse + enforce | `parse_oscal_document(doc: &serde_json::Value) -> Result<Vec<ParsedMeasure>>` at `vl-fairness-gate/src/oscal/parser.rs:13` |

### Function signatures

- TS emit (`oscal-sidecar.ts`):
  ```typescript
  export function buildAssessmentPlan(input: {
    aiSystemVersionId: string;
    orgSlug: string;
    aiSystemSlug: string;
    rows: OscalRow[];
  }): Record<string, unknown>
  ```
  Invoked from `venturalitica/src/app/actions/declare-conformity.ts:316`
  inside `dispatchProxyConfig()`; the resulting envelope is attached as
  `payload.policies` on the `proxy_config` SQS task.

- Rust parse (`parser.rs:13`):
  ```rust
  pub fn parse_oscal_document(doc: &serde_json::Value) -> Result<Vec<ParsedMeasure>>
  ```
  Accepts only `assessment-plan` or legacy `system-security-plan` roots
  (see `CLAUDE.md` "OSCAL Policy Format (non-negotiable)").

- SDK parse (`sync.py:36-56`): `vl pull` issues
  `GET {SAAS_URL}/api/pull?format=oscal`, asserts the response carries an
  `assessment-plan` root, flattens every `control-implementations[].
  implemented-requirements[]` into `all_requirements`, and writes the
  full document to `assessment_plan.oscal.yaml` and
  `.venturalitica/policy.oscal.json` (the path consumed by `monitor()`
  and `annex-iv`).

## Single source of truth

`packages/venturalitica-sdk/tests/fixtures/oscal/assessment-plan.canonical.json`
is shared verbatim across all three components:

- Python: read by `tests/test_oscal_roundtrip.py` (13 test functions →
  20 collected cases after parametrization — root shape, mandatory
  props, symbolic operators, severity/enforcement-mode vocabulary,
  traceability props, input bindings, JSON+YAML roundtrip, SSP-leakage
  guard).
- Rust: embedded via
  `include_str!("../../../packages/venturalitica-sdk/tests/fixtures/oscal/assessment-plan.canonical.json")`
  in `vl-fairness-gate/src/oscal/parser.rs:229` (test
  `test_parse_canonical_assessment_plan_fixture`).
- SaaS: covered by the unit suite under
  `venturalitica/src/lib/oscal/assurance-measure-sidecar.test.ts`,
  which round-trips through `buildAssessmentPlan()`.

## Cross-component matrix

|              | SDK Python | SaaS TS | Proxy Rust |
|--------------|------------|---------|------------|
| Emit         | n/a        | `buildAssessmentPlan()` | n/a |
| Parse        | `vl pull` + `loader` | round-trip in unit test | `parse_oscal_document` |

## Smoke procedure (manual)

### Smoke 1 — canonical fixture parses everywhere

```bash
# SDK Python
cd packages/venturalitica-sdk
VENTURALITICA_NO_ANALYTICS=1 uv run pytest tests/test_oscal_roundtrip.py -q
# Expected: 20 cases pass (13 functions, parametrized to 20)
```

```bash
# Proxy Rust
cd vl-fairness-gate
cargo test oscal::parser
# Expected: tests/parser.rs::test_parse_canonical_assessment_plan_fixture passes
```

```bash
# SaaS TS — covered by the SaaS unit suite
cd venturalitica
npm run test:unit -- oscal
# Expected: src/lib/oscal/assurance-measure-sidecar.test.ts passes
```

### Smoke 2 — SaaS-emitted plan parses in SDK and Rust (live)

This requires the SaaS dev stack running locally
(`docker-compose.dev.yml`).

```bash
# 1. Bring up the stack
docker-compose -f docker-compose.dev.yml up -d
cd venturalitica && npm run seed:fintech

# 2. From SDK, login and pull
mkdir -p /tmp/sdk-e2e && cd /tmp/sdk-e2e
SAAS_URL=http://localhost:3000 vl login          # alice@alpha.com
SAAS_URL=http://localhost:3000 vl pull
test -f .venturalitica/policy.oscal.json && echo "SDK parse OK"

# 3. From Rust, parse the same response
curl -s -H "Authorization: Bearer $(jq -r .key /tmp/sdk-e2e/.venturalitica/credentials.json)" \
     "http://localhost:3000/api/pull?format=oscal" \
     > /tmp/saas_emitted_assessment_plan.json
cd /home/morganrcu/proyectos/venturalitica-integration/vl-fairness-gate
SMOKE_FIXTURE=/tmp/saas_emitted_assessment_plan.json \
  cargo test smoke_saas_emitted_plan -- --include-ignored
```

If/when the smoke is fully automated in CI, see Task F1 (SaaS smoke
script: `venturalitica/scripts/smoke-emit-oscal.ts`) and Task F2 (Rust
integration test) of the v0.6.0 stabilization plan.

## Drift detection

Add to your release checklist before tagging:

- [ ] `pytest tests/test_oscal_roundtrip.py` — green (20 cases).
- [ ] `cargo test oscal::parser` in `vl-fairness-gate` — green
      (canonical-fixture test included).
- [ ] `npm run test:unit -- oscal` in `venturalitica` — green
      (`assurance-measure-sidecar.test.ts`).
- [ ] `git diff` over
      `tests/fixtures/oscal/assessment-plan.canonical.json` — only
      intentional, additive changes since the previous release tag.
- [ ] Verify `parse_oscal_document` still rejects any root other than
      `assessment-plan` (`vl-fairness-gate/src/oscal/parser.rs`) — no
      third root has been introduced.

## References

- Normative spec: `docs/contracts/oscal-assessment-plan-v1.md` at the
  integration-repo root (shared by SaaS, SDK and Proxy).
- Paper Listing 1: `docs/papers/ieee-computer-2026/main.tex`
  (root repo, not the SDK submodule) — arXiv preprint: https://arxiv.org/abs/2604.13767.
- Companion CHANGELOG entry: `packages/venturalitica-sdk/CHANGELOG.md`
  v0.6.0.
- Integration contract enforcement note: project root `CLAUDE.md`,
  section "OSCAL Policy Format (non-negotiable)".
