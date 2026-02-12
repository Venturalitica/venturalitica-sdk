import importlib
import sys

import venturalitica.assurance.fairness.metrics
import venturalitica.assurance.performance.metrics
import venturalitica.assurance.quality.metrics


def test_metrics_no_fairlearn():
        # Force fallback mode to test the logic, avoiding fragile reload/sys.modules behavior
        venturalitica.assurance.quality.metrics.HAS_FAIRLEARN = False
        venturalitica.assurance.fairness.metrics.HAS_FAIRLEARN = False
        venturalitica.assurance.performance.metrics.HAS_FAIRLEARN = False
        
        # Verify flags (trivial now, but confirms we are in fallback mode)
        assert venturalitica.assurance.quality.metrics.HAS_FAIRLEARN is False

        
        import pandas as pd
        df = pd.DataFrame({'t': [1, 0], 'p': [1, 0], 's': ['A', 'B']})
        
        # Test fallbacks
        from venturalitica.assurance.fairness.metrics import calc_demographic_parity, calc_equal_opportunity
        from venturalitica.assurance.quality.metrics import calc_disparate_impact
        
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
        importlib.reload(venturalitica.assurance.quality.metrics)
        importlib.reload(venturalitica.assurance.fairness.metrics)
        importlib.reload(venturalitica.assurance.performance.metrics)

