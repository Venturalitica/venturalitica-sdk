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
    'hiring': 2,    # Adult (Census Income)
    'health': 17,   # Breast Cancer Wisconsin
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
    },
    'hiring': {
        'name': 'Hiring Bias Detection',
        'dataset': 'adult_income.csv',
        'policy': 'hiring/hiring-bias.oscal.yaml',
        'target': 'target',
        'protected_attrs': {'sex': 'sex'},
        'description': 'Multi-attribute fairness in recruitment'
    },
    'health': {
        'name': 'Clinical Risk Assessment',
        'dataset': 'breast_cancer.csv',
        'policy': 'health/clinical-risk.oscal.yaml',
        'target': 'target',
        'protected_attrs': {'age_group': 'age_group'},
        'description': 'Healthcare diagnosis fairness'
    },
    'llm': {
        'name': 'LLM Bias Auditing',
        'dataset': 'crows_pairs_sample.csv',
        'policy': 'bias/llm-fairness.oscal.yaml',
        'target': 'bias_score',
        'protected_attrs': {
            'protected_attribute': 'protected_attribute',
            'stereotype_preference_rate': 'stereotype_preference_rate',
            'category_bias_score': 'category_bias_score'
        },
        'description': 'Language model demographic bias'
    },
    'vision': {
        'name': 'Computer Vision Fairness',
        'dataset': 'fairface_sample.csv',
        'policy': 'vision/fairness.oscal.yaml',
        'target': 'prediction',
        'protected_attrs': {'race': 'race', 'gender': 'gender'},
        'description': 'Facial recognition bias'
    },
    'medical': {
        'name': 'Medical Imaging Fairness',
        'dataset': 'tcia_sample.csv',
        'policy': 'medical/dicom-governance.oscal.yaml',
        'target': 'radiologist_score',
        'protected_attrs': {
            'modality': 'modality',
            'sex': 'sex',
            'age_group': 'age_group',
            'mask_quality_target': 'mask_quality_target',
            'subgroup': 'subgroup'
        },
        'description': 'DICOM imaging equity'
    }
}


def quickstart(scenario: str = 'loan', verbose: bool = True) -> List[ComplianceResult]:
    """
    One-liner to experience Venturalitica with pre-configured data and policies.
    
    This is the fastest way to understand the SDK's value proposition.
    Perfect for demos, tutorials, and first-time users.
    
    Args:
        scenario: One of 'loan', 'hiring', 'health', 'llm', 'vision', 'medical'
        verbose: If True, shows educational explanations
    
    Returns:
        List[ComplianceResult]: Audit results
    
    Example:
        >>> import venturalitica as vl
        >>> results = vl.quickstart('loan')
        
        [Venturalitica] 🎓 Scenario: Credit Scoring Fairness
        [Venturalitica] 📊 Loaded: 1000 loans
        [Venturalitica] 🛡️  Policy: EU AI Act - Fair Lending
        
        ╭─────────── Compliance Audit Results ───────────╮
        │ Control  │ Metric               │ Value │ Status │
        ├──────────┼──────────────────────┼───────┼────────┤
        │ fair-gen │ demographic_parity   │ 0.08  │ ✓ PASS │
        ╰──────────┴──────────────────────┴───────┴────────╯
        
        🎉 Aha! Moment: All controls passed!
    """
    if scenario not in SAMPLE_SCENARIOS:
        available = ', '.join(SAMPLE_SCENARIOS.keys())
        raise ValueError(f"Unknown scenario '{scenario}'. Choose from: {available}")
    
    config = SAMPLE_SCENARIOS[scenario]
    
    if verbose:
        print(f"\n[Venturalitica] 🎓 Scenario: {config['name']}")
        print(f"[Venturalitica] 📖 {config['description']}")
    
    # Load sample data
    df = load_sample(scenario, verbose=verbose)
    
    if verbose:
        print(f"[Venturalitica] 🛡️  Policy: {config['policy']}")
        print()
    
    # Build policy path
    # Assume samples repo structure: ../../venturalitica-sdk-samples/policies/
    sdk_root = Path(__file__).parent.parent.parent
    samples_root = sdk_root.parent.parent / 'venturalitica-sdk-samples'
    policy_path = samples_root / 'policies' / config['policy']
    
    # Fallback: try relative to cwd
    if not policy_path.exists():
        policy_path = Path('policies') / config['policy']
    
    if not policy_path.exists():
        print(f"  ⚠️  Policy file not found: {policy_path}")
        print(f"  Tip: Run quickstart from venturalitica-sdk-samples directory")
        return []
    
    # Enforce policy
    attrs = {**config['protected_attrs'], 'target': config['target']}
    results = enforce(data=df, policy=str(policy_path), **attrs)
    
    if verbose:
        print_aha_moment(scenario, results)
    
    return results


def load_sample(name: str, verbose: bool = True) -> pd.DataFrame:
    """
    Load a pre-configured sample dataset from UCI Machine Learning Repository.
    
    Uses the `ucimlrepo` package to fetch datasets directly from:
    https://archive.ics.uci.edu/datasets
    
    Args:
        name: Scenario name ('loan', 'hiring', etc.)
        verbose: Show loading messages
    
    Returns:
        pd.DataFrame: Sample dataset ready for governance checks
    
    Example:
        >>> df = vl.load_sample('loan')
        [Venturalitica] 📊 Loaded: UCI German Credit (1000 samples)
    """
    if name not in SAMPLE_SCENARIOS:
        available = ', '.join(SAMPLE_SCENARIOS.keys())
        raise ValueError(f"Unknown sample '{name}'. Choose from: {available}")
    
    config = SAMPLE_SCENARIOS[name]
    
    # Try UCI dataset first (preferred)
    if 'uci_id' in config:
        try:
            from ucimlrepo import fetch_ucirepo
            dataset = fetch_ucirepo(id=config['uci_id'])
            df = dataset.data.features.copy()
            df[config['target']] = dataset.data.targets
            
            if verbose:
                print(f"[Venturalitica] 📊 Loaded: UCI Dataset #{config['uci_id']} ({len(df)} samples)")
            
            return df
        except ImportError:
            print("  ⚠️  ucimlrepo not installed. Run: pip install ucimlrepo")
        except Exception as e:
            print(f"  ⚠️  Could not fetch from UCI: {e}")
    
    # Fallback: try local dataset files
    dataset_name = config.get('dataset', f"{name}.csv")
    sdk_root = Path(__file__).parent.parent.parent
    samples_root = sdk_root.parent.parent / 'venturalitica-sdk-samples'
    dataset_path = samples_root / 'datasets' / name / dataset_name
    
    if not dataset_path.exists():
        dataset_path = Path('datasets') / name / dataset_name
    
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found. Install ucimlrepo: pip install ucimlrepo"
        )
    
    df = pd.read_csv(dataset_path)
    
    if verbose:
        print(f"[Venturalitica] 📊 Loaded: {len(df)} samples from {name} scenario")
    
    return df


def show_code(scenario: str) -> None:
    """
    Display the full source code for a scenario.
    Useful for learning how to integrate the SDK.
    
    Args:
        scenario: Scenario name
    
    Example:
        >>> vl.show_code('loan')
        # Opens 00_minimal.py in your editor
    """
    print(f"📚 To see the full code for '{scenario}':")
    print(f"   Open: venturalitica-sdk-samples/scenarios/{scenario}-*/00_minimal.py")
    print(f"   Or visit: https://github.com/venturalitica/venturalitica-sdk-samples")


def list_scenarios() -> Dict[str, str]:
    """
    List all available quickstart scenarios.
    
    Returns:
        Dict mapping scenario names to descriptions
    
    Example:
        >>> scenarios = vl.list_scenarios()
        >>> for name, desc in scenarios.items():
        ...     print(f"{name}: {desc}")
    """
    return {name: config['description'] for name, config in SAMPLE_SCENARIOS.items()}
