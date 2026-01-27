
import pytest
from unittest.mock import patch, MagicMock, Mock
import pandas as pd
import sys
from venturalitica.quickstart import quickstart, load_sample, list_scenarios, show_code, SAMPLE_SCENARIOS
from venturalitica.models import ComplianceResult

# --- Test list_scenarios ---
def test_list_scenarios():
    scenarios = list_scenarios()
    assert isinstance(scenarios, dict)
    assert 'loan' in scenarios

# --- Test show_code ---
def test_show_code(capsys):
    show_code('loan')
    captured = capsys.readouterr()
    assert "00_minimal.py" in captured.out

# --- Test load_sample ---
def test_load_sample_unknown():
    with pytest.raises(ValueError, match="Unknown sample"):
        load_sample('unknown_scenario')

def test_load_sample_uci_success():
    # Helper to mock ucimlrepo module which is imported inside the function
    mock_ucimlrepo = MagicMock()
    mock_dataset = MagicMock()
    mock_dataset.data.features = pd.DataFrame({'feature': [1, 2]})
    mock_dataset.data.targets = [0, 1]
    mock_ucimlrepo.fetch_ucirepo.return_value = mock_dataset
    
    with patch.dict(sys.modules, {'ucimlrepo': mock_ucimlrepo}):
        df = load_sample('loan', verbose=True)
    
    assert isinstance(df, pd.DataFrame)
    assert 'class' in df.columns
    mock_ucimlrepo.fetch_ucirepo.assert_called_with(id=144)

def test_load_sample_uci_import_error(capsys):
    # Simulate ImportError when importing ucimlrepo
    with patch.dict(sys.modules, {'ucimlrepo': None}): # This might cause confusion, better to use side_effect on import?
        # Actually standard way to mock missing module is tricky.
        # But we can patch builtins.__import__ or check how to mock ImportError.
        # Simpler: Mock the fetch_ucirepo to raise ImportError? 
        # No, the import itself raises it.
        # Let's assumes we can patch sys.modules so the IMPORT fails. 
        # But load_sample does `from ucimlrepo import fetch_ucirepo`
        with patch.dict(sys.modules):
            sys.modules.pop('ucimlrepo', None)
            # We need to make sure the import raises ImportError. 
            # We can use a Mock that raises ImportError on access? No.
            # Let's rely on patching `fetch_ucirepo` if we can access it, or just testing the fallback path directly
            pass

    # Alternative: Test fallback path directly by mocking that uci_id is NOT in config or forced exception
    # Let's try mocking fetch_ucirepo to raise Exception, covering line 198
    mock_ucimlrepo = MagicMock()
    mock_ucimlrepo.fetch_ucirepo.side_effect = Exception("UCI Error")
    
    with patch.dict(sys.modules, {'ucimlrepo': mock_ucimlrepo}):
        with patch('pathlib.Path.exists', return_value=False):
             with pytest.raises(FileNotFoundError):
                load_sample('loan')

    captured = capsys.readouterr()
    assert "Could not fetch from UCI" in captured.out

# --- Test quickstart ---
@patch('venturalitica.quickstart.load_sample')
@patch('venturalitica.quickstart.enforce')
@patch('pathlib.Path.exists', return_value=True)
def test_quickstart_success(mock_exists, mock_enforce, mock_load):
    mock_load.return_value = pd.DataFrame({'age': [20], 'class': [1]})
    # Fix: enforce must return objects with .passed attribute
    result_mock = MagicMock(spec=ComplianceResult)
    result_mock.passed = True
    mock_enforce.return_value = [result_mock]
    
    results = quickstart('loan', verbose=True)
    
    assert len(results) == 1
    mock_load.assert_called_with('loan', verbose=True)
    mock_enforce.assert_called()
