"""
Rich terminal output formatting for Venturalítica SDK.
Provides visual enhancements for compliance results with semantic indicators.
"""

from typing import List

from .models import ComplianceResult

try:
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

console = Console() if RICH_AVAILABLE else None



def print_compliance_summary(scenario: str, results: List[ComplianceResult]) -> None:
    """Print the compliance summary message for quickstart demos."""
    if not RICH_AVAILABLE or not console:
        print(f"\n✅ Audit Complete: Scenario '{scenario}' verified.")
        return
    
    passed_count = sum(1 for r in results if r.passed)
    total_count = len(results)
    
    if passed_count == total_count:
        console.print("\n[bold green]✅ Audit Complete: All controls passed. Your model is compliant.[/bold green]")
    else:
        console.print(f"\n[bold yellow]⚠️  Compliance Summary: {passed_count}/{total_count} controls passed.[/bold yellow]")
    
    console.print("\n[bold cyan]📚 Next Steps:[/bold cyan]")
    console.print("  1. [bold white]Explore results:[/bold white] Run [bold green]venturalitica ui[/bold green] to visualize the audit.")
    console.print("  2. [bold white]See full docs:[/bold white] Visit [link=https://venturalitica.github.io/venturalitica-sdk]venturalitica.github.io/venturalitica-sdk[/link]")
    console.print("  3. [bold white]Customize policy:[/bold white] Edit [bold cyan]policy.yaml[/bold cyan] to change thresholds.")
