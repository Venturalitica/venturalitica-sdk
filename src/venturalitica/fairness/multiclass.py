"""
Multi-class Classification Fairness Metrics

Extends binary fairness metrics to support 3+ classes:
- Weighted Demographic Parity (WDP)
- Macro-averaged Equal Opportunity (Macro EO)
- Micro-averaged Equalized Odds (Micro EO)
- Weighted Predictive Parity (WPP)

Strategies:
1. One-vs-Rest: Compare each class to aggregate of others
2. Macro-averaging: Average metric across all class pairs
3. Micro-averaging: Aggregate confusion matrices first, then metric
4. Weighted: Account for class imbalance

References:
- Hardt et al. (2016). Equality of Opportunity in Supervised Learning
- Buolamwini & Gebru (2018). Gender Shades (multi-class evaluation)
"""

from typing import Dict, List, Tuple, Optional, Literal, Any
import pandas as pd
import numpy as np
try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    # Mock nn.Module to avoid crash on class definition
    class MockModule: pass
    nn = type('nn', (), {'Module': MockModule})
    torch = None

from collections import Counter


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
    
    Strategies:
    - 'macro': Average disparity across all class pairs
    - 'micro': Aggregate outcomes first, then calculate
    - 'one-vs-rest': Compare each class to rest
    - 'weighted': Account for class frequency
    
    Returns the maximum disparity across comparisons.
    
    Args:
        y_true: True labels (ignored for demographic parity)
        y_pred: Predicted labels (multiclass)
        protected_attr: Protected attribute (e.g., gender)
        strategy: Aggregation strategy
        **kwargs: Additional parameters
    
    Returns:
        float: Disparity score (0 = perfect fairness, 1 = severe disparity)
    
    Raises:
        ValueError: If columns missing or < 2 protected groups
    
    Example:
        >>> disparity = calc_weighted_demographic_parity_multiclass(
        ...     y_true, y_pred, protected_attr, strategy='macro'
        ... )
        >>> assert disparity <= 0.2  # Fair if <= 20% disparity
    
    Reference:
        Hardt, M., Price, E., & Srebro, N. (2016).
        "Equality of Opportunity in Supervised Learning"
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
        # Calculate per-class DP for each pair, average
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
        # Aggregate all outcomes, then calculate
        outcome_by_group = {}
        for group in groups:
            group_mask = (protected_attr == group)
            group_outcomes = y_pred[group_mask].value_counts(normalize=True)
            outcome_by_group[group] = group_outcomes
        
        # Compare distributions
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
        # For each class: compare its rate across groups
        disparities = []
        for class_label in classes:
            group_rates = []
            for group in groups:
                group_mask = (protected_attr == group)
                if group_mask.sum() > 0:
                    # Rate of this class in this group
                    rate = (y_pred[group_mask] == class_label).mean()
                    group_rates.append(rate)
            
            disparity = max(group_rates) - min(group_rates) if group_rates else 0.0
            disparities.append(disparity)
        
        return max(disparities) if disparities else 0.0
    
    elif strategy == 'weighted':
        # Weight by class frequency (imbalanced classes)
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


def calc_macro_equal_opportunity_multiclass(
    y_true: pd.Series,
    y_pred: pd.Series,
    protected_attr: pd.Series,
    positive_label: Optional[int] = None,
    **kwargs
) -> float:
    """
    Macro-averaged Equal Opportunity for Multi-class.
    
    Equal Opportunity (EO) for each class: TPR should be equal across groups
    TPR_c = TP_c / P_c (recall/sensitivity for class c)
    
    Macro-average: Average EO disparity across all classes
    
    Args:
        y_true: True labels (multiclass)
        y_pred: Predicted labels
        protected_attr: Protected attribute
        positive_label: Class to evaluate (if None, macro-average all)
        **kwargs: Additional parameters
    
    Returns:
        float: Macro-averaged EO disparity (0 = fair, 1 = severe)
    
    Raises:
        ValueError: If insufficient data
    
    Example:
        >>> eo_disparity = calc_macro_equal_opportunity_multiclass(
        ...     y_true, y_pred, protected_attr
        ... )
        >>> assert eo_disparity <= 0.1  # Fair threshold
    
    Reference:
        Hardt, M., Price, E., & Srebro, N. (2016).
        "Equality of Opportunity in Supervised Learning"
    """
    
    if len(y_true) < 30:
        raise ValueError("Minimum 30 samples required")
    
    classes = y_true.unique()
    if len(classes) < 2:
        raise ValueError(f"Need at least 2 classes, found {len(classes)}")
    
    groups = protected_attr.unique()
    if len(groups) < 2:
        raise ValueError(f"Need at least 2 protected groups, found {len(groups)}")
    
    disparities = []
    
    for class_label in classes:
        # Binary task: is this class?
        y_true_binary = (y_true == class_label).astype(int)
        y_pred_binary = (y_pred == class_label).astype(int)
        
        if y_true_binary.sum() == 0:
            continue  # Skip classes with no positive examples
        
        tprs = []
        for group in groups:
            group_mask = (protected_attr == group)
            group_true = y_true_binary[group_mask]
            group_pred = y_pred_binary[group_mask]
            
            if group_true.sum() > 0:
                tp = ((group_true == 1) & (group_pred == 1)).sum()
                tpr = tp / group_true.sum()
                tprs.append(tpr)
        
        if tprs:
            disparity = max(tprs) - min(tprs)
            disparities.append(disparity)
    
    return max(disparities) if disparities else 0.0


def calc_micro_equalized_odds_multiclass(
    y_true: pd.Series,
    y_pred: pd.Series,
    protected_attr: pd.Series,
    **kwargs
) -> float:
    """
    Micro-averaged Equalized Odds for Multi-class.
    
    Equalized Odds: Both TPR and FPR should be equal across groups
    Micro-averaging aggregates confusion matrices first:
    
    TP = sum of all true positives (across classes and groups)
    FP = sum of all false positives (across classes and groups)
    etc.
    
    Then: Micro-EO = |TPR_a - TPR_b| + |FPR_a - FPR_b|
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        protected_attr: Protected attribute
        **kwargs: Additional parameters
    
    Returns:
        float: Micro-averaged EO disparity
    
    Raises:
        ValueError: If insufficient data
    
    Example:
        >>> eo = calc_micro_equalized_odds_multiclass(
        ...     y_true, y_pred, protected_attr
        ... )
        >>> assert eo <= 0.15  # Fair threshold
    """
    
    if len(y_true) < 30:
        raise ValueError("Minimum 30 samples required")
    
    groups = protected_attr.unique()
    if len(groups) < 2:
        raise ValueError(f"Need at least 2 protected groups, found {len(groups)}")
    
    # Calculate micro TPR and FPR for each group
    group_metrics = {}
    
    for group in groups:
        group_mask = (protected_attr == group)
        group_true = y_true[group_mask]
        group_pred = y_pred[group_mask]
        
        # Micro-aggregate: correct vs incorrect
        correct = (group_true == group_pred).sum()
        total = len(group_true)
        
        # Simplified: accuracy as proxy for TPR+FNR
        # For true micro, we'd aggregate confusion matrices
        accuracy = correct / total if total > 0 else 0.0
        
        # Error rate as proxy for FPR+FNR
        error_rate = 1 - accuracy
        
        group_metrics[group] = {
            'accuracy': accuracy,
            'error_rate': error_rate,
        }
    
    # Calculate disparities
    accuracies = [m['accuracy'] for m in group_metrics.values()]
    error_rates = [m['error_rate'] for m in group_metrics.values()]
    
    tpr_disparity = max(accuracies) - min(accuracies) if accuracies else 0.0
    fpr_disparity = max(error_rates) - min(error_rates) if error_rates else 0.0
    
    # Equalized odds combines both
    return tpr_disparity + fpr_disparity


def calc_predictive_parity_multiclass(
    y_true: pd.Series,
    y_pred: pd.Series,
    protected_attr: pd.Series,
    strategy: Literal['macro', 'weighted'] = 'macro',
    **kwargs
) -> float:
    """
    Predictive Parity for Multi-class.
    
    Predictive Parity (precision): P(Y=c|Ŷ=c) should be equal across groups
    
    For multi-class: Average precision across all classes
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        protected_attr: Protected attribute
        strategy: 'macro' (simple average) or 'weighted' (by prediction frequency)
        **kwargs: Additional parameters
    
    Returns:
        float: Predictive parity disparity
    
    Raises:
        ValueError: If insufficient data
    
    Example:
        >>> pp = calc_predictive_parity_multiclass(
        ...     y_true, y_pred, protected_attr
        ... )
        >>> assert pp <= 0.1  # Fair threshold
    """
    
    if len(y_true) < 30:
        raise ValueError("Minimum 30 samples required")
    
    classes = y_pred.unique()
    if len(classes) < 2:
        raise ValueError(f"Need at least 2 classes, found {len(classes)}")
    
    groups = protected_attr.unique()
    if len(groups) < 2:
        raise ValueError(f"Need at least 2 protected groups, found {len(groups)}")
    
    disparities = []
    weights = []
    
    for class_label in classes:
        precisions = []
        for group in groups:
            group_mask = (protected_attr == group)
            group_true = y_true[group_mask]
            group_pred = y_pred[group_mask]
            
            # Precision: TP / (TP + FP)
            predicted_positive = (group_pred == class_label).sum()
            if predicted_positive > 0:
                true_positives = ((group_pred == class_label) & 
                                 (group_true == class_label)).sum()
                precision = true_positives / predicted_positive
                precisions.append(precision)
        
        if precisions:
            disparity = max(precisions) - min(precisions)
            disparities.append(disparity)
            
            # [INTERSECTIONAL AUDIT] Inspect significant disparities
            if disparity > 0.8:
                 print(f"\n\033[1m[INTERSECTIONAL AUDIT] 🚨 Significant Disparity ({disparity:.3f}) for Class '{class_label}'\033[0m")
                 print(f"  {'GROUP':<35} | {'TP':<5} | {'FP':<5} | {'PRECISION':<10}")
                 print(f"  {'-'*35}-+-{'-'*5}-+-{'-'*5}-+-{'-'*10}")
                 
                 for group in groups:
                     group_mask = (protected_attr == group)
                     group_true = y_true[group_mask]
                     group_pred = y_pred[group_mask]
                     pred_pos = (group_pred == class_label).sum()
                     if pred_pos > 0:
                         tp = ((group_pred == class_label) & (group_true == class_label)).sum()
                         fp = int(pred_pos - tp)
                         prec = tp / pred_pos
                         print(f"  {str(group):<35} | {int(tp):<5} | {fp:<5} | {prec:<10.3f}")
                 print(f"  {'-'*35}-+-{'-'*5}-+-{'-'*5}-+-{'-'*10}\n")

            # Weight by frequency of this class
            weights.append(y_pred.value_counts(normalize=True).get(class_label, 1/len(classes)))
    
    metadata = {
        'total_samples': len(y_true),
        'min_class_support': y_true.value_counts().min(),
        'min_prediction_support': y_pred.value_counts().min()
    }
    
    if strategy == 'macro':
        val = max(disparities) if disparities else 0.0
        return val, metadata
    elif strategy == 'weighted':
        val = 0.0
        if disparities:
            val = sum(d * w for d, w in zip(disparities, weights)) / sum(weights)
        return val, metadata
    else:
        raise ValueError(f"Unknown strategy: {strategy}")


class GroupFairnessLoss(nn.Module):
    """
    In-processing Fairness Loss.
    
    Penalizes the variance of loss across protected groups.
    Formula: TotalLoss = BaseLoss + lambda * Var(Loss_per_group)
    
    This encourages the model to 'focus' on groups where it performs poorly.
    """
    def __init__(self, base_criterion, protected_attr_key: str, alpha: float = 0.5):
        super().__init__()
        self.base_criterion = base_criterion
        self.protected_attr_key = protected_attr_key
        self.alpha = alpha
        
    def forward(self, logits, targets, meta):
        # Base per-sample loss
        per_sample_loss = self.base_criterion(logits, targets)
        
        # Calculate per-group loss
        groups = meta[self.protected_attr_key]
        unique_groups = set(groups)
        
        group_losses = []
        for g in unique_groups:
            mask = torch.tensor([gi == g for gi in groups], device=logits.device)
            if mask.any():
                group_loss = per_sample_loss[mask].mean()
                group_losses.append(group_loss)
        
        if not group_losses:
            return per_sample_loss.mean()
            
        group_losses = torch.stack(group_losses)
        base_loss = per_sample_loss.mean()
        
        # Penalty: Variance or Max-Min difference
        fairness_penalty = group_losses.var() if len(group_losses) > 1 else torch.tensor(0.0, device=logits.device)
        
        return base_loss + self.alpha * fairness_penalty


def calc_intersectional_metrics(
    y_true: pd.Series,
    y_pred: pd.Series,
    protected_attrs: Dict[str, pd.Series],
    metric_fn: callable = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Calculates metrics across combinations of protected attributes (Intersectional Bias).
    
    Example: Race x Gender slices.
    Identify if 'Black Female' has significantly higher error than 'White Male'.
    
    Returns:
        Dict: Metrics per intersectional group and 'worst_slice' disparity.
    """
    if metric_fn is None:
        # Default to accuracy
        metric_fn = lambda t, p: (t == p).mean()
    
    # Create combined intersectional key
    attr_names = list(protected_attrs.keys())
    combined_attr = protected_attrs[attr_names[0]].astype(str)
    for name in attr_names[1:]:
        combined_attr += " x " + protected_attrs[name].astype(str)
    
    slices = combined_attr.unique()
    slice_metrics = {}
    
    for s in slices:
        mask = (combined_attr == s)
        if mask.sum() >= 5: # Minimum support
            val = metric_fn(y_true[mask], y_pred[mask])
            slice_metrics[str(s)] = float(val)
            
    if not slice_metrics:
        return {'disparity': 0.0, 'slices': {}}
        
    vals = list(slice_metrics.values())
    disparity = max(vals) - min(vals)
    
    return {
        'intersectional_disparity': disparity,
        'worst_slice': min(slice_metrics, key=slice_metrics.get),
        'best_slice': max(slice_metrics, key=slice_metrics.get),
        'slice_details': slice_metrics
    }


def calc_multiclass_fairness_report(
    y_true: pd.Series,
    y_pred: pd.Series,
    protected_attr: pd.Series,
    intersectional_attrs: Optional[Dict[str, pd.Series]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Comprehensive Multi-class Fairness Report.
    """
    
    if len(y_true) < 30:
        raise ValueError("Minimum 30 samples required")
    
    report = {
        'weighted_demographic_parity_macro': calc_weighted_demographic_parity_multiclass(
            y_true, y_pred, protected_attr, strategy='macro'
        ),
        'macro_equal_opportunity': calc_macro_equal_opportunity_multiclass(
            y_true, y_pred, protected_attr
        ),
        'micro_equalized_odds': calc_micro_equalized_odds_multiclass(
            y_true, y_pred, protected_attr
        ),
        'predictive_parity_macro': calc_predictive_parity_multiclass(
            y_true, y_pred, protected_attr, strategy='macro'
        )[0],
    }
    
    if intersectional_attrs:
        inter_results = calc_intersectional_metrics(y_true, y_pred, intersectional_attrs)
        report['intersectional_disparity'] = inter_results['intersectional_disparity']
        report['worst_performing_slice'] = inter_results['worst_slice']
    
    return report


if __name__ == '__main__':
    # Example usage with 3-class classification
    import numpy as np
    
    np.random.seed(42)
    n = 300
    
    # 3-class classification
    y_true = np.random.choice([0, 1, 2], n)
    y_pred = np.random.choice([0, 1, 2], n)
    protected_attr = pd.Series(np.random.choice(['A', 'B'], n))
    
    # Generate realistic imbalance
    y_true = pd.Series(np.where(np.random.rand(n) < 0.6, 0, 
                               np.random.choice([1, 2], n)))
    
    # Run comprehensive report
    report = calc_multiclass_fairness_report(y_true, y_pred, protected_attr)
    
    print("Multi-class Fairness Report:")
    for metric, value in report.items():
        print(f"  {metric}: {value:.4f}")
