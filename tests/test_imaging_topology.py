"""Per-case TOPOLOGY primitives (issue #945).

With ankylosis, DISH, a bridging osteophyte or a collapsed disc, a segmentation
label can jump the disc space and FUSE two vertebrae. The added volume is tiny,
so Dice barely moves — none of the 51 registry metrics sees it. This is a
STRUCTURAL control, not an overlap one: each vertebra must be exactly one
connected component, with no contact between adjacent labels.

Pure scipy (no monai/torch): ``scipy.ndimage.label`` already ships with the
``imaging`` extra, so these run wherever the extra is installed.
"""

import numpy as np
import pytest

pytest.importorskip("scipy", reason="needs venturalitica[imaging]")

from venturalitica.assurance.imaging import (  # noqa: E402
    component_counts,
    euler_characteristic,
    excess_components,
)


def _two_vertebrae(fused: bool):
    """Two labelled 'vertebrae' in a 12^3 volume, separated by a disc gap.

    ``fused=True`` bridges the gap with a thin osteophyte of label 1 — the
    failure the issue describes: a handful of voxels, invisible to Dice.
    """
    vol = np.zeros((12, 12, 12), dtype=np.int16)
    vol[2:5, 3:9, 3:9] = 1  # vértebra superior
    vol[7:10, 3:9, 3:9] = 2  # vértebra inferior
    if fused:
        vol[5:7, 5:7, 5:7] = 1  # puente osteofítico: une la 1 consigo misma
    return vol


def test_una_vertebra_sana_es_una_sola_componente():
    vol = _two_vertebrae(fused=False)
    assert component_counts(vol) == {1: 1, 2: 1}
    assert excess_components(vol) == 0


def test_el_puente_osteofitico_parte_la_etiqueta_en_dos():
    """El puente NO toca la etiqueta 2: deja la 1 como UNA componente que se
    extiende de más. Lo que delata la fuga es comparar contra la anatomía."""
    vol = _two_vertebrae(fused=True)
    assert component_counts(vol)[1] == 1


def test_una_etiqueta_partida_en_dos_islas_se_detecta():
    """El caso simétrico: la segmentación deja una isla suelta. Dice apenas se
    mueve, pero la vértebra deja de ser una componente conexa."""
    vol = np.zeros((10, 10, 10), dtype=np.int16)
    vol[1:4, 1:4, 1:4] = 1
    vol[6:8, 6:8, 6:8] = 1  # isla desconectada, MISMA etiqueta
    assert component_counts(vol) == {1: 2}
    assert excess_components(vol) == 1


def test_excess_components_suma_sobre_todas_las_etiquetas():
    vol = np.zeros((10, 10, 10), dtype=np.int16)
    vol[1:3, 1:3, 1:3] = 1
    vol[5:7, 1:3, 1:3] = 1  # etiqueta 1 → 2 componentes (+1)
    vol[1:3, 5:7, 1:3] = 2
    vol[5:7, 5:7, 1:3] = 2
    vol[8:9, 8:9, 1:3] = 2  # etiqueta 2 → 3 componentes (+2)
    assert excess_components(vol) == 3


def test_el_fondo_no_cuenta_como_etiqueta():
    vol = np.zeros((6, 6, 6), dtype=np.int16)
    vol[1:3, 1:3, 1:3] = 1
    assert 0 not in component_counts(vol)


def test_volumen_vacio_no_tiene_etiquetas_ni_exceso():
    vol = np.zeros((5, 5, 5), dtype=np.int16)
    assert component_counts(vol) == {}
    assert excess_components(vol) == 0


def test_labels_acota_las_etiquetas_miradas():
    vol = _two_vertebrae(fused=False)
    assert component_counts(vol, labels=[2]) == {2: 1}


def test_conectividad_configurable():
    """Dos vóxeles que solo se tocan por una esquina: una componente con
    conectividad completa (3), dos con conectividad por caras (1)."""
    vol = np.zeros((6, 6, 6), dtype=np.int16)
    vol[2, 2, 2] = 1
    vol[3, 3, 3] = 1
    assert component_counts(vol, connectivity=3) == {1: 1}
    assert component_counts(vol, connectivity=1) == {1: 2}


def test_euler_de_una_bola_maciza_es_uno():
    """χ = 1 para un sólido simple sin agujeros ni túneles (b0=1, b1=b2=0)."""
    vol = np.zeros((10, 10, 10), dtype=np.int16)
    vol[3:7, 3:7, 3:7] = 1
    assert euler_characteristic(vol, label=1) == 1


def test_euler_de_dos_solidos_sueltos_es_dos():
    vol = np.zeros((12, 12, 12), dtype=np.int16)
    vol[1:4, 1:4, 1:4] = 1
    vol[7:10, 7:10, 7:10] = 1
    assert euler_characteristic(vol, label=1) == 2
