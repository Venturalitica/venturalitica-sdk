# retained-vault

## Purpose

The retained vault holds the subset of evaluated results that the caller explicitly retained, and
that subset alone is what leaves the machine as a signed OSCAL assessment. It exists because a
pipeline may evaluate the same control over more than one partition of the data, so a verdict is
meaningless unless it is bound to the data it was computed over.

## Requirements

### Requirement: The vault holds what was retained, not everything evaluated

A pipeline may call `enforce` more than once over different partitions and filter afterwards. The
SDK SHALL persist to the retained vault only the results passed to `retain`, and SHALL NOT persist
the union of everything evaluated. The evaluated cache remains complete and separate: that is
deliberate, and it is not what makes the two disagree.

#### Scenario: Two partitions are evaluated and only one is retained
- **Status:** CURRENT
- **Proof:** `tests/test_vault_retained.py::test_la_boveda_guarda_lo_RETENIDO_no_todo_lo_evaluado`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** two controls are evaluated over different partitions and only the first is retained
- **THEN** the retained vault holds exactly the first control
- **AND** the evaluated cache still holds both

#### Scenario: Retaining the same results twice is a re-declaration, not a second contribution
- **Status:** CURRENT
- **Proof:** `tests/test_vault_retained.py::test_retain_es_idempotente_no_duplica_al_repetirse`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** `retain` is called twice with the same list
- **THEN** the retained vault holds one entry, not two
- **AND** the emitted assessment carries one observation and one finding rather than duplicates

### Requirement: Only what was retained can leave the machine

The document `vl push` uploads SHALL be derived from the retained vault. It SHALL NOT fall back to
the unfiltered evaluated cache, because a fallback would upload the union of every call while the
pipeline's own authoritative metrics report the filtered subset, with no mark saying which governs.

#### Scenario: The uploaded assessment carries only the retained partition
- **Status:** CURRENT
- **Proof:** `tests/test_vault_retained.py::test_el_ar_que_sube_vl_push_contiene_solo_lo_retenido`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the same control is evaluated over two partitions inside a session and one is retained
- **THEN** the emitted assessment-results document holds exactly one finding and one observation
- **AND** the observed value is the retained partition's value, not the other one's

#### Scenario: Retaining nothing is a valid declaration and is recorded as one
- **Status:** CURRENT
- **Proof:** `tests/test_vault_retained.py::test_retain_vacio_no_deja_que_el_ar_caiga_a_lo_evaluado_sin_filtrar`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the pipeline filters and nothing survives, and `retain` is called with an empty list
- **THEN** an empty retained vault is written rather than no vault at all
- **AND** no assessment-results document is emitted, so an upload fails loudly instead of
  silently uploading the unfiltered union

#### Scenario: Retaining outside a session says so instead of failing silently
- **Status:** CURRENT
- **Proof:** `tests/test_vault_retained.py::test_retain_fuera_de_monitor_avisa_y_no_rompe_nada`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** `retain` is called with no active session, having nowhere to write
- **THEN** a warning naming `retain` is printed
- **AND** the call returns its input unchanged, so it stays chainable and breaks no flow

### Requirement: Every retained result declares the partition it was computed over

Each retained result SHALL carry a digest of the data the measurement ran on. Without it, two
measurements of the same control over different partitions are indistinguishable by inspection:
they share a control identifier and differ only in a number nobody can attribute.

#### Scenario: The same control over two partitions yields two distinct digests
- **Status:** CURRENT
- **Proof:** `tests/test_vault_retained.py::test_cada_resultado_retenido_declara_sobre_que_particion_se_computo`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** one control identifier is evaluated over two different partitions and both are retained
- **THEN** both retained results carry a non-empty partition digest
- **AND** the two digests differ

#### Scenario: The digest reaches the assessment even when the control passes
- **Status:** CURRENT
- **Proof:** `tests/test_vault_retained.py::test_el_digest_llega_al_ar_incluso_si_el_control_pasa`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a control passes and its result is emitted into the assessment
- **THEN** the observation carries the partition digest
- **AND** the digest is not reserved to the risk facets of a failing control, because the
  misleading measurement is typically the one that passes

#### Scenario: The fallback digest still separates partitions that differ late in the table
- **Status:** CURRENT
- **Proof:** `tests/test_vault_retained.py::test_digest_no_colisiona_cuando_hash_pandas_object_falla`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a column holds unhashable values, so the primary hash cannot be used
- **THEN** two large partitions differing only past a truncation point still produce different
  digests

#### Scenario: The digest declares the algorithm that produced it
- **Status:** PENDING
- **Reason:** the digest is emitted as bare hexadecimal with no algorithm key, against this
  project's frozen convention that every digest travels as an algorithm-keyed set. It is inert
  today because the vault is git-ignored and the value travels to no third party, and it stops
  being inert the moment the vault is uploaded or ingested elsewhere. The repair is to the form
  and not to the substance: the digest must keep existing. A value with no declared algorithm
  reads as *unknown algorithm*, never as an assumed one, because assuming would invent a match.
- **WHEN** a retained result is written to the vault
- **THEN** its partition digest names the algorithm that produced it

### Requirement: The vault is durable evidence that outlives the process

A run SHALL leave its measurements on disk in a form that survives the process that produced them.
An assessment nobody can re-read afterwards is not evidence.

#### Scenario: A run directory holds the measurements it claims
- **Status:** UNPROVEN
- **Reason:** nothing that runs pins it. `tests/test_session.py` asserts the artefact directory
  *exists*, never that it holds anything, so a silent write failure would leave every test green.
  A run directory that exists with no measurements in it is the stated failure of this step, and
  whether the empty artefact directories observed on a development machine are correct behaviour
  or a silent write failure is **not measured**. Not measured is not the same as fine.
- **WHEN** a session ends after producing artefacts
- **THEN** the run's artefact directory holds them
