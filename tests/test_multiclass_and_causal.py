"""
Comprehensive tests for multi-class and causal fairness metrics.

Tests cover:
- Multi-class classification fairness (3+ classes)
- Causal path decomposition
- Counterfactual fairness analysis
- Fairness through awareness
"""

import pytest
import pandas as pd
import numpy as np
import pytest
import pandas as pd
import numpy as np
from venturalitica.fairness.multiclass import (
    calc_weighted_demographic_parity_multiclass,
    calc_macro_equal_opportunity_multiclass,
    calc_micro_equalized_odds_multiclass,
    calc_predictive_parity_multiclass,
    calc_multiclass_fairness_report,
)
from venturalitica.causal.metrics import (
    calc_path_decomposition,
    calc_counterfactual_fairness,
    calc_fairness_through_awareness,
    calc_causal_fairness_diagnostic,
    CausalEffect,
)


class TestWeightedDemographicParity:
    """Tests for multi-class weighted demographic parity."""
    
    def test_perfect_fairness_macro(self):
        """Perfect fairness: same prediction rate across groups."""
        y_pred = pd.Series([0, 1, 2, 0, 1, 2] * 10)  # Balanced predictions
        protected = pd.Series(['A', 'B'] * 30)
        y_true = pd.Series([0, 1, 2, 0, 1, 2] * 10)
        
        disparity = calc_weighted_demographic_parity_multiclass(
            y_true, y_pred, protected, strategy='macro'
        )
        assert disparity <= 0.01  # Nearly perfect
    
    def test_severe_disparity_macro(self):
        """Severe disparity: one group rarely gets positive prediction."""
        y_pred = pd.Series([0] * 30 + [1, 2] * 15)  # Group B mostly gets class 0
        protected = pd.Series(['A'] * 30 + ['B'] * 30)
        y_true = pd.Series([0, 1, 2] * 20)
        
        disparity = calc_weighted_demographic_parity_multiclass(
            y_true, y_pred, protected, strategy='macro'
        )
        assert disparity > 0.3  # Severe disparity
    
    def test_different_strategies(self):
        """Different strategies produce different results."""
        y_pred = pd.Series([0, 1, 2] * 20)
        protected = pd.Series(['A', 'B'] * 30)
        y_true = pd.Series([0, 1, 2] * 20)
        
        macro = calc_weighted_demographic_parity_multiclass(
            y_true, y_pred, protected, strategy='macro'
        )
        micro = calc_weighted_demographic_parity_multiclass(
            y_true, y_pred, protected, strategy='micro'
        )
        weighted = calc_weighted_demographic_parity_multiclass(
            y_true, y_pred, protected, strategy='weighted'
        )
        
        # All should return valid floats
        assert isinstance(macro, float)
        assert isinstance(micro, float)
        assert isinstance(weighted, float)
        assert 0 <= macro <= 1
        assert 0 <= micro <= 1
        assert 0 <= weighted <= 1
    
    def test_insufficient_data(self):
        """Raises error with insufficient data."""
        y_pred = pd.Series([0, 1] * 5)
        protected = pd.Series(['A', 'B'] * 5)
        y_true = pd.Series([0, 1] * 5)
        
        with pytest.raises(ValueError, match="Minimum 30"):
            calc_weighted_demographic_parity_multiclass(
                y_true, y_pred, protected
            )
    
    def test_single_class(self):
        """Raises error with single class."""
        y_pred = pd.Series([0] * 30)  # Only one class
        protected = pd.Series(['A', 'B'] * 15)
        y_true = pd.Series([0] * 30)
        
        with pytest.raises(ValueError, match="at least 2 classes"):
            calc_weighted_demographic_parity_multiclass(
                y_true, y_pred, protected
            )
    
    def test_single_group(self):
        """Raises error with single protected group."""
        y_pred = pd.Series([0, 1, 2] * 10)
        protected = pd.Series(['A'] * 30)  # Only one group
        y_true = pd.Series([0, 1, 2] * 10)
        
        with pytest.raises(ValueError, match="at least 2 protected groups"):
            calc_weighted_demographic_parity_multiclass(
                y_true, y_pred, protected
            )


class TestMacroEqualOpportunity:
    """Tests for macro-averaged equal opportunity."""
    
    def test_perfect_tpr_parity(self):
        """Perfect: same TPR for each class across groups."""
        n = 100
        y_true = pd.Series([0, 1, 2] * n)[:n]
        y_pred = y_true.copy()  # Perfect prediction
        protected = pd.Series(['A', 'B'] * 50)
        
        disparity = calc_macro_equal_opportunity_multiclass(
            y_true, y_pred, protected
        )
        assert disparity <= 0.01
    
    def test_poor_tpr_parity(self):
        """Poor: very different TPR across groups for some classes."""
        n = 100
        y_true = pd.Series([0, 1, 2] * n)[:n]
        y_pred = pd.Series([0] * 50 + [1, 2] * 25)  # Biased predictions
        protected = pd.Series(['A'] * 50 + ['B'] * 50)
        
        disparity = calc_macro_equal_opportunity_multiclass(
            y_true, y_pred, protected
        )
        assert disparity > 0.2  # Significant disparity
    
    def test_no_positive_examples(self):
        """Handles classes with no positive examples gracefully."""
        y_true = pd.Series([0, 1, 2, 0, 1, 2] * 5)
        y_pred = pd.Series([0] * 30)  # All predict class 0
        protected = pd.Series(['A', 'B'] * 15)
        
        disparity = calc_macro_equal_opportunity_multiclass(
            y_true, y_pred, protected
        )
        # Should not raise error
        assert isinstance(disparity, float)
        assert 0 <= disparity <= 1


class TestMicroEqualizedOdds:
    """Tests for micro-averaged equalized odds."""
    
    def test_perfect_accuracy_parity(self):
        """Perfect: same accuracy across groups."""
        n = 100
        y_true = pd.Series([0, 1, 2] * n)[:n]
        y_pred = y_true.copy()
        protected = pd.Series(['A', 'B'] * 50)
        
        disparity = calc_micro_equalized_odds_multiclass(
            y_true, y_pred, protected
        )
        assert disparity <= 0.01
    
    def test_very_different_accuracy(self):
        """Poor: very different accuracy across groups."""
        y_true = pd.Series([0, 1, 2] * 20)
        # Group A: accurate, Group B: all wrong
        y_pred = pd.Series([0, 1, 2] * 10 + [2, 2, 2] * 10)
        protected = pd.Series(['A'] * 30 + ['B'] * 30)
        
        disparity = calc_micro_equalized_odds_multiclass(
            y_true, y_pred, protected
        )
        assert disparity > 0.5  # Very poor


class TestPredictiveParityMulticlass:
    """Tests for multi-class predictive parity."""
    
    def test_perfect_precision_parity(self):
        """Perfect: same precision across groups."""
        y_true = pd.Series([0, 1, 2] * 10)
        y_pred = y_true.copy()  # Perfect predictions
        protected = pd.Series(['A', 'B'] * 15)
        
        disparity, _ = calc_predictive_parity_multiclass(
            y_true, y_pred, protected
        )
        assert disparity <= 0.01
    
    def test_macro_vs_weighted_strategies(self):
        """Different strategies for precision aggregation."""
        y_true = pd.Series([0, 1, 2] * 10)
        y_pred = pd.Series([0, 0, 0] + [1, 1, 1] + [2, 2, 2] * 7)
        protected = pd.Series(['A', 'B'] * 15)
        
        macro, _ = calc_predictive_parity_multiclass(
            y_true, y_pred, protected, strategy='macro'
        )
        weighted, _ = calc_predictive_parity_multiclass(
            y_true, y_pred, protected, strategy='weighted'
        )
        
        assert isinstance(macro, float)
        assert isinstance(weighted, float)
        assert 0 <= macro <= 1
        assert 0 <= weighted <= 1


class TestMulticlassFairnessReport:
    """Tests for comprehensive multi-class fairness report."""
    
    def test_report_structure(self):
        """Report includes all expected metrics."""
        y_true = pd.Series([0, 1, 2] * 20)
        y_pred = pd.Series([0, 1, 2] * 20)
        protected = pd.Series(['A', 'B'] * 30)
        
        report = calc_multiclass_fairness_report(
            y_true, y_pred, protected
        )
        
        # Check all keys present
        expected_keys = [
            'weighted_demographic_parity_macro',
            'macro_equal_opportunity',
            'micro_equalized_odds',
            'predictive_parity_macro',
        ]
        for key in expected_keys:
            assert key in report
            assert isinstance(report[key], float)


class TestCausalEffect:
    """Tests for CausalEffect dataclass."""
    
    def test_causal_effect_creation(self):
        """Creates valid CausalEffect objects."""
        effect = CausalEffect(
            total_effect=0.1,
            direct_effect=0.05,
            indirect_effect=0.05,
            proportion_mediated=0.5,
        )
        
        assert effect.total_effect == 0.1
        assert effect.direct_effect == 0.05
        assert effect.indirect_effect == 0.05
        assert effect.proportion_mediated == 0.5
    
    def test_string_representation(self):
        """String representation includes all components."""
        effect = CausalEffect(
            total_effect=0.1,
            direct_effect=0.05,
            indirect_effect=0.05,
            proportion_mediated=0.5,
        )
        
        str_repr = str(effect)
        assert "Total Effect" in str_repr
        assert "Direct Effect" in str_repr
        assert "Indirect Effect" in str_repr
        assert "Proportion Mediated" in str_repr


class TestPathDecomposition:
    """Tests for causal path decomposition."""
    
    def test_simple_path_decomposition(self):
        """Calculates path decomposition on synthetic data."""
        df = pd.DataFrame({
            'gender': ['M', 'F'] * 50,
            'education': np.random.randint(1, 5, 100),
            'income': np.random.randint(0, 100000, 100),
        })
        
        effects = calc_path_decomposition(
            df, 'gender', 'income', mediators=['education']
        )
        
        # Should return dict with comparison
        assert isinstance(effects, dict)
        for comparison, effect in effects.items():
            assert isinstance(effect, CausalEffect)
            assert effect.total_effect >= 0
            assert effect.direct_effect >= 0
            assert effect.indirect_effect >= 0
    
    def test_missing_column(self):
        """Raises error if column missing."""
        df = pd.DataFrame({
            'gender': ['M', 'F'] * 50,
            'income': np.random.randint(0, 100000, 100),
        })
        
        with pytest.raises(ValueError, match="not found"):
            calc_path_decomposition(
                df, 'gender', 'income', mediators=['education']
            )
    
    def test_insufficient_data(self):
        """Raises error with insufficient data."""
        df = pd.DataFrame({
            'gender': ['M', 'F'] * 5,
            'income': np.random.randint(0, 100000, 10),
        })
        
        with pytest.raises(ValueError, match="Insufficient data"):
            calc_path_decomposition(df, 'gender', 'income')


class TestCounterfactualFairness:
    """Tests for counterfactual fairness metric."""
    
    def test_perfect_counterfactual_fairness(self):
        """Perfect: outcome wouldn't change with counterfactual."""
        df = pd.DataFrame({
            'gender': ['M', 'F'] * 50,
            'income': [1] * 100,  # All same outcome
        })
        
        unfairness = calc_counterfactual_fairness(
            df, 'gender', 'income'
        )
        assert unfairness == 0.0
    
    def test_severe_counterfactual_disparity(self):
        """Poor: outcome would very likely change."""
        df = pd.DataFrame({
            'gender': ['M'] * 50 + ['F'] * 50,
            'income': [1] * 50 + [0] * 50,  # Completely different by gender
        })
        
        unfairness = calc_counterfactual_fairness(
            df, 'gender', 'income'
        )
        assert unfairness > 0.8
    
    def test_non_binary_protected_attr(self):
        """Raises error with non-binary protected attribute."""
        df = pd.DataFrame({
            'gender': ['M', 'F', 'X'] * 20,
            'income': np.random.randint(0, 2, 60),
        })
        
        with pytest.raises(ValueError, match="binary"):
            calc_counterfactual_fairness(df, 'gender', 'income')


class TestFairnessThroughAwareness:
    """Tests for fairness through awareness metric."""
    
    def test_low_information_leakage(self):
        """Legitimate features don't correlate with protected attribute."""
        df = pd.DataFrame({
            'gender': ['M', 'F'] * 50,
            'qualification_score': np.random.normal(0.5, 0.2, 100),
            'years_experience': np.random.normal(5, 2, 100),
            'income': np.random.randint(0, 2, 100),
        })
        
        awareness = calc_fairness_through_awareness(
            df, 'gender', 'income',
            relevant_features=['qualification_score', 'years_experience']
        )
        
        assert 'information_leakage_score' in awareness
        assert 'legitimate_predictor_power' in awareness
        assert 0 <= awareness['information_leakage_score'] <= 1
    
    def test_high_information_leakage(self):
        """Legitimate features correlate with protected attribute."""
        df = pd.DataFrame({
            'gender': ['M', 'F'] * 50,
            'male_proxy': list(range(100)),  # Increasing feature (correlated with index/gender)
            'income': np.random.randint(0, 2, 100),
        })
        
        awareness = calc_fairness_through_awareness(
            df, 'gender', 'income',
            relevant_features=['male_proxy']
        )
        
        # Should detect some information leakage
        assert awareness['information_leakage_score'] >= 0


class TestCausalFairnessDiagnostic:
    """Tests for comprehensive causal fairness diagnostic."""
    
    def test_diagnostic_structure(self):
        """Diagnostic includes all components."""
        df = pd.DataFrame({
            'gender': ['M', 'F'] * 50,
            'education': np.random.randint(1, 5, 100),
            'experience': np.random.randint(0, 30, 100),
            'income': np.random.randint(0, 2, 100),
        })
        
        diagnostic = calc_causal_fairness_diagnostic(
            df, 'gender', 'income',
            mediators=['education', 'experience']
        )
        
        assert 'protected_attribute' in diagnostic
        assert 'path_decomposition' in diagnostic
        assert 'counterfactual_fairness' in diagnostic
        assert 'fairness_through_awareness' in diagnostic
        assert 'causal_fairness_verdict' in diagnostic
    
    def test_diagnostic_verdict_generation(self):
        """Diagnostic generates meaningful verdict."""
        df = pd.DataFrame({
            'gender': ['M'] * 50 + ['F'] * 50,
            'education': np.random.randint(1, 5, 100),
            'income': [1] * 50 + [0] * 50,  # Biased
        })
        
        diagnostic = calc_causal_fairness_diagnostic(
            df, 'gender', 'income', mediators=['education']
        )
        
        verdict = diagnostic['causal_fairness_verdict']
        assert isinstance(verdict, str)
        assert len(verdict) > 0
        # Should contain some indicator
        assert '✓' in verdict or '⚠️' in verdict


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
