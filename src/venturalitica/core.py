from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from .binding import COLUMN_SYNONYMS, resolve_col_names
from .models import ComplianceResult, InternalPolicy
from .storage import BaseStorage, LocalFileSystemStorage


class ComplianceBlockError(RuntimeError):
    """Raised when a control with enforcement_mode='block' fails.

    This halts the pipeline regardless of the strict flag, as the policy itself
    has declared the control blocking.
    """


class AssuranceValidator:
    def __init__(
        self,
        policy: Union[str, Path, Dict[str, Any]],
        storage: Optional[BaseStorage] = None,
        strict: bool = False,
    ):
        import os

        self.storage = storage or LocalFileSystemStorage()
        self.policy_source = policy
        self.policy: Optional[InternalPolicy] = None

        # Auto-detect Strict Mode (CI or Explicit Env)
        self.strict = (
            strict
            or os.getenv("CI") == "true"
            or os.getenv("VENTURALITICA_STRICT") == "true"
        )
        if self.strict and not strict:
            print("    [Strict] Enforcing strict compliance mode (CI/Env detected).")

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
        from .models import InternalPolicy

        if isinstance(self.policy_source, InternalPolicy):
            self.policy = self.policy_source
        elif isinstance(self.policy_source, dict):
            # Direct dict policy - use loader directly
            from .loader import OSCALPolicyLoader

            loader = OSCALPolicyLoader(self.policy_source)
            self.policy = loader.load()
        else:
            # File-based policy - use storage
            self.policy = self.storage.get_policy(str(self.policy_source))

    def compute_and_evaluate(
        self,
        data: pd.DataFrame,
        context_mapping: Dict[str, str],
        strict: Optional[bool] = None,
        phase: Optional[str] = None,
    ) -> List[ComplianceResult]:
        """Computes metrics and evaluates them against controls.

        If `strict` is True (or if the validator was initialized in strict mode via CI env vars),
        any control that cannot be evaluated due to missing metric implementation or missing role
        bindings will raise a ValueError.

        If `phase` is provided, only controls whose `lifecycle_phase` metadata matches
        (or is absent) are evaluated. Phases are the values proposed in the OSCAL profile:
        `training`, `validation`, `monitoring`, `incident`. Controls tagged `monitoring`
        are skipped by the SDK because they target the runtime proxy (FairGage).

        Controls declaring `enforcement_mode: block` that fail evaluation raise
        ComplianceBlockError immediately, regardless of strict mode.
        """
        from .metrics import METRIC_REGISTRY

        # Use method argument if provided, otherwise fall back to instance setting
        strict = strict if strict is not None else self.strict

        if not isinstance(data, pd.DataFrame):
            raise ValueError("Data must be a pandas DataFrame")

        results = []
        for ctrl in self.policy.controls:
            if not self._control_matches_phase(ctrl, phase):
                continue
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
                    if var in data.columns:
                        actual_col = var
                    else:
                        for cand in COLUMN_SYNONYMS.get(var, []) + COLUMN_SYNONYMS.get(
                            role, []
                        ):
                            if cand in data.columns:
                                actual_col = cand
                                break

                if not actual_col:
                    # Fallback: Treat as MISSING if not found in columns
                    actual_col = "MISSING"

                eval_context[role] = actual_col
                print(
                    f"    [Binding] Virtual Role '{role}' bound to Variable '{var}' (Column: '{actual_col}')"
                )

            # The statistical unit (`input.cluster`, e.g. patient_id) is an
            # OPTIONAL binding used only by power-stats — never a hard metric
            # requirement. If it can't be resolved to a real column, drop it so
            # it neither fails reconciliation nor is passed to the metric.
            if eval_context.get("cluster") == "MISSING":
                eval_context.pop("cluster", None)

            # If any virtual variables remain 'MISSING' after auto-binding, consider this a reconciliation failure.
            # `cluster` is excluded above (optional power-stats input).
            unresolved = [
                r
                for r in ctrl.input_mapping.keys()
                if r != "cluster" and eval_context.get(r) == "MISSING"
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
                resolved_params = {}
                for k, v in params.items():
                    if k in ("quasi_identifiers", "sensitive_columns"):
                        resolved = resolve_col_names(v, data, COLUMN_SYNONYMS)
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
                # Merge profile metadata (policy-level) with metric function metadata
                # (computation-level). Profile properties carry through to AR as facets.
                combined_metadata = dict(ctrl.metadata or {})
                combined_metadata.update(meta_data or {})

                # Statistical reliability of `metric_value`: a percentile
                # bootstrap CI over the SAME in-memory df, recomputing the SAME
                # calc_fn (cheap, no retraining). Online — never persists a CSV.
                power = self._compute_power(
                    data=data,
                    calc_fn=calc_fn,
                    eval_context=eval_context,
                    resolved_params=resolved_params,
                    metric_value=metric_value,
                )

                result = ComplianceResult(
                    control_id=ctrl.id,
                    description=ctrl.description,
                    metric_key=metric_key,
                    threshold=ctrl.threshold,
                    actual_value=metric_value,
                    operator=ctrl.operator,
                    passed=passed,
                    severity=ctrl.severity,
                    metadata=combined_metadata,
                    power=power,
                )
                results.append(result)
                self._apply_enforcement_mode(ctrl, result)
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

    @staticmethod
    def _compute_power(
        data: pd.DataFrame,
        calc_fn,
        eval_context: Dict[str, Any],
        resolved_params: Dict[str, Any],
        metric_value: Any,
    ) -> dict:
        """Compute the percentile-bootstrap power-stats for one control.

        Reuses the exact call shape of the enforce loop
        (``calc_fn(df, **eval_context, **resolved_params)``) so the bootstrap
        measures the same statistic. The statistical unit (``cluster``) and the
        subgroup column (``dimension``) are read from the resolved binding;
        ``cluster`` drives a cluster bootstrap (resample whole units), otherwise
        a row bootstrap is used.

        Escape hatch: ``VENTURALITICA_POWER=0`` skips the computation entirely
        and leaves ``power={}``. Any failure is swallowed (power is additive
        evidence; it must never break a gate).
        """
        import os

        if os.getenv("VENTURALITICA_POWER") == "0":
            return {}

        try:
            from .assurance.power import DEFAULT_SEED, compute_power

            # The kwargs the metric was actually called with.
            metric_kwargs = {**eval_context, **resolved_params}

            # `dimension`/`cluster` are resolved column names in the binding.
            dimension = metric_kwargs.get("dimension")
            cluster = metric_kwargs.get("cluster")

            # Power-only knobs may be declared as control params; pop them so
            # they never reach the metric callable.
            n_boot_raw = metric_kwargs.pop("power_n_boot", None)
            ci_level_raw = metric_kwargs.pop("power_ci_level", None)
            seed_raw = metric_kwargs.pop("power_seed", metric_kwargs.pop("seed", None))

            kwargs = {
                "n_boot": int(n_boot_raw) if n_boot_raw is not None else 1000,
                "ci_level": float(ci_level_raw) if ci_level_raw is not None else 0.95,
                "seed": int(seed_raw) if seed_raw is not None else DEFAULT_SEED,
            }

            return compute_power(
                data,
                calc_fn,
                metric_kwargs,
                value=metric_value,
                cluster=cluster,
                dimension=dimension,
                **kwargs,
            )
        except Exception as e:  # pragma: no cover - defensive
            print(f"    [Power] skipped (computation failed): {e}")
            return {}

    def evaluate(
        self,
        metrics: Dict[str, float],
        phase: Optional[str] = None,
        strict: bool = False,
    ) -> List[ComplianceResult]:
        """Evaluates pre-computed metrics against controls.

        Filters by `lifecycle_phase` when `phase` is provided. Controls declaring
        `enforcement_mode: block` that fail raise ComplianceBlockError, which is
        caught and logged when `strict=False` so the rest of the policy continues
        to be evaluated — mirroring `compute_and_evaluate(data=)` behavior so
        both entry points behave identically.

        Set `strict=True` to fail-fast on the first `block`-mode violation.
        """
        results = []
        for ctrl in self.policy.controls:
            if not self._control_matches_phase(ctrl, phase):
                continue
            actual = metrics.get(ctrl.metric_key)
            if actual is None:
                continue

            try:
                passed = self._check_condition(actual, ctrl.operator, ctrl.threshold)
                result = ComplianceResult(
                    control_id=ctrl.id,
                    description=ctrl.description,
                    metric_key=ctrl.metric_key,
                    threshold=ctrl.threshold,
                    actual_value=actual,
                    operator=ctrl.operator,
                    passed=passed,
                    severity=ctrl.severity,
                    metadata=dict(ctrl.metadata or {}),
                )
                results.append(result)
                self._apply_enforcement_mode(ctrl, result)
            except ComplianceBlockError:
                # Already recorded above; surface only in strict mode so the
                # caller can fail-fast. Default behaviour collects every result.
                if strict:
                    raise
                continue
            except (ValueError, TypeError, KeyError) as e:
                if strict:
                    raise
                print(f"    [Skip] Control '{ctrl.id}' ({ctrl.metric_key}) skipped: {e}")
                continue
            except Exception as e:
                if strict:
                    raise
                print(f"⚠ [Venturalitica] Error evaluating {ctrl.metric_key}: {e}")
                continue
        return results

    @staticmethod
    def _control_matches_phase(ctrl, phase: Optional[str]) -> bool:
        """Filters controls by lifecycle_phase.

        A control may declare `lifecycle_phase` as a single string or a list
        of strings (when it applies to multiple phases, e.g., both training
        and validation).

        - If `phase` is None: the SDK evaluates all controls except those
          tagged *exclusively* for the runtime proxy (`monitoring`) or the
          incident handler (`incident`). A control tagged with both `training`
          and `monitoring` is still evaluated by the SDK in its training phase.
        - If `phase` is specified: only controls whose phases include it
          (or untagged controls) are evaluated.
        """
        raw = (ctrl.metadata or {}).get("lifecycle_phase")
        if raw is None:
            phases: list = []
        elif isinstance(raw, list):
            phases = list(raw)
        else:
            phases = [raw]

        if phase is None:
            # Skip only when the control targets proxy/incident exclusively.
            if not phases:
                return True
            proxy_only = {"monitoring", "incident"}
            return any(p not in proxy_only for p in phases)

        if not phases:
            return True
        return phase in phases

    @staticmethod
    def _apply_enforcement_mode(ctrl, result: ComplianceResult) -> None:
        """Reacts to a ComplianceResult according to the control's enforcement_mode.

        - `block`: raises ComplianceBlockError on failure, halting the pipeline.
        - `warn`: emits a stderr alert on failure; execution continues.
        - `monitor` (default): silent.
        """
        if result.passed:
            return
        mode = (ctrl.metadata or {}).get("enforcement_mode", "monitor")
        if mode == "block":
            raise ComplianceBlockError(
                f"Control '{ctrl.id}' failed with enforcement_mode=block: "
                f"{result.metric_key}={result.actual_value} "
                f"does not satisfy {result.operator} {result.threshold}"
            )
        if mode == "warn":
            import sys
            print(
                f"⚠ [Venturalitica] Control '{ctrl.id}' failed "
                f"(enforcement_mode=warn): {result.metric_key}="
                f"{result.actual_value} {result.operator} {result.threshold}",
                file=sys.stderr,
            )

    def _check_condition(self, actual: float, operator: str, threshold: float) -> bool:
        """Helper to evaluate logical operators."""
        ops = {
            "<": lambda a, b: a < b,
            "lt": lambda a, b: a < b,
            ">": lambda a, b: a > b,
            "gt": lambda a, b: a > b,
            "<=": lambda a, b: a <= b,
            "le": lambda a, b: a <= b,
            "lte": lambda a, b: a <= b,
            ">=": lambda a, b: a >= b,
            "ge": lambda a, b: a >= b,
            "gte": lambda a, b: a >= b,
            "==": lambda a, b: a == b,
            "eq": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            "ne": lambda a, b: a != b,
        }
        return ops.get(operator, lambda a, b: False)(actual, threshold)
