from typing import Dict, Any, Callable, Optional
import pandas as pd
import numpy as np
import warnings
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Try to import scientific libraries (optional dependencies)
try:
    import fairlearn.metrics as flm
    HAS_FAIRLEARN = True
except ImportError:
    HAS_FAIRLEARN = False

def _get_cols(kwargs, required):
    missing = [c for c in required if c not in kwargs or kwargs[c] is None]
    if missing:
        raise ValueError(f"Missing required columns for metric: {missing}")
        
    return [kwargs[c] for c in required]

# --- Standard Performance Metrics (Sklearn) ---
def calc_accuracy(df: pd.DataFrame, **kwargs) -> float:
    target = kwargs.get('target')
    pred = kwargs.get('prediction')
    if not all([target, pred]) or any(v == "MISSING" for v in [target, pred]):
        return 0.0
    if target not in df.columns or pred not in df.columns:
        return 0.0
    return float(accuracy_score(df[target], df[pred]))

def calc_precision(df: pd.DataFrame, **kwargs) -> float:
    target = kwargs.get('target')
    pred = kwargs.get('prediction')
    if not all([target, pred]) or any(v == "MISSING" for v in [target, pred]):
        return 0.0
    if target not in df.columns or pred not in df.columns:
        return 0.0
    return float(precision_score(df[target], df[pred], zero_division=0))

def calc_recall(df: pd.DataFrame, **kwargs) -> float:
    target = kwargs.get('target')
    pred = kwargs.get('prediction')
    if not all([target, pred]) or any(v == "MISSING" for v in [target, pred]):
        return 0.0
    if target not in df.columns or pred not in df.columns:
        return 0.0
    return float(recall_score(df[target], df[pred], zero_division=0))

def calc_f1(df: pd.DataFrame, **kwargs) -> float:
    target = kwargs.get('target')
    pred = kwargs.get('prediction')
    if not all([target, pred]) or any(v == "MISSING" for v in [target, pred]):
        return 0.0
    if target not in df.columns or pred not in df.columns:
        return 0.0
    return float(f1_score(df[target], df[pred], zero_division=0))

# --- Fairness Metrics (Scientific Wrappers) ---
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

# --- Data Bias Metrics ---
def calc_disparate_impact(df: pd.DataFrame, **kwargs) -> float:
    target = kwargs.get('target')
    dim = kwargs.get('dimension')
    
    if not all([target, dim]) or any(v == "MISSING" for v in [target, dim]):
        return 1.0
        
    if target not in df.columns or dim not in df.columns:
        return 1.0
    
    if HAS_FAIRLEARN:
        # demographic_parity_ratio is min_rate / max_rate which is exactly Disparate Impact
        return flm.demographic_parity_ratio(
            df[target], df[target], sensitive_features=df[dim]
        )
               
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


METRIC_REGISTRY: Dict[str, Callable] = {
    "accuracy_score": calc_accuracy,
    "precision_score": calc_precision,
    "recall_score": calc_recall,
    "f1_score": calc_f1,
    "demographic_parity_diff": calc_demographic_parity,
    "equal_opportunity_diff": calc_equal_opportunity,
    "disparate_impact": calc_disparate_impact,
    "class_imbalance": calc_class_imbalance,
}
