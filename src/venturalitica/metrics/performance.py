from typing import Dict, Any, Callable
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

def calc_accuracy(df: pd.DataFrame, **kwargs) -> float:
    target = kwargs.get('target')
    pred = kwargs.get('prediction')
    if not all([target, pred]) or any(v in [None, "MISSING"] for v in [target, pred]):
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

def calc_mean(df: pd.DataFrame, **kwargs) -> float:
    """Generic mean calculation for benchmark scores (bias, preference, etc.)"""
    target = kwargs.get('target')
    if not target or target == "MISSING" or target not in df.columns:
        return 0.0
    return float(df[target].mean())
