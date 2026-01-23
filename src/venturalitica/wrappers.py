import functools
from typing import Any, Dict, Optional, Union
from pathlib import Path

class GovernanceWrapper:
    """
    A transparency proxy for ML models that automatically triggers
    Venturalitica audits on key lifecycle methods (fit, predict).
    """
    def __init__(self, model: Any, policy: Optional[Union[str, Path]] = None):
        self._venturalitica_model = model
        self._venturalitica_policy = policy
        self.last_audit_results = []
        
        # Intercept common ML methods
        self._wrap_method("fit")
        self._wrap_method("predict")
        self._wrap_method("predict_proba")

    def __getattr__(self, name):
        # Delegate everything else to the original model
        return getattr(self._venturalitica_model, name)

    def _wrap_method(self, method_name: str):
        if not hasattr(self._venturalitica_model, method_name):
            return

        original_method = getattr(self._venturalitica_model, method_name)

        @functools.wraps(original_method)
        def wrapped(*args, **kwargs):
            from . import enforce
            import inspect

            # 1. Use inspect to separate model kwargs from audit kwargs
            sig = inspect.signature(original_method)
            model_kwargs = {}
            audit_kwargs = {}

            # Always treat 'audit_data' as audit-only
            audit_data = kwargs.pop("audit_data", None)

            for k, v in kwargs.items():
                if k in sig.parameters or sig.parameters.get("kwargs"):
                    model_kwargs[k] = v
                else:
                    audit_kwargs[k] = v

            # Pre-execution: Fit usually implies a data audit
            if method_name == "fit":
                data = audit_data if audit_data is not None else self._find_dataframe(args, model_kwargs)
                if data is not None:
                    # Pass all audit-relevant mappings to enforce
                    self.last_audit_results = enforce(
                        data=data, 
                        policy=self._venturalitica_policy,
                        **audit_kwargs
                    )

            # Execute original logic (without audit-only kwargs)
            result = original_method(*args, **model_kwargs)

            # Post-execution: Predict implies a model fairness audit
            if method_name in ["predict", "predict_proba"]:
                data = audit_data if audit_data is not None else self._find_dataframe(args, model_kwargs)
                if data is not None:
                    # Inject prediction for the audit
                    data_with_pred = data.copy()
                    
                    # We need to know where to put the prediction. 
                    # Use 'prediction' key from audit_kwargs if present, else default
                    pred_col_name = audit_kwargs.get('prediction', 'prediction')
                    data_with_pred[pred_col_name] = result
                    
                    self.last_audit_results = enforce(
                        data=data_with_pred, 
                        policy=self._venturalitica_policy,
                        **audit_kwargs
                    )
            
            return result

        setattr(self, method_name, wrapped)

    def _find_dataframe(self, args, kwargs) -> Optional[Any]:
        # Simple heuristic to find a pandas DataFrame in the arguments
        import pandas as pd
        for arg in args:
            if isinstance(arg, pd.DataFrame):
                return arg
        for val in kwargs.values():
            if isinstance(val, pd.DataFrame):
                return val
        return None

def wrap(model: Any, policy: Optional[Union[str, Path]] = None) -> GovernanceWrapper:
    """
    Transparently wraps an ML model with Venturalitica governance.
    """
    return GovernanceWrapper(model, policy)
