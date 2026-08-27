import ast
import os
import sys
from typing import Optional, Set

from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component, ComponentType
from cyclonedx.model import HashAlgorithm, HashType
from cyclonedx.output.json import JsonV1Dot6
from cyclonedx.schema import SchemaVersion
from packageurl import PackageURL

# CycloneDX schema version emitted by this scanner. Bump when migrating
# the output class (e.g. JsonV1Dot6 → JsonV1Dot7). The SaaS bom-ingestion
# service (bom-ingestion.service.ts) reads the standard CycloneDX schema
# keys (`components[]`, `dependencies[]`, `formulation[]`) and is forward
# compatible across 1.5 → 1.6 → 1.7.
CYCLONEDX_SCHEMA_VERSION = SchemaVersion.V1_6

# Known ML Model classes to detect
KNOWN_MODELS: Set[str] = {
    "RandomForestClassifier", "LogisticRegression", "SVC", "LinearRegression",
    "DecisionTreeClassifier", "KNeighborsClassifier", "GradientBoostingClassifier",
    "XGBClassifier", "LGBMClassifier", "CatBoostClassifier",
    "Sequential", "Module", "resnet18", "resnet50"
}

# CycloneDX property that tags *what* a component describes: the software
# the client deploys (`SUBJECT_PRODUCT`), or the interpreter that happened
# to run the measurement (`SUBJECT_MEASUREMENT_ENVIRONMENT`). Without this,
# a scan resolves `importlib.metadata` against the live interpreter and the
# BOM silently presents the scanner's own environment as if it were the
# inventoried product — mdr.soup-inventory (IEC 62304 §8.1.2) is satisfied
# on the wrong subject. `properties[]` is the CycloneDX-standard slot for
# vendor metadata: unlike a `bom-ref` naming convention, a consumer that
# doesn't know this property simply ignores it instead of misparsing it.
SUBJECT_PROPERTY_NAME = "venturalitica:subject"
SUBJECT_PRODUCT = "product"
SUBJECT_MEASUREMENT_ENVIRONMENT = "measurement-environment"

class BOMScanner:
    """
    Scans a directory to generate a CycloneDX Bill of Materials (BOM)
    for Python projects, including dependencies and ML models.
    """
    
    # Extensiones que identifican un fichero de PESOS. CycloneDX ya tiene el tipo
    # `machine-learning-model` desde 1.5, así que esto solo decide CUÁL de los tipos
    # estándar aplica — no inventa vocabulario.
    _EXT_MODELO = (".pth", ".pt", ".onnx", ".safetensors", ".pkl", ".joblib", ".h5", ".keras", ".ckpt")

    def __init__(self, target_dir: str):
        self.target_dir = target_dir
        self.bom = Bom()
        self._artefactos: list = []
        self._sujeto: Optional[str] = None

    def declarar_sujeto(self, nombre: str) -> None:
        """Declara DE QUÉ trata este BOM, en `metadata.component`.

        Es el campo que CycloneDX reserva para el sujeto del documento y estaba sin
        poner. Su ausencia es la causa exacta de que dos etapas del MISMO entorno de
        Python produjeran BOM idénticos byte a byte (medido en el piloto de
        CyberSurgery: `sha256 dbc77ee3…` en adopción y en validación). Sin sujeto, el
        documento no sabe nombrar su propia etapa, y como linaje del Anexo IV §2 no
        aporta nada — un artefacto que no puede salir distinto no describe nada.
        """
        self._sujeto = nombre

    def declarar_artefactos(self, artefactos: list) -> None:
        """Artefactos que la etapa declara (`vl.monitor(inputs=…, outputs=…)`).

        El escáner resuelve paquetes de Python con `importlib.metadata`, así que por
        construcción NO podía ver un fichero de pesos: un `.pth` no es una
        distribución. Por eso `cl.mdr.soup-inventory` (IEC 62304 §8.1.2) quedaba
        incompleto sobre el objeto que de verdad se despliega.

        El dato ya existía —`ArtifactProbe` captura estos mismos artefactos con su
        `fingerprint` sha256— y simplemente no llegaba hasta aquí.
        """
        self._artefactos = list(artefactos or [])

    def scan(self) -> str:
        """
        Orchestrates the scanning process and returns the BOM as a JSON string.

        Emits CycloneDX v1.6 — adds ML-BOM `formulation` support and the
        full `vulnerabilities[]` schema vs. v1.5. The SaaS ingester
        (`bom-ingestion.service.ts`) is forward-compatible across 1.5/1.6/1.7;
        we pick the highest version with a stable cyclonedx-python-lib emitter.

        The output is deterministic for identical inputs: `Bom()` seeds a
        random `serial_number` and `BomMetaData()` seeds a wall-clock
        `timestamp`, both via public properties, so a re-scan of unchanged
        inputs would otherwise diff on every run. Clearing them (both
        setters accept `None` and the CycloneDX JSON writer simply omits
        the field when unset) is what lets the BOM be committed to git and
        found where the engine looks for it — a re-run over unchanged
        inputs leaves the working tree clean instead of always dirty.
        """
        self._scan_requirements()
        self._scan_pyproject()
        self._scan_imports()
        self._scan_models()
        self._add_declared_artifacts()

        self.bom.serial_number = None
        self.bom.metadata.timestamp = None
        # `metadata.component` es el sujeto del documento. Se pone DESPUÉS de limpiar
        # el timestamp para no reintroducir no-determinismo: el nombre lo da quien
        # declara la etapa, no el reloj.
        if self._sujeto:
            self.bom.metadata.component = Component(
                name=self._sujeto, type=ComponentType.APPLICATION, bom_ref=f"stage:{self._sujeto}"
            )

        output = JsonV1Dot6(self.bom).output_as_string()
        return output

    def _scan_imports(self) -> None:
        """
        AST-walk every .py file under target_dir collecting top-level
        imported package names. Resolve each via importlib.metadata to
        confirm it's a real installed distribution + capture its
        version. Emits one CycloneDX Component(type=LIBRARY) per
        observed dependency.

        Why: requirements.txt / pyproject.toml is rarely present in
        scenario directories — the trainer just imports `mlflow`,
        `sklearn`, `pandas`, `fairlearn`, etc. Without import scanning,
        the BOM was reduced to AST-detected model class instances,
        leaving the platform's ManagedItem(ICT_THIRD_PARTY) inventory
        empty (DORA Art.28(9) gap). The set of imported top-level
        packages observed in the run directory is the most honest
        proxy for "what does this AI system actually depend on".

        Filtering rules:
          - Only top-level package (`from sklearn.linear_model import X`
            → 'sklearn').
          - Skip stdlib modules (sys.stdlib_module_names; Python 3.10+).
          - Skip relative imports (level > 0 — those are local).
          - Skip the SDK itself (`venturalitica`) — it's not a
            third party from the user's POV.
          - Dedupe across files.
          - Skip names that don't resolve to an installed
            distribution (filters typo'd / vendored).
        """
        try:
            import importlib.metadata as _md
        except ImportError:  # pragma: no cover — Python <3.8 unsupported
            return
        try:
            stdlib = set(sys.stdlib_module_names)  # type: ignore[attr-defined]
        except AttributeError:
            # Python <3.10 — best-effort fallback list of common stdlib roots.
            stdlib = {
                'os', 'sys', 'json', 're', 'time', 'datetime', 'math',
                'pathlib', 'typing', 'collections', 'itertools', 'functools',
                'subprocess', 'shutil', 'tempfile', 'logging', 'asyncio',
                'urllib', 'http', 'io', 'csv', 'sqlite3', 'hashlib', 'hmac',
                'base64', 'uuid', 'random', 'pickle', 'argparse', 'unittest',
                'ast', 'inspect', 'dataclasses', 'enum', 'warnings', 'copy',
                'string', 'struct', 'threading', 'multiprocessing',
            }
        skip = {'venturalitica'}

        EXCLUDE_DIRS = {'.venv', 'venv', '__pycache__', '.git', '.ipynb_checkpoints'}
        observed: Set[str] = set()
        for root, dirs, files in os.walk(self.target_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                if not file.endswith('.py'):
                    continue
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read(), filename=path)
                except Exception:
                    continue
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            top = (alias.name or '').split('.')[0]
                            if top:
                                observed.add(top)
                    elif isinstance(node, ast.ImportFrom):
                        if (node.level or 0) > 0:
                            continue  # relative import, local
                        if not node.module:
                            continue
                        top = node.module.split('.')[0]
                        observed.add(top)

        # Map import-name → distribution-name(s). Many libraries ship
        # under a different distribution name than their importable
        # module (sklearn → scikit-learn, cv2 → opencv-python, yaml →
        # PyYAML, etc.). importlib.metadata.packages_distributions()
        # was added in Python 3.10 and uses the runtime metadata to
        # resolve this honestly. Fall back to the import-name
        # verbatim for older runtimes.
        try:
            import_to_dist = _md.packages_distributions()  # type: ignore[attr-defined]
        except AttributeError:
            import_to_dist = {}

        emitted: Set[str] = set()
        for name in sorted(observed):
            if not name or name in stdlib or name in skip:
                continue
            distributions = import_to_dist.get(name)
            if not distributions:
                # Fall back to import-name as distribution name (works
                # when they happen to coincide, e.g. `requests`).
                distributions = [name]
            for dist_name in distributions:
                if dist_name in emitted:
                    continue
                try:
                    version = _md.version(dist_name)
                except _md.PackageNotFoundError:
                    continue
                emitted.add(dist_name)
                self._add_component(
                    dist_name, version, ComponentType.LIBRARY,
                    subject=SUBJECT_MEASUREMENT_ENVIRONMENT,
                )

    def _scan_requirements(self) -> None:
        """Parses requirements.txt if present."""
        req_file = os.path.join(self.target_dir, "requirements.txt")
        if not os.path.exists(req_file):
            return

        with open(req_file, "r") as f:
            for line in f:
                self._process_requirement_line(line)

    def _process_requirement_line(self, line: str) -> None:
        """Parses a single line from requirements.txt."""
        line = line.strip()
        if not line or line.startswith("#"):
            return

        # Naive parsing. In production, use 'packaging.requirements'
        # Splits on operators to find package name
        name = line.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].strip()
        version: Optional[str] = None
        
        # Try to extract version
        if "==" in line:
            version = line.split("==")[1].split(";")[0].strip()
        elif ">=" in line:
            version = line.split(">=")[1].split(";")[0].strip()
            
        if name:
            self._add_component(name, version, ComponentType.LIBRARY)

    def _scan_pyproject(self) -> None:
        """Scans pyproject.toml for declared product dependencies.

        Reads both layouts a repository may use — they aren't mutually
        exclusive, so both are scanned when present:

        - **PEP 621** (`[project]` / `dependencies = [...]`) — version
          pins come from `_process_requirement_line`, same as
          requirements.txt.
        - **Poetry** (`[tool.poetry.dependencies]`) — a map of
          name→constraint rather than a list of strings. Without this,
          a Poetry-only repository (the client's, in this piloto) has
          zero product components: the BOM falls back to whatever
          `_scan_imports` resolves off the live interpreter, silently
          presenting the measurement bench as the product.

        All components found here describe the **product** the client
        declared — never the environment that happened to run the scan.
        """
        pyproject_path = os.path.join(self.target_dir, "pyproject.toml")
        if not os.path.exists(pyproject_path):
            return

        try:
            import tomllib
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
        except (ImportError, Exception):
            # Fallback or error handling
            return

        # Standard PEP 621 dependencies
        project = data.get("project", {})

        # Try to get project license for the root component
        license_info = project.get("license")
        root_license = None
        if isinstance(license_info, dict):
            root_license = license_info.get("text") or license_info.get("file")
        elif isinstance(license_info, str):
            root_license = license_info

        if root_license:
            self._add_component(project.get("name", "root"), project.get("version"), ComponentType.LIBRARY, licenses=[root_license])

        for dep in project.get("dependencies", []):
            self._add_dependency_str(dep)

        # Optional deps
        optional = project.get("optional-dependencies", {})
        for group_deps in optional.values():
            for dep in group_deps:
                self._add_dependency_str(dep)

        self._scan_poetry_dependencies(data)

    def _scan_poetry_dependencies(self, data: dict) -> None:
        """Reads `[tool.poetry.dependencies]`, the Poetry dependency layout.

        Shaped differently from PEP 621's list of strings: it's a map of
        `name -> constraint`, and the `python` key isn't a component at
        all — it's the interpreter requirement, same role as
        `requires-python` under `[project]`.
        """
        poetry = data.get("tool", {}).get("poetry", {})
        dependencies = poetry.get("dependencies", {})
        for name, constraint in dependencies.items():
            if name.lower() == "python":
                continue
            version = self._parse_poetry_constraint(constraint)
            self._add_component(name, version, ComponentType.LIBRARY)

    @staticmethod
    def _parse_poetry_constraint(constraint) -> Optional[str]:
        """Extracts a single version string from a Poetry constraint.

        Poetry constraints come in three shapes:

        - a bare string, possibly with a leading operator:
          `"2.0.1"`, `"^3.11"`, `"~2.0"`. The pinned number is what
          matters for the BOM, so the operator is stripped.
        - a table with a `version` key (plus `extras`, `optional`, ...):
          `{version = "~2.1", extras = ["gpu"]}`. Same stripping applies
          to the nested `version`.
        - a range or union (`">=1.2,<2"`, `"1.0 || 2.0"`): this isn't a
          pin, and collapsing it to one number would invent a version
          nobody declared. It's kept verbatim instead — a range showing
          up as `version` is honest; a fabricated pin isn't.
        """
        if isinstance(constraint, dict):
            constraint = constraint.get("version")
        if not isinstance(constraint, str):
            return None
        constraint = constraint.strip()
        if not constraint:
            return None
        if "," in constraint or "||" in constraint or " " in constraint:
            return constraint
        for prefix in ("^", "~=", "~", ">=", "<=", "==", "!=", ">", "<", "="):
            if constraint.startswith(prefix):
                return constraint[len(prefix):].strip()
        return constraint

    def _add_dependency_str(self, dep_str: str) -> None:
        """Helper to parse dependency string from pyproject.toml."""
        # Clean string from extras like named[extra]
        clean_str = dep_str.split("[")[0]
        self._process_requirement_line(clean_str)

    def _scan_models(self) -> None:
        """Scans .py files for ML model definitions using AST."""
        EXCLUDE_DIRS = {".venv", "venv", "__pycache__", ".git", ".ipynb_checkpoints"}
        for root, dirs, files in os.walk(self.target_dir):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                if file.endswith(".py"):
                    self._analyze_python_file(os.path.join(root, file))

    def _analyze_python_file(self, file_path: str) -> None:
        """Parses a single Python file to find ML models."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=file_path)
                
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    self._check_ast_call(node, file_path)
        except Exception:
            # Skip files that can't be parsed
            pass

    def _check_ast_call(self, node: ast.Call, file_path: str) -> None:
        """Checks if an AST Call node corresponds to a known ML model."""
        model_name = None
        if isinstance(node.func, ast.Name):
            model_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            model_name = node.func.attr
        
        if model_name and model_name in KNOWN_MODELS:
            self._add_component(
                model_name, 
                None, 
                ComponentType.MACHINE_LEARNING_MODEL,
                description=f"Detected in {os.path.basename(file_path)}"
            )

    def _add_declared_artifacts(self) -> None:
        """Emite los artefactos declarados como componentes CycloneDX.

        Cada uno lleva su digest en `hashes[]` —el slot estándar— y se clasifica con
        los tipos que el propio estándar ya define: `machine-learning-model` para un
        fichero de pesos, `data` para el resto (cohortes, tablas). No se inventa
        ningún tipo ni ninguna convención de nombres.

        `bom-ref` va cualificado con `artifact:` porque estos componentes NO tienen
        PURL: no viven en ningún registro de paquetes. El contrato `bom-ref == purl`
        que fijan los tests solo aplica a las librerías, que sí lo tienen.
        """
        from cyclonedx.model import Property

        for art in self._artefactos:
            nombre = art.get("name")
            if not nombre:
                continue
            huella = art.get("fingerprint")
            # `MISSING` es lo que devuelve `FileArtifact.get_fingerprint()` cuando el
            # fichero no está. Anclar eso sería peor que no anclar: un digest inventado.
            hashes = []
            if huella and huella != "MISSING" and len(huella) == 64:
                hashes = [HashType(alg=HashAlgorithm.SHA_256, content=huella)]
            ruta = (art.get("path") or nombre).lower()
            tipo = (
                ComponentType.MACHINE_LEARNING_MODEL
                if ruta.endswith(self._EXT_MODELO)
                else ComponentType.DATA
            )
            self.bom.components.add(Component(
                name=nombre,
                type=tipo,
                bom_ref=f"artifact:{nombre}",
                hashes=hashes,
                properties=[Property(name=SUBJECT_PROPERTY_NAME, value=SUBJECT_PRODUCT)],
            ))

    def _add_component(
        self,
        name: str,
        version: Optional[str],
        type: ComponentType,
        description: Optional[str] = None,
        licenses: Optional[list] = None,
        subject: str = SUBJECT_PRODUCT,
    ) -> None:
        """Add a CycloneDX 1.6 component to the BOM.

        Adds four things over the bare `Component(name, version, type)`
        construction the previous version emitted:

        - **PURL** (`pkg:pypi/<name>@<version>` for libraries) — Package URL
          spec is the canonical CycloneDX identifier. The SaaS ingester's
          `bom-ref` lookup and the OSCAL ML-BOM `formulation[].inputs[].ref`
          edges both resolve via PURL when present.
        - **`bom-ref`** mirrored from the PURL (or `<name>@<version>` for
          ML models without a PyPI mapping) so the graph remains stable
          across rescans.
        - **License enrichment from installed metadata** — for libraries
          we already resolved via `importlib.metadata`, we copy the
          declared `License-Expression` / `License` metadata field into
          the component so the SoA / DORA Art.28(9) inventory has SPDX
          ids without a second pass.
        - **`venturalitica:subject` property** — every component is
          explicitly tagged `product` or `measurement-environment`
          (`SUBJECT_PROPERTY_NAME`), not left to imply "product" by
          the absence of a tag. An explicit tag survives a caller that
          forgets to opt in; an implicit default doesn't.
        - **Merge on matching PURL, not a second component.** A declared
          product dependency and the measurement environment's installed
          version of the SAME package legitimately land here twice (e.g. a
          client whose environment satisfies its own pin). Before the
          `subject` property existed, two `Component`s built from the same
          name+version were equal, so `self.bom.components` (a `SortedSet`)
          folded them into one for free. The property makes them unequal --
          same PURL, different `properties` -- so both now survive, with
          the SAME `bom-ref` (mirrored from the PURL): a collision the
          CycloneDX writer resolves by handing ONE of them a random
          `bom-ref`, non-deterministic across scans. Qualifying the
          `bom-ref` with the subject would "fix" that but break the
          contract `bom-ref == purl` (`tests/test_scanner.py`, the SaaS
          ingester's lookup key). Merging is the honest fix instead: same
          package, same version, both subjects apply to it at once. When
          the version DIFFERS (the declared pin doesn't match what's
          installed -- #971's whole point, e.g. torch 2.0.1 vs. 2.13.0),
          the PURL differs too, so this lookup finds no match and the two
          stay separate components, keeping that divergence visible.
        """
        from cyclonedx.model import Property
        from cyclonedx.model.license import DisjunctiveLicense

        purl: Optional[PackageURL] = None
        if type == ComponentType.LIBRARY and name:
            # PyPI is the assumed registry for Python library components.
            # `version` is optional in PackageURL — emit a name-only PURL
            # when the version is unknown (still better than no identifier).
            try:
                purl = PackageURL(type="pypi", name=name, version=version)
            except Exception:
                purl = None

        if type == ComponentType.LIBRARY and not licenses:
            license_from_metadata = self._lookup_license(name)
            if license_from_metadata:
                licenses = [license_from_metadata]

        if purl is not None:
            existing = next(
                (c for c in self.bom.components if c.purl == purl), None
            )
            if existing is not None:
                if licenses:
                    for lic_name in licenses:
                        existing.licenses.add(DisjunctiveLicense(name=lic_name))
                existing.properties.add(Property(name=SUBJECT_PROPERTY_NAME, value=subject))
                return

        bom_ref: Optional[str] = None
        if purl is not None:
            bom_ref = str(purl)
        elif name:
            bom_ref = f"{name}@{version}" if version else name

        component = Component(
            name=name,
            version=version,
            type=type,
            description=description,
            purl=purl,
            bom_ref=bom_ref,
        )

        if licenses:
            for lic_name in licenses:
                component.licenses.add(DisjunctiveLicense(name=lic_name))

        component.properties.add(Property(name=SUBJECT_PROPERTY_NAME, value=subject))

        self.bom.components.add(component)

    @staticmethod
    def _lookup_license(dist_name: str) -> Optional[str]:
        """Best-effort SPDX-ish license lookup via importlib.metadata.

        PEP 639 introduced `License-Expression`; older packages still ship
        `License` (free-form). We prefer the SPDX expression, fall back to
        the legacy field, return `None` when neither is set rather than
        emitting an empty license slot.
        """
        try:
            import importlib.metadata as _md
        except ImportError:  # pragma: no cover — Python <3.8 unsupported
            return None
        try:
            meta = _md.metadata(dist_name)
        except _md.PackageNotFoundError:
            return None
        except Exception:
            return None
        # PEP 639 first
        expr = meta.get("License-Expression")
        if expr and expr.strip():
            return expr.strip()
        legacy = meta.get("License")
        if legacy and legacy.strip() and legacy.strip().upper() != "UNKNOWN":
            return legacy.strip()
        return None
