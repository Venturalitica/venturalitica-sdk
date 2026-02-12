from .multiclass_parity import calc_weighted_demographic_parity_multiclass as _weighted_dp
from .multiclass_error import (
    calc_macro_equal_opportunity_multiclass as _macro_eo,
    calc_micro_equalized_odds_multiclass as _micro_eo
)
from .multiclass_predictive import calc_predictive_parity_multiclass as _predictive_p
from .multiclass_reporting import (
    calc_intersectional_metrics,
    calc_multiclass_fairness_report as _reporting
)
import pandas as pd

def _get_vitals(df_or_series, *args, **kwargs):
    """Smart vitals extraction: handles both (df, **kwargs) and (y_true, y_pred, prot, **kwargs)"""
    if isinstance(df_or_series, pd.DataFrame):
        target = kwargs.get('target')
        pred = kwargs.get('prediction')
        dim = kwargs.get('dimension')
        if not all([target, pred, dim]) or any(v in [None, "MISSING"] for v in [target, pred, dim]):
             raise ValueError("Missing required roles: target, prediction, dimension")
        return df_or_series[target], df_or_series[pred], df_or_series[dim]
    else:
        # Positional arguments: y_true, y_pred, protected_attr
        if len(args) < 2:
             raise TypeError("Expected either (df, **kwargs) or (y_true, y_pred, protected_attr)")
        return df_or_series, args[0], args[1]

def calc_weighted_demographic_parity_multiclass(df_or_series, *args, **kwargs):
    y_true, y_pred, protected_attr = _get_vitals(df_or_series, *args, **kwargs)
    # If positional args were used, kwargs might contain the rest
    return _weighted_dp(y_true, y_pred, protected_attr, **kwargs)

def calc_macro_equal_opportunity_multiclass(df_or_series, *args, **kwargs):
    y_true, y_pred, protected_attr = _get_vitals(df_or_series, *args, **kwargs)
    return _macro_eo(y_true, y_pred, protected_attr, **kwargs)

def calc_micro_equalized_odds_multiclass(df_or_series, *args, **kwargs):
    y_true, y_pred, protected_attr = _get_vitals(df_or_series, *args, **kwargs)
    return _micro_eo(y_true, y_pred, protected_attr, **kwargs)

def calc_predictive_parity_multiclass(df_or_series, *args, **kwargs):
    y_true, y_pred, protected_attr = _get_vitals(df_or_series, *args, **kwargs)
    return _predictive_p(y_true, y_pred, protected_attr, **kwargs)

def calc_multiclass_fairness_report(df_or_series, *args, **kwargs):
    y_true, y_pred, protected_attr = _get_vitals(df_or_series, *args, **kwargs)
    return _reporting(y_true, y_pred, protected_attr, **kwargs)

__all__ = [
    "calc_weighted_demographic_parity_multiclass",
    "calc_macro_equal_opportunity_multiclass",
    "calc_micro_equalized_odds_multiclass",
    "calc_predictive_parity_multiclass",
    "calc_intersectional_metrics",
    "calc_multiclass_fairness_report",
]
