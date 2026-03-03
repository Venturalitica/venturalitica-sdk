from pathlib import Path
from typing import Any, Dict, List

import yaml

POLICY_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Venturalitica Simplified OSCAL Policy",
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "uuid": {"type": "string"},
        "controls": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "metric_key", "operator", "threshold"],
                "properties": {
                    "id": {"type": "string"},
                    "metric_key": {"type": "string"},
                    "operator": {"enum": [">", ">=", "<", "<=", "=="]},
                    "threshold": {"type": "number"},
                    "severity": {"enum": ["low", "medium", "high", "critical"]},
                    "description": {"type": "string"}
                }
            }
        }
    },
    "required": ["title", "controls"]
}

class PolicyManager:
    """
    Decoupled engine for managing OSCAL policies.
    Handles loading, saving, and schema validation.
    """
    
    def __init__(self, target_dir: str):
        self.target_dir = Path(target_dir)
        self.policy_path = self.target_dir / "model_policy.oscal.yaml"

    def load(self) -> Dict[str, Any]:
        """Loads and returns the policy as a dict."""
        if self.policy_path.exists():
            with open(self.policy_path, "r") as f:
                data = yaml.safe_load(f) or {}
                # Handle potential list-only legacy format
                if isinstance(data, list):
                    data = {"title": "Legacy Policy", "controls": data}
                return data
        return {"title": "New Policy", "controls": []}

    def save(self, data: Dict[str, Any]) -> bool:
        """Validates and saves the policy to YAML."""
        # Simple internal validation (could use jsonschema library if installed)
        if not data.get("title"):
            raise ValueError("Policy title is required")
            
        with open(self.policy_path, "w") as f:
            yaml.dump(data, f, sort_keys=False)
        return True

    def validate(self, data: Dict[str, Any]) -> List[str]:
        """
        Validates the policy against the schema.
        Returns a list of error messages (empty if valid).
        """
        errors = []
        if "title" not in data:
            errors.append("Missing 'title'")
        if "controls" not in data or not isinstance(data["controls"], list):
            errors.append("Missing or invalid 'controls' list")
        else:
            for i, ctrl in enumerate(data["controls"]):
                for field in ["id", "metric_key", "operator", "threshold"]:
                    if field not in ctrl:
                        errors.append(f"Control {i} ({ctrl.get('id', 'unknown')}) missing required field: {field}")
        return errors

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        return POLICY_SCHEMA
