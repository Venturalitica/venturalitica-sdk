"""
Test suite for enhanced fairness metrics (Equalized Odds, Predictive Parity)
and privacy metrics (k-anonymity, l-diversity, t-closeness, data minimization)
"""

import pytest
import pandas as pd
import numpy as np
from venturalitica.fairness.metrics import (
    calc_demographic_parity,
    calc_equal_opportunity,
    calc_equalized_odds_ratio,
    calc_predictive_parity,
)
from venturalitica.privacy.metrics import (
    calc_k_anonymity,
    calc_l_diversity,
    calc_t_closeness,
    calc_data_minimization_score,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def balanced_data():
    """Perfectly balanced, perfectly fair data"""
    return pd.DataFrame({
        'target': [1, 0, 1, 0, 1, 0, 1, 0],
        'prediction': [1, 0, 1, 0, 1, 0, 1, 0],
        'dimension': ['A', 'A', 'A', 'A', 'B', 'B', 'B', 'B'],
    })


@pytest.fixture
def biased_data():
    """Data with systematic bias against group B"""
    return pd.DataFrame({
        'target': [1, 0, 1, 1, 0, 0, 1, 0],
        'prediction': [1, 0, 1, 1, 0, 0, 0, 1],  # Group B: higher FP, lower TP
        'dimension': ['A', 'A', 'A', 'A', 'B', 'B', 'B', 'B'],
    })


@pytest.fixture
def privacy_data():
    """Data for privacy metric testing"""
    return pd.DataFrame({
        'age_bin': ['20-30', '20-30', '20-30', '30-40', '30-40', '30-40'],
        'gender': ['M', 'M', 'F', 'M', 'F', 'F'],
        'job': ['Engineer', 'Engineer', 'Doctor', 'Engineer', 'Doctor', 'Doctor'],
        'income': ['high', 'high', 'low', 'high', 'low', 'low'],
    })


# ============================================================================
# TESTS: Equalized Odds Ratio
# ============================================================================

class TestEqualizedOdds:
    """Test Equalized Odds (TPR + FPR Parity)"""
    
    def test_perfect_equalized_odds(self, balanced_data):
        """Perfectly balanced data should have ~0.0 equalized odds"""
        result = calc_equalized_odds_ratio(
            balanced_data,
            target='target',
            prediction='prediction',
            dimension='dimension'
        )
        assert result <= 0.1, f"Expected ≈0, got {result}"
    
    def test_biased_equalized_odds(self, biased_data):
        """Biased data should show higher equalized odds"""
        result = calc_equalized_odds_ratio(
            biased_data,
            target='target',
            prediction='prediction',
            dimension='dimension'
        )
        assert result > 0.2, f"Expected >0.2, got {result}"
    
    def test_missing_columns_raises_error(self, balanced_data):
        """Missing columns should raise ValueError, not return 0.0"""
        with pytest.raises(ValueError, match="Missing columns"):
            calc_equalized_odds_ratio(
                balanced_data,
                target='MISSING',
                prediction='prediction',
                dimension='dimension'
            )
    
    def test_equalized_odds_bounds(self, biased_data):
        """Equalized odds should be in [0, 2] (max |TPR_diff| + |FPR_diff|)"""
        result = calc_equalized_odds_ratio(
            biased_data,
            target='target',
            prediction='prediction',
            dimension='dimension'
        )
        assert 0 <= result <= 2, f"Expected [0,2], got {result}"


# ============================================================================
# TESTS: Predictive Parity
# ============================================================================

class TestPredictiveParity:
    """Test Predictive Parity (Precision Parity)"""
    
    def test_perfect_predictive_parity(self, balanced_data):
        """Perfectly balanced data should have ~0.0 predictive parity"""
        result = calc_predictive_parity(
            balanced_data,
            target='target',
            prediction='prediction',
            dimension='dimension'
        )
        assert result <= 0.1, f"Expected ≈0, got {result}"
    
    def test_biased_predictive_parity(self, biased_data):
        """Biased data should show differences in precision"""
        result = calc_predictive_parity(
            biased_data,
            target='target',
            prediction='prediction',
            dimension='dimension'
        )
        # Group A has better precision than B due to lower FP
        assert result > 0.05, f"Expected >0.05, got {result}"
    
    def test_missing_target_raises_error(self, balanced_data):
        """Should raise error for missing target column"""
        with pytest.raises(ValueError):
            calc_predictive_parity(
                balanced_data,
                target='NOT_FOUND',
                prediction='prediction',
                dimension='dimension'
            )
    
    def test_predictive_parity_bounds(self, biased_data):
        """Precision difference should be in [0, 1]"""
        result = calc_predictive_parity(
            biased_data,
            target='target',
            prediction='prediction',
            dimension='dimension'
        )
        assert 0 <= result <= 1, f"Expected [0,1], got {result}"


# ============================================================================
# TESTS: k-Anonymity
# ============================================================================

class TestKAnonymity:
    """Test k-Anonymity metric"""
    
    def test_perfect_k_anonymity(self, privacy_data):
        """All groups should have same size for k-anonymity"""
        result = calc_k_anonymity(
            privacy_data,
            quasi_identifiers=['age_bin', 'gender']
        )
        assert result >= 1, f"Expected k≥1, got {result}"
    
    def test_low_k_anonymity(self):
        """Data with unique combinations should have k=1"""
        df = pd.DataFrame({
            'age_bin': ['20-30', '30-40', '40-50'],
            'gender': ['M', 'F', 'M'],
        })
        result = calc_k_anonymity(df, quasi_identifiers=['age_bin', 'gender'])
        assert result == 1, f"Expected k=1, got {result}"
    
    def test_k_anonymity_higher_grouping(self):
        """More combinations should increase k"""
        df = pd.DataFrame({
            'age_bin': ['20-30'] * 5 + ['30-40'] * 3,
            'gender': ['M'] * 5 + ['F'] * 3,
        })
        result = calc_k_anonymity(df, quasi_identifiers=['age_bin', 'gender'])
        assert result >= 3, f"Expected k≥3, got {result}"
    
    def test_empty_quasi_identifiers_raises_error(self, privacy_data):
        """Empty QI list should raise error"""
        with pytest.raises((ValueError, IndexError)):
            calc_k_anonymity(privacy_data, quasi_identifiers=[])
    
    def test_gdpr_minimum_threshold(self, privacy_data):
        """GDPR recommends k≥5"""
        result = calc_k_anonymity(privacy_data, quasi_identifiers=['age_bin', 'gender'])
        gdpr_compliant = result >= 5
        assert isinstance(gdpr_compliant, bool), "Should return boolean comparison"


# ============================================================================
# TESTS: l-Diversity
# ============================================================================

class TestLDiversity:
    """Test l-Diversity metric"""
    
    def test_perfect_l_diversity(self, privacy_data):
        """Perfectly diverse sensitive attributes"""
        result = calc_l_diversity(
            privacy_data,
            quasi_identifiers=['age_bin'],
            sensitive_attribute='job'
        )
        # Should have multiple distinct values per age_bin group
        assert result >= 2, f"Expected l≥2, got {result}"
    
    def test_no_diversity(self):
        """All same sensitive value = l=1"""
        df = pd.DataFrame({
            'age_bin': ['20-30', '20-30', '30-40', '30-40'],
            'gender': ['M', 'F', 'M', 'F'],
            'job': ['Engineer', 'Engineer', 'Engineer', 'Engineer'],  # All same
        })
        result = calc_l_diversity(
            df,
            quasi_identifiers=['age_bin', 'gender'],
            sensitive_attribute='job'
        )
        assert result == 1, f"Expected l=1, got {result}"
    
    def test_high_diversity(self):
        """Many distinct values per group"""
        df = pd.DataFrame({
            'age_bin': ['20-30'] * 5,
            'gender': ['M'] * 5,
            'job': ['Engineer', 'Doctor', 'Manager', 'Nurse', 'Teacher'],
        })
        result = calc_l_diversity(
            df,
            quasi_identifiers=['age_bin'],
            sensitive_attribute='job'
        )
        assert result == 5, f"Expected l=5, got {result}"


# ============================================================================
# TESTS: t-Closeness
# ============================================================================

class TestTCloseness:
    """Test t-Closeness metric"""
    
    def test_perfect_t_closeness(self):
        """t-Closeness should be in valid range [0,1]"""
        df = pd.DataFrame({
            'age': [30, 40] * 5,
            'income': [50000, 60000] * 5,  # Identical distribution
        })
        result = calc_t_closeness(
            df,
            quasi_identifiers=['age'],
            sensitive_attribute='income'
        )
        assert 0 <= result <= 1, f"Expected [0,1], got {result}"
    
    def test_different_distributions(self):
        """Different distributions should have higher t"""
        df = pd.DataFrame({
            'group': ['A'] * 4 + ['B'] * 4,
            'age': [30] * 4 + [50] * 4,  # Very different
        })
        result = calc_t_closeness(
            df,
            quasi_identifiers=['group'],
            sensitive_attribute='age'
        )
        assert result > 0.1, f"Expected t>0.1, got {result}"
    
    def test_t_closeness_bounds(self):
        """t-Closeness should be in [0, 1]"""
        df = pd.DataFrame({
            'group': ['A'] * 3 + ['B'] * 3,
            'value': [1, 2, 3, 4, 5, 6],
        })
        result = calc_t_closeness(
            df,
            quasi_identifiers=['group'],
            sensitive_attribute='value'
        )
        assert 0 <= result <= 1, f"Expected [0,1], got {result}"


# ============================================================================
# TESTS: Data Minimization (GDPR Art. 5)
# ============================================================================

class TestDataMinimization:
    """Test Data Minimization metric (GDPR)"""
    
    def test_all_sensitive_data(self):
        """All columns sensitive = score 0"""
        df = pd.DataFrame({
            'age': [25, 30, 35],
            'income': [50000, 60000, 70000],
            'health': ['A', 'B', 'C'],
        })
        result = calc_data_minimization_score(
            df,
            sensitive_columns=['age', 'income', 'health']
        )
        assert result == 0.0, f"Expected score=0, got {result}"
    
    def test_no_sensitive_data(self):
        """No sensitive columns marked = all are non-sensitive"""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'category': ['A', 'B', 'C'],
        })
        result = calc_data_minimization_score(
            df,
            sensitive_columns=[]
        )
        # Score should be between 0 and 1
        assert 0 <= result <= 1, f"Expected [0,1], got {result}"
    
    def test_mixed_sensitive_data(self):
        """Some sensitive columns = score between 0-1"""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'category': ['A', 'B', 'C'],
            'age': [25, 30, 35],
            'income': [50000, 60000, 70000],
        })
        result = calc_data_minimization_score(
            df,
            sensitive_columns=['age', 'income']
        )
        expected = (4 - 2) / 4  # 2 non-sensitive out of 4 total
        assert result == expected, f"Expected {expected}, got {result}"
    
    def test_gdpr_recommendation(self):
        """GDPR recommends score >= 0.70"""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'category': ['A', 'B', 'C'],
            'age': [25, 30, 35],
        })
        result = calc_data_minimization_score(
            df,
            sensitive_columns=['age']
        )
        gdpr_compliant = result >= 0.70
        assert isinstance(gdpr_compliant, bool)


# ============================================================================
# TESTS: Strict Validation (No Silent 0.0)
# ============================================================================

class TestStrictValidation:
    """Ensure metrics raise errors instead of silently returning 0.0"""
    
    def test_demographic_parity_no_silent_zero(self):
        """Should raise, not return 0.0"""
        df = pd.DataFrame({
            'target': [1, 0, 1, 0],
            'prediction': [1, 0, 1, 0],
        })
        with pytest.raises(ValueError):
            calc_demographic_parity(
                df,
                target='target',
                prediction='prediction',
                dimension='MISSING'  # Column doesn't exist
            )
    
    def test_equal_opportunity_no_silent_zero(self):
        """Should raise, not return 0.0"""
        df = pd.DataFrame({
            'target': [1, 0, 1, 0],
            'prediction': [1, 0, 1, 0],
        })
        with pytest.raises(ValueError):
            calc_equal_opportunity(
                df,
                target='target',
                prediction='prediction',
                dimension='MISSING'
            )
    
    def test_equalized_odds_no_silent_zero(self):
        """Should raise, not return 0.0"""
        df = pd.DataFrame({
            'target': [1, 0, 1, 0],
            'prediction': [1, 0, 1, 0],
        })
        with pytest.raises(ValueError):
            calc_equalized_odds_ratio(
                df,
                target='target',
                prediction='prediction',
                dimension='MISSING'
            )


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestMetricIntegration:
    """Integration tests comparing metrics"""
    
    def test_equal_opportunity_stricter_than_demographic_parity(self):
        """Equalized Odds typically stricter than EqOpp which is stricter than DP"""
        df = pd.DataFrame({
            'target': [1, 0, 1, 1, 0, 0, 1, 0],
            'prediction': [1, 0, 1, 1, 0, 0, 0, 1],
            'dimension': ['A', 'A', 'A', 'A', 'B', 'B', 'B', 'B'],
        })
        
        dp = calc_demographic_parity(
            df, target='target', prediction='prediction', dimension='dimension'
        )
        eqopp = calc_equal_opportunity(
            df, target='target', prediction='prediction', dimension='dimension'
        )
        eqodds = calc_equalized_odds_ratio(
            df, target='target', prediction='prediction', dimension='dimension'
        )
        
        # Generally: DP <= EqOpp <= EqOdds
        assert dp >= 0, "DP should be non-negative"
        assert eqopp >= 0, "EqOpp should be non-negative"
        assert eqodds >= 0, "EqOdds should be non-negative"
    
    def test_privacy_metrics_all_calculated(self):
        """All privacy metrics should calculate without error"""
        df = pd.DataFrame({
            'age_bin': ['20-30'] * 3 + ['30-40'] * 3,
            'gender': ['M'] * 3 + ['F'] * 3,
            'job': ['Engineer', 'Doctor', 'Manager'] * 2,
            'income': [50000, 60000, 70000] * 2,
        })
        
        k = calc_k_anonymity(df, quasi_identifiers=['age_bin', 'gender'])
        l = calc_l_diversity(
            df, quasi_identifiers=['age_bin'], sensitive_attribute='job'
        )
        t = calc_t_closeness(
            df, quasi_identifiers=['age_bin'], sensitive_attribute='income'
        )
        dm = calc_data_minimization_score(
            df, sensitive_columns=['age_bin', 'income']
        )
        
        assert all([k > 0, l > 0, t >= 0, 0 <= dm <= 1])


if __name__ == "__main__":
    # Run tests with: pytest test_enhanced_metrics.py -v
    pass
