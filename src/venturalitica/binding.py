"""
Unified column name binding and synonym resolution for data role mapping.

This module centralizes all synonym dictionaries and column resolution logic
that was previously duplicated across core.py and api.py.
"""

from typing import Dict, List, Union, Any
import pandas as pd


# Centralized synonym dictionary for all supported data roles
COLUMN_SYNONYMS: Dict[str, List[str]] = {
    "gender": ["sex", "gender", "sexo", "Attribute9"],
    "age": ["age", "age_group", "edad", "Attribute13"],
    "race": ["race", "ethnicity", "raza"],
    "target": [
        "target",
        "class",
        "label",
        "y",
        "true_label",
        "ground_truth",
        "approved",
        "default",
        "outcome",
    ],
    "prediction": [
        "prediction",
        "pred",
        "y_pred",
        "predictions",
        "score",
        "proba",
        "output",
    ],
    "dimension": [
        "sex",
        "gender",
        "age",
        "race",
        "Attribute9",
        "Attribute13",
    ],
}


def resolve_col_names(
    val: Union[str, List[str], tuple, None],
    data: pd.DataFrame,
    synonyms: Dict[str, List[str]] = None,
) -> Union[List[str], Any]:
    """
    Resolve column names using synonym-based discovery.

    Handles:
    - String inputs (comma-separated): "target, gender"
    - List/tuple inputs: ["target", "gender"]
    - Fallback to lowercase column names if not found
    - Returns original value if already a column in data

    Args:
        val: The value to resolve (string, list, tuple, or None)
        data: pandas DataFrame to check columns against
        synonyms: Optional custom synonym dict (defaults to COLUMN_SYNONYMS)

    Returns:
        List of resolved column names, or original value if not resolvable
    """
    if synonyms is None:
        synonyms = COLUMN_SYNONYMS

    if isinstance(val, str):
        parts = [s.strip() for s in val.split(",") if s.strip()]
    elif isinstance(val, (list, tuple)):
        parts = list(val)
    else:
        return val

    resolved = []
    for item in parts:
        if item in data.columns:
            resolved.append(item)
            continue

        # Try to find a synonym group that contains this item
        found = None
        for key, cand_list in synonyms.items():
            if item in cand_list or item == key:
                for cand in cand_list:
                    if cand in data.columns:
                        found = cand
                        break
                if found:
                    break

        if found:
            resolved.append(found)
        else:
            # Fallback to lower-cased column name if exists
            if item.lower() in data.columns:
                resolved.append(item.lower())
            else:
                # Keep original (metric functions may handle missing columns themselves)
                resolved.append(item)

    return resolved


def discover_column(
    requested: str,
    context_mapping: Dict[str, str],
    data: pd.DataFrame,
    synonyms: Dict[str, List[str]] = None,
) -> str:
    """
    Discover a data column using context mapping, synonym resolution, or fallback.

    Args:
        requested: The requested variable name (e.g., "target", "prediction")
        context_mapping: Pre-defined mapping of variable names to column names
        data: pandas DataFrame to check columns against
        synonyms: Optional custom synonym dict (defaults to COLUMN_SYNONYMS)

    Returns:
        The actual column name, or "MISSING" if not found
    """
    if synonyms is None:
        synonyms = COLUMN_SYNONYMS

    # Check if already in context mapping
    actual_col = context_mapping.get(requested)
    if actual_col:
        return actual_col

    # Check if requested name is a direct column
    if requested in data.columns:
        return requested

    # Try synonym discovery
    for cand in synonyms.get(requested, []) + synonyms.get(requested, []):
        if cand in data.columns:
            return cand

    # Last resort: lowercase fallback
    if requested.lower() in data.columns:
        return requested.lower()

    return "MISSING"
