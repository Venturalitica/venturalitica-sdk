import yaml
import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class ComplianceResult:
    control_id: str
    description: str
    metric_key: str
    threshold: float
    actual_value: float
    operator: str
    passed: bool
    severity: str

class GovernanceValidator:
    def __init__(self, policy_path: str):
        self.policy_path = Path(policy_path)
        self.controls = []
        self._load_policy()

    def _load_policy(self):
        """Loads and parses the OSCAL policy file."""
        if not self.policy_path.exists():
            raise FileNotFoundError(f"OSCAL policy not found at: {self.policy_path}")
            
        with open(self.policy_path, 'r') as f:
            self.oscal_data = yaml.safe_load(f) or {}
            
        inventory = self._parse_local_definitions()
        self._parse_control_implementations(inventory)

    def _parse_local_definitions(self) -> Dict[str, Dict[str, str]]:
        """Parses inventory items from local-definitions."""
        inventory = {}
        assessment_plan = self.oscal_data.get('assessment-plan', {})
        local_defs = assessment_plan.get('local-definitions', {})
        items = local_defs.get('inventory-items', [])
        
        for item in items:
            uuid = item.get('uuid')
            if not uuid:
                continue
            metric_def = {p['name']: p['value'] for p in item.get('props', []) if 'name' in p and 'value' in p}
            inventory[uuid] = metric_def
        return inventory

    def _parse_control_implementations(self, inventory: Dict[str, Dict[str, str]]):
        """Parses control implementations and links them to metrics."""
        assessment_plan = self.oscal_data.get('assessment-plan', {})
        impls = assessment_plan.get('control-implementations', [])
        
        for impl in impls:
            for req in impl.get('implemented-requirements', []):
                self._process_requirement(req, inventory)

    def _process_requirement(self, req: Dict[str, Any], inventory: Dict[str, Dict[str, str]]):
        """Processes a single requirement and its links to metrics."""
        control_id = req.get('control-id')
        description = req.get('description', '')
        severity = next((p['value'] for p in req.get('props', []) if p.get('name') == 'severity'), 'low')
        
        for link in req.get('links', []):
            href = link.get('href', '')
            if href.startswith('#'):
                metric_uuid = href[1:]
                if metric_uuid in inventory:
                    self._add_control(control_id, description, severity, inventory[metric_uuid])
            else:
                # Coverage hit for non-anchor links
                pass

    def _add_control(self, control_id: str, description: str, severity: str, metric_def: Dict[str, str]):
        """Adds a control to the validator if it contains valid metric data."""
        try:
            control = {
                'id': control_id,
                'description': description,
                'severity': severity,
                'metric_key': metric_def['metric_key'],
                'threshold': float(metric_def['threshold']),
                'operator': metric_def['operator']
            }
            self.controls.append(control)
        except (KeyError, ValueError, TypeError):
            # Skip malformed metric definitions
            pass

    def compute_and_evaluate(self, data: pd.DataFrame, context_mapping: Dict[str, str]) -> List[ComplianceResult]:
        """Computes metrics and evaluates them against controls."""
        from .metrics import METRIC_REGISTRY
        
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Data must be a pandas DataFrame")

        results = []
        for ctrl in self.controls:
            metric_key = ctrl['metric_key']
            calc_fn = METRIC_REGISTRY.get(metric_key)
            
            if not calc_fn:
                continue
                
            try:
                actual = calc_fn(data, **context_mapping)
                passed = self._check_condition(actual, ctrl['operator'], ctrl['threshold'])
                
                results.append(ComplianceResult(
                    control_id=ctrl['id'],
                    description=ctrl['description'],
                    metric_key=metric_key,
                    threshold=ctrl['threshold'],
                    actual_value=actual,
                    operator=ctrl['operator'],
                    passed=passed,
                    severity=ctrl['severity']
                ))
            except (ValueError, TypeError):
                # Expected if columns are missing for a specific metric
                continue
            except Exception as e:
                print(f"⚠ [Venturalitica] Unexpected error evaluating {metric_key}: {e}")
                
        return results

    def evaluate(self, metrics: Dict[str, float]) -> List[ComplianceResult]:
        """Evaluates pre-computed metrics against controls."""
        results = []
        for ctrl in self.controls:
            actual = metrics.get(ctrl['metric_key'])
            if actual is None:
                continue
                
            passed = self._check_condition(actual, ctrl['operator'], ctrl['threshold'])
            results.append(ComplianceResult(
                control_id=ctrl['id'],
                description=ctrl['description'],
                metric_key=ctrl['metric_key'],
                threshold=ctrl['threshold'],
                actual_value=actual,
                operator=ctrl['operator'],
                passed=passed,
                severity=ctrl['severity']
            ))
        return results

    def _check_condition(self, actual: float, operator: str, threshold: float) -> bool:
        """Helper to evaluate logical operators."""
        ops = {
            '<': lambda a, b: a < b,
            '>': lambda a, b: a > b,
            '<=': lambda a, b: a <= b,
            '>=': lambda a, b: a >= b,
            '==': lambda a, b: a == b,
            '!=': lambda a, b: a != b
        }
        return ops.get(operator, lambda a, b: False)(actual, threshold)
