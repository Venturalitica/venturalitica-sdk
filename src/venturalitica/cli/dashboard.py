"""`vl ui` — launch the local Streamlit compliance dashboard.

The dashboard ships behind the optional `\[dashboard]` extra to keep the base
SDK install lightweight. This entry point fails loudly with installation
guidance instead of letting `subprocess.run(["streamlit", ...])` blow up with
an opaque FileNotFoundError when the extra isn't installed.
"""

import importlib.util
import os
import subprocess
import sys

import typer

from ..telemetry import track_command
from .common import app, console


@app.command()
@track_command("ui")
def ui(
    port: int = typer.Option(8501, "--port", "-p", help="Port to bind Streamlit to."),
    host: str = typer.Option("localhost", "--host", help="Host/interface to bind Streamlit to."),
    headless: bool = typer.Option(
        False, "--headless", help="Skip opening a browser tab (useful in CI/Docker)."
    ),
):
    """Launches the Venturalítica Local Compliance Dashboard.

    Requires the optional \[dashboard] extra. Install with:

        pip install 'venturalitica\[dashboard]'
    """
    console.print("[bold green]🚀 Launching Venturalítica UI...[/bold green]")

    # Preflight: streamlit must be importable. Without this the subprocess
    # call below crashes with a confusing FileNotFoundError that hides the
    # real issue (missing optional extra).
    if importlib.util.find_spec("streamlit") is None:
        console.print(
            "[bold red]Dashboard dependency missing.[/bold red]\n"
            "[yellow]The Streamlit dashboard ships behind the optional "
            "\[dashboard] extra. Install it with:[/yellow]\n\n"
            "    pip install 'venturalitica\[dashboard]'\n\n"
            "[dim]Or, with uv:[/dim]\n"
            "    uv add 'venturalitica\[dashboard]'"
        )
        raise typer.Exit(code=1)

    base_dir = os.path.dirname(os.path.dirname(__file__))  # venturalitica/
    dashboard_path = os.path.join(base_dir, "dashboard", "main.py")

    if not os.path.exists(dashboard_path):
        console.print(
            f"[bold red]Error:[/bold red] Dashboard file not found at {dashboard_path}"
        )
        raise typer.Exit(code=1)

    # Use `sys.executable -m streamlit` so the dashboard always runs against
    # the interpreter that resolved the import — robust across venvs, conda,
    # Docker, and uv-managed environments where bare `streamlit` may not be
    # on PATH even when the package is installed.
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        dashboard_path,
        "--server.port",
        str(port),
        "--server.address",
        host,
    ]
    if headless:
        cmd += ["--server.headless", "true"]

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Failed to launch dashboard:[/bold red] {e}")
        raise typer.Exit(code=1)
