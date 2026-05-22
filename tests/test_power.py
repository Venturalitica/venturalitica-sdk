"""Unit tests for power-stats (percentile bootstrap reliability per control).

Covers the design contract (2026-05-22-seigarrena-power-stats-design.md §3.1, §4):
- proportion-style metric: CI brackets the value; small n → wide CI;
- continuous per-case (Dice-like) metric: CI via bootstrap;
- cluster bootstrap: n_clusters < n and CI WIDER than naive row bootstrap;
- determinism: identical CIs across runs;
- subgroup counts populated in `groups`;
- end-to-end wiring through `enforce` (power attached; env escape hatch; cluster).
"""

import os
import tempfile

import numpy as np
import pandas as pd
import pytest
import yaml

from venturalitica import enforce
from venturalitica.assurance.fairness.fairness_binary import calc_demographic_parity
from venturalitica.assurance.performance.metrics import calc_mean
from venturalitica.assurance.power import compute_power


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    """Run every test from a temp dir so `enforce` never writes its
    `.venturalitica/results.json` cache into the repository working tree
    (which would pollute other tests, e.g. the handshake probe summary)."""
    monkeypatch.chdir(tmp_path)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ci_width(power: dict) -> float:
    return float(power["ci_high"]) - float(power["ci_low"])


def _make_proportion_df(n_per_group: int, seed: int = 0) -> pd.DataFrame:
    """A small fairness df with two groups and a binary outcome."""
    rng = np.random.default_rng(seed)
    g0 = pd.DataFrame(
        {
            "outcome": rng.integers(0, 2, size=n_per_group),
            "group": 0,
        }
    )
    g1 = pd.DataFrame(
        {
            "outcome": rng.integers(0, 2, size=n_per_group),
            "group": 1,
        }
    )
    return pd.concat([g0, g1], ignore_index=True)


# ---------------------------------------------------------------------------
# 1. Proportion-style metric (demographic parity)
# ---------------------------------------------------------------------------

def test_proportion_metric_ci_brackets_value():
    df = _make_proportion_df(n_per_group=200, seed=1)
    kwargs = {"target": "outcome", "prediction": "outcome", "dimension": "group"}
    value = calc_demographic_parity(df, **kwargs)

    power = compute_power(df, calc_demographic_parity, kwargs, value=value,
                          dimension="group", n_boot=300, seed=42)

    # The point estimate sits inside the CI (allow tiny float slack).
    assert power["ci_low"] <= value + 1e-9
    assert power["ci_high"] >= value - 1e-9
    assert power["method"] == "bootstrap"
    assert power["n"] == len(df)
    assert power["n_clusters"] is None
    assert power["n_boot"] == 300
    assert power["seed"] == 42
    assert power["ci_level"] == 0.95


def test_proportion_metric_small_n_is_wide():
    """On a SMALL sample the CI must be wide (large sampling error)."""
    small = _make_proportion_df(n_per_group=8, seed=3)
    large = _make_proportion_df(n_per_group=600, seed=3)
    kwargs = {"target": "outcome", "prediction": "outcome", "dimension": "group"}

    p_small = compute_power(small, calc_demographic_parity, kwargs,
                            value=calc_demographic_parity(small, **kwargs),
                            dimension="group", n_boot=400, seed=42)
    p_large = compute_power(large, calc_demographic_parity, kwargs,
                            value=calc_demographic_parity(large, **kwargs),
                            dimension="group", n_boot=400, seed=42)

    # Small-n CI is meaningfully wide, and wider than the large-n CI.
    assert _ci_width(p_small) > 0.15
    assert _ci_width(p_small) > _ci_width(p_large)


# ---------------------------------------------------------------------------
# 2. Continuous per-case metric (Dice-like mean of a per-row score)
# ---------------------------------------------------------------------------

def test_continuous_per_case_metric_ci():
    rng = np.random.default_rng(7)
    # Per-row Dice-like scores in [0, 1].
    scores = np.clip(rng.normal(0.85, 0.08, size=120), 0, 1)
    df = pd.DataFrame({"dice": scores})
    kwargs = {"target": "dice"}
    value = calc_mean(df, **kwargs)

    power = compute_power(df, calc_mean, kwargs, value=value, n_boot=500, seed=42)

    assert power["method"] == "bootstrap"
    assert power["ci_low"] <= value <= power["ci_high"]
    assert _ci_width(power) > 0  # non-degenerate
    assert power["groups"] == {}  # no dimension → no subgroup counts


# ---------------------------------------------------------------------------
# 3. Cluster bootstrap: pseudoreplication handled (n_clusters < n, wider CI)
# ---------------------------------------------------------------------------

def test_cluster_bootstrap_widens_ci_vs_row():
    """Repeated rows per cluster: cluster bootstrap CI must be WIDER than the
    naive row bootstrap, and report n_clusters < n.

    Construct strong within-cluster correlation: each patient contributes many
    near-identical slices, so treating rows as independent (row bootstrap)
    badly understates the sampling error.
    """
    rng = np.random.default_rng(11)
    n_clusters = 12
    rows_per = 10
    patient_ids, dice = [], []
    for pid in range(n_clusters):
        base = rng.uniform(0.6, 0.95)  # per-patient level
        for _ in range(rows_per):
            patient_ids.append(pid)
            dice.append(np.clip(base + rng.normal(0, 0.005), 0, 1))
    df = pd.DataFrame({"patient_id": patient_ids, "dice": dice})
    kwargs = {"target": "dice"}
    value = calc_mean(df, **kwargs)

    p_row = compute_power(df, calc_mean, kwargs, value=value,
                          n_boot=600, seed=42)
    p_clu = compute_power(df, calc_mean, kwargs, value=value,
                          cluster="patient_id", n_boot=600, seed=42)

    assert p_row["method"] == "bootstrap"
    assert p_row["n_clusters"] is None

    assert p_clu["method"] == "cluster_bootstrap"
    assert p_clu["n_clusters"] == n_clusters
    assert p_clu["n"] == n_clusters * rows_per
    assert p_clu["n_clusters"] < p_clu["n"]

    # Pseudoreplication: cluster CI is strictly wider than the row CI.
    assert _ci_width(p_clu) > _ci_width(p_row)


# ---------------------------------------------------------------------------
# 4. Determinism — same input twice → byte-identical CIs
# ---------------------------------------------------------------------------

def test_determinism_identical_cis():
    df = _make_proportion_df(n_per_group=120, seed=5)
    kwargs = {"target": "outcome", "prediction": "outcome", "dimension": "group"}
    value = calc_demographic_parity(df, **kwargs)

    a = compute_power(df, calc_demographic_parity, kwargs, value=value,
                      dimension="group", n_boot=500, seed=42)
    b = compute_power(df, calc_demographic_parity, kwargs, value=value,
                      dimension="group", n_boot=500, seed=42)

    assert a["ci_low"] == b["ci_low"]
    assert a["ci_high"] == b["ci_high"]


def test_determinism_cluster_path():
    rng = np.random.default_rng(2)
    df = pd.DataFrame(
        {
            "patient_id": np.repeat(np.arange(15), 6),
            "dice": np.clip(rng.normal(0.8, 0.1, size=90), 0, 1),
        }
    )
    kwargs = {"target": "dice"}
    a = compute_power(df, calc_mean, kwargs, cluster="patient_id", n_boot=300, seed=42)
    b = compute_power(df, calc_mean, kwargs, cluster="patient_id", n_boot=300, seed=42)
    assert (a["ci_low"], a["ci_high"]) == (b["ci_low"], b["ci_high"])


def test_different_seeds_differ():
    df = _make_proportion_df(n_per_group=60, seed=9)
    kwargs = {"target": "outcome", "prediction": "outcome", "dimension": "group"}
    a = compute_power(df, calc_demographic_parity, kwargs, dimension="group",
                      n_boot=400, seed=42)
    b = compute_power(df, calc_demographic_parity, kwargs, dimension="group",
                      n_boot=400, seed=7)
    # Different seeds → (almost surely) different CIs.
    assert (a["ci_low"], a["ci_high"]) != (b["ci_low"], b["ci_high"])


# ---------------------------------------------------------------------------
# 5. Subgroup counts populated in `groups`
# ---------------------------------------------------------------------------

def test_subgroup_counts_populated():
    df = pd.DataFrame(
        {
            "outcome": [1, 0, 1, 1, 0, 1, 0],
            "group": ["A", "A", "A", "B", "B", "C", "C"],
        }
    )
    kwargs = {"target": "outcome", "prediction": "outcome", "dimension": "group"}
    power = compute_power(df, calc_demographic_parity, kwargs, dimension="group",
                          n_boot=50, seed=42)
    assert power["groups"] == {"A": 3, "B": 2, "C": 2}


def test_groups_empty_when_no_dimension():
    df = pd.DataFrame({"dice": [0.8, 0.9, 0.7]})
    power = compute_power(df, calc_mean, {"target": "dice"}, n_boot=20, seed=42)
    assert power["groups"] == {}


# ---------------------------------------------------------------------------
# 6. Robustness / guards
# ---------------------------------------------------------------------------

def test_metric_returning_tuple_is_handled():
    def calc_tuple(df, **kwargs):
        return float(df["dice"].mean()), {"extra": "meta"}

    df = pd.DataFrame({"dice": [0.7, 0.8, 0.9, 0.6, 0.85]})
    power = compute_power(df, calc_tuple, {}, n_boot=100, seed=42)
    assert power["ci_low"] <= df["dice"].mean() <= power["ci_high"]


def test_degenerate_resamples_dropped():
    """A metric that raises on some resamples must not abort the bootstrap."""
    state = {"calls": 0}

    def flaky(df, **kwargs):
        state["calls"] += 1
        if state["calls"] % 3 == 0:
            raise ValueError("degenerate resample")
        return float(df["v"].mean())

    df = pd.DataFrame({"v": [0.5, 0.6, 0.7, 0.4]})
    power = compute_power(df, flaky, {}, value=0.55, n_boot=60, seed=42)
    # Some resamples raised, yet we still got a finite CI.
    assert power["ci_low"] is not None and power["ci_high"] is not None
    assert power["ci_low"] <= power["ci_high"]


def test_empty_dataframe_guard():
    df = pd.DataFrame({"v": []})
    power = compute_power(df, calc_mean, {"target": "v"}, value=None, n_boot=10, seed=42)
    assert power["n"] == 0
    assert power["method"] == "bootstrap"


# ---------------------------------------------------------------------------
# End-to-end wiring through enforce()
# ---------------------------------------------------------------------------

def _write_policy(props, control_id="C1"):
    policy = {
        "component-definition": {
            "local-definitions": {
                "inventory-items": [{"uuid": "m1", "props": props}]
            },
            "components": [
                {
                    "control-implementations": [
                        {
                            "implemented-requirements": [
                                {
                                    "control-id": control_id,
                                    "description": "power test",
                                    "links": [{"href": "#m1", "rel": "related"}],
                                }
                            ]
                        }
                    ]
                }
            ],
        }
    }
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    yaml.dump(policy, f)
    f.close()
    return f.name


def test_enforce_attaches_power():
    df = _make_proportion_df(n_per_group=50, seed=4)
    path = _write_policy(
        [
            {"name": "metric_key", "value": "demographic_parity_diff"},
            {"name": "threshold", "value": "0.1"},
            {"name": "operator", "value": "lt"},
            {"name": "input.target", "value": "outcome"},
            {"name": "input.prediction", "value": "outcome"},
            {"name": "input.dimension", "value": "group"},
        ]
    )
    try:
        results = enforce(data=df, policy=path, target="outcome", prediction="outcome")
        assert len(results) == 1
        power = results[0].power
        assert power, "power dict must be populated on the metric path"
        assert set(power) == {
            "n", "n_clusters", "groups", "ci_low", "ci_high",
            "ci_level", "method", "n_boot", "seed",
        }
        assert power["n"] == len(df)
        assert power["method"] == "bootstrap"
        assert power["groups"] == {"0": 50, "1": 50}
        assert power["ci_low"] <= results[0].actual_value <= power["ci_high"]
    finally:
        os.unlink(path)


def test_enforce_power_escape_hatch(monkeypatch):
    monkeypatch.setenv("VENTURALITICA_POWER", "0")
    df = _make_proportion_df(n_per_group=30, seed=6)
    path = _write_policy(
        [
            {"name": "metric_key", "value": "demographic_parity_diff"},
            {"name": "threshold", "value": "0.1"},
            {"name": "operator", "value": "lt"},
            {"name": "input.target", "value": "outcome"},
            {"name": "input.prediction", "value": "outcome"},
            {"name": "input.dimension", "value": "group"},
        ]
    )
    try:
        results = enforce(data=df, policy=path, target="outcome", prediction="outcome")
        assert len(results) == 1
        assert results[0].power == {}  # escape hatch leaves it empty
    finally:
        os.unlink(path)


def test_enforce_cluster_binding_triggers_cluster_bootstrap():
    """A control declaring input.cluster runs a cluster bootstrap end-to-end."""
    rng = np.random.default_rng(13)
    df = pd.DataFrame(
        {
            "patient_id": np.repeat(np.arange(10), 5),
            "dice": np.clip(rng.normal(0.82, 0.05, size=50), 0, 1),
        }
    )
    path = _write_policy(
        [
            {"name": "metric_key", "value": "bias_score"},  # alias for calc_mean
            {"name": "threshold", "value": "0.7"},
            {"name": "operator", "value": "gt"},
            {"name": "input.target", "value": "dice"},
            {"name": "input.cluster", "value": "patient_id"},
        ]
    )
    try:
        results = enforce(data=df, policy=path, target="dice")
        assert len(results) == 1
        power = results[0].power
        assert power["method"] == "cluster_bootstrap"
        assert power["n_clusters"] == 10
        assert power["n"] == 50
    finally:
        os.unlink(path)


def test_enforce_missing_cluster_column_falls_back_to_row():
    """A declared cluster that doesn't resolve must NOT fail the control; it
    falls back to a row bootstrap (back-compat: optional input)."""
    df = pd.DataFrame({"dice": [0.8, 0.9, 0.7, 0.85, 0.75, 0.95]})
    path = _write_policy(
        [
            {"name": "metric_key", "value": "bias_score"},
            {"name": "threshold", "value": "0.5"},
            {"name": "operator", "value": "gt"},
            {"name": "input.target", "value": "dice"},
            {"name": "input.cluster", "value": "nonexistent_patient_col"},
        ]
    )
    try:
        results = enforce(data=df, policy=path, target="dice")
        assert len(results) == 1  # control still evaluated
        assert results[0].power["method"] == "bootstrap"
        assert results[0].power["n_clusters"] is None
    finally:
        os.unlink(path)


def test_enforce_custom_seed_param_is_deterministic():
    """input.power_seed is honored and never leaks into the metric kwargs."""
    df = _make_proportion_df(n_per_group=40, seed=8)
    props = [
        {"name": "metric_key", "value": "demographic_parity_diff"},
        {"name": "threshold", "value": "0.1"},
        {"name": "operator", "value": "lt"},
        {"name": "input.target", "value": "outcome"},
        {"name": "input.prediction", "value": "outcome"},
        {"name": "input.dimension", "value": "group"},
        {"name": "power_seed", "value": "123"},
    ]
    path = _write_policy(props)
    try:
        r1 = enforce(data=df, policy=path, target="outcome", prediction="outcome")
        r2 = enforce(data=df, policy=path, target="outcome", prediction="outcome")
        assert r1[0].power["seed"] == 123
        assert r1[0].power["ci_low"] == r2[0].power["ci_low"]
        assert r1[0].power["ci_high"] == r2[0].power["ci_high"]
    finally:
        os.unlink(path)
