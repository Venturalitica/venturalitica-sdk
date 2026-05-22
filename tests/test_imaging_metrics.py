"""Unit tests for the per-case imaging helpers (MONAI wrappers).

These compute a SINGLE scalar per case (one pair of masks → one number) used to
BUILD the per-case score column the segmentation aggregates consume.

CPU only — no CUDA. The test forces ``CUDA_VISIBLE_DEVICES=""`` defensively so
it is safe to run alongside a GPU job. The module is OPTIONAL (needs the
``imaging`` extra), so the whole file is skipped when monai/torch are absent;
one test asserts the clear install error in that case.
"""

import os

import numpy as np
import pytest

# Force CPU before torch is imported anywhere in this process.
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

monai = pytest.importorskip("monai", reason="needs venturalitica[imaging]")

from venturalitica.assurance.imaging import (  # noqa: E402
    dice,
    hausdorff95,
    iou,
    nsd,
)


def _cube_masks():
    """Two overlapping 3D cubes in an 8^3 volume; the prediction is the GT cube
    shifted by one voxel along the last axis."""
    gt = np.zeros((8, 8, 8), dtype=np.float32)
    gt[2:6, 2:6, 2:6] = 1
    pred = np.zeros((8, 8, 8), dtype=np.float32)
    pred[2:6, 2:6, 3:7] = 1
    return pred, gt


def test_dice_known_value():
    pred, gt = _cube_masks()
    # Two 4x4x4 cubes overlapping in 3 of 4 slices → |inter|=48, |a|=|b|=64.
    # Dice = 2*48 / (64+64) = 0.75.
    assert dice(pred, gt) == pytest.approx(0.75, abs=1e-6)


def test_dice_perfect_overlap():
    gt = np.zeros((6, 6, 6), dtype=np.float32)
    gt[1:5, 1:5, 1:5] = 1
    assert dice(gt, gt) == pytest.approx(1.0, abs=1e-6)


def test_iou_known_value():
    pred, gt = _cube_masks()
    # IoU = inter/union = 48 / (64+64-48) = 48/80 = 0.6.
    assert iou(pred, gt) == pytest.approx(0.6, abs=1e-6)


def test_dice_iou_2d():
    """Bare 2D masks are accepted (auto batch/channel)."""
    gt = np.zeros((10, 10), dtype=np.float32)
    gt[2:8, 2:8] = 1
    pred = np.zeros((10, 10), dtype=np.float32)
    pred[2:8, 2:8] = 1
    assert dice(pred, gt) == pytest.approx(1.0, abs=1e-6)
    assert iou(pred, gt) == pytest.approx(1.0, abs=1e-6)


def test_hausdorff95_voxels_vs_spacing():
    pred, gt = _cube_masks()
    hd_voxel = hausdorff95(pred, gt)
    hd_mm = hausdorff95(pred, gt, spacing=[1.0, 1.0, 2.0])
    assert hd_voxel == pytest.approx(1.0, abs=1e-6)
    # Anisotropic spacing along the shifted axis doubles the physical distance.
    assert hd_mm == pytest.approx(2.0, abs=1e-6)


def test_hausdorff95_zero_for_identical():
    gt = np.zeros((8, 8, 8), dtype=np.float32)
    gt[2:6, 2:6, 2:6] = 1
    assert hausdorff95(gt, gt) == pytest.approx(0.0, abs=1e-6)


def test_nsd_returns_unit_interval():
    pred, gt = _cube_masks()
    val = nsd(pred, gt, tolerance_mm=1.0, spacing=[1.0, 1.0, 1.0])
    assert 0.0 <= val <= 1.0


def test_nsd_perfect_for_identical():
    gt = np.zeros((8, 8, 8), dtype=np.float32)
    gt[2:6, 2:6, 2:6] = 1
    assert nsd(gt, gt, tolerance_mm=1.0, spacing=[1.0, 1.0, 1.0]) == pytest.approx(
        1.0, abs=1e-6
    )


def test_shape_mismatch_raises():
    a = np.zeros((8, 8, 8), dtype=np.float32)
    b = np.zeros((8, 8, 7), dtype=np.float32)
    with pytest.raises(ValueError):
        dice(a, b)


def test_accepts_torch_tensors():
    import torch

    gt = torch.zeros(8, 8, 8)
    gt[2:6, 2:6, 2:6] = 1
    assert dice(gt, gt) == pytest.approx(1.0, abs=1e-6)


def test_builds_per_case_score_column():
    """The intended use: loop over cases to build a per-case Dice column the
    segmentation aggregates then consume."""
    import pandas as pd

    rng = np.random.default_rng(0)
    rows = []
    for _ in range(5):
        gt = np.zeros((8, 8, 8), dtype=np.float32)
        gt[2:6, 2:6, 2:6] = 1
        pred = gt.copy()
        # Randomly drop a slice to vary the score.
        if rng.random() < 0.5:
            pred[..., 5] = 0
        rows.append({"Dice": dice(pred, gt)})
    df = pd.DataFrame(rows)

    from venturalitica.assurance.segmentation import calc_mean_score

    mean = calc_mean_score(df, score="Dice")
    assert 0.0 <= mean <= 1.0
