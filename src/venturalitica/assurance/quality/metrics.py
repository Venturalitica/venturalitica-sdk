import pandas as pd
import numpy as np

try:
    import fairlearn.metrics as flm

    HAS_FAIRLEARN = True
except ImportError:
    HAS_FAIRLEARN = False

# Re-export ESG-specific metrics from esg_metrics module
from .esg_metrics import (
    calc_classification_distribution,
    calc_report_coverage,
    calc_provenance_completeness,
    calc_chunk_diversity,
    calc_subtitle_diversity,
)

__all__ = [
    "calc_disparate_impact",
    "calc_class_imbalance",
    "calc_group_min_positive_rate",
    "calc_data_completeness",
    "calc_classification_distribution",
    "calc_report_coverage",
    "calc_provenance_completeness",
    "calc_chunk_diversity",
    "calc_subtitle_diversity",
]


def calc_disparate_impact(df: pd.DataFrame, **kwargs) -> float:
    target = kwargs.get("target")
    dim = kwargs.get("dimension")
    pred = kwargs.get("prediction")

    # Audit outcome: use prediction if provided and valid, else use target (data audit)
    outcome = pred if (pred and pred != "MISSING") else target

    if not all([outcome, dim]) or any(v in [None, "MISSING"] for v in [outcome, dim]):
        # We return 1.0 only if dimension is missing, but core should have skipped it
        return 1.0

    if outcome not in df.columns or dim not in df.columns:
        return 1.0

    # Filter groups with minimal support (e.g., < 5 samples) to avoid noise
    group_counts = df[dim].value_counts()
    valid_groups = group_counts[group_counts >= 5].index
    if len(valid_groups) < 2:
        return 1.0  # Not enough data for meaningful comparison

    filtered_df = df[df[dim].isin(valid_groups)]

    if HAS_FAIRLEARN:
        res = flm.demographic_parity_ratio(
            filtered_df[target],
            filtered_df[outcome],
            sensitive_features=filtered_df[dim],
        )
        return float(np.nan_to_num(res, nan=1.0))

    group_rates = filtered_df.groupby(dim)[outcome].mean()
    rates = group_rates.values
    if len(rates) < 2 or max(rates) == 0:
        return 1.0
    return min(rates) / max(rates)


def calc_class_imbalance(df: pd.DataFrame, **kwargs) -> float:
    """Compute class imbalance as the ratio min_class_count / max_class_count.

    Returns a value between 0.0 (completely imbalanced) and 1.0 (perfectly balanced).
    Required kwargs: target OR input:target
    """
    target = kwargs.get("target") or kwargs.get("input:target")
    if not target:
        raise ValueError("Missing required role 'target' for calc_class_imbalance")
    if target not in df.columns:
        raise ValueError(f"Target column '{target}' not found in DataFrame")

    counts = df[target].dropna().value_counts()
    if counts.empty:
        return 0.0
    if len(counts) == 1:
        # Only a single class present -> worst-case imbalance
        return 0.0

    min_count = counts.min()
    max_count = counts.max()
    if max_count == 0:
        return 0.0
    return float(min_count) / float(max_count)


def calc_group_min_positive_rate(df: pd.DataFrame, **kwargs) -> tuple:
    """Compute the minimum positive rate across groups for a given dimension.

    Returns a tuple (min_rate, metadata_dict) where metadata contains per-group rates.
    Required kwargs: target, input:dimension OR dimension
    Optional kwargs: age_bucket_method='quantiles', age_buckets=3
    """
    target = kwargs.get("target")
    dim = kwargs.get("input:dimension") or kwargs.get("dimension")

    if not target or not dim:
        raise ValueError(
            "Missing required roles for group_min_positive_rate: 'target' and 'dimension' are required"
        )

    if dim not in df.columns:
        raise ValueError(f"Dimension column '{dim}' not found in DataFrame")

    series = df[dim]
    # handle optional bucketing for numeric age fields
    bucket_method = kwargs.get("age_bucket_method")
    buckets = int(kwargs.get("age_buckets", 3)) if kwargs.get("age_buckets") else 3

    if bucket_method == "quantiles" and pd.api.types.is_numeric_dtype(series):
        groups = pd.qcut(series, q=buckets, duplicates="drop")
    else:
        groups = series

    grouped = df.groupby(groups)
    rates = {}
    for name, g in grouped:
        grp_y = g[target]
        try:
            grp_y_num = pd.to_numeric(grp_y, errors="coerce")
            pos_rate = (
                (grp_y_num == grp_y_num.max()).sum() / len(grp_y_num.dropna())
                if len(grp_y_num.dropna()) > 0
                else 0.0
            )
        except Exception:
            pos_rate = float((grp_y == grp_y.max()).sum() / len(grp_y))
        rates[str(name)] = pos_rate

    if len(rates) == 0:
        min_rate = 0.0
    else:
        min_rate = min(rates.values())

    return min_rate, {"groups": rates}


def calc_data_completeness(df: pd.DataFrame, **kwargs) -> float:
    """Compute an overall data completeness score (0.0 - 1.0).

    Approach: For all columns, compute the fraction of non-null
    values per column, then return the mean completeness across columns.
    """
    cols = [c for c in df.columns]
    if not cols or len(df) == 0:
        return 0.0
    completeness_per_col = []
    for c in cols:
        completeness_per_col.append(df[c].notna().sum() / len(df))
    return float(sum(completeness_per_col) / len(completeness_per_col))
