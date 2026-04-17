"""Tests for OSCAL profile runtime semantics:

- `enforcement_mode` (monitor/warn/block) drives pipeline reaction to failures.
- `lifecycle_phase` (training/validation/monitoring/incident) filters which
  controls the SDK evaluates. Controls tagged `monitoring` or `incident` are
  skipped by the SDK because they target the runtime proxy / incident handler.
"""

import sys

import pandas as pd
import pytest

from venturalitica.core import AssuranceValidator, ComplianceBlockError
from venturalitica.models import InternalControl, InternalPolicy


def _policy(*controls: InternalControl) -> InternalPolicy:
    return InternalPolicy(title="Test", controls=list(controls))


def _control(
    id: str,
    metric_key: str = "accuracy_score",
    threshold: float = 0.9,
    operator: str = ">=",
    severity: str = "high",
    metadata=None,
) -> InternalControl:
    return InternalControl(
        id=id,
        description=f"Test control {id}",
        severity=severity,
        metric_key=metric_key,
        threshold=threshold,
        operator=operator,
        metadata=metadata or {},
    )


# ---------------------------------------------------------------------------
# enforcement_mode
# ---------------------------------------------------------------------------

class TestEnforcementMode:

    def test_block_raises_on_failure(self):
        ctrl = _control("C1", threshold=0.9, metadata={"enforcement_mode": "block"})
        validator = AssuranceValidator(policy=_policy(ctrl))
        with pytest.raises(ComplianceBlockError) as exc:
            validator.evaluate({"accuracy_score": 0.5})
        assert "C1" in str(exc.value)
        assert "block" in str(exc.value)

    def test_block_does_not_raise_on_pass(self):
        ctrl = _control("C1", threshold=0.5, metadata={"enforcement_mode": "block"})
        validator = AssuranceValidator(policy=_policy(ctrl))
        results = validator.evaluate({"accuracy_score": 0.9})
        assert results[0].passed is True

    def test_warn_emits_stderr_and_continues(self, capsys):
        ctrl = _control("C1", threshold=0.9, metadata={"enforcement_mode": "warn"})
        validator = AssuranceValidator(policy=_policy(ctrl))
        results = validator.evaluate({"accuracy_score": 0.5})
        assert len(results) == 1
        assert results[0].passed is False
        captured = capsys.readouterr()
        assert "C1" in captured.err
        assert "warn" in captured.err

    def test_monitor_is_silent_default(self, capsys):
        """When no enforcement_mode is set, behavior is monitor (silent)."""
        ctrl = _control("C1", threshold=0.9)
        validator = AssuranceValidator(policy=_policy(ctrl))
        results = validator.evaluate({"accuracy_score": 0.5})
        assert len(results) == 1
        assert results[0].passed is False
        captured = capsys.readouterr()
        assert "C1" not in captured.err

    def test_explicit_monitor_is_silent(self, capsys):
        ctrl = _control("C1", threshold=0.9, metadata={"enforcement_mode": "monitor"})
        validator = AssuranceValidator(policy=_policy(ctrl))
        validator.evaluate({"accuracy_score": 0.5})
        captured = capsys.readouterr()
        assert "C1" not in captured.err

    def test_block_halts_before_subsequent_controls(self):
        """When C1 is block and fails, C2 should not be reached."""
        c1 = _control("C1", threshold=0.9, metadata={"enforcement_mode": "block"})
        c2 = _control("C2", threshold=0.5)
        validator = AssuranceValidator(policy=_policy(c1, c2))
        with pytest.raises(ComplianceBlockError):
            validator.evaluate({"accuracy_score": 0.5})


# ---------------------------------------------------------------------------
# lifecycle_phase
# ---------------------------------------------------------------------------

class TestLifecyclePhase:

    def test_no_phase_skips_monitoring_and_incident(self):
        c_train = _control("C-train", threshold=0.5,
                           metadata={"lifecycle_phase": "training"})
        c_mon = _control("C-mon", threshold=0.5,
                         metadata={"lifecycle_phase": "monitoring"})
        c_inc = _control("C-inc", threshold=0.5,
                         metadata={"lifecycle_phase": "incident"})
        validator = AssuranceValidator(
            policy=_policy(c_train, c_mon, c_inc)
        )
        results = validator.evaluate({"accuracy_score": 0.9})
        ids = {r.control_id for r in results}
        assert ids == {"C-train"}

    def test_phase_training_filters_in_only_training(self):
        c_train = _control("C-train", threshold=0.5,
                           metadata={"lifecycle_phase": "training"})
        c_val = _control("C-val", threshold=0.5,
                         metadata={"lifecycle_phase": "validation"})
        validator = AssuranceValidator(policy=_policy(c_train, c_val))
        results = validator.evaluate({"accuracy_score": 0.9}, phase="training")
        assert [r.control_id for r in results] == ["C-train"]

    def test_phase_validation_filters_in_only_validation(self):
        c_train = _control("C-train", threshold=0.5,
                           metadata={"lifecycle_phase": "training"})
        c_val = _control("C-val", threshold=0.5,
                         metadata={"lifecycle_phase": "validation"})
        validator = AssuranceValidator(policy=_policy(c_train, c_val))
        results = validator.evaluate({"accuracy_score": 0.9}, phase="validation")
        assert [r.control_id for r in results] == ["C-val"]

    def test_untagged_controls_run_in_any_phase(self):
        c_any = _control("C-any", threshold=0.5)  # no lifecycle_phase
        c_train = _control("C-train", threshold=0.5,
                           metadata={"lifecycle_phase": "training"})
        validator = AssuranceValidator(policy=_policy(c_any, c_train))
        results = validator.evaluate({"accuracy_score": 0.9}, phase="validation")
        ids = {r.control_id for r in results}
        assert "C-any" in ids
        assert "C-train" not in ids

    def test_multi_phase_control_matches_any_listed_phase(self):
        """A control tagged with BOTH training and validation should match either phase."""
        c = _control("C-multi", threshold=0.5, metadata={
            "lifecycle_phase": ["training", "validation"],
        })
        validator = AssuranceValidator(policy=_policy(c))
        assert [r.control_id for r in validator.evaluate({"accuracy_score": 0.9},
                                                          phase="training")] == ["C-multi"]
        assert [r.control_id for r in validator.evaluate({"accuracy_score": 0.9},
                                                          phase="validation")] == ["C-multi"]

    def test_multi_phase_with_monitoring_still_runs_in_sdk_when_training_also_listed(self):
        """Control applying to training+monitoring runs in SDK (training side)."""
        c = _control("C-dual", threshold=0.5, metadata={
            "lifecycle_phase": ["training", "monitoring"],
        })
        validator = AssuranceValidator(policy=_policy(c))
        results = validator.evaluate({"accuracy_score": 0.9})  # no phase
        assert [r.control_id for r in results] == ["C-dual"]

    def test_monitoring_only_control_still_skipped(self):
        """A control exclusively in monitoring is skipped by SDK default."""
        c = _control("C-mon-only", threshold=0.5, metadata={
            "lifecycle_phase": ["monitoring"],
        })
        validator = AssuranceValidator(policy=_policy(c))
        assert validator.evaluate({"accuracy_score": 0.9}) == []

    def test_compute_and_evaluate_respects_phase(self):
        """Phase filter also applies when evaluating against a DataFrame."""
        df = pd.DataFrame({
            "target": [1, 0, 1, 0, 1, 0],
            "prediction": [1, 0, 1, 1, 1, 0],
        })
        c_train = _control("C-train", metric_key="accuracy_score",
                           threshold=0.5, metadata={"lifecycle_phase": "training"})
        c_val = _control("C-val", metric_key="accuracy_score", threshold=0.5,
                         metadata={"lifecycle_phase": "validation"})
        validator = AssuranceValidator(policy=_policy(c_train, c_val))
        results = validator.compute_and_evaluate(
            df, {"target": "target", "prediction": "prediction"},
            phase="training",
        )
        assert [r.control_id for r in results] == ["C-train"]


# ---------------------------------------------------------------------------
# Combined
# ---------------------------------------------------------------------------

class TestCombinedSemantics:

    def test_block_in_monitoring_not_triggered_by_sdk(self):
        """If a monitoring control is `block`, the SDK must skip it (leave it
        to the runtime proxy) so training does not halt spuriously."""
        c_mon = _control("C-mon", threshold=0.9, metadata={
            "lifecycle_phase": "monitoring",
            "enforcement_mode": "block",
        })
        validator = AssuranceValidator(policy=_policy(c_mon))
        # Should NOT raise — monitoring phase is filtered out by default
        results = validator.evaluate({"accuracy_score": 0.5})
        assert results == []
