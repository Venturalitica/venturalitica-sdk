import yaml
import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
from .models import InternalPolicy, InternalControl, ComplianceResult
from .storage import BaseStorage, LocalFileSystemStorage


class GovernanceValidator:
    def __init__(
        self,
        policy: Union[str, Path, Dict[str, Any]],
        storage: Optional[BaseStorage] = None,
    ):
        self.storage = storage or LocalFileSystemStorage()
        self.policy_source = policy
        self.policy: Optional[InternalPolicy] = None
        self._load_policy()

    @property
    def controls(self):
        """Backward compatibility for existing tests."""
        if not self.policy:
            return []
        return [
            {
                "id": c.id,
                "description": c.description,
                "severity": c.severity,
                "metric_key": c.metric_key,
                "threshold": c.threshold,
                "operator": c.operator,
            }
            for c in self.policy.controls
        ]

    def _load_policy(self):
        """Loads and parses the OSCAL policy using the configured storage or direct dict."""
        if isinstance(self.policy_source, dict):
            # Direct dict policy - use loader directly
            from .loader import OSCALPolicyLoader

            loader = OSCALPolicyLoader(self.policy_source)
            self.policy = loader.load()
        else:
            # File-based policy - use storage
            self.policy = self.storage.get_policy(str(self.policy_source))

    def compute_and_evaluate(
        self, data: pd.DataFrame, context_mapping: Dict[str, str], strict: bool = False
    ) -> List[ComplianceResult]:
        """Computes metrics and evaluates them against controls.

        If `strict` is True, any control that cannot be evaluated due to missing
        metric implementation or missing role bindings will raise a ValueError.
        """
        from .metrics import METRIC_REGISTRY

        if not isinstance(data, pd.DataFrame):
            raise ValueError("Data must be a pandas DataFrame")

        results = []
        for ctrl in self.policy.controls:
            metric_key = ctrl.metric_key
            calc_fn = METRIC_REGISTRY.get(metric_key)

            if not calc_fn:
                msg = f"No metric function registered for '{metric_key}' in control '{ctrl.id}'"
                if strict:
                    raise ValueError(msg)
                print(f"    [Skip] {msg}")
                continue

            print(f"  Evaluating Control '{ctrl.id}': {ctrl.description[:50]}...")

            # Policy Binding and Attribute Alignment logs
            eval_context = {}

            # Explicitly add critical roles if mapped
            if "target" in context_mapping:
                eval_context["target"] = context_mapping["target"]
            if "prediction" in context_mapping:
                eval_context["prediction"] = context_mapping["prediction"]

            # Forward all extra context_mapping entries (dimension, gender, age, etc.)
            # so metric functions can access them even when input_mapping is empty
            for key, val in context_mapping.items():
                if key not in eval_context:
                    eval_context[key] = val

            # print(f"DEBUG MAPPING: {ctrl.input_mapping}")  # Disabled debug output
            for role, var in ctrl.input_mapping.items():
                # [Fix] Static Parameter Support for Scikit-Learn (e.g. average='macro')
                if role == "average":
                    eval_context[role] = var
                    print(f"    [Param] Set static parameter '{role}' = '{var}'")
                    continue

                actual_col = context_mapping.get(var)

                # [PLG] Auto-Binding: Smart discovery based on variable synonyms
                if not actual_col:
                    synonyms = {
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
                    if var in data.columns:
                        actual_col = var
                    else:
                        for cand in synonyms.get(var, []) + synonyms.get(role, []):
                            if cand in data.columns:
                                actual_col = cand
                                break

                if not actual_col:
                    # Fallback: Treat as literal value if not found in columns
                    # actual_col = "MISSING"
                    actual_col = var

                eval_context[role] = actual_col
                print(
                    f"    [Binding] Virtual Role '{role}' bound to Variable '{var}' (Column: '{actual_col}')"
                )

            # If any virtual variables remain 'MISSING' after auto-binding, consider this a reconciliation failure
            unresolved = [
                r for r in ctrl.input_mapping.keys() if eval_context.get(r) == "MISSING"
            ]
            if unresolved:
                msg = f"Control '{ctrl.id}' has unresolved virtual variables: {unresolved}"
                if strict:
                    raise ValueError(msg)
                print(f"    [Skip] {msg} Skipping.")
                continue

            # Compute metric value and append result
            try:
                # Merge any control params (e.g., quasi_identifiers) into kwargs
                params = getattr(ctrl, "params", {}) or {}

                # Resolve any quasi-identifier or column-like params to actual dataframe columns
                # using the same synonym discovery logic as for virtual role binding.
                synonyms = {
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

                def resolve_col_names(val):
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
                        # try to find a synonym group that contains this item
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
                            # fallback to lower-cased column name if exists
                            if item.lower() in data.columns:
                                resolved.append(item.lower())
                            else:
                                # keep original (metric functions may handle missing columns themselves)
                                resolved.append(item)
                    return resolved

                resolved_params = {}
                for k, v in params.items():
                    if k in ("quasi_identifiers", "sensitive_columns"):
                        resolved = resolve_col_names(v)
                        resolved_params[k] = resolved
                    else:
                        resolved_params[k] = v

                metric_result = calc_fn(data, **eval_context, **resolved_params)

                # Support metric functions that return (value, metadata)
                if isinstance(metric_result, tuple):
                    metric_value, meta_data = metric_result
                else:
                    metric_value = metric_result
                    meta_data = {}

                passed = self._check_condition(
                    metric_value, ctrl.operator, ctrl.threshold
                )
                results.append(
                    ComplianceResult(
                        control_id=ctrl.id,
                        description=ctrl.description,
                        metric_key=metric_key,
                        threshold=ctrl.threshold,
                        actual_value=metric_value,
                        operator=ctrl.operator,
                        passed=passed,
                        severity=ctrl.severity,
                        metadata=meta_data,
                    )
                )
            except (ValueError, TypeError, KeyError) as e:
                # Expected if columns are missing or calculation fails
                if strict:
                    raise
                print(f"    [Skip] Control '{ctrl.id}' ({metric_key}) skipped: {e}")
                continue
            except Exception as e:
                # Unexpected errors
                if strict:
                    raise
                print(f"⚠ [Venturalitica] Error evaluating {metric_key}: {e}")
                continue
        return results

    def evaluate(self, metrics: Dict[str, float]) -> List[ComplianceResult]:
        """Evaluates pre-computed metrics against controls."""
        results = []
        for ctrl in self.policy.controls:
            actual = metrics.get(ctrl.metric_key)
            if actual is None:
                continue

            passed = self._check_condition(actual, ctrl.operator, ctrl.threshold)
            results.append(
                ComplianceResult(
                    control_id=ctrl.id,
                    description=ctrl.description,
                    metric_key=ctrl.metric_key,
                    threshold=ctrl.threshold,
                    actual_value=actual,
                    operator=ctrl.operator,
                    passed=passed,
                    severity=ctrl.severity,
                )
            )
        return results

    def _check_condition(self, actual: float, operator: str, threshold: float) -> bool:
        """Helper to evaluate logical operators."""
        ops = {
            "<": lambda a, b: a < b,
            "lt": lambda a, b: a < b,
            ">": lambda a, b: a > b,
            "gt": lambda a, b: a > b,
            "<=": lambda a, b: a <= b,
            "le": lambda a, b: a <= b,
            ">=": lambda a, b: a >= b,
            "ge": lambda a, b: a >= b,
            "==": lambda a, b: a == b,
            "eq": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            "ne": lambda a, b: a != b,
        }
        return ops.get(operator, lambda a, b: False)(actual, threshold)
