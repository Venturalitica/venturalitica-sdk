from typing import Dict, Any, Callable
import pandas as pd
import numpy as np

try:
    import fairlearn.metrics as flm
    HAS_FAIRLEARN = True
except ImportError:
    HAS_FAIRLEARN = False

def calc_demographic_parity(df: pd.DataFrame, **kwargs) -> float:
    """
    Calculates Demographic Parity Difference (also known as Disparate Impact Difference).
    
    Measures: max(P(Ŷ=1|A=a)) - min(P(Ŷ=1|A=a)) across protected groups
    
    Returns:
        float: Difference in positive prediction rates between groups (0-1)
               0 = perfect parity, 1 = maximum disparity
    
    Raises:
        ValueError: If required columns are missing or invalid
    """
    target = kwargs.get('target')
    pred = kwargs.get('prediction')
    dim = kwargs.get('dimension')
    
    # Strict validation - raise instead of silently returning 0
    missing = [v for v in [target, pred, dim] if v in [None, "MISSING"]]
    if missing:
        raise ValueError(
            f"Missing required columns for demographic_parity_diff: {missing}. "
            f"Ensure 'target', 'prediction', and 'dimension' are properly mapped. "
            f"💡 Did you mean? Check policy input_mapping and context_mapping."
        )
    
    missing_cols = [c for c in [target, pred, dim] if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Columns not found in DataFrame: {missing_cols}. "
            f"Available columns: {list(df.columns)}. "
            f"💡 Did you mean? Use vl.audit --inspect to see column names."
        )
    
    if HAS_FAIRLEARN:
        try:
            return flm.demographic_parity_difference(
                df[target], df[pred], sensitive_features=df[dim]
            )
        except Exception as e:
            raise ValueError(f"Fairlearn calculation failed: {e}")
    
    # Fallback: manual calculation
    groups = df.groupby(dim)
    pprs = [grp[pred].mean() for _, grp in groups]
    
    if not pprs:
        raise ValueError(f"No groups found in dimension '{dim}'")
    
    return max(pprs) - min(pprs)

def calc_equal_opportunity(df: pd.DataFrame, **kwargs) -> float:
    """
    Calculates Equal Opportunity Difference (TPR parity).
    
    Measures: max(TPR|A=a) - min(TPR|A=a) across protected groups
    Only considers positive labels (target == 1)
    
    Returns:
        float: Difference in true positive rates between groups (0-1)
               0 = perfect equal opportunity, 1 = maximum disparity
    
    Raises:
        ValueError: If required columns are missing or invalid
    """
    target = kwargs.get('target')
    pred = kwargs.get('prediction')
    dim = kwargs.get('dimension')
    
    # Strict validation
    missing = [v for v in [target, pred, dim] if v in [None, "MISSING"]]
    if missing:
        raise ValueError(
            f"Missing required columns for equal_opportunity_diff: {missing}. "
            f"💡 Did you mean? Check policy input_mapping and context_mapping."
        )
        
    missing_cols = [c for c in [target, pred, dim] if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Columns not found in DataFrame: {missing_cols}. "
            f"Available: {list(df.columns)}. "
            f"💡 Did you mean? Use inspect mode to verify column names."
        )
    
    if HAS_FAIRLEARN:
        try:
            return flm.equalized_odds_difference(
                df[target], df[pred], sensitive_features=df[dim]
            )
        except Exception as e:
            raise ValueError(f"Fairlearn calculation failed: {e}")
        
    groups = df.groupby(dim)
    tprs = []
    for _, grp in groups:
        pos_grp = grp[grp[target] == 1]
        if len(pos_grp) > 0:
            tprs.append(pos_grp[pred].mean())
        else:
            # Warning: no positive samples in this group
            tprs.append(np.nan)
    
    # Filter out NaN values
    tprs = [t for t in tprs if not np.isnan(t)]
    
    if not tprs:
        raise ValueError(
            f"No positive samples found for equal_opportunity calculation in groups. "
            f"Target distribution by group:\n{df.groupby(dim)[target].value_counts()}"
        )
    
    return max(tprs) - min(tprs)

def calc_equalized_odds_ratio(df: pd.DataFrame, **kwargs) -> float:
    """
    Equalized Odds Ratio: Combined TPR and FPR parity.
    
    Measures: |max(TPR) - min(TPR)| + |max(FPR) - min(FPR)|
    
    Reference: Hardt et al. (2016) https://arxiv.org/abs/1610.02413
    
    Returns:
        float: Sum of TPR diff + FPR diff (0 = perfect equalized odds)
    
    Raises:
        ValueError: If required columns are missing
    """
    target = kwargs.get('target')
    pred = kwargs.get('prediction')
    dim = kwargs.get('dimension')
    
    missing = [v for v in [target, pred, dim] if v in [None, "MISSING"]]
    if missing:
        raise ValueError(
            f"Missing columns for equalized_odds_ratio: {missing}. "
            f"💡 Did you mean? Ensure target, prediction, and dimension are mapped."
        )
    
    missing_cols = [c for c in [target, pred, dim] if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Columns not found: {missing_cols}. Available: {list(df.columns)}")
    
    groups = df.groupby(dim)
    tprs, fprs = [], []
    
    for _, grp in groups:
        # TPR: True Positive Rate
        pos_grp = grp[grp[target] == 1]
        if len(pos_grp) > 0:
            tprs.append(pos_grp[pred].mean())
        
        # FPR: False Positive Rate
        neg_grp = grp[grp[target] == 0]
        if len(neg_grp) > 0:
            fprs.append((neg_grp[pred] == 1).mean())
    
    tprs = [t for t in tprs if not np.isnan(t)]
    fprs = [f for f in fprs if not np.isnan(f)]
    
    if not tprs or not fprs:
        raise ValueError("Insufficient positive or negative samples for equalized_odds calculation")
    
    tpr_diff = max(tprs) - min(tprs)
    fpr_diff = max(fprs) - min(fprs)
    
    return tpr_diff + fpr_diff

def calc_predictive_parity(df: pd.DataFrame, **kwargs) -> float:
    """
    Predictive Parity (Precision Parity): P(Y=1|Ŷ=1, A=a)
    
    Measures consistency of positive predictive value across groups.
    
    Returns:
        float: Difference in precision between groups (0-1)
    """
    target = kwargs.get('target')
    pred = kwargs.get('prediction')
    dim = kwargs.get('dimension')
    
    missing = [v for v in [target, pred, dim] if v in [None, "MISSING"]]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    
    missing_cols = [c for c in [target, pred, dim] if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Columns not found: {missing_cols}")
    
    groups = df.groupby(dim)
    precisions = []
    
    for _, grp in groups:
        tp = ((grp[target] == 1) & (grp[pred] == 1)).sum()
        fp = ((grp[target] == 0) & (grp[pred] == 1)).sum()
        if (tp + fp) > 0:
            precisions.append(tp / (tp + fp))
    
    if not precisions:
        raise ValueError("No predictions found for precision calculation")
    
    return max(precisions) - min(precisions)


# ============================================================================
# MULTI-CLASS FAIRNESS METRICS
# ============================================================================

def calc_multiclass_demographic_parity(df: pd.DataFrame, **kwargs) -> float:
    """
    Multi-class Demographic Parity: Extends binary parity to multi-class.
    
    Calculates the maximum parity difference across all class-group combinations.
    Uses one-vs-rest approach: for each target class, treats it as positive
    and all others as negative.
    
    Args:
        df: DataFrame with predictions
        target: Target column name
        prediction: Prediction column name
        dimension: Protected attribute column name
        aggregation: 'max' (default) or 'macro' or 'micro'
    
    Returns:
        float: Maximum parity difference (0-1) or aggregated score
    
    Raises:
        ValueError: If required columns missing or invalid
    """
    target = kwargs.get('target')
    pred = kwargs.get('prediction')
    dim = kwargs.get('dimension')
    aggregation = kwargs.get('aggregation', 'max')
    
    # Validation
    missing = [v for v in [target, pred, dim] if v in [None, "MISSING"]]
    if missing:
        raise ValueError(
            f"Missing columns for multiclass_demographic_parity: {missing}. "
            f"💡 Did you mean? Check policy column mappings."
        )
    
    missing_cols = [c for c in [target, pred, dim] if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Columns not found: {missing_cols}")
    
    # Get unique classes from target
    classes = df[target].unique()
    if len(classes) < 2:
        raise ValueError(f"Expected multi-class, but found {len(classes)} unique values")
    
    # Calculate parity for each class (one-vs-rest)
    class_parities = []
    
    for cls in classes:
        # Create binary labels: cls vs rest
        binary_target = (df[target] == cls).astype(int)
        binary_pred = (df[pred] == cls).astype(int)
        
        # Calculate parity for this class
        groups = df.groupby(dim)
        pprs = []
        
        for _, grp in groups:
            if len(grp) > 0:
                ppr = binary_pred[grp.index].mean()
                pprs.append(ppr)
        
        if pprs:
            class_parities.append(max(pprs) - min(pprs))
    
    if not class_parities:
        raise ValueError("No parity scores calculated")
    
    # Aggregate
    if aggregation == 'macro':
        return np.mean(class_parities)
    elif aggregation == 'micro':
        # Weighted by class frequency
        class_weights = [(df[target] == cls).sum() / len(df) for cls in classes]
        return sum(p * w for p, w in zip(class_parities, class_weights))
    else:  # 'max' (default)
        return max(class_parities)


def calc_multiclass_equal_opportunity(df: pd.DataFrame, **kwargs) -> float:
    """
    Multi-class Equal Opportunity: TPR parity across classes and groups.
    
    For each class (one-vs-rest), calculates TPR parity across protected groups.
    Returns maximum TPR difference or aggregated score.
    
    Args:
        df: DataFrame
        target: Target column
        prediction: Prediction column
        dimension: Protected attribute
        aggregation: 'max' (default), 'macro', or 'micro'
    
    Returns:
        float: Maximum TPR difference across classes (0-1)
    """
    target = kwargs.get('target')
    pred = kwargs.get('prediction')
    dim = kwargs.get('dimension')
    aggregation = kwargs.get('aggregation', 'max')
    
    missing = [v for v in [target, pred, dim] if v in [None, "MISSING"]]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    
    missing_cols = [c for c in [target, pred, dim] if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Columns not found: {missing_cols}")
    
    classes = df[target].unique()
    if len(classes) < 2:
        raise ValueError(f"Expected multi-class, found {len(classes)} unique values")
    
    # Calculate TPR parity for each class
    class_tpr_parities = []
    
    for cls in classes:
        # Binary: this class vs rest
        binary_target = (df[target] == cls).astype(int)
        binary_pred = (df[pred] == cls).astype(int)
        
        groups = df.groupby(dim)
        tprs = []
        
        for _, grp in groups:
            # TPR only for positive samples
            pos_idx = grp.index[binary_target[grp.index] == 1]
            if len(pos_idx) > 0:
                tp = binary_pred[pos_idx].mean()
                tprs.append(tp)
        
        if tprs:
            class_tpr_parities.append(max(tprs) - min(tprs))
    
    if not class_tpr_parities:
        raise ValueError("No TPR scores calculated")
    
    # Aggregate
    if aggregation == 'macro':
        return np.mean(class_tpr_parities)
    elif aggregation == 'micro':
        class_weights = [(df[target] == cls).sum() / len(df) for cls in classes]
        return sum(p * w for p, w in zip(class_tpr_parities, class_weights))
    else:
        return max(class_tpr_parities)


def calc_multiclass_confusion_metrics(df: pd.DataFrame, **kwargs) -> Dict[str, float]:
    """
    Multi-class Confusion Matrix Metrics: Detailed fairness analysis.
    
    Returns comprehensive confusion matrix metrics by class and group:
    - Precision, Recall, F1 per class and group
    - Class imbalance ratios
    - Per-group performance gaps
    
    Args:
        df: DataFrame
        target: Target column
        prediction: Prediction column
        dimension: Protected attribute
    
    Returns:
        dict: Comprehensive metrics including per-class and per-group statistics
    
    Raises:
        ValueError: If required columns missing
    """
    target = kwargs.get('target')
    pred = kwargs.get('prediction')
    dim = kwargs.get('dimension')
    
    missing = [v for v in [target, pred, dim] if v in [None, "MISSING"]]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    
    missing_cols = [c for c in [target, pred, dim] if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Columns not found: {missing_cols}")
    
    classes = df[target].unique()
    groups = df[dim].unique()
    
    metrics = {
        'num_classes': len(classes),
        'num_groups': len(groups),
        'class_distribution': {},
        'per_class_metrics': {},
        'per_group_performance_gap': {},
        'macro_metrics': {},
    }
    
    # Class distribution
    for cls in classes:
        metrics['class_distribution'][str(cls)] = (df[target] == cls).sum() / len(df)
    
    # Per-class metrics (macro: average across groups)
    all_precisions = {}
    all_recalls = {}
    
    for cls in classes:
        class_key = str(cls)
        binary_target = (df[target] == cls).astype(int)
        binary_pred = (df[pred] == cls).astype(int)
        
        tp = (binary_target & binary_pred).sum()
        fp = ((1 - binary_target) & binary_pred).sum()
        fn = (binary_target & (1 - binary_pred)).sum()
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        metrics['per_class_metrics'][class_key] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'support': (binary_target == 1).sum(),
        }
        
        all_precisions[class_key] = precision
        all_recalls[class_key] = recall
    
    # Per-group performance gaps
    for group in groups:
        group_key = str(group)
        group_mask = df[dim] == group
        group_df = df[group_mask]
        
        group_acc = (group_df[target] == group_df[pred]).sum() / len(group_df) if len(group_df) > 0 else 0
        metrics['per_group_performance_gap'][group_key] = group_acc
    
    # Macro-averaged metrics
    metrics['macro_metrics'] = {
        'macro_precision': np.mean(list(all_precisions.values())),
        'macro_recall': np.mean(list(all_recalls.values())),
        'micro_accuracy': (df[target] == df[pred]).sum() / len(df),
    }
    
    return metrics
