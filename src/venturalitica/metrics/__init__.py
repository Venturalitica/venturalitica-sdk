from .performance import calc_accuracy, calc_precision, calc_recall, calc_f1, calc_mean
from .fairness import (
    calc_demographic_parity, 
    calc_equal_opportunity,
    calc_equalized_odds_ratio,
    calc_predictive_parity,
    calc_multiclass_demographic_parity,
    calc_multiclass_equal_opportunity,
    calc_multiclass_confusion_metrics,
    HAS_FAIRLEARN
)
from .data import calc_disparate_impact, calc_class_imbalance
from .privacy import calc_k_anonymity, calc_l_diversity, calc_t_closeness, calc_data_minimization_score
from .multiclass import (
    calc_weighted_demographic_parity_multiclass,
    calc_macro_equal_opportunity_multiclass,
    calc_micro_equalized_odds_multiclass,
    calc_predictive_parity_multiclass,
    calc_multiclass_fairness_report,
)
from .causal import (
    calc_path_decomposition,
    calc_counterfactual_fairness,
    calc_fairness_through_awareness,
    calc_causal_fairness_diagnostic,
    CausalEffect,
)

# Registry for all metrics
METRIC_REGISTRY = {
    # Performance metrics
    "accuracy_score": calc_accuracy,
    "precision_score": calc_precision,
    "recall_score": calc_recall,
    "f1_score": calc_f1,
    
    # Fairness metrics (Traditional)
    "demographic_parity_diff": calc_demographic_parity,
    "equal_opportunity_diff": calc_equal_opportunity,
    
    # Fairness metrics (Alternative)
    "equalized_odds_ratio": calc_equalized_odds_ratio,
    "predictive_parity": calc_predictive_parity,
    
    # Multi-class fairness metrics (New)
    "multiclass_demographic_parity": calc_multiclass_demographic_parity,
    "multiclass_equal_opportunity": calc_multiclass_equal_opportunity,
    "multiclass_confusion_metrics": calc_multiclass_confusion_metrics,
    "weighted_demographic_parity_multiclass": calc_weighted_demographic_parity_multiclass,
    "macro_equal_opportunity_multiclass": calc_macro_equal_opportunity_multiclass,
    "micro_equalized_odds_multiclass": calc_micro_equalized_odds_multiclass,
    "predictive_parity_multiclass": calc_predictive_parity_multiclass,
    
    # Data quality
    "disparate_impact": calc_disparate_impact,
    "class_imbalance": calc_class_imbalance,
    
    # Privacy metrics
    "k_anonymity": calc_k_anonymity,
    "l_diversity": calc_l_diversity,
    "t_closeness": calc_t_closeness,
    "data_minimization": calc_data_minimization_score,
    
    # Causal fairness metrics (New)
    "path_decomposition": calc_path_decomposition,
    "counterfactual_fairness": calc_counterfactual_fairness,
    "fairness_through_awareness": calc_fairness_through_awareness,
    "causal_fairness_diagnostic": calc_causal_fairness_diagnostic,
    
    # LLM & Benchmark specific aliases
    "bias_score": calc_mean,
    "stereotype_preference_rate": calc_mean,
    "category_bias_score": calc_mean,
}

# Metric metadata for interpretability
METRIC_METADATA = {
    "demographic_parity_diff": {
        "name": "Demographic Parity",
        "description": "Difference in positive prediction rates between groups",
        "category": "fairness",
        "ideal_value": 0.0,
        "scale": (0.0, 1.0),
        "reference": "https://fairlearn.org",
    },
    "equal_opportunity_diff": {
        "name": "Equal Opportunity",
        "description": "Difference in true positive rates (only positive labels)",
        "category": "fairness",
        "ideal_value": 0.0,
        "scale": (0.0, 1.0),
        "reference": "https://arxiv.org/abs/1610.02413",
    },
    "equalized_odds_ratio": {
        "name": "Equalized Odds",
        "description": "Combined TPR and FPR parity across groups",
        "category": "fairness",
        "ideal_value": 0.0,
        "scale": (0.0, 2.0),
        "reference": "https://arxiv.org/abs/1610.02413",
    },
    "predictive_parity": {
        "name": "Predictive Parity",
        "description": "Difference in precision (positive predictive value) between groups",
        "category": "fairness",
        "ideal_value": 0.0,
        "scale": (0.0, 1.0),
        "reference": "https://fairlearn.org",
    },
    "multiclass_demographic_parity": {
        "name": "Multi-class Demographic Parity",
        "description": "One-vs-rest demographic parity across classes. Use aggregation='max'|'macro'|'micro'",
        "category": "fairness",
        "ideal_value": 0.0,
        "scale": (0.0, 1.0),
        "reference": "https://fairlearn.org/v0.8/user_guide/fairness_metrics/index.html",
    },
    "multiclass_equal_opportunity": {
        "name": "Multi-class Equal Opportunity",
        "description": "One-vs-rest TPR parity for each class across groups",
        "category": "fairness",
        "ideal_value": 0.0,
        "scale": (0.0, 1.0),
        "reference": "https://arxiv.org/abs/1610.02413",
    },
    "multiclass_confusion_metrics": {
        "name": "Multi-class Confusion Matrix Metrics",
        "description": "Comprehensive per-class and per-group metrics (dict output)",
        "category": "fairness",
        "ideal_value": "See documentation",
        "scale": "Variable",
        "reference": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html",
    },
    "k_anonymity": {
        "name": "k-Anonymity",
        "description": "Minimum group size (higher = better privacy)",
        "category": "privacy",
        "ideal_value": float('inf'),  # Higher is better
        "scale": (1.0, float('inf')),
        "reference": "https://en.wikipedia.org/wiki/K-anonymity",
    },
    "l_diversity": {
        "name": "l-Diversity",
        "description": "Minimum distinct sensitive values per group",
        "category": "privacy",
        "ideal_value": float('inf'),
        "scale": (1.0, float('inf')),
        "reference": "https://en.wikipedia.org/wiki/L-diversity",
    },
    "t_closeness": {
        "name": "t-Closeness",
        "description": "Max distribution difference (lower = better)",
        "category": "privacy",
        "ideal_value": 0.0,
        "scale": (0.0, 1.0),
        "reference": "https://en.wikipedia.org/wiki/T-closeness",
    },
    "data_minimization": {
        "name": "Data Minimization (GDPR Art. 5)",
        "description": "Proportion of non-sensitive columns",
        "category": "privacy",
        "ideal_value": 1.0,
        "scale": (0.0, 1.0),
        "reference": "https://gdpr-info.eu/",
    },
    "weighted_demographic_parity_multiclass": {
        "name": "Weighted Demographic Parity (Multi-class)",
        "description": "Demographic parity across 3+ classes with weighted aggregation",
        "category": "fairness",
        "ideal_value": 0.0,
        "scale": (0.0, 1.0),
        "reference": "https://fairlearn.org/v0.8/user_guide/fairness_metrics/index.html",
    },
    "macro_equal_opportunity_multiclass": {
        "name": "Macro-averaged Equal Opportunity (Multi-class)",
        "description": "Equal opportunity (TPR parity) averaged across all classes",
        "category": "fairness",
        "ideal_value": 0.0,
        "scale": (0.0, 1.0),
        "reference": "https://arxiv.org/abs/1610.02413",
    },
    "micro_equalized_odds_multiclass": {
        "name": "Micro-averaged Equalized Odds (Multi-class)",
        "description": "TPR and FPR parity with micro-aggregation of confusion matrices",
        "category": "fairness",
        "ideal_value": 0.0,
        "scale": (0.0, 2.0),
        "reference": "https://arxiv.org/abs/1610.02413",
    },
    "predictive_parity_multiclass": {
        "name": "Predictive Parity (Multi-class)",
        "description": "Precision parity across groups for each class",
        "category": "fairness",
        "ideal_value": 0.0,
        "scale": (0.0, 1.0),
        "reference": "https://fairlearn.org",
    },
    "path_decomposition": {
        "name": "Causal Path Decomposition",
        "description": "Decomposes protected attribute effect into direct and indirect (mediated) components",
        "category": "causal_fairness",
        "ideal_value": "Low direct effect, high indirect",
        "scale": "Variable",
        "reference": "https://en.wikipedia.org/wiki/Mediation_(statistics)",
    },
    "counterfactual_fairness": {
        "name": "Counterfactual Fairness",
        "description": "Proportion of individuals affected if protected attribute counterfactually changed",
        "category": "causal_fairness",
        "ideal_value": 0.0,
        "scale": (0.0, 1.0),
        "reference": "https://arxiv.org/abs/1705.08857",
    },
    "fairness_through_awareness": {
        "name": "Fairness Through Awareness",
        "description": "Evaluates whether legitimate features can predict outcomes without leaking protected information",
        "category": "causal_fairness",
        "ideal_value": "Low information leakage",
        "scale": "Variable",
        "reference": "https://arxiv.org/abs/1412.5644",
    },
    "causal_fairness_diagnostic": {
        "name": "Comprehensive Causal Fairness Diagnostic",
        "description": "Combined path decomposition, counterfactual fairness, and fairness-through-awareness report",
        "category": "causal_fairness",
        "ideal_value": "See diagnostic verdict",
        "scale": "Variable",
        "reference": "https://arxiv.org/abs/1705.08857",
    },
}

