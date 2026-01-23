__version__ = "0.2.3"
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

# Custom JSON encoder para tipos complejos
class VenturaliticaJSONEncoder(json.JSONEncoder):
    """Encoder que maneja tipos complejos de numpy, pandas y datetime"""
    def default(self, obj):
        if isinstance(obj, (np.bool_, np.integer, np.floating)):
            return obj.item()
        if isinstance(obj, (datetime,)):
            return obj.isoformat()
        try:
            # Intenta para pandas Timestamp y Series
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            if hasattr(obj, 'tolist'):
                return obj.tolist()
        except:
            pass
        return super().default(obj)

def _is_enforced():
    return _SESSION_ENFORCED

@contextmanager
def monitor(name: str = "Training Task"):
    """
    Multimodal Monitor: Extensible probe-based observation platform.
    Tracks Green AI, Hardware Telemetry, and Security Integrity.
    """
    from .probes import CarbonProbe, HardwareProbe, IntegrityProbe, HandshakeProbe
    
    probes = [
        IntegrityProbe(),
        HardwareProbe(),
        CarbonProbe(),
        HandshakeProbe(_is_enforced)
    ]

    print(f"\n[Venturalitica] 🟢 Starting monitor: {name}")
    start_time = time.time()
    
    for probe in probes:
        probe.start()

    try:
        yield
    finally:
        duration = time.time() - start_time
        print(f"[Venturalitica] 🔴 Monitor stopped: {name}")
        print(f"  ⏱  Duration: {duration:.2f}s")
        
        for probe in probes:
            probe.stop()
            summary = probe.get_summary()
            if summary:
                print(summary)

def enforce(
    data: Any = None,
    metrics: Dict[str, float] = None,
    policy: Union[str, Path, List[Union[str, Path]]] = "risks.oscal.yaml",
    target: str = "target",
    prediction: str = "prediction",
    **attributes
) -> List[ComplianceResult]:
    """
    Main entry point for enforcing governance policies.
    """
    global _SESSION_ENFORCED
    _SESSION_ENFORCED = True
    
    policies = [policy] if not isinstance(policy, list) else policy
    all_results = []

    for p in policies:
        print(f"\n[Venturalitica] 🛡  Enforcing policy: {p}")
        try:
            validator = GovernanceValidator(str(p))
            results = []

            if data is not None:
                mapping = {}
                if target in data.columns: mapping['target'] = target
                if prediction in data.columns: mapping['prediction'] = prediction
                mapping.update(attributes)
                results = validator.compute_and_evaluate(data, mapping)
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
            print(f"  ⚠ Unexpected error loading {p}: {e}")
            
    if all_results:
        auto_log(all_results)
        
        # Cache results for CLI push
        try:
            os.makedirs(".venturalitica", exist_ok=True)
            results_path = ".venturalitica/results.json"
            with open(results_path, "w") as f:
                serializable_results = [asdict(r) for r in all_results]
                json.dump(serializable_results, f, indent=2, cls=VenturaliticaJSONEncoder)
            print(f"  ✓ Results cached for 'venturalitica push'")
        except Exception as e:
            print(f"  ⚠ Failed to cache results: {e}")
            
    return all_results

def _print_summary(results: List[ComplianceResult], is_data_only: bool):
    """Prints a concise summary to the console."""
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    status = "✅ PASS" if passed == total else "❌ FAIL"
    print(f"  {status} | Controls: {passed}/{total} passed")
    
    for r in results:
        mark = "✓" if r.passed else "✗"
        print(f"    {mark} [{r.control_id}] {r.description[:40]}...: {r.actual_value:.3f} (Limit: {r.operator}{r.threshold})")

def save_audit_results(results: List[ComplianceResult], path: str = ".venturalitica/results.json"):
    """
    Manually persists audit results to a JSON file for later processing by the CLI.
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        serializable_results = [asdict(r) for r in results]
        json.dump(serializable_results, f, indent=2, cls=VenturaliticaJSONEncoder)
    print(f"  ✓ Results saved to {path}")

# Import public API
from .wrappers import wrap
from .badges import generate_compliance_badge, generate_metric_badge
from .quickstart import quickstart, load_sample, list_scenarios

# Public API
__all__ = [
    'monitor',
    'enforce',
    'wrap',
    'save_audit_results',
    'generate_compliance_badge',
    'generate_metric_badge',
    'ComplianceResult',
    'quickstart',
    'load_sample',
    'list_scenarios',
]
