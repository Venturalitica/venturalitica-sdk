__version__ = "0.5.4"

from .api import (
    enforce,
    monitor,
)
from .policy import PolicyManager
from .quickstart import quickstart
from .wrappers import wrap

__all__ = [
    "monitor",
    "enforce",
    "wrap",
    "quickstart",
    "PolicyManager",
]


def _send_first_import():
    """Fire a one-time sdk_first_import event (guarded by analytics.json flag)."""
    try:
        import json
        from pathlib import Path
        config_path = Path.home() / ".venturalitica" / "analytics.json"
        if config_path.exists():
            with open(config_path, "r") as f:
                data = json.load(f)
            if data.get("first_import_sent"):
                return

        from .telemetry import telemetry
        telemetry.capture("sdk_first_import", {})

        # Mark as sent
        config_path.parent.mkdir(parents=True, exist_ok=True)
        existing = {}
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    existing = json.load(f)
            except Exception:
                pass
        existing["first_import_sent"] = True
        with open(config_path, "w") as f:
            json.dump(existing, f)
    except Exception:
        pass  # Never crash the import

_send_first_import()
