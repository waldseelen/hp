"""
Authentication and Security Views
================================

Views for 2FA setup, session management, and security dashboard.
"""

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from apps.main.models import UserSession


@login_required
def setup_2fa(request):
    """Setup Two-Factor Authentication"""
    user = request.user

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "enable":
            totp_token = request.POST.get("totp_token", "").strip()

            if not totp_token:
                messages.error(
                    request,
                    "Please enter the verification code from your authenticator app.",
                )
                return render(
                    request,
                    "auth/setup_2fa.html",
                    {
                        "qr_code": user.get_qr_code(),
                        "secret": user.totp_secret or user.generate_totp_secret(),
                    },
                )

            # Verify the token
            if user.verify_totp(totp_token):
                user.is_2fa_enabled = True
                user.save(update_fields=["is_2fa_enabled"])

                # Generate backup codes
                backup_codes = user.generate_backup_codes()

                messages.success(request, "2FA has been successfully enabled!")
                return render(
                    request, "auth/backup_codes.html", {"backup_codes": backup_codes}
                )
            else:
                messages.error(request, "Invalid verification code. Please try again.")

        elif action == "disable":
            password = request.POST.get("password", "")

            if user.check_password(password):
                user.is_2fa_enabled = False
                user.totp_secret = ""
                user.backup_codes = []
                user.save(
                    update_fields=["is_2fa_enabled", "totp_secret", "backup_codes"]
                )

                messages.success(request, "2FA has been disabled.")
                return redirect("setup_2fa")
            else:
                messages.error(request, "Incorrect password.")

        elif action == "regenerate_codes":
            backup_codes = user.generate_backup_codes()
            messages.success(request, "New backup codes generated!")
            return render(
                request, "auth/backup_codes.html", {"backup_codes": backup_codes}
            )

    # GET request - show setup page
    context = {
        "is_2fa_enabled": user.is_2fa_enabled,
        "backup_codes_count": len(user.backup_codes) if user.backup_codes else 0,
    }

    if not user.is_2fa_enabled:
        secret = user.totp_secret or user.generate_totp_secret()
        context.update(
            {
                "qr_code": user.get_qr_code(),
                "secret": secret,
            }
        )

    return render(request, "auth/setup_2fa.html", context)


@login_required
def session_management(request):
    """Session management dashboard"""
    user = request.user

    # Get all active sessions for the user
    sessions = user.sessions.filter(is_active=True).order_by("-last_activity")

    # Add device info to each session
    for session in sessions:
        session.device_info = session.get_device_info()
        session.is_current = session.session_key == request.session.session_key

    context = {
        "sessions": sessions,
        "current_session_key": request.session.session_key,
    }

    return render(request, "auth/session_management.html", context)


@login_required
@require_http_methods(["POST"])
def terminate_session(request):
    """Terminate a specific session"""
    session_key = request.POST.get("session_key")

    if not session_key:
        return JsonResponse({"success": False, "error": "Session key required"})

    try:
        session = UserSession.objects.get(
            session_key=session_key, user=request.user, is_active=True
        )

        # Don't allow terminating current session this way
        if session_key == request.session.session_key:
            return JsonResponse(
                {"success": False, "error": "Cannot terminate current session"}
            )

        session.deactivate()

        return JsonResponse(
            {"success": True, "message": "Session terminated successfully"}
        )

    except UserSession.DoesNotExist:
        return JsonResponse({"success": False, "error": "Session not found"})


@login_required
@require_http_methods(["POST"])
def terminate_all_sessions(request):
    """Terminate all other sessions except current"""
    user = request.user
    current_session_key = request.session.session_key

    # Deactivate all sessions except current
    terminated_count = (
        user.sessions.filter(is_active=True)
        .exclude(session_key=current_session_key)
        .update(is_active=False)
    )

    return JsonResponse(
        {
            "success": True,
            "message": f"{terminated_count} sessions terminated",
            "terminated_count": terminated_count,
        }
    )


@login_required
def security_dashboard(request):
    """Security overview dashboard"""
    user = request.user

    # Get recent login attempts
    failed_attempts = user.failed_login_attempts
    last_failed = user.last_failed_login

    # Get active sessions count
    active_sessions = user.sessions.filter(is_active=True).count()

    # Get recent sessions (last 10)
    recent_sessions = user.sessions.filter(is_active=True).order_by("-last_activity")[
        :10
    ]

    # Security score calculation
    security_score = 0
    security_factors = []

    # 2FA enabled (+40 points)
    if user.is_2fa_enabled:
        security_score += 40
        security_factors.append(
            {"name": "Two-Factor Authentication", "status": "enabled", "points": 40}
        )
    else:
        security_factors.append(
            {
                "name": "Two-Factor Authentication",
                "status": "disabled",
                "points": 0,
                "recommendation": "Enable 2FA for better security",
            }
        )

    # Strong password (+20 points - simplified check)
    if len(user.password) > 60:  # Hashed password length indicates strong password
        security_score += 20
        security_factors.append(
            {"name": "Strong Password", "status": "good", "points": 20}
        )

    # No recent failed attempts (+20 points)
    if failed_attempts == 0:
        security_score += 20
        security_factors.append(
            {"name": "No Failed Login Attempts", "status": "good", "points": 20}
        )
    else:
        security_factors.append(
            {
                "name": "Recent Failed Attempts",
                "status": "warning",
                "points": 0,
                "recommendation": f"{failed_attempts} failed attempts recorded",
            }
        )

    # Limited active sessions (+20 points if ≤ 3 sessions)
    if active_sessions <= 3:
        security_score += 20
        security_factors.append(
            {"name": "Session Management", "status": "good", "points": 20}
        )
    else:
        security_factors.append(
            {
                "name": "Too Many Active Sessions",
                "status": "warning",
                "points": 0,
                "recommendation": f"{active_sessions} active sessions",
            }
        )

    context = {
        "security_score": security_score,
        "security_factors": security_factors,
        "failed_attempts": failed_attempts,
        "last_failed": last_failed,
        "active_sessions": active_sessions,
        "recent_sessions": recent_sessions,
        "is_2fa_enabled": user.is_2fa_enabled,
        "account_locked": user.is_account_locked(),
    }

    return render(request, "auth/security_dashboard.html", context)


@csrf_protect
def two_factor_login(request):
    """Handle 2FA verification during login"""
    if request.method != "POST":
        return redirect("login")

    username = request.session.get("2fa_username")
    password = request.session.get("2fa_password")

    if not username or not password:
        messages.error(request, "Session expired. Please login again.")
        return redirect("login")

    totp_token = request.POST.get("totp_token", "").strip()
    backup_code = request.POST.get("backup_code", "").strip()

    if not totp_token and not backup_code:
        messages.error(
            request, "Please enter either a verification code or backup code."
        )
        return render(request, "auth/two_factor_login.html")

    # Authenticate with 2FA
    user = authenticate(
        request,
        username=username,
        password=password,
        totp_token=totp_token,
        backup_code=backup_code,
    )

    if user:
        login(request, user)

        # Clear 2FA session data
        del request.session["2fa_username"]
        del request.session["2fa_password"]

        messages.success(request, "Successfully logged in!")
        return redirect("home")
    else:
        messages.error(request, "Invalid verification code or backup code.")
        return render(request, "auth/two_factor_login.html")


@login_required
def change_password(request):
    """Enhanced password change with strength validation"""
    if request.method == "POST":
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        # Validate current password
        if not request.user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
            return render(request, "auth/change_password.html")

        # Validate new password
        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            return render(request, "auth/change_password.html")

        # Password strength validation
        strength_errors = validate_password_strength(new_password)
        if strength_errors:
            for error in strength_errors:
                messages.error(request, error)
            return render(request, "auth/change_password.html")

        # Set new password
        request.user.set_password(new_password)
        request.user.save()

        messages.success(request, "Password changed successfully!")
        return redirect("security_dashboard")

    return render(request, "auth/change_password.html")


def validate_password_strength(password):
    """Validate password strength"""
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")

    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter.")

    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter.")

    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number.")

    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one special character.")

    # Check for common patterns
    common_patterns = ["123456", "password", "qwerty", "admin"]
    if any(pattern in password.lower() for pattern in common_patterns):
        errors.append("Password contains common patterns that are not secure.")

    return errors
