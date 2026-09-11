# policy-authoring

## Purpose

Policy authoring turns what must be true of the data and of the model into machine-readable OSCAL
controls, each carrying its metric key, operator, threshold and severity, before anything is
measured. Data controls precede model controls deliberately: a fairness finding in the data is a
finding about the data, and discovering it after training misattributes it to the model.

## Requirements

### Requirement: A policy round-trips without losing a control

The SDK SHALL write and read back a policy without altering its controls. A threshold or an
operator that does not survive the round trip silently changes what is being enforced, and the
measurement that follows would be a correct answer to the wrong question.

#### Scenario: A saved policy reads back as it was written
- **Status:** CURRENT
- **Proof:** `tests/test_policy.py::test_save_roundtrip`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a policy is saved and loaded again
- **THEN** the loaded policy carries the same controls as the one saved

#### Scenario: A policy expressed as a legacy bare list still loads
- **Status:** CURRENT
- **Proof:** `tests/test_policy.py::test_load_legacy_list_format`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a policy file holds the older bare-list shape rather than a mapping
- **THEN** it loads rather than failing, so an existing policy does not stop working on upgrade

#### Scenario: A policy read from an OSCAL catalog resolves nested controls
- **Status:** CURRENT
- **Proof:** `tests/test_loader.py::test_loader_catalog_recursive`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** controls are nested inside an OSCAL catalog rather than listed flat
- **THEN** every nested control is found, so nesting does not silently drop controls

### Requirement: An incomplete control is rejected rather than defaulted

The SDK SHALL reject a control missing its identifier, metric key, operator or threshold, and
SHALL NOT substitute a default for any of them. A defaulted threshold is a policy nobody wrote
that nonetheless produces verdicts.

#### Scenario: A control with no metric key is rejected
- **Status:** CURRENT
- **Proof:** `tests/test_policy.py::test_validate_control_missing_metric_key`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a control omits its metric key
- **THEN** validation reports it rather than accepting the control

#### Scenario: A control with no threshold is rejected
- **Status:** CURRENT
- **Proof:** `tests/test_policy.py::test_validate_control_missing_threshold`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a control omits its threshold
- **THEN** validation reports it rather than assuming one

#### Scenario: A control with no operator is rejected
- **Status:** CURRENT
- **Proof:** `tests/test_policy.py::test_validate_control_missing_operator`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a control omits its comparison operator
- **THEN** validation reports it rather than assuming a direction

#### Scenario: Several bad controls are all reported, not just the first
- **Status:** CURRENT
- **Proof:** `tests/test_policy.py::test_validate_multiple_controls_mixed`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a policy mixes valid and invalid controls
- **THEN** every invalid one is reported, so a second fix is not needed to discover a third fault

#### Scenario: A policy with no title is rejected on save
- **Status:** CURRENT
- **Proof:** `tests/test_policy.py::test_save_missing_title_raises`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a policy is saved with no title
- **THEN** the save raises rather than writing an unattributable policy

#### Scenario: An empty policy file does not read as an empty policy
- **Status:** CURRENT
- **Proof:** `tests/test_policy.py::test_load_empty_yaml`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the policy file is empty or holds only whitespace
- **THEN** loading does not yield a policy with zero controls that would then pass everything

### Requirement: An emitted policy is valid against the normative OSCAL contract

The assessment plan the SDK emits SHALL be valid against the normative OSCAL contract this project
publishes, so that a document accepted here is accepted by every other component reading it.

#### Scenario: The emitted plan validates against the published contract
- **Status:** PENDING
- **Reason:** the contract does not currently resolve. `README.md` cites
  `docs/contracts/oscal-assessment-plan-v1.md` as *the normative OSCAL contract*, and that path
  does not exist in the tree. It was present once, at 135 lines, and was removed by the 0.6.4
  hotfix that dropped the legacy assessment plan. A normative reference that does not resolve is a
  defect rather than a typo, and no consequence can be CURRENT against a contract that is not
  there. The consequences above are written against what the tests actually prove, which is the
  round trip and the structure. Restoring or superseding the contract is tracked outside this
  repository.
- **WHEN** an assessment plan is emitted
- **THEN** it validates against the published normative contract

### Requirement: A control carries the risk it was derived from

A control SHALL carry the identifier of the risk that motivated it, so that a verdict can be
traced back to the concern it answers rather than standing as a free-floating threshold.

#### Scenario: A control derived from a risk names that risk
- **Status:** UNPROVEN
- **Reason:** nothing that can fail pins it. Four tests in `tests/test_cli_sync.py` cover risk
  binding (`test_risk_bound_in_model_policy`, `test_risk_bound_in_data_policy`,
  `test_risk_unbound`, `test_multiple_risks_mixed_binding`). All four run on every CI job and
  none of them contains a single assertion, so they cannot fail and the behaviour they describe
  could regress without any red announcing it. This is the SUBJECT family: installing an extra
  will never fix it, only writing the assertion will. The tests are deliberately left untouched
  for now, because they are measured data behind a decision dated 2026-09-11 and repairing them
  moves the number that decision rests on.
- **WHEN** a policy is pulled and a control derives from a declared risk
- **THEN** the control names that risk, and an underived control is marked as unbound
