import pytest
import pandas as pd
import yaml
import tempfile
import os
from venturalitica import enforce

@pytest.fixture
def mock_policy():
    policy = {
        'assessment-plan': {
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
                    }
                ]
            },
            'control-implementations': [
                {
                    'implemented-requirements': [
                        {
                            'control-id': 'C1',
                            'description': 'test',
                            'links': [{'href': '#m1', 'rel': 'related'}]
                        }
                    ]
                }
            ]
        }
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(policy, f)
        path = f.name
    yield path
    os.unlink(path)

def test_enforce_with_data(mock_policy):
    df = pd.DataFrame({'t': [1, 1], 'p': [1, 1]})
    # Note: target='t' maps the variable 'target' to column 't'
    results = enforce(data=df, policy=mock_policy, target='t', prediction='p')
    assert len(results) == 1
    assert results[0].passed is True

def test_enforce_with_metrics(mock_policy):
    results = enforce(metrics={'accuracy_score': 0.9}, policy=mock_policy)
    assert len(results) == 1
    assert results[0].passed is True

def test_enforce_no_input(mock_policy):
    results = enforce(policy=mock_policy)
    assert results == []

def test_enforce_no_results(mock_policy):
    # Policy with metric but we provide data without required columns
    df = pd.DataFrame({'a': [1]})
    results = enforce(data=df, policy=mock_policy)
    # Since columns are missing, calc_accuracy returns 0.0, and it FAILS the control
    assert len(results) == 1
    assert results[0].passed is False

def test_enforce_file_not_found():
    results = enforce(metrics={'a': 1}, policy="nonexistent.yaml")
    assert results == []

def test_enforce_exception(mock_policy):
    # Pass something that causes an exception in validator
    results = enforce(data="not-a-df", policy=mock_policy)
    assert results == []

def test_enforce_failed_controls(mock_policy):
    results = enforce(metrics={'accuracy_score': 0.1}, policy=mock_policy)
    assert len(results) == 1
    assert results[0].passed is False

def test_enforce_data_bias_warning(mock_policy):
    # No prediction -> triggers data bias warning in print
    results = enforce(metrics={'accuracy_score': 0.1}, policy=mock_policy)
    # This just tests it returns the results correctly
    assert len(results) == 1
