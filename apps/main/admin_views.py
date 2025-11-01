"""
Admin Dashboard Views for Search Monitoring

Provides:
- Search health status view
- Performance metrics dashboard
- Recent queries and errors
- Index statistics
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page

from apps.main.monitoring import search_monitor
from apps.main.search_index import search_index_manager


@staff_member_required
def search_status_dashboard(request):
    """
    Main dashboard view for search monitoring.
    Shows health status, performance metrics, and recent activity.
    """
    dashboard_data = search_monitor.get_dashboard_data()

    # Get additional index stats
    try:
        index_stats = search_index_manager.index.get_stats()
        dashboard_data["index_stats"] = index_stats
    except Exception as e:
        dashboard_data["index_stats"] = {"error": str(e)}

    context = {
        "title": "Search Index Status",
        "dashboard_data": dashboard_data,
        "health": dashboard_data["health"],
        "metrics": dashboard_data["metrics"],
        "recent_queries": dashboard_data["recent_queries"],
        "recent_errors": dashboard_data["recent_errors"],
        "sync_events": dashboard_data["sync_events"],
    }

    return render(request, "admin/search_status.html", context)


@staff_member_required
def search_metrics_api(request):
    """
    JSON API endpoint for search metrics.
    Used for live dashboard updates.
    """
    metrics = search_monitor.get_metrics()
    health = search_monitor.check_index_health()

    return JsonResponse(
        {
            "metrics": metrics,
            "health": health,
            "timestamp": search_monitor.get_metrics().get("last_updated"),
        }
    )


@staff_member_required
@cache_page(300)  # Cache for 5 minutes
def search_performance_chart(request):
    """
    Return data for performance charts.
    Shows latency trends over time.
    """
    recent_queries = search_monitor.get_recent_queries(100)

    # Aggregate data for chart
    latency_data = [
        {
            "timestamp": q["timestamp"],
            "duration": q["duration_ms"],
            "error": q["error"],
        }
        for q in recent_queries
    ]

    return JsonResponse(
        {
            "latency_data": latency_data,
            "threshold_warning": search_monitor.LATENCY_WARNING_MS,
            "threshold_error": search_monitor.LATENCY_ERROR_MS,
        }
    )
