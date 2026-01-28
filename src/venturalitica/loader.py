import yaml
import uuid
from pathlib import Path
from typing import Union, List, Dict, Any, Optional
from .models import InternalPolicy, InternalControl

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
                raise FileNotFoundError(f"OSCAL policy not found at: {self.policy_path}")

    def load(self) -> InternalPolicy:
        """Loads and parses the OSCAL policy from file or dict into a standardized InternalPolicy."""
        if self.policy_dict is not None:
            # Use in-memory dict
            data = self.policy_dict
        else:
            # Load from file
            with open(self.policy_path, 'r') as f:
                data = yaml.safe_load(f) or {}

        # Determine root object
        root_key = next((k for k in ['assessment-plan', 'catalog', 'profile', 'component-definition'] if k in data), None)
        
        if root_key:
            return self._parse_generic_oscal(data[root_key])
        elif isinstance(data, list):
            return self._parse_flat_list(data)
        else:
            raise ValueError("Unsupported OSCAL format or missing root element (assessment-plan, catalog, etc.)")

    def _parse_generic_oscal(self, obj: Dict[str, Any]) -> InternalPolicy:
        """A generic, permissive parser that looks for controls and implementations in any OSCAL object."""
        title = obj.get('metadata', {}).get('title', self.policy_path.stem if self.policy_path else "Embedded Policy")
        policy = InternalPolicy(title=title)
        
        # 1. Build Inventory of Metrics (from local-definitions or root)
        inventory = {}
        # Try finding inventory-items in local-definitions or at the root of the object
        local_defs = obj.get('local-definitions', {})
        items = local_defs.get('inventory-items', []) if isinstance(local_defs, dict) else []
        if not items:
            items = obj.get('inventory-items', []) # Hybrid format
            
        for item in items:
            item_uuid = item.get('uuid')
            if not item_uuid: continue
            props = {p['name']: p['value'] for p in item.get('props', []) if 'name' in p and 'value' in p}
            inventory[item_uuid] = props
        
        # 2. Process Control Implementations (handles both standard and simplified locations)
        control_impls = []
        # Standard location for Assessment Plan
        reviewed = obj.get('reviewed-controls', {})
        if isinstance(reviewed, dict):
             control_impls.extend(reviewed.get('control-implementations', []))
        
        # Root location (hybrid or simplified)
        root_impls = obj.get('control-implementations', [])
        if isinstance(root_impls, list):
            control_impls.extend(root_impls)

        for impl in control_impls:
            for req in impl.get('implemented-requirements', []):
                self._add_to_policy(policy, req, inventory)
                
        # 3. Process Controls directly (for Catalogs without explicit implementations)
        raw_controls = obj.get('controls', [])
        if isinstance(raw_controls, list):
            for control in raw_controls:
                self._process_catalog_recursive(control, policy)
        
        return policy

    def _add_to_policy(self, policy: InternalPolicy, req: Dict[str, Any], inventory: Dict[str, Any]):
        """Helper to map a requirement and its links to the internal policy."""
        control_id = req.get('control-id')
        description = req.get('description', '')
        
        # Extract severity and check for direct metric props
        severity = "low"
        direct_props = {}
        for p in req.get('props', []):
            name = p.get('name')
            value = p.get('value')
            if name == 'severity':
                severity = value
            elif name in ['metric_key', 'threshold', 'operator']:
                direct_props[name] = value
            elif name.startswith("input:"):
                role = name.split(":", 1)[1]
                if "input_mapping" not in direct_props:
                    direct_props["input_mapping"] = {}
                direct_props["input_mapping"][role] = value
                
                if "required_vars" not in direct_props:
                    direct_props["required_vars"] = []
                direct_props["required_vars"].append(value)
        
        # 1. Direct props support (Simplified OSCAL)
        if "metric_key" in direct_props:
            policy.controls.append(InternalControl(
                id=control_id,
                description=description or f"Control {control_id}",
                severity=severity,
                metric_key=direct_props["metric_key"],
                threshold=float(direct_props.get("threshold", 0.0)),
                operator=direct_props.get("operator", "=="),
                required_vars=direct_props.get("required_vars", []),
                input_mapping=direct_props.get("input_mapping", {})
            ))
            return # Skip link hunting if we have direct props

        # 2. Link hunting (Standard OSCAL)
        for link in req.get('links', []):
            href = link.get('href', '')
            if href.startswith("#"):
                metric_uuid = href[1:]
                if metric_uuid in inventory:
                    m_def = inventory[metric_uuid]
                    if "metric_key" in m_def:
                        policy.controls.append(InternalControl(
                            id=control_id,
                            description=description or f"Control {control_id}",
                            severity=severity,
                            metric_key=m_def["metric_key"],
                            threshold=float(m_def.get("threshold", 0.0)),
                            operator=m_def.get("operator", "=="),
                            required_vars=[v for k, v in m_def.items() if k.startswith("input:")],
                            input_mapping={k.split(":", 1)[1]: v for k, v in m_def.items() if k.startswith("input:")}
                        ))

    def _process_catalog_recursive(self, control: Dict[str, Any], policy: InternalPolicy):
        """Recursively processes catalog controls looking for metric properties."""
        props = {p['name']: p['value'] for p in control.get('props', []) if 'name' in p and 'value' in p}
        
        if "metric_key" in props:
            policy.controls.append(InternalControl(
                id=control.get('id', 'unknown'),
                description=control.get('title', control.get('id', '')),
                severity=props.get("severity", "low"),
                metric_key=props["metric_key"],
                threshold=float(props.get("threshold", 0.0)),
                operator=props.get("operator", "=="),
                required_vars=[v for k, v in props.items() if k.startswith("input:")],
                input_mapping={k.split(":", 1)[1]: v for k, v in props.items() if k.startswith("input:")}
            ))
            
        for sub in control.get('controls', []):
            self._process_catalog_recursive(sub, policy)

    def _parse_flat_list(self, data: List[Dict[str, Any]]) -> InternalPolicy:
        """Emergency fallback for extremely simplified YAML lists."""
        policy = InternalPolicy(title="Flat Policy")
        for item in data:
            if all(k in item for k in ['id', 'metric_key', 'threshold', 'operator']):
                policy.controls.append(InternalControl(
                    id=item['id'],
                    description=item.get('description', ''),
                    severity=item.get('severity', 'low'),
                    metric_key=item['metric_key'],
                    threshold=float(item['threshold']),
                    operator=item['operator']
                ))
        return policy
