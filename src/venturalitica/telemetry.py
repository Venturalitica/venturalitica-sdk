import json
import os
import time
import uuid
from functools import wraps
from pathlib import Path
from typing import Any, Dict, Optional

# GDPR-Compliant PostHog Configuration
POSTHOG_HOST = "https://eu.i.posthog.com"  # EU Data Sovereignty

# Public Write-Only Key (Safe to embed, similar to Next.js/Google Analytics)
# This allows the SDK to send anonymous usage stats to the Venturalítica Project.
# Users can verify this key has NO admin access.
DEFAULT_PUBLIC_POSTHOG_KEY = "phc_ExGZUlLBLUyI6pHKaBFWdekgDF0mFeDYWyFOwffOjWe"

try:
    import importlib.util

    POSTHOG_AVAILABLE = importlib.util.find_spec("posthog") is not None
except ImportError:
    POSTHOG_AVAILABLE = False


class TelemetryClient:
    _instance = None
    _opt_out = False
    _session_id = str(uuid.uuid4())
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TelemetryClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # 1. check for opt-out environment variable
        if (
            os.getenv("VENTURALITICA_NO_ANALYTICS") == "1"
            or os.getenv("DO_NOT_TRACK") == "1"
        ):
            self._opt_out = True
            return

        self.config_dir = Path.home() / ".venturalitica"
        self.config_path = self.config_dir / "analytics.json"

        # 2. Load or create anonymous ID
        self.anonymous_id = self._get_or_create_anonymous_id()

        # 3. Initialize PostHog
        if POSTHOG_AVAILABLE and not self._opt_out:
            # Priority: Env Var > Embedded Public Key
            api_key = os.getenv("VENTURALITICA_POSTHOG_KEY", DEFAULT_PUBLIC_POSTHOG_KEY)

            # valid if it's not the raw placeholder
            if api_key and "PLACEHOLDER" not in api_key:
                try:
                    from posthog import Posthog

                    self._client = Posthog(project_api_key=api_key, host=POSTHOG_HOST)
                    # Enable/Disable based on initialization success
                    self._enabled = True
                except Exception:
                    self._enabled = False
            else:
                self._enabled = False
        else:
            self._enabled = False

    def _get_or_create_anonymous_id(self) -> str:
        if not self.config_dir.exists():
            try:
                self.config_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                return "unknown-user"

        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    return data.get("anonymous_id", str(uuid.uuid4()))
            except Exception:
                pass

        # Create new
        new_id = str(uuid.uuid4())
        try:
            with open(self.config_path, "w") as f:
                json.dump({"anonymous_id": new_id}, f)
        except Exception:
            pass
        return new_id

    def capture(self, event: str, properties: Optional[Dict[str, Any]] = None):
        """
        Captures an event.
        GDPR: No PII, Anonymized IP.
        """
        if self._opt_out or not self._enabled or not self._client:
            return

        if properties is None:
            properties = {}

        # Enrich with safe metadata
        properties["session_id"] = self._session_id
        properties["version"] = self._get_version()
        properties["platform"] = os.name

        # GDPR: Disable person profiles for anonymous events
        properties["$process_person_profile"] = False

        try:
            self._client.capture(
                distinct_id=self.anonymous_id,
                event=event,
                properties=properties,
                context={"ip": 0},  # GDPR: Anonymize IP
            )
        except Exception:
            pass  # Fail silently, never crash the app

    def _get_version(self):
        try:
            from . import __version__

            return __version__
        except ImportError:
            return "unknown"

    def group(
        self,
        group_type: str,
        group_key: str,
        group_properties: Optional[Dict[str, Any]] = None,
    ):
        if self._opt_out or not self._enabled or not self._client:
            return
        try:
            self._client.group_identify(group_type, group_key, group_properties)
        except Exception:
            pass


telemetry = TelemetryClient()


def track_command(command_name: str):
    """Decorator to track CLI command usage."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error = str(type(e).__name__)
                raise
            finally:
                duration = time.time() - start_time
                telemetry.capture(
                    "cli_command_executed",
                    {
                        "command": command_name,
                        "duration": duration,
                        "success": error is None,
                        "error_type": error,
                    },
                )

        return wrapper

    return decorator
