import platform
import sys
import os
import hashlib
from typing import Dict, Any
from .base import BaseProbe


class IntegrityProbe(BaseProbe):
    """
    Generates a Security Fingerprint of the execution environment.
    'Bruce Schneier' approved: Verify the integrity of the run.
    """

    def __init__(self):
        super().__init__("Security & Integrity")

    def _generate_fingerprint(self) -> Dict[str, Any]:
        info = {
            "os": f"{platform.system()} {platform.release()}",
            "python": sys.version.split()[0],
            "arch": platform.machine(),
            "node": platform.node(),
            "cwd": os.getcwd(),
        }

        # Create a deterministic hash of the environment state
        env_str = f"{info['os']}-{info['python']}-{info['cwd']}"
        fingerprint = hashlib.sha256(env_str.encode()).hexdigest()[:12]

        return {"fingerprint": fingerprint, "metadata": info}

    def start(self):
        self.results["start_state"] = self._generate_fingerprint()

    def stop(self) -> Dict[str, Any]:
        self.results["end_state"] = self._generate_fingerprint()
        self.results["drift_detected"] = (
            self.results["start_state"]["fingerprint"]
            != self.results["end_state"]["fingerprint"]
        )
        return self.results

    def get_summary(self) -> str:
        fp = self.results.get("start_state", {}).get("fingerprint", "Unknown")
        drift = (
            "🚨 DRIFT DETECTED" if self.results.get("drift_detected") else "✅ Stable"
        )
        return f"  🛡 [Security] Fingerprint: {fp} | Integrity: {drift}"
