import os

import typer
from rich.console import Console

app = typer.Typer()
console = Console()

SAAS_URL = os.getenv("VENTURALITICA_SAAS_URL", "http://localhost:3000")

def get_config_path(filename: str) -> str:
    path = os.path.expanduser(f"~/.venturalitica/{filename}")
    dir_path = os.path.dirname(path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
        # First Run Detection
        if "VENTURALITICA_NO_ANALYTICS" not in os.environ:
             console.print(
                "[bold blue]ℹ Telemetry Notice[/bold blue]\n"
                "[dim]Venturalítica collects anonymous technical metrics to improve this tool.\n"
                "We NEVER collect your model data, datasets, or personal identifiers.\n"
                "To opt-out, set [/dim][cyan]VENTURALITICA_NO_ANALYTICS=1[/cyan][dim].\n"
                "Read our transparent privacy policy at: [link=https://venturalitica.ai/telemetry]https://venturalitica.ai/telemetry[/link][/dim]\n"
             )
    return path
