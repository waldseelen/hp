"""
API views for cache monitoring and management.
"""

import json
import logging

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.main.cache import CacheWarmer, cache_manager

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def cache_stats_api(request):
    """API endpoint for cache statistics."""
    try:
        stats = cache_manager.get_stats()

        # Add additional information
        stats.update(
            {
                "cache_backend": settings.CACHES["default"]["BACKEND"],
                "timestamp": timezone.now().isoformat(),
                "redis_available": "redis"
                in settings.CACHES["default"]["BACKEND"].lower(),
            }
        )

        # Add performance assessment
        hit_ratio = stats["hit_ratio"]
        if hit_ratio >= 90:
            performance_grade = "A+"
        elif hit_ratio >= 80:
            performance_grade = "A"
        elif hit_ratio >= 70:
            performance_grade = "B"
        elif hit_ratio >= 60:
            performance_grade = "C"
        else:
            performance_grade = "D"

        stats["performance_grade"] = performance_grade

        return JsonResponse({"status": "success", "data": stats})

    except Exception as e:
        logger.error(f"Cache stats API error: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@require_http_methods(["GET"])
def cache_health_api(request):
    """API endpoint for cache health check."""
    try:
        # Perform basic connectivity test
        test_key = "health_check_api"
        test_value = timezone.now().isoformat()

        # Test set/get/delete cycle
        cache_manager.set(test_key, test_value, 60)
        result = cache_manager.get(test_key)
        cache_manager.delete(test_key)

        health_status = "healthy" if result == test_value else "unhealthy"

        return JsonResponse(
            {
                "status": "success",
                "health": health_status,
                "timestamp": timezone.now().isoformat(),
                "cache_backend": settings.CACHES["default"]["BACKEND"],
            }
        )

    except Exception as e:
        logger.error(f"Cache health API error: {e}")
        return JsonResponse(
            {
                "status": "error",
                "health": "unhealthy",
                "message": str(e),
                "timestamp": timezone.now().isoformat(),
            },
            status=500,
        )


@staff_member_required
@require_http_methods(["POST"])
def cache_warm_api(request):
    """API endpoint for cache warming (admin only)."""
    try:
        # Get cache type from request
        data = json.loads(request.body) if request.body else {}
        cache_type = data.get("type", "all")

        # Warm caches based on type
        if cache_type == "all":
            count = CacheWarmer.warm_all_caches()
        elif cache_type == "blog":
            count = CacheWarmer.warm_blog_caches()
        elif cache_type == "main":
            count = CacheWarmer.warm_main_caches()
        else:
            return JsonResponse(
                {"status": "error", "message": f"Invalid cache type: {cache_type}"},
                status=400,
            )

        return JsonResponse(
            {
                "status": "success",
                "message": f"Cache warming completed: {count} items cached",
                "items_cached": count,
                "cache_type": cache_type,
                "timestamp": timezone.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Cache warm API error: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@staff_member_required
@require_http_methods(["POST"])
def cache_clear_api(request):
    """API endpoint for cache clearing (admin only)."""
    try:
        data = json.loads(request.body) if request.body else {}
        pattern = data.get("pattern", None)

        if pattern:
            # Clear specific pattern
            count = cache_manager.delete_pattern(pattern)
            message = f"Cleared {count} cache entries matching pattern: {pattern}"
        else:
            # Clear entire cache
            cache_manager.clear()
            message = "Entire cache cleared"

        return JsonResponse(
            {
                "status": "success",
                "message": message,
                "timestamp": timezone.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Cache clear API error: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@require_http_methods(["GET"])
def cache_monitor_dashboard(request):
    """API endpoint for cache monitoring dashboard data."""
    try:
        stats = cache_manager.get_stats()

        # Calculate additional metrics
        total_ops = stats["total_operations"]
        uptime_hours = (
            stats["uptime_seconds"] / 3600 if stats["uptime_seconds"] > 0 else 0.01
        )

        dashboard_data = {
            "overview": {
                "hit_ratio": stats["hit_ratio"],
                "total_operations": total_ops,
                "operations_per_hour": (
                    total_ops / uptime_hours if uptime_hours > 0 else 0
                ),
                "error_rate": (
                    (stats["errors"] / total_ops * 100) if total_ops > 0 else 0
                ),
                "uptime_hours": uptime_hours,
                "performance_grade": get_performance_grade(stats["hit_ratio"]),
            },
            "operations": {
                "hits": stats["hits"],
                "misses": stats["misses"],
                "sets": stats["sets"],
                "deletes": stats["deletes"],
                "errors": stats["errors"],
            },
            "cache_info": {
                "backend": settings.CACHES["default"]["BACKEND"],
                "redis_available": "redis"
                in settings.CACHES["default"]["BACKEND"].lower(),
                "location": settings.CACHES["default"].get("LOCATION", "N/A"),
            },
            "recent_errors": (
                stats["recent_errors"][-5:] if stats["recent_errors"] else []
            ),
            "recommendations": get_cache_recommendations(stats),
            "timestamp": timezone.now().isoformat(),
        }

        return JsonResponse({"status": "success", "data": dashboard_data})

    except Exception as e:
        logger.error(f"Cache monitor dashboard API error: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def get_performance_grade(hit_ratio):
    """Get performance grade based on hit ratio."""
    if hit_ratio >= 95:
        return {
            "grade": "A+",
            "color": "success",
            "description": "Excellent performance",
        }
    elif hit_ratio >= 85:
        return {
            "grade": "A",
            "color": "success",
            "description": "Very good performance",
        }
    elif hit_ratio >= 75:
        return {"grade": "B", "color": "warning", "description": "Good performance"}
    elif hit_ratio >= 65:
        return {
            "grade": "C",
            "color": "warning",
            "description": "Acceptable performance",
        }
    else:
        return {
            "grade": "D",
            "color": "danger",
            "description": "Poor performance - needs optimization",
        }


def get_cache_recommendations(stats):
    """Generate cache optimization recommendations."""
    recommendations = []
    hit_ratio = stats["hit_ratio"]
    error_rate = (
        (stats["errors"] / stats["total_operations"] * 100)
        if stats["total_operations"] > 0
        else 0
    )

    if hit_ratio < 80:
        recommendations.append(
            {
                "type": "performance",
                "message": "Low cache hit ratio detected. Consider increasing cache timeouts or improving cache keys.",
                "severity": "warning",
            }
        )

    if error_rate > 1:  # > 1% error rate
        recommendations.append(
            {
                "type": "reliability",
                "message": "High error rate detected. Check cache backend connectivity and configuration.",
                "severity": "error",
            }
        )

    if (
        stats["total_operations"] < 100 and stats["uptime_seconds"] > 3600
    ):  # Low usage after 1 hour
        recommendations.append(
            {
                "type": "usage",
                "message": "Low cache usage detected. Ensure caching is properly implemented in views and templates.",
                "severity": "info",
            }
        )

    if not ("redis" in settings.CACHES["default"]["BACKEND"].lower()):
        recommendations.append(
            {
                "type": "configuration",
                "message": "Consider using Redis for better performance and advanced features like pattern deletion.",
                "severity": "info",
            }
        )

    return recommendations


@require_http_methods(["GET"])
def cache_performance_metrics(request):
    """API endpoint for cache performance metrics over time."""
    try:
        # This would typically query a time-series database
        # For now, return current stats with mock historical data
        current_stats = cache_manager.get_stats()

        # Mock time series data for demonstration
        now = timezone.now()
        metrics = {
            "hit_ratio_timeline": [
                {
                    "timestamp": (now - timezone.timedelta(minutes=i * 5)).isoformat(),
                    "hit_ratio": max(
                        0, current_stats["hit_ratio"] + (i * 2 - 10)
                    ),  # Mock variation
                }
                for i in range(12)  # Last hour in 5-minute intervals
            ],
            "operations_timeline": [
                {
                    "timestamp": (now - timezone.timedelta(minutes=i * 5)).isoformat(),
                    "operations": max(
                        0, current_stats["total_operations"] // 12 + (i * 5)
                    ),
                }
                for i in range(12)
            ],
            "current_stats": current_stats,
        }

        return JsonResponse({"status": "success", "data": metrics})

    except Exception as e:
        logger.error(f"Cache performance metrics API error: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


# Cache invalidation webhook for external systems
@csrf_exempt
@require_http_methods(["POST"])
def cache_invalidate_webhook(request):
    """Webhook endpoint for external cache invalidation."""
    try:
        data = json.loads(request.body)

        # Validate webhook signature if configured
        if hasattr(settings, "CACHE_WEBHOOK_SECRET"):
            # Implement webhook signature validation here
            pass

        # Get invalidation parameters
        pattern = data.get("pattern")
        key = data.get("key")
        model = data.get("model")

        if pattern:
            count = cache_manager.delete_pattern(pattern)
            message = f"Invalidated {count} entries matching pattern: {pattern}"
        elif key:
            cache_manager.delete(key)
            message = f"Invalidated cache key: {key}"
        elif model:
            # Model-based invalidation
            pattern = f"queryset_*{model.lower()}*"
            count = cache_manager.delete_pattern(pattern)
            message = f"Invalidated {count} entries for model: {model}"
        else:
            return JsonResponse(
                {"status": "error", "message": "No invalidation parameters provided"},
                status=400,
            )

        return JsonResponse(
            {
                "status": "success",
                "message": message,
                "timestamp": timezone.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Cache invalidate webhook error: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
