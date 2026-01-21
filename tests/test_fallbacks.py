import pytest
import sys
from unittest.mock import patch
import importlib
import venturalitica.metrics.data
import venturalitica.metrics.fairness
import venturalitica.metrics.performance

def test_metrics_no_fairlearn():
    with patch.dict('sys.modules', {'fairlearn.metrics': None, 'fairlearn': None}):
        importlib.reload(venturalitica.metrics.data)
        importlib.reload(venturalitica.metrics.fairness)
        importlib.reload(venturalitica.metrics.performance)
        
        from venturalitica.metrics.data import HAS_FAIRLEARN as HF_DATA
        from venturalitica.metrics.fairness import HAS_FAIRLEARN as HF_FAIR
        
        assert HF_DATA is False
        assert HF_FAIR is False
        
        import pandas as pd
        df = pd.DataFrame({'t': [1, 0], 'p': [1, 0], 's': ['A', 'B']})
        
        # Test fallbacks
        from venturalitica.metrics.fairness import calc_demographic_parity, calc_equal_opportunity
        from venturalitica.metrics.data import calc_disparate_impact
        
        assert calc_demographic_parity(df, target='t', prediction='p', dimension='s') == 1.0
        assert calc_equal_opportunity(df, target='t', prediction='p', dimension='s') == 1.0
        assert calc_disparate_impact(df, target='t', dimension='s') == 0.0

def test_metrics_cleanup():
    # Attempt to restore normalcy
    if 'fairlearn' in sys.modules:
        importlib.reload(venturalitica.metrics.data)
        importlib.reload(venturalitica.metrics.fairness)
        importlib.reload(venturalitica.metrics.performance)
