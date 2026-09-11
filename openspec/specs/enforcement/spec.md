# enforcement

## Purpose

Enforcement runs an authored policy against real data and returns a verdict per control: the
observed value, the threshold, the comparison and the outcome. What the caller asked for decides
whether a failing control halts the run, records and continues, or merely reports, and that choice
has to be explicit rather than inferred.

## Requirements

### Requirement: A failing control does what the caller asked, and nothing more

The SDK SHALL apply the enforcement mode the caller declared. In strict mode a blocking control
that fails SHALL raise; by default it SHALL record the failure and continue. A control that passes
SHALL NOT raise under any mode.

#### Scenario: A blocking control that fails raises in strict mode
- **Status:** CURRENT
- **Proof:** `tests/test_enforcement_semantics.py::test_block_raises_on_failure_when_strict`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a control declared as blocking fails and strict mode is on
- **THEN** the call raises rather than returning a recorded failure

#### Scenario: The same control records and continues by default
- **Status:** CURRENT
- **Proof:** `tests/test_enforcement_semantics.py::test_block_records_and_continues_by_default`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the same blocking control fails and strict mode is off
- **THEN** the failure is recorded and the run continues

#### Scenario: A passing control never raises
- **Status:** CURRENT
- **Proof:** `tests/test_enforcement_semantics.py::test_block_does_not_raise_on_pass`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a blocking control passes
- **THEN** nothing is raised

#### Scenario: Strict mode halts before the controls that follow
- **Status:** CURRENT
- **Proof:** `tests/test_enforcement_semantics.py::test_block_halts_before_subsequent_controls_when_strict`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a blocking control fails under strict mode and further controls are queued
- **THEN** the later controls do not run, because continuing past a blocking failure would
  produce measurements attributed to a state that was supposed to be unreachable

#### Scenario: Without strict mode the later controls still run
- **Status:** CURRENT
- **Proof:** `tests/test_enforcement_semantics.py::test_block_does_not_halt_subsequent_controls_by_default`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the same failure happens with strict mode off
- **THEN** the remaining controls are evaluated

#### Scenario: Monitoring is silent and stays silent
- **Status:** CURRENT
- **Proof:** `tests/test_enforcement_semantics.py::test_monitor_is_silent_default`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a control is in monitoring mode
- **THEN** nothing is written to the error stream, so monitoring never looks like a warning

#### Scenario: Warning mode writes to the error stream and continues
- **Status:** CURRENT
- **Proof:** `tests/test_enforcement_semantics.py::test_warn_emits_stderr_and_continues`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a control in warning mode fails
- **THEN** the warning reaches the error stream and the run continues

### Requirement: A missing metric is a failure in strict mode, not a silent pass

When a control names a metric the run cannot produce, the SDK SHALL raise under strict mode rather
than treating the absent measurement as satisfied. A control that passes without a value is the
single most misleading outcome this SDK can emit.

#### Scenario: A missing metric raises when strict mode comes from the CI environment
- **Status:** CURRENT
- **Proof:** `tests/test_strict_mode.py::test_strict_mode_via_ci_env_raises_on_missing_metric`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the run is in a CI environment and a control's metric cannot be produced
- **THEN** the call raises

#### Scenario: Strict mode can also be demanded explicitly
- **Status:** CURRENT
- **Proof:** `tests/test_strict_mode.py::test_strict_mode_via_explicit_env_raises`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** strict mode is requested explicitly outside CI
- **THEN** the same missing metric raises

#### Scenario: Outside strict mode the missing metric is swallowed
- **Status:** CURRENT
- **Proof:** `tests/test_strict_mode.py::test_loose_mode_swallows_missing_metric`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** strict mode is off and a control's metric cannot be produced
- **THEN** the run continues, which is why CI turns strict mode on

### Requirement: A control runs only in the lifecycle phase it belongs to

A control tagged for a phase SHALL be evaluated only in that phase, and an untagged control SHALL
run in every phase. Otherwise a training-time control would report a verdict about validation data
and the finding would be attributed to the wrong stage.

#### Scenario: A training control runs only during training
- **Status:** CURRENT
- **Proof:** `tests/test_enforcement_semantics.py::test_phase_training_filters_in_only_training`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the run declares the training phase
- **THEN** only the controls tagged for training are evaluated

#### Scenario: A validation control runs only during validation
- **Status:** CURRENT
- **Proof:** `tests/test_enforcement_semantics.py::test_phase_validation_filters_in_only_validation`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the run declares the validation phase
- **THEN** only the controls tagged for validation are evaluated

#### Scenario: An untagged control runs in any phase
- **Status:** CURRENT
- **Proof:** `tests/test_enforcement_semantics.py::test_untagged_controls_run_in_any_phase`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a control carries no phase tag
- **THEN** it is evaluated whichever phase is declared

### Requirement: The session captures the model's lineage wherever the model is built

The governance session SHALL capture the traces of the model itself — the session, the bill of
materials and the lineage of the fit — and not only the measurement that follows. That lineage is
what fills the model-development section of the technical file.

#### Scenario: The lineage is captured when the fit happens in another process
- **Status:** PENDING
- **Reason:** the session is a Python context manager and does not cross process boundaries. In
  any pipeline of more than one stage it can only wrap what happens inside a single command, so a
  fit that runs as its own stage falls outside every session and the model never enters the
  trace. This is structural rather than a misconfigured script: it depends on the number of
  stages. The SDK's own quickstart already states that wrapping training and validation is what
  feeds the technical file, so the gap is between what the SDK knows it needs and what it can
  currently reach. Tracked outside this repository.
- **WHEN** the model is built in a process that does not open a session
- **THEN** its lineage still reaches the trace
