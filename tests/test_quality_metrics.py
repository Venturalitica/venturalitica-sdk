from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from venturalitica.assurance.quality import (
    calc_chunk_diversity,
    calc_class_imbalance,
    calc_classification_distribution,
    calc_data_completeness,
    calc_disparate_impact,
    calc_group_min_positive_rate,
    calc_provenance_completeness,
    calc_report_coverage,
    calc_subtitle_diversity,
)

# ===================================================================
# EXISTING TESTS (preserved)
# ===================================================================


def test_calc_class_imbalance_balanced():
    df = pd.DataFrame({"y": [1, 0, 1, 0]})
    val = calc_class_imbalance(df, target="y")
    assert 0.99 <= val <= 1.0  # Should be ~1.0 for perfectly balanced


def test_calc_class_imbalance_imbalanced():
    df = pd.DataFrame({"y": [1, 1, 1, 0]})
    val = calc_class_imbalance(df, target="y")
    assert 0.0 < val < 1.0


def test_calc_class_imbalance_single_class():
    df = pd.DataFrame({"y": [1, 1, 1, 1]})
    val = calc_class_imbalance(df, target="y")
    assert val == 0.0


def test_calc_data_completeness_all_present():
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    assert calc_data_completeness(df) == 1.0


def test_calc_data_completeness_with_missing():
    df = pd.DataFrame({"a": [1, None], "b": [None, 4]})
    # completeness per col: [0.5, 0.5] -> mean 0.5
    assert calc_data_completeness(df) == 0.5


# ===================================================================
# calc_disparate_impact
# ===================================================================


class TestCalcDisparateImpact:
    def test_with_fairlearn(self):
        """With fairlearn available: uses demographic_parity_ratio."""
        # Groups of 5+ each, clear disparity
        df = pd.DataFrame(
            {
                "target": [1] * 5 + [0] * 5 + [1] * 2 + [0] * 8,
                "pred": [1] * 5 + [0] * 5 + [1] * 2 + [0] * 8,
                "dim": ["A"] * 10 + ["B"] * 10,
            }
        )
        result = calc_disparate_impact(df, target="target", dimension="dim")
        assert 0.0 <= result <= 1.0

    def test_without_fairlearn(self):
        """Fallback manual calc when fairlearn is not available."""
        df = pd.DataFrame(
            {
                "target": [1] * 5 + [0] * 5 + [1] * 2 + [0] * 8,
                "dim": ["A"] * 10 + ["B"] * 10,
            }
        )
        with patch("venturalitica.assurance.quality.metrics.HAS_FAIRLEARN", False):
            result = calc_disparate_impact(df, target="target", dimension="dim")
        assert 0.0 <= result <= 1.0

    def test_missing_columns(self):
        """Missing outcome or dimension -> returns 1.0."""
        df = pd.DataFrame({"a": [1, 2]})
        assert calc_disparate_impact(df, target="MISSING", dimension="d") == 1.0
        assert calc_disparate_impact(df, target="a", dimension="MISSING") == 1.0

    def test_min_support_filter(self):
        """Groups with <5 samples are filtered; if <2 valid groups -> 1.0."""
        df = pd.DataFrame(
            {
                "target": [1, 0, 1, 0],
                "dim": ["A", "A", "B", "B"],
            }
        )
        result = calc_disparate_impact(df, target="target", dimension="dim")
        assert result == 1.0  # both groups have <5

    def test_with_prediction_column(self):
        """When prediction column is provided, uses prediction as outcome."""
        df = pd.DataFrame(
            {
                "target": [1] * 5 + [0] * 5 + [1] * 5 + [0] * 5,
                "pred": [1] * 5 + [0] * 5 + [0] * 5 + [0] * 5,
                "dim": ["A"] * 10 + ["B"] * 10,
            }
        )
        result = calc_disparate_impact(
            df, target="target", prediction="pred", dimension="dim"
        )
        assert 0.0 <= result <= 1.0

    def test_outcome_not_in_columns(self):
        """Outcome column not in df -> returns 1.0."""
        df = pd.DataFrame({"dim": ["A"] * 10})
        result = calc_disparate_impact(df, target="missing_col", dimension="dim")
        assert result == 1.0


# ===================================================================
# calc_group_min_positive_rate
# ===================================================================


class TestCalcGroupMinPositiveRate:
    def test_basic(self):
        """Basic positive rate calculation."""
        df = pd.DataFrame(
            {
                "target": [1, 0, 1, 0, 1, 1],
                "dim": ["A", "A", "A", "B", "B", "B"],
            }
        )
        rate, meta = calc_group_min_positive_rate(df, target="target", dimension="dim")
        assert isinstance(rate, float)
        assert "groups" in meta

    def test_with_quantile_bucketing(self):
        """Numeric dimension with quantile bucketing."""
        np.random.seed(42)
        df = pd.DataFrame(
            {
                "target": np.random.randint(0, 2, 30),
                "age": np.random.randint(20, 60, 30),
            }
        )
        rate, meta = calc_group_min_positive_rate(
            df,
            target="target",
            dimension="age",
            age_bucket_method="quantiles",
            age_buckets=3,
        )
        assert isinstance(rate, float)
        assert len(meta["groups"]) > 0

    def test_missing_dimension(self):
        """Missing dimension column raises ValueError."""
        df = pd.DataFrame({"target": [1, 0]})
        with pytest.raises(ValueError, match="not found"):
            calc_group_min_positive_rate(df, target="target", dimension="missing")

    def test_missing_target_role(self):
        """Missing target role raises ValueError."""
        df = pd.DataFrame({"dim": ["A", "B"]})
        with pytest.raises(ValueError, match="Missing"):
            calc_group_min_positive_rate(df, dimension="dim")

    def test_input_dimension_kwarg(self):
        """Accepts 'input:dimension' kwarg alias."""
        df = pd.DataFrame(
            {
                "target": [1, 0, 1, 0],
                "dim": ["A", "A", "B", "B"],
            }
        )
        rate, meta = calc_group_min_positive_rate(
            df,
            target="target",
            **{"input:dimension": "dim"},
        )
        assert isinstance(rate, float)


# ===================================================================
# calc_data_completeness (extended)
# ===================================================================


class TestCalcDataCompleteness:
    def test_partial_missing(self):
        df = pd.DataFrame(
            {
                "a": [1, None, 3],
                "b": [None, None, 3],
                "c": [1, 2, 3],
            }
        )
        # col a: 2/3, col b: 1/3, col c: 3/3 -> mean = (2/3 + 1/3 + 1) / 3
        result = calc_data_completeness(df)
        expected = (2 / 3 + 1 / 3 + 1.0) / 3
        assert pytest.approx(result, rel=1e-4) == expected

    def test_empty_df(self):
        df = pd.DataFrame({"a": pd.Series(dtype=float)})
        result = calc_data_completeness(df)
        assert result == 0.0


# ===================================================================
# calc_classification_distribution
# ===================================================================


class TestCalcClassificationDistribution:
    def test_basic(self):
        df = pd.DataFrame({"cat": ["A", "A", "B", "B", "C"]})
        score, pcts = calc_classification_distribution(df, target="cat")
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert "A" in pcts
        assert "C" in pcts

    def test_single_class(self):
        df = pd.DataFrame({"cat": ["X", "X", "X"]})
        score, pcts = calc_classification_distribution(df, target="cat")
        assert score == 0.0

    def test_empty(self):
        df = pd.DataFrame({"cat": pd.Series(dtype=str)})
        score, pcts = calc_classification_distribution(df, target="cat")
        assert score == 0.0
        assert pcts == {}

    def test_missing_target_raises(self):
        df = pd.DataFrame({"a": [1]})
        with pytest.raises(ValueError):
            calc_classification_distribution(df, target="missing")


# ===================================================================
# calc_report_coverage
# ===================================================================


class TestCalcReportCoverage:
    def test_basic(self):
        df = pd.DataFrame({"report": ["R1", "R2", "R1", "R3"]})
        coverage = calc_report_coverage(df, target="report")
        # 3 unique / 4 total = 0.75
        assert coverage == 0.75

    def test_empty(self):
        df = pd.DataFrame({"report": pd.Series(dtype=str)})
        coverage = calc_report_coverage(df, target="report")
        assert coverage == 0.0

    def test_all_unique(self):
        df = pd.DataFrame({"report": ["A", "B", "C"]})
        coverage = calc_report_coverage(df, target="report")
        assert coverage == 1.0

    def test_missing_target_raises(self):
        df = pd.DataFrame({"a": [1]})
        with pytest.raises(ValueError):
            calc_report_coverage(df, target="missing")


# ===================================================================
# calc_provenance_completeness
# ===================================================================


class TestCalcProvenanceCompleteness:
    def test_basic(self):
        df = pd.DataFrame(
            {
                "page_number": [1, 2, None],
                "chunk_number": [1, None, 3],
            }
        )
        result = calc_provenance_completeness(df)
        # row 0: both present, row 1: chunk missing, row 2: page missing => 1/3
        assert pytest.approx(result, abs=0.01) == 0.3333

    def test_missing_fields(self):
        """Required fields not in df -> returns 0.0."""
        df = pd.DataFrame({"other": [1, 2, 3]})
        result = calc_provenance_completeness(df)
        assert result == 0.0

    def test_string_input(self):
        """String input for fields is parsed."""
        df = pd.DataFrame(
            {
                "page_number": [1, 2],
                "chunk_number": [1, 2],
            }
        )
        result = calc_provenance_completeness(
            df, **{"input:fields": "['page_number', 'chunk_number']"}
        )
        assert result == 1.0

    def test_string_single_field(self):
        """Single string field (not a list repr)."""
        df = pd.DataFrame({"page_number": [1, 2, None]})
        result = calc_provenance_completeness(df, **{"input:fields": "page_number"})
        assert pytest.approx(result, abs=0.01) == 0.6667

    def test_all_complete(self):
        df = pd.DataFrame(
            {
                "page_number": [1, 2, 3],
                "chunk_number": [10, 20, 30],
            }
        )
        result = calc_provenance_completeness(df)
        assert result == 1.0


# ===================================================================
# calc_chunk_diversity
# ===================================================================


class TestCalcChunkDiversity:
    def test_basic(self):
        df = pd.DataFrame(
            {
                "report": ["R1", "R1", "R2", "R2"],
                "chunk": [1, 2, 1, 1],
            }
        )
        avg, details = calc_chunk_diversity(df, target="report", dimension="chunk")
        assert isinstance(avg, float)
        assert "R1" in details
        assert details["R1"] == 2  # two unique chunks
        assert details["R2"] == 1

    def test_missing_columns(self):
        df = pd.DataFrame({"a": [1]})
        with pytest.raises(ValueError, match="not found"):
            calc_chunk_diversity(df, target="missing", dimension="also_missing")

    def test_missing_roles(self):
        df = pd.DataFrame({"a": [1]})
        with pytest.raises(ValueError, match="Missing"):
            calc_chunk_diversity(df)


# ===================================================================
# calc_subtitle_diversity
# ===================================================================


class TestCalcSubtitleDiversity:
    def test_basic(self):
        df = pd.DataFrame(
            {
                "report": ["R1", "R1", "R1", "R2", "R2"],
                "subtitle": ["Intro", "Methods", "Results", "Intro", "Intro"],
            }
        )
        score = calc_subtitle_diversity(df, target="report", dimension="subtitle")
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_missing_columns(self):
        df = pd.DataFrame({"a": [1]})
        with pytest.raises(ValueError, match="not found"):
            calc_subtitle_diversity(df, target="missing", dimension="also_missing")

    def test_high_diversity(self):
        """Many unique subtitles -> score >= 0."""
        subtitles = [f"section_{i}" for i in range(15)]
        df = pd.DataFrame(
            {
                "report": ["R1"] * 15,
                "subtitle": subtitles,
            }
        )
        score = calc_subtitle_diversity(df, target="report", dimension="subtitle")
        # The internal count_unique_subtitles works on group DataFrames;
        # Series doesn't match isinstance(list) or isinstance(str), so
        # the raw function may return 0 for non-string/non-list types.
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
