"""Unit tests for the segmentation aggregate metrics (continuous per-case score).

These metrics (`mean_score`, `min_group_score`, `worst_cell_score`,
`group_score_gap`, `max_score`) turn a per-case score column (e.g. Dice per
scan) into first-class registry metrics. The key property under test: registered
in `METRIC_REGISTRY`, they flow through `enforce(data=df)` AND get a power-stats
CI attached automatically — cluster-aware when the control declares
`input.cluster`.
"""

import os
import tempfile

import numpy as np
import pandas as pd
import pytest
import yaml

from venturalitica import enforce
from venturalitica.assurance.segmentation import (
    calc_group_score_gap,
    calc_max_score,
    calc_mean_score,
    calc_min_group_score,
    calc_worst_cell_score,
)
from venturalitica.metrics import METRIC_REGISTRY


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    """Run each test from a temp dir so enforce never writes its results cache
    into the repo working tree."""
    monkeypatch.chdir(tmp_path)


# ---------------------------------------------------------------------------
# Synthetic per-case dataframe (Dice-like scores)
# ---------------------------------------------------------------------------

def _make_per_case_df(seed: int = 0) -> pd.DataFrame:
    """A per-case segmentation cohort: one row per scan, with a Dice column,
    scanner manufacturer, age band and a patient cluster id."""
    rng = np.random.default_rng(seed)
    rows = []
    # Two scanners with different quality levels, two age bands.
    config = {
        ("GE", "adult"): 0.90,
        ("GE", "elderly"): 0.85,
        ("Siemens", "adult"): 0.80,
        ("Siemens", "elderly"): 0.70,
    }
    pid = 0
    for (mfr, age), level in config.items():
        for _ in range(15):
            pid += 1
            # 2 slices per patient → exercises cluster bootstrap.
            for _ in range(2):
                rows.append(
                    {
                        "Dice": float(np.clip(level + rng.normal(0, 0.03), 0, 1)),
                        "Manufacturer": mfr,
                        "age_band": age,
                        "patient_id": pid,
                    }
                )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 1. Registry wiring
# ---------------------------------------------------------------------------

def test_metrics_registered():
    for key in (
        "mean_score",
        "min_group_score",
        "worst_cell_score",
        "group_score_gap",
        "max_score",
    ):
        assert key in METRIC_REGISTRY


# ---------------------------------------------------------------------------
# 2. Direct calc_* behaviour
# ---------------------------------------------------------------------------

def test_mean_score():
    df = pd.DataFrame({"Dice": [0.8, 0.9, 1.0]})
    assert calc_mean_score(df, score="Dice") == pytest.approx(0.9)


def test_mean_score_back_compat_target_role():
    """A control may bind the per-case column via input.target instead of score."""
    df = pd.DataFrame({"Dice": [0.6, 0.8]})
    assert calc_mean_score(df, target="Dice") == pytest.approx(0.7)


def test_min_group_score():
    df = pd.DataFrame(
        {"Dice": [0.9, 0.9, 0.6, 0.6], "Manufacturer": ["GE", "GE", "S", "S"]}
    )
    value, meta = calc_min_group_score(df, score="Dice", dimension="Manufacturer")
    assert value == pytest.approx(0.6)
    assert meta["groups"] == {"GE": pytest.approx(0.9), "S": pytest.approx(0.6)}


def test_worst_cell_score():
    df = pd.DataFrame(
        {
            "Dice": [0.95, 0.9, 0.7, 0.5],
            "Manufacturer": ["GE", "GE", "S", "S"],
            "age_band": ["adult", "elderly", "adult", "elderly"],
        }
    )
    value, meta = calc_worst_cell_score(
        df, score="Dice", dimensions=["Manufacturer", "age_band"]
    )
    # Worst cell is Siemens|elderly = 0.5.
    assert value == pytest.approx(0.5)
    assert meta["cells"]["S|elderly"] == pytest.approx(0.5)
    assert meta["cells"]["GE|adult"] == pytest.approx(0.95)


def test_worst_cell_score_comma_string_dimensions():
    df = pd.DataFrame(
        {
            "Dice": [0.9, 0.4],
            "Manufacturer": ["GE", "S"],
            "age_band": ["adult", "elderly"],
        }
    )
    value, _ = calc_worst_cell_score(
        df, score="Dice", dimensions="Manufacturer, age_band"
    )
    assert value == pytest.approx(0.4)


def test_group_score_gap():
    df = pd.DataFrame(
        {"Dice": [0.9, 0.9, 0.6, 0.6], "age_band": ["a", "a", "e", "e"]}
    )
    gap, meta = calc_group_score_gap(df, score="Dice", dimension="age_band")
    assert gap == pytest.approx(0.3)
    assert meta["max_group"] == "a"
    assert meta["min_group"] == "e"


def test_max_score():
    df = pd.DataFrame({"Dice": [0.8, 0.99, 0.7]})
    assert calc_max_score(df, score="Dice") == pytest.approx(0.99)


# ---------------------------------------------------------------------------
# 3. Error handling (so the enforce loop can skip / fail-fast)
# ---------------------------------------------------------------------------

def test_missing_score_raises():
    df = pd.DataFrame({"Dice": [0.8]})
    with pytest.raises(ValueError):
        calc_mean_score(df)


def test_score_column_absent_raises():
    df = pd.DataFrame({"Dice": [0.8]})
    with pytest.raises(KeyError):
        calc_mean_score(df, score="NotThere")


def test_missing_dimension_raises():
    df = pd.DataFrame({"Dice": [0.8]})
    with pytest.raises(ValueError):
        calc_min_group_score(df, score="Dice")


def test_worst_cell_missing_dimensions_raises():
    df = pd.DataFrame({"Dice": [0.8], "Manufacturer": ["GE"]})
    with pytest.raises(ValueError):
        calc_worst_cell_score(df, score="Dice")


# ---------------------------------------------------------------------------
# 4. End-to-end through enforce() — POWER MUST ATTACH (the headline behaviour)
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
                                    "description": "segmentation test",
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


def test_enforce_mean_score_attaches_power_with_cluster():
    """global_dice (mean_score) over a per-case df with input.cluster → the
    control gets a cluster-aware power-stats CI end-to-end."""
    df = _make_per_case_df(seed=1)
    path = _write_policy(
        [
            {"name": "metric_key", "value": "mean_score"},
            {"name": "threshold", "value": "0.7"},
            {"name": "operator", "value": "gt"},
            {"name": "input.score", "value": "Dice"},
            {"name": "input.cluster", "value": "patient_id"},
        ]
    )
    try:
        results = enforce(data=df, policy=path)
        assert len(results) == 1
        r = results[0]
        assert r.actual_value == pytest.approx(df["Dice"].mean())
        power = r.power
        assert power, "power dict must be populated on the data path"
        assert set(power) == {
            "n", "n_clusters", "groups", "ci_low", "ci_high",
            "ci_level", "method", "n_boot", "seed",
        }
        # Cluster-aware: bootstrap resamples whole patients.
        assert power["method"] == "cluster_bootstrap"
        assert power["n"] == len(df)
        assert power["n_clusters"] == df["patient_id"].nunique()
        # The point estimate sits inside its CI.
        assert power["ci_low"] <= r.actual_value <= power["ci_high"]
        assert power["ci_low"] < power["ci_high"]  # non-degenerate
    finally:
        os.unlink(path)


def test_enforce_min_group_score_attaches_power_and_groups():
    """min-scanner-dice: min_group_score over Manufacturer; power reports the
    subgroup counts in `groups`."""
    df = _make_per_case_df(seed=2)
    path = _write_policy(
        [
            {"name": "metric_key", "value": "min_group_score"},
            {"name": "threshold", "value": "0.6"},
            {"name": "operator", "value": "gt"},
            {"name": "input.score", "value": "Dice"},
            {"name": "input.dimension", "value": "Manufacturer"},
            {"name": "input.cluster", "value": "patient_id"},
        ]
    )
    try:
        results = enforce(data=df, policy=path)
        assert len(results) == 1
        r = results[0]
        # Per-group means came back as metadata.
        assert "groups" in r.metadata
        assert set(r.metadata["groups"]) == {"GE", "Siemens"}
        # Power reports per-subgroup row counts.
        assert r.power["method"] == "cluster_bootstrap"
        assert set(r.power["groups"]) == {"GE", "Siemens"}
        assert r.power["ci_low"] <= r.actual_value <= r.power["ci_high"]
    finally:
        os.unlink(path)


def test_enforce_worst_cell_score_with_dimensions_param():
    """worst_subgroup_dice: dimensions list arrives via control params and the
    composite-cell minimum is computed; power still attaches."""
    df = _make_per_case_df(seed=3)
    path = _write_policy(
        [
            {"name": "metric_key", "value": "worst_cell_score"},
            {"name": "threshold", "value": "0.5"},
            {"name": "operator", "value": "gt"},
            {"name": "input.score", "value": "Dice"},
            {"name": "dimensions", "value": ["Manufacturer", "age_band"]},
        ]
    )
    try:
        results = enforce(data=df, policy=path)
        assert len(results) == 1
        r = results[0]
        # Worst cell is Siemens|elderly (~0.70).
        assert r.actual_value < df["Dice"].mean()
        assert "cells" in r.metadata
        assert r.power, "power must attach for worst_cell_score"
        assert r.power["ci_low"] <= r.actual_value <= r.power["ci_high"]
    finally:
        os.unlink(path)


def test_enforce_group_score_gap():
    df = _make_per_case_df(seed=4)
    path = _write_policy(
        [
            {"name": "metric_key", "value": "group_score_gap"},
            {"name": "threshold", "value": "0.2"},
            {"name": "operator", "value": "lt"},
            {"name": "input.score", "value": "Dice"},
            {"name": "input.dimension", "value": "age_band"},
        ]
    )
    try:
        results = enforce(data=df, policy=path)
        assert len(results) == 1
        r = results[0]
        assert r.actual_value > 0  # there IS a gap between adult/elderly
        assert r.power["ci_low"] <= r.actual_value <= r.power["ci_high"]
    finally:
        os.unlink(path)


def test_enforce_max_score():
    df = _make_per_case_df(seed=5)
    path = _write_policy(
        [
            {"name": "metric_key", "value": "max_score"},
            {"name": "threshold", "value": "0.999"},
            {"name": "operator", "value": "lt"},
            {"name": "input.score", "value": "Dice"},
        ]
    )
    try:
        results = enforce(data=df, policy=path)
        assert len(results) == 1
        r = results[0]
        assert r.actual_value == pytest.approx(df["Dice"].max())
        assert r.power, "power must attach for max_score"
    finally:
        os.unlink(path)
