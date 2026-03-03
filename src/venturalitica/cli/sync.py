import json
import os

import requests
import typer
import yaml

from ..telemetry import track_command
from .common import SAAS_URL, app, console, get_config_path


@app.command()
@track_command("pull")
def pull():
    """
    Pulls assurance policies and objectives from the SaaS.
    """
    console.print("[bold blue]📥 Pulling assurance configuration...[/bold blue]")

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

        # [Annex IV.1] Sync System Description
        # Check for AISystemVersion object (new schema) or fallback to 'system'
        system_version = config_data.get("aiSystemVersion", config_data.get("system", {}))
        policy_info = config_data.get("policy", {})
        
        # Mapping from SaaS (CamelCase or SnakeCase) to Local SystemDescription
        sys_desc = {
            "name": system_version.get("name", policy_info.get("name", "")),
            "version": system_version.get("version", "1.0.0"),
            "provider_name": system_version.get("providerName", system_version.get("provider", "")),
            "intended_purpose": system_version.get("intendedPurpose", system_version.get("description", policy_info.get("description", ""))),
            
            # Detailed Annex IV.1 Fields
            "interaction_description": system_version.get("interactionDescription", system_version.get("interaction_description", "")),
            "software_dependencies": system_version.get("softwareDependencies", system_version.get("software_dependencies", "")),
            "market_placement_form": system_version.get("marketPlacementForm", system_version.get("market_placement_form", "")),
            "hardware_description": system_version.get("hardwareDescription", system_version.get("hardware_description", "")),
            "external_features": system_version.get("externalFeatures", system_version.get("external_features", "")),
            "ui_description": system_version.get("uiDescription", system_version.get("ui_description", "")),
            "instructions_for_use": system_version.get("instructionsForUse", system_version.get("instructions_for_use", ""))
        }
        
        # Only write if we have meaningful data
        if sys_desc["name"] or sys_desc["intended_purpose"]:
            with open("system_description.yaml", "w") as f:
                yaml.dump(sys_desc, f, sort_keys=False)
            console.print("  [green]✓ Synced system_description.yaml from SaaS[/green]")
        
        console.print(
            "[bold green]✓ Assurance configuration synchronized.[/bold green]"
        )
        policy_data = config_data.get("policy") or {}
        console.print(f"  Policy: {policy_data.get('name', 'N/A')}")
        console.print(f"  Objectives: {len(config_data.get('objectives', []))}")
    except Exception as e:
        console.print(f"[bold red]Sync failed:[/bold red] {e}")
        raise typer.Exit(code=1)
