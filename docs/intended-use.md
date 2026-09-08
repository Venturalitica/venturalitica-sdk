# Intended use — the journey the SDK exists to serve

**Status: PROVISIONAL. This is a candidate A1 anchor, not a verified one.**

Read the status line literally. What follows is a statement of *intent* — what a user is
trying to accomplish and what this SDK must do for them. It is **not** a description of what
the code currently does, and where the two disagree, that disagreement is the point. A document
that cannot disagree with the implementation is not an input; it is a transcription.

## Why this file exists

This journey was recovered from `tests/e2e/test_dashboard_missions.py`, retired in the same
change that created this file. That test claimed to walk the seven steps below through the
dashboard UI. It could not: `playwright` was never a declared dependency, it was excluded from
collection by `--ignore=tests/e2e`, and it reached into two absolute paths in a sibling
repository that resolve on one developer's machine and nowhere else.

The reason it was retired rather than repaired is worse than "it did not run", and is recorded
here because it is the kind of defect that survives a green build:

> Step 2 never touched the UI — it called `_create_data_policy_fallback()`, which wrote the
> policy YAML from a string literal. Step 3 did the same whenever the UI save failed. Step 4
> then asserted that the file contained `class_imbalance` and two `disparate_impact` entries —
> the exact contents the fallback had just written. **The test asserted the value of its own
> string literal.** It could not fail for the reason it claimed to test.

The seven steps were nonetheless the only artefact in this repository that expressed *what the
SDK is for* rather than *what it does*. That is what is preserved here. The assertions are not
preserved, because they were never evidence.

## The journey

Each step states the user's goal, what the SDK must produce, and — the part that lets this
document disagree with the code — **how you would know it had failed**.

### 1. Declare what the system is

**Goal.** Identify the AI system under assessment: commercial name, version, provider.

**The SDK must produce** a durable system description that later artefacts cite, so that an
assessment is attributable to a specific version of a specific product.

**It has failed if** the technical file it eventually emits does not name the product and
version, or names a different one than was declared. An assessment that does not identify its
subject identifies nothing.

### 2. State the data policy before the model exists

**Goal.** Express what must be true of the *data* — class balance, disparate impact across
protected attributes — as machine-readable controls, before any model is trained.

**The SDK must produce** an OSCAL assessment plan holding those controls, each carrying its
metric key, operator, threshold and severity.

**It has failed if** the emitted plan is not valid against the normative OSCAL contract, or if a
control's threshold or operator does not survive the round trip. Ordering matters here and is
deliberate: data controls precede model controls because a fairness finding in the data is a
finding about the data, and discovering it after training misattributes it to the model.

### 3. State the model policy

**Goal.** Express what must be true of the *model* — accuracy floors, demographic parity —
against the same control vocabulary.

**The SDK must produce** a second assessment plan, structurally identical to the first, so that
one evaluator handles both.

**It has failed if** the two plans require different handling, or if a metric available for data
is silently unavailable for models.

### 4. Check the plans say what was meant

**Goal.** Confirm the emitted policy is the policy that was intended, before anything is run
against it.

**The SDK must produce** an artefact a human can read and a machine can validate.

**It has failed if** validation passes on a plan whose controls were dropped, reordered, or
defaulted. **Not measured:** whether an empty control set is currently rejected or silently
accepted. The retired test papered over exactly this case by rewriting the file when it found it
empty — which is how the gap survived.

### 5. Run the policy against real data

**Goal.** Enforce both policies against a dataset and get a verdict per control.

**The SDK must produce** a measurement per control — the observed value, the threshold, the
comparison, and the pass/fail — with enough provenance to say which data produced it.

**It has failed if** a control passes without a value, if the partition digest does not change
when the data changes, or if a failure is reported as a pass.

### 6. See the evidence

**Goal.** Read the results — as a run directory on disk with the measurements in it.

**The SDK must produce** durable evidence that outlives the process that made it.

**It has failed if** a run directory exists with no measurements in it. **This is the step most
in need of a real anchor:** the `.venturalitica/` tree on the development machine contains
twelve run directories whose `artifacts/` folders are all empty. Whether that is correct
behaviour for those runs or a silent write failure is **not measured**, and "not measured" is
not "fine".

### 7. Emit the technical documentation

**Goal.** Derive the Annex IV technical file from the evidence gathered, not from prose written
afterwards.

**The SDK must produce** a document whose claims trace back to measurements in step 5.

**It has failed if** a claim appears in the technical file with no measurement behind it. That
is the failure this whole SDK exists to prevent, and it is the one it would be most embarrassing
to commit.

## What this document is not

It is not acceptance criteria. Per the method in `CLAUDE.md`, §5 of a spec is written as an
invariant and proved with a frozen corpus or a known-answer test — never by walking a UI. This
file is an input to writing those invariants, not a substitute for them.

It has also not been confirmed with a user. It was recovered from a test written by the same
person who wrote the implementation, which makes it a statement of intent from one side only.
Until a real use is observed and recorded, the A1 anchor for this component remains **weak**,
and any requirements baseline derived mostly from the test suite will describe what the SDK does
today — defects included — with little to disagree with it.
