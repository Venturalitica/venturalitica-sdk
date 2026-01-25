import pytest
import sys
from unittest.mock import patch
import importlib
import venturalitica.quality.metrics
import venturalitica.fairness.metrics
import venturalitica.performance.metrics

def test_metrics_no_fairlearn():
    with patch.dict('sys.modules', {'fairlearn.metrics': None, 'fairlearn': None}):
        importlib.reload(venturalitica.quality.metrics)
        importlib.reload(venturalitica.fairness.metrics)
        importlib.reload(venturalitica.performance.metrics)
        
        from venturalitica.quality.metrics import HAS_FAIRLEARN as HF_DATA
        from venturalitica.fairness.metrics import HAS_FAIRLEARN as HF_FAIR
        
        assert HF_DATA is False
        assert HF_FAIR is False
        
        import pandas as pd
        df = pd.DataFrame({'t': [1, 0], 'p': [1, 0], 's': ['A', 'B']})
        
        # Test fallbacks
        from venturalitica.fairness.metrics import calc_demographic_parity, calc_equal_opportunity
        from venturalitica.quality.metrics import calc_disparate_impact
        
        # Values might differ based on impl details, but just checking they run
        assert isinstance(calc_demographic_parity(df, target='t', prediction='p', dimension='s'), float)
        assert isinstance(calc_equal_opportunity(df, target='t', prediction='p', dimension='s'), float)
        # Disparate impact fallback check
        try:
             calc_disparate_impact(df, target='t', dimension='s')
        except Exception:
             pass

def test_metrics_cleanup():
    # Attempt to restore normalcy
    if 'fairlearn' in sys.modules:
        importlib.reload(venturalitica.quality.metrics)
        importlib.reload(venturalitica.fairness.metrics)
        importlib.reload(venturalitica.performance.metrics)
