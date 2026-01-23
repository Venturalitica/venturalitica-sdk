from typing import Dict, Any, Callable
import pandas as pd
import numpy as np

try:
    import fairlearn.metrics as flm
    HAS_FAIRLEARN = True
except ImportError:
    HAS_FAIRLEARN = False

def calc_disparate_impact(df: pd.DataFrame, **kwargs) -> float:
    # If prediction is available, use it as the outcome for DI, otherwise use target
    target = kwargs.get('target')
    dim = kwargs.get('dimension')
    outcome = kwargs.get('prediction') if kwargs.get('prediction') != "MISSING" else target
    
    if not all([outcome, dim]) or any(v in [None, "MISSING"] for v in [outcome, dim]):
        return 1.0
        
    if outcome not in df.columns or dim not in df.columns:
        return 1.0
    
    # Filter groups with minimal support (e.g., < 5 samples) to avoid noise
    group_counts = df[dim].value_counts()
    valid_groups = group_counts[group_counts >= 5].index
    if len(valid_groups) < 2:
        return 1.0 # Not enough data for meaningful comparison
        
    filtered_df = df[df[dim].isin(valid_groups)]
    
    if HAS_FAIRLEARN:
        res = flm.demographic_parity_ratio(
            filtered_df[target], filtered_df[outcome], sensitive_features=filtered_df[dim]
        )
        return float(np.nan_to_num(res, nan=1.0))
               
    group_rates = filtered_df.groupby(dim)[outcome].mean()
    rates = group_rates.values
    if len(rates) < 2 or max(rates) == 0: return 1.0
    return min(rates) / max(rates)

def calc_class_imbalance(df: pd.DataFrame, **kwargs) -> float:
    target = kwargs.get('target')
    if not target or target == "MISSING" or target not in df.columns:
        return 0.0
    counts = df[target].value_counts()
    if len(counts) < 2: return 0.0
    return float(counts.min() / counts.max())
