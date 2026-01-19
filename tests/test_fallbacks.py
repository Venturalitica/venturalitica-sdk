import pytest
import sys
from unittest.mock import patch
import importlib
import venturalitica.metrics

def test_metrics_no_fairlearn():
    with patch.dict('sys.modules', {'fairlearn.metrics': None, 'fairlearn': None}):
        importlib.reload(venturalitica.metrics)
        
        assert venturalitica.metrics.HAS_FAIRLEARN is False
        
        import pandas as pd
        # Test data where demographic parity should be 1.0 (max bias)
        df = pd.DataFrame({'t': [1, 0], 'p': [1, 0], 's': ['A', 'B']})
        # Group A: mean(p) = 1.0, Group B: mean(p) = 0.0. Diff = 1.0
        res = venturalitica.metrics.calc_demographic_parity(df, target='t', prediction='p', sensitive='s')
        assert res == 1.0
        
        # Test Equal Opportunity fallback
        res_eq = venturalitica.metrics.calc_equal_opportunity(df, target='t', prediction='p', sensitive='s')
        assert res_eq == 1.0 # Group A TPR=1.0, Group B TPR=0.0 (Wait, Group B s=B has t=0, so TPR is undefined/0 handled)
        
        # Test Disparate Impact fallback
        res_di = venturalitica.metrics.calc_disparate_impact(df, target='t', sensitive='s')
        assert res_di == 0.0

def test_metrics_cleanup():
    importlib.reload(venturalitica.metrics)
