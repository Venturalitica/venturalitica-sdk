import os
import json
from typing import Dict, Any
from .base import BaseProbe
from venturalitica.session import GovernanceSession


class BOMProbe(BaseProbe):
    """
    Captures the Software Bill of Materials (SBOM) at runtime.
    Ensures that the specific versions of libraries (pip freeze) are bound to the audit.
    """

    def __init__(self, target_dir: str = "."):
        super().__init__("Software Supply Chain")
        self.target_dir = target_dir

    def start(self):
        # BOM capture is a snapshot, no need for continuous monitoring
        pass

    def stop(self) -> Dict[str, Any]:
        try:
            from venturalitica.scanner import BOMScanner

            # Simple scan of current environment
            scanner = BOMScanner(self.target_dir)
            bom_str = scanner.scan()

            # Persist BOM as a backup/debug artifact
            session = GovernanceSession.get_current()
            bom_json = json.loads(bom_str)

            if session:
                bom_path = session.base_dir / "bom.json"
                os.makedirs(session.base_dir, exist_ok=True)
            else:
                os.makedirs(".venturalitica", exist_ok=True)
                bom_path = ".venturalitica/bom.json"

            with open(bom_path, "w") as f:
                json.dump(bom_json, f, indent=2)

            self.results = {
                "component_count": len(scanner.bom.components),
                "bom": bom_json,  # EMBEDDED IN TRACE
                "bom_path": str(bom_path),
            }
        except Exception as e:
            self.results = {"error": str(e)}

        return self.results

    def get_summary(self) -> str:
        count = self.results.get("component_count")
        if count is not None:
            return f"  📦 [Supply Chain] BOM Captured: {count} components linked."
        return f"  ⚠ [Supply Chain] Failed to capture BOM: {self.results.get('error')}"
