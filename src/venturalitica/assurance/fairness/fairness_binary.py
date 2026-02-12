import pandas as pd
import numpy as np

try:
    import fairlearn.metrics as flm

    HAS_FAIRLEARN = True
except ImportError:
    HAS_FAIRLEARN = False


def calc_demographic_parity(df: pd.DataFrame, **kwargs) -> float:
    """Calculates Demographic Parity Difference."""
    target = kwargs.get("target")
    dim = kwargs.get("dimension")
    pred = kwargs.get("prediction")

    # [v0.4] Fallback to target if prediction is missing (Data Audit mode)
    outcome = pred if (pred and pred != "MISSING") else target

    if any(v in [None, "MISSING"] for v in [outcome, dim]):
        raise ValueError("Missing required columns for demographic_parity_diff")

    if HAS_FAIRLEARN:
        return flm.demographic_parity_difference(
            df[target], df[outcome], sensitive_features=df[dim]
        )

    groups = df.groupby(dim)
    pprs = [grp[outcome].mean() for _, grp in groups]
    return max(pprs) - min(pprs) if pprs else 0.0


def calc_equal_opportunity(df: pd.DataFrame, **kwargs) -> float:
    """Calculates Equal Opportunity Difference (TPR parity)."""
    target = kwargs.get("target")
    dim = kwargs.get("dimension")
    pred = kwargs.get("prediction")

    # [v0.4] Fallback to target if prediction is missing (Data Audit mode)
    outcome = pred if (pred and pred != "MISSING") else target

    if any(v in [None, "MISSING"] for v in [target, outcome, dim]):
        raise ValueError("Missing required columns for equal_opportunity_diff")

    if HAS_FAIRLEARN:
        return flm.equalized_odds_difference(
            df[target], df[outcome], sensitive_features=df[dim]
        )

    groups = df.groupby(dim)
    tprs = []
    for _, grp in groups:
        pos_grp = grp[grp[target] == 1]
        if len(pos_grp) > 0:
            tprs.append(grp[outcome].mean())  # Use outcome

    tprs = [t for t in tprs if not np.isnan(t)]
    return max(tprs) - min(tprs) if tprs else 0.0


def calc_equalized_odds_ratio(df: pd.DataFrame, **kwargs) -> float:
    """Equalized Odds Ratio: Combined TPR and FPR parity."""
    target = kwargs.get("target")
    pred = kwargs.get("prediction")
    dim = kwargs.get("dimension")

    if any(v in [None, "MISSING"] for v in [target, pred, dim]):
        raise ValueError("Missing columns for equalized_odds_ratio")

    groups = df.groupby(dim)
    tprs, fprs = [], []
    for _, grp in groups:
        pos_grp = grp[grp[target] == 1]
        if len(pos_grp) > 0:
            tprs.append(pos_grp[pred].mean())
        neg_grp = grp[grp[target] == 0]
        if len(neg_grp) > 0:
            fprs.append((neg_grp[pred] == 1).mean())

    tprs = [t for t in tprs if not np.isnan(t)]
    fprs = [f for f in fprs if not np.isnan(f)]

    if not tprs or not fprs:
        return 0.0
    return (max(tprs) - min(tprs)) + (max(fprs) - min(fprs))


def calc_predictive_parity(df: pd.DataFrame, **kwargs) -> float:
    """Predictive Parity (Precision Parity)."""
    target = kwargs.get("target")
    pred = kwargs.get("prediction")
    dim = kwargs.get("dimension")

    if any(v in [None, "MISSING"] for v in [target, pred, dim]):
        raise ValueError("Missing columns for predictive_parity")

    groups = df.groupby(dim)
    precisions = []
    for _, grp in groups:
        tp = ((grp[target] == 1) & (grp[pred] == 1)).sum()
        fp = ((grp[target] == 0) & (grp[pred] == 1)).sum()
        if (tp + fp) > 0:
            precisions.append(tp / (tp + fp))

    return max(precisions) - min(precisions) if precisions else 0.0
