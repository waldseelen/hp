"""
Analytics API views for user behavior tracking
"""

import json
import logging

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from ..analytics import analytics

logger = logging.getLogger(__name__)


@csrf_protect
@require_http_methods(["POST"])
def track_event(request):
    """
    API endpoint to track custom events from frontend
    """
    try:
        data = json.loads(request.body)

        event_name = data.get("event_name")
        event_data = data.get("event_data", {})

        if not event_name:
            return JsonResponse(
                {"status": "error", "message": "event_name is required"}, status=400
            )

        # Track the event
        success = analytics.track_event(request, event_name, event_data)

        if success:
            return JsonResponse(
                {"status": "ok", "message": "Event tracked successfully"}
            )
        else:
            return JsonResponse(
                {"status": "error", "message": "Failed to track event"}, status=500
            )

    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "Invalid JSON data"}, status=400
        )
    except Exception as e:
        logger.error(f"Event tracking error: {e}")
        return JsonResponse(
            {"status": "error", "message": "Internal server error"}, status=500
        )


@csrf_protect
@require_http_methods(["POST"])
def track_conversion(request):
    """
    API endpoint to track conversions from frontend
    """
    try:
        data = json.loads(request.body)

        conversion_type = data.get("conversion_type")
        conversion_value = data.get("conversion_value")

        if not conversion_type:
            return JsonResponse(
                {"status": "error", "message": "conversion_type is required"},
                status=400,
            )

        # Track the conversion
        success = analytics.track_conversion(request, conversion_type, conversion_value)

        if success:
            return JsonResponse(
                {"status": "ok", "message": "Conversion tracked successfully"}
            )
        else:
            return JsonResponse(
                {"status": "error", "message": "Failed to track conversion"}, status=500
            )

    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "Invalid JSON data"}, status=400
        )
    except Exception as e:
        logger.error(f"Conversion tracking error: {e}")
        return JsonResponse(
            {"status": "error", "message": "Internal server error"}, status=500
        )


@staff_member_required
@require_http_methods(["GET"])
def analytics_summary(request):
    """
    Get analytics summary (admin only)
    """
    try:
        days = int(request.GET.get("days", 7))
        days = min(days, 30)  # Limit to 30 days max

        summary = analytics.get_analytics_summary(days=days)

        return JsonResponse({"status": "ok", "summary": summary, "period_days": days})

    except Exception as e:
        logger.error(f"Analytics summary error: {e}")
        return JsonResponse(
            {"status": "error", "message": "Failed to get analytics summary"},
            status=500,
        )


@staff_member_required
@require_http_methods(["GET"])
def analytics_dashboard(request):
    """
    Analytics dashboard view (admin only)
    """
    try:
        days = int(request.GET.get("days", 7))
        summary = analytics.get_analytics_summary(days=days)

        # Calculate additional metrics
        total_page_views = sum(summary.get("page_views", {}).values())
        total_events = sum(summary.get("events", {}).values())
        total_conversions = sum(summary.get("conversions", {}).values())

        # Calculate conversion rate
        conversion_rate = 0
        if total_page_views > 0:
            conversion_rate = (total_conversions / total_page_views) * 100

        context = {
            "summary": summary,
            "period_days": days,
            "metrics": {
                "total_page_views": total_page_views,
                "total_events": total_events,
                "total_conversions": total_conversions,
                "conversion_rate": round(conversion_rate, 2),
            },
        }

        return render(request, "analytics/dashboard.html", context)

    except Exception as e:
        logger.error(f"Analytics dashboard error: {e}")
        return render(
            request,
            "analytics/dashboard.html",
            {"error": "Unable to load analytics data"},
        )


@require_http_methods(["POST"])
@csrf_protect
def track_journey(request):
    """Track user journey step"""
    try:
        data = json.loads(request.body)
        step_name = data.get("step_name")
        journey_id = data.get("journey_id")

        if not step_name:
            return JsonResponse({"error": "step_name required"}, status=400)

        journey_id = analytics.track_user_journey(request, step_name, journey_id)

        return JsonResponse({"success": True, "journey_id": journey_id})

    except Exception as e:
        logger.error(f"Journey tracking error: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_protect
def track_funnel(request):
    """Track funnel progression"""
    try:
        data = json.loads(request.body)
        funnel_name = data.get("funnel_name")
        step_name = data.get("step_name")
        step_order = data.get("step_order", 1)

        if not all([funnel_name, step_name]):
            return JsonResponse(
                {"error": "funnel_name and step_name required"}, status=400
            )

        success = analytics.track_funnel_step(
            request, funnel_name, step_name, step_order
        )

        return JsonResponse({"success": success})

    except Exception as e:
        logger.error(f"Funnel tracking error: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_ab_variant(request):
    """Get A/B test variant for user"""
    try:
        test_name = request.GET.get("test_name")
        variants = request.GET.getlist("variants")

        if not test_name:
            return JsonResponse({"error": "test_name required"}, status=400)

        variant = analytics.get_ab_test_variant(request, test_name, variants or None)

        return JsonResponse(
            {"success": True, "test_name": test_name, "variant": variant}
        )

    except Exception as e:
        logger.error(f"A/B test error: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_protect
def track_ab_conversion(request):
    """Track A/B test conversion"""
    try:
        data = json.loads(request.body)
        test_name = data.get("test_name")
        conversion_type = data.get("conversion_type", "conversion")

        if not test_name:
            return JsonResponse({"error": "test_name required"}, status=400)

        success = analytics.track_ab_test_conversion(
            request, test_name, conversion_type
        )

        return JsonResponse({"success": success})

    except Exception as e:
        logger.error(f"A/B conversion tracking error: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
@staff_member_required
def funnel_analytics(request):
    """Get funnel analytics data"""
    try:
        funnel_name = request.GET.get("funnel_name")
        days = int(request.GET.get("days", 7))

        if not funnel_name:
            return JsonResponse({"error": "funnel_name required"}, status=400)

        data = analytics.get_funnel_analytics(funnel_name, days)

        return JsonResponse({"success": True, "data": data})

    except Exception as e:
        logger.error(f"Funnel analytics error: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
@staff_member_required
def ab_test_results(request):
    """Get A/B test results"""
    try:
        test_name = request.GET.get("test_name")

        if not test_name:
            return JsonResponse({"error": "test_name required"}, status=400)

        results = analytics.get_ab_test_results(test_name)

        return JsonResponse({"success": True, "results": results})

    except Exception as e:
        logger.error(f"A/B test results error: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
@staff_member_required
def journey_insights(request):
    """Get user journey insights"""
    try:
        days = int(request.GET.get("days", 7))

        insights = analytics.get_user_journey_insights(days)

        return JsonResponse({"success": True, "insights": insights})

    except Exception as e:
        logger.error(f"Journey insights error: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
@staff_member_required
def analytics_dashboard_data(request):
    """Get comprehensive analytics dashboard data"""
    try:
        days = int(request.GET.get("days", 7))

        # Get all analytics data
        summary = analytics.get_analytics_summary(days)
        journey_insights = analytics.get_user_journey_insights(days)

        # Get active A/B tests (simplified for now)
        active_tests = []

        # Get active funnels
        active_funnels = {
            "signup": analytics.get_funnel_analytics("signup", days),
            "contact": analytics.get_funnel_analytics("contact", days),
        }

        return JsonResponse(
            {
                "success": True,
                "data": {
                    "summary": summary,
                    "journey_insights": journey_insights,
                    "active_tests": active_tests,
                    "active_funnels": active_funnels,
                    "period_days": days,
                },
            }
        )

    except Exception as e:
        logger.error(f"Analytics dashboard error: {e}")
        return JsonResponse({"error": str(e)}, status=500)
