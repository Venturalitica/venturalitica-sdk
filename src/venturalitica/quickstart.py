"""
Quickstart helpers for frictionless SDK demos.
Enables 60-second 'Aha! Moment' experiences.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
from .models import ComplianceResult
from . import enforce
from .output import render_compliance_results, print_aha_moment

# UCI Dataset IDs from archive.ics.uci.edu
UCI_DATASETS = {
    'loan': 144,    # German Credit Data
}

# Sample data registry
SAMPLE_SCENARIOS = {
    'loan': {
        'name': 'Credit Scoring Fairness',
        'uci_id': 144,
        'policy': 'loan/risks.oscal.yaml',
        'target': 'class',
        'protected_attrs': {'gender': 'Attribute9', 'age': 'Attribute13'},
        'description': 'Detect bias in loan approval decisions (UCI German Credit)'
    }
}


def quickstart(scenario: str = 'loan', verbose: bool = True) -> List[ComplianceResult]:
    """
    One-liner to experience Venturalítica with pre-configured data and policies.
    
    This is the fastest way to understand the SDK's value proposition.
    Perfect for demos, tutorials, and first-time users.
    
    Args:
        scenario: Only 'loan' is supported for quickstart. 
                 For other scenarios, check the 'venturalitica-sdk-samples' repository.
        verbose: If True, shows educational explanations
    
    Returns:
        List[ComplianceResult]: Audit results
    
    Example:
        >>> import venturalitica as vl
        >>> results = vl.quickstart('loan')
        
        [Venturalítica] 🎓 Scenario: Credit Scoring Fairness
        [Venturalítica] 📊 Loaded: 1000 loans
        [Venturalítica] 🛡️  Policy: EU AI Act - Fair Lending
        
        ╭─────────── Compliance Audit Results ───────────╮
        │ Control  │ Metric               │ Value │ Status │
        ├──────────┼──────────────────────┼───────┼────────┤
        │ fair-gen │ demographic_parity   │ 0.08  │ ✓ PASS │
        ╰──────────┴──────────────────────┴───────┴────────╯
        
        🎉 Aha! Moment: All controls passed!
    """
    if scenario != 'loan':
        raise ValueError(
            f"Scenario '{scenario}' is not supported in quickstart. "
            "Please visit 'venturalitica-sdk-samples' for professional scenarios."
        )
    
    config = SAMPLE_SCENARIOS['loan']
    
    if verbose:
        print(f"\n[Venturalítica] 🎓 Scenario: {config['name']}")
        print(f"[Venturalítica] 📖 {config['description']}")
    
    # Load sample data
    df = load_sample('loan', verbose=verbose)
    
    if verbose:
        print(f"[Venturalítica] 🛡️  Policy: {config['policy']}")
        print()
    
    # Build policy path
    sdk_root = Path(__file__).parent.parent.parent
    # Handle both workspace and standalone installs
    samples_candidates = [
        sdk_root.parent.parent / 'venturalitica-sdk-samples',
        Path.cwd() / 'venturalitica-sdk-samples',
        Path.home() / 'venturalitica-sdk-samples',
    ]
    
    samples_root = None
    for cand in samples_candidates:
        if cand.exists():
            samples_root = cand
            break
            
    if samples_root:
        # Try root policies dir (legacy/extra)
        policy_path = samples_root / 'policies' / config['policy']
        
        # Try scenario-specific policies dir (current standard)
        if not policy_path.exists():
            scenario_dir = 'loan-credit-scoring' if scenario == 'loan' else scenario
            policy_path = samples_root / 'scenarios' / scenario_dir / 'policies' / config['policy']
    else:
        policy_path = Path('policies') / config['policy']
    
    # Fallback: try relative to cwd
    if not policy_path.exists():
        policy_path = Path('policies') / config['policy']
    
    if not policy_path.exists():
        print(f"  ⚠️  Policy file not found: {policy_path}")
        print(f"  Tip: Ensure venturalitica-sdk-samples is available.")
        return []
    
    # Enforce policy
    attrs = {**config['protected_attrs'], 'target': config['target']}
    
    # [v0.4] Auto-Trace: Capture runtime evidence via the Multimodal Monitor
    with monitor(f"quickstart_{scenario}"):
        results = enforce(data=df, policy=str(policy_path), **attrs)
    
    if verbose:
        print_aha_moment(scenario, results)
    
    return results


def load_sample(name: str, verbose: bool = True) -> pd.DataFrame:
    """
    Load the 'loan' sample dataset from UCI Machine Learning Repository.
    
    Args:
        name: Must be 'loan'
        verbose: Show loading messages
    
    Returns:
        pd.DataFrame: Sample dataset ready for governance checks
    """
    if name != 'loan':
        raise ValueError("Only 'loan' sample is available in SDK. Use venturalitica-sdk-samples for more.")
    
    config = SAMPLE_SCENARIOS['loan']
    
    # Try UCI dataset first (preferred)
    try:
        from ucimlrepo import fetch_ucirepo
        dataset = fetch_ucirepo(id=config['uci_id'])
        df = dataset.data.features.copy()
        df[config['target']] = dataset.data.targets
        
        if verbose:
            print(f"[Venturalítica] 📊 Loaded: UCI Dataset #{config['uci_id']} ({len(df)} samples)")
        
        return df
    except ImportError:
        print("  ⚠️  ucimlrepo not installed. Run: pip install ucimlrepo")
    except Exception as e:
        print(f"  ⚠️  Could not fetch from UCI: {e}")
    
    # Fallback: try local dataset files
    dataset_name = "loan.csv"
    sdk_root = Path(__file__).parent.parent.parent
    samples_root = sdk_root.parent.parent / 'venturalitica-sdk-samples'
    dataset_path = samples_root / 'datasets' / 'loan' / dataset_name
    
    if not dataset_path.exists():
        dataset_path = Path('datasets') / 'loan' / dataset_name
    
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found. Install ucimlrepo: pip install ucimlrepo"
        )
    
    df = pd.read_csv(dataset_path)
    
    if verbose:
        print(f"[Venturalítica] 📊 Loaded: {len(df)} samples from loan scenario")
    
    return df


def show_code(scenario: str = 'loan') -> None:
    """
    Display instructions to find the source code for the loan scenario.
    """
    print(f"📚 To see the full code for '{scenario}':")
    print(f"   Open: venturalitica-sdk-samples/scenarios/loan-credit-scoring/00_minimal.py")
    print(f"   Or visit: https://github.com/venturalitica/venturalitica-sdk-samples")


def list_scenarios() -> Dict[str, str]:
    """
    List available quickstart scenarios (only 'loan').
    """
    return {name: config['description'] for name, config in SAMPLE_SCENARIOS.items()}
