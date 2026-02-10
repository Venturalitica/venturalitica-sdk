import tempfile
import yaml
import os
import pandas as pd
from venturalitica import enforce


def test_group_min_positive_rate_triggered():
    # Build a tiny dataset with imbalanced positives across gender
    df = pd.DataFrame({'target': [1,2,2,1,2,2], 'Attribute9': ['M','M','F','F','M','F']})
    # For this df: groups M -> targets [1,2,2] positives=2/3 ~0.666, F -> [2,1,2] positives=2/3 ~0.666 -> min 0.666

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
                            {'name': 'input:dimension', 'value': 'Attribute9'}
                        ]
                    }
                ]
            },
            'control-implementations': [
                {
                    'implemented-requirements': [
                        {
                            'control-id': 'GB1',
                            'description': 'Group balance check',
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
        results = enforce(data=df, policy=path, target='target')
        # Should evaluate one control
        assert len(results) == 1
        r = results[0]
        assert r.metric_key == 'group_min_positive_rate'
        assert r.actual_value >= 0.66 and r.actual_value <= 0.67
        assert bool(r.passed) is True
    finally:
        os.unlink(path)
