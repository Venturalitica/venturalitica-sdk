from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class InternalControl:
    """Standardized representation of a assurance control."""
    id: str
    description: str
    severity: str
    metric_key: str
    threshold: float
    operator: str
    metadata: Dict[str, Any] = None
    input_mapping: dict = field(default_factory=dict) # Role -> VirtualVarName
    params: dict = field(default_factory=dict)  # Additional params for metric functions (e.g., quasi_identifiers)

@dataclass
class InternalPolicy:
    """Standardized representation of a assurance policy."""
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

@dataclass
class SystemDescription:
    """Representation of Annex IV.1 System Description (Model Card)."""
    # (a) General Description
    name: str = ""
    version: str = ""
    provider_name: str = ""
    intended_purpose: str = ""
    
    # (b) Interaction
    interaction_description: str = "" # Software/Hardware interaction
    
    # (c) Dependencies
    software_dependencies: str = "" # Versions of relevant software
    
    # (d) Market Form
    market_placement_form: str = "" # API, Download, Embedded?
    
    # (e) Hardware
    hardware_description: str = ""
    
    # (f) External Features
    external_features: str = "" # Photos, markings, layout
    
    # (g) UI Description
    ui_description: str = ""
    
    # (h) Instructions
    # (h) Instructions
    instructions_for_use: str = ""
    
    # ZenStack Alignment
    potential_misuses: str = "" # Foreseeable misuse (Art 15)

    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "version": self.version,
            "provider_name": self.provider_name,
            "intended_purpose": self.intended_purpose,
            "interaction_description": self.interaction_description,
            "software_dependencies": self.software_dependencies,
            "market_placement_form": self.market_placement_form,
            "hardware_description": self.hardware_description,
            "external_features": self.external_features,
            "ui_description": self.ui_description,
            "instructions_for_use": self.instructions_for_use,
            "potential_misuses": self.potential_misuses
        }

@dataclass
class TechnicalDocumentation:
    """Representation of Annex IV.2 Technical Documentation."""
    # (a) Development
    development_methods: List[str] = field(default_factory=list)
    
    # (b) Logic
    logic_description: str = ""
    
    # (c) Architecture
    architecture_diagram: str = "" # Mermaid code
    
    # (d) Data
    data_provenance: Dict[str, Any] = field(default_factory=dict) # {sources: [], cleaning: ""}
    
    # (e) Oversight
    human_oversight_measures: List[str] = field(default_factory=list)
    
    # (f) Changes
    predetermined_changes: str = ""
    
    # (g) Validation
    validation_procedures: str = ""
    
    # (h) Cybersecurity
    cybersecurity_measures: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "development_methods": self.development_methods,
            "logic_description": self.logic_description,
            "architecture_diagram": self.architecture_diagram,
            "data_provenance": self.data_provenance,
            "human_oversight_measures": self.human_oversight_measures,
            "predetermined_changes": self.predetermined_changes,
            "validation_procedures": self.validation_procedures,
            "cybersecurity_measures": self.cybersecurity_measures
        }
@dataclass
class RiskAssessment:
    """Representation of EU AI Act Risk Classification."""
    risk_level: str = "UNKNOWN" # PROHIBITED, HIGH_RISK, TRANSPARENCY_ONLY, MINIMAL
    reasoning: str = ""
    applicable_articles: List[str] = field(default_factory=list)
    flags: List[str] = field(default_factory=list) # e.g. "Biometric", "Critical Infrastructure"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_level": self.risk_level,
            "reasoning": self.reasoning,
            "applicable_articles": self.applicable_articles,
            "flags": self.flags
        }
