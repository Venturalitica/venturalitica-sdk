"""
Rich terminal output formatting for Venturalítica SDK.
Provides visual enhancements for compliance results with semantic indicators.
"""

from typing import List, Optional
from .models import ComplianceResult

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

console = Console() if RICH_AVAILABLE else None


def _get_metric_interpretation(metric_key: str, actual_value: float, threshold: float, operator: str) -> dict:
    """
    Provide semantic interpretation of metric values.
    Returns dict with interpretation, risk_level, and recommendation.
    """
    from .metrics import METRIC_METADATA
    
    metadata = METRIC_METADATA.get(metric_key, {})
    
    # Determine risk level based on metric category and value
    if metric_key in ['k_anonymity', 'l_diversity']:
        # Higher is better for privacy
        if actual_value >= threshold:
            risk = "🟢 LOW"
            interpretation = f"Excellent: {actual_value:.0f} ≥ {threshold:.0f}"
        elif actual_value >= threshold * 0.7:
            risk = "🟡 MEDIUM"
            interpretation = f"Fair: {actual_value:.0f} is close to {threshold:.0f}"
        else:
            risk = "🔴 HIGH"
            interpretation = f"Poor: {actual_value:.0f} < {threshold:.0f} (recommend ≥ {threshold:.0f})"
    
    elif metric_key in ['demographic_parity_diff', 'equal_opportunity_diff', 't_closeness']:
        # Lower is better for fairness/privacy
        if actual_value <= threshold:
            risk = "🟢 LOW"
            interpretation = f"Perfect: {actual_value:.4f} ≤ {threshold:.4f}"
        elif actual_value <= threshold * 1.5:
            risk = "🟡 MEDIUM"
            interpretation = f"Acceptable: {actual_value:.4f} is close to {threshold:.4f}"
        else:
            risk = "🔴 HIGH"
            interpretation = f"Violation: {actual_value:.4f} > {threshold:.4f} (recommend ≤ {threshold:.4f})"
    
    else:
        # Default logic
        if operator in ['<', 'lt']:
            if actual_value <= threshold:
                risk = "🟢 LOW"
                interpretation = f"Pass: {actual_value:.4f} < {threshold:.4f}"
            else:
                risk = "🔴 HIGH"
                interpretation = f"Fail: {actual_value:.4f} ≥ {threshold:.4f}"
        elif operator in ['>', 'gt']:
            if actual_value >= threshold:
                risk = "🟢 LOW"
                interpretation = f"Pass: {actual_value:.4f} > {threshold:.4f}"
            else:
                risk = "🔴 HIGH"
                interpretation = f"Fail: {actual_value:.4f} ≤ {threshold:.4f}"
        else:
            risk = "⚪ INFO"
            interpretation = f"Value: {actual_value:.4f}"
    
    return {
        "risk_level": risk,
        "interpretation": interpretation,
        "metadata": metadata
    }


def render_compliance_results(results: List[ComplianceResult], policy_name: str = "Policy") -> None:
    """
    Render compliance results with semantic indicators.
    Shows interpretable risk levels, not just pass/fail.
    """
    if not RICH_AVAILABLE or not console:
        _render_plain(results, policy_name)
        return
    
    # Header
    passed_count = sum(1 for r in results if r.passed)
    total_count = len(results)
    compliance_pct = (passed_count / total_count * 100) if total_count > 0 else 0
    
    status_emoji = "✅" if passed_count == total_count else "⚠️" if passed_count > 0 else "❌"
    header_text = f"{status_emoji} Compliance Audit: {passed_count}/{total_count} passed ({compliance_pct:.0f}%)"
    
    console.print(Panel.fit(
        header_text,
        style="bold green" if passed_count == total_count else "bold yellow" if passed_count > 0 else "bold red",
        title=f"🛡️  {policy_name}"
    ))
    
    # Results table with semantic indicators
    table = Table(show_header=True, header_style="bold magenta", show_lines=False)
    table.add_column("Control", style="cyan", no_wrap=True, width=15)
    table.add_column("Metric", style="white", width=25)
    table.add_column("Value", justify="right", style="yellow", width=12)
    table.add_column("Interpretation", width=35)
    table.add_column("Risk", justify="center", width=10)
    
    for res in results:
        try:
            interp_info = _get_metric_interpretation(
                res.metric_key, 
                res.actual_value, 
                res.threshold, 
                res.operator
            )
            risk_level = interp_info["risk_level"]
            interpretation = interp_info["interpretation"]
        except Exception as e:
            risk_level = "⚪ INFO"
            interpretation = f"Value: {res.actual_value:.4f} {res.operator} {res.threshold}"
        
        table.add_row(
            res.control_id,
            res.metric_key,
            f"{res.actual_value:.4f}",
            interpretation,
            risk_level
        )
    
    console.print(table)
    
    # Recommendations based on failures
    failed_results = [r for r in results if not r.passed]
    if failed_results:
        console.print("\n[bold yellow]⚠️  Recommendations:[/bold yellow]")
        for r in failed_results:
            console.print(f"  • [{r.control_id}] Review '{r.metric_key}' calculation")
            console.print(f"    💡 Did you mean? Check your data mapping and policy configuration")
        console.print("\n📖 Links:")
        console.print("  • Fairness metrics: https://fairlearn.org/main/user_guide/")
        console.print("  • Privacy metrics: https://en.wikipedia.org/wiki/K-anonymity")


def _render_plain(results: List[ComplianceResult], policy_name: str) -> None:
    """Fallback plain text rendering with semantic indicators."""
    passed_count = sum(1 for r in results if r.passed)
    total_count = len(results)
    
    print(f"\n{'='*80}")
    print(f"  🛡️  {policy_name}")
    print(f"  Compliance: {passed_count}/{total_count} passed")
    print(f"{'='*80}")
    
    for r in results:
        try:
            interp_info = _get_metric_interpretation(
                r.metric_key, 
                r.actual_value, 
                r.threshold, 
                r.operator
            )
            risk_level = interp_info["risk_level"]
            interpretation = interp_info["interpretation"]
        except:
            risk_level = "⚪"
            interpretation = f"{r.actual_value:.4f} {r.operator} {r.threshold}"
        
        status = "✓" if r.passed else "✗"
        print(f"  {status} [{r.control_id:15}] {interpretation}")
        print(f"     Risk: {risk_level}")
    
    print(f"{'='*80}\n")


def print_aha_moment(scenario: str, results: List[ComplianceResult]) -> None:
    """Print the 'Aha! Moment' message for quickstart demos."""
    if not RICH_AVAILABLE or not console:
        print(f"\n🎉 Aha! Moment: Scenario '{scenario}' completed!")
        return
    
    passed_count = sum(1 for r in results if r.passed)
    total_count = len(results)
    
    if passed_count == total_count:
        console.print("\n[bold green]🎉 Aha! Moment: All controls passed! Your model is compliant.[/bold green]")
    else:
        console.print(f"\n[bold yellow]⚠️  Compliance Check: {passed_count}/{total_count} controls passed.[/bold yellow]")
    
    console.print("\n[bold cyan]📚 Next Steps:[/bold cyan]")
    console.print("  1. [cyan]Modify the policy:[/cyan] Experiment with different thresholds")
    console.print("  2. [cyan]See training code:[/cyan] Open 01_with_training.py")
    console.print("  3. [cyan]Export report:[/cyan] vl.export(results, 'report.html')")
