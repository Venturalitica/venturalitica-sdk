from unittest.mock import MagicMock, patch

import pytest
import typer

from venturalitica.cli.sync import pull


def test_sync_pull_command_basic():
    # 1. Test no login
    with patch("os.path.exists", return_value=False):
        with pytest.raises(typer.Exit):
            pull()

    # 2. Test successful pull
    mock_creds = {"key": "test-key"}
    mock_oscal = {
        "model": {
            "system-security-plan": {
                "control-implementation": {"implemented-requirements": []}
            }
        },
        "data": {
            "system-security-plan": {
                "control-implementation": {"implemented-requirements": []}
            }
        },
        "risks": [],
    }
    mock_config = {
        "aiSystemVersion": {"name": "Test System"},
        "policy": {"name": "Test Policy"},
        "objectives": [],
    }

    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", MagicMock()):
            with patch("json.load", return_value=mock_creds):
                with patch("requests.get") as mock_get:
                    # Mock two calls (one for oscal, one for config)
                    m1 = MagicMock()
                    m1.json.return_value = mock_oscal
                    m1.status_code = 200

                    m2 = MagicMock()
                    m2.json.return_value = mock_config
                    m2.status_code = 200

                    mock_get.side_effect = [m1, m2]

                    with patch("yaml.dump"):
                        with patch("json.dump"):
                            with patch("os.makedirs"):
                                pull()
                                assert mock_get.call_count == 2


# ── Risk binding output (lines 55-63) ──────────────────────────────────────


def _make_oscal(risks, model_reqs=None, data_reqs=None):
    return {
        "model": {
            "system-security-plan": {
                "control-implementation": {"implemented-requirements": model_reqs or []}
            }
        },
        "data": {
            "system-security-plan": {
                "control-implementation": {"implemented-requirements": data_reqs or []}
            }
        },
        "risks": risks,
    }


def _make_config():
    return {
        "policy": {"name": "Test Policy"},
        "objectives": [],
        "aiSystemVersion": {"name": "Test", "version": "1.0"},
    }


def _run_pull_with_risks(risks, model_reqs=None, data_reqs=None):
    """Helper: run pull() with mocked OSCAL containing given risks."""
    mock_creds = {"key": "test-key"}
    oscal_data = _make_oscal(risks, model_reqs, data_reqs)
    config_data = _make_config()

    m1 = MagicMock()
    m1.json.return_value = oscal_data
    m1.status_code = 200

    m2 = MagicMock()
    m2.json.return_value = config_data
    m2.status_code = 200

    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", MagicMock()):
            with patch("json.load", return_value=mock_creds):
                with patch("requests.get", side_effect=[m1, m2]):
                    with patch("yaml.dump"):
                        with patch("json.dump"):
                            with patch("os.makedirs"):
                                pull()


def test_risk_bound_in_model_policy():
    """Lines 57-61: risk UUID matches model policy requirement."""
    risks = [{"uuid": "risk-001", "title": "Data Bias"}]
    model_reqs = [{"legacy-id": "risk-001"}]
    _run_pull_with_risks(risks, model_reqs=model_reqs)


def test_risk_bound_in_data_policy():
    """Lines 57-61: risk UUID matches data policy requirement."""
    risks = [{"uuid": "risk-002", "title": "Privacy Leak"}]
    data_reqs = [{"legacy-id": "risk-002"}]
    _run_pull_with_risks(risks, data_reqs=data_reqs)


def test_risk_unbound():
    """Lines 62-63: risk UUID not in any policy."""
    risks = [{"uuid": "risk-999", "title": "Unknown Risk"}]
    _run_pull_with_risks(risks)


def test_multiple_risks_mixed_binding():
    """Multiple risks: some bound, some unbound."""
    risks = [
        {"uuid": "r1", "title": "Bound Risk"},
        {"uuid": "r2", "title": "Unbound Risk"},
    ]
    model_reqs = [{"legacy-id": "r1"}]
    _run_pull_with_risks(risks, model_reqs=model_reqs)


# ── Error handler (lines 111-113) ──────────────────────────────────────────


def test_pull_network_error_exits():
    """Lines 111-113: exception during pull raises typer.Exit."""
    mock_creds = {"key": "test-key"}
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", MagicMock()):
            with patch("json.load", return_value=mock_creds):
                with patch("requests.get", side_effect=Exception("Connection refused")):
                    with pytest.raises(typer.Exit):
                        pull()
