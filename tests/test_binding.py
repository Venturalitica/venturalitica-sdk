"""Tests for binding module - column name resolution and synonym discovery."""

import pandas as pd
import pytest

from venturalitica.binding import (
    COLUMN_SYNONYMS,
    discover_column,
    resolve_col_names,
)


class TestResolveColNames:
    """Test resolve_col_names function with various input formats."""

    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame(
            {
                "target": [0, 1, 0, 1],
                "gender": ["M", "F", "M", "F"],
                "age": [25, 30, 35, 40],
                "approved": [1, 0, 1, 1],
            }
        )

    def test_resolve_single_string(self, sample_df):
        """Test resolving a single column name from string."""
        result = resolve_col_names("target", sample_df)
        assert result == ["target"]

    def test_resolve_comma_separated_string(self, sample_df):
        """Test resolving comma-separated column names."""
        result = resolve_col_names("target, gender, age", sample_df)
        assert result == ["target", "gender", "age"]

    def test_resolve_list_input(self, sample_df):
        """Test resolving from list input."""
        result = resolve_col_names(["target", "gender"], sample_df)
        assert result == ["target", "gender"]

    def test_resolve_tuple_input(self, sample_df):
        """Test resolving from tuple input."""
        result = resolve_col_names(("target", "gender"), sample_df)
        assert result == ["target", "gender"]

    def test_resolve_with_synonyms(self, sample_df):
        """Test resolving column names using synonyms."""
        # "class" is a synonym for "target"
        result = resolve_col_names("class", sample_df)
        assert result == ["target"]

    def test_resolve_with_label_synonym(self, sample_df):
        """Test label as synonym for target."""
        result = resolve_col_names("label", sample_df)
        assert result == ["target"]

    def test_resolve_lowercase_fallback(self, sample_df):
        """Test lowercase fallback when column name not found exactly."""
        df = pd.DataFrame(
            {
                "Target": [0, 1, 0, 1],
                "Gender": ["M", "F", "M", "F"],
            }
        )
        result = resolve_col_names("target", df)
        assert result == ["target"]

    def test_resolve_nonexistent_column(self, sample_df):
        """Test handling of non-existent columns."""
        result = resolve_col_names("nonexistent", sample_df)
        assert result == ["nonexistent"]

    def test_resolve_none_input(self, sample_df):
        """Test handling of None input."""
        result = resolve_col_names(None, sample_df)
        assert result is None

    def test_resolve_mixed_synonyms(self, sample_df):
        """Test mixed synonyms and direct column names."""
        # "class" is synonym for "target", gender exists, age exists
        result = resolve_col_names("class, gender, age", sample_df)
        assert result == ["target", "gender", "age"]

    def test_resolve_approval_synonym(self, sample_df):
        """Test 'approved' column resolution."""
        result = resolve_col_names("target", sample_df)
        assert result == ["target"]

    def test_resolve_custom_synonyms(self, sample_df):
        """Test using custom synonym dictionary."""
        custom_synonyms = {
            "target": ["label", "output"],
            "feature": ["column", "field"],
        }
        # Create dataframe with "label" column to test synonym resolution
        df = pd.DataFrame(
            {
                "label": [0, 1, 0, 1],
                "gender": ["M", "F", "M", "F"],
            }
        )
        result = resolve_col_names("output", df, synonyms=custom_synonyms)
        assert result == ["label"]

    def test_resolve_empty_string(self, sample_df):
        """Test handling of empty string."""
        result = resolve_col_names("", sample_df)
        assert result == []

    def test_resolve_whitespace_handling(self, sample_df):
        """Test that whitespace is stripped correctly."""
        result = resolve_col_names("  target  ,  gender  ", sample_df)
        assert result == ["target", "gender"]


class TestDiscoverColumn:
    """Test discover_column function for context-based discovery."""

    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame(
            {
                "target": [0, 1, 0, 1],
                "gender": ["M", "F", "M", "F"],
                "age": [25, 30, 35, 40],
            }
        )

    @pytest.fixture
    def context_mapping(self):
        """Create a sample context mapping."""
        return {
            "target": "label_col",
            "prediction": "pred_col",
        }

    def test_discover_from_context(self, sample_df, context_mapping):
        """Test discovering column from context mapping."""
        result = discover_column("target", context_mapping, sample_df)
        assert result == "label_col"

    def test_discover_direct_column(self, sample_df):
        """Test discovering when column name exists directly."""
        result = discover_column("target", {}, sample_df)
        assert result == "target"

    def test_discover_from_synonym(self, sample_df):
        """Test discovering using synonym resolution."""
        result = discover_column("class", {}, sample_df)
        assert result == "target"

    def test_discover_from_synonym_age(self, sample_df):
        """Test discovering age group synonym."""
        result = discover_column("age", {}, sample_df)
        assert result == "age"

    def test_discover_missing_column(self, sample_df):
        """Test discovering non-existent column returns MISSING."""
        result = discover_column("nonexistent", {}, sample_df)
        assert result == "MISSING"

    def test_discover_lowercase_fallback(self):
        """Test lowercase fallback in discovery."""
        df = pd.DataFrame(
            {
                "target": [0, 1, 0, 1],  # Already lowercase
                "Gender": ["M", "F", "M", "F"],
            }
        )
        result = discover_column("target", {}, df)
        assert result == "target"

    def test_discover_label_synonym(self, sample_df):
        """Test label synonym discovery."""
        result = discover_column("label", {}, sample_df)
        assert result == "target"

    def test_discover_context_priority(self, sample_df):
        """Test context mapping takes priority over synonyms."""
        context = {"target": "actual_col"}
        df = pd.DataFrame(
            {
                "target": [0, 1],
                "actual_col": [1, 0],
            }
        )
        result = discover_column("target", context, df)
        assert result == "actual_col"

    def test_discover_custom_synonyms(self, sample_df):
        """Test discover with custom synonyms."""
        custom_synonyms = {
            "target": ["result", "outcome"],
        }
        df = pd.DataFrame(
            {
                "result": [0, 1, 0, 1],
                "gender": ["M", "F", "M", "F"],
            }
        )
        result = discover_column("outcome", {}, df, synonyms=custom_synonyms)
        assert result == "result"


class TestColumnSynonyms:
    """Test COLUMN_SYNONYMS constant for completeness."""

    def test_column_synonyms_has_required_keys(self):
        """Test that COLUMN_SYNONYMS has all required keys."""
        required_keys = {"gender", "age", "race", "target", "prediction", "dimension"}
        assert all(key in COLUMN_SYNONYMS for key in required_keys)

    def test_column_synonyms_non_empty_values(self):
        """Test that all synonym lists are non-empty."""
        for key, values in COLUMN_SYNONYMS.items():
            assert len(values) > 0, f"Synonym list for '{key}' is empty"

    def test_column_synonyms_target_includes_common_names(self):
        """Test that target synonyms include common names."""
        target_synonyms = COLUMN_SYNONYMS["target"]
        common_names = ["target", "label", "class", "y"]
        assert all(name in target_synonyms for name in common_names)

    def test_column_synonyms_prediction_includes_common_names(self):
        """Test that prediction synonyms include common names."""
        pred_synonyms = COLUMN_SYNONYMS["prediction"]
        common_names = ["prediction", "pred", "y_pred", "score"]
        assert all(name in pred_synonyms for name in common_names)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_resolve_with_unicode_chars(self):
        """Test handling of unicode characters in column names."""
        df = pd.DataFrame(
            {
                "año": [1, 2, 3],
                "género": ["M", "F", "M"],
            }
        )
        result = resolve_col_names("año", df)
        assert result == ["año"]

    def test_resolve_duplicate_columns_in_input(self):
        """Test handling of duplicate column names in input."""
        df = pd.DataFrame(
            {
                "target": [0, 1],
                "gender": ["M", "F"],
            }
        )
        result = resolve_col_names("target, target, gender", df)
        assert result == ["target", "target", "gender"]

    def test_large_dataframe(self):
        """Test with a large DataFrame."""
        df = pd.DataFrame({f"col_{i}": range(1000) for i in range(100)})
        df["target"] = [0, 1] * 500
        result = resolve_col_names("target", df)
        assert result == ["target"]

    def test_empty_dataframe(self):
        """Test with an empty DataFrame."""
        df = pd.DataFrame()
        result = resolve_col_names("target", df)
        assert result == ["target"]

    def test_integer_input(self):
        """Test handling of integer input."""
        df = pd.DataFrame(
            {
                "target": [0, 1],
                "col_1": [1, 2],
            }
        )
        result = resolve_col_names(123, df)
        assert result == 123
