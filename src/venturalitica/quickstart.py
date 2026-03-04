"""
Quickstart helpers for frictionless SDK demos.
Enables 60-second audit experiences.
"""

from pathlib import Path
from typing import List

import pandas as pd

from . import enforce, monitor
from .models import ComplianceResult

# Embedded OSCAL policy for loan scenario (no file dependency)
LOAN_POLICY_DICT = {
    'assessment-plan': {
        'metadata': {
            'title': 'Credit Risk Assessment Policy (German Credit)',
            'version': '1.1'
        },
        'control-implementations': [
            {
                'description': 'Credit Scoring Fairness (v2)',
                'implemented-requirements': [
                    {
                        'control-id': 'credit-data-imbalance',
                        'description': 'Data Quality: Minority class representation >= 20%',
                        'props': [
                            {'name': 'metric_key', 'value': 'class_imbalance'},
                            {'name': 'threshold', 'value': '0.2'},
                            {'name': 'operator', 'value': 'gt'},
                            {'name': 'input:target', 'value': 'target'}
                        ]
                    },
                    {
                        'control-id': 'credit-data-bias',
                        'description': 'Disparate impact ratio follows the Four-Fifths Rule',
                        'props': [
                            {'name': 'metric_key', 'value': 'disparate_impact'},
                            {'name': 'threshold', 'value': '0.8'},
                            {'name': 'operator', 'value': 'gt'},
                            {'name': 'input:target', 'value': 'target'},
                            {'name': 'input:dimension', 'value': 'gender'}
                        ]
                    },
                    {
                        'control-id': 'credit-age-disparate',
                        'description': 'Age disparate impact ratio > 0.5',
                        'props': [
                            {'name': 'metric_key', 'value': 'disparate_impact'},
                            {'name': 'threshold', 'value': '0.5'},
                            {'name': 'operator', 'value': 'gt'},
                            {'name': 'input:target', 'value': 'target'},
                            {'name': 'input:dimension', 'value': 'age'}
                        ]
                    }
                ]
            }
        ]
    }
}

# Sample data registry
SAMPLE_SCENARIOS = {
    'loan': {
        'name': 'Fairness Audit loan_scoring_v2',
        'uci_id': 144,
        'policy': LOAN_POLICY_DICT,  # Use embedded dict instead of file path
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
        
        Audit Complete: All controls passed!
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
        print("[Venturalítica] 🛡️  Policy: Embedded (no file required)")
        print()
    
    # Use embedded policy dictionary (no file dependency)
    policy = config['policy']
    
    # Enforce policy
    attrs = {**config['protected_attrs'], 'target': config['target']}
    
    # [v0.4] Auto-Trace: Capture runtime evidence via the Multimodal Monitor
    with monitor(f"quickstart_{scenario}"):
        results = enforce(data=df, policy=policy, **attrs)
    
    if verbose:
        from .output import print_compliance_summary
        print_compliance_summary(scenario, results)
    
    return results


def load_sample(name: str, verbose: bool = True) -> pd.DataFrame:
    """
    Load the 'loan' sample dataset from UCI Machine Learning Repository.
    
    Args:
        name: Must be 'loan'
        verbose: Show loading messages
    
    Returns:
        pd.DataFrame: Sample dataset ready for assurance checks
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
            "Dataset not found. Install ucimlrepo: pip install ucimlrepo"
        )
    
    df = pd.read_csv(dataset_path)
    
    if verbose:
        print(f"[Venturalítica] 📊 Loaded: {len(df)} samples from loan scenario")
    
    return df


def list_scenarios() -> dict:
    """Returns a dictionary of available quickstart scenarios."""
    return SAMPLE_SCENARIOS


def show_code(scenario: str = 'loan'):
    """Prints the location of the scenario code."""
    print(f"Code for {scenario}: see 00_minimal.py in venturalitica-sdk-samples repository.")
