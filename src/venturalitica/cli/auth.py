import json

import requests
import typer

from ..telemetry import track_command
from .common import SAAS_URL, app, console, get_config_path


@app.command()
@track_command("login")
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
