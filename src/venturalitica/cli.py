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
def ui():
    """
    Launches the Venturalítica Local Compliance Dashboard.
    """
    console.print("[bold green]🚀 Launching Venturalítica UI...[/bold green]")

    # Path to dashboard/main.py
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard", "main.py")

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
        # Check trace for BOM
        trace_dir = ".venturalitica"
        if os.path.exists(trace_dir):
             for f in os.listdir(trace_dir):
                if f.startswith("trace_") and f.endswith(".json"):
                    try:
                        with open(os.path.join(trace_dir, f), 'r') as tf:
                            trace = json.load(tf)
                            if "bom" in trace:
                                bom = trace["bom"]
                                console.print(f"  ✓ Loaded BOM from trace: {f}")
                                break
                    except: pass
        if not bom:
             console.print(
                 "[yellow]Warning:[/yellow] No BOM found in 'bom.json' or recent traces."
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
