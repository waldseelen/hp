"""
Performance monitoring API views.
Simple stub for collecting frontend performance metrics.
"""

import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def collect_performance_metric(request):
    """
    Collect performance metrics from frontend.
    Returns success response to prevent 404 errors in console.
    """
    try:
        if request.content_type == "application/json":
            data = json.loads(request.body)
            # Log performance data for monitoring (optional)
            if data.get("lcp") or data.get("fid") or data.get("cls"):
                logger.debug(f"Performance metrics received: {data}")

        return JsonResponse(
            {"status": "success", "message": "Metrics received"}, status=201
        )
    except Exception as e:
        logger.warning(f"Error processing performance metric: {e}")
        return JsonResponse(
            {"status": "error", "message": "Failed to process metrics"},
            status=200,  # Still return 200 to prevent console errors
        )


@require_http_methods(["GET"])
def performance_dashboard_data(request):
    """
    Stub endpoint for performance dashboard.
    Returns empty data structure.
    """
    return JsonResponse(
        {
            "status": "success",
            "data": {"metrics": [], "summary": {"lcp": 0, "fid": 0, "cls": 0}},
        },
        status=200,
    )


def health_check(request):
    """Simple health check endpoint."""
    return JsonResponse({"status": "healthy"}, status=200)
