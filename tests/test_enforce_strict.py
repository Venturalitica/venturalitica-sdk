import tempfile
import yaml
import os
import pandas as pd
from venturalitica import enforce


def test_enforce_strict_missing_metric_raises():
    # Create a policy that references an unknown metric
    policy = {
        'assessment-plan': {
            'local-definitions': {
                'inventory-items': [
                    {
                        'uuid': 'x1',
                        'props': [
                            {'name': 'metric_key', 'value': 'nonexistent_metric'},
                            {'name': 'threshold', 'value': '0.1'},
                            {'name': 'operator', 'value': 'gt'},
                            {'name': 'input:target', 'value': 'target'}
                        ]
                    }
                ]
            },
            'control-implementations': [
                {
                    'implemented-requirements': [
                        {
                            'control-id': 'NM1',
                            'description': 'Unknown metric control',
                            'links': [{'href': '#x1', 'rel': 'related'}]
                        }
                    ]
                }
            ]
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(policy, f)
        path = f.name
    try:
        df = pd.DataFrame({'target': [1, 0]})
        try:
            enforce(data=df, policy=path, target='target', strict=True)
            raise AssertionError('Expected ValueError for missing metric, but enforce returned')
        except ValueError as e:
            assert "No metric function registered" in str(e)
    finally:
        os.unlink(path)


def test_enforce_strict_missing_role_raises():
    # Create a policy which needs a 'dimension' that isn't present in data
    policy = {
        'assessment-plan': {
            'local-definitions': {
                'inventory-items': [
                    {
                        'uuid': 'g1',
                        'props': [
                            {'name': 'metric_key', 'value': 'group_min_positive_rate'},
                            {'name': 'threshold', 'value': '0.5'},
                            {'name': 'operator', 'value': 'gt'},
                            {'name': 'input:target', 'value': 'target'},
                            {'name': 'input:dimension', 'value': 'SomeMissingColumn'}
                        ]
                    }
                ]
            },
            'control-implementations': [
                {
                    'implemented-requirements': [
                        {
                            'control-id': 'GBX',
                            'description': 'Group balance check missing role',
                            'links': [{'href': '#g1', 'rel': 'related'}]
                        }
                    ]
                }
            ]
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(policy, f)
        path = f.name
    try:
        df = pd.DataFrame({'target': [1, 1, 0, 0]})
        try:
            enforce(data=df, policy=path, target='target', strict=True)
            raise AssertionError('Expected ValueError for missing role, but enforce returned')
        except ValueError as e:
            assert "requires" in str(e)
    finally:
        os.unlink(path)
