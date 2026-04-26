import ast
import os
import sys
from typing import Optional, Set

from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component, ComponentType
from cyclonedx.output.json import JsonV1Dot5

# Known ML Model classes to detect
KNOWN_MODELS: Set[str] = {
    "RandomForestClassifier", "LogisticRegression", "SVC", "LinearRegression",
    "DecisionTreeClassifier", "KNeighborsClassifier", "GradientBoostingClassifier",
    "XGBClassifier", "LGBMClassifier", "CatBoostClassifier",
    "Sequential", "Module", "resnet18", "resnet50"
}

class BOMScanner:
    """
    Scans a directory to generate a CycloneDX Bill of Materials (BOM)
    for Python projects, including dependencies and ML models.
    """
    
    def __init__(self, target_dir: str):
        self.target_dir = target_dir
        self.bom = Bom()

    def scan(self) -> str:
        """
        Orchestrates the scanning process and returns the BOM as a JSON string.
        """
        self._scan_requirements()
        self._scan_pyproject()
        self._scan_imports()
        self._scan_models()

        output = JsonV1Dot5(self.bom).output_as_string()
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
                self._add_component(dist_name, version, ComponentType.LIBRARY)

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
        """Scans pyproject.toml (PEP 621) if present."""
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

    def _add_component(
        self,
        name: str,
        version: Optional[str],
        type: ComponentType,
        description: Optional[str] = None,
        licenses: Optional[list] = None
    ) -> None:
        """Helper to add a component to the BOM."""
        from cyclonedx.model.license import DisjunctiveLicense

        component = Component(
            name=name,
            version=version,
            type=type,
            description=description
        )

        if licenses:
            for lic_name in licenses:
                component.licenses.add(DisjunctiveLicense(name=lic_name))
                
        self.bom.components.add(component)
