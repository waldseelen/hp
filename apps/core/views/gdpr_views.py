"""
GDPR Views
==========

Views for GDPR compliance features:
- Cookie consent management
- Privacy preferences
- Data export (Article 20)
- Data deletion (Article 17)
- Consent management
"""

import json
import logging
import secrets
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.middleware.gdpr_compliance import (
    clear_consent_cookie,
    invalidate_privacy_preferences_cache,
    set_consent_cookie,
)
from apps.core.models.gdpr import (
    ConsentRecord,
    DataDeletionRequest,
    DataExportRequest,
    PrivacyPreferences,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Cookie Consent Views
# ============================================================================


@require_http_methods(["GET", "POST"])
def cookie_consent(request):
    """
    Handle cookie consent.

    GET: Show consent banner
    POST: Save consent preferences
    """
    if request.method == "GET":
        return render(request, "gdpr/cookie_consent.html")

    # POST: Save consent
    try:
        data = json.loads(request.body)
        categories = data.get("categories", {})

        # Validate categories
        valid_categories = ["necessary", "functional", "analytics", "marketing"]
        for category in categories.keys():
            if category not in valid_categories:
                return JsonResponse(
                    {"success": False, "error": f"Invalid category: {category}"},
                    status=400,
                )

        # Necessary cookies are always allowed
        categories["necessary"] = True

        # Create response
        response = JsonResponse(
            {
                "success": True,
                "message": "Consent preferences saved",
                "categories": categories,
            }
        )

        # Set consent cookie
        set_consent_cookie(response, categories)

        # Log consent
        _log_consent(request, "cookie_consent", categories)

        logger.info(f"Cookie consent saved: {categories}")

        return response

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error saving consent: {e}")
        return JsonResponse(
            {"success": False, "error": "Failed to save consent"}, status=500
        )


@require_POST
def revoke_consent(request):
    """Revoke all cookie consent."""
    try:
        response = JsonResponse({"success": True, "message": "Consent revoked"})

        # Clear consent cookie
        clear_consent_cookie(response)

        # Log consent revocation
        _log_consent(request, "cookie_consent", {}, consented=False)

        logger.info("Cookie consent revoked")

        return response

    except Exception as e:
        logger.error(f"Error revoking consent: {e}")
        return JsonResponse(
            {"success": False, "error": "Failed to revoke consent"}, status=500
        )


# ============================================================================
# Privacy Preferences Views
# ============================================================================


@login_required
@require_http_methods(["GET", "POST"])
def privacy_preferences(request):  # noqa: C901
    """
    Manage privacy preferences.

    GET: Show preferences form
    POST: Update preferences
    """
    if request.method == "GET":
        return _get_privacy_preferences(request)

    return _update_privacy_preferences(request)


def _get_privacy_preferences(request):
    """Handle GET request for privacy preferences."""
    prefs, _ = PrivacyPreferences.objects.get_or_create(user=request.user)
    return render(request, "gdpr/privacy_preferences.html", {"preferences": prefs})


def _update_privacy_preferences(request):
    """Handle POST request to update privacy preferences."""
    try:
        data = json.loads(request.body)
        prefs, _ = PrivacyPreferences.objects.get_or_create(user=request.user)

        # Update all preference fields
        _update_preference_fields(prefs, data)
        prefs.save()

        # Invalidate cache
        invalidate_privacy_preferences_cache(request.user)

        logger.info(f"Privacy preferences updated for user {request.user.username}")

        return JsonResponse({"success": True, "message": "Privacy preferences updated"})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        return JsonResponse(
            {"success": False, "error": "Failed to update preferences"}, status=500
        )


def _update_preference_fields(prefs, data):
    """Update privacy preference fields from data."""
    if "data_retention_period" in data:
        period = int(data["data_retention_period"])
        if 30 <= period <= 3650:  # 30 days to 10 years
            prefs.data_retention_period = period

    if "allow_profiling" in data:
        prefs.allow_profiling = bool(data["allow_profiling"])

    if "allow_third_party" in data:
        prefs.allow_third_party = bool(data["allow_third_party"])

    if "allow_analytics" in data:
        prefs.allow_analytics = bool(data["allow_analytics"])

    if "communication_preferences" in data:
        prefs.communication_preferences = data["communication_preferences"]


# ============================================================================
# Data Export Views (Article 20 - Data Portability)
# ============================================================================


@login_required
@require_POST
def request_data_export(request):
    """
    Request data export (GDPR Article 20).

    User can request a copy of all their personal data.
    """
    try:
        data = json.loads(request.body)

        export_format = data.get("format", "json")
        include_categories = data.get(
            "categories", ["profile", "content", "activity", "preferences"]
        )

        # Create export request
        export_request = DataExportRequest.objects.create(
            user=request.user,
            export_format=export_format,
            include_categories=include_categories,
        )

        # Queue export job (async processing)
        # export_user_data_task.delay(export_request.id)

        logger.info(
            f"Data export requested by user {request.user.username}: "
            f"{export_request.id}"
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Data export request created. You will receive an email when ready.",
                "request_id": str(export_request.id),
                "status": export_request.status,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error creating export request: {e}")
        return JsonResponse(
            {"success": False, "error": "Failed to create export request"}, status=500
        )


@login_required
@require_http_methods(["GET"])
def data_export_status(request, request_id):
    """Check status of data export request."""
    try:
        export_request = get_object_or_404(
            DataExportRequest, id=request_id, user=request.user
        )

        response_data = {
            "request_id": str(export_request.id),
            "status": export_request.status,
            "requested_at": export_request.requested_at.isoformat(),
        }

        if export_request.status == "completed":
            response_data.update(
                {
                    "download_url": export_request.download_url,
                    "download_expires_at": (
                        export_request.download_expires_at.isoformat()
                        if export_request.download_expires_at
                        else None
                    ),
                    "file_size": export_request.file_size,
                }
            )

        if export_request.status == "failed":
            response_data["error_message"] = export_request.error_message

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Error getting export status: {e}")
        return JsonResponse(
            {"success": False, "error": "Failed to get export status"}, status=500
        )


@login_required
@require_http_methods(["GET"])
def download_data_export(request, request_id):
    """Download completed data export."""
    try:
        export_request = get_object_or_404(
            DataExportRequest, id=request_id, user=request.user, status="completed"
        )

        # Check if download link expired
        if (
            export_request.download_expires_at
            and timezone.now() > export_request.download_expires_at
        ):
            return JsonResponse(
                {
                    "success": False,
                    "error": "Download link has expired. Please request a new export.",
                },
                status=410,
            )

        # Serve file
        import os

        if not os.path.exists(export_request.file_path):
            return JsonResponse(
                {"success": False, "error": "Export file not found"}, status=404
            )

        response = FileResponse(
            open(export_request.file_path, "rb"),
            content_type="application/octet-stream",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="data_export_{request_id}.{export_request.export_format}"'
        )

        logger.info(f"Data export downloaded: {request_id}")

        return response

    except Exception as e:
        logger.error(f"Error downloading export: {e}")
        return JsonResponse(
            {"success": False, "error": "Failed to download export"}, status=500
        )


# ============================================================================
# Data Deletion Views (Article 17 - Right to Erasure)
# ============================================================================


@login_required
@require_POST
def request_data_deletion(request):
    """
    Request data deletion (GDPR Article 17).

    User can request deletion of their personal data.
    Includes verification step to prevent accidental deletion.
    """
    try:
        data = json.loads(request.body)

        delete_account = data.get("delete_account", True)
        delete_categories = data.get("categories", [])

        # Generate verification code
        verification_code = secrets.token_hex(3).upper()  # 6-character code

        # Create deletion request
        deletion_request = DataDeletionRequest.objects.create(
            user=request.user,
            delete_account=delete_account,
            delete_categories=delete_categories,
            verification_code=verification_code,
            verification_expires_at=timezone.now() + timedelta(hours=24),
            scheduled_deletion_at=timezone.now()
            + timedelta(days=30),  # 30-day grace period
        )

        # Send verification email
        _send_deletion_verification_email(
            request.user.email, verification_code, str(deletion_request.id)
        )

        logger.info(
            f"Data deletion requested by user {request.user.username}: "
            f"{deletion_request.id}"
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Data deletion request created. Please check your email for verification code.",
                "request_id": str(deletion_request.id),
                "scheduled_deletion_at": deletion_request.scheduled_deletion_at.isoformat(),
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error creating deletion request: {e}")
        return JsonResponse(
            {"success": False, "error": "Failed to create deletion request"}, status=500
        )


@login_required
@require_POST
def verify_data_deletion(request, request_id):
    """Verify data deletion request with code."""
    try:
        data = json.loads(request.body)
        verification_code = data.get("code", "").upper()

        deletion_request = get_object_or_404(
            DataDeletionRequest, id=request_id, user=request.user, status="pending"
        )

        # Check if code expired
        if timezone.now() > deletion_request.verification_expires_at:
            return JsonResponse(
                {"success": False, "error": "Verification code has expired"}, status=400
            )

        # Verify code
        if deletion_request.verification_code != verification_code:
            return JsonResponse(
                {"success": False, "error": "Invalid verification code"}, status=400
            )

        # Mark as confirmed
        deletion_request.status = "confirmed"
        deletion_request.verified_at = timezone.now()
        deletion_request.save()

        logger.info(f"Data deletion verified: {request_id}")

        return JsonResponse(
            {
                "success": True,
                "message": f'Deletion confirmed. Your data will be deleted on {deletion_request.scheduled_deletion_at.strftime("%Y-%m-%d")}',
                "scheduled_deletion_at": deletion_request.scheduled_deletion_at.isoformat(),
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error verifying deletion: {e}")
        return JsonResponse(
            {"success": False, "error": "Failed to verify deletion"}, status=500
        )


@login_required
@require_POST
def cancel_data_deletion(request, request_id):
    """Cancel data deletion request (before execution)."""
    try:
        deletion_request = get_object_or_404(
            DataDeletionRequest, id=request_id, user=request.user
        )

        # Can only cancel pending or confirmed requests
        if deletion_request.status not in ["pending", "confirmed"]:
            return JsonResponse(
                {"success": False, "error": "Cannot cancel deletion in current status"},
                status=400,
            )

        deletion_request.status = "cancelled"
        deletion_request.save()

        logger.info(f"Data deletion cancelled: {request_id}")

        return JsonResponse({"success": True, "message": "Deletion request cancelled"})

    except Exception as e:
        logger.error(f"Error cancelling deletion: {e}")
        return JsonResponse(
            {"success": False, "error": "Failed to cancel deletion"}, status=500
        )


# ============================================================================
# Helper Functions
# ============================================================================


def _log_consent(request, consent_type, categories, consented=True):
    """Log consent to database."""
    try:
        ConsentRecord.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_id=request.session.session_key or "",
            ip_address=_get_client_ip(request),
            consent_type=consent_type,
            consented=consented,
            consent_text=f"Cookie consent: {json.dumps(categories)}",
            consent_version="1.0",
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )
    except Exception as e:
        logger.error(f"Failed to log consent: {e}")


def _get_client_ip(request):
    """Get client IP address."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def _send_deletion_verification_email(email, code, request_id):
    """Send deletion verification email."""
    try:
        subject = "Verify Data Deletion Request"
        message = f"""
You have requested to delete your personal data.

Verification Code: {code}

This code will expire in 24 hours.

If you did not request this deletion, please ignore this email.

Request ID: {request_id}
"""

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Failed to send deletion verification email: {e}")
        raise
