"""Named catalogue entries for surface distance and topology (issues #943, #945).

`assurance.imaging` already COMPUTES nsd and hausdorff95, and any per-case
scalar can be gated because the aggregates resolve their column from the bound
`score` role. What was missing is the NAME: a control declared as
`metric: mean_score` over a column each project baptises by convention.

Three concrete consequences, all fixed here:

1. The identity of the gated metric never reached the file. The compiled OSCAL
   builds its description as "<risk> — <metric>", so it read "… — mean_score":
   a gate on NSD@tau and one on mean Dice were INDISTINGUISHABLE in the signed
   bundle.
2. The catalogue could carry no unit or sense. HD95 is in millimetres and lower
   is better; `mean_score` knows neither, so a wrongly oriented threshold
   (`gte` on HD95) passed with nothing to detect it.
3. Every project reinvented the column name.
"""

import pandas as pd
import pytest

from venturalitica.metrics import METRIC_META, METRIC_REGISTRY, check_threshold_orientation


def _df():
    return pd.DataFrame(
        {
            "case": ["a", "b", "c", "d"],
            "nsd": [0.95, 0.90, 0.80, 0.99],
            "hd95_mm": [1.0, 2.0, 9.0, 1.5],
            "excess_components": [0, 0, 2, 0],
        }
    )


# ── #943: la métrica gateada tiene nombre propio ────────────────────────────
@pytest.mark.parametrize("name", ["mean_nsd", "mean_hd95", "max_hd95"])
def test_las_metricas_de_superficie_estan_en_el_catalogo(name):
    assert name in METRIC_REGISTRY, f"{name} debe tener entrada propia, no ser un mean_score anónimo"


def test_mean_nsd_promedia_la_columna_enlazada():
    assert METRIC_REGISTRY["mean_nsd"](_df(), score="nsd") == pytest.approx(0.91)


def test_mean_hd95_promedia_en_milimetros():
    assert METRIC_REGISTRY["mean_hd95"](_df(), score="hd95_mm") == pytest.approx(3.375)


def test_max_hd95_es_el_peor_caso_no_el_mejor():
    """En «menor es mejor», el peor caso es el MÁXIMO. Un `max_score` genérico
    no sabe eso; una entrada con sentido, sí."""
    assert METRIC_REGISTRY["max_hd95"](_df(), score="hd95_mm") == pytest.approx(9.0)


# ── #943 punto 2: el catálogo lleva unidad y sentido ────────────────────────
def test_hd95_declara_milimetros_y_que_menor_es_mejor():
    meta = METRIC_META["mean_hd95"]
    assert meta.unit == "mm"
    assert meta.lower_is_better is True
    assert meta.bounds is None, "una distancia no está acotada por arriba"


def test_nsd_declara_fraccion_acotada_y_que_mayor_es_mejor():
    meta = METRIC_META["mean_nsd"]
    assert meta.unit == "fraction"
    assert meta.lower_is_better is False
    assert meta.bounds == (0.0, 1.0)


def test_un_umbral_mal_orientado_sobre_hd95_se_detecta():
    """`gte` sobre HD95 pide una distancia GRANDE: exactamente al revés."""
    assert check_threshold_orientation("mean_hd95", "gte", 2.0) is not None
    assert check_threshold_orientation("mean_hd95", "lt", 2.0) is None


def test_un_umbral_mal_orientado_sobre_nsd_se_detecta():
    assert check_threshold_orientation("mean_nsd", "lt", 0.9) is not None
    assert check_threshold_orientation("mean_nsd", "gt", 0.9) is None


def test_un_umbral_fuera_de_rango_se_detecta():
    assert check_threshold_orientation("mean_nsd", "gt", 1.4) is not None


def test_una_metrica_sin_metadatos_no_opina():
    """Sin unidad ni sentido declarados no inventamos una opinión: solo
    hablamos de las familias que conocemos, igual que el half-gate del motor."""
    assert check_threshold_orientation("mean_score", "gte", 999.0) is None


# ── #945: la topología también entra al catálogo con su nombre ──────────────
@pytest.mark.parametrize("name", ["max_excess_components", "mean_excess_components"])
def test_la_topologia_esta_en_el_catalogo(name):
    assert name in METRIC_REGISTRY


def test_max_excess_components_delata_el_caso_fragmentado():
    assert METRIC_REGISTRY["max_excess_components"](_df(), score="excess_components") == pytest.approx(2.0)


def test_excess_components_es_cero_based_y_menor_es_mejor():
    meta = METRIC_META["max_excess_components"]
    assert meta.lower_is_better is True
    assert meta.unit == "components"
