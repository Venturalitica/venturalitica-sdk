import json
import os
from typing import Optional

import requests
import typer
import yaml

from ..telemetry import track_command
from .common import SAAS_URL, app, console, get_config_path


@app.command()
@track_command("pull")
def pull(
    system: Optional[str] = typer.Option(
        None,
        "--system",
        help=(
            "AI system slug to pull the assessment-plan for. Required when "
            "authenticating with a PAT (vl_pat_…); legacy AISystemAPIKey is "
            "already bound to one system so this can be omitted. Falls back "
            "to credentials.json default_system when not provided."
        ),
    ),
):
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

    # 1-token-1-system tokens carry the target inside their scope; the
    # SaaS auto-derives it. Multi-system tokens (rare) require explicit
    # disambiguation — fall through and let the SaaS surface the 400
    # with the granted scopes for clarity.
    target_system = system or creds.get("default_system")

    try:
        # Pull the canonical OSCAL assessment-plan (single dialect — see
        # docs/contracts/oscal-assessment-plan-v1.md). No more split
        # model/data SSPs: one document carries every implemented-
        # requirement tagged with lifecycle_phase + target_type so the
        # SDK can filter locally for each consumer.
        url = f"{SAAS_URL}/api/pull?format=oscal"
        if target_system:
            url += f"&system={target_system}"
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {creds['key']}"},
        )
        response.raise_for_status()
        oscal_doc = response.json()

        plan = oscal_doc.get("assessment-plan")
        if not plan:
            raise ValueError(
                "SaaS did not return an assessment-plan root — expected the "
                "canonical OSCAL dialect per docs/contracts/oscal-assessment-plan-v1.md. "
                "Check the SaaS version (>= v0.6.0)."
            )

        impls = plan.get("control-implementations", []) or []
        all_requirements = [
            req
            for impl in impls
            for req in (impl.get("implemented-requirements", []) or [])
        ]

        # Persist one full policy file (the source of truth)…
        with open("assessment_plan.oscal.yaml", "w") as f:
            yaml.dump(oscal_doc, f, sort_keys=False)
        console.print(
            f"  ✓ Saved assessment_plan.oscal.yaml ({len(all_requirements)} requirement(s))"
        )

        # …and cache the canonical JSON at .venturalitica/policy.oscal.json
        # so monitor() + annex-iv can read the tenant binding props
        # (ai-system-uuid, ai-system-version-uuid) without re-parsing YAML.
        # This is the path POLICY_PATH_CANDIDATES[0] uses everywhere.
        os.makedirs(".venturalitica", exist_ok=True)
        with open(".venturalitica/policy.oscal.json", "w") as f:
            json.dump(oscal_doc, f, indent=2)

        # …and emit two backwards-compatible filtered views keyed on
        # target_type so legacy trainers that still read model_policy /
        # data_policy paths keep working for one release.
        def _requirements_by_target(target: str):
            out = []
            for req in all_requirements:
                for p in req.get("props", []) or []:
                    if p.get("name") == "target_type" and p.get("value") in (
                        target,
                        "system_and_dataset" if target == "system" else None,
                    ):
                        out.append(req)
                        break
            return out

        model_reqs = _requirements_by_target("system")
        data_reqs = [
            req
            for req in all_requirements
            if any(
                p.get("name") == "target_type" and p.get("value") in ("dataset", "system_and_dataset")
                for p in req.get("props", []) or []
            )
        ]

        def _dump_view(path: str, requirements):
            wrapper = {
                "assessment-plan": {
                    **plan,
                    "control-implementations": [
                        {
                            **(impls[0] if impls else {"component-uuid": "derived"}),
                            "implemented-requirements": requirements,
                        }
                    ],
                }
            }
            with open(path, "w") as f:
                yaml.dump(wrapper, f, sort_keys=False)

        _dump_view("model_policy.oscal.yaml", model_reqs)
        _dump_view("data_policy.oscal.yaml", data_reqs)
        console.print(
            f"  ✓ Filtered views: model_policy.oscal.yaml ({len(model_reqs)}) + "
            f"data_policy.oscal.yaml ({len(data_reqs)})"
        )

        # Log risk binding status from the new dialect. Each requirement
        # carries a `risk_id` prop that points to the IdentifiedRisk.
        risks_seen = set()
        for req in all_requirements:
            for p in req.get("props", []) or []:
                if p.get("name") == "risk_id" and p.get("value"):
                    risks_seen.add(p["value"])
        console.print(
            f"  Risks referenced by assessment-plan: {len(risks_seen)}"
        )

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
        # Check for AISystemVersion object (new schema) or fallback to 'system'.
        # Both fields can be explicitly null on the wire — coerce to {} so
        # downstream .get() calls don't crash when the AI System has no
        # versions yet.
        system_version = (
            config_data.get("aiSystemVersion")
            or config_data.get("system")
            or {}
        )
        policy_info = config_data.get("policy") or {}
        
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
