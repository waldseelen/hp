"""
Log Analysis Dashboard Views
===========================

Dashboard views for centralized log analysis, monitoring, and alerting.
"""

import json
import logging

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..logging.log_aggregator import log_aggregator
from ..utils.apm_decorators import trace_function

logger = logging.getLogger(__name__)


@login_required
@trace_function(
    operation_name="view.logging_dashboard", description="Log analysis dashboard"
)
def logging_dashboard_view(request):
    """
    Main logging dashboard view with comprehensive log analysis
    """
    try:
        # Get time range from request
        hours_back = int(request.GET.get("hours", 24))

        # Generate log report
        report = log_aggregator.generate_report(hours_back=hours_back)

        # Check for active alerts
        alerts = log_aggregator.check_alert_conditions()

        context = {
            "report": report,
            "alerts": alerts,
            "hours_back": hours_back,
            "page_title": "Log Analysis Dashboard",
            "refresh_interval": 30,  # 30 seconds
        }

        logger.info(
            f"Log dashboard accessed by user {request.user}",
            extra={
                "user_id": request.user.id if request.user.is_authenticated else None,
                "hours_back": hours_back,
                "alert_count": len(alerts),
                "total_log_entries": report["summary"]["total_log_entries"],
            },
        )

        return render(request, "pages/portfolio/logging_dashboard.html", context)

    except Exception as e:
        logger.error(
            f"Error in logging dashboard: {e}",
            extra={
                "user_id": request.user.id if request.user.is_authenticated else None,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )

        # Fallback data
        context = {
            "report": {
                "error": str(e),
                "summary": {
                    "total_log_entries": 0,
                    "error_count": 0,
                    "warning_count": 0,
                },
                "alerts": [],
            },
            "alerts": [],
            "hours_back": hours_back,
            "page_title": "Log Analysis Dashboard - Error",
        }

        return render(request, "pages/portfolio/logging_dashboard.html", context)


@login_required
@require_http_methods(["GET"])
@trace_function(operation_name="api.log_data", description="Log data API endpoint")
def log_data_api(request):
    """
    API endpoint for log data (for AJAX updates)
    """
    try:
        hours_back = int(request.GET.get("hours", 24))
        level = request.GET.get("level")
        logger_name = request.GET.get("logger")
        query = request.GET.get("q", "")

        # Get log stats
        stats = log_aggregator.aggregate_logs(hours_back=hours_back)

        # Search logs if query provided
        search_results = []
        if query or level or logger_name:
            search_results = log_aggregator.search_logs(
                query=query,
                level=level,
                logger=logger_name,
                hours_back=hours_back,
                limit=50,
            )

            # Convert LogEntry objects to dicts
            search_results = [
                {
                    "timestamp": entry.timestamp.isoformat(),
                    "level": entry.level,
                    "logger": entry.logger,
                    "message": entry.message,
                    "service": entry.service,
                    "trace_id": entry.trace_id,
                    "request_id": entry.request_id,
                    "source": entry.source,
                    "exception": entry.exception,
                    "extra": entry.extra,
                }
                for entry in search_results
            ]

        # Check alerts
        alerts = log_aggregator.check_alert_conditions()

        response_data = {
            "success": True,
            "timestamp": timezone.now().isoformat(),
            "stats": {
                "total_entries": stats.total_entries,
                "by_level": stats.by_level,
                "by_logger": stats.by_logger,
                "error_count": stats.error_count,
                "warning_count": stats.warning_count,
                "top_errors": stats.top_errors,
                "performance_issues": stats.performance_issues,
                "security_events": stats.security_events,
            },
            "search_results": search_results,
            "alerts": alerts,
            "query_info": {
                "hours_back": hours_back,
                "level": level,
                "logger": logger_name,
                "query": query,
                "result_count": len(search_results),
            },
        }

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(
            f"Error in log data API: {e}",
            extra={
                "user_id": request.user.id if request.user.is_authenticated else None,
                "query_params": dict(request.GET),
            },
            exc_info=True,
        )

        return JsonResponse(
            {
                "success": False,
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            },
            status=500,
        )


@login_required
@require_http_methods(["GET"])
@trace_function(operation_name="api.log_alerts", description="Log alerts API endpoint")
def log_alerts_api(request):
    """
    API endpoint for log alerts
    """
    try:
        alerts = log_aggregator.check_alert_conditions()

        # Add alert history from cache
        alert_history_key = "log_alert_history"
        alert_history = cache.get(alert_history_key, [])

        # Add current alerts to history
        current_time = timezone.now().isoformat()
        for alert in alerts:
            alert_history.append(
                {
                    **alert,
                    "detected_at": current_time,
                }
            )

        # Keep only last 100 alerts
        alert_history = alert_history[-100:]
        cache.set(alert_history_key, alert_history, 3600 * 24)  # 24 hours

        response_data = {
            "success": True,
            "timestamp": current_time,
            "active_alerts": alerts,
            "alert_history": alert_history[-20:],  # Last 20 for API
            "alert_counts": {
                "critical": len([a for a in alerts if a.get("severity") == "critical"]),
                "warning": len([a for a in alerts if a.get("severity") == "warning"]),
                "total": len(alerts),
            },
        }

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Error in log alerts API: {e}", exc_info=True)
        return JsonResponse(
            {
                "success": False,
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            },
            status=500,
        )


@login_required
@require_http_methods(["POST"])
@csrf_exempt
@trace_function(
    operation_name="api.acknowledge_alert", description="Acknowledge log alert"
)
def acknowledge_alert_api(request):
    """
    API endpoint to acknowledge alerts
    """
    try:
        data = json.loads(request.body)
        alert_type = data.get("alert_type")
        alert_timestamp = data.get("timestamp")

        if not alert_type:
            return JsonResponse(
                {"success": False, "error": "alert_type is required"}, status=400
            )

        # Store acknowledgment in cache
        ack_key = f"alert_ack_{alert_type}_{alert_timestamp}"
        cache.set(
            ack_key,
            {
                "acknowledged_by": request.user.username,
                "acknowledged_at": timezone.now().isoformat(),
                "alert_type": alert_type,
            },
            3600 * 24,
        )  # 24 hours

        logger.info(
            f"Alert acknowledged: {alert_type}",
            extra={
                "alert_type": alert_type,
                "alert_timestamp": alert_timestamp,
                "acknowledged_by": request.user.username,
            },
        )

        return JsonResponse(
            {
                "success": True,
                "message": f"Alert {alert_type} acknowledged",
                "acknowledged_by": request.user.username,
                "acknowledged_at": timezone.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}", exc_info=True)
        return JsonResponse(
            {
                "success": False,
                "error": str(e),
            },
            status=500,
        )


@login_required
@require_http_methods(["GET"])
@trace_function(operation_name="view.log_export", description="Export logs")
def log_export_view(request):
    """
    Export logs in various formats
    """
    try:
        export_format = request.GET.get("format", "json")
        hours_back = int(request.GET.get("hours", 24))
        level = request.GET.get("level")
        logger_name = request.GET.get("logger")
        query = request.GET.get("q", "")

        # Search logs
        logs = log_aggregator.search_logs(
            query=query,
            level=level,
            logger=logger_name,
            hours_back=hours_back,
            limit=1000,  # Max export limit
        )

        if export_format == "json":
            response_data = [
                {
                    "timestamp": entry.timestamp.isoformat(),
                    "level": entry.level,
                    "logger": entry.logger,
                    "message": entry.message,
                    "service": entry.service,
                    "environment": entry.environment,
                    "trace_id": entry.trace_id,
                    "request_id": entry.request_id,
                    "source": entry.source,
                    "exception": entry.exception,
                    "extra": entry.extra,
                    "django": entry.django,
                    "performance": entry.performance,
                    "security": entry.security,
                }
                for entry in logs
            ]

            response = JsonResponse(
                {
                    "logs": response_data,
                    "export_info": {
                        "format": "json",
                        "count": len(response_data),
                        "exported_at": timezone.now().isoformat(),
                        "filters": {
                            "hours_back": hours_back,
                            "level": level,
                            "logger": logger_name,
                            "query": query,
                        },
                    },
                }
            )

            response["Content-Disposition"] = (
                f'attachment; filename="logs_export_{timezone.now().strftime("%Y%m%d_%H%M")}.json"'
            )

        elif export_format == "csv":
            import csv
            from io import StringIO

            output = StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(
                [
                    "timestamp",
                    "level",
                    "logger",
                    "message",
                    "service",
                    "trace_id",
                    "request_id",
                    "exception_type",
                    "exception_message",
                ]
            )

            # Write data
            for entry in logs:
                writer.writerow(
                    [
                        entry.timestamp.isoformat(),
                        entry.level,
                        entry.logger,
                        entry.message,
                        entry.service,
                        entry.trace_id,
                        entry.request_id,
                        entry.exception.get("type") if entry.exception else "",
                        entry.exception.get("message") if entry.exception else "",
                    ]
                )

            response = HttpResponse(output.getvalue(), content_type="text/csv")
            response["Content-Disposition"] = (
                f'attachment; filename="logs_export_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'
            )

        else:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Unsupported export format: {export_format}",
                },
                status=400,
            )

        logger.info(
            f"Logs exported by user {request.user}",
            extra={
                "export_format": export_format,
                "count": len(logs),
                "filters": {
                    "hours_back": hours_back,
                    "level": level,
                    "logger": logger_name,
                    "query": query,
                },
            },
        )

        return response

    except Exception as e:
        logger.error(f"Error exporting logs: {e}", exc_info=True)
        return JsonResponse(
            {
                "success": False,
                "error": str(e),
            },
            status=500,
        )
