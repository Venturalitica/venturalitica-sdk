"""OSCAL v1.1.2 data models for Assessment Results and Plan of Action & Milestones.

These models represent the subset of OSCAL needed to serialize AI Assurance
evidence as standards-compliant documents. Field names use Python conventions
internally; serialization to kebab-case OSCAL JSON/YAML is handled by the
serializer module.

Reference: https://pages.nist.gov/OSCAL-Reference/models/v1.1.2/
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4


def _uuid() -> str:
    return str(uuid4())


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

OSCAL_VERSION = "1.1.2"


@dataclass
class OSCALProp:
    """OSCAL prop (name/value pair) used across metadata, observations, etc.

    The platform's AR ingester reads specific names (e.g. `ai-system-uuid`,
    `ai-system-version-uuid`, `trace-id`) from `metadata.props[]` to resolve
    tenant bindings — see src/lib/services/oscal-ar-ingestion.service.ts.
    """

    name: str
    value: str
    ns: str = ""


@dataclass
class OSCALMetadata:
    """OSCAL metadata block (required on every document)."""

    title: str
    version: str = "1.0"
    last_modified: str = field(default_factory=_now)
    oscal_version: str = OSCAL_VERSION
    props: List[OSCALProp] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Assessment Results
# ---------------------------------------------------------------------------

@dataclass
class RelevantEvidence:
    """Pointer to an evidence artifact (file, hash, URL)."""

    href: str
    description: str = ""


@dataclass
class OSCALObservation:
    """A single measurement or inspection performed during assessment.

    Maps one-to-one with a ComplianceResult metric evaluation.

    The `props` list carries the structured metric data (control-id,
    metric-key, actual-value, threshold, operator, severity). The SaaS
    AR ingester reads these props to materialize TechnicalMetric +
    RiskEvaluation rows; without them only the free-text `description`
    survives the round-trip and the platform-side metric-processing
    chain leaves `TechnicalMetric.value`/`threshold` empty.
    """

    uuid: str = field(default_factory=_uuid)
    title: str = ""
    description: str = ""
    methods: List[str] = field(default_factory=lambda: ["TEST"])
    types: List[str] = field(default_factory=lambda: ["control-implementation"])
    collected: str = field(default_factory=_now)
    relevant_evidence: List[RelevantEvidence] = field(default_factory=list)
    props: List["OSCALProp"] = field(default_factory=list)


@dataclass
class FindingTargetStatus:
    """Status of a finding target (OSCAL expects an object, not a string)."""

    state: str = "satisfied"  # "satisfied" | "not-satisfied"


@dataclass
class FindingTarget:
    """The control targeted by a finding."""

    target_id: str  # control-id
    type: str = "objective-id"
    status: FindingTargetStatus = field(default_factory=FindingTargetStatus)


@dataclass
class ObservationRef:
    """Reference to an observation by UUID (OSCAL expects object, not bare string)."""

    observation_uuid: str


@dataclass
class RiskRef:
    """Reference to a risk by UUID."""

    risk_uuid: str


@dataclass
class OSCALFinding:
    """A conclusion drawn from one or more observations about a control.

    A finding is "satisfied" if the control passed, "not-satisfied" otherwise.
    """

    uuid: str = field(default_factory=_uuid)
    title: str = ""
    description: str = ""
    target: FindingTarget = None
    related_observations: List[ObservationRef] = field(default_factory=list)
    related_risks: List[RiskRef] = field(default_factory=list)


@dataclass
class CharacterizationFacet:
    """A single facet of a risk characterization."""

    name: str
    value: str
    system: str = "https://venturalitica.ai/oscal"


@dataclass
class OriginActor:
    """An actor that originated the characterization."""

    type: str = "tool"
    actor_uuid: str = field(default_factory=_uuid)


@dataclass
class CharacterizationOrigin:
    """Origin of the characterization (requires actors[])."""

    actors: List[OriginActor] = field(default_factory=lambda: [OriginActor()])


@dataclass
class RiskCharacterization:
    """Quantitative details about a risk (metric value vs threshold)."""

    origin: CharacterizationOrigin = field(default_factory=CharacterizationOrigin)
    facets: List[CharacterizationFacet] = field(default_factory=list)


@dataclass
class OSCALRisk:
    """A risk identified during assessment (auto-generated for failed controls)."""

    uuid: str = field(default_factory=_uuid)
    title: str = ""
    description: str = ""
    statement: str = ""
    status: str = "open"  # "open" | "investigating" | "remediating" | "deviation-requested" | "deviation-approved" | "closed"
    characterizations: List[RiskCharacterization] = field(default_factory=list)


@dataclass
class IncludeControl:
    """A control included in the assessment scope."""

    control_id: str


@dataclass
class ControlSelection:
    """A selection of controls to include in the review."""

    include_controls: List[IncludeControl] = field(default_factory=list)


@dataclass
class ReviewedControls:
    """The set of controls that were reviewed in this assessment."""

    control_selections: List[ControlSelection] = field(default_factory=list)


@dataclass
class OSCALResult:
    """A single assessment execution (one run of enforce() within monitor())."""

    uuid: str = field(default_factory=_uuid)
    title: str = ""
    description: str = ""
    start: str = field(default_factory=_now)
    end: str = field(default_factory=_now)
    reviewed_controls: ReviewedControls = field(default_factory=ReviewedControls)
    observations: List[OSCALObservation] = field(default_factory=list)
    findings: List[OSCALFinding] = field(default_factory=list)
    risks: List[OSCALRisk] = field(default_factory=list)


@dataclass
class ImportAP:
    """Reference to the assessment plan (OSCAL policy file) used."""

    href: str


@dataclass
class AssessmentResults:
    """Top-level OSCAL Assessment Results document.

    Spec: https://pages.nist.gov/OSCAL-Reference/models/v1.1.2/assessment-results/
    """

    uuid: str = field(default_factory=_uuid)
    metadata: OSCALMetadata = field(default_factory=lambda: OSCALMetadata(title="AI Assurance Assessment Results"))
    import_ap: Optional[ImportAP] = None
    results: List[OSCALResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Plan of Action and Milestones (POA&M)
# ---------------------------------------------------------------------------

@dataclass
class POAMItem:
    """A remediation action for an identified risk.

    Auto-generated for each failed control during assessment.
    """

    uuid: str = field(default_factory=_uuid)
    title: str = ""
    description: str = ""
    related_findings: List[str] = field(default_factory=list)  # finding uuids
    related_risks: List[str] = field(default_factory=list)  # risk uuids
    status: str = "open"  # "open" | "investigating" | "remediating" | "completed" | "cancelled"


@dataclass
class PlanOfActionAndMilestones:
    """Top-level OSCAL POA&M document.

    Spec: https://pages.nist.gov/OSCAL-Reference/models/v1.1.2/plan-of-action-and-milestones/
    """

    uuid: str = field(default_factory=_uuid)
    metadata: OSCALMetadata = field(default_factory=lambda: OSCALMetadata(title="AI Assurance Plan of Action and Milestones"))
    risks: List[OSCALRisk] = field(default_factory=list)
    poam_items: List[POAMItem] = field(default_factory=list)
