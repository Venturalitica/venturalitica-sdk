"""
JSON encoding and console formatting utilities for Venturalitica.

This module centralizes all formatting logic including custom JSON encoding
for numpy/pandas types and console output formatting.
"""

import json
import numpy as np
from datetime import datetime
from typing import List
from .core import ComplianceResult


class VenturalíticaJSONEncoder(json.JSONEncoder):
    """Encoder que maneja tipos complejos de numpy, pandas y datetime"""

    def default(self, o):
        if isinstance(o, (np.bool_, np.integer, np.floating)):
            return o.item()
        if isinstance(o, (datetime,)):
            return o.isoformat()
        try:
            # Intenta para pandas Timestamp y Series
            if hasattr(o, "isoformat"):
                return o.isoformat()
            if hasattr(o, "tolist"):
                return o.tolist()
        except Exception:
            pass
        return super().default(o)


def print_summary(results: List[ComplianceResult], is_data_only: bool):
    """Prints a beautiful table summary to the console."""
    if not results:
        return

    # ANSI colors for premium terminal feel
    C_G, C_R, C_Y, C_B, C_0 = "\033[92m", "\033[91m", "\033[93m", "\033[1m", "\033[0m"

    passed = sum(1 for r in results if r.passed)
    total = len(results)

    # Table Header
    print(
        f"\n  {C_B}{'CONTROL':<22} {'DESCRIPTION':<38} {'ACTUAL':<10} {'LIMIT':<10} {'RESULT'}{C_0}"
    )
    print(f"  {'─' * 96}")

    for r in results:
        res_label = f"{C_G}✅ PASS{C_0}" if r.passed else f"{C_R}❌ FAIL{C_0}"

        # Map operator to symbol
        op_map = {"gt": ">", "lt": "<", "ge": ">=", "le": "<=", "eq": "==", "ne": "!="}
        limit_str = f"{op_map.get(r.operator, r.operator)} {r.threshold}"

        # Clean description and ID
        desc = (
            (r.description[:35] + "...") if len(r.description) > 35 else r.description
        )
        ctrl_id = r.control_id[:20]

        print(
            f"  {ctrl_id:<22} {desc:<38} {r.actual_value:<10.3f} {limit_str:<10} {res_label}"
        )

        # [Enhancement] Show stability context if available
        if hasattr(r, "metadata") and r.metadata:
            # Filter for key stability metrics to keep it clean
            meta_str = ", ".join([f"{k}={v}" for k, v in r.metadata.items()])
            print(f"  {'':<22} {C_Y}↳ Stability: {meta_str}{C_0}")

    print(f"  {'─' * 96}")
    verdict = (
        f"{C_G}✅ POLICY MET{C_0}" if passed == total else f"{C_R}❌ VIOLATION{C_0}"
    )
    print(f"  {C_B}Audit Summary: {verdict} | {passed}/{total} controls passed{C_0}\n")
