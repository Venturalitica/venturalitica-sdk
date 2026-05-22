"""Unit tests for the torch-free segmentation-fairness metrics.

ESSP/ES-Dice (FairSeg, ICLR 2024) and the subgroup-disparity family
(gap/ratio/std/cv/worst-group/skew, incl. DSC Skewness from FairMedFM) operate
on a per-case continuous SCORE column + a group dimension — NOT on masks. They
are registered in METRIC_REGISTRY so `enforce(data=df)` attaches a power-stats CI
automatically. No monai/torch needed for any of these.
"""

import os
import tempfile

import numpy as np
import pandas as pd
import pytest
import yaml
from scipy import stats as _scipy_stats

from venturalitica import enforce
from venturalitica.assurance.segmentation import (
    calc_es_dice,
    calc_essp,
    calc_essp_stdev,
    calc_score_cv,
    calc_score_gap,
    calc_score_ratio,
    calc_score_skew,
    calc_score_std,
    calc_subgroup_disparity,
)
from venturalitica.metrics import METRIC_REGISTRY


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _make_df(group_levels: dict, n_per: int = 20, seed: int = 0) -> pd.DataFrame:
    """Per-case df: one row per case, a Dice score per group at a target level."""
    rng = np.random.default_rng(seed)
    rows = []
    pid = 0
    for g, level in group_levels.items():
        for _ in range(n_per):
            pid += 1
            rows.append(
                {
                    "Dice": float(np.clip(level + rng.normal(0, 0.01), 0, 1)),
                    "Sex": g,
                    "patient_id": pid,
                }
            )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Registry wiring
# ---------------------------------------------------------------------------

def test_fairness_metrics_registered():
    for key in (
        "essp",
        "es_dice",
        "es_iou",
        "essp_stdev",
        "subgroup_disparity",
        "score_gap",
        "score_ratio",
        "score_std",
        "score_cv",
        "score_skew",
        "worst_group_score",
    ):
        assert key in METRIC_REGISTRY


# ---------------------------------------------------------------------------
# ESSP / ES-Dice formula (FairSeg)
# ---------------------------------------------------------------------------

def test_essp_equals_overall_when_fair():
    """No disparity → ESSP == overall mean I."""
    df = pd.DataFrame({"Dice": [0.8] * 6, "Sex": ["M", "M", "M", "F", "F", "F"]})
    val, meta = calc_essp(df, score="Dice", dimension="Sex")
    assert val == pytest.approx(0.8)
    assert meta["disparity_sum"] == pytest.approx(0.0)
    assert val == pytest.approx(meta["overall"])


def test_essp_formula_exact():
    """ESSP = I / (1 + Σ_g |I − I_g|), checked by hand.

    Groups: M mean=0.9 (n=2), F mean=0.6 (n=2). Overall I = 0.75.
    Σ|I−I_g| = |0.75−0.9| + |0.75−0.6| = 0.15 + 0.15 = 0.30.
    ESSP = 0.75 / 1.30.
    """
    df = pd.DataFrame(
        {"Dice": [0.9, 0.9, 0.6, 0.6], "Sex": ["M", "M", "F", "F"]}
    )
    val, meta = calc_essp(df, score="Dice", dimension="Sex")
    assert meta["overall"] == pytest.approx(0.75)
    assert meta["disparity_sum"] == pytest.approx(0.30)
    assert val == pytest.approx(0.75 / 1.30)
    # ESSP ≤ I.
    assert val <= meta["overall"]


def test_essp_penalizes_disparity():
    fair = _make_df({"M": 0.8, "F": 0.8}, seed=1)
    unfair = _make_df({"M": 0.9, "F": 0.6}, seed=1)
    v_fair, _ = calc_essp(fair, score="Dice", dimension="Sex")
    v_unfair, _ = calc_essp(unfair, score="Dice", dimension="Sex")
    assert v_fair > v_unfair


def test_es_dice_alias_matches_essp():
    df = _make_df({"M": 0.9, "F": 0.6}, seed=2)
    assert calc_es_dice(df, score="Dice", dimension="Sex")[0] == pytest.approx(
        calc_essp(df, score="Dice", dimension="Sex")[0]
    )


def test_essp_stdev_variant():
    df = pd.DataFrame(
        {"Dice": [0.9, 0.9, 0.6, 0.6], "Sex": ["M", "M", "F", "F"]}
    )
    val, meta = calc_essp_stdev(df, score="Dice", dimension="Sex")
    # group means [0.9, 0.6] → population std = 0.15. ESSP = 0.75 / 1.15.
    assert meta["group_std"] == pytest.approx(0.15)
    assert val == pytest.approx(0.75 / 1.15)


# ---------------------------------------------------------------------------
# Subgroup disparities
# ---------------------------------------------------------------------------

def test_subgroup_disparity_all_measures():
    df = pd.DataFrame(
        {"Dice": [0.9, 0.9, 0.6, 0.6], "Sex": ["M", "M", "F", "F"]}
    )
    val, meta = calc_subgroup_disparity(df, score="Dice", dimension="Sex")
    # default measure = gap = 0.9 - 0.6 = 0.3
    assert val == pytest.approx(0.3)
    assert meta["gap"] == pytest.approx(0.3)
    assert meta["ratio"] == pytest.approx(0.6 / 0.9)
    assert meta["std"] == pytest.approx(0.15)
    assert meta["cv"] == pytest.approx(0.15 / 0.75)
    assert meta["worst_group"] == pytest.approx(0.6)
    assert meta["measure"] == "gap"


def test_subgroup_disparity_select_measure():
    df = pd.DataFrame(
        {"Dice": [0.9, 0.9, 0.6, 0.6], "Sex": ["M", "M", "F", "F"]}
    )
    val, _ = calc_subgroup_disparity(
        df, score="Dice", dimension="Sex", measure="ratio"
    )
    assert val == pytest.approx(0.6 / 0.9)


def test_subgroup_disparity_unknown_measure_raises():
    df = pd.DataFrame({"Dice": [0.9, 0.6], "Sex": ["M", "F"]})
    with pytest.raises(ValueError):
        calc_subgroup_disparity(df, score="Dice", dimension="Sex", measure="bogus")


def test_score_gap_ratio_std_cv():
    df = pd.DataFrame(
        {"Dice": [0.9, 0.9, 0.6, 0.6], "Sex": ["M", "M", "F", "F"]}
    )
    assert calc_score_gap(df, score="Dice", dimension="Sex")[0] == pytest.approx(0.3)
    assert calc_score_ratio(df, score="Dice", dimension="Sex")[0] == pytest.approx(
        0.6 / 0.9
    )
    assert calc_score_std(df, score="Dice", dimension="Sex")[0] == pytest.approx(0.15)
    assert calc_score_cv(df, score="Dice", dimension="Sex")[0] == pytest.approx(
        0.15 / 0.75
    )


def test_score_skew_matches_scipy():
    """DSC Skewness == Fisher-Pearson skewness of the per-group means."""
    # 4 groups with an asymmetric (left-skewed) profile of means.
    means = {"A": 0.9, "B": 0.88, "C": 0.86, "D": 0.5}
    df = _make_df(means, n_per=10, seed=7)
    val, _ = calc_score_skew(df, score="Dice", dimension="Sex")
    group_means = df.groupby("Sex")["Dice"].mean().to_numpy()
    expected = float(_scipy_stats.skew(group_means, bias=True))
    assert val == pytest.approx(expected, abs=1e-6)
    # A long low tail (group D) → negative skew.
    assert val < 0


def test_score_skew_zero_for_two_groups():
    df = pd.DataFrame({"Dice": [0.9, 0.6], "Sex": ["M", "F"]})
    assert calc_score_skew(df, score="Dice", dimension="Sex")[0] == 0.0


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_missing_dimension_raises():
    df = pd.DataFrame({"Dice": [0.8]})
    with pytest.raises(ValueError):
        calc_essp(df, score="Dice")


def test_missing_score_raises():
    df = pd.DataFrame({"Dice": [0.8], "Sex": ["M"]})
    with pytest.raises(ValueError):
        calc_essp(df, dimension="Sex")


# ---------------------------------------------------------------------------
# End-to-end through enforce() with power-stats CI
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
                                    "description": "fairness test",
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


def test_enforce_es_dice_attaches_power():
    """fairness-sex via es_dice over score=Dice dimension=Sex, cluster-aware."""
    df = _make_df({"M": 0.9, "F": 0.6}, n_per=25, seed=3)
    path = _write_policy(
        [
            {"name": "metric_key", "value": "es_dice"},
            {"name": "threshold", "value": "0.6"},
            {"name": "operator", "value": "gt"},
            {"name": "input.score", "value": "Dice"},
            {"name": "input.dimension", "value": "Sex"},
            {"name": "input.cluster", "value": "patient_id"},
        ]
    )
    try:
        results = enforce(data=df, policy=path)
        assert len(results) == 1
        r = results[0]
        assert r.power, "power must attach for es_dice"
        assert r.power["method"] == "cluster_bootstrap"
        assert set(r.power["groups"]) == {"M", "F"}
        assert r.power["ci_low"] <= r.actual_value <= r.power["ci_high"]
        # ES-Dice carries the per-group means as metadata.
        assert set(r.metadata["groups"]) == {"M", "F"}
    finally:
        os.unlink(path)


def test_enforce_score_skew_actionable_when_ci_excludes_zero():
    """A real disparity → score_skew CI should be informative; a fair cohort →
    skew near 0. We assert power attaches and the CI brackets the value."""
    df = _make_df({"A": 0.9, "B": 0.88, "C": 0.86, "D": 0.5}, n_per=20, seed=5)
    path = _write_policy(
        [
            {"name": "metric_key", "value": "score_skew"},
            {"name": "threshold", "value": "-0.5"},
            {"name": "operator", "value": "gt"},
            {"name": "input.score", "value": "Dice"},
            {"name": "input.dimension", "value": "Sex"},
        ]
    )
    try:
        results = enforce(data=df, policy=path)
        assert len(results) == 1
        r = results[0]
        assert r.power, "power must attach for score_skew"
        assert r.power["ci_low"] <= r.actual_value <= r.power["ci_high"]
    finally:
        os.unlink(path)


def test_enforce_score_gap_power():
    df = _make_df({"M": 0.9, "F": 0.6}, n_per=30, seed=8)
    path = _write_policy(
        [
            {"name": "metric_key", "value": "score_gap"},
            {"name": "threshold", "value": "0.05"},
            {"name": "operator", "value": "lt"},
            {"name": "input.score", "value": "Dice"},
            {"name": "input.dimension", "value": "Sex"},
        ]
    )
    try:
        results = enforce(data=df, policy=path)
        assert len(results) == 1
        r = results[0]
        assert r.actual_value > 0  # there IS a gap
        assert r.power["ci_low"] <= r.actual_value <= r.power["ci_high"]
    finally:
        os.unlink(path)
