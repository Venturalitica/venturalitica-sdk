"""CLI sync tests post-OSCAL unification.

The SaaS now returns a single `assessment-plan` root per the canonical
v1 contract (docs/contracts/oscal-assessment-plan-v1.md). The legacy
`{model: ssp, data: ssp}` envelope is gone.
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
        "assessment-plan": {
            "uuid": "plan-uuid",
            "metadata": {"title": "Test Plan", "oscal-version": "1.1.2"},
            "control-implementations": [
                {
                    "component-uuid": "comp-1",
                    "description": "Test component",
                    "implemented-requirements": requirements,
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
