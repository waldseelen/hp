"""
UI Kit View for Design System Documentation
"""

import logging

from django.shortcuts import render

from apps.main.fixtures.portfolio_fixtures import PortfolioFixtures

logger = logging.getLogger(__name__)


def ui_kit_view(request):
    """
    UI Kit page view showcasing all design system components with live examples.
    Uses fixtures for realistic data demonstration.
    """
    try:
        # Get sample data from fixtures
        featured_projects = PortfolioFixtures.get_featured_projects()
        development_projects = PortfolioFixtures.get_development_projects()
        all_projects = PortfolioFixtures.get_all_projects()
        stats = PortfolioFixtures.get_project_stats()

        # Prepare sample data for component showcases
        sample_featured_project = featured_projects[0] if featured_projects else None
        sample_compact_projects = (
            development_projects[:3] if development_projects else []
        )
        sample_grid_projects = all_projects[:6] if all_projects else []

        # Format stats for display
        stats_display = {
            "total": stats["total"],
            "completed": stats["completed"],
            "in_development": stats["in_development"],
            "planning": stats["planning"],
            "success_rate": stats["success_rate"],
            "success_rate_display": f"{stats['success_rate']}%",
            "total_views": stats["total_views"],
            "total_views_display": f"{stats['total_views']:,}",
            "total_likes": stats["total_likes"],
        }

        context = {
            # Sample data for component showcases
            "sample_featured_project": sample_featured_project,
            "sample_compact_projects": sample_compact_projects,
            "sample_grid_projects": sample_grid_projects,
            "sample_stats": stats_display,
            # Page metadata
            "page_title": "UI Kit - Design System",
            "meta_description": "Comprehensive design system documentation with colors, typography, components, and patterns.",
        }

        return render(request, "pages/portfolio/ui-kit.html", context)

    except Exception as e:
        logger.error(f"Error in ui_kit view: {str(e)}")
        # Return minimal context on error
        context = {
            "sample_featured_project": None,
            "sample_compact_projects": [],
            "sample_grid_projects": [],
            "sample_stats": {},
            "page_title": "UI Kit - Design System",
            "meta_description": "Design System Documentation",
        }
        return render(request, "pages/portfolio/ui-kit.html", context)
