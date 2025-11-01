"""
Security Views Module
====================

Handles security-related endpoints like CSP violation reports,
security monitoring, and other security features.
"""

import json
import logging

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from django_ratelimit.decorators import ratelimit

logger = logging.getLogger(__name__)


@require_http_methods(["POST"])
@csrf_exempt
@ratelimit(key="ip", rate="20/m", method="POST")
def csp_violation_report(request):
    """
    Handle CSP violation reports
    """
    try:
        data = json.loads(request.body)

        # Log CSP violation with structured logging
        csp_report = data.get("csp-report", {})
        logger.warning(
            "CSP Violation reported",
            extra={
                "violation_type": "csp",
                "blocked_uri": csp_report.get("blocked-uri", ""),
                "document_uri": csp_report.get("document-uri", ""),
                "violated_directive": csp_report.get("violated-directive", ""),
                "effective_directive": csp_report.get("effective-directive", ""),
                "original_policy": csp_report.get("original-policy", ""),
                "disposition": csp_report.get("disposition", ""),
                "script_sample": csp_report.get("script-sample", ""),
                "status_code": csp_report.get("status-code", ""),
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                "ip_address": request.META.get("REMOTE_ADDR", ""),
                "timestamp": timezone.now().isoformat(),
            },
        )

        # In production, you might want to store these in a database
        # or send them to a monitoring service like Sentry

        return JsonResponse({"status": "received"}, status=204)

    except json.JSONDecodeError:
        logger.error("Invalid JSON in CSP violation report")
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error processing CSP violation report: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
@ratelimit(key="ip", rate="20/m", method="POST")
def network_error_report(request):
    """
    Handle Network Error Logging (NEL) reports
    """
    try:
        data = json.loads(request.body)

        # Log network error
        logger.warning(
            "Network error reported",
            extra={
                "error_type": "network",
                "nel_report": data,
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                "ip_address": request.META.get("REMOTE_ADDR", ""),
                "timestamp": timezone.now().isoformat(),
            },
        )

        return JsonResponse({"status": "received"}, status=204)

    except json.JSONDecodeError:
        logger.error("Invalid JSON in network error report")
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error processing network error report: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)
