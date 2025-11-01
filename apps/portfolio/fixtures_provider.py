"""
Fixtures Data Provider for UI Kit Living Documentation

This module provides fixture-based sample data for all portfolio components
used in the UI Kit page. These fixtures ensure consistent, realistic examples
without requiring actual database records.

Usage:
    from apps.portfolio.fixtures_provider import get_ui_kit_fixtures
    fixtures = get_ui_kit_fixtures()
"""

from typing import Any, Dict, List


def get_project_fixture(mode: str = "featured") -> Dict[str, Any]:
    """
    Generate a sample project fixture.

    Args:
        mode: 'featured' for large showcase, 'compact' for grid display

    Returns:
        Dictionary representing a project object
    """
    if mode == "featured":
        return {
            "title": "Advanced AI Portfolio System",
            "description": "A comprehensive portfolio management system powered by machine learning algorithms for intelligent content curation and recommendation.",
            "technologies": ["Python", "Django", "TensorFlow", "React", "PostgreSQL"],
            "image_url": "/media/projects/ai-portfolio.jpg",
            "status": "Completed",
            "status_display": "Completed",
            "link": "#",
            "github_link": "#",
            "github_url": "https://github.com",
            "featured": True,
            "views": 1250,
            "view_count": 1250,
            "progress_percentage": 100,
            "slug": "ai-portfolio",
        }
    else:  # compact
        return {
            "title": "Sample Project",
            "description": "A well-crafted project showcasing modern development practices",
            "technologies": ["Python", "Django", "React"],
            "status": "Completed",
            "status_display": "Completed",
            "featured": False,
            "views": 500,
            "view_count": 500,
            "slug": "sample-project",
            "difficulty_level": 3,
        }


def get_compact_projects_fixtures() -> List[Dict[str, Any]]:
    """
    Generate a list of sample projects for compact grid display.

    Returns:
        List of project dictionaries
    """
    return [
        {
            "title": "E-Commerce Platform",
            "description": "Full-stack e-commerce solution with payment integration and inventory management",
            "technologies": ["Django", "React", "Stripe"],
            "status": "In Progress",
            "status_display": "In Progress",
            "featured": False,
            "views": 350,
            "view_count": 350,
            "slug": "ecommerce-platform",
            "difficulty_level": 4,
        },
        {
            "title": "Real-time Chat Application",
            "description": "WebSocket-based real-time messaging application with user authentication",
            "technologies": ["Node.js", "Socket.io", "Vue.js"],
            "status": "Completed",
            "status_display": "Completed",
            "featured": False,
            "views": 890,
            "view_count": 890,
            "slug": "chat-app",
            "difficulty_level": 3,
        },
        {
            "title": "Data Visualization Dashboard",
            "description": "Interactive analytics dashboard with live data streaming and custom visualizations",
            "technologies": ["Python", "Plotly", "FastAPI"],
            "status": "Completed",
            "status_display": "Completed",
            "featured": False,
            "views": 620,
            "view_count": 620,
            "slug": "data-dashboard",
            "difficulty_level": 5,
        },
    ]


def get_statistics_fixtures() -> Dict[str, Any]:
    """
    Generate sample statistics data.

    Returns:
        Dictionary with statistics values
    """
    return {
        "total": 42,
        "in_development": 8,
        "success_rate_display": "96%",
        "total_views_display": "12.5K",
    }


def get_design_tokens_summary() -> Dict[str, Any]:
    """
    Generate a summary of design tokens for reference.

    Returns:
        Dictionary with design tokens metadata
    """
    return {
        "colors": {
            "primary_scale": 10,  # 50-900
            "secondary_scale": 10,
            "semantic_colors": ["success", "warning", "error", "info"],
            "wcag_compliance": "AA/AAA",
        },
        "typography": {
            "font_families": ["Inter (sans-serif)", "JetBrains Mono (monospace)"],
            "scale_levels": 8,  # 8 typography sizes
        },
        "spacing": {
            "system": "Base-8",
            "range": "4px to 96px",
            "tokens": 10,
        },
        "shadows": {
            "levels": 5,
            "effects": ["soft", "medium", "hard", "blur", "glow"],
        },
        "animations": {
            "pre_defined": 6,
            "duration_options": ["fast", "normal", "slow"],
        },
    }


def get_ui_kit_fixtures() -> Dict[str, Any]:
    """
    Get all UI Kit fixtures in one call.

    Returns:
        Dictionary containing all fixture data for UI Kit page
    """
    return {
        "sample_featured_project": get_project_fixture("featured"),
        "sample_compact_projects": get_compact_projects_fixtures(),
        "sample_grid_projects": get_compact_projects_fixtures(),
        "sample_stats": get_statistics_fixtures(),
        "design_tokens_summary": get_design_tokens_summary(),
    }


if __name__ == "__main__":
    # Example usage for testing
    fixtures = get_ui_kit_fixtures()
    print("UI Kit Fixtures Generated:")
    print(f"- Featured Project: {fixtures['sample_featured_project']['title']}")
    print(f"- Compact Projects: {len(fixtures['sample_compact_projects'])} items")
    print(f"- Statistics: Total={fixtures['sample_stats']['total']}")
    print(
        f"- Design Tokens Categories: {list(fixtures['design_tokens_summary'].keys())}"
    )
