import pytest
import pandas as pd
import os
import json
import sys
from unittest.mock import MagicMock, patch
from venturalitica.probes import CarbonProbe, HardwareProbe, IntegrityProbe, HandshakeProbe

def test_carbon_probe():
    # Mock codecarbon module
    mock_tracker = MagicMock()
    mock_tracker_inst = mock_tracker.return_value
    mock_tracker_inst.stop.return_value = 0.001
    
    with patch.dict("sys.modules", {"codecarbon": MagicMock()}):
        import codecarbon
        codecarbon.EmissionsTracker = mock_tracker
        
        probe = CarbonProbe()
        probe.start()
        res = probe.stop()
        assert "emissions_kg" in res
        assert res["emissions_kg"] == 0.001
        assert "Carbon emissions" in probe.get_summary()

def test_carbon_probe_errors():
    probe = CarbonProbe()
    # Test summary when no results
    assert "unavailable" in probe.get_summary()
    
    # Test start with ImportError
    with patch.dict("sys.modules", {"codecarbon": None}):
        with patch("builtins.__import__", side_effect=ImportError):
            probe.start() # Should catch ImportError
    
    # Test start with generic Exception
    with patch.dict("sys.modules", {"codecarbon": MagicMock()}):
        with patch("codecarbon.EmissionsTracker", side_effect=RuntimeError("Crash")):
             probe.start() # Should catch Exception
    
    # Test stop exception
    probe.tracker = MagicMock()
    probe.tracker.stop.side_effect = Exception("Crash")
    res = probe.stop()
    assert res == {}

def test_hardware_probe_errors():
    probe = HardwareProbe()
    # Mock psutil to not exist
    with patch.dict("sys.modules", {"psutil": None}):
        probe.start()
    
    # Mock stop exception
    with patch("psutil.Process", side_effect=Exception("No psutil")):
        res = probe.stop()
    assert res == {}
    assert probe.get_summary() == ""

def test_hardware_probe():
    probe = HardwareProbe()
    probe.start()
    res = probe.stop()
    assert "peak_memory_mb" in res
    assert "cpu_count" in res
    assert res["cpu_count"] > 0
    assert "[Hardware]" in probe.get_summary()

def test_integrity_probe():
    probe = IntegrityProbe()
    probe.start()
    res = probe.stop()
    assert "start_state" in res
    assert "drift_detected" in res
    assert "🛡 [Security]" in probe.get_summary()
    
    # Test drift detected
    probe.results["end_state"]["fingerprint"] = "DIFFERENT"
    probe.results["drift_detected"] = True
    assert "DRIFT DETECTED" in probe.get_summary()

def test_handshake_probe_summary():
    mock_func = MagicMock(return_value=False)
    probe = HandshakeProbe(mock_func)
    probe.start()
    probe.stop()
    assert "Nudge" in probe.get_summary()
    
    mock_func.return_value = True
    probe.stop()
    assert "Policy enforced" in probe.get_summary()

def test_handshake_probe():
    probe = HandshakeProbe(lambda: True)
    probe.start()
    res = probe.stop()
    assert "is_compliant" in res
    assert res["is_compliant"] is True
