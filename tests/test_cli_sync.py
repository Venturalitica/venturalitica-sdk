"""CLI sync tests.

The SaaS returns a canonical NIST OSCAL v1.2.2 `component-definition`
document on `/api/pull?format=oscal`.
"""
from __future__ import annotations

from typing import Optional
from unittest.mock import MagicMock, patch

import pytest
import typer

from venturalitica.cli.sync import pull


def _requirement(uuid: str, *, target_type: str = "system", risk_id: Optional[str] = None):
    props = [
        {"name": "metric_key", "value": "demographic_parity_diff"},
        {"name": "operator", "value": "<"},
        {"name": "threshold", "value": "0.1"},
        {"name": "severity", "value": "block"},
        {"name": "enforcement_mode", "value": "gate"},
        {"name": "evaluation_method", "value": "automated"},
        {"name": "target_type", "value": target_type},
        {"name": "lifecycle_phase", "value": "production"},
    ]
    if risk_id:
        props.append({"name": "risk_id", "value": risk_id})
    return {
        "uuid": uuid,
        "control-id": "A.6.2.4",
        "description": f"Synthetic requirement {uuid}",
        "props": props,
    }


def _make_oscal(requirements):
    return {
        "component-definition": {
            "uuid": "145d61f3-b2d4-51ec-998a-dec9d24c6ab2",
            "metadata": {
                "title": "Test Policy",
                "last-modified": "2026-05-16T10:00:00.000Z",
                "version": "1",
                "oscal-version": "1.2.2",
            },
            "components": [
                {
                    "uuid": "18f5d663-07b9-5ef4-9197-41f0195eee10",
                    "type": "software",
                    "title": "Test System v1.0",
                    "description": "Test component",
                    "control-implementations": [
                        {
                            "uuid": "7f0641a9-923a-5957-b835-4a5d5272a3b0",
                            "source": "#vl-ai-assurance-profile-2026",
                            "description": "Test control-implementations",
                            "implemented-requirements": requirements,
                        }
                    ],
                }
            ],
        }
    }


def _make_config():
    return {
        "policy": {"name": "Test Policy"},
        "objectives": [],
        "aiSystemVersion": {"name": "Test", "version": "1.0"},
    }


def _run_pull_with_requirements(requirements):
    """Helper: run pull() with mocked OSCAL containing given requirements."""
    mock_creds = {"key": "test-key"}
    oscal_data = _make_oscal(requirements)
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


def test_sync_pull_command_basic():
    # 1. Test no login
    with patch("os.path.exists", return_value=False):
        with pytest.raises(typer.Exit):
            pull()

    # 2. Test successful pull with empty plan
    _run_pull_with_requirements([])


def test_risk_bound_in_model_policy():
    """Requirement targeting the system (model) carries a risk_id prop."""
    reqs = [_requirement("req-001", target_type="system", risk_id="risk-001")]
    _run_pull_with_requirements(reqs)


def test_risk_bound_in_data_policy():
    """Requirement targeting the dataset carries a risk_id prop."""
    reqs = [_requirement("req-002", target_type="dataset", risk_id="risk-002")]
    _run_pull_with_requirements(reqs)


def test_risk_unbound():
    """Requirement without a risk_id prop is still emitted."""
    reqs = [_requirement("req-999", target_type="system")]
    _run_pull_with_requirements(reqs)


def test_multiple_risks_mixed_binding():
    """Multiple requirements: bound system + unbound dataset."""
    reqs = [
        _requirement("req-1", target_type="system", risk_id="r1"),
        _requirement("req-2", target_type="dataset"),
    ]
    _run_pull_with_requirements(reqs)


def test_pull_network_error_exits():
    """Exception during pull raises typer.Exit."""
    mock_creds = {"key": "test-key"}
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", MagicMock()):
            with patch("json.load", return_value=mock_creds):
                with patch("requests.get", side_effect=Exception("Connection refused")):
                    with pytest.raises(typer.Exit):
                        pull()
