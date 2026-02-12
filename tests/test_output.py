"""
Comprehensive tests for venturalitica.output module.
Covers print_compliance_summary with rich available/unavailable, all-pass, partial-fail.
"""

from unittest.mock import MagicMock

from venturalitica.models import ComplianceResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_result(passed: bool, control_id: str = "C1") -> ComplianceResult:
    return ComplianceResult(
        control_id=control_id,
        description="desc",
        metric_key="metric",
        threshold=0.5,
        actual_value=0.1 if passed else 0.9,
        operator="<=",
        passed=passed,
        severity="high",
    )


# ===========================================================================
# RICH_AVAILABLE = False  (fallback branch, line 24-26)
# ===========================================================================


class TestFallbackPrint:
    def test_fallback_when_rich_unavailable(self, capsys):
        """When RICH_AVAILABLE is False, uses plain print()."""
        import venturalitica.output as mod

        original_rich = mod.RICH_AVAILABLE
        original_console = mod.console
        try:
            mod.RICH_AVAILABLE = False
            mod.console = None
            mod.print_compliance_summary("loan", [_make_result(True)])
            captured = capsys.readouterr()
            assert "Audit Complete" in captured.out
            assert "loan" in captured.out
        finally:
            mod.RICH_AVAILABLE = original_rich
            mod.console = original_console

    def test_fallback_when_console_is_none(self, capsys):
        """Even with RICH_AVAILABLE=True, if console is None -> fallback."""
        import venturalitica.output as mod

        original_console = mod.console
        try:
            mod.console = None
            mod.print_compliance_summary("test", [_make_result(True)])
            captured = capsys.readouterr()
            assert "Audit Complete" in captured.out
        finally:
            mod.console = original_console


# ===========================================================================
# RICH_AVAILABLE = True, all controls passed  (line 31-32)
# ===========================================================================


class TestAllPassed:
    def test_all_passed_green_message(self):
        """When all controls pass, prints the green 'All controls passed' message."""
        import venturalitica.output as mod

        mock_console = MagicMock()
        original_console = mod.console
        original_rich = mod.RICH_AVAILABLE
        try:
            mod.RICH_AVAILABLE = True
            mod.console = mock_console
            results = [_make_result(True, f"C{i}") for i in range(3)]
            mod.print_compliance_summary("fairness", results)

            # Collect all print calls
            all_args = [str(call) for call in mock_console.print.call_args_list]
            joined = " ".join(all_args)
            assert "All controls passed" in joined
        finally:
            mod.RICH_AVAILABLE = original_rich
            mod.console = original_console


# ===========================================================================
# RICH_AVAILABLE = True, some controls failed  (line 33-34)
# ===========================================================================


class TestPartialFailure:
    def test_partial_failure_yellow_warning(self):
        """When some controls fail, prints the yellow summary with counts."""
        import venturalitica.output as mod

        mock_console = MagicMock()
        original_console = mod.console
        original_rich = mod.RICH_AVAILABLE
        try:
            mod.RICH_AVAILABLE = True
            mod.console = mock_console
            results = [
                _make_result(True, "C1"),
                _make_result(False, "C2"),
                _make_result(True, "C3"),
            ]
            mod.print_compliance_summary("hiring", results)

            all_args = [str(call) for call in mock_console.print.call_args_list]
            joined = " ".join(all_args)
            assert "2/3" in joined  # 2 passed out of 3
        finally:
            mod.RICH_AVAILABLE = original_rich
            mod.console = original_console


# ===========================================================================
# "Next Steps" section  (lines 36-39)
# ===========================================================================


class TestNextSteps:
    def test_next_steps_printed(self):
        """The 'Next Steps' section is always printed when rich is available."""
        import venturalitica.output as mod

        mock_console = MagicMock()
        original_console = mod.console
        original_rich = mod.RICH_AVAILABLE
        try:
            mod.RICH_AVAILABLE = True
            mod.console = mock_console
            mod.print_compliance_summary("demo", [_make_result(True)])

            all_args = [str(call) for call in mock_console.print.call_args_list]
            joined = " ".join(all_args)
            assert "Next Steps" in joined
            assert "venturalitica ui" in joined
            assert "docs.venturalitica.com" in joined
            assert "policy.yaml" in joined
        finally:
            mod.RICH_AVAILABLE = original_rich
            mod.console = original_console

    def test_next_steps_not_printed_in_fallback(self, capsys):
        """Fallback branch does NOT print next steps (only the summary)."""
        import venturalitica.output as mod

        original_rich = mod.RICH_AVAILABLE
        original_console = mod.console
        try:
            mod.RICH_AVAILABLE = False
            mod.console = None
            mod.print_compliance_summary("x", [_make_result(True)])
            captured = capsys.readouterr()
            assert "Next Steps" not in captured.out

        finally:
            mod.RICH_AVAILABLE = original_rich
            mod.console = original_console
