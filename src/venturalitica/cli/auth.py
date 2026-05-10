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
        help="Organization slug the token belongs to.",
    ),
    system: Optional[str] = typer.Option(
        None,
        "--system",
        help=(
            "AI system slug the token targets. Recorded so push/pull "
            "have a default target without explicit flags. The SaaS "
            "auto-derives this from the token's scopes when omitted, "
            "but stamping it locally lets the SDK fail fast with a "
            "clear message if the user typos a system name."
        ),
    ),
):
    """
    Stores a Personal Access Token (PAT) for SDK auth. The token is
    sent on every push/pull as ``Authorization: Bearer <key>``.

    Canonical model: one token == one AI system. Generate the token
    from /profile/tokens in the SaaS UI; the dialog binds it to a
    single AI system via the `ai:system:<slug>` scope so push and
    pull can run with no extra flags.
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
    if system:
        # Stored under both keys so existing readers (sync.py default
        # fallback) and human-friendly inspection both work.
        payload["system"] = system
        payload["default_system"] = system

    with open(creds_path, "w") as f:
        json.dump(payload, f)

    console.print(
        f"[bold green]✓ PAT stored.[/bold green] Org: {org or '(unset)'}, "
        f"system: {system or '(auto-derived from token scopes)'}"
    )
    console.print(f"Key stored in: {creds_path}")
