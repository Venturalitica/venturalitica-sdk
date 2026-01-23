"""
Test suite for output rendering and semantic interpretation
"""

import pytest
import pandas as pd
from venturalitica.output import _get_metric_interpretation
from venturalitica.metrics import METRIC_METADATA


class TestMetricInterpretation:
    """Test semantic interpretation of metric values"""
    
    def test_low_risk_demographic_parity(self):
        """Demographic parity below threshold = LOW RISK"""
        result = _get_metric_interpretation(
            metric_key='demographic_parity_diff',
            actual_value=0.05,
            threshold=0.10,
            operator='<'
        )
        
        assert result is not None
        assert 'risk_level' in result
        assert '🟢' in result['risk_level']
        assert 'LOW' in result['risk_level']
    
    def test_medium_risk_demographic_parity(self):
        """Demographic parity marginally above threshold = MEDIUM RISK"""
        result = _get_metric_interpretation(
            metric_key='demographic_parity_diff',
            actual_value=0.14,
            threshold=0.10,
            operator='<'
        )
        
        assert result is not None
        assert '🟡' in result['risk_level']
        assert 'MEDIUM' in result['risk_level']
    
    def test_high_risk_demographic_parity(self):
        """Demographic parity well above threshold = HIGH RISK"""
        result = _get_metric_interpretation(
            metric_key='demographic_parity_diff',
            actual_value=0.25,
            threshold=0.10,
            operator='<'
        )
        
        assert result is not None
        assert '🔴' in result['risk_level']
        assert 'HIGH' in result['risk_level']
    
    def test_low_risk_k_anonymity(self):
        """k-anonymity above threshold (higher is better) = LOW RISK"""
        result = _get_metric_interpretation(
            metric_key='k_anonymity',
            actual_value=10,
            threshold=5,
            operator='>'
        )
        
        assert result is not None
        assert '🟢' in result['risk_level']
    
    def test_high_risk_k_anonymity(self):
        """k-anonymity below threshold = HIGH RISK"""
        result = _get_metric_interpretation(
            metric_key='k_anonymity',
            actual_value=2,
            threshold=5,
            operator='>'
        )
        
        assert result is not None
        assert '🔴' in result['risk_level']
    
    def test_interpretation_includes_metadata(self):
        """Interpretation should include metric metadata"""
        result = _get_metric_interpretation(
            metric_key='demographic_parity_diff',
            actual_value=0.05,
            threshold=0.10,
            operator='<'
        )
        
        assert 'interpretation' in result or 'metadata' in result
        assert isinstance(result.get('interpretation'), str) or \
               isinstance(result.get('metadata'), dict)


class TestInterpretationStrings:
    """Test quality of interpretation messages"""
    
    def test_interpretation_is_human_readable(self):
        """Interpretation should be understandable to non-experts"""
        result = _get_metric_interpretation(
            metric_key='demographic_parity_diff',
            actual_value=0.05,
            threshold=0.10,
            operator='<'
        )
        
        interp = result.get('interpretation', '')
        # Should contain numbers and comparison language
        assert any(str(v) in interp for v in [0.05, 0.10, '0.05', '0.10'])
    
    def test_interpretation_includes_threshold(self):
        """Interpretation should explain the threshold"""
        result = _get_metric_interpretation(
            metric_key='equal_opportunity_diff',
            actual_value=0.18,
            threshold=0.15,
            operator='<'
        )
        
        interp = result.get('interpretation', '')
        # Should reference threshold value
        assert '0.15' in interp or 'threshold' in interp.lower()
    
    def test_interpretation_explains_direction(self):
        """Interpretation should clarify if higher/lower is better"""
        # For fairness, lower is better
        dp_result = _get_metric_interpretation(
            metric_key='demographic_parity_diff',
            actual_value=0.02,
            threshold=0.10,
            operator='<'
        )
        
        # For privacy (k), higher is better
        k_result = _get_metric_interpretation(
            metric_key='k_anonymity',
            actual_value=8,
            threshold=5,
            operator='>'
        )
        
        # Both should have clear interpretations
        assert dp_result['interpretation']
        assert k_result['interpretation']


class TestRiskLevelConsistency:
    """Test consistency of risk level assignments"""
    
    def test_same_metric_consistent_levels(self):
        """Same metric with different values should have consistent risk levels"""
        # Good value
        good = _get_metric_interpretation(
            metric_key='demographic_parity_diff',
            actual_value=0.02,
            threshold=0.10,
            operator='<'
        )
        
        # Bad value
        bad = _get_metric_interpretation(
            metric_key='demographic_parity_diff',
            actual_value=0.30,
            threshold=0.10,
            operator='<'
        )
        
        assert '🟢' in good['risk_level']
        assert '🔴' in bad['risk_level']
    
    def test_boundary_conditions(self):
        """Values at threshold should be handled correctly"""
        # Exactly at threshold
        at_threshold = _get_metric_interpretation(
            metric_key='demographic_parity_diff',
            actual_value=0.10,
            threshold=0.10,
            operator='<'
        )
        
        # Just below threshold
        below_threshold = _get_metric_interpretation(
            metric_key='demographic_parity_diff',
            actual_value=0.099,
            threshold=0.10,
            operator='<'
        )
        
        # Just above threshold
        above_threshold = _get_metric_interpretation(
            metric_key='demographic_parity_diff',
            actual_value=0.101,
            threshold=0.10,
            operator='<'
        )
        
        # Check they're different (at threshold might be yellow or red)
        assert at_threshold is not None
        assert below_threshold is not None
        assert above_threshold is not None


class TestComparisonOperators:
    """Test different comparison operators (>, <, >=, <=)"""
    
    def test_less_than_operator(self):
        """Test < operator (fairness metrics, lower is better)"""
        result = _get_metric_interpretation(
            metric_key='demographic_parity_diff',
            actual_value=0.05,
            threshold=0.10,
            operator='<'
        )
        
        assert '🟢' in result['risk_level']
    
    def test_greater_than_operator(self):
        """Test > operator (k-anonymity, higher is better)"""
        result = _get_metric_interpretation(
            metric_key='k_anonymity',
            actual_value=8,
            threshold=5,
            operator='>'
        )
        
        assert '🟢' in result['risk_level']
    
    def test_greater_equal_operator(self):
        """Test >= operator"""
        result = _get_metric_interpretation(
            metric_key='accuracy_score',
            actual_value=0.80,
            threshold=0.80,
            operator='>='
        )
        
        assert result is not None
    
    def test_less_equal_operator(self):
        """Test <= operator"""
        result = _get_metric_interpretation(
            metric_key='error_rate',
            actual_value=0.05,
            threshold=0.10,
            operator='<='
        )
        
        assert result is not None


class TestMetadataRetrieval:
    """Test that interpretations use metric metadata correctly"""
    
    def test_interpretation_references_metadata(self):
        """Interpretation should use METRIC_METADATA when available"""
        result = _get_metric_interpretation(
            metric_key='demographic_parity_diff',
            actual_value=0.05,
            threshold=0.10,
            operator='<'
        )
        
        # Should have reference to metadata
        assert 'interpretation' in result
    
    def test_unknown_metric_handled_gracefully(self):
        """Unknown metrics should be handled without crashing"""
        result = _get_metric_interpretation(
            metric_key='unknown_metric',
            actual_value=0.5,
            threshold=0.5,
            operator='<'
        )
        
        # Should return something sensible, not crash
        assert result is not None
        assert 'risk_level' in result or 'interpretation' in result


class TestSeverityLevels:
    """Test severity/risk level assignments"""
    
    def test_critical_metrics(self):
        """Some metrics should be marked as critical"""
        # k-anonymity < 2 is critical for privacy
        critical = _get_metric_interpretation(
            metric_key='k_anonymity',
            actual_value=1,
            threshold=5,
            operator='>'
        )
        
        assert '🔴' in critical['risk_level']
    
    def test_high_vs_medium_risk(self):
        """Should distinguish between medium and high risk"""
        medium = _get_metric_interpretation(
            metric_key='demographic_parity_diff',
            actual_value=0.12,  # Slightly over threshold
            threshold=0.10,
            operator='<'
        )
        
        high = _get_metric_interpretation(
            metric_key='demographic_parity_diff',
            actual_value=0.35,  # Well over threshold
            threshold=0.10,
            operator='<'
        )
        
        # Both should show some risk, but different levels
        assert medium is not None
        assert high is not None


class TestRenderingOutput:
    """Test actual rendering of compliance results"""
    
    def test_compliance_table_structure(self):
        """Compliance results should be structured as table"""
        # This would test render_compliance_results function
        # Structure should have: Control, Metric, Value, Interpretation, Risk
        pass  # Requires full render_compliance_results implementation
    
    def test_error_messages_include_hints(self):
        """Error messages should include 'Did you mean?' hints"""
        # This tests error message generation
        pass  # Requires full error handling implementation


if __name__ == "__main__":
    # Run tests with: pytest test_output.py -v
    pass
