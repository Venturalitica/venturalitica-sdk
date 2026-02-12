import pandas as pd
import pytest

from venturalitica.metrics import (
    METRIC_REGISTRY,
    calc_accuracy,
    calc_class_imbalance,
    calc_demographic_parity,
    calc_disparate_impact,
    calc_equal_opportunity,
    calc_f1,
    calc_mean,
    calc_precision,
    calc_recall,
)


@pytest.fixture
def sample_data():
    return pd.DataFrame(
        {
            "target": [1, 0, 1, 1, 0, 0, 1, 0],
            "prediction": [1, 0, 0, 1, 1, 0, 1, 0],
            "sensitive": ["A", "A", "A", "A", "B", "B", "B", "B"],
        }
    )


def test_standard_metrics(sample_data):
    kwargs = {"target": "target", "prediction": "prediction"}
    assert calc_accuracy(sample_data, **kwargs) == 0.75
    assert (
        calc_precision(sample_data, **kwargs) == 0.75
    )  # TP=3 (idx 0,3,6), FP=1 (idx 4)
    assert calc_recall(sample_data, **kwargs) == 0.75  # TP=3, FN=1 (idx 2)
    assert calc_f1(sample_data, **kwargs) == 0.75


def test_demographic_parity(sample_data):
    kwargs = {"target": "target", "prediction": "prediction", "dimension": "sensitive"}
    # Group A: [1, 0, 0, 1] -> mean = 0.5
    # Group B: [1, 0, 1, 0] -> mean = 0.5
    # Diff = 0.0
    assert calc_demographic_parity(sample_data, **kwargs) == 0.0


def test_equal_opportunity(sample_data):
    kwargs = {"target": "target", "prediction": "prediction", "dimension": "sensitive"}
    # Group A positive: idx 0, 2, 3 -> preds [1, 0, 1] -> mean = 0.666...
    # Group B positive: idx 6 -> preds [1] -> mean = 1.0
    # Diff = 0.333...
    res = calc_equal_opportunity(sample_data, **kwargs)
    assert pytest.approx(res) == 0.3333333333333333


def test_disparate_impact(sample_data):
    # Need >5 samples per group for filtered check, so replicate data
    large_data = pd.concat([sample_data] * 5, ignore_index=True)
    kwargs = {"target": "target", "dimension": "sensitive"}
    # Group A target: [1, 0, 1, 1] * 5 -> mean = 0.75
    # Group B target: [0, 0, 1, 0] * 5 -> mean = 0.25
    # Ratio = 0.25 / 0.75 = 0.333...
    res = calc_disparate_impact(large_data, **kwargs)
    assert pytest.approx(res) == 0.3333333333333333


def test_class_imbalance(sample_data):
    kwargs = {"target": "target"}
    # 4 ones, 4 zeros -> ratio 1.0
    assert calc_class_imbalance(sample_data, **kwargs) == 1.0


def test_registry():
    assert "accuracy_score" in METRIC_REGISTRY
    assert "disparate_impact" in METRIC_REGISTRY


def test_missing_cols(sample_data):
    # Performance metrics return 0.0 if missing columns
    assert calc_accuracy(sample_data, target="MISSING") == 0.0

    # Fairness metrics now raise ValueError on missing columns (Strict Validation)
    with pytest.raises(ValueError, match="Missing.*columns"):
        calc_demographic_parity(sample_data, dimension="MISSING")

    with pytest.raises(ValueError):
        calc_equal_opportunity(sample_data, dimension="MISSING")

    # Disparate impact returns 1.0 on missing columns (safe fallback in data.py/quality.py)
    assert calc_disparate_impact(sample_data, target="MISSING") == 1.0


def test_class_imbalance_edge_cases():
    df = pd.DataFrame({"t": [1, 1, 1]})
    assert calc_class_imbalance(df, target="t") == 0.0

    with pytest.raises(ValueError):
        calc_class_imbalance(df, target="MISSING")


def test_disparate_impact_edge_cases():
    df = pd.DataFrame({"t": [0, 0], "d": ["A", "B"]})
    assert calc_disparate_impact(df, target="t", dimension="d") == 1.0

    df_one = pd.DataFrame({"t": [1], "d": ["A"]})
    assert calc_disparate_impact(df_one, target="t", dimension="d") == 1.0

    # Missing columns - gracefully returns 1.0
    assert calc_disparate_impact(df, target="missing", dimension="d") == 1.0
    assert calc_disparate_impact(df, target="t", dimension="missing") == 1.0


# ============================================================================
# PERFORMANCE METRICS: MISSING sentinel & edge-case coverage
# ============================================================================


class TestAccuracyEdgeCases:
    """Covers lines 7-10 of performance/metrics.py."""

    def test_target_missing_sentinel(self, sample_data):
        assert (
            calc_accuracy(sample_data, target="MISSING", prediction="prediction") == 0.0
        )

    def test_prediction_missing_sentinel(self, sample_data):
        assert calc_accuracy(sample_data, target="target", prediction="MISSING") == 0.0

    def test_both_missing_sentinels(self, sample_data):
        assert calc_accuracy(sample_data, target="MISSING", prediction="MISSING") == 0.0

    def test_target_none(self, sample_data):
        assert calc_accuracy(sample_data, prediction="prediction") == 0.0

    def test_prediction_none(self, sample_data):
        assert calc_accuracy(sample_data, target="target") == 0.0

    def test_target_not_in_df(self, sample_data):
        assert (
            calc_accuracy(sample_data, target="no_col", prediction="prediction") == 0.0
        )

    def test_prediction_not_in_df(self, sample_data):
        assert calc_accuracy(sample_data, target="target", prediction="no_col") == 0.0


class TestPrecisionEdgeCases:
    """Covers lines 16-21 of performance/metrics.py."""

    def test_target_missing_sentinel(self, sample_data):
        assert (
            calc_precision(sample_data, target="MISSING", prediction="prediction")
            == 0.0
        )

    def test_prediction_missing_sentinel(self, sample_data):
        assert calc_precision(sample_data, target="target", prediction="MISSING") == 0.0

    def test_target_none(self, sample_data):
        assert calc_precision(sample_data, prediction="prediction") == 0.0

    def test_target_not_in_df(self, sample_data):
        assert (
            calc_precision(sample_data, target="no_col", prediction="prediction") == 0.0
        )

    def test_prediction_not_in_df(self, sample_data):
        assert calc_precision(sample_data, target="target", prediction="no_col") == 0.0

    def test_macro_average(self, sample_data):
        result = calc_precision(
            sample_data, target="target", prediction="prediction", average="macro"
        )
        assert isinstance(result, float) and 0 <= result <= 1

    def test_weighted_average(self, sample_data):
        result = calc_precision(
            sample_data, target="target", prediction="prediction", average="weighted"
        )
        assert isinstance(result, float) and 0 <= result <= 1


class TestRecallEdgeCases:
    """Covers lines 26-31 of performance/metrics.py."""

    def test_target_missing_sentinel(self, sample_data):
        assert (
            calc_recall(sample_data, target="MISSING", prediction="prediction") == 0.0
        )

    def test_prediction_missing_sentinel(self, sample_data):
        assert calc_recall(sample_data, target="target", prediction="MISSING") == 0.0

    def test_target_none(self, sample_data):
        assert calc_recall(sample_data, prediction="prediction") == 0.0

    def test_target_not_in_df(self, sample_data):
        assert calc_recall(sample_data, target="no_col", prediction="prediction") == 0.0

    def test_prediction_not_in_df(self, sample_data):
        assert calc_recall(sample_data, target="target", prediction="no_col") == 0.0

    def test_macro_average(self, sample_data):
        result = calc_recall(
            sample_data, target="target", prediction="prediction", average="macro"
        )
        assert isinstance(result, float) and 0 <= result <= 1


class TestF1EdgeCases:
    """Covers lines 36-41 of performance/metrics.py."""

    def test_target_missing_sentinel(self, sample_data):
        assert calc_f1(sample_data, target="MISSING", prediction="prediction") == 0.0

    def test_prediction_missing_sentinel(self, sample_data):
        assert calc_f1(sample_data, target="target", prediction="MISSING") == 0.0

    def test_target_none(self, sample_data):
        assert calc_f1(sample_data, prediction="prediction") == 0.0

    def test_target_not_in_df(self, sample_data):
        assert calc_f1(sample_data, target="no_col", prediction="prediction") == 0.0

    def test_prediction_not_in_df(self, sample_data):
        assert calc_f1(sample_data, target="target", prediction="no_col") == 0.0

    def test_macro_average(self, sample_data):
        result = calc_f1(
            sample_data, target="target", prediction="prediction", average="macro"
        )
        assert isinstance(result, float) and 0 <= result <= 1


class TestCalcMean:
    """Covers lines 43-48 of performance/metrics.py."""

    def test_basic_mean(self):
        df = pd.DataFrame({"score": [1.0, 2.0, 3.0]})
        assert calc_mean(df, target="score") == pytest.approx(2.0)

    def test_target_none(self):
        df = pd.DataFrame({"score": [1.0, 2.0]})
        assert calc_mean(df) == 0.0

    def test_target_missing_sentinel(self):
        df = pd.DataFrame({"score": [1.0, 2.0]})
        assert calc_mean(df, target="MISSING") == 0.0

    def test_target_not_in_df(self):
        df = pd.DataFrame({"score": [1.0, 2.0]})
        assert calc_mean(df, target="no_col") == 0.0

    def test_single_value(self):
        df = pd.DataFrame({"v": [42.0]})
        assert calc_mean(df, target="v") == 42.0

    def test_negative_values(self):
        df = pd.DataFrame({"v": [-1.0, 1.0]})
        assert calc_mean(df, target="v") == pytest.approx(0.0)
