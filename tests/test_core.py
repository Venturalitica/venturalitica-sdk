import pytest
import yaml
import tempfile
import os
import pandas as pd
from unittest.mock import patch, MagicMock
from venturalitica.core import GovernanceValidator, ComplianceResult

@pytest.fixture
def mock_policy_file():
    policy_data = {
        'assessment-plan': {
            'local-definitions': {
                'inventory-items': [
                    {
                        'description': 'Malformed Item',
                        'props': []
                    },
                    {
                        'uuid': 'm1',
                        'description': 'Accuracy',
                        'props': [
                            {'name': 'metric_key', 'value': 'accuracy_score'},
                            {'name': 'threshold', 'value': '0.8'},
                            {'name': 'operator', 'value': '>='}
                        ]
                    },
                    {
                        'uuid': 'm2',
                        'description': 'Disparate Impact',
                        'props': [
                            {'name': 'metric_key', 'value': 'disparate_impact'},
                            {'name': 'threshold', 'value': '0.8'},
                            {'name': 'operator', 'value': '<'}
                        ]
                    }
                ]
            },
            'control-implementations': [
                {
                    'implemented-requirements': [
                        {
                            'uuid': 'req1',
                            'control-id': 'C1',
                            'description': 'High Accuracy',
                            'props': [{'name': 'severity', 'value': 'high'}],
                            'links': [{'href': '#m1', 'rel': 'related'}]
                        },
                        {
                            'uuid': 'req2',
                            'control-id': 'C2',
                            'links': [{'href': '#m2', 'rel': 'related'}] # No description, default severity
                        }
                    ]
                }
            ]
        }
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(policy_data, f)
        path = f.name
    yield path
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

def test_malformed_policy():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("invalid: yaml: [")
        path = f.name
    
    try:
        with pytest.raises(Exception): # yaml.YAMLError
             GovernanceValidator(path)
    finally:
        os.unlink(path)

def test_empty_policy():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("")
        path = f.name
    
    validator = GovernanceValidator(path)
    assert len(validator.controls) == 0
    os.unlink(path)

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
        's': ['A', 'A', 'B', 'B']
    })
    
    mapping = {'target': 't', 'prediction': 'p', 'sensitive': 's'}
    results = validator.compute_and_evaluate(df, mapping)
    
    assert len(results) == 2
    # Accuracy is 1.0 >= 0.8 (Pass)
    assert results[0].metric_key == 'accuracy_score'
    assert results[0].passed == True
    # Disparate Impact (A: 1.0, B: 0.0 -> Ratio 0) < 0.8 (Pass)
    assert results[1].metric_key == 'disparate_impact'
    assert results[1].passed == True

def test_evaluate_precomputed(mock_policy_file):
    validator = GovernanceValidator(mock_policy_file)
    results = validator.evaluate({'accuracy_score': 0.7, 'disparate_impact': 0.5, 'other': 1.0})
    
    assert len(results) == 2
    assert results[0].passed == False # 0.7 >= 0.8
    assert results[1].passed == True  # 0.5 < 0.8

def test_compute_and_evaluate_invalid_data():
    v = GovernanceValidator.__new__(GovernanceValidator)
    with pytest.raises(ValueError, match="Data must be a pandas DataFrame"):
        v.compute_and_evaluate("not a dataframe", {})

def test_process_requirement_malformed(mock_policy_file):
    validator = GovernanceValidator(mock_policy_file)
    # Add a malformed control definition manually to test _add_control error handling
    validator._add_control("fail", "fail", "low", {"metric_key": "acc"}) # Missing threshold/operator
    assert not any(c['id'] == "fail" for c in validator.controls)

def test_unknown_metric(mock_policy_file):
    validator = GovernanceValidator(mock_policy_file)
    validator.controls.append({
        'id': 'U1', 'description': 'U', 'severity': 'low',
        'metric_key': 'unknown_metric', 'threshold': 1.0, 'operator': '>'
    })
    results = validator.compute_and_evaluate(pd.DataFrame({'a': [1]}), {})
    assert not any(r.control_id == 'U1' for r in results)

def test_unexpected_error_eval(mock_policy_file):
    validator = GovernanceValidator(mock_policy_file)
    # Patch METRIC_REGISTRY to return a function that crashes
    from venturalitica.metrics import METRIC_REGISTRY
    with patch.dict(METRIC_REGISTRY, {'accuracy_score': MagicMock(side_effect=RuntimeError("Serious"))}):
        # This will hit line 117 in core.py
        validator.compute_and_evaluate(pd.DataFrame({'t': [1], 'p': [1]}), {'target': 't', 'prediction': 'p'})

def test_process_requirement_external_link(mock_policy_file):
    validator = GovernanceValidator(mock_policy_file)
    # Link without # is ignored. 
    # Also test href that DOES NOT start with #
    req = {'control-id': 'EXT', 'links': [{'href': 'http://external'}, {'href': 'no-hash'}]}
    validator._process_requirement(req, {})
    assert not any(c['id'] == 'EXT' for c in validator.controls)

def test_evaluate_missing_metric(mock_policy_file):
    validator = GovernanceValidator(mock_policy_file)
    # 'accuracy_score' is in policy but not in the provided dict
    results = validator.evaluate({'some_other': 1.0})
    assert len(results) == 0
