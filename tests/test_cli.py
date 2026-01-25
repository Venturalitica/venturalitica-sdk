from typer.testing import CliRunner
from venturalitica.cli import app
import os
from unittest.mock import patch, MagicMock
import subprocess

runner = CliRunner()

def test_cli_scan(tmp_path):
    # Create a dummy requirements.txt
    (tmp_path / "requirements.txt").write_text("pandas==2.1.0")
    
    # Run scan command
    result = runner.invoke(app, ["scan", "--target", str(tmp_path)])
    
    assert result.exit_code == 0
    assert "BOM generated" in result.stdout
    assert os.path.exists(tmp_path / "bom.json")

def test_cli_scan_error():
    with patch("venturalitica.scanner.BOMScanner.scan", side_effect=Exception("Scan fail")):
        result = runner.invoke(app, ["scan", "--target", "."])
    assert "Error: Scan fail" in result.stdout

def test_cli_ui_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "ui" in result.stdout
    assert "scan" in result.stdout

def test_cli_ui_keyboard_interrupt():
    with patch("subprocess.run", side_effect=KeyboardInterrupt):
        result = runner.invoke(app, ["ui"])
    assert "Dashboard stopped" in result.stdout

def test_cli_ui_exception():
    with patch("subprocess.run", side_effect=Exception("Launch fail")):
        result = runner.invoke(app, ["ui"])
    assert "Failed to launch dashboard: Launch fail" in result.stdout
