import os
import tempfile
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import yaml

from venturalitica.core import AssuranceValidator
from venturalitica.models import InternalControl, InternalPolicy


@pytest.fixture
def mock_policy_file():
    policy_data = {
        "assessment-plan": {
            "metadata": {"title": "Test Policy"},
            "local-definitions": {
                "inventory-items": [
                    {
                        "uuid": "m1",
                        "props": [
                            {"name": "metric_key", "value": "accuracy_score"},
                            {"name": "threshold", "value": "0.8"},
                            {"name": "operator", "value": ">="},
                            {"name": "input:target", "value": "target"},
                            {"name": "input:prediction", "value": "prediction"},
                        ],
                    },
                    {
                        "uuid": "m2",
                        "props": [
                            {"name": "metric_key", "value": "disparate_impact"},
                            {"name": "threshold", "value": "0.8"},
                            {"name": "operator", "value": ">"},  # > 0.8 is good
                            {"name": "input:target", "value": "target"},
                            {"name": "input:prediction", "value": "prediction"},
                            {"name": "input:dimension", "value": "sensitive"},
                        ],
                    },
                ]
            },
            "control-implementations": [
                {
                    "implemented-requirements": [
                        {
                            "control-id": "C1",
                            "description": "High Accuracy",
                            "props": [{"name": "severity", "value": "high"}],
                            "links": [{"href": "#m1"}],
                        },
                        {"control-id": "C2", "links": [{"href": "#m2"}]},
                    ]
                }
            ],
        }
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".oscal.yaml", delete=False) as f:
        yaml.dump(policy_data, f)
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


def test_validator_loading(mock_policy_file):
    validator = AssuranceValidator(mock_policy_file)
    assert len(validator.controls) == 2
    assert validator.controls[0]["metric_key"] == "accuracy_score"
    assert validator.controls[0]["severity"] == "high"
    assert validator.controls[1]["severity"] == "low"


def test_missing_policy():
    with pytest.raises(FileNotFoundError):
        AssuranceValidator("missing.oscal.yaml")


def test_validator_no_policy():
    with patch("venturalitica.core.LocalFileSystemStorage.get_policy", return_value=None):
        validator = AssuranceValidator("any.yaml")
        assert validator.controls == []


@pytest.fixture
def mock_single_control_policy():
    policy_data = {
        "catalog": {
            "metadata": {"title": "Single Control"},
            "controls": [
                {
                    "id": "C1",
                    "props": [
                        {"name": "metric_key", "value": "accuracy_score"},
                        {"name": "threshold", "value": "0.8"},
                    ],
                }
            ],
        }
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".oscal.yaml", delete=False) as f:
        yaml.dump(policy_data, f)
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


def test_compute_and_evaluate_value_error(mock_single_control_policy):
    validator = AssuranceValidator(mock_single_control_policy)
    from venturalitica.metrics import METRIC_REGISTRY

    df = pd.DataFrame({"a": [1]})
    mapping = {"target": "a"}

    with patch.dict(METRIC_REGISTRY, {"accuracy_score": MagicMock(side_effect=ValueError)}):
        results = validator.compute_and_evaluate(df, mapping)
        assert results == []


def test_compute_and_evaluate_unexpected_error(mock_single_control_policy, capsys):
    validator = AssuranceValidator(mock_single_control_policy)
    from venturalitica.metrics import METRIC_REGISTRY

    df = pd.DataFrame({"a": [1], "b": [1]})
    mapping = {"target": "a", "prediction": "b"}

    with patch.dict(
        METRIC_REGISTRY,
        {"accuracy_score": MagicMock(side_effect=RuntimeError("Unexpected"))},
    ):
        validator.compute_and_evaluate(df, mapping)

    captured = capsys.readouterr()
    assert any(x in captured.out for x in ["Unexpected error", "Error computing", "Error evaluating"])


def test_operators():
    v = AssuranceValidator.__new__(AssuranceValidator)
    assert v._check_condition(1.0, ">", 0.5) is True
    assert v._check_condition(0.5, ">", 0.5) is False
    assert v._check_condition(0.4, "<", 0.5) is True
    assert v._check_condition(0.5, "<=", 0.5) is True
    assert v._check_condition(0.6, ">=", 0.5) is True
    assert v._check_condition(0.5, "==", 0.5) is True
    assert v._check_condition(0.6, "==", 0.5) is False
    assert v._check_condition(0.6, "!=", 0.5) is True
    assert v._check_condition(0.5, "invalid", 0.5) is False


def test_compute_and_evaluate(mock_policy_file):
    validator = AssuranceValidator(mock_policy_file)
    df = pd.DataFrame(
        {
            "t": [1, 1, 0, 0],
            "p": [1, 1, 0, 0],
            "s": ["A", "B", "A", "B"],  # Balanced: Both A and B have 1 pos, 1 neg
        }
    )

    # mapping maps Variable Names (from policy) to Actual Columns (in df)
    mapping = {"target": "t", "prediction": "p", "sensitive": "s"}
    results = validator.compute_and_evaluate(df, mapping)

    assert len(results) == 2
    assert results[0].metric_key == "accuracy_score"
    assert results[0].passed
    assert results[1].metric_key == "disparate_impact"
    assert results[1].passed


def test_evaluate_precomputed(mock_policy_file):
    validator = AssuranceValidator(mock_policy_file)
    results = validator.evaluate({"accuracy_score": 0.7, "disparate_impact": 0.5, "other": 1.0})

    assert len(results) == 2
    assert not results[0].passed  # 0.7 >= 0.8
    assert not results[1].passed  # 0.5 > 0.8


def test_compute_and_evaluate_invalid_data():
    v = AssuranceValidator.__new__(AssuranceValidator)
    v.strict = False
    with pytest.raises(ValueError, match="Data must be a pandas DataFrame"):
        v.compute_and_evaluate("not a dataframe", {})


def test_unknown_metric(mock_policy_file):
    validator = AssuranceValidator(mock_policy_file)
    # Inject an unknown metric control into the policy object
    validator.policy.controls.append(
        InternalControl(
            id="U1",
            description="U",
            severity="low",
            metric_key="unknown_metric",
            threshold=1.0,
            operator=">",
        )
    )
    results = validator.compute_and_evaluate(pd.DataFrame({"a": [1]}), {})
    assert not any(r.control_id == "U1" for r in results)


def test_unexpected_error_eval(mock_policy_file):
    validator = AssuranceValidator(mock_policy_file)
    from venturalitica.metrics import METRIC_REGISTRY

    with patch.dict(
        METRIC_REGISTRY,
        {"accuracy_score": MagicMock(side_effect=RuntimeError("Serious"))},
    ):
        validator.compute_and_evaluate(pd.DataFrame({"t": [1], "p": [1]}), {"target": "t", "prediction": "p"})


def test_evaluate_missing_metric(mock_policy_file):
    validator = AssuranceValidator(mock_policy_file)
    results = validator.evaluate({"some_other": 1.0})
    assert len(results) == 0


def test_core_resolve_col_names_synonyms(tmp_path):
    # This targets core.py resolve_col_names and loader.py branches
    policy_dict = {
        "assessment-plan": {
            "reviewed-controls": {
                "control-implementations": [
                    {
                        "implemented-requirements": [
                            {
                                "control-id": "AC-1",
                                "description": "Accuracy check",
                                "props": [
                                    {"name": "metric_key", "value": "accuracy_score"},
                                    {"name": "threshold", "value": "0.5"},
                                    {"name": "operator", "value": "ge"},
                                    {"name": "input:target", "value": "class"},
                                    {
                                        "name": "input:dimension",
                                        "value": "gender",
                                    },  # gender -> Attribute9
                                ],
                            }
                        ]
                    }
                ]
            }
        }
    }

    path = tmp_path / "synonym_policy.yaml"
    with open(path, "w") as f:
        yaml.dump(policy_dict, f)

    # y=class, y_pred=pred
    df = pd.DataFrame(
        {
            "Attribute9": [1, 0, 1, 0],
            "Attribute13": [30, 40, 25, 35],
            "class": [1, 0, 1, 0],
            "pred": [1, 0, 1, 1],
        }
    )
    from venturalitica import enforce

    results = enforce(data=df, policy=str(path))
    assert len(results) > 0
    assert results[0].passed is True


def test_core_results_processing():
    from venturalitica.loader import OSCALPolicyLoader

    # Test with a simple dict policy using standard hyphenated keys
    policy_data = {
        "assessment-plan": {
            "control-implementations": [
                {
                    "implemented-requirements": [
                        {
                            "control-id": "AC-1",
                            "description": "Accuracy test",
                            "props": [
                                {"name": "metric", "value": "accuracy_score"},
                                {"name": "threshold", "value": "0.5"},
                                {"name": "operator", "value": "ge"},
                            ],
                        }
                    ]
                }
            ]
        }
    }
    loader = OSCALPolicyLoader(policy_data)
    policy = loader.load()

    validator = AssuranceValidator(policy)
    df = pd.DataFrame({"target": [0, 1], "prediction": [0, 1]})

    # Evaluate
    results = validator.compute_and_evaluate(df, {"target": "target", "prediction": "prediction"})
    assert len(results) >= 1
    assert results[0].control_id == "AC-1"
    assert results[0].passed is True


# ──────────────────────────────────────────────────────────────────────
# Additional coverage tests appended below
# ──────────────────────────────────────────────────────────────────────


def test_strict_mode_ci_env(monkeypatch, tmp_path):
    """Line 21-23: CI=true triggers strict mode auto-detection."""
    monkeypatch.setenv("CI", "true")
    monkeypatch.delenv("VENTURALITICA_STRICT", raising=False)

    policy = InternalPolicy(title="Empty", controls=[])
    validator = AssuranceValidator(policy, strict=False)
    assert validator.strict is True


def test_strict_mode_env_var(monkeypatch, tmp_path):
    """Line 21-23: VENTURALITICA_STRICT=true triggers strict mode."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("VENTURALITICA_STRICT", "true")

    policy = InternalPolicy(title="Empty", controls=[])
    validator = AssuranceValidator(policy, strict=False)
    assert validator.strict is True


def test_strict_mode_not_set(monkeypatch):
    """Verify strict is False when env vars are absent."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("VENTURALITICA_STRICT", raising=False)

    policy = InternalPolicy(title="Empty", controls=[])
    validator = AssuranceValidator(policy, strict=False)
    assert validator.strict is False


def test_load_policy_from_internal_policy(monkeypatch):
    """Line 47-48: Pass InternalPolicy directly to the constructor."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("VENTURALITICA_STRICT", raising=False)

    ctrl = InternalControl(
        id="D1",
        description="Direct",
        severity="low",
        metric_key="accuracy_score",
        threshold=0.5,
        operator="ge",
    )
    policy = InternalPolicy(title="Direct Policy", controls=[ctrl])
    validator = AssuranceValidator(policy)
    assert validator.policy is policy
    assert len(validator.controls) == 1
    assert validator.controls[0]["metric_key"] == "accuracy_score"


def test_load_policy_from_dict(monkeypatch):
    """Lines 49-53: Pass a raw dict to the constructor."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("VENTURALITICA_STRICT", raising=False)

    policy_dict = {
        "assessment-plan": {
            "control-implementations": [
                {
                    "implemented-requirements": [
                        {
                            "control-id": "DD-1",
                            "description": "Dict-based control",
                            "props": [
                                {"name": "metric_key", "value": "accuracy_score"},
                                {"name": "threshold", "value": "0.7"},
                                {"name": "operator", "value": "ge"},
                            ],
                        }
                    ]
                }
            ]
        }
    }
    validator = AssuranceValidator(policy_dict)
    assert len(validator.controls) == 1
    assert validator.controls[0]["id"] == "DD-1"


def test_word_form_operators():
    """Lines 326-337: Test word-form operators lt, gt, le, ge, eq, ne."""
    v = AssuranceValidator.__new__(AssuranceValidator)
    assert v._check_condition(0.4, "lt", 0.5) is True
    assert v._check_condition(0.5, "lt", 0.5) is False
    assert v._check_condition(0.6, "gt", 0.5) is True
    assert v._check_condition(0.5, "gt", 0.5) is False
    assert v._check_condition(0.5, "le", 0.5) is True
    assert v._check_condition(0.6, "le", 0.5) is False
    assert v._check_condition(0.5, "ge", 0.5) is True
    assert v._check_condition(0.4, "ge", 0.5) is False
    assert v._check_condition(0.5, "eq", 0.5) is True
    assert v._check_condition(0.6, "eq", 0.5) is False
    assert v._check_condition(0.6, "ne", 0.5) is True
    assert v._check_condition(0.5, "ne", 0.5) is False


def test_resolve_col_names_with_string_splitting(monkeypatch):
    """Lines 218-250: resolve_col_names with comma-separated string input."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("VENTURALITICA_STRICT", raising=False)

    # Build a policy that uses quasi_identifiers param with comma-separated string
    policy = InternalPolicy(
        title="QI Test",
        controls=[
            InternalControl(
                id="QI-1",
                description="k-anon check",
                severity="low",
                metric_key="k_anonymity",
                threshold=2.0,
                operator="ge",
                input_mapping={},
                params={"quasi_identifiers": "age, gender"},
            )
        ],
    )
    validator = AssuranceValidator(policy)
    df = pd.DataFrame(
        {
            "age": [25, 25, 30, 30],
            "gender": ["M", "M", "F", "F"],
            "salary": [100, 200, 150, 250],
        }
    )
    results = validator.compute_and_evaluate(df, {})
    assert len(results) == 1
    assert results[0].metric_key == "k_anonymity"


def test_resolve_col_names_with_list(monkeypatch):
    """Lines 221-222: resolve_col_names with list input."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("VENTURALITICA_STRICT", raising=False)

    policy = InternalPolicy(
        title="QI List Test",
        controls=[
            InternalControl(
                id="QI-2",
                description="k-anon list",
                severity="low",
                metric_key="k_anonymity",
                threshold=2.0,
                operator="ge",
                input_mapping={},
                params={"quasi_identifiers": ["age", "gender"]},
            )
        ],
    )
    validator = AssuranceValidator(policy)
    df = pd.DataFrame(
        {
            "age": [25, 25, 30, 30],
            "gender": ["M", "M", "F", "F"],
            "salary": [100, 200, 150, 250],
        }
    )
    results = validator.compute_and_evaluate(df, {})
    assert len(results) == 1
    assert results[0].metric_key == "k_anonymity"


def test_resolve_col_names_lowercase_fallback(monkeypatch):
    """Lines 245-246: resolve_col_names lowercase fallback when synonym not found."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("VENTURALITICA_STRICT", raising=False)

    # Use a column name that isn't in synonyms but whose lowercase exists in the df
    policy = InternalPolicy(
        title="Lowercase Test",
        controls=[
            InternalControl(
                id="LC-1",
                description="k-anon lowercase",
                severity="low",
                metric_key="k_anonymity",
                threshold=1.0,
                operator="ge",
                input_mapping={},
                params={"quasi_identifiers": "City, Zipcode"},
            )
        ],
    )
    validator = AssuranceValidator(policy)
    # Columns are lowercase versions of the param values
    df = pd.DataFrame(
        {
            "city": ["NY", "NY", "LA", "LA"],
            "zipcode": ["10001", "10001", "90001", "90001"],
            "salary": [100, 200, 150, 250],
        }
    )
    results = validator.compute_and_evaluate(df, {})
    assert len(results) == 1


def test_tuple_metric_result(monkeypatch):
    """Lines 263-264: metric returning (value, metadata) tuple is unpacked."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("VENTURALITICA_STRICT", raising=False)

    def fake_metric(data, **kwargs):
        return (0.95, {"stability": "high", "n_samples": 100})

    policy = InternalPolicy(
        title="Tuple Test",
        controls=[
            InternalControl(
                id="TM-1",
                description="Tuple metric",
                severity="low",
                metric_key="fake_tuple_metric",
                threshold=0.9,
                operator="ge",
            )
        ],
    )
    validator = AssuranceValidator(policy)
    df = pd.DataFrame({"a": [1, 2, 3]})

    from venturalitica.metrics import METRIC_REGISTRY

    with patch.dict(METRIC_REGISTRY, {"fake_tuple_metric": fake_metric}):
        results = validator.compute_and_evaluate(df, {})
    assert len(results) == 1
    assert results[0].actual_value == 0.95
    assert results[0].metadata == {"stability": "high", "n_samples": 100}
    assert results[0].passed is True


def test_static_param_average(monkeypatch):
    """Lines 107-110: input_mapping 'average' role treated as static parameter."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("VENTURALITICA_STRICT", raising=False)

    def fake_metric_with_average(data, target=None, prediction=None, average=None, **kwargs):
        # The metric receives average as a kwarg, not a column name
        assert average == "macro"
        return 0.85

    policy = InternalPolicy(
        title="Average Test",
        controls=[
            InternalControl(
                id="AVG-1",
                description="With average param",
                severity="low",
                metric_key="fake_avg_metric",
                threshold=0.5,
                operator="ge",
                input_mapping={
                    "average": "macro",
                    "target": "target",
                    "prediction": "prediction",
                },
            )
        ],
    )
    validator = AssuranceValidator(policy)
    df = pd.DataFrame({"target": [0, 1, 1], "prediction": [0, 1, 0]})

    from venturalitica.metrics import METRIC_REGISTRY

    with patch.dict(METRIC_REGISTRY, {"fake_avg_metric": fake_metric_with_average}):
        results = validator.compute_and_evaluate(df, {"target": "target", "prediction": "prediction"})
    assert len(results) == 1
    assert results[0].actual_value == 0.85


def test_quasi_identifiers_resolution(monkeypatch):
    """Lines 252-258: resolved_params for quasi_identifiers and sensitive_columns."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("VENTURALITICA_STRICT", raising=False)

    captured_kwargs = {}

    def capturing_metric(data, **kwargs):
        captured_kwargs.update(kwargs)
        return 3.0

    policy = InternalPolicy(
        title="Params Test",
        controls=[
            InternalControl(
                id="P-1",
                description="Params resolution",
                severity="low",
                metric_key="capturing_metric",
                threshold=1.0,
                operator="ge",
                input_mapping={},
                params={
                    "quasi_identifiers": "age, gender",
                    "sensitive_columns": ["salary"],
                    "some_other_param": "keep_as_is",
                },
            )
        ],
    )
    validator = AssuranceValidator(policy)
    df = pd.DataFrame(
        {
            "age": [25, 30],
            "gender": ["M", "F"],
            "salary": [100, 200],
        }
    )

    from venturalitica.metrics import METRIC_REGISTRY

    with patch.dict(METRIC_REGISTRY, {"capturing_metric": capturing_metric}):
        results = validator.compute_and_evaluate(df, {})

    assert len(results) == 1
    # quasi_identifiers should be resolved to a list of actual column names
    assert isinstance(captured_kwargs["quasi_identifiers"], list)
    assert "age" in captured_kwargs["quasi_identifiers"]
    assert "gender" in captured_kwargs["quasi_identifiers"]
    # sensitive_columns should also be resolved
    assert isinstance(captured_kwargs["sensitive_columns"], list)
    assert "salary" in captured_kwargs["sensitive_columns"]
    # non-column params stay as-is
    assert captured_kwargs["some_other_param"] == "keep_as_is"
