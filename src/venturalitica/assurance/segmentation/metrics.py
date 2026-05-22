"""Aggregate metrics over a continuous *per-case* score column.

These turn a per-case score (e.g. a Dice value per patient/scan, built by the
``venturalitica.assurance.imaging`` helpers) into first-class registry metrics.
Because they are registered in ``METRIC_REGISTRY`` and operate on the
``data=df`` the control was evaluated on, the SDK's power-stats
(:func:`venturalitica.assurance.power.compute_power`) bootstraps a confidence
interval for them **automatically** — cluster-aware when the control declares
``input.cluster`` (e.g. ``patient_id``).

This is the alternative to passing a precomputed scalar to
``vl.enforce(metrics={"global_dice": 0.91})`` — which the SDK cannot bootstrap
because there is no underlying sample. By moving the aggregation into a
``calc_*`` over the per-case dataframe, every segmentation gate gets its
sampling-error CI for free.

All functions here are PURE pandas/numpy — **no torch / no monai** — so they
live in the base install. The ``score`` role binds to the per-case score column
the same way the existing metrics bind ``target``/``prediction``/``dimension``
(via ``input.score`` in the OSCAL control). ``min_group_score`` and
``group_score_gap`` additionally bind a single ``dimension`` (e.g.
``Manufacturer``); ``worst_cell_score`` takes a ``dimensions`` list param for a
composite subgroup cell (e.g. scanner × age band).

Each follows the established contract:

- the per-case column name arrives as a *resolved* kwarg (``score=<column>``);
- a scalar (or ``(scalar, metadata)``) is returned;
- missing/empty inputs raise ``ValueError``/``KeyError`` so the enforce loop
  can skip (non-strict) or fail-fast (strict), exactly like the other metrics.
"""

from __future__ import annotations

from typing import List, Union

import pandas as pd

__all__ = [
    "calc_mean_score",
    "calc_min_group_score",
    "calc_worst_cell_score",
    "calc_group_score_gap",
    "calc_max_score",
]


def _resolve_score_col(df: pd.DataFrame, **kwargs) -> str:
    """Resolve the per-case score column from the bound ``score`` role.

    Falls back to ``target`` for back-compat with controls that bind the score
    via ``input.target`` instead of ``input.score``.
    """
    score = kwargs.get("score") or kwargs.get("input.score")
    if not score or score == "MISSING":
        # Back-compat: some controls bind the per-case column as `target`.
        score = kwargs.get("target")
    if not score or score == "MISSING":
        raise ValueError(
            "Missing required role 'score' (the per-case score column) "
            "for the segmentation aggregate metric"
        )
    if score not in df.columns:
        raise KeyError(f"Score column '{score}' not found in DataFrame")
    return score


def _resolve_dimension(df: pd.DataFrame, **kwargs) -> str:
    dim = kwargs.get("dimension") or kwargs.get("input.dimension")
    if not dim or dim == "MISSING":
        raise ValueError(
            "Missing required role 'dimension' (the subgroup column) "
            "for the grouped segmentation metric"
        )
    if dim not in df.columns:
        raise KeyError(f"Dimension column '{dim}' not found in DataFrame")
    return dim


def _resolve_dimensions(
    df: pd.DataFrame, dimensions: Union[str, List[str], tuple, None]
) -> List[str]:
    """Normalize the ``dimensions`` param (list/comma-string) to real columns."""
    if dimensions is None:
        raise ValueError(
            "Missing required param 'dimensions' (the composite-cell columns) "
            "for worst_cell_score"
        )
    if isinstance(dimensions, str):
        cols = [c.strip() for c in dimensions.split(",") if c.strip()]
    elif isinstance(dimensions, (list, tuple)):
        cols = [str(c) for c in dimensions]
    else:
        raise ValueError(f"Unsupported 'dimensions' type: {type(dimensions)!r}")
    if not cols:
        raise ValueError("'dimensions' resolved to an empty column list")
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"Cell columns not found in DataFrame: {missing}")
    return cols


def calc_mean_score(df: pd.DataFrame, **kwargs) -> float:
    """Global mean of a per-case score (e.g. ``global_dice``).

    ``df[score].mean()`` — the headline robustness/quality number. With power
    enabled this is the metric whose CI tells you whether the cohort is large
    enough to trust the mean.

    Required role: ``score`` (binds to the per-case score column).
    """
    score = _resolve_score_col(df, **kwargs)
    series = pd.to_numeric(df[score], errors="coerce").dropna()
    if series.empty:
        raise ValueError(f"Score column '{score}' has no finite values")
    return float(series.mean())


def calc_min_group_score(df: pd.DataFrame, **kwargs) -> tuple:
    """Minimum per-group mean score across a single dimension (robustness).

    ``df.groupby(dimension)[score].mean().min()`` — the worst-performing
    subgroup (e.g. ``min-scanner-dice`` across ``Manufacturer``). Returns
    ``(min_value, {"groups": {group: mean}})`` so the per-group means surface
    in the Assessment Results.

    Required roles: ``score``, ``dimension``.
    """
    score = _resolve_score_col(df, **kwargs)
    dim = _resolve_dimension(df, **kwargs)
    group_means = (
        pd.to_numeric(df[score], errors="coerce")
        .groupby(df[dim])
        .mean()
        .dropna()
    )
    if group_means.empty:
        raise ValueError(
            f"No groups with finite scores for dimension '{dim}'"
        )
    min_value = float(group_means.min())
    return min_value, {"groups": {str(k): float(v) for k, v in group_means.items()}}


def calc_worst_cell_score(df: pd.DataFrame, **kwargs) -> tuple:
    """Minimum over composite-cell mean scores (worst intersectional subgroup).

    Groups by the ``dimensions`` cell (e.g. scanner × age band), takes each
    cell's mean score, and returns the smallest — ``worst_subgroup_dice``.
    Returns ``(min_value, {"cells": {cell_label: mean}})``.

    Required role: ``score``. Required param: ``dimensions`` (list of columns).
    """
    score = _resolve_score_col(df, **kwargs)
    dimensions = _resolve_dimensions(df, kwargs.get("dimensions"))
    keys = [df[c] for c in dimensions]
    cell_means = (
        pd.to_numeric(df[score], errors="coerce").groupby(keys).mean().dropna()
    )
    if cell_means.empty:
        raise ValueError(
            f"No composite cells with finite scores for dimensions {dimensions}"
        )
    min_value = float(cell_means.min())
    cells = {
        ("|".join(map(str, k)) if isinstance(k, tuple) else str(k)): float(v)
        for k, v in cell_means.items()
    }
    return min_value, {"cells": cells}


def calc_group_score_gap(df: pd.DataFrame, **kwargs) -> tuple:
    """Max-minus-min gap of per-group mean scores across a dimension.

    ``max - min`` of ``df.groupby(dimension)[score].mean()`` — a fairness gap
    (e.g. ``elderly_dice_gap`` across age band). Returns ``(gap, {"groups":
    {...}, "max_group": ..., "min_group": ...})``.

    Required roles: ``score``, ``dimension``.
    """
    score = _resolve_score_col(df, **kwargs)
    dim = _resolve_dimension(df, **kwargs)
    group_means = (
        pd.to_numeric(df[score], errors="coerce")
        .groupby(df[dim])
        .mean()
        .dropna()
    )
    if group_means.empty:
        raise ValueError(
            f"No groups with finite scores for dimension '{dim}'"
        )
    gap = float(group_means.max() - group_means.min())
    meta = {
        "groups": {str(k): float(v) for k, v in group_means.items()},
        "max_group": str(group_means.idxmax()),
        "min_group": str(group_means.idxmin()),
    }
    return gap, meta


def calc_max_score(df: pd.DataFrame, **kwargs) -> float:
    """Maximum per-case score (e.g. ``max_single_dice`` — leakage probe).

    ``df[score].max()`` — an implausibly high single-case score can flag
    train/test leakage or a degenerate (e.g. empty-mask) case.

    Required role: ``score``.
    """
    score = _resolve_score_col(df, **kwargs)
    series = pd.to_numeric(df[score], errors="coerce").dropna()
    if series.empty:
        raise ValueError(f"Score column '{score}' has no finite values")
    return float(series.max())
