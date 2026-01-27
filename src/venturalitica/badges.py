"""
Badge generator for fairness compliance reports.

Generates SVG badges for README inclusion:
- Compliance status (PASS/FAIL)
- Audit date
- Custom metrics

Usage:
    python -c "from venturalitica.badges import generate_compliance_badge; 
               generate_compliance_badge('passing', 'loan', '2026-01-22')"
"""

from pathlib import Path
from typing import Literal, Union, List, Any


def generate_compliance_badge(
    status: Union[Literal['passing', 'failing', 'unknown'], List[Any]],
    policy_name: str = 'fairness',
    date: str = '',
    output_path: Union[str, Path] = Path('badge.svg')
) -> Path:
    """
    Generate an SVG badge for compliance status.
    
    Args:
        status: 'passing' (green), 'failing' (red), 'unknown' (gray)
               OR a list of ComplianceResult objects.
        policy_name: Name of policy checked
        date: ISO date string
        output_path: Where to save the SVG
    """
    if isinstance(output_path, str):
        output_path = Path(output_path)

    # If status is a list of results, determine the overall status
    if isinstance(status, list):
        if not status:
            final_status = 'unknown'
        elif all(getattr(r, 'passed', False) for r in status):
            final_status = 'passing'
        else:
            final_status = 'failing'
    else:
        final_status = status
    
    colors = {
        'passing': '#28a745',  # Green
        'failing': '#dc3545',  # Red
        'unknown': '#6c757d',   # Gray
    }
    
    color = colors.get(final_status, colors['unknown'])
    status_text = 'PASSING' if final_status == 'passing' else ('FAILING' if final_status == 'failing' else 'UNKNOWN')
    
    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="180" height="20" role="img" aria-label="Compliance: {status_text}">
  <title>Compliance: {status_text}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb"/>
    <stop offset="1" stop-color="#999"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="180" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="126" height="20" fill="#555"/>
    <rect x="126" width="54" height="20" fill="{color}"/>
    <rect width="180" height="20" fill="url(#s)" opacity="0.1"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="11">
    <text aria-hidden="true" x="63" y="15" fill="#010101" fill-opacity="0.3" transform="scale(.1)" textLength="1160">Venturalítica Audit: {policy_name}</text>
    <text x="63" y="14" transform="scale(.1)" fill="#fff" textLength="1160">Venturalítica Audit: {policy_name}</text>
    <text aria-hidden="true" x="151.5" y="15" fill="#010101" fill-opacity="0.3" transform="scale(.1)" textLength="440">{status_text}</text>
    <text x="151.5" y="14" transform="scale(.1)" fill="#fff" textLength="440">{status_text}</text>
  </g>
</svg>
'''
    
    output_path.write_text(svg_content)
    return output_path


def generate_metric_badge(
    metric_name: str,
    value: float,
    threshold: float,
    output_path: Path = Path('metric_badge.svg')
) -> Path:
    """
    Generate a badge for a specific metric value.
    
    Args:
        metric_name: e.g., 'Demographic Parity'
        value: Actual metric value
        threshold: Threshold value
        output_path: Where to save the SVG
    
    Returns:
        Path to generated badge
    """
    
    # Determine color based on comparison
    if value <= threshold:
        color = '#28a745'  # Green
        status = '✓'
    else:
        color = '#dc3545'  # Red
        status = '✗'
    
    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="240" height="20" role="img" aria-label="{metric_name}: {value:.4f}">
  <title>{metric_name}: {value:.4f}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb"/>
    <stop offset="1" stop-color="#999"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="240" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="160" height="20" fill="#555"/>
    <rect x="160" width="80" height="20" fill="{color}"/>
    <rect width="240" height="20" fill="url(#s)" opacity="0.1"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="11">
    <text aria-hidden="true" x="80" y="15" fill="#010101" fill-opacity="0.3" transform="scale(.1)" textLength="1500">{metric_name}</text>
    <text x="80" y="14" transform="scale(.1)" fill="#fff" textLength="1500">{metric_name}</text>
    <text aria-hidden="true" x="199" y="15" fill="#010101" fill-opacity="0.3" transform="scale(.1)" textLength="600">{status} {value:.4f}</text>
    <text x="199" y="14" transform="scale(.1)" fill="#fff" textLength="600">{status} {value:.4f}</text>
  </g>
</svg>
'''
    
    output_path.write_text(svg_content)
    return output_path


if __name__ == '__main__':
    # Example: Generate sample badges
    badge_pass = generate_compliance_badge('passing', 'loan', output_path=Path('/tmp/badge_pass.svg'))
    badge_fail = generate_compliance_badge('failing', 'hiring', output_path=Path('/tmp/badge_fail.svg'))
    metric_badge = generate_metric_badge(
        'Demographic Parity',
        0.027,
        0.1,
        output_path=Path('/tmp/metric_badge.svg')
    )
    
    print(f"✅ Generated badges:")
    print(f"  - {badge_pass}")
    print(f"  - {badge_fail}")
    print(f"  - {metric_badge}")
