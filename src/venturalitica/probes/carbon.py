from typing import Dict, Any
from .base import BaseProbe


class CarbonProbe(BaseProbe):
    """
    Tracks carbon emissions using CodeCarbon.
    """

    def __init__(self):
        super().__init__("Green AI")
        self.tracker = None

    def start(self):
        try:
            from codecarbon import EmissionsTracker

            self.tracker = EmissionsTracker(save_to_file=False, log_level="error")
            self.tracker.start()
        except ImportError:
            pass
        except Exception:
            pass

    def stop(self) -> Dict[str, Any]:
        if self.tracker:
            try:
                emissions = self.tracker.stop()
                self.results = {"emissions_kg": emissions}
            except Exception:
                pass
        return self.results

    def get_summary(self) -> str:
        emissions = self.results.get("emissions_kg")
        if emissions is not None:
            return f"  🌱 [Green AI] Carbon emissions: {emissions:.6f} kgCO₂"
        return "  ⚠ [Green AI] Emissions tracking unavailable."
