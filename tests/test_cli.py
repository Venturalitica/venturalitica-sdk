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


def _patch_streamlit_available(mp_ctx):
    """Bypass the `vl ui` preflight that requires streamlit to be importable
    so the CLI tests can exercise the launch path even when the optional
    [dashboard] extra isn't installed in the test venv."""
    return mp_ctx(
        "venturalitica.cli.dashboard.importlib.util.find_spec",
        return_value=MagicMock(),
    )


def test_cli_ui_keyboard_interrupt():
    # Patch narrowly on the dashboard module to avoid intercepting subprocess
    # calls from unrelated init code (e.g. `distro` inside telemetry).
    with _patch_streamlit_available(patch), patch(
        "venturalitica.cli.dashboard.subprocess.run", side_effect=KeyboardInterrupt
    ):
        result = runner.invoke(app, ["ui"])
    assert "Dashboard stopped" in result.stdout


def test_cli_ui_exception():
    with _patch_streamlit_available(patch), patch(
        "venturalitica.cli.dashboard.subprocess.run", side_effect=Exception("Launch fail")
    ):
        result = runner.invoke(app, ["ui"])
    assert "Failed to launch dashboard" in result.stdout
    assert "Launch fail" in result.stdout


# --- Merged from test_local_assistant.py ---


def test_cli_ui_launch():
    """Test CLI ui command invokes `<python> -m streamlit run <dashboard>`."""
    with _patch_streamlit_available(patch), patch(
        "venturalitica.cli.dashboard.subprocess.run"
    ) as mock_run:
        result = runner.invoke(app, ["ui"])
        assert "Launching Venturalítica UI" in result.stdout
        # subprocess.run is also called by telemetry helpers (distro lookup);
        # what matters is that at least one of the calls launches streamlit
        # with the new --server.port / --server.address args.
        streamlit_calls = [
            c for c in mock_run.call_args_list
            if c.args and isinstance(c.args[0], list) and "streamlit" in c.args[0]
        ]
        assert len(streamlit_calls) == 1, f"expected one streamlit launch, got {streamlit_calls}"
        cmd = streamlit_calls[0].args[0]
        assert "run" in cmd
        assert "--server.port" in cmd
        assert "--server.address" in cmd


def test_cli_ui_error_message():
    """Test CLI ui command displays error on failure."""
    with _patch_streamlit_available(patch), patch(
        "venturalitica.cli.dashboard.subprocess.run", side_effect=Exception("Launch Error")
    ):
        result = runner.invoke(app, ["ui"])
        assert "Failed to launch dashboard" in result.stdout


def test_cli_ui_missing_dashboard_extra_emits_install_guidance():
    """When streamlit isn't installed, `vl ui` must print the
    `pip install 'venturalitica[dashboard]'` guidance and exit non-zero —
    rather than letting subprocess.run blow up with an opaque
    FileNotFoundError for the missing `streamlit` binary."""
    with patch(
        "venturalitica.cli.dashboard.importlib.util.find_spec",
        return_value=None,
    ):
        result = runner.invoke(app, ["ui"])
    assert result.exit_code == 1
    assert "Dashboard dependency missing" in result.stdout
    assert "venturalitica[dashboard]" in result.stdout


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

    def test_login_pat_stores_canonical_payload(self, tmp_path):
        """`vl login-pat --key vl_pat_… --org X --system Y` writes a JSON
        payload that downstream push/pull readers expect."""
        creds_path = str(tmp_path / "credentials.json")
        with patch("venturalitica.cli.auth.get_config_path", return_value=creds_path):
            result = runner.invoke(
                app,
                [
                    "login-pat",
                    "--key", "vl_pat_synthetic-abc123",
                    "--org", "venturalitica",
                    "--system", "spineguard-ai",
                ],
            )
        assert result.exit_code == 0
        assert "PAT stored" in result.stdout
        with open(creds_path) as f:
            saved = json.load(f)
        assert saved["key"] == "vl_pat_synthetic-abc123"
        assert saved["kind"] == "pat"
        assert saved["org"] == "venturalitica"
        # Stored under both keys so existing readers (sync.py default fallback)
        # and human-friendly inspection both work.
        assert saved["system"] == "spineguard-ai"
        assert saved["default_system"] == "spineguard-ai"

    def test_login_pat_without_system_omits_default_system(self, tmp_path):
        """When `--system` is omitted, the SaaS auto-derives target from
        token scopes — we shouldn't stamp a placeholder client-side."""
        creds_path = str(tmp_path / "credentials.json")
        with patch("venturalitica.cli.auth.get_config_path", return_value=creds_path):
            result = runner.invoke(
                app, ["login-pat", "--key", "vl_pat_only-key", "--org", "venturalitica"]
            )
        assert result.exit_code == 0
        with open(creds_path) as f:
            saved = json.load(f)
        assert "system" not in saved
        assert "default_system" not in saved

    def test_login_pat_without_org_or_system_still_stores_key(self, tmp_path):
        creds_path = str(tmp_path / "credentials.json")
        with patch("venturalitica.cli.auth.get_config_path", return_value=creds_path):
            result = runner.invoke(app, ["login-pat", "--key", "vl_pat_bare"])
        assert result.exit_code == 0
        with open(creds_path) as f:
            saved = json.load(f)
        assert saved == {"key": "vl_pat_bare", "kind": "pat"}

    def test_login_pat_rejects_invalid_token_prefix(self, tmp_path):
        """A PAT that doesn't start with `vl_pat_` is a typo — fail fast
        before writing anything to disk."""
        creds_path = str(tmp_path / "credentials.json")
        with patch("venturalitica.cli.auth.get_config_path", return_value=creds_path):
            result = runner.invoke(app, ["login-pat", "--key", "sk-not-a-pat"])
        assert result.exit_code == 1
        assert "Invalid PAT format" in result.stdout
        # No file should have been written.
        import os as _os
        assert not _os.path.exists(creds_path)

    def test_login_failure_http_error(self):
        """Login failure (HTTP error) prints error and exits with code 1."""
        with patch(
            "venturalitica.cli.auth.requests.post",
            side_effect=Exception("Connection refused"),
        ):
            result = runner.invoke(app, ["login", "sys-abc"])

        assert result.exit_code == 1
        assert "Login failed" in result.stdout
