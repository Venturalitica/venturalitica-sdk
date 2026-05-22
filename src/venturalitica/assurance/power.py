"""Power-stats — statistical reliability (sampling error) of a control's metric.

Every ``actual_value`` a control reports is an *estimator over a finite sample*.
A green gate (``value vs threshold``) is not audit evidence without its sampling
error: the point estimate may be statistically indistinguishable from the
threshold. This module computes, **online from the in-memory dataframe** (no
CSV persisted), a **percentile bootstrap** confidence interval for the *same*
``calc_*`` metric callable, so under-powered controls and under-populated
subgroups become visible.

Design contract (see ``2026-05-22-seigarrena-power-stats-design.md`` §3.1, §4):

- ``B = 1000`` resamples with replacement; the SAME ``calc_*`` is recomputed on
  each resample; ``ci_level = 0.95`` → percentile CI ``(ci_low, ci_high)``.
- **Deterministic**: a ``numpy.random.default_rng(seed)`` with a FIXED seed is
  used (never the global RNG), so two runs give byte-identical CIs. The seed is
  declared per control (``input.cluster``/params) or defaults to
  ``DEFAULT_SEED = 42``.
- **Cluster bootstrap**: when a ``cluster`` column is supplied (e.g.
  ``patient_id``), whole clusters are resampled as units (respecting the
  hierarchy / avoiding pseudoreplication) and ``n_clusters`` is reported. With
  no cluster column it is a row-level bootstrap.
- **Metric-family agnostic**: works for proportions (demographic parity),
  per-row means (Dice-like), and extremes (with the documented caveat that the
  CI of ``min``/``worst`` is wide/biased — it is *reported*, not hidden).

The bootstrap calls the *cheap* ``calc_*`` (no retraining), so cost is
``B × metric`` — fine for ``n`` up to a few thousand.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pandas as pd

#: Default RNG seed used when a control does not declare its own. Fixed so the
#: confidence interval is reproducible byte-for-byte (it feeds ``sei.lock``).
DEFAULT_SEED = 42

#: Default number of bootstrap resamples.
DEFAULT_N_BOOT = 1000

#: Default confidence level for the percentile interval.
DEFAULT_CI_LEVEL = 0.95


def _to_scalar(result: Any) -> Optional[float]:
    """Coerce a metric return into a scalar float.

    Metric callables may return either a bare scalar or a ``(value, metadata)``
    tuple (the SDK's established convention). NaN / non-finite / non-numeric
    results are mapped to ``None`` so degenerate resamples can be dropped by the
    caller instead of poisoning the percentiles.
    """
    if isinstance(result, tuple):
        result = result[0] if result else None
    if result is None:
        return None
    try:
        val = float(result)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(val):
        return None
    return val


def _subgroup_counts(df: pd.DataFrame, dimension: Optional[str]) -> Dict[str, int]:
    """Per-subgroup row counts so under-populated groups are visible.

    Returns ``{}`` when the metric has no group/``dimension`` input or the
    column is absent — an empty mapping signals "not a grouped metric".
    """
    if not dimension or dimension == "MISSING" or dimension not in df.columns:
        return {}
    counts = df[dimension].value_counts(dropna=False)
    return {str(k): int(v) for k, v in counts.items()}


def compute_power(
    df: pd.DataFrame,
    calc_fn: Callable[..., Any],
    kwargs: Dict[str, Any],
    value: Any = None,
    *,
    cluster: Optional[str] = None,
    dimension: Optional[str] = None,
    n_boot: int = DEFAULT_N_BOOT,
    ci_level: float = DEFAULT_CI_LEVEL,
    seed: int = DEFAULT_SEED,
) -> Dict[str, Any]:
    """Compute a percentile-bootstrap confidence interval for a control metric.

    Parameters
    ----------
    df:
        The same in-memory dataframe the control was evaluated on.
    calc_fn:
        The ``calc_*`` metric callable. It is re-invoked on each resample as
        ``calc_fn(resample, **kwargs)`` — exactly how the enforce loop calls it,
        so the bootstrap measures the *same* statistic.
    kwargs:
        The resolved keyword arguments passed to ``calc_fn`` at evaluation time
        (``target``/``prediction``/``dimension`` column names plus metric
        params). Passed through unchanged to every resample.
    value:
        The already-computed point estimate (the control's ``actual_value``).
        Used only as a finite fallback if every resample degenerates.
    cluster:
        Optional name of the column identifying the statistical unit (e.g.
        ``patient_id``). When given, whole clusters are resampled as units
        (cluster bootstrap); otherwise rows are resampled (row bootstrap).
    dimension:
        Optional name of the subgroup column, used to populate ``groups``.
    n_boot:
        Number of bootstrap resamples (``B``).
    ci_level:
        Confidence level (e.g. ``0.95``).
    seed:
        Fixed RNG seed → deterministic CI.

    Returns
    -------
    dict
        ``{n, n_clusters|None, groups, ci_low, ci_high, ci_level,
        method, n_boot, seed}``.
    """
    n = int(len(df))
    groups = _subgroup_counts(df, dimension)

    use_cluster = bool(cluster) and cluster != "MISSING" and cluster in df.columns
    method = "cluster_bootstrap" if use_cluster else "bootstrap"

    # Pre-compute cluster grouping once (row indices per cluster) for speed and
    # determinism. ``n_clusters`` is the number of *units* we resample.
    cluster_groups: List[np.ndarray] = []
    n_clusters: Optional[int] = None
    if use_cluster:
        # Positional row indices grouped by cluster id; stable order so the RNG
        # draws map to the same units run-to-run.
        codes = df[cluster].to_numpy()
        order: Dict[Any, List[int]] = {}
        for pos, key in enumerate(codes):
            order.setdefault(key, []).append(pos)
        cluster_groups = [np.asarray(v, dtype=np.intp) for v in order.values()]
        n_clusters = len(cluster_groups)

    rng = np.random.default_rng(seed)
    boot_values: List[float] = []

    # Degenerate guards: nothing to resample.
    if n == 0 or (use_cluster and n_clusters == 0):
        point = _to_scalar(value)
        return {
            "n": n,
            "n_clusters": n_clusters,
            "groups": groups,
            "ci_low": point,
            "ci_high": point,
            "ci_level": float(ci_level),
            "method": method,
            "n_boot": int(n_boot),
            "seed": int(seed),
        }

    for _ in range(int(n_boot)):
        if use_cluster:
            # Resample whole clusters (with replacement), then stitch their rows.
            pick = rng.integers(0, n_clusters, size=n_clusters)
            idx = np.concatenate([cluster_groups[j] for j in pick])
        else:
            idx = rng.integers(0, n, size=n)
        resample = df.iloc[idx]
        try:
            scalar = _to_scalar(calc_fn(resample, **kwargs))
        except Exception:
            # A degenerate resample (e.g. a subgroup vanished) must not abort
            # the whole bootstrap — drop it and continue.
            scalar = None
        if scalar is not None:
            boot_values.append(scalar)

    if boot_values:
        arr = np.asarray(boot_values, dtype=float)
        alpha = (1.0 - float(ci_level)) / 2.0
        ci_low = float(np.quantile(arr, alpha))
        ci_high = float(np.quantile(arr, 1.0 - alpha))
    else:
        # Every resample degenerated — fall back to the point estimate so the
        # CI is at least well-formed (zero-width) rather than null.
        point = _to_scalar(value)
        ci_low = point
        ci_high = point

    return {
        "n": n,
        "n_clusters": n_clusters,
        "groups": groups,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "ci_level": float(ci_level),
        "method": method,
        "n_boot": int(n_boot),
        "seed": int(seed),
    }
