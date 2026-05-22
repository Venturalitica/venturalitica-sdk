"""Per-case image-segmentation metrics — thin wrappers over ``monai.metrics``.

These compute a **single scalar per case** (one pair of masks → one number) so
an eval can BUILD the per-case score column (e.g. ``Dice``) that the
``venturalitica.assurance.segmentation`` aggregates then turn into power-stats
controls. They replace hand-rolled Dice loops.

We do NOT reinvent the metrics: each delegates to MONAI (Apache-2.0):

- :func:`dice`         → ``monai.metrics.DiceMetric``
- :func:`iou`          → ``monai.metrics.MeanIoU``
- :func:`hausdorff95`  → ``monai.metrics.HausdorffDistanceMetric(percentile=95)``
- :func:`nsd`          → ``monai.metrics.SurfaceDiceMetric`` (Normalized Surface Dice)

MONAI / torch are an OPTIONAL extra. Importing this module without them raises a
clear, actionable error telling the user to install ``venturalitica[imaging]``.
Nothing here uses CUDA: inputs are coerced to CPU torch tensors, so it is safe
to run alongside a GPU job.

Mask conventions
----------------
``pred`` and ``gt`` are binary (0/1) masks for a single case, given as numpy
arrays or torch tensors of identical spatial shape. Accepted shapes:

- ``(H, W)`` or ``(H, W, D)``           — bare spatial, single foreground class;
- ``(C, H, W[, D])`` / ``(B, C, ...)``  — already channel/batch-first.

We normalize to MONAI's expected ``[B, C, *spatial]`` (B=1, C=1) internally.
``spacing`` (physical voxel size per axis) is required for a metrically correct
``hausdorff95``/``nsd`` in millimetres; when omitted, distances are in voxels.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Sequence

_IMPORT_ERROR_MSG = (
    "venturalitica.assurance.imaging requires MONAI + torch, which are an "
    "optional extra. Install them with:\n\n    pip install venturalitica[imaging]\n\n"
    "(this pulls monai, torch, nibabel and scipy). The pure-pandas aggregate "
    "metrics in venturalitica.assurance.segmentation need no extra."
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    import numpy as np
    import torch

try:
    import numpy as np
    import torch
    from monai.metrics import (
        DiceMetric,
        HausdorffDistanceMetric,
        MeanIoU,
        SurfaceDiceMetric,
    )

    _HAS_MONAI = True
except ImportError as exc:  # pragma: no cover - exercised via extra-less envs
    _HAS_MONAI = False
    _IMPORT_EXC = exc


def _require_monai() -> None:
    if not _HAS_MONAI:
        raise ImportError(_IMPORT_ERROR_MSG) from _IMPORT_EXC


__all__ = ["dice", "iou", "hausdorff95", "nsd"]


def _to_bchw(mask: Any) -> "torch.Tensor":
    """Coerce a single-case mask to a CPU ``[B=1, C=1, *spatial]`` float tensor.

    Accepts numpy arrays or torch tensors of shape ``(H, W)``, ``(H, W, D)``,
    ``(C, H, W[, D])`` or ``(B, C, H, W[, D])``. We never move data to CUDA.
    """
    if isinstance(mask, np.ndarray):
        t = torch.as_tensor(mask)
    elif torch.is_tensor(mask):
        t = mask.detach()
    else:
        t = torch.as_tensor(np.asarray(mask))

    # Always operate on CPU — keep clear of any concurrent GPU work.
    t = t.to(device="cpu", dtype=torch.float32)

    ndim = t.ndim
    if ndim in (2, 3):
        # Bare spatial (2D image or 3D volume) → add batch + channel dims.
        t = t.unsqueeze(0).unsqueeze(0)
    elif ndim == 4:
        # Could be (C, H, W, D) or (B, C, H, W). Treat as channel-first single
        # case → prepend a batch dim.
        t = t.unsqueeze(0)
    elif ndim == 5:
        # Already [B, C, H, W, D].
        pass
    else:
        raise ValueError(
            f"Unsupported mask ndim={ndim}; expected 2-5 dims "
            "(H,W) / (H,W,D) / (C,...) / (B,C,...)."
        )
    return t


def _check_pair(pred: Any, gt: Any) -> tuple["torch.Tensor", "torch.Tensor"]:
    p = _to_bchw(pred)
    g = _to_bchw(gt)
    if p.shape != g.shape:
        raise ValueError(
            f"pred and gt must share the same shape; got {tuple(p.shape)} vs "
            f"{tuple(g.shape)}."
        )
    return p, g


def _spacing_arg(spacing: Optional[Sequence[float]]):
    """Normalize ``spacing`` for a single case to what MONAI expects.

    MONAI accepts a per-axis sequence; we pass it through unchanged (or ``None``
    so distances are measured in voxels).
    """
    if spacing is None:
        return None
    return [float(s) for s in spacing]


def dice(pred: Any, gt: Any, *, include_background: bool = True) -> float:
    """Per-case Dice (DSC) for one ``(pred, gt)`` mask pair via MONAI.

    Returns a scalar in ``[0, 1]``. Use this to build a per-case ``Dice`` column.
    """
    _require_monai()
    p, g = _check_pair(pred, gt)
    metric = DiceMetric(include_background=include_background, reduction="none")
    res = metric(p, g)
    return float(np.asarray(res.cpu()).reshape(-1)[0])


def iou(pred: Any, gt: Any, *, include_background: bool = True) -> float:
    """Per-case IoU (Jaccard) for one mask pair via ``monai.metrics.MeanIoU``."""
    _require_monai()
    p, g = _check_pair(pred, gt)
    metric = MeanIoU(include_background=include_background, reduction="none")
    res = metric(p, g)
    return float(np.asarray(res.cpu()).reshape(-1)[0])


def hausdorff95(
    pred: Any,
    gt: Any,
    *,
    spacing: Optional[Sequence[float]] = None,
    include_background: bool = True,
) -> float:
    """Per-case 95th-percentile Hausdorff distance via MONAI.

    With ``spacing`` (physical voxel size per axis) the distance is in the same
    physical unit (e.g. mm); without it, in voxels. Lower is better.
    """
    _require_monai()
    p, g = _check_pair(pred, gt)
    metric = HausdorffDistanceMetric(
        include_background=include_background, percentile=95, reduction="none"
    )
    sp = _spacing_arg(spacing)
    res = metric(p, g, spacing=sp) if sp is not None else metric(p, g)
    return float(np.asarray(res.cpu()).reshape(-1)[0])


def nsd(
    pred: Any,
    gt: Any,
    *,
    tolerance_mm: float,
    spacing: Sequence[float],
    include_background: bool = True,
) -> float:
    """Per-case Normalized Surface Dice (NSD) via ``SurfaceDiceMetric``.

    NSD measures the fraction of the surface within ``tolerance_mm`` of the
    reference surface — a clinically meaningful boundary-agreement metric.
    ``spacing`` (physical voxel size per axis) is required so the tolerance is
    in millimetres. Returns a scalar in ``[0, 1]`` (higher is better).
    """
    _require_monai()
    p, g = _check_pair(pred, gt)
    metric = SurfaceDiceMetric(
        class_thresholds=[float(tolerance_mm)],
        include_background=include_background,
        reduction="none",
    )
    res = metric(p, g, spacing=_spacing_arg(spacing))
    return float(np.asarray(res.cpu()).reshape(-1)[0])
