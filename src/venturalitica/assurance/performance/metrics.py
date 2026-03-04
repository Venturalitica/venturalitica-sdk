import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score


def _require_target_and_prediction(kwargs):
    """Validate that target and prediction columns are available and present in the DataFrame."""
    target = kwargs.get('target')
    pred = kwargs.get('prediction')
    if not target or target in (None, "MISSING"):
        raise ValueError("Required column 'target' is not provided.")
    if not pred or pred in (None, "MISSING"):
        raise ValueError("Required column 'prediction' is not provided.")
    return target, pred


def calc_accuracy(df: pd.DataFrame, **kwargs) -> float:
    target, pred = _require_target_and_prediction(kwargs)
    if target not in df.columns or pred not in df.columns:
        raise KeyError(f"Column '{target}' or '{pred}' not found in DataFrame.")
    return float(accuracy_score(df[target], df[pred]))

def calc_precision(df: pd.DataFrame, **kwargs) -> float:
    target, pred = _require_target_and_prediction(kwargs)
    if target not in df.columns or pred not in df.columns:
        raise KeyError(f"Column '{target}' or '{pred}' not found in DataFrame.")
    avg = kwargs.get('average', 'binary')
    return float(precision_score(df[target], df[pred], average=avg, zero_division=0))

def calc_recall(df: pd.DataFrame, **kwargs) -> float:
    target, pred = _require_target_and_prediction(kwargs)
    if target not in df.columns or pred not in df.columns:
        raise KeyError(f"Column '{target}' or '{pred}' not found in DataFrame.")
    avg = kwargs.get('average', 'binary')
    return float(recall_score(df[target], df[pred], average=avg, zero_division=0))

def calc_f1(df: pd.DataFrame, **kwargs) -> float:
    target, pred = _require_target_and_prediction(kwargs)
    if target not in df.columns or pred not in df.columns:
        raise KeyError(f"Column '{target}' or '{pred}' not found in DataFrame.")
    avg = kwargs.get('average', 'binary')
    return float(f1_score(df[target], df[pred], average=avg, zero_division=0))

def calc_mean(df: pd.DataFrame, **kwargs) -> float:
    """Generic mean calculation for benchmark scores (bias, preference, etc.)"""
    target = kwargs.get('target')
    if not target or target == "MISSING" or target not in df.columns:
        return 0.0
    return float(df[target].mean())
