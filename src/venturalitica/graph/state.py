from typing import TypedDict, List, Dict, Any, Optional, Annotated
import operator

def merge_dicts(a: Dict, b: Dict) -> Dict:
    return {**a, **b}

class SectionDraft(TypedDict):
    content: str
    status: str  # "drafting", "completed", "error"
    feedback: Optional[str]

class ComplianceState(TypedDict):
    """
    The shared state of the Compliance Graph.
    """
    # Inputs
    project_root: str
    bom: Dict[str, Any]      # From Scanner
    runtime_meta: Dict[str, Any] # From vl.wrap logs
    
    # Internal
    sections: Annotated[Dict[str, SectionDraft], merge_dicts] # Keyed by "2.a", "2.b", etc.
    revision_count: int
    critic_verdict: str # "APPROVE" or "REVISE"
    
    # Output
    final_markdown: Optional[str]
