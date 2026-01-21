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

@dataclass
class InternalPolicy:
    """Standardized representation of a governance policy."""
    title: str
    controls: List[InternalControl] = field(default_factory=list)
