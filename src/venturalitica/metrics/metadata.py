"""
Metadata descriptions for all registered metrics.

Sprint P — single source of truth moved to `catalog.yaml` (same dir).
This module is a thin loader that exposes `METRIC_METADATA` with the
same shape downstream consumers expect (dict[str, dict] with `scale`
as a tuple, ideal_value preserved as-is). Adding a new metric is now
a single YAML stanza — no Python edits required.

Public surface (unchanged for callers):
  - METRIC_METADATA : dict[str, dict[str, Any]]
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_CATALOG_PATH = Path(__file__).parent / "catalog.yaml"


def _coerce_scale(raw: Any) -> Any:
    """YAML emits list/string for `scale`; legacy callers expect tuple."""
    if isinstance(raw, list) and len(raw) == 2:
        return (float(raw[0]), float(raw[1]))
    return raw


def _load_catalog() -> dict[str, dict[str, Any]]:
    if not _CATALOG_PATH.exists():
        return {}
    with _CATALOG_PATH.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    out: dict[str, dict[str, Any]] = {}
    for key, meta in raw.items():
        if not isinstance(meta, dict):
            continue
        coerced = dict(meta)
        if "scale" in coerced:
            coerced["scale"] = _coerce_scale(coerced["scale"])
        out[key] = coerced
    return out


# Public surface: identical shape to the pre-Sprint-P literal dict.
# Built once at import time; subsequent reads are O(1).
METRIC_METADATA: dict[str, dict[str, Any]] = _load_catalog()

__all__ = ["METRIC_METADATA"]
