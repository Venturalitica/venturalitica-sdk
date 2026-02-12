from typing import Literal
import pandas as pd

def calc_predictive_parity_multiclass(
    y_true: pd.Series,
    y_pred: pd.Series,
    protected_attr: pd.Series,
    strategy: Literal['macro', 'weighted'] = 'macro',
    **kwargs
) -> float:
    """ Predictive Parity for Multi-class. """
    if len(y_true) < 30:
        raise ValueError("Minimum 30 samples required")
    
    classes = y_pred.unique()
    groups = protected_attr.unique()
    disparities = []
    weights = []
    
    for class_label in classes:
        precisions = []
        for group in groups:
            group_mask = (protected_attr == group)
            group_true = y_true[group_mask]
            group_pred = y_pred[group_mask]
            
            predicted_positive = (group_pred == class_label).sum()
            if predicted_positive > 0:
                true_positives = ((group_pred == class_label) & (group_true == class_label)).sum()
                precisions.append(true_positives / predicted_positive)
        
        if precisions:
            disparity = max(precisions) - min(precisions)
            disparities.append(disparity)
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
        val = sum(d * w for d, w in zip(disparities, weights)) / sum(weights) if disparities else 0.0
        return val, metadata
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
