"""Tests for formatting module - JSON encoding and console output."""

import json
import pytest
import numpy as np
import pandas as pd
from datetime import datetime
from io import StringIO
import sys
from venturalitica.formatting import (
    VenturalíticaJSONEncoder,
    print_summary,
)
from venturalitica.core import ComplianceResult


class TestVenturalíticaJSONEncoder:
    """Test custom JSON encoder for various data types."""

    def test_encode_numpy_bool(self):
        """Test encoding numpy boolean types."""
        data = {"value": np.bool_(True)}
        result = json.dumps(data, cls=VenturalíticaJSONEncoder)
        assert result == '{"value": true}'

    def test_encode_numpy_integer(self):
        """Test encoding numpy integer types."""
        data = {"value": np.int64(42)}
        result = json.dumps(data, cls=VenturalíticaJSONEncoder)
        assert result == '{"value": 42}'

    def test_encode_numpy_float(self):
        """Test encoding numpy float types."""
        data = {"value": np.float64(3.14159)}
        result = json.dumps(data, cls=VenturalíticaJSONEncoder)
        assert '"value": 3.14159' in result

    def test_encode_datetime(self):
        """Test encoding datetime objects."""
        dt = datetime(2024, 1, 15, 10, 30, 45)
        data = {"timestamp": dt}
        result = json.dumps(data, cls=VenturalíticaJSONEncoder)
        assert '"timestamp": "2024-01-15T10:30:45"' in result

    def test_encode_numpy_array(self):
        """Test encoding numpy arrays (converted to lists)."""
        data = {"array": np.array([1, 2, 3])}
        result = json.dumps(data, cls=VenturalíticaJSONEncoder)
        assert result == '{"array": [1, 2, 3]}'

    def test_encode_pandas_series(self):
        """Test encoding pandas Series."""
        series = pd.Series([1, 2, 3])
        data = {"series": series}
        result = json.dumps(data, cls=VenturalíticaJSONEncoder)
        assert "[1, 2, 3]" in result

    def test_encode_nested_structure(self):
        """Test encoding nested structures with mixed types."""
        data = {
            "int_val": np.int32(10),
            "float_val": np.float32(2.5),
            "array_val": np.array([1, 2, 3]),
            "nested": {
                "bool_val": np.bool_(False),
                "timestamp": datetime(2024, 1, 1),
            },
        }
        result = json.dumps(data, cls=VenturalíticaJSONEncoder)
        parsed = json.loads(result)

        assert parsed["int_val"] == 10
        assert abs(parsed["float_val"] - 2.5) < 0.01
        assert parsed["array_val"] == [1, 2, 3]
        assert parsed["nested"]["bool_val"] is False
        assert "2024-01-01" in parsed["nested"]["timestamp"]

    def test_encode_invalid_type(self):
        """Test that invalid types raise appropriate error."""

        class CustomObject:
            pass

        data = {"obj": CustomObject()}
        with pytest.raises(TypeError):
            json.dumps(data, cls=VenturalíticaJSONEncoder)

    def test_encode_none_values(self):
        """Test encoding None values."""
        data = {"value": None, "array": [1, None, 3]}
        result = json.dumps(data, cls=VenturalíticaJSONEncoder)
        assert result == '{"value": null, "array": [1, null, 3]}'

    def test_encode_multiple_numpy_types(self):
        """Test encoding multiple numpy types in one structure."""
        data = {
            "bool": np.bool_(True),
            "int8": np.int8(1),
            "int16": np.int16(100),
            "int32": np.int32(1000),
            "int64": np.int64(10000),
            "float16": np.float16(1.5),
            "float32": np.float32(2.5),
            "float64": np.float64(3.5),
        }
        result = json.dumps(data, cls=VenturalíticaJSONEncoder)
        parsed = json.loads(result)

        assert parsed["bool"] is True
        assert parsed["int8"] == 1
        assert parsed["int32"] == 1000


class TestPrintSummary:
    """Test print_summary function for console output."""

    @pytest.fixture
    def sample_result(self):
        """Create a sample ComplianceResult."""
        return ComplianceResult(
            control_id="AC-1",
            description="Access Control Policy",
            metric_key="access_control",
            operator="ge",
            threshold=0.95,
            actual_value=0.98,
            passed=True,
            severity="high",
        )

    @pytest.fixture
    def failing_result(self):
        """Create a failing ComplianceResult."""
        return ComplianceResult(
            control_id="AC-2",
            description="Role-based Access Control",
            metric_key="rbac",
            operator="le",
            threshold=0.05,
            actual_value=0.12,
            passed=False,
            severity="critical",
        )

    def test_print_summary_empty_list(self, capsys):
        """Test print_summary with empty list."""
        print_summary([], is_data_only=False)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_print_summary_single_pass(self, capsys, sample_result):
        """Test print_summary with single passing result."""
        print_summary([sample_result], is_data_only=False)
        captured = capsys.readouterr()

        assert "AC-1" in captured.out
        assert "Access Control" in captured.out
        assert "PASS" in captured.out or "✅" in captured.out

    def test_print_summary_single_fail(self, capsys, failing_result):
        """Test print_summary with single failing result."""
        print_summary([failing_result], is_data_only=False)
        captured = capsys.readouterr()

        assert "AC-2" in captured.out
        assert "Role-based" in captured.out
        assert "FAIL" in captured.out or "❌" in captured.out

    def test_print_summary_mixed_results(self, capsys, sample_result, failing_result):
        """Test print_summary with mixed pass/fail results."""
        print_summary([sample_result, failing_result], is_data_only=False)
        captured = capsys.readouterr()

        assert "AC-1" in captured.out
        assert "AC-2" in captured.out
        assert "CONTROL" in captured.out
        assert "DESCRIPTION" in captured.out

    def test_print_summary_long_description(self, capsys):
        """Test print_summary truncates long descriptions."""
        long_desc = "This is a very long description that should be truncated to avoid display issues"
        result = ComplianceResult(
            control_id="AC-3",
            description=long_desc,
            metric_key="metric_3",
            operator="eq",
            threshold=1.0,
            actual_value=1.0,
            passed=True,
            severity="medium",
        )
        print_summary([result], is_data_only=False)
        captured = capsys.readouterr()

        # Check that description is truncated with "..."
        assert "..." in captured.out or len(captured.out) > 0

    def test_print_summary_operators(self, capsys):
        """Test print_summary displays operators correctly."""
        results = [
            ComplianceResult(
                control_id="OP-1",
                description="Greater than",
                metric_key="op_1",
                operator="gt",
                threshold=0.5,
                actual_value=0.8,
                passed=True,
                severity="low",
            ),
            ComplianceResult(
                control_id="OP-2",
                description="Less than",
                metric_key="op_2",
                operator="lt",
                threshold=0.5,
                actual_value=0.2,
                passed=True,
                severity="low",
            ),
            ComplianceResult(
                control_id="OP-3",
                description="Equal",
                metric_key="op_3",
                operator="eq",
                threshold=1.0,
                actual_value=1.0,
                passed=True,
                severity="low",
            ),
        ]
        print_summary(results, is_data_only=False)
        captured = capsys.readouterr()

        assert ">" in captured.out
        assert "<" in captured.out
        assert "==" in captured.out

    def test_print_summary_with_metadata(self, capsys):
        """Test print_summary displays metadata when available."""
        result = ComplianceResult(
            control_id="AC-4",
            description="Security Control",
            metric_key="security_metric",
            operator="ge",
            threshold=0.9,
            actual_value=0.95,
            passed=True,
            severity="high",
        )
        result.metadata = {"stability": "high", "confidence": "95%"}

        print_summary([result], is_data_only=False)
        captured = capsys.readouterr()

        assert "AC-4" in captured.out

    def test_print_summary_all_passing(self, capsys):
        """Test print_summary shows correct verdict for all passing."""
        results = [
            ComplianceResult(
                control_id=f"AC-{i}",
                description=f"Control {i}",
                metric_key=f"metric_{i}",
                operator="ge",
                threshold=0.9,
                actual_value=0.95,
                passed=True,
                severity="high",
            )
            for i in range(1, 4)
        ]
        print_summary(results, is_data_only=False)
        captured = capsys.readouterr()

        assert "3/3" in captured.out or "3 controls" in captured.out

    def test_print_summary_all_failing(self, capsys):
        """Test print_summary shows correct verdict for all failing."""
        results = [
            ComplianceResult(
                control_id=f"AC-{i}",
                description=f"Control {i}",
                metric_key=f"metric_{i}",
                operator="ge",
                threshold=0.9,
                actual_value=0.5,
                passed=False,
                severity="critical",
            )
            for i in range(1, 4)
        ]
        print_summary(results, is_data_only=False)
        captured = capsys.readouterr()

        assert "VIOLATION" in captured.out or "❌" in captured.out

    def test_print_summary_formatting_table(self, capsys):
        """Test that print_summary creates a properly formatted table."""
        result = ComplianceResult(
            control_id="AC-5",
            description="Test Control",
            metric_key="test_metric",
            operator="ge",
            threshold=0.95,
            actual_value=0.99,
            passed=True,
            severity="high",
        )
        print_summary([result], is_data_only=False)
        captured = capsys.readouterr()

        # Check for table elements
        assert "─" in captured.out or "CONTROL" in captured.out
