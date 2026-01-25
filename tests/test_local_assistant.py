import os
import tempfile
import json
import pytest
from unittest.mock import patch, MagicMock
from venturalitica.scanner import BOMScanner
from venturalitica.cli import app
from typer.testing import CliRunner

runner = CliRunner()

@pytest.fixture
def temp_project():
    """Creates a temporary directory with dummy project files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Create requirements.txt
        with open(os.path.join(tmpdirname, "requirements.txt"), "w") as f:
            f.write("requests==2.0.0\nnumpy>=1.20.0\n# comment\n")
            
        # Create pyproject.toml
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
        
        # Create a python file with model usage
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
    
    components = {c['name'] for c in bom['components']}
    assert "requests" in components
    assert "numpy" in components

def test_bom_scanner_pyproject(temp_project):
    scanner = BOMScanner(temp_project)
    output = scanner.scan()
    bom = json.loads(output)
    
    components = {c['name'] for c in bom['components']}
    assert "pandas" in components
    assert "scipy" in components
    assert "pytest" in components

def test_bom_scanner_models(temp_project):
    scanner = BOMScanner(temp_project)
    output = scanner.scan()
    bom = json.loads(output)
    
    components = {c['name']: c for c in bom['components'] if c['type'] == 'machine-learning-model'}
    assert "RandomForestClassifier" in components
    assert "LogisticRegression" in components

def test_cli_scan(temp_project):
    result = runner.invoke(app, ["scan", "--target", temp_project])
    assert result.exit_code == 0
    assert "BOM generated" in result.stdout
    assert os.path.exists(os.path.join(temp_project, "bom.json"))

def test_cli_scan_error():
    # Test error handling when target does not exist (or scanner fails)
    # Since BOMScanner doesn't raise on init, we mock scan to raise
    with patch('venturalitica.scanner.BOMScanner.scan', side_effect=Exception("Scan Error")):
        result = runner.invoke(app, ["scan", "--target", "."])
        assert "Error" in result.stdout

def test_cli_ui():
    with patch('subprocess.run') as mock_run:
        result = runner.invoke(app, ["ui"])
        assert result.exit_code == 0
        assert "Launching Venturalitica UI" in result.stdout
        mock_run.assert_called_once()

def test_cli_ui_error():
    with patch('subprocess.run', side_effect=Exception("Launch Error")):
        result = runner.invoke(app, ["ui"])
        # The updated code prints 'Failed to launch dashboard: <error>'
        assert "Failed to launch dashboard" in result.stdout
