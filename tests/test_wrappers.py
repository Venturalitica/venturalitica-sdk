import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from venturalitica.wrappers import AssuranceWrapper, wrap


def test_wrappers_basic_flow(tmp_path):
    # Mock model
    class MockModel:
        def fit(self, X, y=None, **kwargs):
            return self

        def predict(self, X, **kwargs):
            return np.ones(len(X))

        def get_params(self, deep=True):
            return {"param1": "val1"}

    model = MockModel()
    df = pd.DataFrame({"target": [1, 0], "A": [0.5, 0.6]})

    # Wrap without policy for now
    os.chdir(tmp_path)
    wrapped = wrap(model)

    # Test fit
    wrapped.fit(df, target="target")

    # Test predict
    X = df[["A"]]
    pred = wrapped.predict(X)
    assert len(pred) == 2

    # Check if results were saved
    assert os.path.exists(".venturalitica/latest_run.json")


def test_assurance_wrapper_predict_proba():
    """Test wrapper predict_proba method delegates correctly."""

    class DummyModel:
        def fit(self, X, y):
            return self

        def predict(self, X):
            return np.zeros(len(X))

        def predict_proba(self, X):
            return np.column_stack([1 - X[:, 0], X[:, 0]])

    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
        f.write("title: Test\ncontrols: []\n")
        policy_file = f.name

    try:
        wrapper = AssuranceWrapper(DummyModel(), policy=policy_file)
        X = np.array([[0.1], [0.5], [0.9]])
        proba = wrapper.predict_proba(X)
        assert proba.shape == (3, 2)
    finally:
        os.unlink(policy_file)


def test_assurance_wrapper_get_params():
    """Test wrapper preserves model get_params."""

    class DummyModel:
        def fit(self, X, y):
            return self

        def predict(self, X):
            return X

        def get_params(self):
            return {"n_estimators": 100, "max_depth": 5}

    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
        f.write("title: Test\ncontrols: []\n")
        policy_file = f.name

    try:
        wrapper = AssuranceWrapper(DummyModel(), policy=policy_file)
        params = wrapper.get_params()
        assert params["n_estimators"] == 100
    finally:
        os.unlink(policy_file)


# ──────────────────────────────────────────────────────────────────────
# Additional coverage tests appended below
# ──────────────────────────────────────────────────────────────────────


def test_call_forwarding():
    """Lines 29-31: __call__ forwards to the model (PyTorch nn.Module pattern)."""

    class CallableModel:
        def __call__(self, x):
            return x * 2

        def fit(self, X, y):
            return self

        def predict(self, X):
            return X

    wrapper = AssuranceWrapper(CallableModel())
    result = wrapper(5)
    assert result == 10


def test_audit_kwargs_separation(tmp_path):
    """Lines 50-56: audit_kwargs are separated from model_kwargs."""
    os.chdir(tmp_path)

    class StrictModel:
        def fit(self, X, y=None):
            # This model only accepts X and y, no extra kwargs
            return self

        def predict(self, X):
            return np.ones(len(X))

    model = StrictModel()
    wrapper = AssuranceWrapper(model)
    df = pd.DataFrame({"target": [1, 0], "A": [0.5, 0.6]})

    # 'target' is NOT a parameter of fit() so it should go to audit_kwargs
    # This should not raise TypeError for unexpected kwargs
    wrapper.fit(df, target="target")


def test_fit_with_audit_data_kwarg(tmp_path):
    """Lines 60-64: fit uses audit_data kwarg if provided."""
    os.chdir(tmp_path)

    class SimpleModel:
        def fit(self, X, y=None):
            return self

        def predict(self, X):
            return np.zeros(len(X))

    wrapper = AssuranceWrapper(SimpleModel())

    # Training data (numpy)
    X_train = np.array([[1, 2], [3, 4]])

    # Separate audit data (DataFrame)
    audit_df = pd.DataFrame({"target": [1, 0], "A": [0.5, 0.6]})

    with patch("venturalitica.enforce", return_value=[]) as mock_enforce:
        wrapper.fit(X_train, audit_data=audit_df)
        # enforce should have been called with the audit_data DataFrame
        mock_enforce.assert_called_once()
        call_kwargs = mock_enforce.call_args
        assert call_kwargs[1]["data"] is audit_df


def test_fit_save_run_metadata_exception(tmp_path, capsys):
    """Lines 71-75: _save_run_metadata exception is caught and printed."""
    os.chdir(tmp_path)

    class SimpleModel:
        def fit(self, X, y=None):
            return self

        def predict(self, X):
            return np.zeros(len(X))

    wrapper = AssuranceWrapper(SimpleModel())
    df = pd.DataFrame({"target": [1, 0], "A": [0.5, 0.6]})

    with patch.object(wrapper, "_save_run_metadata", side_effect=RuntimeError("meta error")):
        with patch("venturalitica.enforce", return_value=[]):
            wrapper.fit(df, target="target")

    captured = capsys.readouterr()
    assert "Failed to save run metadata" in captured.out


def test_fit_upload_policy_artifacts_exception(tmp_path, capsys):
    """Lines 77-81: _upload_policy_artifacts exception is caught and printed."""
    os.chdir(tmp_path)

    class SimpleModel:
        def fit(self, X, y=None):
            return self

        def predict(self, X):
            return np.zeros(len(X))

    wrapper = AssuranceWrapper(SimpleModel(), policy="some_policy.yaml")
    df = pd.DataFrame({"target": [1, 0], "A": [0.5, 0.6]})

    with patch.object(wrapper, "_upload_policy_artifacts", side_effect=RuntimeError("upload error")):
        with patch("venturalitica.enforce", return_value=[]):
            wrapper.fit(df, target="target")

    captured = capsys.readouterr()
    assert "Regulatory Versioning Warning" in captured.out


def test_find_dataframe_in_kwargs(tmp_path):
    """Lines 112-113: _find_dataframe finds DataFrame in kwargs."""
    os.chdir(tmp_path)

    class SimpleModel:
        def fit(self, data=None):
            return self

        def predict(self, X):
            return np.zeros(len(X))

    wrapper = AssuranceWrapper(SimpleModel())
    df = pd.DataFrame({"a": [1, 2]})

    found = wrapper._find_dataframe((), {"data": df})
    assert found is df


def test_find_dataframe_in_args(tmp_path):
    """Lines 116-118: _find_dataframe finds DataFrame in positional args."""
    os.chdir(tmp_path)

    wrapper = AssuranceWrapper.__new__(AssuranceWrapper)
    df = pd.DataFrame({"a": [1, 2]})

    found = wrapper._find_dataframe([df], {})
    assert found is df


def test_find_dataframe_returns_none(tmp_path):
    """_find_dataframe returns None when no DataFrame found."""
    os.chdir(tmp_path)

    wrapper = AssuranceWrapper.__new__(AssuranceWrapper)
    found = wrapper._find_dataframe([np.array([1, 2])], {"x": 42})
    assert found is None


def test_save_run_metadata_captures_info(tmp_path):
    """Lines 124-144: _save_run_metadata captures model class, data info, audit results."""
    os.chdir(tmp_path)

    class TrackableModel:
        def fit(self, X, y=None):
            return self

        def predict(self, X):
            return np.zeros(len(X))

        def get_params(self, deep=True):
            return {"n_estimators": 100, "max_depth": 5}

    model = TrackableModel()
    wrapper = AssuranceWrapper(model)
    wrapper.last_audit_results = []

    df = pd.DataFrame({"target": [1, 0], "feature": [0.5, 0.6]})
    wrapper._save_run_metadata(df, {})

    meta_path = ".venturalitica/latest_run.json"
    assert os.path.exists(meta_path)
    with open(meta_path, "r") as f:
        meta = json.load(f)

    assert meta["model"]["class"] == "TrackableModel"
    assert meta["data"]["rows"] == 2
    assert "target" in meta["data"]["columns"]
    assert meta["model"]["params"]["n_estimators"] == 100


def test_save_run_metadata_without_get_params(tmp_path):
    """Lines 147-148: _save_run_metadata works when model has no get_params."""
    os.chdir(tmp_path)

    class MinimalModel:
        def fit(self, X, y=None):
            return self

        def predict(self, X):
            return np.zeros(len(X))

    wrapper = AssuranceWrapper(MinimalModel())
    wrapper.last_audit_results = []

    df = pd.DataFrame({"a": [1]})
    wrapper._save_run_metadata(df, {})

    with open(".venturalitica/latest_run.json", "r") as f:
        meta = json.load(f)

    assert "params" not in meta["model"]


def test_save_run_metadata_mlflow_integration(tmp_path):
    """Lines 165-188: _save_run_metadata captures MLflow integration info."""
    os.chdir(tmp_path)

    class SimpleModel:
        def fit(self, X, y=None):
            return self

        def predict(self, X):
            return np.zeros(len(X))

    wrapper = AssuranceWrapper(SimpleModel())
    wrapper.last_audit_results = []

    mock_run = MagicMock()
    mock_run.info.run_id = "run-123"
    mock_run.info.experiment_id = "exp-456"

    # Patch mlflow as an importable module with active_run
    mock_mlflow = MagicMock()
    mock_mlflow.active_run.return_value = mock_run
    mock_mlflow.get_tracking_uri.return_value = "http://localhost:5000"

    df = pd.DataFrame({"a": [1]})

    with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
        wrapper._save_run_metadata(df, {})

    with open(".venturalitica/latest_run.json", "r") as f:
        meta = json.load(f)

    assert "integrations" in meta
    assert "mlflow" in meta["integrations"]
    assert meta["integrations"]["mlflow"]["run_id"] == "run-123"
    assert meta["integrations"]["mlflow"]["active"] is True


def test_save_run_metadata_wandb_integration(tmp_path):
    """Lines 191-203: _save_run_metadata captures WandB integration info."""
    os.chdir(tmp_path)

    class SimpleModel:
        def fit(self, X, y=None):
            return self

        def predict(self, X):
            return np.zeros(len(X))

    wrapper = AssuranceWrapper(SimpleModel())
    wrapper.last_audit_results = []

    mock_run = MagicMock()
    mock_run.url = "https://wandb.ai/test/run-123"
    mock_run.project = "test-project"
    mock_run.entity = "test-entity"

    mock_wandb = MagicMock()
    mock_wandb.run = mock_run

    # Need to also mock mlflow to NOT have an active run
    mock_mlflow = MagicMock()
    mock_mlflow.active_run.return_value = None

    df = pd.DataFrame({"a": [1]})

    with patch.dict("sys.modules", {"mlflow": mock_mlflow, "wandb": mock_wandb}):
        wrapper._save_run_metadata(df, {})

    with open(".venturalitica/latest_run.json", "r") as f:
        meta = json.load(f)

    assert "integrations" in meta
    assert "wandb" in meta["integrations"]
    assert meta["integrations"]["wandb"]["run_url"] == "https://wandb.ai/test/run-123"
    assert meta["integrations"]["wandb"]["project"] == "test-project"


def test_upload_policy_artifacts_no_policy(tmp_path):
    """Lines 215-216: _upload_policy_artifacts returns early when no policy set."""
    os.chdir(tmp_path)

    class SimpleModel:
        def fit(self, X, y=None):
            return self

        def predict(self, X):
            return np.zeros(len(X))

    wrapper = AssuranceWrapper(SimpleModel(), policy=None)
    # Should not raise - just returns early
    wrapper._upload_policy_artifacts()


def test_upload_policy_artifacts_mlflow_path(tmp_path):
    """Lines 223-236: _upload_policy_artifacts logs to MLflow when active."""
    os.chdir(tmp_path)

    # Create a real policy file
    policy_path = tmp_path / "test_policy.yaml"
    policy_path.write_text("title: Test\ncontrols: []\n")

    class SimpleModel:
        def fit(self, X, y=None):
            return self

        def predict(self, X):
            return np.zeros(len(X))

    wrapper = AssuranceWrapper(SimpleModel(), policy=str(policy_path))

    mock_mlflow = MagicMock()
    mock_mlflow.active_run.return_value = MagicMock()

    with patch.dict("sys.modules", {"mlflow": mock_mlflow}):
        wrapper._upload_policy_artifacts()

    mock_mlflow.log_artifact.assert_called_once_with(str(policy_path), artifact_path="policy_snapshot")


def test_upload_policy_artifacts_wandb_path(tmp_path):
    """Lines 241-254: _upload_policy_artifacts logs to WandB when active."""
    os.chdir(tmp_path)

    policy_path = tmp_path / "test_policy.yaml"
    policy_path.write_text("title: Test\ncontrols: []\n")

    class SimpleModel:
        def fit(self, X, y=None):
            return self

        def predict(self, X):
            return np.zeros(len(X))

    wrapper = AssuranceWrapper(SimpleModel(), policy=str(policy_path))

    mock_artifact = MagicMock()
    mock_wandb = MagicMock()
    mock_wandb.run = MagicMock()  # truthy
    mock_wandb.Artifact.return_value = mock_artifact

    # Also mock mlflow to NOT be active
    mock_mlflow = MagicMock()
    mock_mlflow.active_run.return_value = None

    with patch.dict("sys.modules", {"mlflow": mock_mlflow, "wandb": mock_wandb}):
        wrapper._upload_policy_artifacts()

    mock_wandb.Artifact.assert_called_once_with("policy_snapshot", type="assurance")
    mock_artifact.add_file.assert_called_once_with(str(policy_path))
    mock_wandb.log_artifact.assert_called_once_with(mock_artifact)


def test_upload_policy_artifacts_mlflow_import_error(tmp_path):
    """Lines 235-236: _upload_policy_artifacts handles MLflow ImportError gracefully."""
    os.chdir(tmp_path)

    policy_path = tmp_path / "test_policy.yaml"
    policy_path.write_text("title: Test\ncontrols: []\n")

    class SimpleModel:
        def fit(self, X, y=None):
            return self

        def predict(self, X):
            return np.zeros(len(X))

    wrapper = AssuranceWrapper(SimpleModel(), policy=str(policy_path))

    # Simulate MLflow not installed
    import sys

    original_modules = sys.modules.copy()
    sys.modules["mlflow"] = None  # This will cause ImportError on import

    try:
        # Should not raise
        with patch.dict("sys.modules", {"mlflow": None, "wandb": None}):
            wrapper._upload_policy_artifacts()
    finally:
        pass  # No cleanup needed with patch.dict context manager


def test_predict_with_post_audit(tmp_path):
    """Lines 87-106: predict triggers post-audit with prediction injected."""
    os.chdir(tmp_path)

    class PredModel:
        def fit(self, X, y=None):
            return self

        def predict(self, X):
            return np.array([1, 0])

    wrapper = AssuranceWrapper(PredModel())

    df = pd.DataFrame({"target": [1, 0], "feature": [0.5, 0.6]})

    with patch("venturalitica.enforce", return_value=[]) as mock_enforce:
        result = wrapper.predict(df, audit_data=df, target="target")

    assert len(result) == 2
    # enforce should have been called with data_with_pred that has 'prediction' column
    mock_enforce.assert_called_once()
    call_kwargs = mock_enforce.call_args[1]
    assert "data" in call_kwargs
    assert "prediction" in call_kwargs["data"].columns


def test_predict_with_custom_pred_col(tmp_path):
    """Lines 99-100: predict uses custom prediction column name from audit_kwargs."""
    os.chdir(tmp_path)

    class PredModel:
        def fit(self, X, y=None):
            return self

        def predict(self, X):
            return np.array([1, 0])

    wrapper = AssuranceWrapper(PredModel())
    df = pd.DataFrame({"target": [1, 0], "feature": [0.5, 0.6]})

    with patch("venturalitica.enforce", return_value=[]) as mock_enforce:
        result = wrapper.predict(df, audit_data=df, prediction="my_pred")

    mock_enforce.assert_called_once()
    call_kwargs = mock_enforce.call_args[1]
    # The prediction column should be named "my_pred"
    assert "my_pred" in call_kwargs["data"].columns


def test_wrap_function_emits_warning():
    """wrap() should emit a UserWarning about experimental status."""

    class DummyModel:
        def fit(self, X, y):
            return self

        def predict(self, X):
            return X

    import warnings

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        wrapped = wrap(DummyModel())
        assert len(w) == 1
        assert "experimental" in str(w[0].message).lower()
