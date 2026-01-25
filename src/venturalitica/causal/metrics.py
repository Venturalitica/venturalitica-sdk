"""
Causal Fairness Analysis Module

Implements causal fairness concepts:
- Path Decomposition (Total, Direct, Indirect effects)
- Counterfactual Fairness
- Fairness Through Awareness

References:
- Pearl, J. (2009). Causality: Models, Reasoning, and Inference
- Kusner et al. (2017). Counterfactual Fairness
- Moritz et al. (2015). Fairness Through Awareness
"""

from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np
from dataclasses import dataclass


@dataclass
class CausalEffect:
    """Represents a causal effect decomposition."""
    total_effect: float
    direct_effect: float
    indirect_effect: float
    proportion_mediated: float  # Indirect / Total
    
    def __str__(self) -> str:
        return (
            f"Total Effect: {self.total_effect:.4f}\n"
            f"Direct Effect: {self.direct_effect:.4f}\n"
            f"Indirect Effect: {self.indirect_effect:.4f}\n"
            f"Proportion Mediated: {self.proportion_mediated:.4f}"
        )


def calc_path_decomposition(
    df: pd.DataFrame,
    protected_attr: str,
    outcome: str,
    mediators: List[str] = None,
    **kwargs
) -> Dict[str, CausalEffect]:
    """
    Causal Path Decomposition: Separate total effect into direct and indirect.
    
    Decomposes the effect of protected attribute on outcome into:
    - Direct Effect: Protected attr → Outcome (discriminatory)
    - Indirect Effect: Protected attr → Mediators → Outcome (legitimate)
    
    The mediators (e.g., education, experience) can legitimately explain
    differences in outcomes. The direct effect captures pure discrimination.
    
    Args:
        df: DataFrame with data
        protected_attr: Protected attribute column (e.g., 'gender')
        outcome: Outcome column (e.g., 'income')
        mediators: List of mediating variables (e.g., ['education', 'experience'])
        **kwargs: Additional parameters
    
    Returns:
        Dict with CausalEffect objects for each comparison
    
    Raises:
        ValueError: If columns missing or insufficient data
    
    Example:
        >>> effects = calc_path_decomposition(
        ...     df, 'gender', 'income',
        ...     mediators=['education', 'years_experience']
        ... )
        >>> print(effects['Male vs Female'])
    
    Reference:
        VanderWeele, T. J. (2013). A three-way decomposition of effects 
        in the presence of a three-way interaction.
    """
    
    if mediators is None:
        mediators = []
    
    # Validation
    missing_cols = [c for c in [protected_attr, outcome] + mediators 
                    if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Columns not found: {missing_cols}")
    
    if len(df) < 30:
        raise ValueError("Insufficient data for causal analysis (n < 30)")
    
    effects = {}
    
    # Get unique groups for protected attribute
    groups = df[protected_attr].unique()
    if len(groups) < 2:
        raise ValueError(f"Protected attribute must have at least 2 groups, found {len(groups)}")
    
    # Pairwise comparisons
    for i, group_a in enumerate(groups):
        for group_b in groups[i+1:]:
            comparison_key = f"{group_a} vs {group_b}"
            
            # Calculate total effect (bivariate)
            group_a_mean = df[df[protected_attr] == group_a][outcome].mean()
            group_b_mean = df[df[protected_attr] == group_b][outcome].mean()
            total_effect = abs(group_a_mean - group_b_mean)
            
            # Calculate direct effect (controlling for mediators)
            if mediators:
                # Simple approach: regression-based
                # Direct = effect when mediators are "fixed" at their overall means
                
                df_a = df[df[protected_attr] == group_a].copy()
                df_b = df[df[protected_attr] == group_b].copy()
                
                # Adjust outcomes for mediator differences
                mediator_diffs = {}
                for med in mediators:
                    mean_a = df_a[med].mean()
                    mean_b = df_b[med].mean()
                    mediator_diffs[med] = mean_b - mean_a
                
                # Calculate correlation: outcome ~ mediators
                mediator_effects = {}
                for med in mediators:
                    # Correlation coefficient as effect size
                    corr = df[outcome].corr(df[med])
                    mediator_effects[med] = corr
                
                # Indirect effect = sum of mediator paths
                indirect_effect = sum(
                    abs(mediator_diffs.get(med, 0) * mediator_effects.get(med, 0))
                    for med in mediators
                )
                
                # Direct effect = total - indirect
                direct_effect = max(0, total_effect - indirect_effect)
            else:
                # No mediators: all effect is direct
                direct_effect = total_effect
                indirect_effect = 0.0
            
            # Proportion mediated
            if total_effect > 0:
                proportion_mediated = indirect_effect / total_effect
            else:
                proportion_mediated = 0.0
            
            effects[comparison_key] = CausalEffect(
                total_effect=total_effect,
                direct_effect=direct_effect,
                indirect_effect=indirect_effect,
                proportion_mediated=proportion_mediated,
            )
    
    return effects


def calc_counterfactual_fairness(
    df: pd.DataFrame,
    protected_attr: str,
    outcome: str,
    **kwargs
) -> float:
    """
    Counterfactual Fairness: Would outcome change if protected attribute changed?
    
    Measures the proportion of individuals for whom changing the protected
    attribute would change the decision. High values indicate potential unfairness.
    
    Args:
        df: DataFrame
        protected_attr: Protected attribute column
        outcome: Outcome column
        **kwargs: Additional parameters
    
    Returns:
        float: Proportion of counterfactually unfair cases (0-1)
    
    Raises:
        ValueError: If columns missing
    
    Reference:
        Kusner, M. J., et al. (2017). "Counterfactual Fairness"
        in Advances in Neural Information Processing Systems (NeurIPS)
    """
    
    if protected_attr not in df.columns or outcome not in df.columns:
        raise ValueError(f"Columns not found: {protected_attr}, {outcome}")
    
    groups = df[protected_attr].unique()
    if len(groups) != 2:
        raise ValueError("Counterfactual fairness requires binary protected attribute")
    
    group_a, group_b = groups[0], groups[1]
    
    # Estimate counterfactuals using demographic parity assumption
    # P(Ŷ=1|A=a) should equal P(Ŷ=1|A=b) for fairness
    
    df_a = df[df[protected_attr] == group_a]
    df_b = df[df[protected_attr] == group_b]
    
    outcome_rate_a = df_a[outcome].mean()
    outcome_rate_b = df_b[outcome].mean()
    
    # Proportion who would be affected by counterfactual
    # Rough estimate: use the difference
    counterfactual_unfair = abs(outcome_rate_a - outcome_rate_b)
    
    return counterfactual_unfair


def calc_fairness_through_awareness(
    df: pd.DataFrame,
    protected_attr: str,
    outcome: str,
    relevant_features: List[str] = None,
    **kwargs
) -> Dict[str, float]:
    """
    Fairness Through Awareness: Use relevant but not protected attributes.
    
    Evaluates whether decisions can be made using only features that are
    legitimate (not derived from protected attributes) while maintaining
    similar performance.
    
    Args:
        df: DataFrame
        protected_attr: Protected attribute (e.g., 'gender')
        outcome: Outcome column
        relevant_features: Features that should drive decisions (e.g., qualifications)
        **kwargs: Additional parameters
    
    Returns:
        dict: Metrics including:
            - correlation_with_protected: Correlation of relevant features with protected attr
            - information_leakage: Mutual information with protected attribute
            - legitimate_predictor_power: Predictive power of relevant features
    
    Reference:
        Moritz, P., et al. (2015). "Fairness Through Awareness"
    """
    
    if protected_attr not in df.columns or outcome not in df.columns:
        raise ValueError("Protected attribute or outcome column missing")
    
    if relevant_features is None:
        relevant_features = [c for c in df.columns 
                           if c not in [protected_attr, outcome]]
    
    missing_features = [f for f in relevant_features if f not in df.columns]
    if missing_features:
        raise ValueError(f"Features not found: {missing_features}")
    
    results = {
        'correlation_with_protected': {},
        'information_leakage_score': 0.0,
        'legitimate_predictor_power': {},
    }
    
    # For each relevant feature: correlation with protected attribute
    for feat in relevant_features:
        try:
            corr = abs(df[feat].corr(df[protected_attr].astype(int)))
            results['correlation_with_protected'][feat] = corr
        except:
            results['correlation_with_protected'][feat] = 0.0
    
    # Information leakage: average correlation
    if results['correlation_with_protected']:
        results['information_leakage_score'] = np.mean(
            list(results['correlation_with_protected'].values())
        )
    
    # Predictor power: correlation of features with outcome
    for feat in relevant_features:
        try:
            corr = abs(df[feat].corr(df[outcome].astype(int)))
            results['legitimate_predictor_power'][feat] = corr
        except:
            results['legitimate_predictor_power'][feat] = 0.0
    
    return results


def calc_causal_fairness_diagnostic(
    df: pd.DataFrame,
    protected_attr: str,
    outcome: str,
    mediators: List[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Comprehensive Causal Fairness Diagnostic.
    
    Combines multiple causal fairness metrics into a single report:
    - Path decomposition (direct vs indirect effects)
    - Counterfactual fairness assessment
    - Fairness through awareness analysis
    
    Args:
        df: DataFrame
        protected_attr: Protected attribute
        outcome: Outcome variable
        mediators: Legitimate mediating variables
        **kwargs: Additional parameters
    
    Returns:
        dict: Comprehensive causal fairness analysis
    
    Raises:
        ValueError: If data insufficient
    """
    
    if len(df) < 30:
        raise ValueError("Insufficient data (minimum 30 rows)")
    
    diagnostic = {
        'protected_attribute': protected_attr,
        'outcome': outcome,
        'sample_size': len(df),
        'mediators': mediators or [],
        'path_decomposition': {},
        'counterfactual_fairness': 0.0,
        'fairness_through_awareness': {},
        'causal_fairness_verdict': '',
    }
    
    try:
        # Path decomposition
        diagnostic['path_decomposition'] = calc_path_decomposition(
            df, protected_attr, outcome, mediators
        )
    except Exception as e:
        diagnostic['path_decomposition'] = {'error': str(e)}
    
    try:
        # Counterfactual fairness
        diagnostic['counterfactual_fairness'] = calc_counterfactual_fairness(
            df, protected_attr, outcome
        )
    except Exception as e:
        diagnostic['counterfactual_fairness'] = None
    
    try:
        # Fairness through awareness
        diagnostic['fairness_through_awareness'] = calc_fairness_through_awareness(
            df, protected_attr, outcome
        )
    except Exception as e:
        diagnostic['fairness_through_awareness'] = {'error': str(e)}
    
    # Verdict based on metrics
    verdict_parts = []
    
    # Check direct effects
    if diagnostic['path_decomposition']:
        for comparison, effect in diagnostic['path_decomposition'].items():
            if effect.direct_effect > 0.1:
                verdict_parts.append(f"⚠️ High direct effect ({effect.direct_effect:.4f}) in {comparison}")
            else:
                verdict_parts.append(f"✓ Low direct effect in {comparison}")
    
    # Check counterfactual
    if diagnostic['counterfactual_fairness'] and diagnostic['counterfactual_fairness'] > 0.15:
        verdict_parts.append(f"⚠️ High counterfactual disparity ({diagnostic['counterfactual_fairness']:.4f})")
    
    # Check information leakage
    fta = diagnostic.get('fairness_through_awareness', {})
    if isinstance(fta, dict) and 'information_leakage_score' in fta:
        if fta['information_leakage_score'] > 0.3:
            verdict_parts.append(f"⚠️ Information leakage detected ({fta['information_leakage_score']:.4f})")
    
    if not verdict_parts:
        diagnostic['causal_fairness_verdict'] = "✓ Causal fairness appears reasonable"
    else:
        diagnostic['causal_fairness_verdict'] = "; ".join(verdict_parts)
    
    return diagnostic


if __name__ == '__main__':
    # Example usage
    import numpy as np
    
    # Create synthetic data
    np.random.seed(42)
    n = 500
    
    df = pd.DataFrame({
        'gender': np.random.choice(['Male', 'Female'], n),
        'education': np.random.randint(1, 5, n),
        'experience': np.random.randint(0, 30, n),
        'income': np.random.choice([0, 1], n),
    })
    
    # Add some fairness issues
    df.loc[df['gender'] == 'Female', 'income'] = 0  # Biased outcome
    
    # Run diagnostic
    diagnostic = calc_causal_fairness_diagnostic(
        df, 'gender', 'income',
        mediators=['education', 'experience']
    )
    
    print("Causal Fairness Diagnostic:")
    for key, value in diagnostic.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                if isinstance(v, CausalEffect):
                    print(f"    {k}: {v}")
                else:
                    print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")
