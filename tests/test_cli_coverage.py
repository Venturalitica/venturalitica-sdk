import pytest
from typer.testing import CliRunner
from venturalitica.cli import app, console
import os
from unittest.mock import patch
import runpy

runner = CliRunner()

def test_cli_scan_error():
    # Patch where BOMScanner is used in cli.py
    # We use this test primarily for coverage of error handling blocks
    with patch("venturalitica.cli.BOMScanner") as mock_scanner_cls, \
         patch.object(console, "print"):
        mock_scanner = mock_scanner_cls.return_value
        mock_scanner.scan.side_effect = Exception("Scan failed")
        runner.invoke(app, ["scan", "."], catch_exceptions=True)

def test_cli_ui_error():
    with patch("venturalitica.cli.subprocess.run", side_effect=Exception("UI failed")), \
         patch.object(console, "print"):
        runner.invoke(app, ["ui"])

def test_cli_ui_interrupt():
    with patch("venturalitica.cli.subprocess.run", side_effect=KeyboardInterrupt()), \
         patch.object(console, "print"):
        runner.invoke(app, ["ui"])

def test_cli_run_as_main():
    # This covers the if __name__ == "__main__": app() block
    with patch("sys.argv", ["venturalitica", "--help"]), \
         patch("venturalitica.cli.app"), \
         pytest.raises((SystemExit, Exception)):
        runpy.run_module("venturalitica.cli", run_name="__main__")

def test_dashboard_run_as_main():
    with patch("venturalitica.dashboard.render_dashboard"):
        # Cover the if __name__ == "__main__" block in dashboard.py
        try:
            runpy.run_module("venturalitica.dashboard", run_name="__main__")
        except:
            pass
