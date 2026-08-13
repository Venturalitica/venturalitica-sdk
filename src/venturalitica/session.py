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
        # #977: everything `enforce()` evaluates lands in `results.json` (the
        # Local Dashboard reads it, so every control shows up, even ones a
        # downstream pipeline later discards). Only what the caller explicitly
        # reclaims via `vl.retain()` as authoritative lands here instead --
        # this is what `_generate_oscal_artifacts` prefers when building the
        # `assessment-results.oscal.json` that `vl push` ships, so a push can
        # never contradict the caller's own metrics.
        self.retained_results_file = self.base_dir / "retained_results.json"

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

    def save_results(self, results: List[Any], encoder=None, retained: bool = False):
        """Saves compliance results to the session-specific file.

        Two destinations, same "accumulate across calls" semantics --
        `enforce()` is typically called more than once inside a single
        `monitor()` run, and each call's results are meant to add up, not
        replace the previous ones. `retained=False` (the default, used by
        every `enforce()` call) accumulates into `results.json` -- the raw,
        unfiltered "evaluated" cache. `retained=True` (used only by
        `vl.retain()`) accumulates into `retained_results.json` instead --
        the "retained" subset a pipeline has explicitly declared
        authoritative after filtering `enforce()`'s combined output. See
        `api._generate_oscal_artifacts` for which file wins when both exist.
        """
        target_file = self.retained_results_file if retained else self.results_file
        try:
            # results is usually a list of ComplianceResult dataclasses
            data = [
                asdict(r) if hasattr(r, "__dataclass_fields__") else r for r in results
            ]

            # Read existing if we are calling enforce/retain multiple times in one monitor session
            existing = []
            if target_file.exists():
                with open(target_file, "r") as f:
                    try:
                        existing = json.load(f)
                    except Exception:
                        pass

            combined = existing + data
            with open(target_file, "w") as f:
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
