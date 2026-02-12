from typing import Dict, Any
import pandas as pd
import numpy as np


def calc_multiclass_demographic_parity(df: pd.DataFrame, **kwargs) -> float:
    """Multi-class Demographic Parity (One-vs-Rest)."""
    target, pred, dim = (
        kwargs.get("target"),
        kwargs.get("prediction"),
        kwargs.get("dimension"),
    )
    aggregation = kwargs.get("aggregation", "max")

    if any(v in [None, "MISSING"] for v in [target, pred, dim]):
        raise ValueError("Missing columns for multiclass_demographic_parity")

    classes = df[target].unique()
    class_parities = []
    for cls in classes:
        binary_pred = (df[pred] == cls).astype(int)
        groups = df.groupby(dim)
        pprs = [binary_pred[grp.index].mean() for _, grp in groups if len(grp) > 0]
        if pprs:
            class_parities.append(max(pprs) - min(pprs))

    if not class_parities:
        return 0.0
    return np.mean(class_parities) if aggregation == "macro" else max(class_parities)


def calc_multiclass_equal_opportunity(df: pd.DataFrame, **kwargs) -> float:
    """Multi-class Equal Opportunity (TPR parity)."""
    target, pred, dim = (
        kwargs.get("target"),
        kwargs.get("prediction"),
        kwargs.get("dimension"),
    )

    if any(v in [None, "MISSING"] for v in [target, pred, dim]):
        raise ValueError("Missing columns for multiclass_equal_opportunity")

    classes = df[target].unique()
    class_tpr_parities = []
    for cls in classes:
        binary_target = (df[target] == cls).astype(int)
        binary_pred = (df[pred] == cls).astype(int)
        groups = df.groupby(dim)
        tprs = [
            binary_pred[grp.index[binary_target[grp.index] == 1]].mean()
            for _, grp in groups
            if (binary_target[grp.index] == 1).any()
        ]
        if tprs:
            class_tpr_parities.append(max(tprs) - min(tprs))

    return max(class_tpr_parities) if class_tpr_parities else 0.0


def calc_multiclass_confusion_metrics(df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
    """Multi-class Confusion Matrix Metrics."""
    target, pred, dim = (
        kwargs.get("target"),
        kwargs.get("prediction"),
        kwargs.get("dimension"),
    )

    classes, groups = df[target].unique(), df[dim].unique()
    metrics = {"per_class_metrics": {}, "per_group_performance": {}}

    for cls in classes:
        mask_t, mask_p = (df[target] == cls), (df[pred] == cls)
        tp = (mask_t & mask_p).sum()
        precision = tp / mask_p.sum() if mask_p.any() else 0
        recall = tp / mask_t.sum() if mask_t.any() else 0
        metrics["per_class_metrics"][str(cls)] = {
            "precision": precision,
            "recall": recall,
        }

    for grp in groups:
        mask = df[dim] == grp
        metrics["per_group_performance"][str(grp)] = (
            (df[mask][target] == df[mask][pred]).mean() if mask.any() else 0
        )

    return metrics
