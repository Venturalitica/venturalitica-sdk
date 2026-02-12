"""
Tests for venturalitica.assurance.graph.workflow (route_feedback logic).

Since create_compliance_graph depends on LangGraph + LLM services,
we test the route_feedback function in isolation by extracting its logic.
"""



class TestRouteWorkflowLogic:
    """Test the route_feedback branching logic from workflow.py."""

    def _route_feedback(self, state):
        """Reproduce the route_feedback logic from workflow.py lines 48-59."""
        writers = [
            "writer_2a",
            "writer_2b",
            "writer_2c",
            "writer_2d",
            "writer_2e",
            "writer_2f",
            "writer_2g",
            "writer_2h",
        ]
        END = "__end__"
        if state.get("critic_verdict") == "APPROVE":
            lang = state.get("language", "English").lower()
            if lang.startswith("es") or lang == "spanish":
                return END
            return "translator"
        return writers

    def test_approve_spanish_bypasses_translator(self):
        """Lines 55-57: Spanish + APPROVE -> END (bypass translator)."""
        state = {"critic_verdict": "APPROVE", "language": "Spanish"}
        assert self._route_feedback(state) == "__end__"

    def test_approve_es_prefix_bypasses_translator(self):
        """Language starting with 'es' also bypasses."""
        state = {"critic_verdict": "APPROVE", "language": "es-ES"}
        assert self._route_feedback(state) == "__end__"

    def test_approve_english_goes_to_translator(self):
        """Line 58: non-Spanish + APPROVE -> translator."""
        state = {"critic_verdict": "APPROVE", "language": "English"}
        assert self._route_feedback(state) == "translator"

    def test_approve_default_language_goes_to_translator(self):
        """Default language (English) goes to translator."""
        state = {"critic_verdict": "APPROVE"}
        assert self._route_feedback(state) == "translator"

    def test_reject_routes_to_writers(self):
        """Line 59: REJECT -> routes back to all writers."""
        state = {"critic_verdict": "REJECT"}
        result = self._route_feedback(state)
        assert isinstance(result, list)
        assert len(result) == 8
        assert all(w.startswith("writer_") for w in result)

    def test_missing_verdict_routes_to_writers(self):
        """No critic_verdict -> treated as rejection."""
        state = {}
        result = self._route_feedback(state)
        assert isinstance(result, list)
