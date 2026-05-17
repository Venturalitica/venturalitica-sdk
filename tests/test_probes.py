import json
import os

from unittest.mock import MagicMock, patch

from venturalitica.probes import BOMProbe, CarbonProbe, HandshakeProbe, HardwareProbe, IntegrityProbe


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

def test_bom_probe_emits_cyclonedx_1_6(tmp_path, monkeypatch):
    """BOMProbe writes a CycloneDX 1.6 JSON document with valid PURLs.

    Guards three properties the SaaS `bom-ingestion.service.ts` relies on:
    1. specVersion == 1.6 (so the SaaS knows which CycloneDX features it
       can rely on — e.g. `formulation[]` ML-BOM block).
    2. components[].purl is a `pkg:pypi/...` Package URL (the ingester's
       primary `bom-ref` lookup key).
    3. The probe envelope exposes `component_count` AND the flat
       `components[]` projection used by lightweight consumers.
    """
    # Synthetic project — two libraries declared via requirements.txt.
    (tmp_path / "requirements.txt").write_text(
        "requests==2.31.0\nnumpy>=1.24\n"
    )
    monkeypatch.chdir(tmp_path)

    probe = BOMProbe(target_dir=str(tmp_path))
    probe.start()
    res = probe.stop()

    # Envelope contract — back-compat keys preserved + new schema fields.
    assert "component_count" in res
    assert res["component_count"] >= 2
    assert res["_format"] == "CycloneDX"
    assert res["_format_version"] == "1.6"
    assert res["components_count"] == res["component_count"]
    assert isinstance(res["components"], list)

    # CycloneDX 1.6 schema compliance on the embedded BOM.
    bom = res["bom"]
    assert bom["bomFormat"] == "CycloneDX"
    assert bom["specVersion"] == "1.6"
    assert "serialNumber" in bom
    assert isinstance(bom["components"], list)
    assert len(bom["components"]) == res["component_count"]

    # On-disk BOM is byte-identical to the embedded one.
    assert os.path.exists(res["bom_path"])
    with open(res["bom_path"]) as f:
        on_disk = json.load(f)
    assert on_disk == bom

    # PURL validation — every library component must have a pkg:pypi URL.
    library_components = [c for c in bom["components"] if c.get("type") == "library"]
    assert library_components, "expected at least one library component"
    for comp in library_components:
        assert "purl" in comp, f"component {comp['name']} missing purl"
        assert comp["purl"].startswith("pkg:pypi/"), (
            f"component {comp['name']} has non-PyPI PURL: {comp['purl']}"
        )
        # bom-ref must align with the PURL so dependency edges stay stable.
        assert comp.get("bom-ref") == comp["purl"]

    # Projection contract — same fields the SaaS ingester reads.
    for proj in res["components"]:
        assert set(proj.keys()) == {
            "name", "version", "type", "purl", "bom_ref", "license"
        }

    # Summary string reflects the count.
    assert f"{res['component_count']} components" in probe.get_summary()


def test_bom_probe_error_path(monkeypatch):
    """If the scanner blows up, the probe surfaces a clean `error` payload
    instead of crashing the audit run.
    """
    probe = BOMProbe(target_dir=".")
    with patch("venturalitica.scanner.BOMScanner.scan", side_effect=RuntimeError("boom")):
        probe.start()
        res = probe.stop()
    assert "error" in res
    assert "boom" in res["error"]
    assert "Failed to capture BOM" in probe.get_summary()


def test_abstract_probe():
    """Test BaseProbe abstract class can be subclassed."""
    from venturalitica.probes import BaseProbe
    
    class DummyProbe(BaseProbe):
        def start(self):
            return super().start()
        def stop(self):
            return super().stop()
    
    p = DummyProbe("test")
    p.start()
    p.stop()
    assert p.get_summary() == ""
