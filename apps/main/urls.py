from django.urls import path

from . import admin_views, views
from .views import search_views

app_name = "main"

urlpatterns = [
    path("personal/", views.personal_view, name="personal"),
    path("music/", views.music_view, name="music"),
    path("ai/", views.ai_tools_view, name="ai"),
    path("cybersecurity/", views.cybersecurity_view, name="cybersecurity"),
    path("useful/", views.useful_view, name="useful"),
    # Projects/Portfolio URLs
    path("projects/", views.projects_view, name="projects"),
    path("projects/<slug:slug>/", views.project_detail_view, name="project_detail"),
    # Search URLs
    path("api/search/", search_views.search_api, name="search_api"),
    path("api/search/suggest/", search_views.search_suggest, name="search_suggest"),
    path("api/search/stats/", search_views.search_stats, name="search_stats"),
    path("search/results/", search_views.search_results_view, name="search_results"),
    path("search/", search_views.search_view, name="search"),  # Legacy redirect
    # Admin monitoring URLs
    path(
        "admin/search-status/",
        admin_views.search_status_dashboard,
        name="admin_search_status",
    ),
    path(
        "admin/search-metrics-api/",
        admin_views.search_metrics_api,
        name="admin_search_metrics_api",
    ),
    path(
        "admin/search-performance/",
        admin_views.search_performance_chart,
        name="admin_search_performance",
    ),
]
