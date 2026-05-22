"""Segmentation-fairness metrics over a continuous per-case score column.

PURE pandas/numpy — **no torch / no monai**. These ship in the base install and,
because they are registered in ``METRIC_REGISTRY`` and operate on the ``data=df``
the control was evaluated on, the SDK's power-stats
(:func:`venturalitica.assurance.power.compute_power`) bootstraps a confidence
interval for them **automatically** (cluster-aware via ``input.cluster``). A
disparity is only *actionable* when its CI excludes the no-disparity value
(0 for gaps/skew, 1 for ratios) — which the attached power-stats makes visible.

Every metric here consumes a **per-case continuous score** (e.g. Dice / IoU /
NSD per scan, built by ``venturalitica.assurance.imaging``) plus a group
``dimension`` column. None of them touch masks.

Implemented (ported from the literature — not reinvented):

- **ESSP / ES-Dice** — Equity-Scaled Segmentation Performance (FairSeg, ICLR
  2024, Harvard-Ophthalmology-AI-Lab):
  ``ESSP = I / (1 + Σ_g |I − I_g|)`` where ``I`` is the overall mean score and
  ``I_g`` the mean score of group ``g``. ``ESSP ≤ I``; it → ``I`` as the model
  becomes fair across groups and is penalized by disparity. ``es_dice`` /
  ``es_iou`` are convenience aliases (ESSP on a Dice / IoU score column).
  ``ESSP-Stdev`` swaps ``Σ_g |I − I_g|`` for the population standard deviation
  of the group means.
- **subgroup_disparity** — the family of single-number disparities over the
  group means: ``gap`` (max−min, Rawlsian-complement), ``ratio`` (min/max),
  ``std``, ``cv`` (coefficient of variation), ``worst_group`` (min group mean,
  Rawlsian) and ``skew`` (**DSC Skewness**, FairMedFM, NeurIPS 2024 — the
  skewness of the per-group mean scores across advantaged/disadvantaged groups;
  a skew ≠ 0 indicates the disparity is concentrated in a tail of groups).
  Each is also exposed as its own registry metric (``score_gap``,
  ``score_ratio``, ``score_std``, ``score_cv``, ``score_skew``) so it can be a
  standalone OSCAL control with a threshold + CI.

.. caveat::
   The **Dice coefficient has an inherent structure-SIZE bias** (arXiv
   2509.19778, 2025): for the same boundary error, a *smaller* target structure
   yields a *lower* Dice. So a raw **Dice gap by sex/age** can be a metric
   artifact driven by anatomical size differences between groups, NOT model
   bias. Always cross-check the same disparity on a **boundary metric**
   (NSD / HD95 — less size-biased) before treating a Dice disparity as
   actionable. These metrics accept ANY per-case score column, so pointing
   ``score`` at an NSD column reuses the exact same controls for that check.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd

__all__ = [
    "calc_essp",
    "calc_es_dice",
    "calc_es_iou",
    "calc_essp_stdev",
    "calc_subgroup_disparity",
    "calc_score_gap",
    "calc_score_ratio",
    "calc_score_std",
    "calc_score_cv",
    "calc_score_skew",
]


def _resolve_score_col(df: pd.DataFrame, **kwargs) -> str:
    """Resolve the per-case score column from the bound ``score`` role.

    Falls back to ``target`` for back-compat with controls binding the score via
    ``input.target``.
    """
    score = kwargs.get("score") or kwargs.get("input.score")
    if not score or score == "MISSING":
        score = kwargs.get("target")
    if not score or score == "MISSING":
        raise ValueError(
            "Missing required role 'score' (the per-case score column) "
            "for the segmentation-fairness metric"
        )
    if score not in df.columns:
        raise KeyError(f"Score column '{score}' not found in DataFrame")
    return score


def _resolve_dimension(df: pd.DataFrame, **kwargs) -> str:
    dim = kwargs.get("dimension") or kwargs.get("input.dimension")
    if not dim or dim == "MISSING":
        raise ValueError(
            "Missing required role 'dimension' (the protected-group column) "
            "for the segmentation-fairness metric"
        )
    if dim not in df.columns:
        raise KeyError(f"Dimension column '{dim}' not found in DataFrame")
    return dim


def _overall_and_group_means(df: pd.DataFrame, **kwargs) -> Tuple[float, pd.Series]:
    """Return ``(I, group_means)`` for the bound score/dimension.

    ``I`` is the overall mean of the per-case score; ``group_means`` is the mean
    score per group (NaN-group means dropped). Raises if either is empty.
    """
    score = _resolve_score_col(df, **kwargs)
    dim = _resolve_dimension(df, **kwargs)
    s = pd.to_numeric(df[score], errors="coerce")
    overall = s.dropna()
    if overall.empty:
        raise ValueError(f"Score column '{score}' has no finite values")
    group_means = s.groupby(df[dim]).mean().dropna()
    if group_means.empty:
        raise ValueError(f"No groups with finite scores for dimension '{dim}'")
    return float(overall.mean()), group_means


# ---------------------------------------------------------------------------
# ESSP / ES-Dice (FairSeg, ICLR 2024)
# ---------------------------------------------------------------------------

def calc_essp(df: pd.DataFrame, **kwargs) -> tuple:
    """Equity-Scaled Segmentation Performance: ``I / (1 + Σ_g |I − I_g|)``.

    ``ESSP ≤ I``; equals ``I`` only when every group mean equals the overall
    mean (perfect equity), and is dragged below ``I`` by disparity. Higher is
    better. Returns ``(essp, {"overall": I, "groups": {g: I_g}, "disparity_sum":
    Σ|I−I_g|})``.

    Required roles: ``score``, ``dimension``.
    """
    overall, group_means = _overall_and_group_means(df, **kwargs)
    disparity_sum = float(np.abs(overall - group_means.to_numpy()).sum())
    essp = overall / (1.0 + disparity_sum)
    meta = {
        "overall": overall,
        "groups": {str(k): float(v) for k, v in group_means.items()},
        "disparity_sum": disparity_sum,
    }
    return float(essp), meta


def calc_es_dice(df: pd.DataFrame, **kwargs) -> tuple:
    """ES-Dice — :func:`calc_essp` applied to a per-case **Dice** score column.

    Convenience alias; identical computation to ``essp``. See the module
    size-bias caveat: cross-check with ES-NSD/HD before acting on a Dice gap.
    """
    return calc_essp(df, **kwargs)


def calc_es_iou(df: pd.DataFrame, **kwargs) -> tuple:
    """ES-IoU — :func:`calc_essp` applied to a per-case **IoU** score column."""
    return calc_essp(df, **kwargs)


def calc_essp_stdev(df: pd.DataFrame, **kwargs) -> tuple:
    """ESSP-Stdev variant: ``I / (1 + std_g(I_g))``.

    Uses the population standard deviation of the group means instead of
    ``Σ_g |I − I_g|`` as the disparity penalty. Higher is better.

    Required roles: ``score``, ``dimension``.
    """
    overall, group_means = _overall_and_group_means(df, **kwargs)
    std = float(group_means.to_numpy().std())  # population std (ddof=0)
    essp = overall / (1.0 + std)
    meta = {
        "overall": overall,
        "groups": {str(k): float(v) for k, v in group_means.items()},
        "group_std": std,
    }
    return float(essp), meta


# ---------------------------------------------------------------------------
# Subgroup disparities over the continuous score
# ---------------------------------------------------------------------------

def _disparities(group_means: pd.Series) -> dict:
    arr = group_means.to_numpy(dtype=float)
    g_max = float(arr.max())
    g_min = float(arr.min())
    mean = float(arr.mean())
    std = float(arr.std())  # population std (ddof=0)
    cv = float(std / mean) if mean != 0 else float("nan")
    return {
        "gap": g_max - g_min,
        "ratio": (g_min / g_max) if g_max != 0 else float("nan"),
        "std": std,
        "cv": cv,
        "worst_group": g_min,
        "skew": _skewness(arr),
    }


def _skewness(arr: np.ndarray) -> float:
    """Population (Fisher-Pearson) skewness of the per-group mean scores.

    DSC Skewness (FairMedFM, NeurIPS 2024): a 0 skew means the disparity is
    symmetric across groups; a negative skew means a tail of disadvantaged
    groups drags performance down (the equity-relevant case). Returns 0.0 for
    fewer than 3 groups or zero variance (skew undefined / degenerate).
    """
    n = arr.size
    if n < 3:
        return 0.0
    mean = arr.mean()
    std = arr.std()  # population std
    if std == 0:
        return 0.0
    return float(np.mean(((arr - mean) / std) ** 3))


def calc_subgroup_disparity(df: pd.DataFrame, **kwargs) -> tuple:
    """All score disparities at once over the group means.

    Returns ``(primary, metadata)`` where ``primary`` is the disparity selected
    by the ``measure`` param (default ``gap``) and ``metadata`` carries every
    disparity (``gap``/``ratio``/``std``/``cv``/``worst_group``/``skew``) plus
    the per-group means. Lets one control surface the whole disparity profile.

    Required roles: ``score``, ``dimension``. Optional param: ``measure``.
    """
    _, group_means = _overall_and_group_means(df, **kwargs)
    disp = _disparities(group_means)
    measure = kwargs.get("measure", "gap")
    if measure not in disp:
        raise ValueError(
            f"Unknown disparity measure '{measure}'; choose one of {sorted(disp)}"
        )
    meta = dict(disp)
    meta["groups"] = {str(k): float(v) for k, v in group_means.items()}
    meta["measure"] = measure
    return float(disp[measure]), meta


def _single_disparity(df: pd.DataFrame, key: str, **kwargs) -> tuple:
    _, group_means = _overall_and_group_means(df, **kwargs)
    disp = _disparities(group_means)
    meta = {"groups": {str(k): float(v) for k, v in group_means.items()}}
    return float(disp[key]), meta


def calc_score_gap(df: pd.DataFrame, **kwargs) -> tuple:
    """Max−min of the per-group mean scores (actionable only if CI excludes 0).

    Required roles: ``score``, ``dimension``.
    """
    return _single_disparity(df, "gap", **kwargs)


def calc_score_ratio(df: pd.DataFrame, **kwargs) -> tuple:
    """Min/max of the per-group mean scores (1.0 = parity; CI should exclude 1).

    Required roles: ``score``, ``dimension``.
    """
    return _single_disparity(df, "ratio", **kwargs)


def calc_score_std(df: pd.DataFrame, **kwargs) -> tuple:
    """Population std of the per-group mean scores.

    Required roles: ``score``, ``dimension``.
    """
    return _single_disparity(df, "std", **kwargs)


def calc_score_cv(df: pd.DataFrame, **kwargs) -> tuple:
    """Coefficient of variation (std/mean) of the per-group mean scores.

    Required roles: ``score``, ``dimension``.
    """
    return _single_disparity(df, "cv", **kwargs)


def calc_score_skew(df: pd.DataFrame, **kwargs) -> tuple:
    """DSC Skewness of the per-group mean scores (FairMedFM, NeurIPS 2024).

    Negative skew flags a tail of disadvantaged groups. Actionable only if the
    CI excludes 0. Required roles: ``score``, ``dimension``.
    """
    return _single_disparity(df, "skew", **kwargs)
