import json
import os
from pathlib import Path
from typing import Optional

import requests
import typer

from ..telemetry import track_command
from .common import SAAS_URL, app, console, get_config_path

VL_DIR = Path(".venturalitica")
RUNS_DIR = VL_DIR / "runs"


def _latest_ar_path() -> Optional[Path]:
    """Find the OSCAL assessment-results doc of the most recent local run."""
    if not RUNS_DIR.exists():
        return None
    runs = [p for p in RUNS_DIR.iterdir() if p.is_dir()]
    if not runs:
        return None
    latest = max(runs, key=lambda p: p.stat().st_mtime)
    ar = latest / "assessment-results.oscal.json"
    return ar if ar.exists() else None


def _create_bundle_payload() -> dict:
    """
    Internal helper: Creates a signed compliance bundle payload.
    """
    console.print("[bold blue]📦 Preparing compliance bundle...[/bold blue]")

    # 1. Verification of Synchronized State
    if not os.path.exists(".venturalitica/results.json"):
        console.print(
            "[bold red]Error:[/bold red] results.json not found. Run your audit/training first."
        )
        raise typer.Exit(code=1)

    # 2. Collect Artifacts Metadata (Shadow Artifacts)
    artifacts = []

    # Check MLflow
    if os.getenv("MLFLOW_RUN_ID"):
        artifacts.append(
            {
                "name": f"MLflow Run: {os.getenv('MLFLOW_RUN_ID')}",
                "type": "MODEL",
                "uri": f"mlflow-run://{os.getenv('MLFLOW_RUN_ID')}",
                "context": "train",
                "metadata": {"framework": "mlflow"},
            }
        )

    # 3. Load Annex IV if exists.
    # Prefer the structured payload produced by `vl export-annex-iv` and
    # stashed under results.json["annex_iv"] — that's the 9-section EU AI
    # Act Art.11 document the platform binds to the uploaded artifact.
    # Fall back to parsing the legacy Annex_IV.md when the structured file
    # is absent, so projects that predate the new CLI still send something.
    annex_iv: dict = {}
    legacy_md = False
    if os.path.exists(".venturalitica/results.json"):
        try:
            with open(".venturalitica/results.json", "r") as f:
                maybe = json.load(f)
            if isinstance(maybe, dict) and isinstance(maybe.get("annex_iv"), dict):
                annex_iv = maybe["annex_iv"]
        except json.JSONDecodeError:
            pass
    if not annex_iv and os.path.exists("Annex_IV.md"):
        legacy_md = True
        with open("Annex_IV.md", "r") as f:
            for line in f:
                if "Intended Purpose:" in line:
                    annex_iv["intended_purpose"] = line.split(":", 1)[1].strip()
                elif "Hardware:" in line:
                    annex_iv["hardware"] = line.split(":", 1)[1].strip()
    if legacy_md and not annex_iv.get("generated_by"):
        annex_iv["generated_by"] = "legacy-annex-md-parser"

    # Intelligent Metrics Extraction
    metrics = []

    # 3. Load Results
    with open(".venturalitica/results.json", "r") as f:
        results_data = json.load(f)

    if isinstance(results_data, list):
        metrics = results_data
    elif isinstance(results_data, dict):
        # 1. Try standard 'metrics' key
        if "metrics" in results_data and isinstance(results_data["metrics"], list):
            metrics.extend(results_data["metrics"])

        # 2. Try 'pre_metrics' and 'post_metrics' (Training V1/V2 pattern)
        if "pre_metrics" in results_data and isinstance(
            results_data["pre_metrics"], list
        ):
            metrics.extend(results_data["pre_metrics"])
        if "post_metrics" in results_data and isinstance(
            results_data["post_metrics"], list
        ):
            metrics.extend(results_data["post_metrics"])

        # 3. Extract artifacts
        if "artifacts" in results_data and isinstance(results_data["artifacts"], list):
            artifacts.extend(results_data["artifacts"])

    # 4. Auto-discover Audit Traces and Extract BOM
    trace_dir = ".venturalitica"
    bom = {}
    latest_trace_time = 0

    if os.path.exists(trace_dir):
        for f in os.listdir(trace_dir):
            if f.startswith("trace_") and f.endswith(".json"):
                try:
                    with open(os.path.join(trace_dir, f), "r") as tf:
                        trace_data = json.load(tf)
                        # Extract BOM from trace (if present)
                        # We prioritize the most recent trace's BOM
                        trace_ts = trace_data.get(
                            "timestamp_unix", 0
                        )  # Assumes we add this
                        if not trace_ts:
                            # Fallback to file mtime if timestamp missing
                            trace_ts = os.path.getmtime(os.path.join(trace_dir, f))

                        if "bom" in trace_data:
                            if trace_ts > latest_trace_time:
                                bom = trace_data["bom"]
                                latest_trace_time = trace_ts

                        label = (
                            trace_data.get("label")
                            or trace_data.get("name")
                            or "Audit Trace"
                        )
                        artifacts.append(
                            {
                                "name": label,
                                "type": "CODE",
                                "uri": f"trace://{f}",
                                "context": "audit-trail",
                                "metadata": trace_data,
                            }
                        )
                except Exception:
                    pass

    # Fallback to local .venturalitica/bom.json if trace didn't have it (backward compat)
    if not bom and os.path.exists(".venturalitica/bom.json"):
        with open(".venturalitica/bom.json", "r") as f:
            bom = json.load(f)

    # Cryptographic Signing (HMAC-SHA256)
    import hashlib
    import hmac
    import time

    timestamp = time.time()

    # Load secret key
    secret_key = b"default-local-key"  # Fallback
    creds_path = get_config_path("credentials.json")
    if os.path.exists(creds_path):
        try:
            with open(creds_path, "r") as f:
                creds = json.load(f)
                if "key" in creds:
                    secret_key = creds["key"].encode()
        except Exception:
            pass

    # Payload to sign: Metrics + Timestamp + BOM Content Hash
    bom_hash = hashlib.sha256(json.dumps(bom, sort_keys=True).encode()).hexdigest()
    sign_payload = (
        f"{json.dumps(metrics, sort_keys=True)}{timestamp}{bom_hash}".encode()
    )

    signature = hmac.new(secret_key, sign_payload, hashlib.sha256).hexdigest()

    bundle_data = {
        "bundle": {
            "name": f"Compliance Bundle {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "annex_iv": annex_iv,
            "signature": signature,  # HMAC Signature
            "signature_type": "HMAC-SHA256",
            "timestamp": timestamp,
            "metadata": results_data.get("training_metadata")
            if isinstance(results_data, dict)
            else {},
        },
        "bom": bom,
        "metrics": metrics,
        "artifacts": artifacts,
    }
    return bundle_data


@app.command()
@track_command("push")
def push(
    external_run_url: Optional[str] = typer.Option(
        None, "--external-run-url", help="MLFlow/W&B Run URL"
    ),
    treatment_id: Optional[str] = typer.Option(
        None, "--treatment-id", help="Risk Treatment ID to link this trace"
    ),
):
    """
    Pushes the compliance results and artifacts to the SaaS.
    """
    console.print("[bold blue]📤 Pushing to SaaS...[/bold blue]")

    creds_path = get_config_path("credentials.json")
    if not os.path.exists(creds_path):
        console.print("[bold red]Error:[/bold red] Not logged in.")
        raise typer.Exit(code=1)

    with open(creds_path, "r") as f:
        creds = json.load(f)

    # OSCAL-native push: ship the `assessment-results.oscal.json`
    # produced by the monitor() run. The platform rejects any other shape.
    ar_path = _latest_ar_path()
    if ar_path is None:
        console.print(
            "[bold red]No OSCAL assessment-results found.[/bold red] "
            "Run `monitor()` or `vl audit` first to produce "
            ".venturalitica/runs/<run_id>/assessment-results.oscal.json."
        )
        raise typer.Exit(code=1)

    try:
        with open(ar_path, "r") as f:
            ar_doc = json.load(f)
    except Exception as e:
        console.print(f"[bold red]Failed to load AR doc {ar_path}:[/bold red] {e}")
        raise typer.Exit(code=1)

    # Run directory holds the bom.json + other probe outputs alongside
    # the AR. Used below to embed the CycloneDX SBOM into back-matter.
    run_dir: Optional[Path] = ar_path.parent if ar_path is not None else None

    # Embed Annex IV (EU AI Act Art.11) into the AR's back-matter.resources
    # with class='annex-iv'. The platform's oscal-ar-ingestion.service walks
    # back-matter looking for that exact class to extract the 9-section doc
    # and bind it to the produced MODEL artifact's AnnexIvDocument row. The
    # legacy top-level bundle.annex_iv field is no longer consumed (post
    # OSCAL-native rewrite), so this injection is the only path that lands
    # the doc on the platform side.
    annex_iv_payload: dict = {}
    if os.path.exists(".venturalitica/results.json"):
        try:
            with open(".venturalitica/results.json", "r") as f:
                maybe = json.load(f)
            if isinstance(maybe, dict) and isinstance(maybe.get("annex_iv"), dict):
                annex_iv_payload = maybe["annex_iv"]
        except json.JSONDecodeError:
            pass
    if annex_iv_payload:
        import base64 as _b64
        import uuid as _uuid
        ar_root = ar_doc.get("assessment-results", ar_doc)
        back_matter = ar_root.setdefault("back-matter", {})
        resources = back_matter.setdefault("resources", [])
        # Drop any prior annex-iv resource so re-pushes overwrite cleanly.
        resources[:] = [
            r for r in resources
            if not any(
                isinstance(p, dict) and p.get("name") == "class" and p.get("value") == "annex-iv"
                for p in (r.get("props") or [])
            )
        ]
        encoded = _b64.b64encode(
            json.dumps(annex_iv_payload, ensure_ascii=False).encode("utf-8")
        ).decode("ascii")
        resources.append({
            "uuid": str(_uuid.uuid4()),
            "title": "EU AI Act Art.11 Annex IV technical documentation",
            "description": (
                "9-section Annex IV doc derived by `vl export-annex-iv` from the "
                "OSCAL Assessment Results. Class='annex-iv' is the platform's "
                "lookup key (oscal-ar-ingestion.service)."
            ),
            "props": [{"name": "class", "value": "annex-iv"}],
            "base64": {"value": encoded},
        })

    # Embed CycloneDX BOM into the AR's back-matter.resources with
    # class='cyclonedx-bom'. The trace probe writes a CycloneDX 1.5 doc
    # to `.venturalitica/runs/<run_id>/bom.json` listing the
    # ML-model + library components scanned from the trainer. The
    # platform's bom-ingestion service upserts each component as a
    # ManagedItem(ICT_THIRD_PARTY) row + AISystemManagedItemLink so
    # the SoA / DORA Art.28(9) supply-chain catalog auto-populates
    # from observed dependencies — no hand-typed inventory.
    bom_doc: dict = {}
    if run_dir is not None and (run_dir / "bom.json").exists():
        try:
            with open(run_dir / "bom.json", "r") as f:
                maybe_bom = json.load(f)
            if isinstance(maybe_bom, dict) and isinstance(maybe_bom.get("components"), list):
                bom_doc = maybe_bom
        except (json.JSONDecodeError, OSError):
            pass
    if bom_doc:
        import base64 as _b64
        import uuid as _uuid
        ar_root = ar_doc.get("assessment-results", ar_doc)
        back_matter = ar_root.setdefault("back-matter", {})
        resources = back_matter.setdefault("resources", [])
        # Drop any prior cyclonedx-bom resource so re-pushes overwrite cleanly.
        resources[:] = [
            r for r in resources
            if not any(
                isinstance(p, dict) and p.get("name") == "class" and p.get("value") == "cyclonedx-bom"
                for p in (r.get("props") or [])
            )
        ]
        encoded_bom = _b64.b64encode(
            json.dumps(bom_doc, ensure_ascii=False).encode("utf-8")
        ).decode("ascii")
        resources.append({
            "uuid": str(_uuid.uuid4()),
            "title": "CycloneDX SBOM (DORA Art.28(9) supply-chain inventory)",
            "description": (
                "CycloneDX 1.5 SBOM emitted by the trace probe scanner. The "
                "platform's bom-ingestion service upserts each component as a "
                "ManagedItem(ICT_THIRD_PARTY) and links it to the pushing "
                "AISystem via AISystemManagedItemLink(DEPENDS_ON)."
            ),
            "props": [{"name": "class", "value": "cyclonedx-bom"}],
            "base64": {"value": encoded_bom},
        })

    payload: dict = {"assessment_results": ar_doc}
    if external_run_url:
        payload["external_run_url"] = external_run_url
    if treatment_id:
        payload["treatment_id"] = treatment_id

    try:
        response = requests.post(
            f"{SAAS_URL}/api/push",
            headers={"Authorization": f"Bearer {creds['key']}"},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        console.print(
            "[bold green]✓ Handshake complete. OSCAL assessment-results pushed.[/bold green]"
        )
        console.print(f"  Source: {ar_path}")
        console.print(
            f"  SaaS Job ID: {data.get('job_id') or data.get('audit_trace_id')}"
        )

        try:
            from ..telemetry import telemetry
            ar_root = ar_doc.get("assessment-results", ar_doc)
            primary = (ar_root.get("results") or [{}])[0]
            telemetry.capture("sdk_push_completed", {
                "ar_uuid": ar_root.get("uuid"),
                "observation_count": len(primary.get("observations", [])),
                "finding_count": len(primary.get("findings", [])),
            })
        except Exception:
            pass

    except Exception as e:
        console.print(f"[bold red]Upload failed:[/bold red] {e}")
        # Check if it's an HTTP error with response
        response = getattr(e, "response", None)
        if response is not None:
            try:
                error_data = response.json()
                console.print(
                    f"[red]Error details: {json.dumps(error_data, indent=2)}[/red]"
                )
            except Exception:
                console.print(f"[red]Raw server response: {response.text}[/red]")
        raise typer.Exit(code=1)
