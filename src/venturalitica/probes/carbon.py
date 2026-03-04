from typing import Any, Dict

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
            # GPU enumeration may fail (e.g. broken NVIDIA drivers).
            # Retry with GPU detection disabled.
            self.tracker = None
            try:
                import pynvml
                pynvml.nvmlDeviceGetCount = lambda: 0

                from codecarbon import EmissionsTracker as ET
                self.tracker = ET(save_to_file=False, log_level="error")
                self.tracker.start()
            except Exception:
                self.tracker = None

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
