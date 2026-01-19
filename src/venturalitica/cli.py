import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command()
def scan(target: str = "."):
    """
    Scans the target directory to generate a CycloneDX ML-BOM.
    """
    console.print(f"[bold green]Scanning target:[/bold green] {target}")
    
    from venturalitica.scanner import BOMScanner
    import os
    
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
def ui():
    """
    Launches the Local Compliance Dashboard.
    """
    console.print("[bold blue]Launching Dashboard...[/bold blue]")
    
    import subprocess
    import sys
    import os
    
    # Get path to dashboard.py relative to this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dashboard_path = os.path.join(current_dir, "dashboard.py")
    
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", dashboard_path,
            "--server.headless", "true",
            "--server.fileWatcherType", "none"
        ], check=True)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Dashboard stopped.[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red]Error launching dashboard:[/bold red] {e}")

if __name__ == "__main__":
    app()
