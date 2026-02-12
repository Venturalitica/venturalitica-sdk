from typing import Optional
import pandas as pd

def calc_macro_equal_opportunity_multiclass(
    y_true: pd.Series,
    y_pred: pd.Series,
    protected_attr: pd.Series,
    positive_label: Optional[int] = None,
    **kwargs
) -> float:
    """ Macro-averaged Equal Opportunity for Multi-class. """
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
        y_true_binary = (y_true == class_label).astype(int)
        y_pred_binary = (y_pred == class_label).astype(int)
        
        if y_true_binary.sum() == 0:
            continue
        
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
    """ Micro-averaged Equalized Odds for Multi-class. """
    if len(y_true) < 30:
        raise ValueError("Minimum 30 samples required")
    
    groups = protected_attr.unique()
    if len(groups) < 2:
        raise ValueError(f"Need at least 2 protected groups, found {len(groups)}")
    
    group_metrics = {}
    for group in groups:
        group_mask = (protected_attr == group)
        group_true = y_true[group_mask]
        group_pred = y_pred[group_mask]
        
        correct = (group_true == group_pred).sum()
        total = len(group_true)
        accuracy = correct / total if total > 0 else 0.0
        error_rate = 1 - accuracy
        
        group_metrics[group] = {'accuracy': accuracy, 'error_rate': error_rate}
    
    accuracies = [m['accuracy'] for m in group_metrics.values()]
    error_rates = [m['error_rate'] for m in group_metrics.values()]
    
    tpr_disparity = max(accuracies) - min(accuracies) if accuracies else 0.0
    fpr_disparity = max(error_rates) - min(error_rates) if error_rates else 0.0
    
    return tpr_disparity + fpr_disparity
