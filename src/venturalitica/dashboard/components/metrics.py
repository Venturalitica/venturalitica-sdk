import json
from pathlib import Path
from typing import Optional


def list_available_sessions():
    """Returns a list of available session IDs from the runs directory."""
    runs_dir = Path(".venturalitica") / "runs"
    if not runs_dir.exists():
        return []

    # Filter for directories and exclude 'latest' to avoid duplicates
    sessions = [d.name for d in runs_dir.iterdir() if d.is_dir() and d.name != "latest"]
    # Sort by timestamp (descending) - assuming names start with name_YYYYMMDD_...
    sessions.sort(reverse=True)
    return sessions


def load_cached_results(session_id: Optional[str] = None):
    """Loads results from a specific session or the global file."""
    if session_id:
        if session_id == "Global / History":
            results_path = Path(".venturalitica") / "results.json"
        else:
            results_path = Path(".venturalitica") / "runs" / session_id / "results.json"
    else:
        # Fallback to latest or root
        results_path = Path(".venturalitica") / "results.json"

    if results_path.exists():
        with open(results_path, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return None
    return None


def load_session_metadata(session_id: str):
    """Loads all metadata associated with a session (trace, bom)."""
    base_path = Path(".venturalitica") / "runs" / session_id
    if not base_path.exists():
        return {}

    meta = {}

    # Load traces
    traces = []
    for f in base_path.glob("trace_*.json"):
        try:
            with open(f, "r") as tf:
                traces.append(json.load(tf))
        except Exception:
            pass
    meta["traces"] = traces

    # Load BOM
    bom_path = base_path / "bom.json"
    if bom_path.exists():
        try:
            with open(bom_path, "r") as bf:
                meta["bom"] = json.load(bf)
        except Exception:
            pass

    return meta


def parse_bom_metrics(bom):
    """Parses BOM into actionable metrics and lists."""
    if not bom:
        return {}, [], []

    components = bom.get("components", [])
    ml_models = [c for c in components if c.get("type") == "machine-learning-model"]
    libs = [c for c in components if c.get("type") == "library"]

    licenses = set()
    for c in components:
        for lic in c.get("licenses", []):
            if isinstance(lic, dict) and "license" in lic:
                licenses.add(lic["license"].get("id", "Unknown"))
            elif isinstance(lic, str):
                licenses.add(lic)

    metrics = {
        "total": len(components),
        "models": len(ml_models),
        "licenses": len(licenses),
    }
    return metrics, ml_models, libs
