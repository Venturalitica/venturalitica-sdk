from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class InternalControl:
    """Standardized representation of a governance control."""
    id: str
    description: str
    severity: str
    metric_key: str
    threshold: float
    operator: str
    required_vars: List[str] = field(default_factory=list)
    input_mapping: dict = field(default_factory=dict) # Role -> VirtualVarName
    params: dict = field(default_factory=dict)  # Additional params for metric functions (e.g., quasi_identifiers)

@dataclass
class InternalPolicy:
    """Standardized representation of a governance policy."""
    title: str
    controls: List[InternalControl] = field(default_factory=list)

@dataclass
class ComplianceResult:
    """The result of evaluating a single control."""
    control_id: str
    description: str
    metric_key: str
    threshold: float
    actual_value: float
    operator: str
    passed: bool
    severity: str
    metadata: dict = field(default_factory=dict)
