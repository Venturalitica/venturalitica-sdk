import hashlib
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


def _partition_digest(
    data: Any = None, metrics: Optional[Dict[str, float]] = None
) -> str:
    """Content digest of the partition a batch of results was computed against.

    `enforce()` may run twice against the same logical dataset sliced two
    different ways (e.g. one row per case, one row per treated vertebra).
    The two runs can legitimately report very different numbers for the
    exact same control_id -- k-anonymity read on the per-vertebra table
    counts vertebrae as individuals, not patients -- and nothing in a bare
    ComplianceResult says which table produced which number (#977). This
    digest is that mark: stamped on every result `enforce()` returns
    (retained or not), so a result can always be traced back to the exact
    partition it was measured against.
    """
    if data is not None and hasattr(data, "columns"):
        try:
            import pandas as pd

            hashed_rows = pd.util.hash_pandas_object(data, index=True)
            payload = hashed_rows.values.tobytes() + ",".join(
                map(str, data.columns)
            ).encode("utf-8")
            return hashlib.sha256(payload).hexdigest()
        except Exception:
            # `hash_pandas_object` raises on unhashable cell contents --
            # object columns holding lists/arrays, not exotic in a
            # segmentation pipeline (measured: a column of Python lists
            # raises TypeError). `repr(data)` looks like a safe fallback
            # but is the opposite: pandas TRUNCATES repr() past ~60 rows,
            # so two large DataFrames that differ only past the truncation
            # point produce an IDENTICAL repr and therefore the SAME
            # digest -- the exact collision this digest exists to rule out
            # (#977; measured: two 401-row frames differing only at row
            # 200 give identical repr(), distinct to_csv()). Hash the full
            # byte content instead -- `to_csv` never truncates.
            try:
                digest = hashlib.sha256(
                    data.to_csv(index=True).encode("utf-8")
                ).hexdigest()
                print(
                    "  ⚠ partition_digest: hash_pandas_object failed on this "
                    "DataFrame, fell back to a full to_csv() hash"
                )
                return digest
            except Exception:
                print(
                    "  ⚠ partition_digest: could not hash this DataFrame at "
                    "all -- returning an empty digest rather than one that "
                    "might collide with a different partition"
                )
                return ""
    if metrics is not None:
        return hashlib.sha256(
            json.dumps(metrics, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
    return ""


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

        probe_results: Dict[str, Dict[str, Any]] = {}
        for probe in probes:
            result = probe.stop() or {}
            # Keep the structured payload keyed by the probe's human name
            # (matches `get_summary()`'s prefix) so the SaaS ingester can
            # surface each probe on the AssuranceTrace cockpit.
            probe_results[probe.name] = dict(result) if isinstance(result, dict) else {}
            summary = probe.get_summary()
            if summary:
                print(summary)

        # --- OSCAL Assessment Results generation ---
        _generate_oscal_artifacts(
            run_dir=run_dir,
            name=name,
            start_time=start_time,
            probe_results=probe_results,
        )

        GovernanceSession.stop()


def _generate_oscal_artifacts(
    run_dir: Path,
    name: str,
    start_time: float,
    probe_results: Optional[Dict[str, Dict[str, Any]]] = None,
) -> None:
    """Generate OSCAL Assessment Results and POA&M from cached results."""
    try:
        # #977: prefer the RETAINED subset (`vl.retain()`) over the raw
        # evaluated cache. When a pipeline has explicitly filtered
        # `enforce()`'s combined output (e.g. down to the controls the
        # compiled OSCAL profile actually tags for the partition they were
        # computed against), that filtered set is what `assessment-results
        # .oscal.json` -- and therefore `vl push` -- must ship. Scripts that
        # never call `vl.retain()` (the common single-`enforce()`-call case)
        # keep today's behavior: everything evaluated is what gets pushed.
        retained_path = Path(run_dir) / "retained_results.json"
        results_path = retained_path if retained_path.exists() else Path(run_dir) / "results.json"
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
        _cache_files = {"results.json", "retained_results.json"}
        for artifact_file in Path(run_dir).glob("*"):
            if artifact_file.name not in _cache_files and artifact_file.is_file():
                evidence[artifact_file.name] = str(artifact_file)

        # Read tenant binding from the AP the SDK pulled earlier. The
        # platform-side AP emitter stamps `ai-system-uuid` and
        # `ai-system-version-uuid` into metadata.props[] — we echo both
        # back into the AR so the platform resolves the correct version
        # by UUID with no "latest" fallback.
        ai_system_uuid = ""
        ai_system_version_uuid = ""
        policy_path = Path(".venturalitica") / "policy.oscal.json"
        if policy_path.exists():
            try:
                with open(policy_path, "r") as f:
                    policy_doc = json.load(f)
                # Canonical NIST OSCAL v1.2.2 `component-definition` envelope.
                # The tenant-binding props (`ai-system-uuid`,
                # `ai-system-version-uuid`) live on `metadata.props[]`.
                cd = policy_doc.get("component-definition", policy_doc)
                for p in (cd.get("metadata", {}).get("props", []) or []):
                    if p.get("name") == "ai-system-uuid":
                        ai_system_uuid = str(p.get("value", ""))
                    elif p.get("name") == "ai-system-version-uuid":
                        ai_system_version_uuid = str(p.get("value", ""))
            except Exception:
                # Best-effort — if the policy doc is malformed, fall
                # through with empty binding props.
                pass

        # Build OSCAL Assessment Results
        ar = AssessmentResultsBuilder.build(
            results,
            title=f"AI Assurance Assessment: {name}",
            start_time=start_ts,
            end_time=end_ts,
            evidence_artifacts=evidence,
            ai_system_uuid=ai_system_uuid,
            ai_system_version_uuid=ai_system_version_uuid,
            probe_results=probe_results or {},
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
                results = validator.evaluate(metrics, phase=phase, strict=strict)

            if results:
                # #977: stamp the partition digest on every result BEFORE it
                # ever reaches the vault, so a result computed on one slice
                # of the data can never be confused with the same
                # control_id computed on a different slice (e.g. per-case
                # vs. per-vertebra). This runs unconditionally -- whether
                # or not the caller ever calls `vl.retain()`.
                digest = _partition_digest(data=data, metrics=metrics)
                for r in results:
                    r.metadata = dict(r.metadata or {})
                    r.metadata["partition_digest"] = digest
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

            # [GovOps] Save to Session-specific storage. This is the raw
            # EVALUATED cache -- everything this call computed, whether or
            # not a downstream pipeline will keep it. See `retain()` below
            # for the authoritative subset that `vl push` actually ships.
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


def retain(results: List[ComplianceResult]) -> List[ComplianceResult]:
    """Declares `results` as the session's authoritative, push-worthy subset (#977).

    `enforce()` caches every result it evaluates, including ones a
    downstream pipeline later discards -- e.g. a control evaluated once
    per case and once per anatomical partition, kept only for the
    partition the compiled OSCAL profile actually tags it for. That raw
    cache is fine for the Local Dashboard but not safe to `push`: it can
    disagree with the caller's own authoritative metrics (its own
    `metrics.json`), and nothing marks which one governs.

    Call this once, after filtering `enforce()`'s combined output down to
    what the pipeline actually keeps -- typically the union of two or more
    `enforce()` calls, filtered by reading each control's partition from
    the compiled OSCAL. `_generate_oscal_artifacts` reads this retained set
    instead of the raw evaluated cache whenever one exists for the current
    session, so `vl push` ships only what was retained. Scripts that call
    `enforce()` once and never call `retain()` are unaffected: with no
    retained set, everything evaluated is what gets pushed, same as today.

    Each result already carries `metadata["partition_digest"]`, stamped by
    `enforce()` at computation time, so two results sharing a control_id
    (the same control computed against two different partitions) stay
    distinguishable even after this filtering step discards the context
    that produced them.

    Calling this with an empty list is a valid declaration -- "the pipeline
    retained nothing" -- and is recorded as such (an empty
    `retained_results.json`), not silently ignored: `_generate_oscal_artifacts`
    finds no items and produces no AR at all, so `vl push` fails loudly
    instead of shipping the unfiltered evaluated cache by accident.
    """
    session = GovernanceSession.get_current()
    if not session:
        # No active `monitor()` session -- e.g. called standalone, or after
        # the `with monitor(...):` block already exited. There is nowhere
        # to record the retained set, so a later `vl push` would fall back
        # to whatever got evaluated, unfiltered. That's the exact
        # contradiction this function exists to prevent, so it must not
        # fail silently (#977).
        print(
            "  ⚠ vl.retain() called with no active monitor() session -- "
            "nothing was recorded. A later `vl push` will ship everything "
            "evaluated, unfiltered, unless retain() is called again inside "
            "an active session."
        )
        return results
    session.save_results(results, encoder=VenturalíticaJSONEncoder, retained=True)
    return results
