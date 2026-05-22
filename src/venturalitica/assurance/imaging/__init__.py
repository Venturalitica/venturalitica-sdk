"""Per-case image-segmentation metrics — thin wrappers over ``monai.metrics``.

OPTIONAL subpackage: needs the ``imaging`` extra (monai + torch + nibabel +
scipy). Importing this package is always safe (it does not eagerly require
monai); calling any helper without monai installed raises a clear error telling
the user to ``pip install venturalitica[imaging]``.

Use these to BUILD the per-case score column (e.g. ``Dice``) that the pure
pandas aggregates in ``venturalitica.assurance.segmentation`` then turn into
power-stats controls.
"""

from .metrics import (
    dice as dice,
)
from .metrics import (
    hausdorff95 as hausdorff95,
)
from .metrics import (
    iou as iou,
)
from .metrics import (
    nsd as nsd,
)

__all__ = ["dice", "iou", "hausdorff95", "nsd"]
