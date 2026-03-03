import json
import os
from typing import Optional

import requests
import typer

from ..telemetry import track_command
from .common import SAAS_URL, app, console, get_config_path


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

    # 3. Load Annex IV if exists
    annex_iv = {}
    if os.path.exists("Annex_IV.md"):
        # Simple parser for structured fields
        with open("Annex_IV.md", "r") as f:
            lines = f.readlines()
            for line in lines:
                if "Intended Purpose:" in line:
                    annex_iv["intended_purpose"] = line.split(":", 1)[1].strip()
                elif "Hardware:" in line:
                    annex_iv["hardware"] = line.split(":", 1)[1].strip()

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

    # Generate the bundle payload in-memory (no file required)
    try:
        payload = _create_bundle_payload()
    except Exception as e:
        console.print(f"[bold red]Failed to prepare bundle:[/bold red] {e}")
        raise typer.Exit(code=1)

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
            "[bold green]✓ Handshake complete. Results successfully pushed.[/bold green]"
        )
        console.print(
            f"  SaaS Job ID: {data.get('job_id') or data.get('audit_trace_id')}"
        )

        try:
            from ..telemetry import telemetry
            telemetry.capture("sdk_push_completed", {
                "has_metrics": bool(payload.get("metrics")),
                "has_bom": bool(payload.get("bom")),
                "artifact_count": len(payload.get("artifacts", [])),
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
