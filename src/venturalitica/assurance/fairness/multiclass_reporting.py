from typing import Dict, Optional, Any
import pandas as pd
from .multiclass_parity import calc_weighted_demographic_parity_multiclass
from .multiclass_error import (
    calc_macro_equal_opportunity_multiclass,
    calc_micro_equalized_odds_multiclass,
)
from .multiclass_predictive import calc_predictive_parity_multiclass


def calc_intersectional_metrics(
    y_true: pd.Series,
    y_pred: pd.Series,
    protected_attrs: Dict[str, pd.Series],
    metric_fn: callable = None,
    **kwargs,
) -> Dict[str, Any]:
    """Intersectional Bias calculation."""

    def _default_metric(t, p):
        return (t == p).mean()

    if metric_fn is None:
        metric_fn = _default_metric

    attr_names = list(protected_attrs.keys())
    combined_attr = protected_attrs[attr_names[0]].astype(str)
    for name in attr_names[1:]:
        combined_attr += " x " + protected_attrs[name].astype(str)

    slices = combined_attr.unique()
    slice_metrics = {}

    for s in slices:
        mask = combined_attr == s
        if mask.sum() >= 5:
            slice_metrics[str(s)] = float(metric_fn(y_true[mask], y_pred[mask]))

    if not slice_metrics:
        return {"disparity": 0.0, "slices": {}}

    vals = list(slice_metrics.values())
    return {
        "intersectional_disparity": max(vals) - min(vals),
        "worst_slice": min(slice_metrics, key=slice_metrics.get),
        "best_slice": max(slice_metrics, key=slice_metrics.get),
        "slice_details": slice_metrics,
    }


def calc_multiclass_fairness_report(
    y_true: pd.Series,
    y_pred: pd.Series,
    protected_attr: pd.Series,
    intersectional_attrs: Optional[Dict[str, pd.Series]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Comprehensive Multi-class Fairness Report."""
    report = {
        "weighted_demographic_parity_macro": calc_weighted_demographic_parity_multiclass(
            y_true, y_pred, protected_attr, strategy="macro"
        ),
        "macro_equal_opportunity": calc_macro_equal_opportunity_multiclass(
            y_true, y_pred, protected_attr
        ),
        "micro_equalized_odds": calc_micro_equalized_odds_multiclass(
            y_true, y_pred, protected_attr
        ),
        "predictive_parity_macro": calc_predictive_parity_multiclass(
            y_true, y_pred, protected_attr, strategy="macro"
        )[0],
    }

    if intersectional_attrs:
        inter_results = calc_intersectional_metrics(
            y_true, y_pred, intersectional_attrs
        )
        report["intersectional_disparity"] = inter_results["intersectional_disparity"]
        report["worst_performing_slice"] = inter_results["worst_slice"]

    return report
