# ml-bom

## Purpose

The machine-learning bill of materials inventories what a governed run was made of: the artefact
under governance, the declared product dependencies and the environment that took the
measurement. It has to separate those subjects rather than merge them, and it has to be the same
document for the same inventory, or it cannot be versioned alongside the evidence it describes.

## Requirements

### Requirement: The document is determined by its inventory, not by the clock

The same inventory SHALL produce the same document, byte for byte. A document that changes on
every run cannot be committed, and a bill of materials that cannot be committed does not exist in
a clean clone — so any run that does not re-measure signs a record set with no inventory in it.

#### Scenario: Two runs over the same inputs produce the same document
- **Status:** CURRENT
- **Proof:** `tests/test_bom_determinism.py::test_dos_corridas_con_las_mismas_entradas_dan_el_mismo_documento`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the scanner runs twice over an unchanged tree
- **THEN** the two documents are identical

#### Scenario: Neither the serial number nor the timestamp comes from the clock
- **Status:** CURRENT
- **Proof:** `tests/test_bom_determinism.py::test_ni_el_serial_ni_la_marca_de_tiempo_dependen_del_reloj`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the scanner runs twice
- **THEN** the serial number is not a fresh identifier per run
- **AND** the timestamp does not come from the clock

#### Scenario: Determinism is not constancy
- **Status:** CURRENT
- **Proof:** `tests/test_bom_determinism.py::test_un_cambio_real_de_componentes_si_cambia_el_documento`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the components actually change
- **THEN** the document changes, because a document that never changes would also be useless

#### Scenario: A declared pin matching the installed version does not reintroduce noise
- **Status:** CURRENT
- **Proof:** `tests/test_bom_determinism.py::test_el_pin_declarado_que_coincide_con_lo_instalado_no_rompe_el_determinismo`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the environment satisfies its own declared pin, so one package is seen as both product
  and measurement environment
- **THEN** the document is still identical across runs

### Requirement: The product and the bench that measured it stay distinguishable

A component SHALL declare which subject it is. Where the same package is both the product and part
of the measurement environment it SHALL be one component carrying both labels, and where the
declared and installed versions differ they SHALL remain two components, because that divergence
is exactly what an inventory exists to show.

#### Scenario: One package that is both subjects is one component with both labels
- **Status:** CURRENT
- **Proof:** `tests/test_bom_determinism.py::test_el_pin_coincidente_fusiona_en_UN_componente_con_los_dos_sujetos`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a package is both the declared product dependency and present in the measuring
  environment at the same version
- **THEN** it appears once, carrying both subject labels

#### Scenario: A declared version that differs from the installed one stays two components
- **Status:** CURRENT
- **Proof:** `tests/test_bom_determinism.py::test_versiones_distintas_siguen_siendo_DOS_componentes`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the declared pin and the installed version disagree
- **THEN** both remain visible as separate components, so the divergence is not merged away

#### Scenario: The measuring environment travels labelled
- **Status:** CURRENT
- **Proof:** `tests/test_bom_subjects.py::test_el_entorno_de_medida_viaja_ETIQUETADO_y_no_se_confunde_con_el_producto`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the environment is inventoried alongside the product
- **THEN** it is labelled as the environment and is not read as part of the product

#### Scenario: The product declares the pinned version rather than the installed one
- **Status:** CURRENT
- **Proof:** `tests/test_bom_subjects.py::test_el_producto_declara_la_version_PINEADA_no_la_instalada`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the product's declared version differs from what happens to be installed
- **THEN** the product component carries the declared one

#### Scenario: A project declaring dependencies in the older layout is not invisible
- **Status:** CURRENT
- **Proof:** `tests/test_bom_subjects.py::test_un_pyproject_de_poetry_ya_no_es_invisible`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** dependencies are declared in the alternative layout rather than the standard one
- **THEN** they are inventoried rather than silently producing an empty product section

#### Scenario: A version constraint is not dressed up as a version number
- **Status:** CURRENT
- **Proof:** `tests/test_bom_subjects.py::test_restricciones_de_poetry_no_se_disfrazan_de_numero_de_version`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a dependency is declared as a constraint rather than a fixed version
- **THEN** the constraint is not recorded as though it were the resolved version

### Requirement: The governed artefact is in the inventory

The artefact under governance SHALL appear in the inventory with its digest, and SHALL be
distinguishable from the datasets declared beside it. An inventory of a system whose governed
artefact is a model, that does not contain the model, describes the toolchain rather than the
subject.

#### Scenario: The governed model enters the inventory with its digest
- **Status:** CURRENT
- **Proof:** `tests/test_bom_artefactos.py::test_el_modelo_gobernado_entra_en_el_inventario_con_su_digest`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a run declares a governed model
- **THEN** the model is inventoried, carrying its digest

#### Scenario: A declared dataset is not marked as a model
- **Status:** CURRENT
- **Proof:** `tests/test_bom_artefactos.py::test_un_dataset_declarado_no_se_marca_como_modelo`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a dataset is declared alongside the model
- **THEN** it is not inventoried as a model

#### Scenario: The subject of the document travels in its metadata
- **Status:** CURRENT
- **Proof:** `tests/test_bom_artefactos.py::test_el_sujeto_del_documento_viaja_en_metadata_component`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** a document is emitted
- **THEN** its metadata names what the document is about

#### Scenario: Two lifecycle stages of one environment are two documents
- **Status:** CURRENT
- **Proof:** `tests/test_bom_artefactos.py::test_dos_ETAPAS_del_mismo_entorno_ya_no_dan_el_mismo_documento`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the same environment is inventoried at two declared lifecycle stages
- **THEN** the two documents differ, so a stage is not silently overwritten by another

#### Scenario: A run with neither artefacts nor a declared subject still emits
- **Status:** CURRENT
- **Proof:** `tests/test_bom_artefactos.py::test_sin_artefactos_ni_sujeto_el_BOM_sigue_saliendo`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** nothing is declared
- **THEN** a document is still produced, rather than the absence of a subject removing the
  inventory altogether

#### Scenario: The full environment inventory is opt-in
- **Status:** CURRENT
- **Proof:** `tests/test_bom_artefactos.py::test_el_inventario_completo_del_entorno_es_OPT_IN`
- **Accepted:** not yet. No acceptance event exists for this claim.
- **WHEN** the full environment inventory is not requested
- **THEN** it is not produced, so the expensive scan never happens by surprise

#### Scenario: A model built outside any session still enters the inventory
- **Status:** PENDING
- **Reason:** the session cannot reach a fit that runs in another process, so in a multi-stage
  pipeline the model is never registered and the inventory comes out holding only libraries. The
  inventory is then correct about what it saw and wrong about the system: a governed artefact
  that is a derived model, absent from its own bill of materials. The cause is the session's
  process boundary rather than the scanner, and it is recorded under `enforcement` as well.
  Tracked outside this repository.
- **WHEN** the governed model is produced by a stage that opens no session
- **THEN** the model appears in the inventory
