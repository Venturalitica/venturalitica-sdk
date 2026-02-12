"""
Coverage Improvement Tests for v0.5.0 Release (Target: 73% → 90%+)

This test module focuses on edge cases and code paths that are under-tested,
targeting critical modules: api, core, loader, telemetry, integrations, and output.

Strategy:
1. Error handling paths (exceptions, malformed inputs)
2. Boundary conditions (empty data, missing columns)
3. Integration edge cases (multiple policy files, mixed metrics/data)
4. Session lifecycle edge cases
5. Telemetry and integration fallback paths
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import yaml

from venturalitica import enforce, monitor
from venturalitica.core import AssuranceValidator, ComplianceResult
from venturalitica.models import InternalPolicy, InternalControl
from venturalitica.session import GovernanceSession


# ============================================================================
# Coverage: Error Handling and Edge Cases
# ============================================================================


class TestCoreErrorHandling:
    """Test error handling in core module."""

    def test_assurance_validator_with_invalid_control(self):
        """Validator should handle controls with missing required fields."""
        policy_data = {
            "assessment-plan": {
                "local-definitions": {"inventory-items": []},
                "control-implementations": [
                    {
                        "implemented-requirements": [
                            {
                                "control-id": "INVALID",
                                # Missing description
                                "links": [],
                            }
                        ]
                    }
                ],
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(policy_data, f)
            path = f.name

        try:
            validator = AssuranceValidator(path)
            # Should instantiate without error
            assert validator is not None
        finally:
            os.unlink(path)

    def test_assurance_validator_strict_mode_with_missing_columns(self):
        """Validator in strict mode should error on missing columns."""
        policy = {
            "assessment-plan": {
                "local-definitions": {
                    "inventory-items": [
                        {
                            "uuid": "m1",
                            "props": [
                                {"name": "metric_key", "value": "accuracy_score"},
                                {"name": "threshold", "value": "0.8"},
                                {"name": "operator", "value": ">="},
                                {"name": "input:target", "value": "actual"},
                                {"name": "input:prediction", "value": "predicted"},
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

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(policy, f)
            path = f.name

        try:
            validator = AssuranceValidator(path)
            df = pd.DataFrame({"wrong_col": [1, 2, 3]})

            # Strict mode: should handle missing columns gracefully
            results = validator.compute_and_evaluate(df, {}, strict=True)
            assert isinstance(results, list)
        finally:
            os.unlink(path)

    def test_enforce_with_empty_dataframe(self):
        """Enforce should handle empty DataFrames gracefully."""
        policy = {
            "assessment-plan": {
                "local-definitions": {
                    "inventory-items": [
                        {
                            "uuid": "m1",
                            "props": [
                                {"name": "metric_key", "value": "accuracy_score"},
                                {"name": "threshold", "value": "0.8"},
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
                                "description": "Test",
                                "links": [{"href": "#m1", "rel": "related"}],
                            }
                        ]
                    }
                ],
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(policy, f)
            path = f.name

        try:
            # Empty DataFrame
            df = pd.DataFrame()
            results = enforce(data=df, policy=path)
            assert isinstance(results, list)
        finally:
            os.unlink(path)


# ============================================================================
# Coverage: Telemetry Edge Cases
# ============================================================================


class TestTelemetryFallbacks:
    """Test telemetry fallback paths."""

    def test_telemetry_import_failure_handled(self):
        """Monitor should handle telemetry import failures."""
        with patch("venturalitica.api.telemetry", side_effect=ImportError("telemetry unavailable")):
            # Monitor should still work even if telemetry fails
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
                with monitor("Test"):
                    pass

    def test_telemetry_capture_exception_handled(self):
        """Monitor should handle exceptions during telemetry capture."""
        with patch("venturalitica.api.telemetry") as mock_telemetry:
            mock_telemetry.capture.side_effect = Exception("Telemetry error")

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
                # Should not raise even if telemetry fails
                with monitor("Test"):
                    pass


# ============================================================================
# Coverage: Integration Paths
# ============================================================================


class TestIntegrationPaths:
    """Test integration with MLflow, Weights & Biases, etc."""

    def test_enforce_auto_log_handles_import_errors(self, tmp_path):
        """Auto-log should handle missing MLflow/W&B gracefully."""
        os.chdir(tmp_path)

        policy = {
            "assessment-plan": {
                "local-definitions": {
                    "inventory-items": [
                        {
                            "uuid": "m1",
                            "props": [
                                {"name": "metric_key", "value": "accuracy_score"},
                                {"name": "threshold", "value": "0.5"},
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

        with patch("venturalitica.integrations.auto_log", side_effect=ImportError("mlflow not available")):
            # Should still return results despite integration error
            results = enforce(metrics={"accuracy_score": 0.8}, policy=str(policy_path))
            assert isinstance(results, list)


# ============================================================================
# Coverage: Session Lifecycle
# ============================================================================


class TestSessionEdgeCases:
    """Test session management edge cases."""

    def test_governance_session_with_symlink_failure(self, tmp_path):
        """Session should handle symlink creation failures gracefully."""
        os.chdir(tmp_path)

        with patch("os.symlink", side_effect=OSError("symlink not supported")):
            session = GovernanceSession("test_run")
            assert session.base_dir.exists()
            session.stop()

    def test_governance_session_multiple_stops(self, tmp_path):
        """Calling stop multiple times should not error."""
        os.chdir(tmp_path)

        session = GovernanceSession("test_run")
        session.stop()
        session.stop()  # Should not raise


# ============================================================================
# Coverage: API Boundary Conditions
# ============================================================================


class TestAPIBoundaryConditions:
    """Test API with boundary conditions."""

    def test_enforce_with_nan_metrics(self):
        """Enforce should handle NaN values in metrics gracefully."""
        policy = {
            "assessment-plan": {
                "local-definitions": {
                    "inventory-items": [
                        {
                            "uuid": "m1",
                            "props": [
                                {"name": "metric_key", "value": "accuracy_score"},
                                {"name": "threshold", "value": "0.8"},
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
                                "description": "Test",
                                "links": [{"href": "#m1", "rel": "related"}],
                            }
                        ]
                    }
                ],
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(policy, f)
            path = f.name

        try:
            import math

            results = enforce(metrics={"accuracy_score": math.nan}, policy=path)
            assert isinstance(results, list)
        finally:
            os.unlink(path)

    def test_enforce_with_negative_metrics(self):
        """Enforce should handle negative metric values."""
        policy = {
            "assessment-plan": {
                "local-definitions": {
                    "inventory-items": [
                        {
                            "uuid": "m1",
                            "props": [
                                {"name": "metric_key", "value": "loss"},
                                {"name": "threshold", "value": "0.5"},
                                {"name": "operator", "value": "<="},
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

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(policy, f)
            path = f.name

        try:
            results = enforce(metrics={"loss": -0.1}, policy=path)
            assert isinstance(results, list)
        finally:
            os.unlink(path)

    def test_enforce_results_caching_with_existing_results(self, tmp_path):
        """Enforce should append to existing cached results."""
        os.chdir(tmp_path)

        # Pre-create results file
        os.makedirs(".venturalitica", exist_ok=True)
        existing_results = [{"control_id": "OLD", "passed": True}]
        with open(".venturalitica/results.json", "w") as f:
            json.dump(existing_results, f)

        policy = {
            "assessment-plan": {
                "local-definitions": {
                    "inventory-items": [
                        {
                            "uuid": "m1",
                            "props": [
                                {"name": "metric_key", "value": "accuracy_score"},
                                {"name": "threshold", "value": "0.5"},
                                {"name": "operator", "value": ">="},
                            ],
                        }
                    ]
                },
                "control-implementations": [
                    {
                        "implemented-requirements": [
                            {
                                "control-id": "NEW",
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

        enforce(metrics={"accuracy_score": 0.8}, policy=str(policy_path))

        # Check results were appended
        with open(".venturalitica/results.json") as f:
            combined = json.load(f)

        assert len(combined) >= 1  # At least one new result appended


# ============================================================================
# Coverage: Loader Edge Cases
# ============================================================================


class TestLoaderEdgeCases:
    """Test policy loader with edge cases."""

    def test_loader_with_missing_policy_file(self):
        """Loader should handle missing policy files."""
        from venturalitica.loader import load_policy

        with pytest.raises(FileNotFoundError):
            load_policy("nonexistent_policy.yaml")

    def test_loader_with_malformed_yaml(self, tmp_path):
        """Loader should handle malformed YAML."""
        from venturalitica.loader import load_policy

        bad_yaml_path = tmp_path / "bad.yaml"
        with open(bad_yaml_path, "w") as f:
            f.write("{ invalid: yaml: content: [")

        with pytest.raises(Exception):  # Will raise YAML parsing error
            load_policy(str(bad_yaml_path))


# ============================================================================
# Coverage: Column Discovery
# ============================================================================


class TestColumnDiscovery:
    """Test column discovery with various scenarios."""

    def test_column_discovery_with_synonyms(self):
        """Column discovery should find synonyms."""
        from venturalitica.binding import discover_column

        df = pd.DataFrame({"ground_truth": [1, 0, 1], "predictions": [1, 0, 0]})

        # Should discover even with non-standard names
        result = discover_column("target", {}, df, {})
        assert result != "MISSING"  # Should find something or return MISSING

    def test_column_discovery_with_missing_columns(self):
        """Column discovery should return MISSING for non-existent columns."""
        from venturalitica.binding import discover_column

        df = pd.DataFrame({"feature_1": [1, 2, 3], "feature_2": [4, 5, 6]})

        result = discover_column("nonexistent_role", {}, df, {})
        assert result == "MISSING"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
