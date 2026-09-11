# annex-iv

## Purpose

The technical documentation is derived from the evidence a run gathered, not written afterwards as
prose. Every claim in it should trace back to a measurement, because a claim appearing in a
technical file with no measurement behind it is the failure this SDK exists to prevent.

## Requirements

### Requirement: The uploaded bundle carries the measurements and their provenance

The bundle the SDK transfers SHALL carry the run's metrics, its declared artefacts and its traces,
so that a receiving system reads evidence rather than assertions.

#### Scenario: The bundle carries the run's metrics
- **Status:** CURRENT
- **Proof:** `tests/test_cli_transfer.py::test_metrics_key`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a run's results are bundled for transfer
- **THEN** the payload carries the metrics

#### Scenario: The bundle carries the declared artefacts
- **Status:** CURRENT
- **Proof:** `tests/test_cli_transfer.py::test_artifacts_key`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a run declared artefacts
- **THEN** the payload carries them, named

#### Scenario: Metrics before and after treatment are both carried
- **Status:** CURRENT
- **Proof:** `tests/test_cli_transfer.py::test_pre_post_metrics`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a run measured before and after a treatment
- **THEN** both sets travel, so an improvement cannot be shown without its baseline

#### Scenario: A trace carries its bill of materials and its timestamp
- **Status:** CURRENT
- **Proof:** `tests/test_cli_transfer.py::test_trace_with_bom_and_timestamp`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a trace holds an inventory and a timestamp
- **THEN** both travel with it

#### Scenario: A trace with no timestamp falls back to the file's own time
- **Status:** CURRENT
- **Proof:** `tests/test_cli_transfer.py::test_trace_without_timestamp_mtime_fallback`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a trace carries no timestamp of its own
- **THEN** the file's modification time is used rather than the trace being dated to now

#### Scenario: A corrupt trace is skipped rather than failing the whole transfer
- **Status:** CURRENT
- **Proof:** `tests/test_cli_transfer.py::test_trace_invalid_json_skipped`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** one trace on disk does not parse
- **THEN** it is skipped and the remaining evidence still transfers

### Requirement: Nothing is uploaded that was not measured

The SDK SHALL refuse to transfer when there are no results to transfer, and SHALL authenticate the
transfer when credentials are present. Uploading an empty or unattributable bundle would put a
record into a receiving system that no run stands behind.

#### Scenario: A transfer with no results fails loudly
- **Status:** CURRENT
- **Proof:** `tests/test_cli_transfer.py::test_missing_results_json`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** there are no results on disk
- **THEN** the transfer fails rather than sending an empty bundle

#### Scenario: A transfer without a logged-in account does not proceed
- **Status:** CURRENT
- **Proof:** `tests/test_cli_transfer.py::test_push_not_logged_in`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** no account is logged in
- **THEN** the transfer stops and says so

#### Scenario: The bundle is signed when credentials are present
- **Status:** CURRENT
- **Proof:** `tests/test_cli_transfer.py::test_hmac_with_credentials`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** credentials are configured
- **THEN** the payload carries its authentication

#### Scenario: Corrupt credentials do not silently produce an unsigned transfer
- **Status:** CURRENT
- **Proof:** `tests/test_cli_transfer.py::test_hmac_with_corrupt_credentials`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the stored credentials cannot be read
- **THEN** the transfer does not quietly proceed unsigned

#### Scenario: A rejected transfer reports why
- **Status:** CURRENT
- **Proof:** `tests/test_cli_transfer.py::test_push_failure_json_error`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the receiving system rejects the bundle
- **THEN** the reason is reported rather than the failure being swallowed

### Requirement: The system description is derived from what the run observed

The SDK SHALL derive the system description from the run's own inventory and repository, and
SHALL fall back rather than fail when a source is absent or unreadable. A description invented in
place of a missing source would be exactly the unfounded claim this document exists to exclude.

#### Scenario: A description is derived from the run's inventory
- **Status:** CURRENT
- **Proof:** `tests/test_inference.py::test_infer_system_description_mock`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a system description is inferred from a run
- **THEN** it is produced from the run's own evidence

#### Scenario: An unreadable inventory does not stop the description
- **Status:** CURRENT
- **Proof:** `tests/test_inference.py::test_infer_system_description_bom_parse_failure`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the inventory cannot be parsed
- **THEN** the description is still produced rather than the whole derivation failing

#### Scenario: The repository's own README is used when present
- **Status:** CURRENT
- **Proof:** `tests/test_inference.py::test_infer_system_description_readme_discovery`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the repository holds a README
- **THEN** it is used as a source for the description

#### Scenario: A risk classification wrapped in a code block is still read
- **Status:** CURRENT
- **Proof:** `tests/test_inference.py::test_infer_risk_classification_markdown_code_block`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the classification comes back wrapped in a fenced code block
- **THEN** it is extracted rather than read as prose

#### Scenario: A failed derivation falls back instead of inventing
- **Status:** CURRENT
- **Proof:** `tests/test_inference.py::test_infer_risk_classification_exception_fallback`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the derivation fails
- **THEN** a declared fallback is used rather than an invented classification

### Requirement: The agentic writer drafts the technical file from the gathered traces

The agentic writer SHALL assemble the technical documentation from the traces a run gathered, so
that each section of the file rests on a measurement rather than on prose supplied afterwards.

#### Scenario: The writer assembles the file from a run's traces
- **Status:** UNPROVEN
- **Reason:** nothing that runs pins it. The behaviour exists — the writer is implemented under
  `src/venturalitica/assurance/graph/` — and ten tests cover it in `tests/test_graph_nodes.py`,
  but that module calls `pytest.importorskip` on `langchain_core`, which lives in the `agentic`
  extra and is not installed by `uv sync --group dev`. Because the skip fires at module level
  during collection, those ten tests never appear in a CI run at all, not even as skips. This is
  the ENVIRONMENT family: the tests exist and could run, and installing the extra in CI would
  fix it. That is deliberately not done yet, because the count is measured data behind a decision
  dated 2026-09-11 and installing the extra now moves the number that decision rests on.
- **WHEN** a run's traces are handed to the agentic writer
- **THEN** the drafted file's sections rest on those traces

#### Scenario: Every claim in the technical file traces back to a measurement
- **Status:** PENDING
- **Reason:** no check anywhere enforces it. The transfer carries the measurements and the
  derivation prefers observed sources, but nothing verifies that each claim in the emitted file
  resolves to a measurement in the run — a claim added by hand, or produced by the writer without
  a supporting trace, would travel exactly like a derived one. This is the failure the whole SDK
  exists to prevent, and it is the one currently least guarded against in its own output.
- **WHEN** a technical file is emitted
- **THEN** every claim in it resolves to a measurement gathered by the run that produced it
