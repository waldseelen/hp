# Main views module
from .main_views import (
    home, personal_view, music_view, ai_tools_view, cybersecurity_view,
    useful_view, projects_view, project_detail_view, set_language,
    language_status, logout_view
)
from .search import SearchView, search_api, search_suggestions, TagCloudView, search_by_tag
from .shorturl import redirect_short_url as short_url_redirect
from .security import csp_violation_report, network_error_report
from .analytics_api import (
    track_event, track_conversion, analytics_summary,
    track_journey, track_funnel, get_ab_variant, track_ab_conversion,
    funnel_analytics, ab_test_results, journey_insights,
    analytics_dashboard_data
)
from .health_api import (
    health_check_endpoint, health_check_detailed, health_dashboard,
    liveness_probe, readiness_probe, health_metrics
)

# Create function-based view aliases for URL patterns
search_view = SearchView.as_view()
tag_search_view = TagCloudView.as_view()
tag_results_view = search_by_tag