import json
import os
import tempfile

import pytest

from venturalitica.scanner import BOMScanner


def test_scanner_with_requirements(tmp_path):
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("pandas==2.1.0\nnumpy>=1.24\n# comment\n")

    scanner = BOMScanner(str(tmp_path))
    scanner._scan_requirements()

    components = {c.name: c.version for c in scanner.bom.components}
    assert "pandas" in components
    assert components["pandas"] == "2.1.0"
    assert "numpy" in components
    assert components["numpy"] == "1.24"


def test_scanner_with_pyproject(tmp_path):
    # Note: Using standard toml content
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("""
[project]
name = "test-project"
dependencies = [
    "requests==2.31.0",
    "scikit-learn>=1.3"
]
""")

    scanner = BOMScanner(str(tmp_path))
    scanner._scan_pyproject()

    names = [c.name for c in scanner.bom.components]
    assert "requests" in names
    assert "scikit-learn" in names


def test_scanner_with_models(tmp_path):
    code_file = tmp_path / "train.py"
    code_file.write_text(
        "from sklearn.ensemble import RandomForestClassifier\nmodel = RandomForestClassifier()\n"
    )

    scanner = BOMScanner(str(tmp_path))
    scanner._scan_models()

    names = [c.name for c in scanner.bom.components]
    assert "RandomForestClassifier" in names


def test_scanner_full_scan(tmp_path):
    (tmp_path / "requirements.txt").write_text("pandas==2.1.0")
    (tmp_path / "train.py").write_text("m = LogisticRegression()")

    scanner = BOMScanner(str(tmp_path))
    json_output = scanner.scan()

    assert "pandas" in json_output
    assert "LogisticRegression" in json_output


def test_scanner_with_pyproject_error(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("invalid = toml = format")

    scanner = BOMScanner(str(tmp_path))
    # Should not raise, just return early from _scan_pyproject
    scanner._scan_pyproject()
    assert len(scanner.bom.components) == 0


def test_scanner_with_syntax_error(tmp_path):
    code_file = tmp_path / "bad.py"
    code_file.write_text("invalid syntax (")

    scanner = BOMScanner(str(tmp_path))
    # Should not raise, just skip the file
    scanner._scan_models()
    assert len(scanner.bom.components) == 0


# --- Merged from test_local_assistant.py ---


@pytest.fixture
def temp_project():
    """Creates a temporary directory with dummy project files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        with open(os.path.join(tmpdirname, "requirements.txt"), "w") as f:
            f.write("requests==2.0.0\nnumpy>=1.20.0\n# comment\n")

        with open(os.path.join(tmpdirname, "pyproject.toml"), "w") as f:
            f.write("""
[project]
dependencies = [
    "pandas>=1.0.0",
    "scipy[extra]==1.5.0"
]
[project.optional-dependencies]
dev = ["pytest"]
""")

        with open(os.path.join(tmpdirname, "model.py"), "w") as f:
            f.write("""
import sklearn.ensemble
from sklearn.linear_model import LogisticRegression

clf = sklearn.ensemble.RandomForestClassifier()
lr = LogisticRegression()
""")
        yield tmpdirname


def test_bom_scanner_requirements(temp_project):
    scanner = BOMScanner(temp_project)
    output = scanner.scan()
    bom = json.loads(output)

    components = {c["name"] for c in bom["components"]}
    assert "requests" in components
    assert "numpy" in components


def test_bom_scanner_pyproject(temp_project):
    scanner = BOMScanner(temp_project)
    output = scanner.scan()
    bom = json.loads(output)

    components = {c["name"] for c in bom["components"]}
    assert "pandas" in components
    assert "scipy" in components
    assert "pytest" in components


def test_bom_scanner_models(temp_project):
    scanner = BOMScanner(temp_project)
    output = scanner.scan()
    bom = json.loads(output)

    components = {
        c["name"]: c for c in bom["components"] if c["type"] == "machine-learning-model"
    }
    assert "RandomForestClassifier" in components
    assert "LogisticRegression" in components
