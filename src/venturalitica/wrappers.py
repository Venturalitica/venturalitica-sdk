import functools
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional, Union
from pathlib import Path

class GovernanceWrapper:
    """
    A transparency proxy for ML models that automatically triggers
    Venturalítica audits on key lifecycle methods (fit, predict).
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

    def __call__(self, *args, **kwargs):
        # Forward execution to the model (essential for PyTorch nn.Module)
        return self._venturalitica_model(*args, **kwargs)

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
                    
                    
                    # [PLG] Runtime Provenance Capture
                    try:
                        self._save_run_metadata(data, model_kwargs)
                    except Exception as e:
                        print(f"⚠ Failed to save run metadata: {e}")

                    # [GOVERNANCE] Regulatory Versioning: Upload Policy Artifacts
                    try:
                        self._upload_policy_artifacts()
                    except Exception as e:
                        print(f"⚠ Regulatory Versioning Warning: {e}")

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

    def _save_run_metadata(self, data, model_kwargs):
        """
        Captures runtime facts (provenance) for the Compliance Graph.
        """
        import pandas as pd
        
        meta = {
            "timestamp": datetime.now().isoformat(),
            "model": {
                "class": self._venturalitica_model.__class__.__name__,
                "module": self._venturalitica_model.__class__.__module__
            },
            "data": {
                "rows": len(data) if hasattr(data, "__len__") else 0,
                "columns": list(data.columns) if isinstance(data, pd.DataFrame) else []
            },
            "audit_results": [r.metric_key + ": " + ("PASS" if r.passed else "FAIL") for r in self.last_audit_results]
        }
        
        # Try to get hyperparameters
        if hasattr(self._venturalitica_model, "get_params"):
             meta["model"]["params"] = self._venturalitica_model.get_params()
             
        # [NEW] Capture Code Story via AST
        try:
            import inspect
            from .graph.parser import ASTCodeScanner
            
            # Find the calling frame to get the script path
            frame = inspect.currentframe()
            # Go up until we find something not in venturalitica
            while frame:
                module_name = frame.f_globals.get('__name__', '')
                if not module_name.startswith('venturalitica'):
                    break
                frame = frame.f_back
            
            if frame:
                script_path = frame.f_globals.get('__file__')
                if script_path and os.path.exists(script_path):
                    scanner = ASTCodeScanner()
                    meta["code_context"] = {
                        "file": os.path.basename(script_path),
                        "analysis": scanner.scan_file(script_path)
                    }
        except Exception as e:
            print(f"⚠ Trace Audit Warning: Could not capture AST: {e}")

        # [INTEGRATIONS] Capture Linkage
        try:
            import mlflow
            if mlflow.active_run():
                run = mlflow.active_run()
                meta["integrations"] = meta.get("integrations", {})
                meta["integrations"]["mlflow"] = {
                    "active": True,
                    "run_id": run.info.run_id,
                    "experiment_id": run.info.experiment_id,
                    "tracking_uri": mlflow.get_tracking_uri()
                }
        except: pass

        try:
            import wandb
            if wandb.run:
                meta["integrations"] = meta.get("integrations", {})
                meta["integrations"]["wandb"] = {
                    "active": True,
                    "run_url": wandb.run.url,
                    "project": wandb.run.project,
                    "entity": wandb.run.entity
                }
        except: pass

        # Save to disk
        os.makedirs(".venturalitica", exist_ok=True)
        with open(".venturalitica/latest_run.json", "w") as f:
            json.dump(meta, f, indent=2, default=str)

    def _upload_policy_artifacts(self):
        """
        [Regulatory Versioning] Uploads the actual OSCAL YAML files to active MLOps runs.
        Ensures compliance reproducibility.
        """
        if not self._venturalitica_policy:
            return

        # Normalize to list
        policies = self._venturalitica_policy
        if not isinstance(policies, list):
            policies = [policies]

        # 1. Detect MLflow
        try:
            import mlflow
            if mlflow.active_run():
                for p in policies:
                    p_path = Path(p)
                    if p_path.exists():
                        # Log as 'policy_snapshot' artifact
                        mlflow.log_artifact(str(p_path), artifact_path="policy_snapshot")
        except ImportError:
            pass
        except Exception as e:
            print(f"  (MLflow Artifact Upload Error: {e})")

        # 2. Detect WandB
        try:
            import wandb
            if wandb.run:
                artifact = wandb.Artifact("policy_snapshot", type="governance")
                for p in policies:
                    p_path = Path(p)
                    if p_path.exists():
                        artifact.add_file(str(p_path))
                wandb.log_artifact(artifact)
        except ImportError:
            pass
        except Exception as e:
            print(f"  (WandB Artifact Upload Error: {e})")

class TraceCollector:
    """
    Context manager to collect execution evidence for RAG-based compliance.
    """
    def __init__(self, name: str = "default_run"):
        self.name = name
        self.start_time = None
        self.metadata = {}

    def __enter__(self):
        self.start_time = datetime.now()
        print(f"🚀 TraceCollector [{self.name}] starting...")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import inspect
        from .graph.parser import ASTCodeScanner
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Capture context
        meta = {
            "name": self.name,
            "timestamp": end_time.isoformat(),
            "duration_seconds": duration,
            "success": exc_type is None
        }

        # AST Capture
        try:
            # The caller is the frame that entered/exited the context
            frame = inspect.currentframe().f_back
            script_path = frame.f_globals.get('__file__')
            if script_path and os.path.exists(script_path):
                scanner = ASTCodeScanner()
                meta["code_context"] = {
                    "file": os.path.basename(script_path),
                    "analysis": scanner.scan_file(script_path)
                }
        except Exception as e:
            print(f"⚠ TraceCollector Warning: {e}")

        os.makedirs(".venturalitica", exist_ok=True)
        path = f".venturalitica/trace_{self.name}.json"
        with open(path, "w") as f:
            json.dump(meta, f, indent=2, default=str)
        print(f"✅ TraceCollector [{self.name}] evidence saved to {path}")
        print(f"  💡 Run 'venturalitica ui' to visualize this execution trace.")

def tracecollector(name: str = "default_run") -> TraceCollector:
    """
    Helper to create a TraceCollector context manager.
    """
    return TraceCollector(name)

def wrap(model: Any, policy: Optional[Union[str, Path]] = None) -> GovernanceWrapper:
    """
    [EXPERIMENTAL] Transparently wraps an ML model with Venturalítica governance.
    Note: This is an experimental feature and may change or be removed in future versions.
    """
    import warnings
    warnings.warn(
        "vl.wrap is an experimental feature and its API may change in future versions.",
        UserWarning,
        stacklevel=2
    )
    return GovernanceWrapper(model, policy)
