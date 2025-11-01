"""
GDPR Compliance Views
====================

Views for cookie consent, data export, account deletion, and privacy management.
"""

import json
import zipfile
from io import StringIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import models
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from apps.main.models import CookieConsent
from apps.portfolio.models import AccountDeletionRequest


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR", "127.0.0.1")
    return ip


@require_http_methods(["POST"])
@csrf_protect
def cookie_consent(request):
    """Handle cookie consent preferences"""
    try:
        data = json.loads(request.body)

        # Get session key
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key

        # Get or create consent record
        consent, created = CookieConsent.objects.get_or_create(
            session_key=session_key,
            defaults={
                "ip_address": get_client_ip(request),
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            },
        )

        # Update consent preferences
        consent.necessary = True  # Always required
        consent.functional = data.get("functional", False)
        consent.analytics = data.get("analytics", False)
        consent.marketing = data.get("marketing", False)
        consent.consent_given_at = timezone.now()
        consent.save()

        # Store consent in session for quick access
        request.session["cookie_consent"] = consent.get_consent_summary()
        request.session["consent_given"] = True

        return JsonResponse(
            {"success": True, "message": "Cookie preferences saved successfully"}
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


def cookie_policy(request):
    """Display cookie policy page"""
    return render(request, "gdpr/cookie_policy.html")


def privacy_policy(request):
    """Display privacy policy page"""
    return render(request, "gdpr/privacy_policy.html")


@login_required
def privacy_dashboard(request):
    """Privacy management dashboard"""
    user = request.user

    # Get cookie consent
    session_key = request.session.session_key
    cookie_consent = None
    if session_key:
        try:
            cookie_consent = CookieConsent.objects.get(session_key=session_key)
        except CookieConsent.DoesNotExist:
            pass

    # Get data summary
    data_summary = {
        "contact_messages": 0,
        "chat_messages": 0,
        "last_login": user.last_login,
        "date_joined": user.date_joined,
        "account_status": "Active" if user.is_active else "Inactive",
    }

    try:
        from contact.models import ContactMessage

        data_summary["contact_messages"] = ContactMessage.objects.filter(
            models.Q(email=user.email) | models.Q(user=user)
        ).count()
    except Exception:
        pass

    try:
        from chat.models import ChatMessage

        data_summary["chat_messages"] = ChatMessage.objects.filter(user=user).count()
    except Exception:
        pass

    context = {
        "cookie_consent": cookie_consent,
        "data_summary": data_summary,
    }

    return render(request, "gdpr/privacy_dashboard.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def request_data_export(request):
    """Request data export"""
    if request.method == "GET":
        return render(request, "gdpr/data_export.html")

    user = request.user
    export_format = request.POST.get("format", "json")

    try:
        export_data = generate_user_data_export(user)

        if export_format == "json":
            response = HttpResponse(
                json.dumps(export_data, indent=2, ensure_ascii=False),
                content_type="application/json",
            )
            response["Content-Disposition"] = (
                f'attachment; filename="user_data_{user.id}.json"'
            )

        elif export_format == "csv":
            output = StringIO()
            # Write basic user info
            output.write(f"User Data Export for {user.username}\n")
            output.write(
                f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )

            # Personal info
            output.write("PERSONAL INFORMATION\n")
            for key, value in export_data["personal_info"].items():
                output.write(f"{key}: {value}\n")
            output.write("\n")

            # Contact messages
            if export_data["contact_messages"]:
                output.write("CONTACT MESSAGES\n")
                for msg in export_data["contact_messages"]:
                    output.write(f"Subject: {msg['subject']}\n")
                    output.write(f"Date: {msg['created_at']}\n")
                    output.write(f"Message: {msg['message']}\n\n")

            response = HttpResponse(output.getvalue(), content_type="text/csv")
            response["Content-Disposition"] = (
                f'attachment; filename="user_data_{user.id}.csv"'
            )

        elif export_format == "zip":
            # Create ZIP file with multiple formats
            import io

            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                # Add JSON export
                json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
                zip_file.writestr(f"user_data_{user.id}.json", json_data)

                # Add CSV summary
                csv_output = StringIO()
                csv_output.write("User Data Export Summary\n")
                csv_output.write(f"Username: {user.username}\n")
                csv_output.write(f"Email: {user.email}\n")
                csv_output.write(
                    f"Export Date: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                csv_output.write(
                    f"Total Contact Messages: {len(export_data['contact_messages'])}\n"
                )
                csv_output.write(
                    f"Total Chat Messages: {len(export_data['chat_messages'])}\n"
                )

                zip_file.writestr(
                    f"user_data_summary_{user.id}.csv", csv_output.getvalue()
                )

                # Add README
                readme = f"""User Data Export
================

This export contains all personal data associated with your account.
Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

Files included:
- user_data_{user.id}.json: Complete data in JSON format
- user_data_summary_{user.id}.csv: Summary information
- README.txt: This file

For questions, contact: privacy@example.com
"""
                zip_file.writestr("README.txt", readme)

            response = HttpResponse(
                zip_buffer.getvalue(), content_type="application/zip"
            )
            response["Content-Disposition"] = (
                f'attachment; filename="user_data_{user.id}.zip"'
            )

        else:
            messages.error(request, "Invalid export format.")
            return redirect("gdpr:data_export")

        return response

    except Exception as e:
        messages.error(request, f"Data export failed: {str(e)}")
        return redirect("gdpr:data_export")


@login_required
@require_http_methods(["GET", "POST"])
def request_account_deletion(request):  # noqa: C901
    """Request account deletion"""
    if request.method == "GET":
        return render(request, "gdpr/account_deletion.html")

    user = request.user
    deletion_type = request.POST.get("deletion_type", "soft")
    confirmation = request.POST.get("confirmation", "").strip().lower()
    # TODO: Log deletion reason for compliance records
    # reason = request.POST.get("reason", "")

    # Require explicit confirmation
    if confirmation != "delete my account":
        messages.error(request, 'Please type "delete my account" to confirm deletion.')
        return redirect("gdpr:account_deletion")

    try:
        from django.contrib.auth import logout
        from django.db import transaction

        with transaction.atomic():
            # TODO: Store user data backup for GDPR compliance
            # user_data_backup = generate_user_data_export(user)

            if deletion_type == "soft":
                # Soft delete - anonymize data
                original_email = user.email  # Needed for ContactMessage cleanup

                user.username = (
                    f"deleted_user_{user.id}_{int(timezone.now().timestamp())}"
                )
                user.email = f"deleted_{user.id}@deleted.local"
                user.first_name = ""
                user.last_name = ""
                user.is_active = False
                user.save()

                # Anonymize contact messages
                try:
                    from contact.models import ContactMessage

                    ContactMessage.objects.filter(
                        models.Q(email=original_email) | models.Q(user=user)
                    ).update(
                        name="Deleted User",
                        email=f"deleted_{user.id}@deleted.local",
                        user=None,
                    )
                except Exception:
                    pass

                # Anonymize chat messages
                try:
                    from chat.models import ChatMessage

                    ChatMessage.objects.filter(user=user).update(
                        user=None, username="Deleted User"
                    )
                except Exception:
                    pass

                messages.success(
                    request, "Your account has been anonymized successfully."
                )

            elif deletion_type == "hard":
                # Hard delete - completely remove
                # TODO: Log user_id for audit trail before deletion
                # user_id = user.id

                # Delete related data
                try:
                    from contact.models import ContactMessage

                    ContactMessage.objects.filter(
                        models.Q(email=user.email) | models.Q(user=user)
                    ).delete()
                except Exception:
                    pass

                try:
                    from chat.models import ChatMessage

                    ChatMessage.objects.filter(user=user).delete()
                except Exception:
                    pass

                # Delete user account
                user.delete()

                messages.success(
                    request, "Your account and all data have been permanently deleted."
                )

            # Log out user
            logout(request)

        return redirect("home")

    except Exception as e:
        messages.error(request, f"Account deletion failed: {str(e)}")
        return redirect("gdpr:account_deletion")


def confirm_account_deletion(request, token):
    """Confirm account deletion via email link"""
    try:
        deletion_request = get_object_or_404(
            AccountDeletionRequest, confirmation_token=token, status="pending"
        )

        if deletion_request.is_expired():
            messages.error(request, "Deletion confirmation link has expired.")
            return redirect("home")

        if request.method == "POST":
            # Final confirmation
            password = request.POST.get("password")

            if deletion_request.user.check_password(password):
                deletion_request.confirm_deletion()

                # Backup user data
                deletion_request.user_data_backup = generate_user_data_export(
                    deletion_request.user
                )
                deletion_request.save()

                messages.success(
                    request,
                    "Account deletion confirmed. Your account will be deleted within 30 days.",
                )
                return redirect("home")
            else:
                messages.error(request, "Incorrect password.")

        return render(
            request,
            "gdpr/confirm_deletion.html",
            {"deletion_request": deletion_request},
        )

    except AccountDeletionRequest.DoesNotExist:
        messages.error(request, "Invalid deletion confirmation link.")
        return redirect("home")


@login_required
def cancel_account_deletion(request, request_id):
    """Cancel account deletion request"""
    deletion_request = get_object_or_404(
        AccountDeletionRequest,
        id=request_id,
        user=request.user,
        status__in=["pending", "confirmed"],
    )

    deletion_request.cancel_deletion()
    messages.success(request, "Account deletion request has been cancelled.")

    return redirect("privacy_dashboard")


def generate_user_data_export(user):
    """Generate comprehensive user data export"""
    export_data = {
        "export_info": {
            "generated_at": timezone.now().isoformat(),
            "user_id": user.id,
            "export_type": "complete_user_data",
        },
        "personal_info": {
            "username": user.username,
            "email": user.email,
            "first_name": getattr(user, "first_name", ""),
            "last_name": getattr(user, "last_name", ""),
            "date_joined": user.date_joined.isoformat() if user.date_joined else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "is_active": user.is_active,
        },
        "contact_messages": [],
        "chat_messages": [],
        "blog_interactions": [],
        "cookie_consent": {},
        "export_requests": [],
        "deletion_requests": [],
    }

    # Collect contact messages
    try:
        from contact.models import ContactMessage

        messages = ContactMessage.objects.filter(
            models.Q(email=user.email) | models.Q(user=user)
        ).values("subject", "message", "created_at", "name", "email")
        export_data["contact_messages"] = [
            {
                "subject": msg["subject"],
                "message": msg["message"],
                "created_at": (
                    msg["created_at"].isoformat() if msg["created_at"] else None
                ),
                "name": msg["name"],
                "email": msg["email"],
            }
            for msg in messages
        ]
    except Exception:
        pass

    # Collect chat messages
    try:
        from chat.models import ChatMessage

        messages = ChatMessage.objects.filter(user=user).values(
            "message", "created_at", "room_name"
        )
        export_data["chat_messages"] = [
            {
                "message": msg["message"],
                "created_at": (
                    msg["created_at"].isoformat() if msg["created_at"] else None
                ),
                "room_name": msg["room_name"],
            }
            for msg in messages
        ]
    except Exception:
        pass

    # Collect cookie consent
    try:
        session_key = getattr(user, "session_key", None)
        if session_key:
            consent = CookieConsent.objects.filter(session_key=session_key).first()
            if consent:
                export_data["cookie_consent"] = {
                    "consent_given_at": (
                        consent.consent_given_at.isoformat()
                        if consent.consent_given_at
                        else None
                    ),
                    "necessary": consent.necessary,
                    "functional": consent.functional,
                    "analytics": consent.analytics,
                    "marketing": consent.marketing,
                }
    except Exception:
        pass

    return export_data


def send_export_email(user, email, filename):
    """Send data export completion email"""
    subject = "Your Data Export is Ready"
    message = render_to_string(
        "emails/data_export_ready.txt",
        {
            "user": user,
            "filename": filename,
        },
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


def send_deletion_confirmation_email(user, token):
    """Send account deletion confirmation email"""
    subject = "Confirm Account Deletion Request"
    confirmation_url = (
        f"{settings.SITE_URL}{reverse('confirm_account_deletion', args=[token])}"
    )

    message = render_to_string(
        "emails/deletion_confirmation.txt",
        {
            "user": user,
            "confirmation_url": confirmation_url,
        },
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


@require_http_methods(["GET"])
def cookie_consent_status(request):
    """Get current cookie consent status"""
    consent_given = request.session.get("consent_given", False)
    consent_preferences = request.session.get(
        "cookie_consent",
        {
            "necessary": True,
            "functional": False,
            "analytics": False,
            "marketing": False,
        },
    )

    return JsonResponse(
        {"consent_given": consent_given, "preferences": consent_preferences}
    )


def data_retention_policy(request):
    """Display data retention policy"""
    return render(request, "gdpr/data_retention_policy.html")


def user_rights(request):
    """Display user rights under GDPR"""
    return render(request, "gdpr/user_rights.html")
