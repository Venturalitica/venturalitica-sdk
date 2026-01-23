import yaml
import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
from .models import InternalPolicy, InternalControl, ComplianceResult
from .storage import BaseStorage, LocalFileSystemStorage

class GovernanceValidator:
    def __init__(self, policy: Union[str, Path], storage: Optional[BaseStorage] = None):
        self.storage = storage or LocalFileSystemStorage()
        self.policy_name = str(policy)
        self.policy: Optional[InternalPolicy] = None
        self._load_policy()

    @property
    def controls(self):
        """Backward compatibility for existing tests."""
        if not self.policy:
            return []
        return [
            {
                'id': c.id,
                'description': c.description,
                'severity': c.severity,
                'metric_key': c.metric_key,
                'threshold': c.threshold,
                'operator': c.operator
            } for c in self.policy.controls
        ]

    def _load_policy(self):
        """Loads and parses the OSCAL policy using the configured storage."""
        # storage.get_policy might raise FileNotFoundError or other errors
        self.policy = self.storage.get_policy(self.policy_name)

    def compute_and_evaluate(self, data: pd.DataFrame, context_mapping: Dict[str, str]) -> List[ComplianceResult]:
        """Computes metrics and evaluates them against controls."""
        from .metrics import METRIC_REGISTRY
        
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Data must be a pandas DataFrame")

        results = []
        for ctrl in self.policy.controls:
            metric_key = ctrl.metric_key
            calc_fn = METRIC_REGISTRY.get(metric_key)
            
            if not calc_fn:
                continue
            
            print(f"  Evaluating Control '{ctrl.id}': {ctrl.description[:50]}...")
            
            # Policy Binding and Attribute Alignment logs
            eval_context = {}
            
            # Explicitly add critical roles if mapped
            if 'target' in context_mapping: eval_context['target'] = context_mapping['target']
            if 'prediction' in context_mapping: eval_context['prediction'] = context_mapping['prediction']
            
            for role, var in ctrl.input_mapping.items():
                actual_col = context_mapping.get(var)
                
                # [PLG] Auto-Binding: Smart discovery based on variable synonyms
                if not actual_col:
                    synonyms = {
                        'gender': ['sex', 'gender', 'sexo'],
                        'age': ['age', 'age_group', 'edad'],
                        'race': ['race', 'ethnicity', 'raza'],
                        'target': ['target', 'class', 'label', 'y', 'true_label'],
                        'prediction': ['prediction', 'pred', 'y_pred'],
                        'dimension': ['sex', 'gender', 'age', 'race']
                    }
                    if var in data.columns:
                        actual_col = var
                    else:
                        for cand in synonyms.get(var, []) + synonyms.get(role, []):
                            if cand in data.columns:
                                actual_col = cand
                                break
                
                if not actual_col:
                    actual_col = "MISSING"

                eval_context[role] = actual_col
                print(f"    [Binding] Virtual Role '{role}' bound to Variable '{var}' (Column: '{actual_col}')")
                
            try:
                from .metrics import METRIC_METADATA
                meta = METRIC_METADATA.get(metric_key, {})
                required = meta.get('required_roles', [])
                
                # Check if all required roles are bound to actual columns
                missing_roles = [r for r in required if eval_context.get(r, "MISSING") == "MISSING"]
                if missing_roles:
                    print(f"    [Skip] Control '{ctrl.id}' requires {missing_roles} which are not provided. Skipping.")
                    continue

                # Execute the metric function with role-mapped columns
                actual = calc_fn(data, **eval_context)
                passed = self._check_condition(actual, ctrl.operator, ctrl.threshold)
                
                results.append(ComplianceResult(
                    control_id=ctrl.id,
                    description=ctrl.description,
                    metric_key=metric_key,
                    threshold=ctrl.threshold,
                    actual_value=actual,
                    operator=ctrl.operator,
                    passed=passed,
                    severity=ctrl.severity
                ))
            except (ValueError, TypeError, KeyError) as e:
                # Expected if columns are missing for a specific metric
                # We log it explicitly to help user identify mapping issues
                print(f"    [Skip] Control '{ctrl.id}' ({metric_key}) skipped: {e}")
                continue
            except Exception as e:
                print(f"⚠ [Venturalitica] Error evaluating {metric_key}: {e}")
                import traceback
                # traceback.print_exc() # Uncomment for deep debugging
                
        return results

    def evaluate(self, metrics: Dict[str, float]) -> List[ComplianceResult]:
        """Evaluates pre-computed metrics against controls."""
        results = []
        for ctrl in self.policy.controls:
            actual = metrics.get(ctrl.metric_key)
            if actual is None:
                continue
                
            passed = self._check_condition(actual, ctrl.operator, ctrl.threshold)
            results.append(ComplianceResult(
                control_id=ctrl.id,
                description=ctrl.description,
                metric_key=ctrl.metric_key,
                threshold=ctrl.threshold,
                actual_value=actual,
                operator=ctrl.operator,
                passed=passed,
                severity=ctrl.severity
            ))
        return results

    def _check_condition(self, actual: float, operator: str, threshold: float) -> bool:
        """Helper to evaluate logical operators."""
        ops = {
            '<': lambda a, b: a < b, 'lt': lambda a, b: a < b,
            '>': lambda a, b: a > b, 'gt': lambda a, b: a > b,
            '<=': lambda a, b: a <= b, 'le': lambda a, b: a <= b,
            '>=': lambda a, b: a >= b, 'ge': lambda a, b: a >= b,
            '==': lambda a, b: a == b, 'eq': lambda a, b: a == b,
            '!=': lambda a, b: a != b, 'ne': lambda a, b: a != b
        }
        return ops.get(operator, lambda a, b: False)(actual, threshold)
