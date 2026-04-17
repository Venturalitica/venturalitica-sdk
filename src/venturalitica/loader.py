from pathlib import Path
from typing import Any, Dict, List, Union

import yaml

from .models import InternalControl, InternalPolicy

# Proposed OSCAL profile properties for AI Assurance (paper Table 2, 16 properties).
# When present in a policy YAML, these are preserved as profile metadata and
# propagated to Assessment Results as CharacterizationFacets.
PROFILE_PROPERTY_NAMES = frozenset({
    # Lifecycle semantics
    "lifecycle_phase", "enforcement_mode", "evaluation_method",
    "evaluation_window", "target_type",
    # Traceability chain
    "risk_id", "treatment_id", "policy_id", "objective_id",
    # Risk-acceptance and justification (Gealy, SaferAI)
    "risk_acceptance_criteria", "threshold_justification",
    # Stakeholder deliberation (Panai, Association of AI Ethicists)
    "stakeholder_consultation_ref",
})


class OSCALPolicyLoader:
    def __init__(self, policy_source: Union[str, Path, Dict[str, Any]]):
        """Initialize loader with either a file path or an in-memory dict."""
        if isinstance(policy_source, dict):
            self.policy_dict = policy_source
            self.policy_path = None
        else:
            self.policy_path = Path(policy_source)
            self.policy_dict = None
            if not self.policy_path.exists():
                raise FileNotFoundError(
                    f"OSCAL policy not found at: {self.policy_path}"
                )

    def load(self) -> InternalPolicy:
        """Loads and parses the OSCAL policy from file or dict into a standardized InternalPolicy."""
        if self.policy_dict is not None:
            # Use in-memory dict
            data = self.policy_dict
        else:
            # Load from file
            with open(self.policy_path, "r") as f:
                data = yaml.safe_load(f) or {}

        # Determine root object
        root_key = next(
            (
                k
                for k in [
                    "assessment-plan",
                    "catalog",
                    "profile",
                    "component-definition",
                    "system-security-plan",
                ]
                if k in data
            ),
            None,
        )

        if root_key:
            return self._parse_generic_oscal(data[root_key])
        elif isinstance(data, list):
            return self._parse_flat_list(data)
        else:
            raise ValueError(
                "Unsupported OSCAL format or missing root element (system-security-plan, assessment-plan, catalog, etc.)"
            )

    def _parse_generic_oscal(self, obj: Dict[str, Any]) -> InternalPolicy:
        """A generic, permissive parser that looks for controls and implementations in any OSCAL object."""
        title = obj.get("metadata", {}).get(
            "title", self.policy_path.stem if self.policy_path else "Embedded Policy"
        )
        policy = InternalPolicy(title=title)

        # 1. Build Inventory of Metrics (from local-definitions or root)
        inventory = {}
        # Try finding inventory-items in local-definitions or at the root of the object
        local_defs = obj.get("local-definitions", {})
        items = (
            local_defs.get("inventory-items", [])
            if isinstance(local_defs, dict)
            else []
        )
        if not items:
            items = obj.get("inventory-items", [])  # Hybrid format

        for item in items:
            item_uuid = item.get("uuid")
            if not item_uuid:
                continue
            props = {
                p["name"]: p["value"]
                for p in item.get("props", [])
                if "name" in p and "value" in p
            }
            inventory[item_uuid] = props

        # 2. Process Control Implementations (handles both standard and simplified locations)
        control_impls = []
        # Standard location for Assessment Plan
        reviewed = obj.get("reviewed-controls", {})
        if isinstance(reviewed, dict):
            control_impls.extend(reviewed.get("control-implementations", []))

        # Root location (hybrid or simplified)
        root_impls = obj.get("control-implementations", [])
        if isinstance(root_impls, list):
            control_impls.extend(root_impls)

        # [ISO 23894] Singular support for System Security Plan
        singular_impl = obj.get("control-implementation", {})
        if isinstance(singular_impl, dict):
            control_impls.append(singular_impl)

        for impl in control_impls:
            for req in impl.get("implemented-requirements", []):
                self._add_to_policy(policy, req, inventory)

        # 3. Process Controls directly (for Catalogs without explicit implementations)
        raw_controls = obj.get("controls", [])
        if isinstance(raw_controls, list):
            for control in raw_controls:
                self._process_catalog_recursive(control, policy)

        return policy

    def _add_to_policy(
        self, policy: InternalPolicy, req: Dict[str, Any], inventory: Dict[str, Any]
    ):
        """Helper to map a requirement and its links to the internal policy."""
        control_id = req.get("control-id") or req.get("uuid", "unknown")
        description = req.get("description", "")

        # Extract severity and check for direct metric props
        severity = "low"
        direct_props = {}
        metadata: Dict[str, Any] = {}
        for p in req.get("props", []):
            name = p.get("name")
            value = p.get("value")
            if name == "severity":
                severity = value
                metadata[name] = value
            elif name in ["metric_key", "metric", "threshold", "operator"]:
                # Map 'metric' to 'metric_key' for compatibility
                key = "metric_key" if name == "metric" else name
                direct_props[key] = value
            elif name.startswith("input:"):
                role = name.split(":", 1)[1]
                if "input_mapping" not in direct_props:
                    direct_props["input_mapping"] = {}
                direct_props["input_mapping"][role] = value

                if "required_vars" not in direct_props:
                    direct_props["required_vars"] = []
                direct_props["required_vars"].append(value)
            elif name in PROFILE_PROPERTY_NAMES:
                # Profile metadata: carried to Assessment Results for auditor visibility.
                # A single control MAY declare `lifecycle_phase` multiple times to
                # indicate that the control applies in several phases (e.g.,
                # `training` and `validation`). Collect repeated phases into a list.
                if name == "lifecycle_phase":
                    existing = metadata.get("lifecycle_phase")
                    if existing is None:
                        metadata["lifecycle_phase"] = value
                    elif isinstance(existing, list):
                        existing.append(value)
                    else:
                        metadata["lifecycle_phase"] = [existing, value]
                else:
                    metadata[name] = value
            else:
                # Generic parameters for metric functions (e.g., quasi_identifiers)
                if "params" not in direct_props:
                    direct_props["params"] = {}
                direct_props["params"][name] = value

        # 1. Direct props support (Simplified OSCAL)
        if "metric_key" in direct_props:
            policy.controls.append(
                InternalControl(
                    id=control_id,
                    description=description or f"Control {control_id}",
                    severity=severity,
                    metric_key=direct_props["metric_key"],
                    threshold=float(direct_props.get("threshold", 0.0)),
                    operator=direct_props.get("operator", "=="),
                    input_mapping=direct_props.get("input_mapping", {}),
                    params=direct_props.get("params", {}),
                    metadata=metadata,
                )
            )
            return  # Skip link hunting if we have direct props

        # Link hunting (Standard OSCAL - check explicit links that reference inventory items)
        for link in req.get("links", []):
            href = link.get("href", "")
            if href.startswith("#"):
                metric_uuid = href[1:]
                if metric_uuid in inventory:
                    m_def = inventory[metric_uuid]
                    if "metric_key" in m_def:
                        # Separate profile metadata from function params
                        inventory_metadata = dict(metadata)
                        params = {}
                        for k, v in m_def.items():
                            if k.startswith("input:") or k in ("metric_key", "threshold", "operator"):
                                continue
                            if k in PROFILE_PROPERTY_NAMES or k == "severity":
                                inventory_metadata[k] = v
                            else:
                                params[k] = v
                        policy.controls.append(
                            InternalControl(
                                id=control_id,
                                description=description or f"Control {control_id}",
                                severity=severity,
                                metric_key=m_def["metric_key"],
                                threshold=float(m_def.get("threshold", 0.0)),
                                operator=m_def.get("operator", "=="),
                                input_mapping={
                                    k.split(":", 1)[1]: v
                                    for k, v in m_def.items()
                                    if k.startswith("input:")
                                },
                                params=params,
                                metadata=inventory_metadata,
                            )
                        )

    def _process_catalog_recursive(
        self, control: Dict[str, Any], policy: InternalPolicy
    ):
        """Recursively processes catalog controls looking for metric properties."""
        props = {
            p["name"]: p["value"]
            for p in control.get("props", [])
            if "name" in p and "value" in p
        }

        if "metric_key" in props:
            # Separate profile metadata from function params
            catalog_metadata: Dict[str, Any] = {}
            params: Dict[str, Any] = {}
            for k, v in props.items():
                if k.startswith("input:") or k in ("metric_key", "threshold", "operator"):
                    continue
                if k in PROFILE_PROPERTY_NAMES or k == "severity":
                    catalog_metadata[k] = v
                else:
                    params[k] = v
            policy.controls.append(
                InternalControl(
                    id=control.get("id", "unknown"),
                    description=control.get("title", control.get("id", "")),
                    severity=props.get("severity", "low"),
                    metric_key=props["metric_key"],
                    threshold=float(props.get("threshold", 0.0)),
                    operator=props.get("operator", "=="),
                    input_mapping={
                        k.split(":", 1)[1]: v
                        for k, v in props.items()
                        if k.startswith("input:")
                    },
                    params=params,
                    metadata=catalog_metadata,
                )
            )

        for sub in control.get("controls", []):
            self._process_catalog_recursive(sub, policy)

    def _parse_flat_list(self, data: List[Dict[str, Any]]) -> InternalPolicy:
        """Emergency fallback for extremely simplified YAML lists."""
        policy = InternalPolicy(title="Flat Policy")
        for item in data:
            if all(k in item for k in ["id", "metric_key", "threshold", "operator"]):
                policy.controls.append(
                    InternalControl(
                        id=item["id"],
                        description=item.get("description", ""),
                        severity=item.get("severity", "low"),
                        metric_key=item["metric_key"],
                        threshold=float(item["threshold"]),
                        operator=item["operator"],
                    )
                )
        return policy
