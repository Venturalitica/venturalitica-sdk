import pytest
import yaml
import tempfile
import os
import pandas as pd
from unittest.mock import patch, MagicMock
from venturalitica.core import GovernanceValidator, ComplianceResult
from venturalitica.models import InternalPolicy, InternalControl

@pytest.fixture
def mock_policy_file():
    policy_data = {
        'assessment-plan': {
            'metadata': {'title': 'Test Policy'},
            'local-definitions': {
                'inventory-items': [
                    {
                        'uuid': 'm1',
                        'props': [
                            {'name': 'metric_key', 'value': 'accuracy_score'},
                            {'name': 'threshold', 'value': '0.8'},
                            {'name': 'operator', 'value': '>='},
                            {'name': 'input:target', 'value': 'target'},
                            {'name': 'input:prediction', 'value': 'prediction'}
                        ]
                    },
                    {
                        'uuid': 'm2',
                        'props': [
                            {'name': 'metric_key', 'value': 'disparate_impact'},
                            {'name': 'threshold', 'value': '0.8'},
                            {'name': 'operator', 'value': '>'}, # > 0.8 is good
                            {'name': 'input:target', 'value': 'target'},
                            {'name': 'input:prediction', 'value': 'prediction'},
                            {'name': 'input:dimension', 'value': 'sensitive'}
                        ]
                    }
                ]
            },
            'control-implementations': [
                {
                    'implemented-requirements': [
                        {
                            'control-id': 'C1',
                            'description': 'High Accuracy',
                            'props': [{'name': 'severity', 'value': 'high'}],
                            'links': [{'href': '#m1'}]
                        },
                        {
                            'control-id': 'C2',
                            'links': [{'href': '#m2'}]
                        }
                    ]
                }
            ]
        }
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.oscal.yaml', delete=False) as f:
        yaml.dump(policy_data, f)
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)

def test_validator_loading(mock_policy_file):
    validator = GovernanceValidator(mock_policy_file)
    assert len(validator.controls) == 2
    assert validator.controls[0]['metric_key'] == 'accuracy_score'
    assert validator.controls[0]['severity'] == 'high'
    assert validator.controls[1]['severity'] == 'low'

def test_missing_policy():
    with pytest.raises(FileNotFoundError):
        GovernanceValidator("missing.oscal.yaml")

def test_validator_no_policy():
    with patch("venturalitica.core.LocalFileSystemStorage.get_policy", return_value=None):
        validator = GovernanceValidator("any.yaml")
        assert validator.controls == []

@pytest.fixture
def mock_single_control_policy():
    policy_data = {
        'catalog': {
            'metadata': {'title': 'Single Control'},
            'controls': [
                {
                    'id': 'C1',
                    'props': [
                        {'name': 'metric_key', 'value': 'accuracy_score'},
                        {'name': 'threshold', 'value': '0.8'}
                    ]
                }
            ]
        }
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.oscal.yaml', delete=False) as f:
        yaml.dump(policy_data, f)
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)

def test_compute_and_evaluate_value_error(mock_single_control_policy):
    validator = GovernanceValidator(mock_single_control_policy)
    from venturalitica.metrics import METRIC_REGISTRY
    df = pd.DataFrame({'a': [1]})
    mapping = {'target': 'a'}
    
    with patch.dict(METRIC_REGISTRY, {"accuracy_score": MagicMock(side_effect=ValueError)}):
        results = validator.compute_and_evaluate(df, mapping)
        assert results == []

def test_compute_and_evaluate_unexpected_error(mock_single_control_policy, capsys):
    validator = GovernanceValidator(mock_single_control_policy)
    from venturalitica.metrics import METRIC_REGISTRY
    df = pd.DataFrame({'a': [1]})
    mapping = {'target': 'a'}
    
    with patch.dict(METRIC_REGISTRY, {"accuracy_score": MagicMock(side_effect=RuntimeError("Unexpected"))}):
        validator.compute_and_evaluate(df, mapping)
    
    captured = capsys.readouterr()
    assert "Unexpected error" in captured.out

def test_operators():
    v = GovernanceValidator.__new__(GovernanceValidator)
    assert v._check_condition(1.0, '>', 0.5) is True
    assert v._check_condition(0.5, '>', 0.5) is False
    assert v._check_condition(0.4, '<', 0.5) is True
    assert v._check_condition(0.5, '<=', 0.5) is True
    assert v._check_condition(0.6, '>=', 0.5) is True
    assert v._check_condition(0.5, '==', 0.5) is True
    assert v._check_condition(0.6, '==', 0.5) is False
    assert v._check_condition(0.6, '!=', 0.5) is True
    assert v._check_condition(0.5, 'invalid', 0.5) is False

def test_compute_and_evaluate(mock_policy_file):
    validator = GovernanceValidator(mock_policy_file)
    df = pd.DataFrame({
        't': [1, 1, 0, 0], 
        'p': [1, 1, 0, 0],
        's': ['A', 'B', 'A', 'B']  # Balanced: Both A and B have 1 pos, 1 neg
    })
    
    # mapping maps Variable Names (from policy) to Actual Columns (in df)
    mapping = {'target': 't', 'prediction': 'p', 'sensitive': 's'}
    results = validator.compute_and_evaluate(df, mapping)
    
    assert len(results) == 2
    assert results[0].metric_key == 'accuracy_score'
    assert results[0].passed == True
    assert results[1].metric_key == 'disparate_impact'
    assert results[1].passed == True

def test_evaluate_precomputed(mock_policy_file):
    validator = GovernanceValidator(mock_policy_file)
    results = validator.evaluate({'accuracy_score': 0.7, 'disparate_impact': 0.5, 'other': 1.0})
    
    assert len(results) == 2
    assert results[0].passed == False # 0.7 >= 0.8
    assert results[1].passed == False # 0.5 > 0.8

def test_compute_and_evaluate_invalid_data():
    v = GovernanceValidator.__new__(GovernanceValidator)
    with pytest.raises(ValueError, match="Data must be a pandas DataFrame"):
        v.compute_and_evaluate("not a dataframe", {})

def test_unknown_metric(mock_policy_file):
    validator = GovernanceValidator(mock_policy_file)
    # Inject an unknown metric control into the policy object
    validator.policy.controls.append(InternalControl(
        id='U1', description='U', severity='low',
        metric_key='unknown_metric', threshold=1.0, operator='>'
    ))
    results = validator.compute_and_evaluate(pd.DataFrame({'a': [1]}), {})
    assert not any(r.control_id == 'U1' for r in results)

def test_unexpected_error_eval(mock_policy_file):
    validator = GovernanceValidator(mock_policy_file)
    from venturalitica.metrics import METRIC_REGISTRY
    with patch.dict(METRIC_REGISTRY, {'accuracy_score': MagicMock(side_effect=RuntimeError("Serious"))}):
        validator.compute_and_evaluate(pd.DataFrame({'t': [1], 'p': [1]}), {'target': 't', 'prediction': 'p'})

def test_evaluate_missing_metric(mock_policy_file):
    validator = GovernanceValidator(mock_policy_file)
    results = validator.evaluate({'some_other': 1.0})
    assert len(results) == 0
