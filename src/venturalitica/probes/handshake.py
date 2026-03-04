import json
import os
from typing import Any, Callable, Dict

from .base import BaseProbe

SIGNUP_URL = "https://app.venturalitica.ai/signup?ref=sdk"


class HandshakeProbe(BaseProbe):
    """
    Checks if the developer has performed a 'Handshake' (assurance audit).
    Promotes PLG by nudging users towards compliance with actionable CTAs.
    """

    def __init__(self, session_enforced_func: Callable[[], bool]):
        super().__init__("Handshake Readiness")
        self.enforced_func = session_enforced_func
        self.was_enforced_at_start = False

    def start(self):
        self.was_enforced_at_start = self.enforced_func()

    def _count_red_checks(self) -> int:
        """Count failed controls from cached results."""
        try:
            results_path = ".venturalitica/results.json"
            if not os.path.exists(results_path):
                return 0
            with open(results_path, "r") as f:
                data = json.load(f)
            if isinstance(data, list):
                return sum(1 for r in data if not r.get("passed", True))
            return 0
        except Exception:
            return 0

    def stop(self) -> Dict[str, Any]:
        red_checks = self._count_red_checks() if self.enforced_func() else 0
        self.results = {
            "is_compliant": self.enforced_func(),
            "newly_enforced": not self.was_enforced_at_start and self.enforced_func(),
            "red_check_count": red_checks,
        }
        return self.results

    def get_summary(self) -> str:
        if not self.results.get("is_compliant"):
            return "  🤝 [Handshake] Nudge: No policy enforcement detected yet. Run `vl.enforce()` to ensure compliance."

        red_checks = self.results.get("red_check_count", 0)
        if red_checks > 0:
            return (
                f"  🤝 [Handshake] {red_checks} governance gap{'s' if red_checks != 1 else ''} detected.\n"
                f"     To resolve them collaboratively:\n"
                f"     → Sign up: {SIGNUP_URL}\n"
                f"     → Then run: venturalitica login && venturalitica push"
            )
        return "  🤝 [Handshake] Policy enforced — verifiable audit trail present."
