import os
import subprocess

import typer

from ..telemetry import track_command
from .common import app, console


@app.command()
@track_command("ui")
def ui():
    """
    Launches the Venturalítica Local Compliance Dashboard.
    """
    console.print("[bold green]🚀 Launching Venturalítica UI...[/bold green]")

    # Path to dashboard/main.py
    # We need to go up one level from this file (cli/dashboard.py) to venturalitica/dashboard/main.py
    # But imported as package, __file__ is inside cli/
    base_dir = os.path.dirname(os.path.dirname(__file__)) # venturalitica/
    dashboard_path = os.path.join(base_dir, "dashboard", "main.py")

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
