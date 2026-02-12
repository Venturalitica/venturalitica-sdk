from typing import TypedDict, List, Dict, Any, Optional, Annotated

def merge_dicts(a: Dict, b: Dict) -> Dict:
    return {**a, **b}

class SectionDraft(TypedDict):
    content: str
    status: str  # "drafting", "completed", "error"
    feedback: Optional[str]
    thinking: Optional[str] # Chain-of-Thought (if available)

class ComplianceState(TypedDict):
    """
    The shared state of the Compliance Graph.
    """
    # Inputs
    project_root: str
    bom: Dict[str, Any]      # From Scanner
    runtime_meta: Dict[str, Any] # From vl.wrap logs
    languages: List[str] # List of target languages (e.g. ["Catalan", "French"])
    evidence_hash: str # SHA-256 hash of BOM + RuntimeMeta
    bom_security: Dict[str, Any] # OSV Scan results
    
    # Internal
    sections: Annotated[Dict[str, SectionDraft], merge_dicts] # Keyed by "2.a", "2.b", etc.
    revision_count: int
    critic_verdict: str # "APPROVE" or "REVISE"
    
    # Output
    final_markdown: Optional[str] # Master English Draft
    translations: Dict[str, str] # Keyed by language name
    code_context: Dict[str, Any] # Source code analysis metadata
