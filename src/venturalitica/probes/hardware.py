import time
from typing import Dict, Any
from .base import BaseProbe


class HardwareProbe(BaseProbe):
    """
    Tracks hardware telemetry like peak RAM and CPU usage.
    """

    def __init__(self):
        super().__init__("Hardware Telemetry")
        self.start_time = 0
        self.peak_memory = 0

    def start(self):
        self.start_time = time.time()
        try:
            import psutil

            process = psutil.Process()
            self.peak_memory = process.memory_info().rss
        except ImportError:
            pass

    def stop(self) -> Dict[str, Any]:
        try:
            import psutil

            process = psutil.Process()
            # Capture peak during stop as a simple heuristic
            current_mem = process.memory_info().rss
            self.peak_memory = max(self.peak_memory, current_mem)
            self.results = {
                "peak_memory_mb": self.peak_memory / (1024 * 1024),
                "cpu_count": psutil.cpu_count(),
            }
        except Exception:
            pass
        return self.results

    def get_summary(self) -> str:
        mem = self.results.get("peak_memory_mb")
        if mem:
            return f"  💻 [Hardware] Peak Memory: {mem:.2f} MB | CPUs: {self.results.get('cpu_count')}"
        return ""
