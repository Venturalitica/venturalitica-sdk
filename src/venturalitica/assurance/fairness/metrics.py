from .fairness_binary import (
    calc_demographic_parity,
    calc_equal_opportunity,
    calc_equalized_odds_ratio,
    calc_predictive_parity,
    HAS_FAIRLEARN
)
from .fairness_multiclass_simple import (
    calc_multiclass_demographic_parity,
    calc_multiclass_equal_opportunity,
    calc_multiclass_confusion_metrics
)

__all__ = [
    "calc_demographic_parity",
    "calc_equal_opportunity",
    "calc_equalized_odds_ratio",
    "calc_predictive_parity",
    "calc_multiclass_demographic_parity",
    "calc_multiclass_equal_opportunity",
    "calc_multiclass_confusion_metrics",
    "HAS_FAIRLEARN",
]
