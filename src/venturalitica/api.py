import json
import os
import time
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .binding import COLUMN_SYNONYMS, discover_column
from .core import AssuranceValidator, ComplianceResult
from .formatting import VenturalíticaJSONEncoder, print_summary
from .integrations import auto_log
from .oscal.builder import AssessmentResultsBuilder, POAMBuilder
from .oscal.serializer import to_json as oscal_to_json
from .session import GovernanceSession

# We need the version for the enforce print statement
try:
    from . import __version__
except ImportError:
    __version__ = "0.4.1"

_SESSION_ENFORCED = False


def _is_enforced():
    return _SESSION_ENFORCED


@contextmanager
def monitor(
    name: str = "Training Task",
    label: Optional[str] = None,
    inputs: Optional[List[str]] = None,
    outputs: Optional[List[str]] = None,
):
    """
    Multimodal Monitor: Extensible probe-based observation platform.
    Tracks Green AI, Hardware Telemetry, Security Integrity, and Audit Trace.
    """
    from .probes import (
        ArtifactProbe,
        BOMProbe,
        CarbonProbe,
        HandshakeProbe,
        HardwareProbe,
        IntegrityProbe,
        TraceProbe,
    )

    probes = [
        IntegrityProbe(),
        HardwareProbe(),
        CarbonProbe(),
        BOMProbe(),
        ArtifactProbe(inputs=inputs, outputs=outputs),
        HandshakeProbe(_is_enforced),
        TraceProbe(run_name=name, label=label),
    ]

    # [GovOps] Initialize Session
    session = GovernanceSession.start(name)
    run_dir = session.base_dir

    print(f"\n[Venturalítica] 🟢 Starting monitor: {name}")
    print(f"  📂 Evidence Vault: {run_dir}")
    start_time = time.time()

    # Telemetry Start
    telemetry = None
    try:
        from .telemetry import telemetry

        telemetry.capture("sdk_monitor_start", {"name": name, "label": label})
    except Exception:
        telemetry = None

    for probe in probes:
        probe.start()

    try:
        yield
    finally:
        duration = time.time() - start_time
        print(f"[Venturalítica] 🔴 Monitor stopped: {name}")
        print(f"  ⏱  Duration: {duration:.2f}s")

        if telemetry:
            try:
                telemetry.capture("sdk_monitor_end", {"name": name, "duration": duration})
            except Exception:
                pass

        for probe in probes:
            probe.stop()
            summary = probe.get_summary()
            if summary:
                print(summary)

        # --- OSCAL Assessment Results generation ---
        _generate_oscal_artifacts(
            run_dir=run_dir,
            name=name,
            start_time=start_time,
        )

        GovernanceSession.stop()


def _generate_oscal_artifacts(run_dir: Path, name: str, start_time: float) -> None:
    """Generate OSCAL Assessment Results and POA&M from cached results."""
    try:
        results_path = Path(run_dir) / "results.json"
        if not results_path.exists():
            return

        with open(results_path, "r") as f:
            raw = json.load(f)

        # Parse cached results back into ComplianceResult objects
        items = raw if isinstance(raw, list) else raw.get("metrics", [])
        if not items:
            return

        results = [
            ComplianceResult(
                control_id=r.get("control_id", ""),
                description=r.get("description", ""),
                metric_key=r.get("metric_key", ""),
                threshold=float(r.get("threshold", 0)),
                actual_value=float(r.get("actual_value", 0)),
                operator=r.get("operator", ""),
                passed=r.get("passed", False),
                severity=r.get("severity", ""),
                metadata=r.get("metadata", {}),
            )
            for r in items
        ]

        end_ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        start_ts = datetime.fromtimestamp(start_time, tz=timezone.utc).isoformat(timespec="seconds")

        # Collect evidence artifact paths from the run directory
        evidence = {}
        for artifact_file in Path(run_dir).glob("*"):
            if artifact_file.name != "results.json" and artifact_file.is_file():
                evidence[artifact_file.name] = str(artifact_file)

        # Build OSCAL Assessment Results
        ar = AssessmentResultsBuilder.build(
            results,
            title=f"AI Assurance Assessment: {name}",
            start_time=start_ts,
            end_time=end_ts,
            evidence_artifacts=evidence,
        )

        ar_path = Path(run_dir) / "assessment-results.oscal.json"
        with open(ar_path, "w") as f:
            f.write(oscal_to_json(ar))
        print(f"  ✓ OSCAL Assessment Results: {ar_path}")

        # Build POA&M (only if failures exist)
        poam = POAMBuilder.build(ar)
        if poam:
            poam_path = Path(run_dir) / "poam.oscal.json"
            with open(poam_path, "w") as f:
                f.write(oscal_to_json(poam))
            print(f"  ✓ OSCAL POA&M: {poam_path} ({len(poam.poam_items)} items)")

    except Exception as e:
        print(f"  ⚠ OSCAL generation failed: {e}")


def enforce(
    data: Any = None,
    metrics: Optional[Dict[str, float]] = None,
    policy: Union[str, Path, List[Union[str, Path]]] = "risks.oscal.yaml",
    target: str = "target",
    prediction: str = "prediction",
    strict: bool = False,
    phase: Optional[str] = None,
    **attributes,
) -> List[ComplianceResult]:
    """
    Main entry point for enforcing AI Assurance policies.

    Parameters:
        phase: Optional lifecycle_phase filter. When provided, only controls
            tagged with that phase (or untagged) are evaluated. Typical values:
            `training` (raw data, Art. 10), `validation` (model predictions,
            Art. 15). Controls tagged `monitoring` or `incident` are always
            skipped by the SDK; they target the runtime proxy (FairGage) and
            the incident handler respectively.
    """
    global _SESSION_ENFORCED
    _SESSION_ENFORCED = True

    policies = [policy] if not isinstance(policy, list) else policy
    all_results = []

    for p in policies:
        print(f"\n[Venturalítica v{__version__}] 🛡  Enforcing policy: {p}")
        try:
            validator = AssuranceValidator(p)
            results = []

            if data is not None:
                mapping = {}

                # [PLG] Robust Column Discovery for critical roles using shared binding module
                # First, try explicit parameters, then discover
                if target and target in data.columns:
                    mapping["target"] = target
                else:
                    discovered_target = discover_column(
                        "target", {}, data, COLUMN_SYNONYMS
                    )
                    if discovered_target != "MISSING":
                        mapping["target"] = discovered_target

                if prediction and prediction in data.columns:
                    mapping["prediction"] = prediction
                else:
                    discovered_pred = discover_column(
                        "prediction", {}, data, COLUMN_SYNONYMS
                    )
                    if discovered_pred != "MISSING":
                        mapping["prediction"] = discovered_pred

                mapping.update(attributes)
                # pass strict flag to validator so missing/skip behavior can be enforced
                results = validator.compute_and_evaluate(
                    data, mapping, strict=strict, phase=phase
                )
            elif metrics is not None:
                results = validator.evaluate(metrics, phase=phase)

            if results:
                all_results.extend(results)
                print_summary(results, is_data_only=(prediction is None))
            else:
                print(f"  ⚠ No applicable controls found in {p}")

        except FileNotFoundError:
            print(f"  ⚠ Policy file not found: {p}")
        except Exception as e:
            if strict:
                # In strict mode we propagate unexpected errors so callers can fail-fast
                raise
            print(f"  ⚠ Unexpected error loading {p}: {e}")

    if all_results:
        auto_log(all_results)

        # Cache results for Local Dashboard
        try:
            os.makedirs(".venturalitica", exist_ok=True)
            results_path = ".venturalitica/results.json"

            existing_results = []
            if os.path.exists(results_path):
                try:
                    with open(results_path, "r") as f:
                        existing_results = json.load(f)
                except Exception:
                    pass

            # Normalize existing results to a list if file contains a bundle/dict
            if isinstance(existing_results, dict):
                if isinstance(existing_results.get("metrics"), list):
                    existing_results = existing_results.get("metrics")
                elif isinstance(existing_results.get("post_metrics"), list):
                    existing_results = existing_results.get("post_metrics")
                else:
                    # Flatten any list values inside dict
                    flattened = []
                    for v in existing_results.values():
                        if isinstance(v, list):
                            flattened.extend(v)
                    existing_results = flattened

            new_results = [asdict(r) for r in all_results]
            # Avoid duplicates if exactly the same control results are added
            # For now, just append to keep it simple for the handshake
            combined = existing_results + new_results

            with open(results_path, "w") as f:
                json.dump(combined, f, indent=2, cls=VenturalíticaJSONEncoder)

            # [GovOps] Save to Session-specific storage
            session = GovernanceSession.get_current()
            if session:
                session.save_results(all_results, encoder=VenturalíticaJSONEncoder)
                print(f"  ✓ Evidence Synced: {session.results_file}")

            print(
                "  ✓ Results cached. Run 'venturalitica ui' to see the Compliance Dashboard."
            )
        except Exception as e:
            print(f"  ⚠ Failed to cache results: {e}")

    try:
        from .telemetry import telemetry as _tel
        passed = sum(1 for r in all_results if r.passed)
        failed = sum(1 for r in all_results if not r.passed)
        _tel.capture("sdk_enforce_completed", {
            "passed_count": passed,
            "failed_count": failed,
            "has_red_check": failed > 0,
            "total_controls": len(all_results),
        })
    except Exception:
        pass

    return all_results
