import streamlit as st
from venturalitica.scanner import BOMScanner
from pathlib import Path
import os
import json

def load_cached_results():
    results_path = ".venturalitica/results.json"
    if os.path.exists(results_path):
        with open(results_path, "r") as f:
            return json.load(f)
    return None

def parse_bom_metrics(bom):
    """Parses BOM into actionable metrics and lists."""
    if not bom:
        return {}, [], []
    
    components = bom.get('components', [])
    ml_models = [c for c in components if c.get('type') == 'machine-learning-model']
    libs = [c for c in components if c.get('type') == 'library']
    
    licenses = set()
    for c in components:
        for lic in c.get('licenses', []):
            if isinstance(lic, dict) and 'license' in lic:
                licenses.add(lic['license'].get('id', 'Unknown'))
            elif isinstance(lic, str):
                licenses.add(lic)
                
    metrics = {
        "total": len(components),
        "models": len(ml_models),
        "licenses": len(licenses)
    }
    return metrics, ml_models, libs
