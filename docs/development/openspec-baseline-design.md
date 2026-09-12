# Design spec — OpenSpec kit and the current requirements baseline

Status: **IMPLEMENTED.** Written and applied 2026-09-11 under the method in [`CLAUDE.md`](../../CLAUDE.md).
Six sections, all required. §5 is written as an invariant and proved with known-answer tests.

---

## §0 Motivation

This repository is the only MET-SPEC component without an `openspec/` directory. A sibling
MET-SPEC component carries nine capabilities and five archived changes; another, twelve and
fifty-four. The
measured consequence is a single motive, `N0.2`: *the method is DECLARED in the model and cannot
be measured to rule, because it has no kit.*

Installing the kit and writing the current part of the baseline closes `N0.2` and unblocks `N2.1`
("no requirements baseline in its own repository"). This component was declared on the market on
2026-08-29 and is subject to the EU Cyber Resilience Act and the Product Liability Directive, so
the design record has to be reconstructible at any commit rather than asserted from memory.

The failure this design exists to prevent is narrower and more specific than "we have no specs".
It is that **a backlog reads exactly like a baseline**. A sibling component measured 74% of its own
corpus describing behaviour that does not yet exist. Without a declared, checked state per item,
that corpus is indistinguishable from a description of the engine. A requirements baseline that
describes what we wish were true is not an input to design; it is a wish list that passes audits.

The second failure, and the one that belongs to this repository specifically, was measured here on
2026-09-08 and reconfirmed on 2026-09-11 against the binary and the suite:

| Measure | Value |
|---|---|
| `test_*` functions in the tree | 844 |
| collected by pytest | 841 |
| passing | 840 |
| never collected (module-level `importorskip`) | 21 |
| collected but containing no assertion | 26 |
| explicitly skipped with `@pytest.mark.skip` | 1 |

The twenty-one are the tests in `tests/test_graph_nodes.py` and `tests/test_imaging_metrics.py`.
Their modules call `pytest.importorskip` on `langchain_core` and `monai`, which live in the
`agentic` and `imaging` extras. CI runs `uv sync --group dev`, which installs neither. Because the
skip happens at module level during collection, those twenty-one tests are not reported as skipped
individually — they never appear in the run at all. The suite prints `840 passed, 3 skipped` and
the twenty-one vanish inside a green.

A claim whose only support is a test that never executes is not current. It is pending, and the
reason has to be written down.

## §1 Dated decisions

| Date | Decision | Origin |
|---|---|---|
| 2026-09-11 | This repository adopts OpenSpec with **both** the kit and a current corpus, not the empty kit. | Founder, `DEC-30`, due this date |
| 2026-09-11 | The kit is `@fission-ai/openspec` pinned to **exactly `1.11.0`**, matching the sibling MET-SPEC component so the two are comparable. A range is forbidden: the guardian compares the running binary against the pin, and a range makes "the pin" not a value. | the sibling component's operator, measured in its tree |
| 2026-09-11 | The unit of the baseline is the **capability**. | `DEC-30` |
| 2026-09-11 | State hangs from the **consequence**, not from the requirement. A requirement may be one third built and two thirds not; calling it wholly current or wholly pending lies in both directions. | Correction measured on a third component over its 12 requirements and 74 verifiable consequences |
| 2026-09-11 | Three states, not two: `CURRENT`, `UNPROVEN`, `PENDING`. | the sibling component's traceability guardian; `UNPROVEN` is the state that justifies three |
| 2026-09-11 | **No single entry point** for the guardians. The lesson from the double-gate failure is not "add another script"; it is that two guardians answering different questions do not substitute for each other, and a green must be read with the name of what it covers attached. | the sibling component's operator, correcting this design's first draft |
| 2026-09-11 | The backlog proportion is **measured and not gated**. A guardian that also set a threshold would turn a measurement into a policy nobody decided. | the sibling component's traceability guardian |
| 2026-09-11 | Scope of this pass is the **spine of the journey**: six capabilities following steps 2 to 7 of [`docs/intended-use.md`](../intended-use.md). | This session, decided by the requester |
| 2026-09-11 | Support that cannot back a `CURRENT` is written in place as `PENDING` **with its motive**, never omitted. | This session, decided by the requester |
| 2026-09-11 | The non-evidence is **two families and is never summed**: 21 environment gaps (they exist and could run; installing the extras fixes them) and 26 subject gaps (they always run and cannot fail; nothing fixes them but writing the assertion). Summing them means believing one day that installing extras closed 61. | the sibling component's operator |
| 2026-09-12 | The two regimes this product is placed on the market under are written into `ml-bom`, and **differently on purpose**: the Cyber Resilience Act as a demonstrated requirement, because its component-documentation obligation asks for a machine-readable inventory of top-level dependencies and that is what the capability produces; the Product Liability Directive as a `PENDING` requirement over an already-measured gap, because no capability answers it today. Before this, both norms appeared exactly once in the whole repository, in §0 of this document, written here rather than by the product. | This session, decided by the requester |
| 2026-09-12 | The criterion that counts these citations finds the **name** of a norm in the corpus, not that a requirement covers it, so it is satisfiable by writing an acronym anywhere. That is why the two are written differently and why the difference is recorded here: a green on that criterion means *somebody wrote two names*, never *the corpus covers two norms*. Same ceiling as the notation validator — it finds the form, not the subject. | Measured limit, declared by the counter's operator |
| 2026-09-11 | The corpus is written in **English throughout**. This repository is public with an external community, its README and docs are English, and `--strict` requires `SHALL`/`MUST` in English regardless — writing the whole requirement in English removes the bilingual seam instead of routing around it. | This session, decided by the requester |

### Measured against the binary, 2026-09-11

Every claim below was exercised against `@fission-ai/openspec@1.11.0` in a scratch tree, not
recalled. These are the known answers §5 rests on.

| Case | Exit | What the instrument said |
|---|---|---|
| `- **Status:**` inside a `#### Scenario:` body | 0 | `1 passed, 0 failed` — per-consequence state survives `--strict` |
| `### Scenario:` (three hashes) | 1 | `ERROR requirements.0.scenarios: Requirement must have at least one scenario` |
| `DEBERÁ` instead of `SHALL` | 1 | `WARNING requirements[0]: ... should contain SHALL or MUST` |
| Requirement with no scenario at all | 1 | `ERROR requirements.0.scenarios: Requirement must have at least one scenario` |
| **Empty corpus** | **0** | `items=0, passed=0, failed=0` |

The last row is the whole reason the kit gate is not a bare `openspec validate --all --strict`.
By exit code, an empty corpus is indistinguishable from a healthy one.

### Independently reproduced, 2026-09-11

The management system's own corpus counter, which reads this repository from outside it, was run
against the finished baseline and reproduced the census exactly: 82 current, 3 unproven, 5
pending. It also measured the thing this design was built around, once it could tell a declared
state from an inherited one:

| Corpus | Consequences inheriting their state from the requirement |
|---|---|
| a sibling MET-SPEC component | 70 of 70 |
| this repository | 0 of 90 |

That difference is the point of §1's decision that state hangs from the consequence. It is now a
count rather than a warning.

## §2 Design

### The kit is an instrument, not a component

`.github/openspec/` holds `package.json` and `package-lock.json`. It is installed with
`npm ci --prefix .github/openspec` and invoked by path at
`.github/openspec/node_modules/.bin/openspec`, never from `PATH`: a global binary does not appear
in the commit and its version would not be reconstructible. It lives under `.github/` so the
Python packaging never sees it and it does not enter the SDK's own bill of materials. The corpus
under `openspec/` is excluded from the source distribution for the same reason `docs/` and
`tests/` are: design records govern the product without being part of what third parties install.

Telemetry is disabled in the job `env` **and** again inside each script, because the scripts are
also run locally by hand where no job `env` covers them. The kit's own opt-out is not versionable
(`openspec config` is explicitly global), so these two variables are the only thing this
repository can impose. Declared, not papered over.

### The corpus

`openspec/specs/<capability>/spec.md`, one directory per capability. Six capabilities in this
pass, following steps 2 to 7 of the intended-use journey:

| Capability | Journey step | Principal evidence |
|---|---|---|
| `policy-authoring` | 2, 3 | `tests/test_policy.py`, `tests/test_loader.py`, `tests/test_cli_sync.py` |
| `enforcement` | 5 | `tests/test_enforcement_semantics.py`, `tests/test_strict_mode.py` |
| `retained-vault` | 6 | `tests/test_vault_retained.py` |
| `oscal-results` | 5, 6 | `tests/test_oscal_output.py` |
| `ml-bom` | 6, 7 — inventory of the governed artefact | `tests/test_bom_artefactos.py`, `tests/test_bom_subjects.py`, `tests/test_bom_determinism.py` |
| `annex-iv` | 7 | `tests/test_inference.py`, `tests/test_cli_transfer.py` |

A new capability needs a `## Purpose` of 50 characters or more. In a delta against an existing
capability the `Purpose` is ignored.

### The grammar of a consequence

State is declared on the `#### Scenario:`, which is the consequence, and never on the
`### Requirement:`. Measured above: a bullet in the scenario body survives `--all --strict`.

```
#### Scenario: One control is retained of two evaluated
- **Status:** CURRENT
- **Proof:** `tests/test_vault_retained.py::test_la_boveda_guarda_lo_RETENIDO_no_todo_lo_evaluado`
- **WHEN** the session evaluates two controls and only one is marked with `retain`
- **THEN** the vault holds exactly one result
```

The three states and what each obliges:

- **`CURRENT`** — describes what the SDK does today. Requires `**Proof:**` as `path::test_name`.
- **`UNPROVEN`** — describes what the SDK does today, and nothing pins it. This is the dangerous
  state and the reason there are three rather than two. With only two states, real behaviour that
  no test holds would be declared current, and nobody would know it can disappear in silence.
- **`PENDING`** — describes what the SDK should do. It is backlog and is counted as backlog.
  Requires `**Reason:**`, and where the motive is absent evidence it must name which of the two
  families it belongs to.

### Four guardians, each printing the name of what it covers

Three of them are sibling steps in the `openspec` job; the currency one runs in the `test` job. In both
jobs the order is written with the reason beside it. The falsifiers run **before** the guardians:
if a guardian cannot turn red, you find that out before believing its green. Traceability runs
**after** form, because a malformed corpus makes noise in the state census and the reason read
first should be the underlying one.

**Why the currency guardian lives in the `test` job** (decided while implementing, 2026-09-11):
whether a test ran is a property of the RUN, not of the source. Inferring it by reading
`importorskip` calls would re-derive from the same text what the run already knows, and would miss
every skip decided at runtime. So it consumes the JUnit report pytest has just written, in the job
that writes it. That job is already in `ci-gate`'s `needs`, so nothing is weakened by the split.

None of them prints a bare `VERDE`. Each prints its green with the subject attached, so a green is
never read as more than it covers.

**`openspec-gate.sh` — the design records are well-formed.** It does not read the third party's
exit code. It reads what the instrument says it measured and contrasts that with the tree: the
output must be parseable JSON, `summary.totals.items` must be at least one, the spec ids the
instrument reports must match the `spec.md` directories in the tree name by name, and
`summary.totals.failed` must be zero. Census before verdict.

*What it does not cover:* `openspec validate` is structural. A `#### Scenario:` whose entire body is
the letter `z` passes `--all --strict`. It checks that the document is well-formed, never that the
requirement says anything.

**`trazabilidad.sh` — every consequence declares its state and its test resolves.** Both halves of
the citation are checked: the path must exist and the test name must appear inside it. A path alone
is satisfied by any file; a name alone anchors to nothing. It also measures the backlog proportion
and prints it without gating.

*What it does not cover:* that the named test proves the requirement. It checks the test exists.

**`vigencia.sh` — a CURRENT is backed by a test that ran and can fail.** This guardian is not in the
sibling component's precedent and exists because that precedent's operator named the gap: *a test that
exists and cannot fail passes the guardian.* With 26 assertion-free functions in this tree, that
would happen on the first day. It answers two questions no other guardian asks, both against the
JUnit XML of the same CI run rather than by inspection:

1. **Did it run?** The cited test must appear in the report as an executed, non-skipped case. A
   module that is never collected cannot back anything. This closes the environment family.
2. **Can it fail?** The cited test function must contain at least one assertion, parsed from the
   syntax tree. This closes the subject family.

*What it does not cover:* that the assertion is about the right subject.

**`aceptacion.sh` — every declared acceptance was closed by someone other than the author.** Added
after the method fixed the convention (2026-09-11). The semantic half cannot be mechanised, but
whether *somebody other than the implementer closed it* can be. The acceptance is an event the
implementer cannot author alone, and the field in the corpus is only a pointer to that event —
a field alone would land in the same commit as the claim it accepts, which is self-certification
that reads as closed. Four checks: the pointer resolves, the event is closed, the closer is not the
author of the commit that introduced the claim, and the closure postdates that commit. Only the
third can go green by accident, so it carries a mandatory falsifier and its contrast. Three
destinations, never two: accepted, unaccepted, not declared.

*What it does not cover:* whether the check the accepter made was any good. It gives the semantic
half a floor, never a ceiling. It also does **not** require an acceptance to exist: that threshold
belongs to the management system, not to this repository.

### Wiring, which is what decides whether any of this is real

A new `openspec` job is added to the `needs` of `ci-gate`. This is load-bearing and the repository
already carries the warning in `ci.yml`: `ci-gate` is the single required check on `main`, and a job
outside its `needs` is decorative.

The wiring is itself guarded, by a plain pytest test rather than by a step inside the job it
guards. A check that lives inside the job it protects cannot notice its own absence. Running it in
the `test` job — already required — means that unwiring the guardian while leaving it present turns
the suite red.

*What that does not cover:* deleting the `openspec` job and the test together in one change. No
automated guard survives its own deletion; that one is closed by review.

## §3 Phases

1. **The machinery, proved on one capability.** Pin the kit, write `openspec/config.yaml`, write
   `retained-vault` end to end, write the three guardians with their falsifiers, and wire the job
   into `ci-gate`. The gate is live from the first commit rather than after the corpus lands.
2. **The remaining five capabilities**, written against the suite, each consequence carrying its
   own state and, where pending, its motive and its family.
3. **The census returned upstream** — what was built, what was left out and why, and the
   corrections owed to the requesters.

Phase 1 first and alone is deliberate. Writing sixty requirements against machinery nobody has
exercised is the expensive order.

## §4 Boundary

What this change does **not** do, each with its motive, because the motive is worth more than the
corpus.

**Seven capability areas are out of scope this pass**: the metrics library under `assurance/`, the
MLflow/WandB/ClearML integrations, the CLI surface, the provenance probes, the Streamlit dashboard,
the agentic Annex IV writer, and the imaging metrics. The spine is where the tests already speak in
the voice of a consequence and where the intended-use anchor has something to disagree with. The
tail has materially weaker evidence, and weak evidence is exactly where backlog dressed as baseline
gets in. The agentic and imaging behaviours still appear, as `PENDING` consequences inside
`annex-iv`, because that is where they belong.

**The 21, the 26 and the 1 are not touched as tests.** They are the measured data behind a founder
decision dated today, and repairing them now moves the number that decision rests on. They are
cited as motives, never repaired.

**The normative OSCAL contract is a dangling reference and is not fixed here.** `README.md:9` cites
`docs/contracts/oscal-assessment-plan-v1.md` as *the normative OSCAL contract*, in the same line as
the arXiv preprint, and that path does not resolve. `CLAUDE.md` already records this as a defect
rather than a typo. It belongs to the methodology session, which is carrying it.

It has a direct consequence for this design that has to be stated rather than worked around: step 2
of the intended-use journey says the SDK has failed *if the emitted plan is not valid against the
normative OSCAL contract*. Against a contract that does not exist, that consequence **cannot be
`CURRENT`**. In `policy-authoring` it is written as `PENDING` with the missing contract as its
motive, and the consequences that are `CURRENT` there are the ones the tests actually prove: the
round trip and the structure.

**No guardian closes the semantic half.** That a test proves its requirement is not mechanisable
and is not pretended to be. It is closed by whoever asked for the change, against a check of their
own — the rule this repository's `CLAUDE.md` already carries.

**And that half is, today, entirely unclosed. All 82 `CURRENT` consequences are self-certified.**
Every one of them was written by whoever implemented this change, reading the tests, and accepted
by nobody else. The three guardians establish that each citation resolves, that its test ran, and
that its test can fail. None of them establishes, and nothing else in this repository records,
that anyone other than the author agreed the test is about the right subject.

This is stated rather than left implicit because the corpus is otherwise easy to misread. A
baseline that passes three guardians and reports six per cent backlog looks accepted. It is not:
it is measured. Those are different claims, and only the second one is currently true.

The obvious remedy is a trap and is named here so it is not adopted by accident: **a field in the
spec file recording who accepted it certifies nothing**, because whoever writes the spec is
normally whoever implements, and the acceptance would land in the same commit as the claim it
accepts. Self-certification with an extra line is worse than no line, because it reads as closed.
An acceptance record has to be an *event* the implementer cannot author alone, and any field in
the corpus can only ever be a pointer to one. Designing that convention belongs to the method
rather than to this repository, and the question has been put to it.

## §5 Acceptance criteria

Written as invariants over a frozen corpus and proved by known-answer tests. None is proved by
walking a UI.

**INV-1 — the kit gate reads the measurement, not the exit code.** Given the corpus at this commit
and the pinned binary, `openspec-gate.sh` exits 0 if and only if all four hold: the output parses
as JSON; `summary.totals.items >= 1`; the set of reported spec ids equals the set of directory
names under `openspec/specs/`; and `summary.totals.failed == 0`.

**INV-2 — the kit gate turns red for the named reason.** For each seeded mutation the gate exits
non-zero **and its printed reason matches the reason named for that case**, not merely any reason.
This is the specific discipline that a red from the wrong assertion reads exactly like a good one:
fix what you believe you are provoking and move nothing else.

| Seeded mutation | Required reason |
|---|---|
| `openspec/specs/` emptied | empty corpus is not a green |
| a `spec.md` the instrument does not report | tree and report disagree |
| a reported id with no `spec.md` in the tree | tree and report disagree |
| `#### Scenario:` demoted to three hashes | the instrument reports `failed >= 1` |
| `SHALL` replaced by `DEBERÁ` | the instrument reports `failed >= 1` |
| the pinned version changed to a range | running binary does not match the pin |
| the kit absent | the falsifier **fails** rather than skipping the cases that need the real binary |

**INV-3 — every consequence declares its state, and a `CURRENT` names its test.** Every
`#### Scenario:` in `openspec/specs/` carries exactly one `**Status:**` drawn from
`{CURRENT, UNPROVEN, PENDING}`. Every `CURRENT` carries `**Proof:**` as `path::name` where the path
exists and the name appears within it. Every `PENDING` carries `**Reason:**`. Any of these in
default is red, and each failure names the capability and the scenario.

**INV-4 — a `CURRENT` is backed by a test that ran and can fail.** For every `CURRENT` consequence,
the cited test appears in the JUnit XML of the same run as an executed, non-skipped case **reported
under the module it was cited from**, and the cited function contains at least one assertion. The
module qualification is load-bearing: matching on the bare function name would let one file's
`test_x` stand in for another file's `test_x` that never ran, which is a false green on the exact
question this invariant asks. Known answers, all of which must turn red:

- a `CURRENT` citing any test in `tests/test_graph_nodes.py` — never collected, environment family;
- a `CURRENT` citing any test in `tests/test_imaging_metrics.py` — never collected, environment
  family;
- a `CURRENT` citing `tests/test_badges.py::test_generate_multiple_badges` — explicitly skipped;
- a `CURRENT` citing any of the 26 assertion-free functions — runs, cannot fail, subject family;
- a `CURRENT` whose cited function ran only as a homonym in a different module.

**INV-5 — the backlog proportion is measured and never gates.** A corpus whose every consequence is
`PENDING` exits 0 while printing the proportion. The exit code does not depend on the ratio.

**INV-6 — the guardian is in the chain of the required check.** `ci-gate.needs` contains `openspec`.
Proved by a pytest test running in the already-required `test` job, so that unwiring the guardian
while leaving it in place turns the suite red.

**INV-7 — the two families are reported separately and never summed.** The census prints the
environment gap and the subject gap as distinct counts. A single total is a defect, because it
would let installing the extras look like it closed both.

**INV-8 — every declared acceptance was closed by someone other than the claim's author.** For
each `CURRENT` consequence carrying a pointer, the referenced event resolves, is closed, was closed
by someone other than the author of the commit that introduced the claim, and was closed after that
commit. Acceptance is never required to exist; only a declared one is checked. Known answers, in
both directions:

- closer equals the claim's author — red, and this is the only one of the four that would
  otherwise pass by accident;
- a different closer — green, because a detector that fires on every pointer detects nothing;
- pointer to an open event, unresolvable pointer, closure predating the claim — each red for its
  own named reason;
- field absent counts as *not declared*, field present without a pointer counts as *unaccepted*,
  and the two are never merged.
