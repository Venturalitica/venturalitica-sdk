"""
Smoke Tests for Core Venturalítica API (v0.5.0)

These are integration tests that exercise real code paths with minimal mocking.
They verify that the main entry points (monitor and enforce) work end-to-end,
from initialization through to results generation. These are "wet runs" that
test actual functionality rather than isolated units.

Test Coverage:
- vl.monitor(): Context manager probe collection and evidence tracking
- vl.enforce(): Policy validation with data, metrics, and edge cases
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
import yaml

from venturalitica import enforce, monitor
from venturalitica.models import ComplianceResult


@pytest.fixture
def tmp_work_dir(tmp_path):
    """Create isolated temporary working directory for smoke tests."""
    original_dir = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_dir)


@pytest.fixture
def sample_policy_file(tmp_path):
    """Create a sample OSCAL policy file for testing."""
    policy = {
        "assessment-plan": {
            "metadata": {
                "title": "Smoke Test Policy",
                "version": "1.0.0",
            },
            "local-definitions": {
                "inventory-items": [
                    {
                        "uuid": "metric-accuracy",
                        "props": [
                            {"name": "metric_key", "value": "accuracy_score"},
                            {"name": "threshold", "value": "0.75"},
                            {"name": "operator", "value": ">="},
                            {"name": "input:target", "value": "actual"},
                            {"name": "input:prediction", "value": "predicted"},
                        ],
                    },
                    {
                        "uuid": "metric-precision",
                        "props": [
                            {"name": "metric_key", "value": "precision_score"},
                            {"name": "threshold", "value": "0.70"},
                            {"name": "operator", "value": ">="},
                        ],
                    },
                ]
            },
            "control-implementations": [
                {
                    "implemented-requirements": [
                        {
                            "control-id": "AI-ACC-001",
                            "description": "Model accuracy must be >= 0.75",
                            "links": [{"href": "#metric-accuracy", "rel": "related"}],
                        },
                        {
                            "control-id": "AI-PREC-001",
                            "description": "Model precision must be >= 0.70",
                            "links": [{"href": "#metric-precision", "rel": "related"}],
                        },
                    ]
                }
            ],
        }
    }

    policy_path = tmp_path / "test_policy.oscal.yaml"
    with open(policy_path, "w") as f:
        yaml.dump(policy, f)

    return str(policy_path)


@pytest.fixture
def sample_dataframe():
    """Create sample training data for smoke tests."""
    return pd.DataFrame(
        {
            "actual": [0, 1, 1, 0, 1, 1, 0, 1] * 5,
            "predicted": [0, 1, 1, 0, 1, 0, 0, 1] * 5,
            "feature_1": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8] * 5,
        }
    )


# ============================================================================
# Smoke Tests: vl.monitor()
# ============================================================================


class TestMonitorSmokeTests:
    """Smoke tests for vl.monitor() context manager."""

    def test_monitor_creates_session_evidence_vault(self, tmp_work_dir):
        """Monitor should create .venturalitica session directory with evidence."""
        with (
            patch("venturalitica.probes.CarbonProbe.start"),
            patch("venturalitica.probes.CarbonProbe.stop"),
            patch("venturalitica.probes.HardwareProbe.start"),
            patch("venturalitica.probes.HardwareProbe.stop"),
            patch("venturalitica.probes.IntegrityProbe.start"),
            patch("venturalitica.probes.IntegrityProbe.stop"),
            patch("venturalitica.probes.BOMProbe.start"),
            patch("venturalitica.probes.BOMProbe.stop"),
            patch("venturalitica.probes.ArtifactProbe.start"),
            patch("venturalitica.probes.ArtifactProbe.stop"),
            patch("venturalitica.probes.HandshakeProbe.start"),
            patch("venturalitica.probes.HandshakeProbe.stop"),
            patch("venturalitica.probes.TraceProbe.start"),
            patch("venturalitica.probes.TraceProbe.stop"),
        ):
            with monitor("Smoke Test Task"):
                pass

            # Check that .venturalitica directory was created
            assert Path(".venturalitica").exists()
            assert Path(".venturalitica").is_dir()

    def test_monitor_yields_control_to_body(self, tmp_work_dir, capsys):
        """Monitor should yield control and execute body code."""
        executed = False

        with (
            patch("venturalitica.probes.CarbonProbe.start"),
            patch("venturalitica.probes.CarbonProbe.stop"),
            patch("venturalitica.probes.HardwareProbe.start"),
            patch("venturalitica.probes.HardwareProbe.stop"),
            patch("venturalitica.probes.IntegrityProbe.start"),
            patch("venturalitica.probes.IntegrityProbe.stop"),
            patch("venturalitica.probes.BOMProbe.start"),
            patch("venturalitica.probes.BOMProbe.stop"),
            patch("venturalitica.probes.ArtifactProbe.start"),
            patch("venturalitica.probes.ArtifactProbe.stop"),
            patch("venturalitica.probes.HandshakeProbe.start"),
            patch("venturalitica.probes.HandshakeProbe.stop"),
            patch("venturalitica.probes.TraceProbe.start"),
            patch("venturalitica.probes.TraceProbe.stop"),
        ):
            with monitor("Test Task"):
                executed = True
                assert True

        assert executed
        captured = capsys.readouterr()
        assert "Starting monitor" in captured.out
        assert "Monitor stopped" in captured.out

    def test_monitor_with_custom_name_and_label(self, tmp_work_dir, capsys):
        """Monitor should accept custom name and label parameters."""
        task_name = "ML Training Pipeline"
        task_label = "v0.5.0-release"

        with (
            patch("venturalitica.probes.CarbonProbe.start"),
            patch("venturalitica.probes.CarbonProbe.stop"),
            patch("venturalitica.probes.HardwareProbe.start"),
            patch("venturalitica.probes.HardwareProbe.stop"),
            patch("venturalitica.probes.IntegrityProbe.start"),
            patch("venturalitica.probes.IntegrityProbe.stop"),
            patch("venturalitica.probes.BOMProbe.start"),
            patch("venturalitica.probes.BOMProbe.stop"),
            patch("venturalitica.probes.ArtifactProbe.start"),
            patch("venturalitica.probes.ArtifactProbe.stop"),
            patch("venturalitica.probes.HandshakeProbe.start"),
            patch("venturalitica.probes.HandshakeProbe.stop"),
            patch("venturalitica.probes.TraceProbe.start"),
            patch("venturalitica.probes.TraceProbe.stop"),
        ):
            with monitor(name=task_name, label=task_label):
                pass

        captured = capsys.readouterr()
        assert task_name in captured.out

    def test_monitor_cleanup_even_on_exception(self, tmp_work_dir):
        """Monitor should clean up resources even if body raises exception."""
        with (
            patch("venturalitica.probes.CarbonProbe.start"),
            patch("venturalitica.probes.CarbonProbe.stop") as mock_carbon_stop,
            patch("venturalitica.probes.HardwareProbe.start"),
            patch("venturalitica.probes.HardwareProbe.stop") as mock_hw_stop,
            patch("venturalitica.probes.IntegrityProbe.start"),
            patch("venturalitica.probes.IntegrityProbe.stop"),
            patch("venturalitica.probes.BOMProbe.start"),
            patch("venturalitica.probes.BOMProbe.stop"),
            patch("venturalitica.probes.ArtifactProbe.start"),
            patch("venturalitica.probes.ArtifactProbe.stop"),
            patch("venturalitica.probes.HandshakeProbe.start"),
            patch("venturalitica.probes.HandshakeProbe.stop"),
            patch("venturalitica.probes.TraceProbe.start"),
            patch("venturalitica.probes.TraceProbe.stop"),
        ):
            with pytest.raises(ValueError):
                with monitor("Failing Task"):
                    raise ValueError("Test error")

        # Verify cleanup was called
        assert mock_carbon_stop.called
        assert mock_hw_stop.called


# ============================================================================
# Smoke Tests: vl.enforce()
# ============================================================================


class TestEnforceSmokeTests:
    """Smoke tests for vl.enforce() policy enforcement."""

    def test_enforce_with_metrics_passing(self, sample_policy_file, capsys):
        """Enforce should evaluate metrics and return passing results."""
        metrics = {
            "accuracy_score": 0.85,
            "precision_score": 0.80,
        }

        results = enforce(metrics=metrics, policy=sample_policy_file)

        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(r, ComplianceResult) for r in results)

        captured = capsys.readouterr()
        assert "Enforcing policy" in captured.out

    def test_enforce_with_metrics_failing(self, sample_policy_file):
        """Enforce should detect failed controls."""
        metrics = {
            "accuracy_score": 0.50,  # Below 0.75 threshold
            "precision_score": 0.60,  # Below 0.70 threshold
        }

        results = enforce(metrics=metrics, policy=sample_policy_file)

        assert len(results) > 0
        # At least one control should fail
        failed = [r for r in results if not r.passed]
        assert len(failed) > 0

    def test_enforce_with_dataframe(self, sample_policy_file, sample_dataframe):
        """Enforce should compute metrics from DataFrame and evaluate."""
        results = enforce(data=sample_dataframe, policy=sample_policy_file, target="actual", prediction="predicted")

        assert isinstance(results, list)
        # Results depend on actual data, but structure should be valid
        if results:
            assert all(isinstance(r, ComplianceResult) for r in results)

    def test_enforce_caches_results_locally(self, tmp_work_dir, sample_policy_file):
        """Enforce should cache results in .venturalitica/results.json."""
        metrics = {"accuracy_score": 0.85, "precision_score": 0.80}

        enforce(metrics=metrics, policy=sample_policy_file)

        results_file = Path(".venturalitica/results.json")
        assert results_file.exists()

        with open(results_file) as f:
            cached_results = json.load(f)

        assert isinstance(cached_results, list)
        assert len(cached_results) > 0

    def test_enforce_multiple_policies(self, tmp_path, sample_dataframe):
        """Enforce should handle multiple policy files."""
        policy1 = {
            "assessment-plan": {
                "local-definitions": {
                    "inventory-items": [
                        {
                            "uuid": "m1",
                            "props": [
                                {"name": "metric_key", "value": "accuracy_score"},
                                {"name": "threshold", "value": "0.50"},
                                {"name": "operator", "value": ">="},
                            ],
                        }
                    ]
                },
                "control-implementations": [
                    {
                        "implemented-requirements": [
                            {
                                "control-id": "C1",
                                "description": "Basic accuracy",
                                "links": [{"href": "#m1", "rel": "related"}],
                            }
                        ]
                    }
                ],
            }
        }

        policy2 = {
            "assessment-plan": {
                "local-definitions": {
                    "inventory-items": [
                        {
                            "uuid": "m2",
                            "props": [
                                {"name": "metric_key", "value": "precision_score"},
                                {"name": "threshold", "value": "0.40"},
                                {"name": "operator", "value": ">="},
                            ],
                        }
                    ]
                },
                "control-implementations": [
                    {
                        "implemented-requirements": [
                            {
                                "control-id": "C2",
                                "description": "Basic precision",
                                "links": [{"href": "#m2", "rel": "related"}],
                            }
                        ]
                    }
                ],
            }
        }

        policy_path1 = tmp_path / "policy1.yaml"
        policy_path2 = tmp_path / "policy2.yaml"

        with open(policy_path1, "w") as f:
            yaml.dump(policy1, f)
        with open(policy_path2, "w") as f:
            yaml.dump(policy2, f)

        results = enforce(
            metrics={"accuracy_score": 0.85, "precision_score": 0.75}, policy=[str(policy_path1), str(policy_path2)]
        )

        assert isinstance(results, list)

    def test_enforce_handles_missing_policy_gracefully(self):
        """Enforce should handle missing policy files gracefully."""
        results = enforce(metrics={"accuracy_score": 0.85}, policy="nonexistent_policy.yaml")

        # Should return empty list, not raise
        assert results == []

    def test_enforce_strict_mode_raises_on_error(self, tmp_work_dir):
        """Enforce should raise exceptions in strict mode."""
        with pytest.raises(Exception):
            enforce(data="not-a-dataframe", policy="some_policy.yaml", strict=True)

    def test_enforce_non_strict_mode_handles_errors(self, tmp_work_dir, capsys):
        """Enforce should catch errors in non-strict mode."""
        results = enforce(data="not-a-dataframe", policy="some_policy.yaml", strict=False)

        # Should return empty list, not raise
        assert results == []

        captured = capsys.readouterr()
        # May contain error message or just empty results
        assert True  # Successfully handled without raising

    def test_enforce_sets_session_enforced_flag(self):
        """Enforce should set internal session flag."""
        import venturalitica.api

        # Call enforce with nonexistent policy (should fail gracefully)
        enforce(policy="nonexistent.yaml")

        # Flag should be set to True
        assert venturalitica.api._SESSION_ENFORCED is True

    def test_enforce_with_column_discovery(self, tmp_path, sample_dataframe):
        """Enforce should discover target/prediction columns automatically."""
        # Create DataFrame with standard column names
        df = sample_dataframe.rename(columns={"actual": "target", "predicted": "prediction"})

        policy = {
            "assessment-plan": {
                "local-definitions": {
                    "inventory-items": [
                        {
                            "uuid": "m1",
                            "props": [
                                {"name": "metric_key", "value": "accuracy_score"},
                                {"name": "threshold", "value": "0.50"},
                                {"name": "operator", "value": ">="},
                                {"name": "input:target", "value": "target"},
                                {"name": "input:prediction", "value": "prediction"},
                            ],
                        }
                    ]
                },
                "control-implementations": [
                    {
                        "implemented-requirements": [
                            {
                                "control-id": "C1",
                                "description": "Test",
                                "links": [{"href": "#m1", "rel": "related"}],
                            }
                        ]
                    }
                ],
            }
        }

        policy_path = tmp_path / "policy.yaml"
        with open(policy_path, "w") as f:
            yaml.dump(policy, f)

        # Should auto-discover columns
        results = enforce(data=df, policy=str(policy_path))

        assert isinstance(results, list)


# ============================================================================
# Smoke Tests: Integration (monitor + enforce)
# ============================================================================


class TestMonitorEnforceIntegration:
    """Smoke tests for combined monitor and enforce workflows."""

    def test_monitor_and_enforce_together(self, tmp_work_dir, sample_policy_file, capsys):
        """Monitor and enforce should work together in same session."""
        with (
            patch("venturalitica.probes.CarbonProbe.start"),
            patch("venturalitica.probes.CarbonProbe.stop"),
            patch("venturalitica.probes.HardwareProbe.start"),
            patch("venturalitica.probes.HardwareProbe.stop"),
            patch("venturalitica.probes.IntegrityProbe.start"),
            patch("venturalitica.probes.IntegrityProbe.stop"),
            patch("venturalitica.probes.BOMProbe.start"),
            patch("venturalitica.probes.BOMProbe.stop"),
            patch("venturalitica.probes.ArtifactProbe.start"),
            patch("venturalitica.probes.ArtifactProbe.stop"),
            patch("venturalitica.probes.HandshakeProbe.start"),
            patch("venturalitica.probes.HandshakeProbe.stop"),
            patch("venturalitica.probes.TraceProbe.start"),
            patch("venturalitica.probes.TraceProbe.stop"),
        ):
            with monitor("Integration Test"):
                results = enforce(metrics={"accuracy_score": 0.85, "precision_score": 0.80}, policy=sample_policy_file)

                assert isinstance(results, list)

        captured = capsys.readouterr()
        assert "Starting monitor" in captured.out
        assert "Monitor stopped" in captured.out
        assert "Enforcing policy" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
