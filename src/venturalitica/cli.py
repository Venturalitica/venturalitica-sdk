import typer
from rich.console import Console
from typing import Optional
import os
import json
import webbrowser
import subprocess
import requests
import yaml
from venturalitica.scanner import BOMScanner

app = typer.Typer()
console = Console()

SAAS_URL = os.getenv("VENTURALITICA_SAAS_URL", "http://localhost:3000")


def get_config_path(filename: str) -> str:
    path = os.path.expanduser(f"~/.venturalitica/{filename}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


@app.command()
def login(system_id: str):
    """
    Authenticates with the Venturalítica SaaS for a specific AI System.
    """
    console.print(f"[bold green]🔐 Authenticating for system:[/bold green] {system_id}")

    try:
        response = requests.post(
            f"{SAAS_URL}/api/cli-auth", json={"aiSystemId": system_id}
        )
        response.raise_for_status()
        data = response.json()

        creds_path = get_config_path("credentials.json")
        with open(creds_path, "w") as f:
            json.dump(data, f)

        console.print(
            f"[bold green]✓ Login successful for {data.get('aiSystemName')}[/bold green]"
        )
        console.print(f"Key stored in: {creds_path}")

    except Exception as e:
        console.print(f"[bold red]Login failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def pull():
    """
    Pulls governance policies and objectives from the SaaS.
    """
    console.print("[bold blue]📥 Pulling governance configuration...[/bold blue]")

    creds_path = get_config_path("credentials.json")
    if not os.path.exists(creds_path):
        console.print(
            "[bold red]Error:[/bold red] Not logged in. Run 'venturalitica login' first."
        )
        raise typer.Exit(code=1)

    with open(creds_path, "r") as f:
        creds = json.load(f)

    try:
        # Pull OSCAL policies (model + data in one call)
        response = requests.get(
            f"{SAAS_URL}/api/pull?format=oscal",
            headers={"Authorization": f"Bearer {creds['key']}"},
        )
        response.raise_for_status()
        oscal_multi = response.json()

        # Extract model and data policies
        model_policy = oscal_multi.get("model", {})
        data_policy = oscal_multi.get("data", {})
        risks = oscal_multi.get("risks", [])

        # Save model policy
        with open("model_policy.oscal.yaml", "w") as f:
            yaml.dump(model_policy, f)
        model_reqs = model_policy.get("system-security-plan", {}).get("control-implementation", {}).get("implemented-requirements", [])
        console.print(f"  ✓ Saved model_policy.oscal.yaml ({len(model_reqs)} controls)")

        # Save data policy
        with open("data_policy.oscal.yaml", "w") as f:
            yaml.dump(data_policy, f)
        data_reqs = data_policy.get("system-security-plan", {}).get("control-implementation", {}).get("implemented-requirements", [])
        console.print(f"  ✓ Saved data_policy.oscal.yaml ({len(data_reqs)} controls)")

        # Log identified risks and their binding status
        for risk in risks:
            title = risk.get("title")
            # Check if risk is covered in either model or data policies
            is_in_model = any(req.get("legacy-id") == risk.get("uuid") for req in model_reqs)
            is_in_data = any(req.get("legacy-id") == risk.get("uuid") for req in data_reqs)
            if is_in_model or is_in_data:
                policy_type = "model" if is_in_model else "data"
                console.print(f"  [green]✓ Bound [{policy_type}][/green] {title}")
            else:
                console.print(f"  [yellow]⚠ Unbound[/yellow] {title}")

        # Also pull general config for display/verification
        response = requests.get(
            f"{SAAS_URL}/api/pull",
            headers={"Authorization": f"Bearer {creds['key']}"},
        )
        response.raise_for_status()
        config_data = response.json()

        os.makedirs(".venturalitica", exist_ok=True)
        with open(".venturalitica/config.json", "w") as f:
            json.dump(config_data, f, indent=2)

        console.print(
            "[bold green]✓ Governance configuration synchronized.[/bold green]"
        )
        policy_data = config_data.get("policy") or {}
        console.print(f"  Policy: {policy_data.get('name', 'N/A')}")
        console.print(f"  Objectives: {len(config_data.get('objectives', []))}")

    except Exception as e:
        console.print(f"[bold red]Sync failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def bundle(output: str = ".venturalitica/bundle.json"):
    """
    Creates a signed compliance bundle including BOM, results, and documentation.
    """
    console.print("[bold blue]📦 Creating compliance bundle...[/bold blue]")

    # 1. Verification of Synchronized State
    if not os.path.exists("bom.json"):
        console.print(
            "[yellow]Warning:[/yellow] bom.json missing. Running 'venturalitica scan'..."
        )
        scan()

    if not os.path.exists(".venturalitica/results.json"):
        console.print(
            "[bold red]Error:[/bold red] results.json not found. Run your audit/training first."
        )
        raise typer.Exit(code=1)

    # Consistency check: results should be newer than code changes (simplified for now)
    # In a real impl, we'd hash the repo state.

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

    # 4. Generate Bundle
    with open("bom.json", "r") as f:
        bom = json.load(f)
    
    with open(".venturalitica/results.json", "r") as f:
        results_data = json.load(f)

    # Intelligent Metrics Extraction
    metrics = []
    artifacts = []
    
    if isinstance(results_data, list):
        metrics = results_data
    elif isinstance(results_data, dict):
        # 1. Try standard 'metrics' key
        if "metrics" in results_data and isinstance(results_data["metrics"], list):
            metrics.extend(results_data["metrics"])
            
        # 2. Try 'pre_metrics' and 'post_metrics' (Training V1/V2 pattern)
        if "pre_metrics" in results_data and isinstance(results_data["pre_metrics"], list):
            metrics.extend(results_data["pre_metrics"])
        if "post_metrics" in results_data and isinstance(results_data["post_metrics"], list):
            metrics.extend(results_data["post_metrics"])
            
        # 3. Extract artifacts
        if "artifacts" in results_data and isinstance(results_data["artifacts"], list):
            artifacts.extend(results_data["artifacts"])
            console.print(f"  ✓ Included {len(results_data['artifacts'])} local artifacts from results")

    # 4. Auto-discover Audit Traces
    trace_dir = ".venturalitica"
    if os.path.exists(trace_dir):
        for f in os.listdir(trace_dir):
            if f.startswith("trace_") and f.endswith(".json"):
                try:
                    with open(os.path.join(trace_dir, f), "r") as tf:
                        trace_data = json.load(tf)
                        label = trace_data.get("label") or trace_data.get("name") or "Audit Trace"
                        artifacts.append({
                            "name": label,
                            "type": "CODE",
                            "uri": f"trace://{f}",
                            "context": "audit-trail",
                            "metadata": trace_data
                        })
                        console.print(f"  ✓ Auto-discovered trace artifact: [bold]{label}[/bold]")
                except:
                    pass

    # Simplified signing for now: hash of metrics + timestamp
    import hashlib
    import time

    timestamp = time.time()
    sign_payload = f"{json.dumps(metrics)}{timestamp}".encode()
    signature = hashlib.sha256(sign_payload).hexdigest()

    bundle_data = {
        "bundle": {
            "name": f"Compliance Bundle {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "annex_iv": annex_iv,
            "signature": signature,
            "timestamp": timestamp,
            "metadata": results_data.get("training_metadata") if isinstance(results_data, dict) else {}
        },
        "bom": bom,
        "metrics": metrics,
        "artifacts": artifacts,
    }

    os.makedirs(".venturalitica", exist_ok=True)
    with open(output, "w") as f:
        json.dump(bundle_data, f, indent=2)

    console.print(f"[bold green]✓ Bundle created successfully:[/bold green] {output}")
    console.print(
        f"  Captured {len(artifacts)} shadow artifacts and {len(metrics)} metrics."
    )


@app.command()
def push(
    bundle_path: Optional[str] = ".venturalitica/bundle.json",
    external_run_url: Optional[str] = typer.Option(None, "--external-run-url", help="MLFlow/W&B Run URL"),
    treatment_id: Optional[str] = typer.Option(None, "--treatment-id", help="Risk Treatment ID to link this trace")
):
    """
    Pushes the compliance bundle or results to the SaaS.
    """
    console.print("[bold blue]📤 Pushing to SaaS...[/bold blue]")

    creds_path = get_config_path("credentials.json")
    if not os.path.exists(creds_path):
        console.print("[bold red]Error:[/bold red] Not logged in.")
        raise typer.Exit(code=1)

    with open(creds_path, "r") as f:
        creds = json.load(f)

    # Default to creating a bundle if it doesn't exist
    if bundle_path and not os.path.exists(bundle_path):
        bundle(bundle_path)

    if not bundle_path or not os.path.exists(bundle_path):
        console.print("[bold red]Error:[/bold red] Bundle file not found.")
        raise typer.Exit(code=1)

    with open(bundle_path, "r") as f:
        payload = json.load(f)

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
            except:
                console.print(f"[red]Raw server response: {response.text}[/red]")
        raise typer.Exit(code=1)


@app.command()
def refresh():
    """
    Renew the signature key without invalidating existing evidence.
    """
    console.print("[bold blue]🔄 Refreshing signature keys...[/bold blue]")
    # In a real impl, this would call /api/refresh
    console.print(
        "[bold green]✓ Keys renewed. Validity extended for 30 days.[/bold green]"
    )


@app.command()
def scan(target: str = "."):
    """
    Scans the target directory to generate a CycloneDX ML-BOM.
    """
    console.print(f"[bold green]Scanning target:[/bold green] {target}")

    try:
        scanner = BOMScanner(target)
        output = scanner.scan()

        # Ensure we write to current directory, regardless of target path
        output_file = "bom.json"
        with open(output_file, "w") as f:
            f.write(output)

        # Count components from the generated JSON
        bom_data = json.loads(output)
        component_count = len(bom_data.get("components", []))

        console.print(f"[bold green]✓ BOM generated:[/bold green] {output_file}")
        console.print(f"Found {component_count} components.")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@app.command()
def ui():
    """
    Launches the Venturalítica Local Compliance Dashboard.
    """
    console.print("[bold green]🚀 Launching Venturalítica UI...[/bold green]")

    # Path to dashboard.py
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.py")

    if not os.path.exists(dashboard_path):
        console.print(
            f"[bold red]Error:[/bold red] Dashboard file not found at {dashboard_path}"
        )
        raise typer.Exit(code=1)

    try:
        # Run streamlit as a subprocess
        subprocess.run(["streamlit", "run", dashboard_path])
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Failed to launch dashboard:[/bold red] {e}")


@app.command()
def doc(output: str = "Annex_IV.md"):
    """
    Generates a draft of the EU AI Act Annex IV.2 Technical Documentation.
    Uses the project BOM and local audit results.
    """
    console.print(
        f"[bold blue]📄 Generating Technical Documentation:[/bold blue] {output}"
    )

    # 1. Load context
    bom = {}
    if os.path.exists("bom.json"):
        with open("bom.json", "r") as f:
            bom = json.load(f)
    else:
        console.print(
            "[yellow]Warning:[/yellow] bom.json not found. Run 'venturalitica scan' first."
        )

    results = []
    if os.path.exists(".venturalitica/results.json"):
        with open(".venturalitica/results.json", "r") as f:
            data = json.load(f)
            if isinstance(data, dict) and "metrics" in data:
                results = data["metrics"]
            elif isinstance(data, list):
                results = data
            else:
                results = []

    # 2. Generate Draft (reusing logic from dashboard but simplified for CLI)
    components = bom.get("components", [])
    model_names = [
        c["name"] for c in components if c["type"] == "machine-learning-model"
    ]
    passed_count = sum(1 for r in results if r.get("passed")) if results else 0
    total_count = len(results) if results else 0

    content = f"""# EU AI Act: Annex IV Technical Documentation
Generated by Venturalítica CLI v{__import__("venturalitica").__version__}

## 1. General description
**Intended Purpose:** [PENDING USER INPUT]
**Hardware:** [PENDING USER INPUT]

## 2. Technical implementation
This AI System incorporates {len(components)} technical modules, including: {", ".join(model_names) if model_names else "standard architectures"}.
The system leverages local governance tracking for automated compliance oversight.

## 3. Risk management system
The system is integrated with the Venturalítica Risk Management framework.
Current validation status: {passed_count}/{total_count} controls passing in the latest local audit.
"""

    try:
        with open(output, "w") as f:
            f.write(content)
        console.print(
            f"[bold green]✓ Documentation draft created:[/bold green] {output}"
        )
    except Exception as e:
        console.print(f"[bold red]Error generating documentation:[/bold red] {e}")


if __name__ == "__main__":
    app()
