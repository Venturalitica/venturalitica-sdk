from .performance import calc_accuracy, calc_precision, calc_recall, calc_f1
from .fairness import calc_demographic_parity, calc_equal_opportunity, HAS_FAIRLEARN
from .data import calc_disparate_impact, calc_class_imbalance

METRIC_REGISTRY = {
    "accuracy_score": calc_accuracy,
    "precision_score": calc_precision,
    "recall_score": calc_recall,
    "f1_score": calc_f1,
    "demographic_parity_diff": calc_demographic_parity,
    "equal_opportunity_diff": calc_equal_opportunity,
    "disparate_impact": calc_disparate_impact,
    "class_imbalance": calc_class_imbalance,
}
