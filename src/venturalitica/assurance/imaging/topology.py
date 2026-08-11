"""Per-case TOPOLOGY primitives for labelled segmentations (issue #945).

The overlap metrics in :mod:`venturalitica.assurance.imaging.metrics` answer
"how much of the right stuff did we get?". They do **not** answer "is the shape
structurally sound?".

That gap is not academic. With ankylosis, DISH, a bridging osteophyte or a
collapsed disc, a vertebral label can jump the disc space and fuse two bones —
or, symmetrically, leave a stray island. The added or misplaced volume is tiny,
so Dice barely moves and no aggregate over a Dice column sees it. What catches
it is a **structural** invariant: each anatomical label is exactly one connected
component.

These are pure ``scipy.ndimage`` (no monai, no torch): ``scipy`` already ships
with the ``imaging`` extra, so they run wherever that extra is installed.

Like the overlap wrappers, each returns a **per-case** value, so an eval builds
a column that the aggregates in ``venturalitica.assurance.segmentation`` — or
the named registry entries ``max_excess_components`` / ``mean_excess_components``
— then gate.

Mask conventions
----------------
``volume`` is a LABEL map (integer array): 0 is background, every other value is
an anatomical label. This is the multi-label sibling of the binary masks the
overlap metrics take, and it is what a vertebra segmentation naturally produces.
"""

from __future__ import annotations

from itertools import combinations, product
from typing import Dict, Iterable, Optional

_IMPORT_ERROR_MSG = (
    "venturalitica.assurance.imaging.topology requires numpy + scipy, which "
    "ship with the optional imaging extra. Install them with:\n\n"
    "    pip install venturalitica[imaging]\n"
)

try:
    import numpy as np
    from scipy import ndimage

    _HAS_SCIPY = True
except ImportError as exc:  # pragma: no cover - exercised via extra-less envs
    _HAS_SCIPY = False
    _IMPORT_EXC = exc

__all__ = ["component_counts", "excess_components", "euler_characteristic"]

# Conectividad por defecto = 3 (vóxeles que se tocan por CARA, ARISTA o ESQUINA
# cuentan como conectados). Es la lectura PERMISIVA a propósito: así una medida
# solo se queja de una separación anatómica de verdad, no de un vóxel que roza
# por una esquina. Quien quiera el criterio estricto pasa `connectivity=1`.
_DEFAULT_CONNECTIVITY = 3


def _require_scipy() -> None:
    if not _HAS_SCIPY:  # pragma: no cover - exercised via extra-less envs
        raise ImportError(_IMPORT_ERROR_MSG) from _IMPORT_EXC


def _as_label_array(volume) -> "np.ndarray":
    arr = np.asarray(volume)
    if arr.ndim not in (2, 3):
        raise ValueError(
            f"expected a 2D or 3D label map, got shape {arr.shape} (squeeze channel/batch axes before calling)"
        )
    return arr


def component_counts(
    volume,
    labels: Optional[Iterable[int]] = None,
    connectivity: int = _DEFAULT_CONNECTIVITY,
) -> Dict[int, int]:
    """Connected components per label. Background (0) is never a label.

    ``{label: n_components}`` for every label present (or every label in
    ``labels``, when given). A structurally sound segmentation has exactly 1 for
    each anatomical label; anything above means the label is fragmented.

    ``connectivity`` follows ``scipy.ndimage.generate_binary_structure``:
    1 = faces only, 2 = faces+edges, 3 = faces+edges+corners (the default, see
    the module note).
    """
    _require_scipy()
    arr = _as_label_array(volume)
    if labels is None:
        present = [int(v) for v in np.unique(arr) if int(v) != 0]
    else:
        present = [int(v) for v in labels if int(v) != 0]
    structure = ndimage.generate_binary_structure(arr.ndim, min(connectivity, arr.ndim))
    out: Dict[int, int] = {}
    for label in present:
        _, n = ndimage.label(arr == label, structure=structure)
        out[label] = int(n)
    return out


def excess_components(
    volume,
    labels: Optional[Iterable[int]] = None,
    connectivity: int = _DEFAULT_CONNECTIVITY,
) -> int:
    """How many components MORE than one, summed over labels. 0 = sound.

    This is the per-case scalar to gate on: it is 0 exactly when every label is
    a single connected component, and it grows with the fragmentation. Being
    zero-based makes the threshold obvious (``<= 0``) instead of a convention.

    A label that is absent from the case contributes 0, not -1: absence is a
    coverage question, not a topology one.
    """
    return sum(max(n - 1, 0) for n in component_counts(volume, labels, connectivity).values())


def euler_characteristic(volume, label: int) -> int:
    """Euler characteristic χ of one label's mask, on the cubical complex.

    χ = b₀ − b₁ + b₂ (components − tunnels + cavities). For a simple solid it is
    1; for two disjoint solids, 2; a solid with one tunnel drops to 0; a hollow
    shell rises to 2.

    Computed exactly by counting the cells of the cubical complex —
    χ = V − E + F − C — rather than estimated, so it is integer-valued and has
    no tolerance to tune. 2D and 3D label maps are supported.
    """
    _require_scipy()
    arr = _as_label_array(volume)
    mask = arr == int(label)
    if not mask.any():
        return 0
    padded = np.pad(mask, 1, mode="constant", constant_values=False)
    shape = mask.shape
    ndim = mask.ndim

    def cells(free_axes: tuple) -> int:
        """Cuenta las k-celdas cuyos ejes LIBRES (de extensión unidad) son
        `free_axes`; en los demás la celda vive en la retícula de vértices y la
        cubre cualquiera de los dos vóxeles vecinos."""
        # Longitud de la rejilla por eje: libre → shape[a] (una celda por vóxel),
        # fijo → shape[a] + 1 (una posición por plano de vértices).
        lengths = [shape[a] if a in free_axes else shape[a] + 1 for a in range(ndim)]
        # Offsets a recorrer: en un eje libre el vóxel está determinado (1); en un
        # eje fijo la celda la puede cubrir el vóxel de un lado o del otro (0 y 1).
        offset_choices = [(1,) if a in free_axes else (0, 1) for a in range(ndim)]
        covered = np.zeros(lengths, dtype=bool)
        for offsets in product(*offset_choices):
            window = tuple(slice(o, o + lengths[a]) for a, o in enumerate(offsets))
            covered |= padded[window]
        return int(covered.sum())

    # Fórmula de Euler-Poincaré con signo alterno: +V −E +F −C. Las k-celdas son
    # las que tienen k ejes de extensión unidad (k=0 vértices … k=ndim vóxeles).
    return sum((-1) ** k * cells(free_axes) for k in range(ndim + 1) for free_axes in combinations(range(ndim), k))
