# Normative OSCAL contract, v1

This is the contract other components are held to when they exchange OSCAL documents with this
SDK. It describes **what this SDK emits and what it accepts today**, as invariants that can be
checked, not as a description of what anyone believes it does.

It replaces a contract that was deleted in the 0.6.4 hotfix. That one is not restored, and the
reason matters more than the fact: measured on 2026-09-14, its two leading invariants were
**inverted** with respect to the code. They required the envelope that this SDK now refuses, and
denied the one that is now canonical. The canonical root migrated in May 2026 and the contract
did not move with it. It was typed, versioned and normative; what it lacked was a way to expire.

Hence the section at the end, which is the part of this document most worth keeping.

## The machine-checked facts

Everything in this block is compared against the code by
[`tests/test_oscal_contract_v1.py`](../../tests/test_oscal_contract_v1.py). If the code moves and
this block does not, the suite goes red and names this file. That is the whole expiry mechanism.

```yaml
oscal_version: "1.2.2"
policy_root_canonical: component-definition
policy_roots_accepted: [catalog, profile, component-definition, system-security-plan]
policy_roots_refused: [assessment-plan]
evidence_root: assessment-results
remediation_root: plan-of-action-and-milestones
```

## Direction A — policy into the SDK

**A1. The canonical policy envelope is `component-definition`.** It has been since the May 2026
migration. A document arriving under `catalog`, `profile` or `system-security-plan` is also read,
because those are canonical NIST roots that can legitimately carry control implementations; a bare
list is still read for compatibility with policies written before the migration.

**A2. `assessment-plan` is refused.** It is not a policy envelope in this SDK and has not been one
since 0.6.4. A policy under that root raises rather than loading empty, because loading empty
would skip every control and report a clean run. *Proof:*
`tests/test_oscal_contract_v1.py::test_el_sobre_retirado_se_rechaza`.

**A3. Any other root is refused, and the error names what is accepted.** *Proof:*
`tests/test_loader.py::test_loader_invalid_format`.

**A4. Controls are read from `components[].control-implementations[].implemented-requirements[]`,**
and from the singular `control-implementation` of a system security plan. Nesting inside a catalog
is resolved recursively, so a nested control is never silently dropped. *Proof:*
`tests/test_loader.py::test_loader_catalog_recursive`.

**A5. A requirement declares its measurement as props.** `metric_key` (or `metric`, accepted as an
alias), `operator`, `threshold` and `severity`. A requirement missing any of them is not a
requirement this SDK can evaluate, and is reported rather than defaulted. *Proof:*
`tests/test_policy.py::test_validate_control_missing_metric_key`.

**A6. Input bindings use `input.<slot>`,** with a dot. The separator is load-bearing: the
validating consumers on the other side of this contract reject the colon form.

**A7. Profile props travel through to the evidence.** The names are fixed:

    lifecycle semantics ...... lifecycle_phase · enforcement_mode · evaluation_method
                               evaluation_window · target_type
    traceability chain ....... risk_id · treatment_id · policy_id · objective_id
    risk acceptance .......... risk_acceptance_criteria · threshold_justification
    deliberation ............. stakeholder_consultation_ref

`lifecycle_phase` MAY appear more than once on one requirement, and then means that the control
applies in each phase named. Every other name appears at most once. Anything outside this set and
outside A5 is passed to the metric function as a parameter.

## Direction B — evidence out of the SDK

**B1. Evidence is emitted under `assessment-results`, declaring OSCAL `1.2.2`.** *Proof:*
`tests/test_oscal_output.py::test_oscal_version_in_metadata`.

**B2. One observation and one finding per retained result**, and the document lists the controls it
reviewed. *Proof:* `tests/test_oscal_output.py::test_one_observation_per_result`.

**B3. A risk is emitted for a failure and for nothing else.** *Proof:*
`tests/test_oscal_output.py::test_risk_only_for_failures`.

**B4. A failure also produces `plan-of-action-and-milestones`, one item per failure, left open,**
carrying the same risks as the assessment. *Proof:*
`tests/test_oscal_output.py::test_poam_risks_match_ar_risks`.

**B5. Keys are emitted in the canonical spelling and empty fields are omitted.** A key spelled our
way is a private dialect, and a serialised empty value is read by a consumer as a declared one.
*Proof:* `tests/test_oscal_output.py::test_kebab_case_keys`.

**B6. Every observation carries the digest of the partition it was computed over, including when
the control passed.** Without it two measurements of one control over different data are
indistinguishable, and the misleading one is typically the one that passes. *Proof:*
`tests/test_vault_retained.py::test_el_digest_llega_al_ar_incluso_si_el_control_pasa`.

## Known divergence, declared rather than hidden

**The dashboard's policy form still writes the envelope this contract refuses.** Measured
2026-09-14: `save_policy_file` in `src/venturalitica/dashboard/views/policy_editor.py` emits a
document rooted at `assessment-plan`, which A2 says this SDK will not read. There is a guard, and
it is partial: it refuses to overwrite an existing canonical policy, and says so clearly. It does
not stop a *new* policy being written in the retired shape, and the next enforcement run against
that file would skip every control.

No test pins any of this. It is recorded here because a contract that described only the parts
that agree would be a description of what we wish were true, which is the defect that produced the
document this one replaces.

## How you will know this contract has expired

A contract that cannot expire outlives its subject silently, which is what happened to the last
one. This one is bound to the code in three places, and the binding is mechanical:

1. **The block at the top is compared against the code on every run.** The accepted roots are read
   from the loader, the OSCAL version from the emitter's constant. If either moves, the suite fails
   and names this file. The failure message says *re-measure this contract*, not *fix the test*.
2. **Every invariant above that can be demonstrated names the test that demonstrates it.** If a
   named test disappears or is renamed, the corpus guardian in CI reports it, because the same
   citations appear in `openspec/specs/`.
3. **What neither of those covers** is an invariant that stays true in form while ceasing to
   describe what anyone actually exchanges. That is the failure of the previous contract and no
   mechanism here prevents it. It is closed by re-measuring against the other side of the contract
   when either side changes, and by the divergence section above being kept honest.

The version in this file's name is not decoration. When the canonical root migrates again, this is
`v1` and the successor is `v2`; this file is then marked superseded rather than edited, so that a
document produced under it can still be read against the rules it was produced under.
