from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component, ComponentType
from cyclonedx.output.json import JsonV1Dot5
import os
import ast
from typing import Optional, Set

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
        self._scan_models()
        
        output = JsonV1Dot5(self.bom).output_as_string()
        return output

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
        except (ImportError, Exception) as e:
            # Fallback or error handling
            return

        # Standard PEP 621 dependencies
        project = data.get("project", {})
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
        for root, _, files in os.walk(self.target_dir):
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
        description: Optional[str] = None
    ) -> None:
        """Helper to add a component to the BOM."""
        component = Component(
            name=name,
            version=version,
            type=type,
            description=description
        )
        self.bom.components.add(component)
