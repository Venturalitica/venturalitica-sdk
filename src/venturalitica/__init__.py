from .core import GovernanceValidator
from .integrations import auto_log
from pathlib import Path
from typing import Dict, Union, Any, List, Optional
from .core import ComplianceResult

def enforce(
    data: Any = None,
    metrics: Dict[str, float] = None,
    policy: Union[str, Path] = "risks.oscal.yaml",
    target: str = None,
    prediction: str = None,
    sensitive: str = None
) -> Optional[List[ComplianceResult]]:
    """
    Main entry point for enforcing governance policies.
    
    Args:
        data: (Optional) Pandas DataFrame for internal metric computation.
        metrics: (Optional) Dict of pre-computed metrics.
        policy: Path to the OSCAL policy file.
        target: Target column name (ground truth).
        prediction: Prediction column name (required for model metrics).
        sensitive: Sensitive attribute column name (required for fairness).
    """
    print(f"\n[Venturalitica] Enforcing policy: {policy}")
    
    try:
        validator = GovernanceValidator(str(policy))
        results = []

        if data is not None:
            # Automatic computation from DataFrame
            mapping = {k: v for k, v in [
                ('target', target), 
                ('prediction', prediction), 
                ('sensitive', sensitive)
            ] if v}
            results = validator.compute_and_evaluate(data, mapping)
            
        elif metrics is not None:
            # Evaluation of pre-computed metrics
            results = validator.evaluate(metrics)
            
        else:
            print("⚠ [Venturalitica] No data or metrics provided for enforcement.")
            return None
        
        if not results:
            print("⚠ [Venturalitica] No applicable controls found for provided input.")
            return results

        # Report & Feedback
        auto_log(results)
        _print_summary(results, is_data_only=(prediction is None))
        
        return results

    except FileNotFoundError:
        print(f"⚠ [Venturalitica] Policy file not found: {policy}")
    except Exception as e:
        print(f"⚠ [Venturalitica] Unexpected error: {e}")
        
    return None

def _print_summary(results: List[ComplianceResult], is_data_only: bool):
    """Prints a concise summary to the console."""
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    print(f"[Venturalitica] Policy Check: {passed}/{total} controls passed.")
    if passed < total:
        print(f"⚠ [Venturalitica] {total - passed} controls FAILED.")
        if is_data_only:
            print("⚠ [Venturalitica] WARNING: Training data bias detected.")
