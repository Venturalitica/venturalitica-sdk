"""Unidad y sentido de las métricas del catálogo (issue #943).

`METRIC_REGISTRY` mapea nombre → función. Eso basta para CALCULAR, pero no para
leer: una entrada anónima no sabe si su número está en milímetros o es una
fracción, ni si mayor es mejor o peor. Sin esa información, un umbral mal
orientado —`gte` sobre una distancia, que pide que el error sea GRANDE— pasa sin
que nada lo detecte.

Este módulo cuelga esos metadatos del nombre de la métrica y ofrece
`check_threshold_orientation`, el equivalente en el SDK del half-gate de
plausibilidad que el motor ya hace por familia de métrica.

Criterio deliberado: **solo opinamos de lo que conocemos.** Una métrica sin
metadatos declarados no produce aviso, igual que en el motor. Es un aviso, no
una puerta: preferimos callar antes que soltar un falso positivo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

__all__ = ["MetricMeta", "METRIC_META", "check_threshold_orientation"]

_LOWER_OPS = {"<", "lt", "<=", "le", "lte"}
_HIGHER_OPS = {">", "gt", ">=", "ge", "gte"}


@dataclass(frozen=True)
class MetricMeta:
    """Qué significa el número de una métrica.

    `unit` es descriptiva (``"mm"``, ``"fraction"``, ``"components"``).
    `lower_is_better` fija el sentido. `bounds` acota el rango válido del umbral
    cuando la métrica lo tiene (``None`` = sin cota, p. ej. una distancia).
    """

    unit: str
    lower_is_better: bool
    bounds: Optional[Tuple[float, float]] = None
    description: str = ""


METRIC_META: Dict[str, MetricMeta] = {
    # Distancia de superficie (#943) — lo que ya calcula `assurance.imaging`.
    "mean_nsd": MetricMeta(
        unit="fraction",
        lower_is_better=False,
        bounds=(0.0, 1.0),
        description="Normalized Surface Dice medio a la tolerancia tau.",
    ),
    "mean_hd95": MetricMeta(
        unit="mm",
        lower_is_better=True,
        bounds=None,
        description="Distancia de Hausdorff al percentil 95, media, en milimetros.",
    ),
    "max_hd95": MetricMeta(
        unit="mm",
        lower_is_better=True,
        bounds=None,
        description="Peor caso de HD95 de la cohorte, en milimetros.",
    ),
    # Topología (#945) — cero-based: 0 = ninguna etiqueta fragmentada.
    "max_excess_components": MetricMeta(
        unit="components",
        lower_is_better=True,
        bounds=(0.0, float("inf")),
        description="Peor caso de componentes conexas sobrantes por etiqueta.",
    ),
    "mean_excess_components": MetricMeta(
        unit="components",
        lower_is_better=True,
        bounds=(0.0, float("inf")),
        description="Componentes conexas sobrantes por caso, en media.",
    ),
}


def check_threshold_orientation(metric_key: str, operator: str, threshold: float) -> Optional[str]:
    """¿El umbral apunta al lado que corresponde? Devuelve la razón, o `None`.

    `None` = plausible, o la métrica no declara metadatos (no opinamos de lo que
    no conocemos). Nunca lanza: es material de aviso, no una puerta.
    """
    meta = METRIC_META.get(metric_key)
    if meta is None:
        return None

    if meta.bounds is not None:
        low, high = meta.bounds
        if not low <= threshold <= high:
            return f"{metric_key} vive en [{low}, {high}] ({meta.unit}) y el umbral es {threshold}"

    if meta.lower_is_better and operator in _HIGHER_OPS:
        return (
            f"en {metric_key} menor es mejor ({meta.unit}), pero '{operator}' exige un valor "
            "GRANDE: el umbral esta invertido"
        )
    if not meta.lower_is_better and operator in _LOWER_OPS:
        return (
            f"en {metric_key} mayor es mejor ({meta.unit}), pero '{operator}' acota por arriba: "
            "el umbral esta invertido"
        )
    return None
