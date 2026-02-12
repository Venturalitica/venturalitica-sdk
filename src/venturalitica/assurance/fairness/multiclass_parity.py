from typing import Literal
import pandas as pd

def calc_weighted_demographic_parity_multiclass(
    y_true: pd.Series,
    y_pred: pd.Series,
    protected_attr: pd.Series,
    strategy: Literal['macro', 'micro', 'one-vs-rest', 'weighted'] = 'macro',
    **kwargs
) -> float:
    """
    Multi-class Weighted Demographic Parity (WDP).
    
    Extends demographic parity to multi-class scenarios.
    DP requires: P(Ŷ=c|A=a) ≈ P(Ŷ=c|A=b) for all classes c
    """
    # Validation
    if len(y_pred) < 30:
        raise ValueError("Minimum 30 samples required")
    
    if y_pred.nunique() < 2:
        raise ValueError(f"Need at least 2 classes, found {y_pred.nunique()}")
    
    groups = protected_attr.unique()
    if len(groups) < 2:
        raise ValueError(f"Need at least 2 protected groups, found {len(groups)}")
    
    classes = y_pred.unique()
    
    if strategy == 'macro':
        disparities = []
        for class_label in classes:
            group_rates = []
            for group in groups:
                group_mask = (protected_attr == group)
                if group_mask.sum() > 0:
                    rate = (y_pred[group_mask] == class_label).mean()
                    group_rates.append(rate)
            
            if group_rates:
                disparity = max(group_rates) - min(group_rates)
                disparities.append(disparity)
        
        return max(disparities) if disparities else 0.0
    
    elif strategy == 'micro':
        outcome_by_group = {}
        for group in groups:
            group_mask = (protected_attr == group)
            group_outcomes = y_pred[group_mask].value_counts(normalize=True)
            outcome_by_group[group] = group_outcomes
        
        max_disparity = 0.0
        for class_label in classes:
            rates = []
            for group_outcomes in outcome_by_group.values():
                rate = group_outcomes.get(class_label, 0.0)
                rates.append(rate)
            disparity = max(rates) - min(rates) if rates else 0.0
            max_disparity = max(max_disparity, disparity)
        
        return max_disparity
    
    elif strategy == 'one-vs-rest':
        disparities = []
        for class_label in classes:
            group_rates = []
            for group in groups:
                group_mask = (protected_attr == group)
                if group_mask.sum() > 0:
                    rate = (y_pred[group_mask] == class_label).mean()
                    group_rates.append(rate)
            
            disparity = max(group_rates) - min(group_rates) if group_rates else 0.0
            disparities.append(disparity)
        
        return max(disparities) if disparities else 0.0
    
    elif strategy == 'weighted':
        class_weights = y_pred.value_counts(normalize=True)
        disparities = []
        for class_label in classes:
            group_rates = []
            for group in groups:
                group_mask = (protected_attr == group)
                if group_mask.sum() > 0:
                    rate = (y_pred[group_mask] == class_label).mean()
                    group_rates.append(rate)
            
            disparity = max(group_rates) - min(group_rates) if group_rates else 0.0
            weight = class_weights.get(class_label, 1/len(classes))
            disparities.append(disparity * weight)
        
        return sum(disparities) if disparities else 0.0
    
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
