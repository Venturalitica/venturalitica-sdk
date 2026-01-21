import time
import platform
import sys
import os
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseProbe(ABC):
    """
    Abstract base class for all monitoring probes.
    Inspired by Martin Fowler's 'Probe Architecture'.
    """
    def __init__(self, name: str):
        self.name = name
        self.results: Dict[str, Any] = {}

    @abstractmethod
    def start(self):
        """Called when the monitor starts."""
        pass

    @abstractmethod
    def stop(self) -> Dict[str, Any]:
        """Called when the monitor stops. Returns a dictionary of results."""
        pass

    def get_summary(self) -> str:
        """Returns a human-readable summary of the probe's findings."""
        return ""

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
                "cpu_count": psutil.cpu_count()
            }
        except Exception:
            pass
        return self.results

    def get_summary(self) -> str:
        mem = self.results.get("peak_memory_mb")
        if mem:
            return f"  💻 [Hardware] Peak Memory: {mem:.2f} MB | CPUs: {self.results.get('cpu_count')}"
        return ""

class IntegrityProbe(BaseProbe):
    """
    Generates a Security Fingerprint of the execution environment.
    'Bruce Schneier' approved: Verify the integrity of the run.
    """
    def __init__(self):
        super().__init__("Security & Integrity")

    def _generate_fingerprint(self) -> Dict[str, str]:
        info = {
            "os": f"{platform.system()} {platform.release()}",
            "python": sys.version.split()[0],
            "arch": platform.machine(),
            "node": platform.node(),
            "cwd": os.getcwd()
        }
        
        # Create a deterministic hash of the environment state
        env_str = f"{info['os']}-{info['python']}-{info['cwd']}"
        fingerprint = hashlib.sha256(env_str.encode()).hexdigest()[:12]
        
        return {
            "fingerprint": fingerprint,
            "metadata": info
        }

    def start(self):
        self.results["start_state"] = self._generate_fingerprint()

    def stop(self) -> Dict[str, Any]:
        self.results["end_state"] = self._generate_fingerprint()
        self.results["drift_detected"] = (
            self.results["start_state"]["fingerprint"] != self.results["end_state"]["fingerprint"]
        )
        return self.results

    def get_summary(self) -> str:
        fp = self.results.get("start_state", {}).get("fingerprint", "Unknown")
        drift = "🚨 DRIFT DETECTED" if self.results.get("drift_detected") else "✅ Stable"
        return f"  🛡 [Security] Fingerprint: {fp} | Integrity: {drift}"

class HandshakeProbe(BaseProbe):
    """
    Checks if the developer has performed a 'Handshake' (governance audit).
    Promotes PLG by nudging users towards compliance.
    """
    def __init__(self, session_enforced_func: callable):
        super().__init__("Handshake Readiness")
        self.enforced_func = session_enforced_func
        self.was_enforced_at_start = False

    def start(self):
        self.was_enforced_at_start = self.enforced_func()

    def stop(self) -> Dict[str, Any]:
        self.results = {
            "is_compliant": self.enforced_func(),
            "newly_enforced": not self.was_enforced_at_start and self.enforced_func()
        }
        return self.results

    def get_summary(self) -> str:
        if not self.results.get("is_compliant"):
            return "  🤝 [Handshake] Nudge: No policy enforcement detected yet. Run `vl.enforce()` to ensure compliance."
        return "  🤝 [Handshake] Policy enforced verifyable audit trail present."
