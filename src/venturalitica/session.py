import json
import os
import threading
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional


class GovernanceSession:
    """
    Manages a unique execution 'run' for GovOps evidence collection.
    Persistent storage is organized in .venturalitica/runs/<run_id>/
    """

    _local = threading.local()

    def __init__(self, name: str = "run"):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_id = f"{name}_{self.timestamp}_{os.getpid()}"
        self.base_dir = Path(".venturalitica") / "runs" / self.run_id
        self.artifacts_dir = self.base_dir / "artifacts"
        self.results_file = self.base_dir / "results.json"

        # Ensure directories exist
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Update latest symlink (or copy for windows compatibility)
        self._update_latest_link()

    def _update_latest_link(self):
        latest_dir = Path(".venturalitica") / "runs" / "latest"
        try:
            if latest_dir.exists() or latest_dir.is_symlink():
                if latest_dir.is_symlink():
                    latest_dir.unlink()
                else:
                    import shutil

                    shutil.rmtree(latest_dir)

            # Create symlink (Unix)
            os.symlink(self.run_id, latest_dir)
        except Exception:
            # Fallback for Windows or systems without symlink support
            try:
                import shutil

                if latest_dir.exists():
                    shutil.rmtree(latest_dir)
                # On Windows, we just copy or ignore for now to keep it lightweight
                pass
            except Exception:
                pass

    def save_results(self, results: List[Any], encoder=None):
        """Saves compliance results to the session-specific file."""
        try:
            # results is usually a list of ComplianceResult dataclasses
            data = [
                asdict(r) if hasattr(r, "__dataclass_fields__") else r for r in results
            ]

            # Read existing if we are calling enforce multiple times in one monitor session
            existing = []
            if self.results_file.exists():
                with open(self.results_file, "r") as f:
                    try:
                        existing = json.load(f)
                    except Exception:
                        pass

            combined = existing + data
            with open(self.results_file, "w") as f:
                json.dump(combined, f, indent=2, cls=encoder)
        except Exception as e:
            print(f"  ⚠ Failed to save session results: {e}")

    @classmethod
    def get_current(cls) -> Optional["GovernanceSession"]:
        return getattr(cls._local, "current", None)

    @classmethod
    def start(cls, name: str = "run") -> "GovernanceSession":
        session = cls(name)
        cls._local.current = session
        return session

    @classmethod
    def stop(cls):
        cls._local.current = None
