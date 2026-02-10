import os
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from venturalitica.core import GovernanceValidator
from venturalitica.models import InternalPolicy, InternalControl

def get_mock_policy():
    return InternalPolicy(
        title="Test Policy",
        controls=[
            InternalControl(
                id="test-control-missing",
                description="Control with missing metric",
                metric_key="non_existent_metric",
                threshold=0.5,
                operator=">",
                severity="high",
                input_mapping={"target": "y"}
            )
        ]
    )

def test_strict_mode_env():
    print("\n--- Testing Strict Mode (CI=true) ---")
    os.environ["CI"] = "true"
    
    # Patch the loader to return our policy object directly
    with patch("venturalitica.loader.OSCALPolicyLoader.load") as mock_load:
        mock_load.return_value = get_mock_policy()
        
        validator = GovernanceValidator(policy={}) # Input dict is ignored by patched loader
        
        assert validator.strict == True, "Validator should be strict when CI=true"
        
        df = pd.DataFrame({"y": [0, 1]})
        
        try:
            validator.compute_and_evaluate(df, {"target": "y"})
            print("FAIL: Should have raised ValueError")
        except ValueError as e:
            print(f"SUCCESS: Caught expected error: {e}")
        finally:
            del os.environ["CI"]

def test_loose_mode():
    print("\n--- Testing Loose Mode (CI unset) ---")
    if "CI" in os.environ: del os.environ["CI"]
    
    with patch("venturalitica.loader.OSCALPolicyLoader.load") as mock_load:
        mock_load.return_value = get_mock_policy()
        
        validator = GovernanceValidator(policy={})
        
        assert validator.strict == False, "Validator should be loose when CI unset"
        
        df = pd.DataFrame({"y": [0, 1]})
        
        # Should not raise
        results = validator.compute_and_evaluate(df, {"target": "y"})
        print(f"SUCCESS: Handled missing metric gracefully (Results: {len(results)})")

if __name__ == "__main__":
    # We need to ensure we're targeting the right module path for patching
    # Since we run this script directly, imports are from installed package
    test_strict_mode_env()
    test_loose_mode()
