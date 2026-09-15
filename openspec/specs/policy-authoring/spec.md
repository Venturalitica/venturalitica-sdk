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

### Requirement: What this SDK emits and accepts is fixed by a published contract

The envelopes this SDK emits and accepts SHALL be declared in a normative contract that other
components can be held to, and the SDK SHALL conform to it. A contract nobody can read is not a
contract, and one nobody checks is a description of what somebody believed.

#### Scenario: The canonical policy envelope is the one the contract names
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_contract_v1.py::test_las_raices_aceptadas_son_las_que_el_contrato_declara`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a policy arrives under each root the contract declares accepted
- **THEN** it loads, and the canonical root is among them

#### Scenario: The retired envelope is refused rather than read empty
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_contract_v1.py::test_el_sobre_retirado_se_rechaza`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a policy arrives under the envelope retired in 0.6.4
- **THEN** loading raises, because loading it empty would skip every control and report a clean run

#### Scenario: The contract cannot outlive the code it describes
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_contract_v1.py::test_la_version_oscal_del_contrato_es_la_que_el_emisor_declara`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the emitter's declared OSCAL version and the contract's disagree
- **THEN** the suite fails and names the contract, because the contract this one replaces was
  typed, versioned and normative, and what it lacked was a way to expire

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
