from .core import GovernanceValidator
from .integrations import auto_log
from pathlib import Path
from typing import Dict, Union, Any, List, Optional
from .core import ComplianceResult

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
    policies = [policy] if not isinstance(policy, list) else policy
    all_results = []

    for p in policies:
        print(f"\n[Venturalitica] 🛡  Enforcing policy: {p}")
        try:
            validator = GovernanceValidator(str(p))
            results = []

            if data is not None:
                mapping = {
                    'target': target, 
                    'prediction': prediction
                }
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
