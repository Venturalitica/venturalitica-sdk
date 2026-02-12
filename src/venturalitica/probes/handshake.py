from typing import Dict, Any, Callable
from .base import BaseProbe


class HandshakeProbe(BaseProbe):
    """
    Checks if the developer has performed a 'Handshake' (assurance audit).
    Promotes PLG by nudging users towards compliance.
    """

    def __init__(self, session_enforced_func: Callable[[], bool]):
        super().__init__("Handshake Readiness")
        self.enforced_func = session_enforced_func
        self.was_enforced_at_start = False

    def start(self):
        self.was_enforced_at_start = self.enforced_func()

    def stop(self) -> Dict[str, Any]:
        self.results = {
            "is_compliant": self.enforced_func(),
            "newly_enforced": not self.was_enforced_at_start and self.enforced_func(),
        }
        return self.results

    def get_summary(self) -> str:
        if not self.results.get("is_compliant"):
            return "  🤝 [Handshake] Nudge: No policy enforcement detected yet. Run `vl.enforce()` to ensure compliance."
        return "  🤝 [Handshake] Policy enforced verifyable audit trail present."
