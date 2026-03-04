from venturalitica.assurance.causal import (
    CausalEffect as CausalEffect,
)
from venturalitica.assurance.causal import (
    calc_causal_fairness_diagnostic,
    calc_counterfactual_fairness,
    calc_fairness_through_awareness,
    calc_path_decomposition,
)
from venturalitica.assurance.fairness import (
    HAS_FAIRLEARN as HAS_FAIRLEARN,
)
from venturalitica.assurance.fairness import (
    calc_demographic_parity,
    calc_equal_opportunity,
    calc_equalized_odds_ratio,
    calc_macro_equal_opportunity_multiclass,
    calc_micro_equalized_odds_multiclass,
    calc_multiclass_confusion_metrics,
    calc_multiclass_demographic_parity,
    calc_multiclass_equal_opportunity,
    calc_predictive_parity,
    calc_predictive_parity_multiclass,
    calc_weighted_demographic_parity_multiclass,
)
from venturalitica.assurance.fairness import (
    calc_multiclass_fairness_report as calc_multiclass_fairness_report,
)
from venturalitica.assurance.performance import (
    calc_accuracy,
    calc_f1,
    calc_mean,
    calc_precision,
    calc_recall,
)
from venturalitica.assurance.privacy import (
    calc_data_minimization_score,
    calc_k_anonymity,
    calc_l_diversity,
    calc_t_closeness,
)
from venturalitica.assurance.quality import (
    calc_class_imbalance,
    calc_data_completeness,
    calc_disparate_impact,
    calc_group_min_positive_rate,
)
from venturalitica.assurance.quality.metrics import (
    calc_chunk_diversity,
    calc_classification_distribution,
    calc_provenance_completeness,
    calc_report_coverage,
    calc_subtitle_diversity,
)

from .metadata import METRIC_METADATA as METRIC_METADATA

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
    "group_min_positive_rate": calc_group_min_positive_rate,
    "data_completeness": calc_data_completeness,
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
    # ESG/Financial QA specific metrics
    "classification_distribution": calc_classification_distribution,
    "report_coverage": calc_report_coverage,
    "provenance_completeness": calc_provenance_completeness,
    "chunk_diversity": calc_chunk_diversity,
    "subtitle_diversity": calc_subtitle_diversity,
}
