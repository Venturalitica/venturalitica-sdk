from typing import Dict, Any, Callable
import pandas as pd
import numpy as np

try:
    import fairlearn.metrics as flm
    HAS_FAIRLEARN = True
except ImportError:
    HAS_FAIRLEARN = False

def calc_disparate_impact(df: pd.DataFrame, **kwargs) -> float:
    target = kwargs.get('target')
    dim = kwargs.get('dimension')
    
    if not all([target, dim]) or any(v == "MISSING" for v in [target, dim]):
        return 1.0
        
    if target not in df.columns or dim not in df.columns:
        return 1.0
    
    if HAS_FAIRLEARN:
        res = flm.demographic_parity_ratio(
            df[target], df[target], sensitive_features=df[dim]
        )
        return float(np.nan_to_num(res, nan=1.0))
               
    groups = df.groupby(dim)[target].mean()
    rates = groups.values
    if len(rates) < 2 or max(rates) == 0: return 1.0
    return min(rates) / max(rates)

def calc_class_imbalance(df: pd.DataFrame, **kwargs) -> float:
    target = kwargs.get('target')
    if not target or target == "MISSING" or target not in df.columns:
        return 0.0
    counts = df[target].value_counts()
    if len(counts) < 2: return 0.0
    return float(counts.min() / counts.max())
