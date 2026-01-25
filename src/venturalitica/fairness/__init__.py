from .metrics import (
    calc_demographic_parity, 
    calc_equal_opportunity,
    calc_equalized_odds_ratio,
    calc_predictive_parity,
    calc_multiclass_demographic_parity,
    calc_multiclass_equal_opportunity,
    calc_multiclass_confusion_metrics,
    HAS_FAIRLEARN
)
from .multiclass import (
    calc_weighted_demographic_parity_multiclass,
    calc_macro_equal_opportunity_multiclass,
    calc_micro_equalized_odds_multiclass,
    calc_predictive_parity_multiclass,
    calc_multiclass_fairness_report,
)
