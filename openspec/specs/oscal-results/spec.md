# oscal-results

## Purpose

Assessment results turn the verdicts produced by enforcement into canonical NIST OSCAL documents:
an observation and a finding for every control reviewed, a risk for every failure, and a plan of
action carrying those risks. This is the document other components ingest, so its shape is a
contract rather than a rendering choice.

## Requirements

### Requirement: Every reviewed control yields exactly one observation and one finding

The emitted assessment SHALL carry one observation and one finding per result, and SHALL list the
controls it reviewed. A missing observation makes a verdict unattributable; a duplicated one
counts the same measurement twice.

#### Scenario: One observation per result
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_output.py::test_one_observation_per_result`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a mixed set of passing and failing results is emitted
- **THEN** the document holds exactly one observation per result

#### Scenario: One finding per result
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_output.py::test_one_finding_per_result`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the same set is emitted
- **THEN** the document holds exactly one finding per result

#### Scenario: The reviewed controls are listed
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_output.py::test_reviewed_controls_listed`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** results are emitted
- **THEN** the document names the controls it reviewed, so its scope is readable without
  inferring it from the findings

#### Scenario: An observation is linked to its finding
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_output.py::test_observation_links_to_finding`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** results are emitted
- **THEN** each observation resolves to the finding it supports

### Requirement: A failure produces a risk and a pass does not

The SDK SHALL emit a risk only for a control that failed, and SHALL mark a finding satisfied or
not satisfied according to the verdict. A risk raised for a passing control would inflate the
record; a failure with no risk would hide one.

#### Scenario: A risk is emitted only for failures
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_output.py::test_risk_only_for_failures`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a mixed set is emitted
- **THEN** risks correspond to the failing results alone

#### Scenario: No risks at all when everything passes
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_output.py::test_no_risks_when_all_pass`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** every control passes
- **THEN** the document carries no risks

#### Scenario: A passing control is marked satisfied
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_output.py::test_finding_status_satisfied`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a control passes
- **THEN** its finding is marked satisfied

#### Scenario: A failing control is marked not satisfied
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_output.py::test_finding_status_not_satisfied`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a control fails
- **THEN** its finding is marked not satisfied

#### Scenario: A risk resolves to the finding that raised it
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_output.py::test_risk_links_to_finding`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a failure produces a risk
- **THEN** the risk resolves to its finding

### Requirement: A failure also produces a plan of action whose items stay open

A failing control SHALL produce a plan-of-action item, one per failure, carrying the same risks as
the assessment and left open. A failure recorded with no item to act on is a finding nobody owns.

#### Scenario: A plan of action appears only when something failed
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_output.py::test_no_poam_when_all_pass`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** every control passes
- **THEN** no plan of action is produced

#### Scenario: One plan item per failure
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_output.py::test_one_poam_item_per_failure`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** several controls fail
- **THEN** the plan holds one item per failure

#### Scenario: Plan items are open
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_output.py::test_poam_items_status_open`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a plan of action is produced
- **THEN** its items are open, so nothing is filed as already handled

#### Scenario: The plan's risks are the assessment's risks
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_output.py::test_poam_risks_match_ar_risks`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** both documents are produced from one run
- **THEN** they carry the same risks, so the two cannot disagree about what went wrong

### Requirement: The emitted documents are canonical OSCAL that a third party can ingest

Both documents SHALL be valid OSCAL, SHALL declare their OSCAL version, SHALL use the canonical
key spelling, and SHALL omit empty fields rather than serialising them. A document that only this
SDK can read is not interoperability, and a key spelled our way is a private dialect.

#### Scenario: The assessment results document is valid
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_output.py::test_ar_json_is_valid`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** results are emitted
- **THEN** the document is valid OSCAL

#### Scenario: The plan of action document is valid
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_output.py::test_poam_json_is_valid`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a plan of action is emitted
- **THEN** the document is valid OSCAL

#### Scenario: Keys use the canonical spelling
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_output.py::test_kebab_case_keys`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a document is serialised
- **THEN** its keys use the canonical spelling rather than a Python-side one

#### Scenario: The OSCAL version is declared
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_output.py::test_oscal_version_in_metadata`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a document is serialised
- **THEN** it declares the OSCAL version it conforms to

#### Scenario: Empty fields are omitted rather than serialised
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_output.py::test_no_empty_fields_serialized`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a document is serialised
- **THEN** empty fields are absent, so a consumer never reads an empty value as a declared one

#### Scenario: The findings survive a round trip
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_output.py::test_roundtrip_finding_count`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** an emitted document is read back
- **THEN** it holds the findings it was built with

#### Scenario: The policy the results were measured against is recorded
- **Status:** CURRENT
- **Proof:** `tests/test_oscal_output.py::test_policy_href_stored`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** results are emitted
- **THEN** the document records which policy produced them
