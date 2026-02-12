import os
import json
import sys
import inspect
from datetime import datetime
from typing import Dict, Any, Optional
from .base import BaseProbe
from venturalitica.session import GovernanceSession


class TraceProbe(BaseProbe):
    """
    Captures logical execution evidence: AST Code Analysis, Timestamps, and Call Context.
    This fulfills Articles 10 & 11 (Technical Documentation & Data Assurance).
    """

    def __init__(self, run_name: str = "default", label: Optional[str] = None):
        super().__init__("Audit Trace")
        self.run_name = run_name
        self.label = label
        self.start_time: Optional[datetime] = None

    def start(self):
        self.start_time = datetime.now()

    def stop(self) -> Dict[str, Any]:
        from venturalitica.assurance.graph.parser import ASTCodeScanner

        end_time = datetime.now()
        duration = (
            (end_time - self.start_time).total_seconds() if self.start_time else 0
        )

        # 1. Capture Contextual Metadata
        meta = {
            "name": self.run_name,
            "label": self.label,
            "timestamp": end_time.isoformat(),
            "duration_seconds": duration,
            "success": sys.exc_info()[0] is None,
        }

        # 2. AST Code Story Capture
        try:
            # We need to find the frame that called vl.monitor()
            # monitor() -> yield -> finally -> probe.stop()
            # We go back up the stack to find the user code.
            frame = inspect.currentframe()
            script_path = None
            while frame:
                module_name = frame.f_globals.get("__name__", "")
                if not module_name.startswith("venturalitica"):
                    script_path = frame.f_globals.get("__file__")
                    if script_path:
                        break
                frame = frame.f_back

            if script_path and os.path.exists(script_path):
                scanner = ASTCodeScanner()
                meta["code_context"] = {
                    "file": os.path.basename(script_path),
                    "analysis": scanner.scan_file(script_path),
                }
        except Exception as e:
            # We don't want to crash the monitor if AST fails
            meta["warning"] = f"AST Capture error: {e}"

        self.results = meta

        # 3. Persist Trace for UI
        try:
            session = GovernanceSession.get_current()
            if session:
                path = session.base_dir / f"trace_{self.run_name}.json"
                os.makedirs(session.base_dir, exist_ok=True)
            else:
                os.makedirs(".venturalitica", exist_ok=True)
                path = f".venturalitica/trace_{self.run_name}.json"

            with open(path, "w") as f:
                json.dump(meta, f, indent=2, default=str)
        except Exception:
            pass

        return self.results

    def get_summary(self) -> str:
        file_name = self.results.get("code_context", {}).get("file", "Unknown")
        session = GovernanceSession.get_current()
        storage_info = f"{session.base_dir if session else '.venturalitica'}/trace_{self.run_name}.json"
        return f"  📜 [Trace] Context: {file_name} | Evidence saved to {storage_info}"
