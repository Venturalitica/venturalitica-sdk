# Changelog - venturalitica-sdk

All notable changes to this project will be documented in this file.

## [0.6.3] - 2026-05-16

### Changed (wire-compatible hotfix)

- **OSCAL canon migration.** The SDK pull path (`vl pull`) now accepts the canonical NIST OSCAL v1.2.2 **`component-definition`** root as the policy envelope returned by the SaaS, alongside the legacy `assessment-plan` root which keeps working with a deprecation warning. The cached `.venturalitica/policy.oscal.json` reader is symmetric.
- **Input-binding prop name.** The canonical prefix for input bindings is now **`input.<slot>`** (dot allowed by the NIST `prop.name` regex `^(\p{L}|_)(\p{L}|\p{N}|[.\-_])*$`). The legacy `input:<slot>` prefix kept failing official schema validation — accepted as a transitional alias in `loader.py` so old policies still load. Helper functions `_is_input_prop` / `_input_slot` collapse the two forms behind the scenes.

### Why this hotfix

A coordinated cross-repo migration in the Venturalítica monorepo replaced the platform's non-canonical OSCAL envelope (`assessment-plan + control-implementations[]`, documented in the IEEE Computer paper "An OSCAL Profile for AI Assurance" Listing 1) with the canonical NIST OSCAL v1.2.2 wire shape. The 16-property AI Assurance profile from Table 1 of the paper is unchanged; only the document wrapper and one prop-name separator changed. See `docs/papers/ieee-computer-2026/ERRATUM.md` for the full corrigendum.

The SaaS side (`venturalitica` repo, commits `8aa5f46a` and the Phase 3 mapper migration) now emits the canonical shape. The Rust fairness gate (`vl-fairness-gate`, commit `24a0334`) accepts the canonical root via SQS. This SDK hotfix closes the loop on the pull path so installed clients continue to work against both the migrated SaaS (canonical) and any unmigrated mirror (legacy).

**Migration guidance** for SDK users:
- No code changes required. The SDK reads whichever envelope the SaaS happens to return.
- Re-running `vl pull` after the SaaS upgrade will produce a `policy.oscal.json` with the new shape and the new `input.<slot>` prop names.
- Custom OSCAL YAML authored locally with `input:<slot>` keeps working; migrate to `input.<slot>` at your convenience for forward-compatibility.

## [0.6.2] - 2026-05-01

### Changed (docs only — no code changes vs 0.6.1)
- `docs/contracts/oscal-assessment-plan-v1.md` is now implementation-agnostic. The previous draft referenced internal Venturalítica file paths (`vl-fairness-gate/src/oscal/parser.rs`, `pathfinder`, specific SaaS source files); the contract is normative for **any** OSCAL Assessment Plan producer/consumer and should not enumerate specific implementations.
- The internal cross-component smoke procedure moved from `docs/contracts/cross-component-smoke.md` to `docs/development/cross-component-smoke.md`. It documents the smoke runbook for the Venturalítica SaaS, SDK and Rust proxy and is **not** part of the public contract.

### Why this hotfix
A user-reported issue against v0.6.1: the normative OSCAL contract spec (`oscal-assessment-plan-v1.md`) was tied to specific internal component paths (`vl-fairness-gate`, internal SaaS source). A normative contract must be implementation-agnostic so that third-party OSCAL parsers can implement it without depending on Venturalítica internals. v0.6.2 generalises the prose; the 16 props, the envelope shape, the canonicalisation rules and every other normative invariant are unchanged.

## [0.6.1] - 2026-05-01

### Added
- `vl` CLI alias as a shorter shortcut for the `venturalitica` command. Both `vl pull` and `venturalitica pull` now work identically; the docs (Starlight, MIGRATING, RELEASE_NOTES) standardise on `vl` as the canonical short form.

### Why this hotfix
v0.6.0 shipped without the `vl` script entry-point even though all the documentation (Quickstart, Migrating guide, Experimental features, OSCAL contract, cross-component smoke) referenced `vl pull / vl push / vl login / vl ui` as the canonical CLI. Users who installed `pip install venturalitica==0.6.0` and copied the snippets verbatim hit `command not found: vl`. This release adds the alias so the docs match the package.

## [0.6.0] - 2026-04-18

### OSCAL unification — one dialect end-to-end

Replaces the split `model_policy` / `data_policy` SSP emission with a single
`assessment-plan` document covering every AssuranceMeasure the SaaS
declares. Matches Listing 1 of the arXiv preprint *Making AI Compliance Evidence Machine-Readable* (Cilla Ugarte et al., 2026, arXiv:2604.13767) verbatim.

**Breaking changes** (no backward-compat shims):
- `vl pull` now writes `assessment_plan.oscal.yaml` as the source of
  truth. The legacy `model_policy.oscal.yaml` / `data_policy.oscal.yaml`
  are still emitted for one release as filtered views keyed on
  `target_type`, but they are no longer authoritative.
- SaaS-emitted OSCAL no longer has a `system-security-plan` root. The
  parser still accepts SSPs from external (customer-authored) policies,
  but nothing in the SaaS or SDK emits them.
- `OSCALMapper.toMultiSSP` / `.toSSP` / `.buildSSP` deleted. Replace
  with `OSCALMapper.toAssessmentPlan(aiSystem, options?)`.

### Agentic Annex IV writer

- New `vl export-annex-iv --agentic` fills §1/§2/§3/§5/§8/§9 narrative
  sections via a local Ollama model (default `mistral`). `--provider
  cloud` routes to Mistral managed if `MISTRAL_API_KEY` is set.
- `--cache` (default) reuses `.venturalitica/annex_iv.cache.json` across
  demo recordings. Cache key: `(language, model, run_id, policy_hash)`
  — invalidates on any drift. `--force-regenerate` overrides.
- §4 (performance metrics) / §6 (POA&M) / §7 (standards) are derived
  deterministically from the OSCAL Assessment Results + Assessment
  Plan, never overwritten by the LLM.

### Round-trip contract test

- New `tests/test_oscal_roundtrip.py` (20 tests, all green) asserts
  every prop from paper Listing 1 survives JSON + YAML round-trips
  against the canonical fixture at
  `tests/fixtures/oscal/assessment-plan.canonical.json`.
- Rust parser (`vl-fairness-gate/src/oscal/parser.rs`) mirrors the
  same fixture via `include_str!` so the three implementations (SaaS,
  SDK, proxy) stay in lock-step.

### Contract specification

Published the normative specification at
`docs/contracts/oscal-assessment-plan-v1.md`: envelope shape, 16
extension props with exhaustive value sets, canonicalisation rules
(symbolic operators, canonical enforcement modes), consumer split,
and forbidden shortcuts.

### Hygiene
- Cleared remaining ruff F401/F541 warnings (3 unused imports + 1 f-string).
- `publiccode.yml` bumped to 0.6.0 (releaseDate 2026-04-30).
- Added cross-file version consistency test (`tests/test_version_consistency.py`).
- `verify_strict_mode.py` migrated into the regular pytest suite as `tests/test_strict_mode.py` (3 tests).
- `.pre-commit-config.yaml` added: ruff + standard hygiene hooks (trailing whitespace, EOL, YAML/TOML/large-file checks).
- CI coverage floor enforced at 70 % in `.github/workflows/ci.yml` (measured baseline: 84 %).
- Coverage badge in README refreshed to 84 % (brightgreen).
- Cross-component smoke runbook documented in `docs/development/cross-component-smoke.md` (internal procedure for verifying the canonical fixture against the Venturalítica SaaS, SDK and Rust proxy).
- Starlight reference/api.mdx (EN+ES) synchronised with the v0.6.0 public API surface (`enforce`, `monitor`, `wrap`, `quickstart`, `PolicyManager`).

### Concept
- Introduced **Compliance by Design** as the umbrella concept for v0.6.0:
  the OSCAL unification (single `assessment-plan` envelope in/out) makes
  the compliance contract a tractable input to the training run, not a
  post-hoc audit. See [docs/concepts/compliance-by-design](https://github.com/Venturalitica/venturalitica-sdk/blob/main/starlight/src/content/docs/concepts/compliance-by-design.mdx)
  in the published docs and the [arXiv preprint](https://arxiv.org/abs/2604.13767).

## [0.5.0-starlight] - 2026-02-18

### Astro Starlight Documentation Migration

Migrated all documentation from MkDocs → Mintlify → **Astro Starlight** (open-source) with bilingual support (EN/ES) and automatic `llms.txt` generation via the `starlight-llms-txt` plugin.

#### New Documentation Platform (`starlight/`)
- **Astro Starlight**: Open-source documentation framework with first-class i18n, search, and static site generation
- **`astro.config.mjs`**: Full configuration with i18n (root EN, `es` locale), 5-group sidebar, `starlight-llms-txt` plugin
- **18 English `.mdx` pages**: Complete content in `src/content/docs/`
- **18 Spanish `.mdx` pages**: Complete Spanish mirror in `src/content/docs/es/` with accent fixes and translated prose
- **`src/content/i18n/es.json`**: Spanish UI string overrides for sidebar groups and labels
- **`src/styles/custom.css`**: Custom theme styling
- **`public/images/`**: Consolidated image assets (logo.svg, favicon.svg, 5 PNGs)
- **Pagefind search**: Indexed 36 pages across 2 languages, 4781 words

#### Syntax Conversions Applied (Mintlify → Starlight)
- Admonitions: `<Note>` → `:::note`, `<Warning>` → `:::caution`, `<Tip>` → `:::tip`, `<Danger>` → `:::danger`
- Tabbed content: `<Tabs><Tab>` → separate labeled code blocks (no imports needed)
- Card groups: `<CardGroup><Card>` → plain markdown link lists
- Frontmatter: `sidebarTitle` → `sidebar: { label: "..." }`
- Internal links: removed `/es/` prefix (Starlight handles i18n routing), added trailing slashes
- Spanish accent fixes applied throughout all prose text

#### `llms.txt` Generation
- **`starlight-llms-txt`** plugin auto-generates during build:
  - `dist/llms.txt` (586B) — index with links to full/small versions
  - `dist/llms-full.txt` (149KB) — complete documentation for LLM consumption
  - `dist/llms-small.txt` (128KB) — abridged version with non-essential content removed

#### Key Benefits
- **Open-source**: No vendor lock-in or subscription costs (Mintlify requires paid plan)
- **Native `llms.txt`**: Auto-generated by `starlight-llms-txt` plugin during build
- **i18n**: Root locale (EN) + `es` locale with automatic language routing
- **Search**: Pagefind-powered full-text search across both languages
- **Zero-error build**: 37 pages built in ~10s with zero warnings

#### Cleanup
- Removed `mintlify/` directory (superseded by `starlight/`)
- Removed `mkdocs.yml` configuration file
- Removed MkDocs dependencies from `pyproject.toml` (`mkdocs`, `mkdocs-material`, `mkdocs-macros-plugin`, `mkdocs-static-i18n`, `pymdown-extensions`, `mkdocs-llmstxt`)
- Updated Documentation URL in `pyproject.toml` to `https://venturalitica.github.io/venturalitica-sdk`
- MkDocs `docs/` source directory preserved for reference

---

## [0.5.0-docs] - 2026-02-18

### Documentation Overhaul

Comprehensive documentation rewrite addressing all gaps identified in the strategic audit.

#### New Documentation (8 pages)
- **docs/metrics.md**: Complete metrics reference (35+ metrics, 7 categories, formulas, thresholds)
- **docs/dashboard.md**: Glass Box Dashboard user guide (4 phases, 7 views, session management)
- **docs/policy-authoring.md**: OSCAL policy authoring guide (assessment-plan format, props reference, two-policy pattern)
- **docs/column-binding.md**: Column binding documentation (synonym table, resolution algorithm, multilingual support)
- **docs/experimental.md**: Experimental features page (CLI login/pull/push, SaaS status, feature matrix)
- **docs/probes.md**: Probes reference (7 probes, EU AI Act article mapping, evidence structure)
- **docs/full-lifecycle.md**: Zero to Annex IV single-page walkthrough (copy-paste ready)
- **docs/multiclass-fairness.md**: Multiclass fairness metrics deep dive (7 metrics, strategies, intersectional analysis)
- **docs/compliance-mapping.md**: ISO 42001 / EU AI Act mapping (article-by-article SDK capability mapping)

#### Fixed Documentation (4 pages)
- **docs/api.md**: Fully rewritten with correct `enforce()` and `monitor()` signatures from source code
- **docs/quickstart.md**: Fixed install command from `pip install git+...` to `pip install venturalitica`
- **docs/index.md**: Rewritten with correct install, new doc links, removed stale references
- **docs/es/quickstart.md**: Fixed install command in Spanish mirror

#### Updated Documentation (4 pages)
- **docs/academy/level1_policy.md**: Expanded with real data_policy.oscal.yaml (3 controls), expected output, prop reference table
- **docs/academy/level2_integrator.md**: Fixed commands, added cross-references to new docs
- **docs/academy/level3_auditor.md**: Fixed duplicate heading, updated code to use `load_sample()`, added references
- **docs/academy/level4_annex_iv.md**: Fixed commands, updated code, replaced stale links with new doc references

#### Spanish Mirror (`docs/es/`) — Full Update
- Rewrote `es/api.md` and `es/index.md` to match new English sources
- Rewrote all 4 academy levels (`es/academy/level1–level4`) with updated code, outputs, and cross-references
- Created 8 new Spanish pages: `es/metrics.md`, `es/dashboard.md`, `es/policy-authoring.md`, `es/column-binding.md`, `es/experimental.md`, `es/probes.md`, `es/full-lifecycle.md`, `es/multiclass-fairness.md`, `es/compliance-mapping.md`
- Updated `es/quickstart.md` "What's next" links to point to all new documentation pages
- Verified `es/academy/index.md` and `es/tutorials/01_writing_policy.md` (no changes needed)

#### Housekeeping
- Deleted 15 empty `gov_*.md` placeholder files from project root
- Updated `mkdocs.yml` navigation to include all new documentation pages
- Removed references to nonexistent pages (training.md, integrations.md, compliance-dashboard.md, compliance-gap.md)
- Unified OSCAL format references to `assessment-plan` as canonical throughout docs
- Moved 8 stale English docs and 7 stale Spanish docs to `docs/.archive/` and `docs/es/.archive/` respectively
- Removed `mkdocs-llmstxt` plugin: incompatible with `mkdocs-static-i18n` (i18n sub-build resets plugin state, producing empty `llms.txt`); build now runs with zero warnings

#### Known Issues / Technical Debt
- **Platform migration tracked:** `mkdocs-llmstxt` 0.5.0 is unmaintained and broken with the i18n plugin. Agent-friendly docs (`llms.txt`, content negotiation, per-page `.md` serving) require migrating to a platform with native support — **Mintlify** (recommended for AI compliance SDK) or **Docusaurus** (open-source, community `docusaurus-plugin-llms` plugin). Migration is a separate workstream.

## [0.5.0] - 2026-02-12

### "Marie Kondo" Release - Code Quality & Release Finalization

This release represents the completion of the v0.5.0 "Marie Kondo" code cleanup initiative, comprising four major phases:

#### Phase A: Linting & Version Fixes ✅
- Fixed version inconsistency: 0.4.2 → 0.5.0 in `src/venturalitica/__init__.py`
- Updated mkdocs version: v0.4.1 → v0.5.0 in `mkdocs.yml`
- Added comprehensive ruff linter configuration to `pyproject.toml`
  - Python 3.11 target
  - Line-length: 120
  - Rule sets: E (errors), F (pyflakes), I (import sorting)
- Fixed 24 linting issues across 8 test files:
  - E712: Explicit == True/False comparisons (4 occurrences)
  - E741: Ambiguous variable naming (1 occurrence)
  - F841: Unused variable assignments (16 occurrences)
  - E402: Import ordering (2 occurrences)
  - I001: Import sorting (auto-applied via ruff)
- Updated .gitignore to exclude build artifacts and test outputs

#### Phase B: Smoke Tests for Core API ✅
Created comprehensive smoke tests (`tests/test_smoke_core_api.py`) validating core vl.monitor() and vl.enforce() functionality:
- **vl.monitor() tests (4)**:
  - Session creation and context manager behavior
  - Yield control and cleanup verification
  - Custom parameter handling
  - Error recovery
- **vl.enforce() tests (10)**:
  - Metrics evaluation against policies
  - Dataframe processing and validation
  - Results caching mechanisms
  - Multiple policy execution
  - Error handling and edge cases
- **Integration test (1)**:
  - Combined monitor() and enforce() workflow
- Fixtures: Realistic sample policies, dataframes, and temporary directories

#### Phase C: Coverage Improvement Tests ✅
Created targeted coverage tests (`tests/test_coverage_improvements.py`) achieving edge-case coverage for 90%+ target:
- **Error handling paths (6 tests)**:
  - Invalid control specifications
  - Strict mode violations
  - Dataframe edge cases (empty, NaN values)
- **Telemetry robustness (3 tests)**:
  - Import failure recovery
  - Exception handling in metric reporting
- **Integration coverage (3 tests)**:
  - MLflow/W&B fallback mechanisms
  - Session lifecycle edge cases
- **API boundary conditions (3 tests)**:
  - Numeric edge cases (NaN, negative values, large ranges)
  - Results caching edge cases
  - Metrics computation boundary conditions

#### Phase D: Scenario Verification for v0.5.0 ✅
Complete verification of all 5 scenarios in `venturalitica-sdk-samples`:
- **loan-credit-scoring**: ✅ Fully production-ready (OSCAL policies, 4 notebooks, Academy L1-L4 coverage)
- **medical-spine-segmentation**: ✅ Fully production-ready (DICOM processing, compliance testing)
- **financial**: ✅ Ready (demonstrates modular before/after approach)
- **vision-fairness**: ✅ Ready (fairness metrics, data governance)
- **test-inference**: ✅ Minimal/testing-focused (intentional minimal scope)
- Verified all scenarios already use v0.5.0-compatible imports (no migration needed)
- Distribution model confirmed: consolidated in `venturalitica-sdk-samples` (not separate repos)
- Created comprehensive verification report: `docs/engineering/SCENARIO_VERIFICATION_v0.5.0.md`

### Summary of Changes

#### Code Quality Improvements
- **Total tests**: 529 passed, 1 skipped, 0 failed
- **New tests added**: 30 (15 smoke tests + 15 coverage tests)
- **Code coverage**: 73% baseline (targeting 90%+ with new tests)
- **Linting status**: 100% clean (ruff-verified)
- **Regressions**: 0

#### Modules & Architecture
- No breaking changes to core API
- All public APIs remain backward compatible
- Deprecated import shim modules removed (see Breaking Changes)

#### Documentation
- Updated RELEASE_NOTES.md with comprehensive v0.5.0 details
- Added SCENARIO_VERIFICATION_v0.5.0.md for release verification
- Updated pyproject.toml with ruff configuration

### Breaking Changes

**Removed Deprecated Shim Modules**

The following deprecated import paths have been removed in v0.5.0:

| Old Import (Removed) | New Import (Use This) |
|---|---|
| `from venturalitica import causal` | `from venturalitica.assurance.causal import ...` |
| `from venturalitica import fairness` | `from venturalitica.assurance.fairness import ...` |
| `from venturalitica import performance` | `from venturalitica.assurance.performance import ...` |
| `from venturalitica import privacy` | `from venturalitica.assurance.privacy import ...` |
| `from venturalitica import quality` | `from venturalitica.assurance.quality import ...` |

**Migration required if you use deprecated imports:**
```python
# Old (no longer works):
from venturalitica import quality

# New (use this):
from venturalitica.assurance.quality import QualityMetrics
```

**No migration needed** if you use the `venturalitica.assurance.*` namespace directly.

### Commits in This Release

- `c231c52` - chore: v0.5.0 release preparation (Phase A: linting & version fixes)
- `084ba37` - test: add smoke tests for core API (vl.monitor & vl.enforce)
- `1319f24` - test: add coverage improvement tests targeting 90%+ (Phase C)
- `d676888` - docs: add scenario verification report for v0.5.0 release (Phase D)

### Dependencies

- Python >= 3.11 (unchanged)
- Build system: Hatchling + UV (unchanged)
- All runtime dependencies unchanged

### Known Issues

None at this time.

### Future Work

- Implement medical-spine-segmentation modular split (base_medical/venturalitica_medical)
- Add OSCAL policies to financial and vision-fairness scenarios
- Scenario CI/CD validation in SDK test suite
- Performance optimization pass (Phase 5)
- Documentation enhancement (Phase 6)

### Verification Checklist

- [x] All unit tests pass (529/529)
- [x] All integration tests pass
- [x] Linting clean (ruff)
- [x] No regressions detected
- [x] All scenarios verified for v0.5.0 compatibility
- [x] RELEASE_NOTES.md complete and accurate
- [x] CHANGELOG.md created and comprehensive

### Download

Available on PyPI:
```bash
pip install venturalitica==0.5.0
```

Or with UV:
```bash
uv add venturalitica==0.5.0
```

---

## Previous Releases

For releases prior to v0.5.0, see the git log or RELEASE_NOTES.md for historical information.
