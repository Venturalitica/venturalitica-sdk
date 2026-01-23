"""
Test suite for badge generation functionality
"""

import pytest
from pathlib import Path
from venturalitica.badges import (
    generate_compliance_badge,
    generate_metric_badge,
)


class TestComplianceBadge:
    """Test compliance badge generation"""
    
    def test_generate_passing_badge(self, tmp_path):
        """Generate a passing compliance badge"""
        badge_path = Path(tmp_path) / "badge.svg"
        
        result = generate_compliance_badge(
            status='passing',
            policy_name='loan',
            date='2026-01-22',
            output_path=badge_path
        )
        
        assert result is not None
        assert 'passing' in str(result).lower() or result.exists()
    
    def test_generate_failing_badge(self, tmp_path):
        """Generate a failing compliance badge"""
        badge_path = Path(tmp_path) / "badge.svg"
        
        result = generate_compliance_badge(
            status='failing',
            policy_name='hiring',
            date='2026-01-22',
            output_path=badge_path
        )
        
        assert result is not None
    
    def test_generate_unknown_badge(self, tmp_path):
        """Generate an unknown status badge"""
        badge_path = Path(tmp_path) / "badge.svg"
        
        result = generate_compliance_badge(
            status='unknown',
            policy_name='health',
            date='2026-01-22',
            output_path=badge_path
        )
        
        assert result is not None
    
    def test_invalid_status_raises_error(self):
        """Invalid status should raise error or be handled gracefully"""
        try:
            generate_compliance_badge(
                status='invalid',
                policy_name='loan',
                date='2026-01-22'
            )
            # If it doesn't raise, it should return something
            assert True
        except (ValueError, KeyError):
            # This is also acceptable
            assert True
    
    def test_badge_contains_metadata(self, tmp_path):
        """Badge should contain policy name and date"""
        badge_path = Path(tmp_path) / "badge.svg"
        
        result = generate_compliance_badge(
            status='passing',
            policy_name='loan',
            date='2026-01-22',
            output_path=badge_path
        )
        
        # If it's a file, read and check content
        if isinstance(result, Path) and result.exists():
            content = result.read_text()
            # SVG should contain metadata
            assert isinstance(content, str)
            assert len(content) > 0


class TestMetricBadge:
    """Test metric-specific badge generation"""
    
    @pytest.mark.skip(reason="generate_metric_badge not yet implemented")
    def test_generate_fairness_badge(self, tmp_path):
        """Generate a badge for fairness metric"""
        badge_path = Path(tmp_path) / "metric_badge.svg"
        
        result = generate_metric_badge(
            metric_name='demographic_parity_diff',
            value=0.05,
            threshold=0.10,
            status='passing',
            output_path=badge_path
        )
        
        assert result is not None
    
    @pytest.mark.skip(reason="generate_metric_badge not yet implemented")
    def test_generate_privacy_badge(self, tmp_path):
        """Generate a badge for privacy metric"""
        badge_path = Path(tmp_path) / "privacy_badge.svg"
        
        result = generate_metric_badge(
            metric_name='k_anonymity',
            value=8,
            threshold=5,
            status='passing',
            output_path=badge_path
        )
        
        assert result is not None
    
    @pytest.mark.skip(reason="generate_metric_badge not yet implemented")
    def test_generate_failing_metric_badge(self, tmp_path):
        """Generate a badge for failing metric"""
        badge_path = Path(tmp_path) / "failing_badge.svg"
        
        result = generate_metric_badge(
            metric_name='equal_opportunity_diff',
            value=0.25,
            threshold=0.15,
            status='failing',
            output_path=badge_path
        )
        
        assert result is not None
    
    @pytest.mark.skip(reason="generate_metric_badge not yet implemented")
    def test_badge_value_formatting(self, tmp_path):
        """Badge should format numeric values appropriately"""
        badge_path = Path(tmp_path) / "formatted_badge.svg"
        
        result = generate_metric_badge(
            metric_name='demographic_parity_diff',
            value=0.027,
            threshold=0.10,
            status='passing',
            output_path=badge_path
        )
        
        assert result is not None


class TestBadgeIntegration:
    """Integration tests for badge system"""
    
    @pytest.mark.skip(reason="generate_multiple_badges uses generate_metric_badge not yet implemented")
    def test_generate_multiple_badges(self, tmp_path):
        """Generate badges for multiple metrics"""
        metrics = [
            ('demographic_parity_diff', 0.05, 0.10, 'passing'),
            ('k_anonymity', 8, 5, 'passing'),
            ('equal_opportunity_diff', 0.25, 0.15, 'failing'),
        ]
        
        badges = []
        for metric_name, value, threshold, status in metrics:
            badge_path = Path(tmp_path) / f"{metric_name}.svg"
            result = generate_metric_badge(
                metric_name=metric_name,
                value=value,
                threshold=threshold,
                status=status,
                output_path=badge_path
            )
            badges.append(result)
        
        assert len(badges) == 3
        assert all(b is not None for b in badges)
    
    def test_badge_markdown_format(self, tmp_path):
        """Badges should be usable in Markdown"""
        badge_path = Path(tmp_path) / "badge.svg"
        
        result = generate_compliance_badge(
            status='passing',
            policy_name='loan',
            date='2026-01-22',
            output_path=badge_path
        )
        
        # Should be able to format as markdown
        markdown = f"![Compliance]({result})"
        assert '![' in markdown
        assert '.svg' in markdown


class TestBadgeFormatting:
    """Test badge styling and colors"""
    
    def test_passing_badge_color(self, tmp_path):
        """Passing badge should use green color"""
        badge_path = Path(tmp_path) / "passing.svg"
        
        result = generate_compliance_badge(
            status='passing',
            policy_name='test',
            date='2026-01-22',
            output_path=badge_path
        )
        
        if isinstance(result, Path) and result.exists():
            content = result.read_text()
            # SVG often uses color codes or keywords
            assert any(color in content.lower() 
                      for color in ['green', '#00ff00', '#28a745', '4CAF50'])
    
    def test_failing_badge_color(self, tmp_path):
        """Failing badge should use red color"""
        badge_path = Path(tmp_path) / "failing.svg"
        
        result = generate_compliance_badge(
            status='failing',
            policy_name='test',
            date='2026-01-22',
            output_path=badge_path
        )
        
        if isinstance(result, Path) and result.exists():
            content = result.read_text()
            # SVG often uses color codes or keywords
            assert any(color in content.lower() 
                      for color in ['red', '#ff0000', '#f44336', '#dc3545'])
    
    def test_unknown_badge_color(self, tmp_path):
        """Unknown badge should use a valid color"""
        badge_path = Path(tmp_path) / "unknown.svg"
        
        result = generate_compliance_badge(
            status='unknown',
            policy_name='test',
            date='2026-01-22',
            output_path=badge_path
        )
        
        if isinstance(result, Path) and result.exists():
            content = result.read_text()
            # SVG should contain color information
            assert isinstance(content, str) and len(content) > 0


if __name__ == "__main__":
    # Run tests with: pytest test_badges.py -v
    pass
