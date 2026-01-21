from typing import Dict, Any, Callable
import pandas as pd
import numpy as np

try:
    import fairlearn.metrics as flm
    HAS_FAIRLEARN = True
except ImportError:
    HAS_FAIRLEARN = False

def calc_demographic_parity(df: pd.DataFrame, **kwargs) -> float:
    target = kwargs.get('target')
    pred = kwargs.get('prediction')
    dim = kwargs.get('dimension')
    
    if not all([target, pred, dim]) or any(v == "MISSING" for v in [target, pred, dim]):
        return 0.0
    
    if any(c not in df.columns for c in [target, pred, dim]):
        return 0.0
    
    if HAS_FAIRLEARN:
        return flm.demographic_parity_difference(
            df[target], df[pred], sensitive_features=df[dim]
        )
    
    groups = df.groupby(dim)
    pprs = [grp[pred].mean() for _, grp in groups]
    return max(pprs) - min(pprs) if pprs else 0.0

def calc_equal_opportunity(df: pd.DataFrame, **kwargs) -> float:
    target = kwargs.get('target')
    pred = kwargs.get('prediction')
    dim = kwargs.get('dimension')
    
    if not all([target, pred, dim]) or any(v == "MISSING" for v in [target, pred, dim]):
        return 0.0
        
    if any(c not in df.columns for c in [target, pred, dim]):
        return 0.0
    
    if HAS_FAIRLEARN:
        return flm.equalized_odds_difference(
            df[target], df[pred], sensitive_features=df[dim]
        )
        
    groups = df.groupby(dim)
    tprs = []
    for _, grp in groups:
        pos_grp = grp[grp[target] == 1]
        tprs.append(pos_grp[pred].mean() if len(pos_grp) > 0 else 0.0)
    return max(tprs) - min(tprs) if tprs else 0.0
