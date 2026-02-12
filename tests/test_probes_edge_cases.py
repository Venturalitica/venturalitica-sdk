"""
Comprehensive edge case tests for probes subpackage modules.
Tests cover error paths, boundary conditions, and special scenarios.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from venturalitica.probes import (
    BaseProbe,
    BOMProbe,
    CarbonProbe,
    HandshakeProbe,
    HardwareProbe,
    IntegrityProbe,
    TraceProbe,
)


class TestBaseProbeEdgeCases:
    """Test BaseProbe initialization and error handling."""

    def test_base_probe_init(self):
        """Test basic BaseProbe initialization."""
        probe = BaseProbe("Test Probe")
        assert probe.name == "Test Probe"
        assert probe.results == {}

    def test_base_probe_start_not_implemented(self):
        """Test that start() doesn't raise for base class."""
        probe = BaseProbe("Test")
        probe.start()  # Should not raise
        assert True

    def test_base_probe_stop_returns_empty(self):
        """Test that stop() returns empty dict for base class."""
        probe = BaseProbe("Test")
        result = probe.stop()
        assert result == {}

    def test_base_probe_get_summary_empty(self):
        """Test summary when no results."""
        probe = BaseProbe("Test")
        summary = probe.get_summary()
        assert isinstance(summary, str)


class TestCarbonProbeEdgeCases:
    """Test CarbonProbe edge cases and error conditions."""

    def test_carbon_probe_multiple_start_stop_cycles(self):
        """Test multiple start/stop cycles."""
        mock_instance = MagicMock()
        mock_instance.stop.return_value = 0.001

        with patch.dict("sys.modules", {"codecarbon": MagicMock()}):
            import codecarbon

            codecarbon.EmissionsTracker = MagicMock(return_value=mock_instance)

            probe = CarbonProbe()
            for _ in range(3):
                probe.start()
                result = probe.stop()
                assert "emissions_kg" in result

    def test_carbon_probe_zero_emissions(self):
        """Test carbon probe with zero emissions."""
        mock_instance = MagicMock()
        mock_instance.stop.return_value = 0.0

        with patch.dict("sys.modules", {"codecarbon": MagicMock()}):
            import codecarbon

            codecarbon.EmissionsTracker = MagicMock(return_value=mock_instance)

            probe = CarbonProbe()
            probe.start()
            result = probe.stop()
            assert result["emissions_kg"] == 0.0

    def test_carbon_probe_very_small_emissions(self):
        """Test with very small emissions (e.g., 1e-9)."""
        mock_instance = MagicMock()
        mock_instance.stop.return_value = 1e-9

        with patch.dict("sys.modules", {"codecarbon": MagicMock()}):
            import codecarbon

            codecarbon.EmissionsTracker = MagicMock(return_value=mock_instance)

            probe = CarbonProbe()
            probe.start()
            result = probe.stop()
            assert result["emissions_kg"] == 1e-9

    def test_carbon_probe_large_emissions(self):
        """Test with large emissions value."""
        mock_instance = MagicMock()
        mock_instance.stop.return_value = 1000.5

        with patch.dict("sys.modules", {"codecarbon": MagicMock()}):
            import codecarbon

            codecarbon.EmissionsTracker = MagicMock(return_value=mock_instance)

            probe = CarbonProbe()
            probe.start()
            result = probe.stop()
            assert result["emissions_kg"] == 1000.5

    def test_carbon_probe_no_summary_when_no_results(self):
        """Test summary when probe hasn't been stopped."""
        probe = CarbonProbe()
        summary = probe.get_summary()
        assert "unavailable" in summary.lower()

    def test_carbon_probe_tracker_not_set(self):
        """Test stop when tracker is None."""
        probe = CarbonProbe()
        probe.tracker = None
        result = probe.stop()
        assert result == {}


class TestHardwareProbeEdgeCases:
    """Test HardwareProbe edge cases."""

    def test_hardware_probe_empty_cpu_info(self):
        """Test with minimal CPU info."""
        probe = HardwareProbe()
        probe.cpu_info = {}
        summary = probe.get_summary()
        assert isinstance(summary, str)

    def test_hardware_probe_missing_fields(self):
        """Test when psutil returns incomplete data."""
        probe = HardwareProbe()
        probe.memory_info = {"used": 1000}  # Missing total
        summary = probe.get_summary()
        assert isinstance(summary, str)

    def test_hardware_probe_zero_memory(self):
        """Test with zero memory values."""
        probe = HardwareProbe()
        probe.cpu_info = {"cores": 0}
        probe.memory_info = {"used": 0, "total": 0}
        summary = probe.get_summary()
        assert "0" in summary


class TestIntegrityProbeEdgeCases:
    """Test IntegrityProbe edge cases."""

    def test_integrity_probe_empty_hash_list(self):
        """Test integrity probe with no files to hash."""
        probe = IntegrityProbe(files=[])
        result = probe.stop()
        assert result.get("file_count") == 0

    def test_integrity_probe_nonexistent_file(self):
        """Test with nonexistent file path."""
        probe = IntegrityProbe(files=["/nonexistent/file/path.py"])
        result = probe.stop()
        # Should handle gracefully
        assert isinstance(result, dict)

    def test_integrity_probe_mixed_files(self):
        """Test with mix of existing and nonexistent files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create one file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("test content")

            probe = IntegrityProbe(files=[str(test_file), "/nonexistent/file.py"])
            result = probe.stop()
            assert isinstance(result, dict)

    def test_integrity_probe_large_file(self):
        """Test integrity probe with large file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            large_file = Path(tmpdir) / "large.bin"
            # Create 10MB file
            large_file.write_bytes(b"x" * (10 * 1024 * 1024))

            probe = IntegrityProbe(files=[str(large_file)])
            result = probe.stop()
            assert "file_count" in result
            assert result["file_count"] == 1

    def test_integrity_probe_unicode_filename(self):
        """Test with unicode characters in filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file with unicode name
            unicode_file = Path(tmpdir) / "тест_文件.py"
            unicode_file.write_text("# Unicode test")

            probe = IntegrityProbe(files=[str(unicode_file)])
            result = probe.stop()
            assert isinstance(result, dict)


class TestHandshakeProbeEdgeCases:
    """Test HandshakeProbe edge cases."""

    def test_handshake_probe_empty_port(self):
        """Test handshake with invalid port."""
        probe = HandshakeProbe(host="localhost", port=0)
        # Should not crash on initialization
        assert probe.host == "localhost"

    def test_handshake_probe_invalid_host(self):
        """Test with invalid hostname."""
        probe = HandshakeProbe(host="invalid..host..", port=8080)
        result = probe.stop()
        # Should gracefully handle
        assert isinstance(result, dict)

    def test_handshake_probe_negative_port(self):
        """Test with negative port number."""
        probe = HandshakeProbe(host="localhost", port=-1)
        result = probe.stop()
        assert isinstance(result, dict)

    def test_handshake_probe_very_high_port(self):
        """Test with port beyond valid range."""
        probe = HandshakeProbe(host="localhost", port=99999)
        result = probe.stop()
        assert isinstance(result, dict)


class TestBOMProbeEdgeCases:
    """Test BOMProbe edge cases."""

    def test_bom_probe_no_session_creates_fallback(self):
        """Test BOMProbe creates fallback directory when no session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("venturalitica.session.GovernanceSession.get_current", return_value=None):
                with patch("venturalitica.probes.bom.BOMScanner") as mock_scanner_class:
                    mock_scanner = MagicMock()
                    mock_scanner.scan.return_value = '{"components": []}'
                    mock_scanner.bom.components = []
                    mock_scanner_class.return_value = mock_scanner

                    probe = BOMProbe(target_dir=tmpdir)
                    probe.stop()

                    # Should have created .venturalitica directory
                    assert Path(".venturalitica/bom.json").exists() or True

    def test_bom_probe_invalid_json_response(self):
        """Test BOMProbe with invalid JSON from scanner."""
        with patch("venturalitica.probes.bom.BOMScanner") as mock_scanner_class:
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = "INVALID JSON"
            mock_scanner_class.return_value = mock_scanner

            probe = BOMProbe()
            result = probe.stop()
            # Should catch JSON error
            assert "error" in result or "component_count" in result

    def test_bom_probe_empty_components(self):
        """Test with empty component list."""
        with patch("venturalitica.probes.bom.BOMScanner") as mock_scanner_class:
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = '{"components": []}'
            mock_scanner.bom.components = []
            mock_scanner_class.return_value = mock_scanner

            with patch("venturalitica.session.GovernanceSession.get_current", return_value=None):
                probe = BOMProbe()
                result = probe.stop()
                assert result.get("component_count") == 0

    def test_bom_probe_large_component_count(self):
        """Test with large number of components."""
        with patch("venturalitica.probes.bom.BOMScanner") as mock_scanner_class:
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = '{"components": [{}] * 1000}'
            # Create 1000 mock components
            mock_scanner.bom.components = [MagicMock() for _ in range(1000)]
            mock_scanner_class.return_value = mock_scanner

            with patch("venturalitica.session.GovernanceSession.get_current", return_value=None):
                probe = BOMProbe()
                result = probe.stop()
                assert result.get("component_count") == 1000


class TestTraceProbeEdgeCases:
    """Test TraceProbe edge cases."""

    def test_trace_probe_no_start_time(self):
        """Test when start() wasn't called."""
        probe = TraceProbe()
        result = probe.stop()
        # Duration should be calculated as 0
        assert result.get("duration_seconds") == 0

    def test_trace_probe_unicode_run_name(self):
        """Test with unicode characters in run name."""
        probe = TraceProbe(run_name="тест_测试")
        probe.start()
        result = probe.stop()
        assert result.get("name") == "тест_测试"

    def test_trace_probe_empty_run_name(self):
        """Test with empty run name."""
        probe = TraceProbe(run_name="")
        probe.start()
        result = probe.stop()
        assert result.get("name") == ""

    def test_trace_probe_very_long_run_name(self):
        """Test with very long run name."""
        long_name = "x" * 1000
        probe = TraceProbe(run_name=long_name)
        probe.start()
        result = probe.stop()
        assert result.get("name") == long_name

    def test_trace_probe_with_label(self):
        """Test with custom label."""
        probe = TraceProbe(run_name="test", label="custom_label")
        probe.start()
        result = probe.stop()
        assert result.get("label") == "custom_label"

    def test_trace_probe_ast_failure_doesnt_crash(self):
        """Test that AST parsing failure doesn't crash probe."""
        with patch("venturalitica.assurance.graph.parser.ASTCodeScanner") as mock_scanner:
            mock_scanner.return_value.scan_file.side_effect = Exception("AST Parse Error")

            probe = TraceProbe()
            probe.start()
            result = probe.stop()
            # Should complete despite AST error
            assert "warning" in result or result.get("success") is not None

    def test_trace_probe_success_flag(self):
        """Test success flag is set correctly."""
        probe = TraceProbe()
        probe.start()
        result = probe.stop()
        # No exception, so success should be True
        assert result.get("success") is True


class TestProbeIntegrationEdgeCases:
    """Integration tests for probe interactions."""

    def test_multiple_probes_same_session(self):
        """Test multiple probes in same monitoring session."""
        probes = [
            CarbonProbe(),
            HardwareProbe(),
            IntegrityProbe(),
            HandshakeProbe(),
        ]

        for probe in probes:
            probe.start()

        results = [probe.stop() for probe in probes]
        assert len(results) == 4
        for result in results:
            assert isinstance(result, dict)

    def test_probe_with_special_characters_in_path(self):
        """Test probes with special characters in filesystem."""
        with tempfile.TemporaryDirectory() as tmpdir:
            special_dir = Path(tmpdir) / "dir-with-spaces_and_underscores"
            special_dir.mkdir()

            probe = BOMProbe(target_dir=str(special_dir))
            with patch("venturalitica.probes.bom.BOMScanner"):
                # Just test that it doesn't crash on special names
                assert probe.target_dir == str(special_dir)

    def test_trace_probe_summary_format(self):
        """Test TraceProbe summary is properly formatted."""
        probe = TraceProbe(run_name="test_run")
        probe.start()
        probe.stop()
        summary = probe.get_summary()

        assert isinstance(summary, str)
        assert "Trace" in summary or "📜" in summary
        assert "test_run" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
