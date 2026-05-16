from typing import Any, Dict

from .base import BaseProbe


class CarbonProbe(BaseProbe):
    """
    Tracks carbon emissions using CodeCarbon.
    """

    def __init__(self):
        super().__init__("carbon")
        self.tracker = None

    def start(self):
        try:
            # NVIDIA probing (pynvml.nvmlInitWithFlags) can hang indefinitely
            # on hosts with broken / partially-installed drivers rather than
            # raising, so the legacy try/except-retry path never triggered.
            # Neutralise pynvml up front: every EmissionsTracker ctor goes
            # through `set_GPU_tracking` → `is_gpu_details_available` → the
            # monkeypatched stub returns 0, codecarbon concludes "no GPU"
            # and skips nvmlInit entirely.
            try:
                import pynvml

                pynvml.nvmlDeviceGetCount = lambda: 0
                # Also short-circuit nvmlInitWithFlags so any retry paths
                # don't re-enter the native hang.
                pynvml.nvmlInitWithFlags = lambda _flags=0: None
                pynvml.nvmlInit = lambda: None
            except Exception:
                pass

            from codecarbon import EmissionsTracker

            self.tracker = EmissionsTracker(
                save_to_file=False,
                log_level="error",
                gpu_ids=[],
            )
            self.tracker.start()
        except ImportError:
            pass
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
