# Cross-component smoke — canonical NIST OSCAL v1.2.2 envelopes

The platform produces and consumes canonical NIST OSCAL v1.2.2 documents end-to-end. This document describes how to verify the three components stay in lock-step.

## Components

| Component | Role | Entry point |
|---|---|---|
| SaaS (TypeScript) — codegen sidecar | Emit policy | `buildComponentDefinition()` at `venturalitica/codegen/entities/assurance-measure/_generated/oscal-sidecar.ts` |
| SaaS (TypeScript) — hand-written mapper | Emit policy on pull path | `OSCALMapper.toComponentDefinition()` at `venturalitica/src/lib/oscal/mapper.ts` |
| SaaS REST API | Transport policy | `GET /api/pull?format=oscal` (`venturalitica/src/app/api/pull/route.ts`) |
| SaaS REST API | Transport evidence | `POST /api/push` (`venturalitica/src/app/api/push/route.ts`) — ajv-validates `assessment-results` envelopes |
| SDK Python | Pull + parse policy | `venturalitica.cli.sync` (`vl pull`) and `venturalitica.loader` |
| SDK Python | Push evidence | `venturalitica.cli.transfer` (`vl push`) — emits `assessment-results` documents |
| Proxy Rust (vl-fairness-gate) | Parse + enforce policy | `parse_oscal_document(doc: &serde_json::Value) -> Result<Vec<ParsedMeasure>>` at `vl-fairness-gate/src/oscal/parser.rs` |

### Envelopes

| Direction | Envelope | NIST root |
|---|---|---|
| SaaS → SQS → gate (policy) | canonical | `component-definition` |
| SaaS → SDK `vl pull` (policy) | canonical | `component-definition` |
| SDK `vl push` → SaaS `/api/push` (evidence) | canonical | `assessment-results` |

### Function signatures

- **TS emit (sidecar)** in `oscal-sidecar.ts` (generated):
  ```typescript
  export function buildComponentDefinition(input: {
    aiSystemVersionId: string;
    orgSlug: string;
    aiSystemSlug: string;
    aiSystemVersion?: string;
    timestamp?: Date;
    profileRef?: string;
    rows: OscalRow[];
  }): Record<string, unknown>
  ```
  Invoked from `venturalitica/src/app/actions/declare-conformity.ts` inside `dispatchProxyConfig()`. The result is validated via `validateComponentDefinition()` from `@venturalitica/oscal-types` BEFORE being attached as `payload.policies` on the SQS task.

- **TS emit (pull-path mapper)** in `mapper.ts`:
  ```typescript
  static toComponentDefinition(aiSystem: any, options?: OSCALExportOptions): {
    'component-definition': { ... }
  }
  ```
  Called by `AISystemDataService.formatAsOSCAL` to serve `/api/pull?format=oscal`. Validates via ajv before returning.

- **Rust parse** (`parser.rs`):
  ```rust
  pub fn parse_oscal_document(doc: &serde_json::Value) -> Result<Vec<ParsedMeasure>>
  ```
  Accepts `component-definition` (canonical) or `system-security-plan` (FedRAMP-style) only.

- **SDK pull** (`sync.py`): `vl pull` issues `GET {SAAS_URL}/api/pull?format=oscal`, asserts the response carries a `component-definition` root, flattens every `components[].control-implementations[].implemented-requirements[]` into `all_requirements`, and writes the full document to `assessment_plan.oscal.yaml` (kept as the cached filename for shell-script back-compat — its contents are now a `component-definition`) and `.venturalitica/policy.oscal.json` (the JSON twin consumed by `monitor()` and `annex-iv`).

## Single source of truth

Canonical NIST OSCAL v1.2.2 JSON Schemas, vendored once at `venturalitica/packages/oscal-types/schemas/v1.2.2/`:

- `oscal_component-definition_schema.json`
- `oscal_assessment-results_schema.json`
- `oscal_assessment-plan_schema.json` (for `import-ap` cross-refs)
- `oscal_complete_schema.json`

Every emitter calls `validateComponentDefinition` / `validateAssessmentResults` from `@venturalitica/oscal-types/validate` (ajv-backed). Every consumer (`/api/push`) calls the same on receipt. Round-trip tests at:

- TS: `venturalitica/src/lib/oscal/assurance-measure-sidecar.test.ts`, `venturalitica/src/lib/oscal/mapper.test.ts`, `venturalitica/src/lib/oscal/assessment-results.fixture.test.ts`.
- Rust: `vl-fairness-gate/src/oscal/parser.rs::test_parse_oscal_component_definition`.
- Python: `packages/venturalitica-sdk/tests/test_loader.py`, `tests/test_cli_sync.py`, `tests/test_smoke_core_api.py`.

## Smoke procedure (manual)

### Smoke 1 — unit-test stack passes on each component

```bash
# SDK Python
cd packages/venturalitica-sdk
.venv/bin/pytest -q tests/test_loader.py tests/test_cli_sync.py tests/test_smoke_core_api.py
# Expected: 28 passed
```

```bash
# Proxy Rust
cd vl-fairness-gate
cargo test oscal::parser
# Expected: 4 passed (test_parse_oscal_ssp, test_parse_oscal_component_definition,
# test_unknown_root_errors_with_helpful_message, test_legacy_assessment_plan_root_is_rejected)
```

```bash
# SaaS TS
cd venturalitica
npx vitest run src/lib/oscal/ src/app/api/push/
# Expected: 63 passed
```

### Smoke 2 — SaaS-emitted policy parses end-to-end (live)

Requires the dev stack running (`docker-compose.dev.yml`).

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
     > /tmp/saas_emitted_component_definition.json

# 4. Verify it's canonical
jq 'keys[0]' /tmp/saas_emitted_component_definition.json   # → "component-definition"
```

## Drift detection

Add to your release checklist before tagging:

- [ ] `pytest -q tests/test_loader.py tests/test_cli_sync.py tests/test_smoke_core_api.py` — green (28+ tests).
- [ ] `cargo test oscal::parser` in `vl-fairness-gate` — green (4+ tests).
- [ ] `npx vitest run src/lib/oscal/ src/app/api/push/` in `venturalitica` — green (63+ tests).
- [ ] `git diff` over `venturalitica/packages/oscal-types/schemas/v1.2.2/` — empty (vendored NIST schemas are pinned; bump requires a coordinated cross-repo change).
- [ ] Verify `parse_oscal_document` rejects unknown roots (`vl-fairness-gate/src/oscal/parser.rs::test_unknown_root_errors_with_helpful_message`).

## References

- Live contract: `CLAUDE.md` *"OSCAL Policy Format (non-negotiable)"* in the venturalitica monorepo root.
- Corrigendum to IEEE Computer Listing 1: `docs/papers/ieee-computer-2026/ERRATUM.md`.
- Vendored NIST schemas + TS types + ajv validators + UUID v5 helpers: `venturalitica/packages/oscal-types/`.
- Companion CHANGELOG entry: `packages/venturalitica-sdk/CHANGELOG.md` v0.6.4.
