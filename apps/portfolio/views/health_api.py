"""
Health Check API Views
Provides endpoints for system health monitoring
"""

import logging
import sys

import django
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from ..health_checks import health_checker

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
@never_cache
def health_check_endpoint(request):
    """
    Basic health check endpoint for load balancers and monitoring
    Returns 200 if system is healthy, 503 if unhealthy
    """
    try:
        # Run basic checks only for performance
        basic_checks = {
            "database": health_checker.check_database(),
            "cache": health_checker.check_cache(),
            "application": health_checker.check_application_health(),
        }

        # Determine overall status
        overall_healthy = all(
            check["status"] == "healthy" for check in basic_checks.values()
        )

        response_data = {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": timezone.now().isoformat(),
            "version": "1.0.0",  # You can make this dynamic
            "checks": basic_checks,
        }

        status_code = 200 if overall_healthy else 503

        return JsonResponse(response_data, status=status_code)

    except Exception as e:
        logger.error(f"Health check endpoint failed: {e}")
        return JsonResponse(
            {
                "status": "error",
                "message": "Health check failed",
                "timestamp": timezone.now().isoformat(),
            },
            status=503,
        )


@require_http_methods(["GET"])
@never_cache
def health_check_detailed(request):
    """
    Detailed health check endpoint (public but comprehensive)
    """
    try:
        # Run all health checks
        results = health_checker.run_all_checks()

        # Determine HTTP status code
        if results["overall_status"] == "healthy":
            status_code = 200
        elif results["overall_status"] == "warning":
            status_code = 200  # Warnings don't affect availability
        else:
            status_code = 503

        return JsonResponse(results, status=status_code)

    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return JsonResponse(
            {
                "status": "error",
                "message": f"Health check system failed: {str(e)}",
                "timestamp": timezone.now().isoformat(),
            },
            status=503,
        )


@require_http_methods(["GET"])
@staff_member_required
@never_cache
def health_dashboard(request):
    """
    Health monitoring dashboard (admin only)
    """
    try:
        # Get comprehensive health data
        current_health = health_checker.run_all_checks()
        uptime_stats = health_checker.get_uptime_stats()

        dashboard_data = {
            "current_health": current_health,
            "uptime_stats": uptime_stats,
            "system_info": {
                "timestamp": timezone.now().isoformat(),
                "django_version": getattr(django, "VERSION", "unknown"),
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            },
        }

        return JsonResponse(dashboard_data)

    except Exception as e:
        logger.error(f"Health dashboard failed: {e}")
        return JsonResponse(
            {"status": "error", "message": f"Dashboard failed: {str(e)}"}, status=500
        )


@require_http_methods(["GET"])
@never_cache
def liveness_probe(request):
    """
    Kubernetes liveness probe endpoint
    Simple check to see if the application is running
    """
    try:
        return JsonResponse(
            {"status": "alive", "timestamp": timezone.now().isoformat()}
        )
    except Exception:
        return JsonResponse({"status": "dead"}, status=503)


@require_http_methods(["GET"])
@never_cache
def readiness_probe(request):
    """
    Kubernetes readiness probe endpoint
    Checks if the application is ready to serve requests
    """
    try:
        # Quick readiness checks
        db_check = health_checker.check_database()
        cache_check = health_checker.check_cache()

        ready = db_check["status"] in ["healthy", "warning"] and cache_check[
            "status"
        ] in ["healthy", "warning"]

        response_data = {
            "status": "ready" if ready else "not_ready",
            "timestamp": timezone.now().isoformat(),
            "checks": {"database": db_check["status"], "cache": cache_check["status"]},
        }

        return JsonResponse(response_data, status=200 if ready else 503)

    except Exception as e:
        logger.error(f"Readiness probe failed: {e}")
        return JsonResponse({"status": "not_ready", "error": str(e)}, status=503)


@require_http_methods(["GET"])
@staff_member_required
def health_metrics(request):
    """
    Prometheus-style metrics endpoint for monitoring integration
    """
    try:
        results = health_checker.run_all_checks()
        uptime_stats = health_checker.get_uptime_stats()

        # Convert to Prometheus format
        metrics = []

        # Overall health metric
        overall_status_value = {
            "healthy": 1,
            "warning": 0.5,
            "unhealthy": 0,
            "error": 0,
        }.get(results["overall_status"], 0)

        metrics.append(f"health_overall_status {overall_status_value}")

        # Individual check metrics
        for check_name, check_result in results["checks"].items():
            status_value = {
                "healthy": 1,
                "warning": 0.5,
                "error": 0,
                "unhealthy": 0,
            }.get(check_result["status"], 0)

            metrics.append(
                f'health_check_status{{check="{check_name}"}} {status_value}'
            )

            # Add specific metrics if available
            if "details" in check_result:
                details = check_result["details"]

                if check_name == "database" and "query_time_ms" in details:
                    metrics.append(
                        f'health_database_query_time_ms {details["query_time_ms"]}'
                    )

                if check_name == "cache" and "response_time_ms" in details:
                    metrics.append(
                        f'health_cache_response_time_ms {details["response_time_ms"]}'
                    )

                if check_name == "disk_space" and "free_percent" in details:
                    metrics.append(
                        f'health_disk_free_percent {details["free_percent"]}'
                    )

                if check_name == "memory" and "used_percent" in details:
                    metrics.append(
                        f'health_memory_used_percent {details["used_percent"]}'
                    )

        # Uptime metrics
        if uptime_stats["status"] != "error":
            metrics.append(
                f'health_uptime_percentage {uptime_stats.get("uptime_percentage", 0)}'
            )
            metrics.append(
                f'health_checks_total_today {uptime_stats.get("total_checks_today", 0)}'
            )
            metrics.append(
                f'health_checks_healthy_today {uptime_stats.get("healthy_checks", 0)}'
            )
            metrics.append(
                f'health_checks_unhealthy_today {uptime_stats.get("unhealthy_checks", 0)}'
            )

        metrics_text = "\n".join(metrics)

        return JsonResponse({"metrics_text": metrics_text, "metrics_data": results})

    except Exception as e:
        logger.error(f"Health metrics failed: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
