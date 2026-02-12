import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from venturalitica.cli import app

runner = CliRunner()


def test_cli_ui_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "ui" in result.stdout
    assert "scan" not in result.stdout


def test_cli_ui_keyboard_interrupt():
    with patch("subprocess.run", side_effect=KeyboardInterrupt):
        result = runner.invoke(app, ["ui"])
    assert "Dashboard stopped" in result.stdout


def test_cli_ui_exception():
    with patch("subprocess.run", side_effect=Exception("Launch fail")):
        result = runner.invoke(app, ["ui"])
    assert "Failed to launch dashboard: Launch fail" in result.stdout


# --- Merged from test_local_assistant.py ---


def test_cli_ui_launch():
    """Test CLI ui command calls subprocess.run with streamlit."""
    with patch("subprocess.run") as mock_run:
        result = runner.invoke(app, ["ui"])
        assert result.exit_code == 0
        assert "Launching Venturalítica UI" in result.stdout
        # subprocess.run may be called multiple times (e.g. by telemetry),
        # so we check the streamlit call is among them.
        streamlit_calls = [c for c in mock_run.call_args_list if "streamlit" in str(c)]
        assert len(streamlit_calls) >= 1


def test_cli_ui_error_message():
    """Test CLI ui command displays error on failure."""
    with patch("subprocess.run", side_effect=Exception("Launch Error")):
        result = runner.invoke(app, ["ui"])
        assert "Failed to launch dashboard" in result.stdout


# ===================================================================
# CLI auth: login command
# ===================================================================


class TestCliLogin:
    """Tests for the `login` CLI command (auth.py)."""

    def test_login_success(self, tmp_path):
        """Successful login stores credentials."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "key": "sk-test-123",
            "aiSystemName": "TestSystem",
        }

        creds_path = str(tmp_path / "credentials.json")

        with (
            patch(
                "venturalitica.cli.auth.requests.post", return_value=mock_resp
            ) as mock_post,
            patch("venturalitica.cli.auth.get_config_path", return_value=creds_path),
        ):
            result = runner.invoke(app, ["login", "sys-abc"])

        assert result.exit_code == 0
        assert "Login successful" in result.stdout
        assert "TestSystem" in result.stdout

        # Verify credentials were written
        with open(creds_path) as f:
            saved = json.load(f)
        assert saved["key"] == "sk-test-123"

        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["json"] == {"aiSystemId": "sys-abc"}

    def test_login_failure_http_error(self):
        """Login failure (HTTP error) prints error and exits with code 1."""
        with patch(
            "venturalitica.cli.auth.requests.post",
            side_effect=Exception("Connection refused"),
        ):
            result = runner.invoke(app, ["login", "sys-abc"])

        assert result.exit_code == 1
        assert "Login failed" in result.stdout
