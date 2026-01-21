import os
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
    code_file.write_text("from sklearn.ensemble import RandomForestClassifier\nmodel = RandomForestClassifier()\n")
    
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
