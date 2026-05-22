"""Aggregate + fairness metrics over a continuous per-case score column.

PURE pandas/numpy (no torch / no monai) so they ship in the base install. They
turn a per-case score (e.g. Dice per scan) into first-class registry metrics
that get power-stats confidence intervals automatically through ``enforce``.

- ``metrics`` — aggregates (mean/min-group/worst-cell/gap/max).
- ``fairness`` — segmentation-fairness (ESSP/ES-Dice, ESSP-Stdev, and the
  subgroup-disparity family: gap/ratio/std/cv/worst-group/skew). See the
  Dice size-bias caveat in ``fairness``.
"""

from .fairness import (
    calc_es_dice as calc_es_dice,
)
from .fairness import (
    calc_es_iou as calc_es_iou,
)
from .fairness import (
    calc_essp as calc_essp,
)
from .fairness import (
    calc_essp_stdev as calc_essp_stdev,
)
from .fairness import (
    calc_score_cv as calc_score_cv,
)
from .fairness import (
    calc_score_gap as calc_score_gap,
)
from .fairness import (
    calc_score_ratio as calc_score_ratio,
)
from .fairness import (
    calc_score_skew as calc_score_skew,
)
from .fairness import (
    calc_score_std as calc_score_std,
)
from .fairness import (
    calc_subgroup_disparity as calc_subgroup_disparity,
)
from .metrics import (
    calc_group_score_gap as calc_group_score_gap,
)
from .metrics import (
    calc_max_score as calc_max_score,
)
from .metrics import (
    calc_mean_score as calc_mean_score,
)
from .metrics import (
    calc_min_group_score as calc_min_group_score,
)
from .metrics import (
    calc_worst_cell_score as calc_worst_cell_score,
)

__all__ = [
    # Aggregates over a per-case score
    "calc_mean_score",
    "calc_min_group_score",
    "calc_worst_cell_score",
    "calc_group_score_gap",
    "calc_max_score",
    # Segmentation-fairness over a per-case score
    "calc_essp",
    "calc_es_dice",
    "calc_es_iou",
    "calc_essp_stdev",
    "calc_subgroup_disparity",
    "calc_score_gap",
    "calc_score_ratio",
    "calc_score_std",
    "calc_score_cv",
    "calc_score_skew",
]
