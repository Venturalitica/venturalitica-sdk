"""Verify VENTURALITICA_STRICT / CI gating semantics for the public API.

Migrated from the ad-hoc verify_strict_mode.py script. Exercises the
env-driven strict path (CI=true / VENTURALITICA_STRICT=true) with a
policy that references a metric_key the registry does not implement.
"""
from __future__ import annotations

import os
import tempfile

import pandas as pd
import pytest
import yaml

from venturalitica.api import enforce


def _missing_metric_policy() -> dict:
    return {
        "assessment-plan": {
            "local-definitions": {
                "inventory-items": [
                    {
                        "uuid": "x1",
                        "props": [
                            {"name": "metric_key", "value": "nonexistent_metric"},
                            {"name": "threshold", "value": "0.5"},
                            {"name": "operator", "value": "gt"},
                            {"name": "input:target", "value": "target"},
                        ],
                    }
                ]
            },
            "control-implementations": [
                {
                    "implemented-requirements": [
                        {
                            "control-id": "MISS-1",
                            "description": "Control whose metric is not registered",
                            "links": [{"href": "#x1", "rel": "related"}],
                        }
                    ]
                }
            ],
        }
    }


@pytest.fixture
def policy_path():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".oscal.yaml", delete=False
    ) as f:
        yaml.dump(_missing_metric_policy(), f)
        path = f.name
    yield path
    os.unlink(path)


def test_strict_mode_via_ci_env_raises_on_missing_metric(policy_path, monkeypatch):
    """CI=true should activate strict mode and raise on unknown metric."""
    monkeypatch.setenv("CI", "true")
    monkeypatch.delenv("VENTURALITICA_STRICT", raising=False)

    df = pd.DataFrame({"target": [0, 1]})
    with pytest.raises(ValueError, match="No metric function registered"):
        enforce(data=df, policy=policy_path, target="target", strict=True)


def test_strict_mode_via_explicit_env_raises(policy_path, monkeypatch):
    """VENTURALITICA_STRICT=true should activate strict mode."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("VENTURALITICA_STRICT", "true")

    df = pd.DataFrame({"target": [0, 1]})
    with pytest.raises(ValueError, match="No metric function registered"):
        enforce(data=df, policy=policy_path, target="target", strict=True)


def test_loose_mode_swallows_missing_metric(policy_path, monkeypatch):
    """When CI/VENTURALITICA_STRICT are unset and strict=False, missing
    metrics must not crash; enforce returns a list (possibly empty)."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("VENTURALITICA_STRICT", raising=False)

    df = pd.DataFrame({"target": [0, 1]})
    results = enforce(data=df, policy=policy_path, target="target", strict=False)
    assert isinstance(results, list)
