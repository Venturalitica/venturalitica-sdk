import json
from typing import Optional

import requests
import typer

from ..telemetry import track_command
from .common import SAAS_URL, app, console, get_config_path


@app.command()
@track_command("login")
def login(system_id: str):
    """
    [Legacy] Authenticates with the Venturalítica SaaS for a specific AI
    System using the per-system AISystemAPIKey flow. Requires an active
    SaaS session cookie (works only when run from the same host as a
    logged-in browser). New deployments should prefer ``login-pat``.
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
            json.dump({**data, "kind": "ai-system-key"}, f)

        console.print(
            f"[bold green]✓ Login successful for {data.get('aiSystemName')}[/bold green]"
        )
        console.print(f"Key stored in: {creds_path}")

    except Exception as e:
        console.print(f"[bold red]Login failed:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command("login-pat")
@track_command("login_pat")
def login_pat(
    key: str = typer.Option(
        ...,
        "--key",
        help="Personal access token in the form vl_pat_xxxxx (generate at /profile/tokens).",
    ),
    org: Optional[str] = typer.Option(
        None,
        "--org",
        help="Default organization slug. Pull/push commands use this when --system is omitted.",
    ),
    default_system: Optional[str] = typer.Option(
        None,
        "--default-system",
        help="Default AI system slug for push/pull when --system is not provided.",
    ),
):
    """
    Stores a Personal Access Token (PAT) for SDK auth. The token is
    sent on every push/pull as ``Authorization: Bearer <key>``.

    Generate a token from the SaaS UI at /profile/tokens. PATs are
    user+org scoped and carry per-system permissions via scopes; one
    token can cover any number of AI systems within a single org.
    """
    if not key.startswith("vl_pat_"):
        console.print(
            "[bold red]Invalid PAT format.[/bold red] Expected a token starting with"
            " 'vl_pat_'. Generate one at /profile/tokens in the SaaS UI."
        )
        raise typer.Exit(code=1)

    creds_path = get_config_path("credentials.json")
    payload = {
        "key": key,
        "kind": "pat",
    }
    if org:
        payload["org"] = org
    if default_system:
        payload["default_system"] = default_system

    with open(creds_path, "w") as f:
        json.dump(payload, f)

    console.print(
        f"[bold green]✓ PAT stored.[/bold green] Org: {org or '(unset)'}, "
        f"default system: {default_system or '(none)'}"
    )
    console.print(f"Key stored in: {creds_path}")
