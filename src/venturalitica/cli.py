import typer
from rich.console import Console
from typing import Optional
import os
import json
import webbrowser
from venturalitica.scanner import BOMScanner
from venturalitica.client import VenturaliticaClient, save_credentials, load_credentials

app = typer.Typer()
console = Console()

@app.command()
def scan(target: str = "."):
    """
    Scans the target directory to generate a CycloneDX ML-BOM.
    """
    console.print(f"[bold green]Scanning target:[/bold green] {target}")
    
    try:
        scanner = BOMScanner(target)
        output = scanner.scan()
        
        output_file = os.path.join(target, "bom.json")
        with open(output_file, "w") as f:
            f.write(output)
            
        console.print(f"[bold green]✓ BOM generated:[/bold green] {output_file}")
        console.print(f"Found {len(scanner.bom.components)} components.")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

@app.command()
def login(ai_system_id: Optional[str] = typer.Argument(None)):
    """
    Authenticates the CLI via OAuth 2.0 Device Flow.
    The user selects the AI System in the web browser.
    """
    import time
    client = VenturaliticaClient()
    
    try:
        console.print("[bold blue]Initiating Device Authentication...[/bold blue]")
        device_code_data = client.initiate_device_flow()
        
        user_code = device_code_data["userCode"]
        verification_uri = device_code_data["verificationUri"]
        interval = device_code_data.get("interval", 5)
        
        console.print(f"\n[bold]1. Go to:[/bold] [link={verification_uri}]{verification_uri}[/link]")
        console.print(f"[bold]2. Enter the code:[/bold] [bold green]{user_code}[/bold green]\n")
        
        # Open browser automatically
        webbrowser.open(verification_uri)
        
        console.print("[dim]Waiting for authorization and system selection...[/dim]")
        
        device_code = device_code_data["deviceCode"]
        while True:
            try:
                token_data = client.poll_device_token(device_code)
                if token_data:
                    # Success!
                    session = token_data.get("session", {})
                    user = token_data.get("user", {})
                    
                    # Store session
                    save_credentials(
                        session_token=session.get("token"),
                        ai_system_name=session.get("scope", "Unknown System")
                    )
                    
                    console.print(f"\n[bold green]✓ Logged in successfully![/bold green]")
                    console.print(f"  User: {user.get('email')}")
                    console.print(f"  Scope: {session.get('scope')}")
                    break
            except Exception as e:
                if "authorization_pending" not in str(e):
                    raise e
            
            time.sleep(interval)
            
    except Exception as e:
        console.print(f"[bold red]Error during login:[/bold red] {e}")
        raise typer.Exit(code=1)

@app.command()
def pull(format: Optional[str] = typer.Option(None, "--format", help="Export format (e.g. 'oscal')")):
    """
    Fetches governance configuration from the SaaS.
    """
    client = VenturaliticaClient()
    
    if not client.is_authenticated():
        console.print("[bold red]Error:[/bold red] Not authenticated. Run 'venturalitica login' first.")
        raise typer.Exit(code=1)
    
    console.print(f"[bold blue]Pulling governance configuration{' (format: ' + format + ')' if format else ''}...[/bold blue]")
    
    try:
        config = client.pull_config(format=format)
        
        os.makedirs(".venturalitica", exist_ok=True)
        
        filename = "oscal.json" if format == "oscal" else "config.json"
        config_path = f".venturalitica/{filename}"
        
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
            
        console.print(f"[bold green]✓ Configuration synced:[/bold green] {config_path}")
        
        if format != 'oscal':
            if config.get('aiSystem'):
                console.print(f"  AI System: {config['aiSystem'].get('name')}")
            if config.get('traceId'):
                # Store trace_id in state for later push
                state_path = ".venturalitica/state.json"
                with open(state_path, "w") as f:
                    json.dump({"last_trace_id": config['traceId']}, f, indent=2)

    except Exception as e:
        console.print(f"[bold red]Error pulling configuration:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def push():
    """
    Pushes evaluation results (BOM and metrics) to the SaaS for reconciliation.
    Requires prior authentication via 'venturalitica login'.
    """
    client = VenturaliticaClient()
    
    if not client.is_authenticated():
        console.print("[bold red]Error:[/bold red] Not authenticated. Run 'venturalitica login <ai_system_id>' first.")
        raise typer.Exit(code=1)

    console.print("[bold blue]Pushing results...[/bold blue]")
    
    try:
        # Load BOM
        if not os.path.exists("bom.json"):
            console.print("[bold yellow]Warning:[/bold yellow] bom.json not found. Generating a fresh one...")
            scan(".")
            
        with open("bom.json", "r") as f:
            bom = json.load(f)
            
        # Load Metrics if available
        metrics = []
        if os.path.exists(".venturalitica/results.json"):
            with open(".venturalitica/results.json", "r") as f:
                metrics = json.load(f)
            console.print(f"[dim]Loaded {len(metrics)} cached metrics.[/dim]")

        payload = {
            "bom": bom,
            "metrics": metrics
        }
        
        result = client.push_results(payload)
        console.print(f"[bold green]✓ Results pushed successfully![/bold green]")
        console.print(f"  AI System: {result.get('aiSystem', 'N/A')}")
        console.print(f"  Version: {result.get('version_id', 'N/A')}")
        console.print(f"  Metrics Recorded: {result.get('metrics_count', 0)}")
        
    except Exception as e:
        console.print(f"[bold red]Error pushing results:[/bold red] {e}")
        raise typer.Exit(code=1)

@app.command()
def whoami():
    """
    Shows the currently authenticated AI System.
    """
    creds = load_credentials()
    if not creds:
        console.print("[bold yellow]Not logged in.[/bold yellow]")
        console.print("Run 'venturalitica login <ai_system_id>' to authenticate.")
        raise typer.Exit(code=1)
        
    console.print("[bold blue]Current Credentials:[/bold blue]")
    console.print(f"  AI System: {creds.get('ai_system_name', 'Unknown')}")
    console.print(f"  Expires: {creds.get('expires_at', 'N/A')}")

@app.command()
def logout():
    """
    Clears stored credentials.
    """
    from venturalitica.client import CREDENTIALS_FILE
    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()
        console.print("[bold green]✓ Logged out successfully.[/bold green]")
    else:
        console.print("[dim]No credentials found.[/dim]")

@app.command()
def ui():
    """
    Launches the Venturalitica Local Compliance Dashboard.
    """
    console.print("[bold green]🚀 Launching Venturalitica UI...[/bold green]")
    
    # Path to dashboard.py
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.py")
    
    if not os.path.exists(dashboard_path):
        console.print(f"[bold red]Error:[/bold red] Dashboard file not found at {dashboard_path}")
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
    console.print(f"[bold blue]📄 Generating Technical Documentation:[/bold blue] {output}")
    
    # 1. Load context
    bom = {}
    if os.path.exists("bom.json"):
        with open("bom.json", "r") as f:
            bom = json.load(f)
    else:
        console.print("[yellow]Warning:[/yellow] bom.json not found. Run 'venturalitica scan' first.")
        
    results = []
    if os.path.exists(".venturalitica/results.json"):
        with open(".venturalitica/results.json", "r") as f:
            results = json.load(f)
            
    # 2. Generate Draft (reusing logic from dashboard but simplified for CLI)
    components = bom.get('components', [])
    model_names = [c['name'] for c in components if c['type'] == 'machine-learning-model']
    passed_count = sum(1 for r in results if r.get('passed')) if results else 0
    total_count = len(results) if results else 0
    
    content = f"""# EU AI Act: Annex IV Technical Documentation
Generated by Venturalitica CLI v0.1.0

## 1. General description
**Intended Purpose:** [PENDING USER INPUT]
**Hardware:** [PENDING USER INPUT]

## 2. Technical implementation
This AI System incorporates {len(components)} technical modules, including: {', '.join(model_names) if model_names else 'standard architectures'}.
The system leverages local governance tracking for automated compliance oversight.

## 3. Risk management system
The system is integrated with the Venturalitica Risk Management framework.
Current validation status: {passed_count}/{total_count} controls passing in the latest local audit.
"""
    
    try:
        with open(output, "w") as f:
            f.write(content)
        console.print(f"[bold green]✓ Documentation draft created:[/bold green] {output}")
    except Exception as e:
        console.print(f"[bold red]Error generating documentation:[/bold red] {e}")

if __name__ == "__main__":
    app()
