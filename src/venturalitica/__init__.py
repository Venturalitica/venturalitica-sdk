__version__ = "0.4.0"
from .core import GovernanceValidator
from .integrations import auto_log
from pathlib import Path
from typing import Dict, Union, Any, List, Optional
from .core import ComplianceResult
import time
import json
import os
import json
import os
from contextlib import contextmanager
from dataclasses import asdict
import numpy as np
from datetime import datetime

_SESSION_ENFORCED = False


# Custom JSON encoder para tipos complejos
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
        except:
            pass
        return super().default(o)


def _is_enforced():
    return _SESSION_ENFORCED


@contextmanager
def monitor(name: str = "Training Task", label: Optional[str] = None):
    """
    Multimodal Monitor: Extensible probe-based observation platform.
    Tracks Green AI, Hardware Telemetry, Security Integrity, and Audit Trace.
    """
    from .probes import (
        CarbonProbe,
        HardwareProbe,
        IntegrityProbe,
        HandshakeProbe,
        TraceProbe,
    )

    probes = [
        IntegrityProbe(),
        HardwareProbe(),
        CarbonProbe(),
        HandshakeProbe(_is_enforced),
        TraceProbe(run_name=name, label=label),
    ]

    print(f"\n[Venturalítica] 🟢 Starting monitor: {name}")
    start_time = time.time()

    for probe in probes:
        probe.start()

    try:
        yield
    finally:
        duration = time.time() - start_time
        print(f"[Venturalítica] 🔴 Monitor stopped: {name}")
        print(f"  ⏱  Duration: {duration:.2f}s")

        for probe in probes:
            probe.stop()
            summary = probe.get_summary()
            if summary:
                print(summary)


def enforce(
    data: Any = None,
    metrics: Optional[Dict[str, float]] = None,
    policy: Union[str, Path, List[Union[str, Path]]] = "risks.oscal.yaml",
    target: str = "target",
    prediction: str = "prediction",
    strict: bool = False,
    **attributes,
) -> List[ComplianceResult]:
    """
    Main entry point for enforcing governance policies.
    """
    global _SESSION_ENFORCED
    _SESSION_ENFORCED = True

    policies = [policy] if not isinstance(policy, list) else policy
    all_results = []

    for p in policies:
        print(f"\n[Venturalítica v{__version__}] 🛡  Enforcing policy: {p}")
        try:
            validator = GovernanceValidator(p)
            results = []

            if data is not None:
                mapping = {}

                # [PLG] Robust Column Discovery for critical roles
                actual_target = target if target in data.columns else None
                if not actual_target:
                    # Common industry names for targets
                    target_cands = [
                        "target",
                        "class",
                        "label",
                        "y",
                        "true_label",
                        "ground_truth",
                        "approved",
                        "default",
                        "outcome",
                    ]
                    for cand in target_cands:
                        if cand in data.columns:
                            actual_target = cand
                            break

                actual_prediction = prediction if prediction in data.columns else None
                if not actual_prediction:
                    # Common industry names for predictions
                    pred_cands = [
                        "prediction",
                        "pred",
                        "y_pred",
                        "predictions",
                        "score",
                        "proba",
                        "output",
                    ]
                    for cand in pred_cands:
                        if cand in data.columns:
                            actual_prediction = cand
                            break

                if actual_target:
                    mapping["target"] = actual_target
                if actual_prediction:
                    mapping["prediction"] = actual_prediction

                mapping.update(attributes)
                # pass strict flag to validator so missing/skip behavior can be enforced
                results = validator.compute_and_evaluate(data, mapping, strict=strict)
            elif metrics is not None:
                results = validator.evaluate(metrics)

            if results:
                all_results.extend(results)
                _print_summary(results, is_data_only=(prediction is None))
            else:
                print(f"  ⚠ No applicable controls found in {p}")

        except FileNotFoundError:
            print(f"  ⚠ Policy file not found: {p}")
        except Exception as e:
            if strict:
                # In strict mode we propagate unexpected errors so callers can fail-fast
                raise
            print(f"  ⚠ Unexpected error loading {p}: {e}")

    if all_results:
        auto_log(all_results)

        # Cache results for Local Dashboard
        try:
            os.makedirs(".venturalitica", exist_ok=True)
            results_path = ".venturalitica/results.json"

            existing_results = []
            if os.path.exists(results_path):
                try:
                    with open(results_path, "r") as f:
                        existing_results = json.load(f)
                except:
                    pass

            # Normalize existing results to a list if file contains a bundle/dict
            if isinstance(existing_results, dict):
                if isinstance(existing_results.get('metrics'), list):
                    existing_results = existing_results.get('metrics')
                elif isinstance(existing_results.get('post_metrics'), list):
                    existing_results = existing_results.get('post_metrics')
                else:
                    # Flatten any list values inside dict
                    flattened = []
                    for v in existing_results.values():
                        if isinstance(v, list):
                            flattened.extend(v)
                    existing_results = flattened

            new_results = [asdict(r) for r in all_results]
            # Avoid duplicates if exactly the same control results are added
            # For now, just append to keep it simple for the handshake
            combined = existing_results + new_results

            with open(results_path, "w") as f:
                json.dump(combined, f, indent=2, cls=VenturalíticaJSONEncoder)
            print(
                f"  ✓ Results cached. Run 'venturalitica ui' to see the Compliance Dashboard."
            )
        except Exception as e:
            print(f"  ⚠ Failed to cache results: {e}")

    return all_results


def _print_summary(results: List[ComplianceResult], is_data_only: bool):
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


def save_audit_results(
    results: List[ComplianceResult], path: str = ".venturalitica/results.json"
):
    """
    Manually persists audit results to a JSON file for later processing by the CLI.
    Converts ComplianceResult to MetricInput format expected by SaaS.
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    # Convert ComplianceResult to MetricInput format
    metrics = []
    for result in results:
        # Map operator to comparison
        comparison = "equal"
        if result.operator == "gt":
            comparison = "greater"
        elif result.operator == "lt":
            comparison = "less"

        metric_input = {
            "name": result.control_id,
            "control_id": result.control_id,
            "metric_key": result.metric_key,
            "value": result.actual_value,
            "threshold": result.threshold,
            "passed": result.passed,
            "severity": result.severity,
            "comparison": comparison,
            "context": {"description": result.description, "metadata": result.metadata},
        }
        metrics.append(metric_input)

    with open(path, "w") as f:
        json.dump(metrics, f, indent=2, cls=VenturalíticaJSONEncoder)
    print(f"  ✓ Results saved to {path} ({len(metrics)} metrics)")


# Import public API
from .wrappers import wrap
from .badges import generate_compliance_badge, generate_metric_badge
from .quickstart import quickstart, load_sample, list_scenarios, SAMPLE_SCENARIOS

# Public API
__all__ = [
    "monitor",
    "enforce",
    "wrap",
    "save_audit_results",
    "generate_compliance_badge",
    "generate_metric_badge",
    "ComplianceResult",
    "quickstart",
    "load_sample",
    "list_scenarios",
]
