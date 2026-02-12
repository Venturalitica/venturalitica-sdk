from unittest.mock import MagicMock, patch

import pytest

from venturalitica.core import ComplianceResult
from venturalitica.integrations import _log_clearml, _log_mlflow, _log_wandb, auto_log, generate_report


@pytest.fixture
def sample_results():
    return [
        ComplianceResult(
            control_id="C1",
            description="Test Control",
            metric_key="accuracy",
            threshold=0.8,
            actual_value=0.9,
            operator=">=",
            passed=True,
            severity="high",
        )
    ]


def test_generate_report(sample_results):
    report = generate_report(sample_results)
    assert "# Assurance Compliance Report" in report
    assert "✅ Control C1" in report

    # Test failed case in report
    failed = [ComplianceResult("F1", "Fail", "acc", 0.5, 0.4, "<", False, "high")]
    report_fail = generate_report(failed)
    assert "❌ Control F1" in report_fail
    assert "Fix this in Venturalítica SaaS" in report_fail


def test_log_mlflow_active(sample_results):
    with (
        patch("mlflow.active_run") as mock_active,
        patch("mlflow.log_metrics") as mock_log_metrics,
        patch("mlflow.log_text") as mock_log_text,
        patch("mlflow.set_tags") as mock_set_tags,
    ):
        mock_active.return_value = MagicMock()
        _log_mlflow(sample_results, "Report Text")

        mock_log_metrics.assert_called_once()
        mock_set_tags.assert_called_once()
        mock_log_text.assert_called_once()


def test_log_mlflow_inactive(sample_results):
    with patch("mlflow.active_run") as mock_active, patch("mlflow.log_metrics") as mock_log_metrics:
        mock_active.return_value = None
        _log_mlflow(sample_results, "Report Text")
        mock_log_metrics.assert_not_called()


def test_log_wandb_active(sample_results):
    with patch("wandb.run") as mock_run, patch("wandb.log") as mock_log, patch("wandb.log_artifact") as mock_log_art:
        mock_run.id = "test-run-id"
        mock_run.summary = {}
        _log_wandb(sample_results, "Report Text")

        mock_log.assert_called()
        assert mock_run.summary["assurance.C1"] == "PASS"
        mock_log_art.assert_called_once()


def test_log_wandb_inactive(sample_results):
    with patch("wandb.run", None), patch("wandb.log") as mock_log:
        _log_wandb(sample_results, "Report Text")
        mock_log.assert_not_called()


def test_log_clearml_active(sample_results):
    with patch("clearml.Task") as mock_task_cls:
        mock_results = [sample_results[0], ComplianceResult("F1", "Fail", "acc", 0.5, 0.4, "<", False, "low")]
        mock_task = MagicMock()
        mock_task_cls.current_task.return_value = mock_task
        mock_logger = MagicMock()
        mock_task.get_logger.return_value = mock_logger
        mock_task.get_tags.return_value = ["existing"]

        _log_clearml(mock_results, "Report Text")

        mock_task.set_tags.assert_called()
        mock_logger.report_text.assert_called()


def test_log_clearml_inactive(sample_results):
    with patch("clearml.Task") as mock_task_cls:
        mock_task_cls.current_task.return_value = None
        _log_clearml(sample_results, "Report Text")
        # Should just return gracefully


def test_auto_log_empty():
    with patch("venturalitica.integrations._log_mlflow") as m1:
        auto_log([])
        m1.assert_not_called()


def test_import_errors(sample_results):
    # Test that catching ImportError works (ImportError path coverage)
    with patch.dict("sys.modules", {"mlflow": None, "wandb": None, "clearml": None}):
        # These should not raise exceptions even if the module "failed" to import
        _log_mlflow(sample_results, "txt")
        _log_wandb(sample_results, "txt")
        _log_clearml(sample_results, "txt")


def test_exception_handling(sample_results):
    # Test that generic exceptions are caught
    with patch("mlflow.active_run", side_effect=Exception("Crash")):
        _log_mlflow(sample_results, "txt")


def test_wandb_cleanup_error(sample_results):
    # Cover line where os.remove fails
    with (
        patch("wandb.run") as mock_run,
        patch("wandb.log"),
        patch("wandb.log_artifact"),
        patch("wandb.Artifact"),
        patch("os.remove", side_effect=OSError("Permission denied")),
    ):
        mock_run.id = "test"
        mock_run.summary = {}
        _log_wandb(sample_results, "txt")
