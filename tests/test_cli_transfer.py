import json
import os
from unittest.mock import MagicMock, patch

import pytest
from click.exceptions import Exit as ClickExit

from venturalitica.cli.transfer import _create_bundle_payload, push

# ---------------------------------------------------------------------------
# Helper: set up a minimal project directory and return config dir
# ---------------------------------------------------------------------------


def _setup_project(
    tmp_path,
    results_data=None,
    traces=None,
    bom=None,
    annex_iv_lines=None,
    credentials=None,
    mlflow_run_id=None,
):
    """
    Prepare a temporary project tree under *tmp_path* and return the
    credentials directory path.
    """
    vent_dir = tmp_path / ".venturalitica"
    vent_dir.mkdir(parents=True, exist_ok=True)

    if results_data is not None:
        (vent_dir / "results.json").write_text(json.dumps(results_data))

    if traces:
        for name, content in traces.items():
            (vent_dir / name).write_text(json.dumps(content))

    if bom is not None:
        (vent_dir / "bom.json").write_text(json.dumps(bom))

    if annex_iv_lines is not None:
        (tmp_path / "Annex_IV.md").write_text("\n".join(annex_iv_lines))

    config_dir = tmp_path / ".venturalitica_config"
    config_dir.mkdir(parents=True, exist_ok=True)

    if credentials is not None:
        (config_dir / "credentials.json").write_text(json.dumps(credentials))

    return config_dir


# ===================================================================
# EXISTING TEST (preserved)
# ===================================================================


def test_transfer_bundle_payload(tmp_path):
    curr = os.getcwd()
    try:
        os.chdir(tmp_path)
        os.makedirs(".venturalitica", exist_ok=True)

        with open(".venturalitica/results.json", "w") as f:
            json.dump([{"passed": True, "metric_key": "accuracy"}], f)

        with open(".venturalitica/trace_123.json", "w") as f:
            json.dump({"bom": {"components": []}, "name": "Test Trace"}, f)

        config_dir = tmp_path / ".venturalitica_config"
        os.makedirs(config_dir, exist_ok=True)
        with patch(
            "venturalitica.cli.transfer.get_config_path",
            return_value=str(config_dir / "credentials.json"),
        ):
            with open(config_dir / "credentials.json", "w") as f:
                json.dump({"key": "test_key"}, f)

            payload = _create_bundle_payload()
            assert "bundle" in payload
            assert "metrics" in payload
            assert len(payload["metrics"]) == 1
    finally:
        os.chdir(curr)


# ===================================================================
# _create_bundle_payload – uncovered paths
# ===================================================================


class TestCreateBundlePayloadMissingResults:
    """results.json not found -> typer.Exit(1)."""

    def test_missing_results_json(self, tmp_path):
        curr = os.getcwd()
        try:
            os.chdir(tmp_path)
            os.makedirs(".venturalitica", exist_ok=True)
            # No results.json created
            with pytest.raises((SystemExit, ClickExit)):
                _create_bundle_payload()
        finally:
            os.chdir(curr)


class TestCreateBundlePayloadMLflow:
    """MLflow env detection (MLFLOW_RUN_ID set)."""

    def test_mlflow_env_detection(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MLFLOW_RUN_ID", "run-42")
        curr = os.getcwd()
        try:
            os.chdir(tmp_path)
            config_dir = _setup_project(
                tmp_path,
                results_data=[{"metric_key": "a"}],
                credentials={"key": "k"},
            )
            with patch(
                "venturalitica.cli.transfer.get_config_path",
                return_value=str(config_dir / "credentials.json"),
            ):
                payload = _create_bundle_payload()
            mlflow_arts = [
                a
                for a in payload["artifacts"]
                if a.get("metadata", {}).get("framework") == "mlflow"
            ]
            assert len(mlflow_arts) == 1
            assert "run-42" in mlflow_arts[0]["uri"]
        finally:
            os.chdir(curr)


class TestCreateBundlePayloadAnnexIV:
    """Annex IV parsing from file."""

    def test_annex_iv_parsing(self, tmp_path):
        curr = os.getcwd()
        try:
            os.chdir(tmp_path)
            config_dir = _setup_project(
                tmp_path,
                results_data=[],
                credentials={"key": "k"},
                annex_iv_lines=[
                    "# Annex IV",
                    "Intended Purpose: Credit scoring",
                    "Hardware: GPU server",
                ],
            )
            with patch(
                "venturalitica.cli.transfer.get_config_path",
                return_value=str(config_dir / "credentials.json"),
            ):
                payload = _create_bundle_payload()
            assert payload["bundle"]["annex_iv"]["intended_purpose"] == "Credit scoring"
            assert payload["bundle"]["annex_iv"]["hardware"] == "GPU server"
        finally:
            os.chdir(curr)


class TestCreateBundlePayloadDictResults:
    """Dict-shaped results with various key patterns."""

    def _run(self, tmp_path, results_data, credentials=None):
        curr = os.getcwd()
        try:
            os.chdir(tmp_path)
            config_dir = _setup_project(
                tmp_path,
                results_data=results_data,
                credentials=credentials or {"key": "k"},
            )
            with patch(
                "venturalitica.cli.transfer.get_config_path",
                return_value=str(config_dir / "credentials.json"),
            ):
                return _create_bundle_payload()
        finally:
            os.chdir(curr)

    def test_metrics_key(self, tmp_path):
        payload = self._run(tmp_path, {"metrics": [{"m": 1}]})
        assert payload["metrics"] == [{"m": 1}]

    def test_pre_post_metrics(self, tmp_path):
        payload = self._run(
            tmp_path,
            {
                "pre_metrics": [{"m": "pre"}],
                "post_metrics": [{"m": "post"}],
            },
        )
        assert {"m": "pre"} in payload["metrics"]
        assert {"m": "post"} in payload["metrics"]

    def test_artifacts_key(self, tmp_path):
        payload = self._run(
            tmp_path,
            {
                "metrics": [],
                "artifacts": [{"name": "model.pkl", "type": "MODEL"}],
            },
        )
        assert any(a["name"] == "model.pkl" for a in payload["artifacts"])


class TestCreateBundlePayloadTraces:
    """Trace auto-discovery, BOM from trace, mtime fallback."""

    def test_trace_with_bom_and_timestamp(self, tmp_path):
        curr = os.getcwd()
        try:
            os.chdir(tmp_path)
            config_dir = _setup_project(
                tmp_path,
                results_data=[],
                credentials={"key": "k"},
                traces={
                    "trace_old.json": {
                        "timestamp_unix": 100,
                        "bom": {"old": True},
                        "label": "Old Trace",
                    },
                    "trace_new.json": {
                        "timestamp_unix": 999,
                        "bom": {"new": True},
                        "name": "New Trace",
                    },
                },
            )
            with patch(
                "venturalitica.cli.transfer.get_config_path",
                return_value=str(config_dir / "credentials.json"),
            ):
                payload = _create_bundle_payload()
            # BOM should come from the most recent trace (timestamp_unix=999)
            assert payload["bom"] == {"new": True}
            # Both traces should appear as artifacts
            trace_names = [a["name"] for a in payload["artifacts"]]
            assert "Old Trace" in trace_names
            assert "New Trace" in trace_names
        finally:
            os.chdir(curr)

    def test_trace_without_timestamp_mtime_fallback(self, tmp_path):
        """When trace has no timestamp_unix, file mtime is used."""
        curr = os.getcwd()
        try:
            os.chdir(tmp_path)
            config_dir = _setup_project(
                tmp_path,
                results_data=[],
                credentials={"key": "k"},
                traces={
                    "trace_a.json": {"bom": {"a": True}, "name": "A"},
                },
            )
            with patch(
                "venturalitica.cli.transfer.get_config_path",
                return_value=str(config_dir / "credentials.json"),
            ):
                payload = _create_bundle_payload()
            # BOM should be picked up despite no timestamp_unix
            assert payload["bom"] == {"a": True}
        finally:
            os.chdir(curr)

    def test_trace_invalid_json_skipped(self, tmp_path):
        """Malformed trace files are silently skipped."""
        curr = os.getcwd()
        try:
            os.chdir(tmp_path)
            vent_dir = tmp_path / ".venturalitica"
            vent_dir.mkdir(parents=True, exist_ok=True)
            (vent_dir / "results.json").write_text("[]")
            (vent_dir / "trace_bad.json").write_text("NOT-JSON!!!")
            config_dir = _setup_project(
                tmp_path,
                credentials={"key": "k"},
            )
            with patch(
                "venturalitica.cli.transfer.get_config_path",
                return_value=str(config_dir / "credentials.json"),
            ):
                payload = _create_bundle_payload()
            # Should succeed; bad trace is skipped
            assert payload["bom"] == {}
        finally:
            os.chdir(curr)


class TestCreateBundlePayloadBOMFallback:
    """BOM fallback to bom.json when traces have no BOM."""

    def test_bom_json_fallback(self, tmp_path):
        curr = os.getcwd()
        try:
            os.chdir(tmp_path)
            config_dir = _setup_project(
                tmp_path,
                results_data=[],
                credentials={"key": "k"},
                bom={"fallback": True},
                traces={"trace_no_bom.json": {"name": "NoBom"}},
            )
            with patch(
                "venturalitica.cli.transfer.get_config_path",
                return_value=str(config_dir / "credentials.json"),
            ):
                payload = _create_bundle_payload()
            assert payload["bom"] == {"fallback": True}
        finally:
            os.chdir(curr)


class TestCreateBundlePayloadHMAC:
    """HMAC signing with credentials and without."""

    def test_hmac_with_credentials(self, tmp_path):
        curr = os.getcwd()
        try:
            os.chdir(tmp_path)
            config_dir = _setup_project(
                tmp_path,
                results_data=[],
                credentials={"key": "my-secret"},
            )
            with patch(
                "venturalitica.cli.transfer.get_config_path",
                return_value=str(config_dir / "credentials.json"),
            ):
                payload = _create_bundle_payload()
            assert payload["bundle"]["signature"]
            assert payload["bundle"]["signature_type"] == "HMAC-SHA256"
        finally:
            os.chdir(curr)

    def test_hmac_without_credentials(self, tmp_path):
        """Default key used when credentials file does not exist."""
        curr = os.getcwd()
        try:
            os.chdir(tmp_path)
            _setup_project(tmp_path, results_data=[])
            # Point to a path that does NOT exist
            fake_creds = str(tmp_path / "nonexistent" / "credentials.json")
            with patch(
                "venturalitica.cli.transfer.get_config_path", return_value=fake_creds
            ):
                payload = _create_bundle_payload()
            assert payload["bundle"]["signature"]
            assert payload["bundle"]["signature_type"] == "HMAC-SHA256"
        finally:
            os.chdir(curr)

    def test_hmac_with_corrupt_credentials(self, tmp_path):
        """Corrupt credentials file falls back to default key."""
        curr = os.getcwd()
        try:
            os.chdir(tmp_path)
            config_dir = _setup_project(tmp_path, results_data=[])
            creds_path = config_dir / "credentials.json"
            creds_path.write_text("NOT-JSON")
            with patch(
                "venturalitica.cli.transfer.get_config_path",
                return_value=str(creds_path),
            ):
                payload = _create_bundle_payload()
            assert payload["bundle"]["signature"]
        finally:
            os.chdir(curr)


# ===================================================================
# push – uncovered paths
# ===================================================================


class TestPushNotLoggedIn:
    """push: not logged in (no credentials file)."""

    def test_push_not_logged_in(self, tmp_path):
        fake_creds = str(tmp_path / "nonexistent" / "credentials.json")
        with patch(
            "venturalitica.cli.transfer.get_config_path", return_value=fake_creds
        ):
            with pytest.raises((SystemExit, ClickExit)):
                push(external_run_url=None, treatment_id=None)


class TestPushSuccess:
    """push: successful HTTP round-trip."""

    def test_push_success(self, tmp_path):
        curr = os.getcwd()
        try:
            os.chdir(tmp_path)
            config_dir = _setup_project(
                tmp_path,
                results_data=[{"m": 1}],
                credentials={"key": "bearer-token"},
            )
            mock_resp = MagicMock()
            mock_resp.raise_for_status = MagicMock()
            mock_resp.json.return_value = {"job_id": "j-1"}

            with (
                patch(
                    "venturalitica.cli.transfer.get_config_path",
                    return_value=str(config_dir / "credentials.json"),
                ),
                patch(
                    "venturalitica.cli.transfer.requests.post", return_value=mock_resp
                ) as mock_post,
            ):
                push(external_run_url=None, treatment_id=None)

            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args
            assert "Bearer bearer-token" in str(call_kwargs)
        finally:
            os.chdir(curr)

    def test_push_with_external_run_url_and_treatment_id(self, tmp_path):
        curr = os.getcwd()
        try:
            os.chdir(tmp_path)
            config_dir = _setup_project(
                tmp_path,
                results_data=[],
                credentials={"key": "k"},
            )
            mock_resp = MagicMock()
            mock_resp.raise_for_status = MagicMock()
            mock_resp.json.return_value = {"audit_trace_id": "at-1"}

            with (
                patch(
                    "venturalitica.cli.transfer.get_config_path",
                    return_value=str(config_dir / "credentials.json"),
                ),
                patch(
                    "venturalitica.cli.transfer.requests.post", return_value=mock_resp
                ) as mock_post,
            ):
                push(
                    external_run_url="https://mlflow.example/run/1", treatment_id="t-42"
                )

            sent_json = mock_post.call_args[1]["json"]
            assert sent_json["external_run_url"] == "https://mlflow.example/run/1"
            assert sent_json["treatment_id"] == "t-42"
        finally:
            os.chdir(curr)


class TestPushFailure:
    """push: error response paths."""

    def test_push_failure_json_error(self, tmp_path):
        """Server returns an error with JSON body."""
        curr = os.getcwd()
        try:
            os.chdir(tmp_path)
            config_dir = _setup_project(
                tmp_path,
                results_data=[],
                credentials={"key": "k"},
            )
            error_resp = MagicMock()
            error_resp.json.return_value = {"error": "quota exceeded"}
            error_resp.text = '{"error":"quota exceeded"}'
            error_resp.status_code = 429

            exc = Exception("429 Too Many Requests")
            exc.response = error_resp

            with (
                patch(
                    "venturalitica.cli.transfer.get_config_path",
                    return_value=str(config_dir / "credentials.json"),
                ),
                patch("venturalitica.cli.transfer.requests.post", side_effect=exc),
            ):
                with pytest.raises((SystemExit, ClickExit)):
                    push(external_run_url=None, treatment_id=None)
        finally:
            os.chdir(curr)

    def test_push_failure_non_json_error(self, tmp_path):
        """Server returns an error with non-JSON body."""
        curr = os.getcwd()
        try:
            os.chdir(tmp_path)
            config_dir = _setup_project(
                tmp_path,
                results_data=[],
                credentials={"key": "k"},
            )
            error_resp = MagicMock()
            error_resp.json.side_effect = ValueError("No JSON")
            error_resp.text = "Internal Server Error"
            error_resp.status_code = 500

            exc = Exception("500 Server Error")
            exc.response = error_resp

            with (
                patch(
                    "venturalitica.cli.transfer.get_config_path",
                    return_value=str(config_dir / "credentials.json"),
                ),
                patch("venturalitica.cli.transfer.requests.post", side_effect=exc),
            ):
                with pytest.raises((SystemExit, ClickExit)):
                    push(external_run_url=None, treatment_id=None)
        finally:
            os.chdir(curr)
