"""Serialize OSCAL data models to JSON and YAML following OSCAL v1.2.2 conventions.

OSCAL uses kebab-case for JSON/YAML keys. This module handles the conversion
from Python snake_case dataclass fields to OSCAL kebab-case output.
"""

import json
from dataclasses import asdict
from typing import Any, Dict, Union

from .models import AssessmentResults, PlanOfActionAndMilestones


def _to_kebab(key: str) -> str:
    """Convert snake_case to kebab-case."""
    return key.replace("_", "-")


def _convert_keys(obj: Any) -> Any:
    """Recursively convert all dict keys from snake_case to kebab-case."""
    if isinstance(obj, dict):
        return {_to_kebab(k): _convert_keys(v) for k, v in obj.items() if v is not None and v != "" and v != []}
    if isinstance(obj, list):
        return [_convert_keys(item) for item in obj]
    return obj


def _wrap_document(doc_type: str, data: Dict) -> Dict:
    """Wrap serialized data in the OSCAL top-level envelope."""
    return {doc_type: data}


def assessment_results_to_dict(ar: AssessmentResults) -> Dict:
    """Convert AssessmentResults to an OSCAL-compliant dict."""
    raw = asdict(ar)
    converted = _convert_keys(raw)
    return _wrap_document("assessment-results", converted)


def poam_to_dict(poam: PlanOfActionAndMilestones) -> Dict:
    """Convert PlanOfActionAndMilestones to an OSCAL-compliant dict."""
    raw = asdict(poam)
    converted = _convert_keys(raw)
    return _wrap_document("plan-of-action-and-milestones", converted)


def to_json(
    document: Union[AssessmentResults, PlanOfActionAndMilestones],
    indent: int = 2,
) -> str:
    """Serialize an OSCAL document to JSON string."""
    if isinstance(document, AssessmentResults):
        data = assessment_results_to_dict(document)
    elif isinstance(document, PlanOfActionAndMilestones):
        data = poam_to_dict(document)
    else:
        raise TypeError(f"Unsupported document type: {type(document)}")
    return json.dumps(data, indent=indent, ensure_ascii=False)


def to_yaml(
    document: Union[AssessmentResults, PlanOfActionAndMilestones],
) -> str:
    """Serialize an OSCAL document to YAML string."""
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML is required for YAML serialization: pip install pyyaml")

    if isinstance(document, AssessmentResults):
        data = assessment_results_to_dict(document)
    elif isinstance(document, PlanOfActionAndMilestones):
        data = poam_to_dict(document)
    else:
        raise TypeError(f"Unsupported document type: {type(document)}")
    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
