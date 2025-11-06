#!/usr/bin/env python
"""
Security Checklist Script
Validates all security settings before deployment.

Usage:
    python scripts/security_check.py
    python scripts/security_check.py --environment production
    python scripts/security_check.py --verbose
"""

import argparse
import os
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings.simple")
import django

django.setup()

from django.conf import settings
from django.core.management import call_command


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


class SecurityChecker:
    """Comprehensive security checklist validator."""

    def __init__(self, environment="development", verbose=False):
        self.environment = environment
        self.verbose = verbose
        self.checks_passed = 0
        self.checks_failed = 0
        self.checks_warning = 0
        self.issues = []

    def print_header(self):
        """Print script header."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
        print(f"{Colors.BOLD}🔐 SECURITY CHECKLIST VALIDATION{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")
        print(f"Environment: {Colors.BOLD}{self.environment.upper()}{Colors.END}")
        print(f"Django Settings: {Colors.BOLD}{settings.SETTINGS_MODULE}{Colors.END}\n")

    def check(self, name, condition, severity="error", recommendation=""):
        """
        Check a security condition.

        Args:
            name: Name of the check
            condition: Boolean condition to check
            severity: 'error', 'warning', or 'info'
            recommendation: What to do if check fails
        """
        status_icons = {"passed": "✅", "failed": "❌", "warning": "⚠️", "error": "❌"}

        if condition:
            status = "passed"
            self.checks_passed += 1
            color = Colors.GREEN
        elif severity == "warning":
            status = "warning"
            self.checks_warning += 1
            color = Colors.YELLOW
        else:
            status = "failed"
            self.checks_failed += 1
            color = Colors.RED
            self.issues.append({"name": name, "recommendation": recommendation})

        display_status = (
            status if condition else ("warning" if severity == "warning" else "failed")
        )
        icon = status_icons[display_status]
        print(f"{icon} {color}{name}{Colors.END}")

        if self.verbose or not condition:
            if not condition and recommendation:
                print(f"   → {recommendation}")

    def check_secret_key(self):
        """Check SECRET_KEY security."""
        print(f"\n{Colors.BOLD}1. SECRET_KEY Security{Colors.END}")

        secret_key = settings.SECRET_KEY

        self.check(
            "SECRET_KEY is set",
            secret_key and secret_key != "",
            recommendation="Set SECRET_KEY in environment variables",
        )

        self.check(
            "SECRET_KEY is not default",
            secret_key != "your-secret-key-here",
            recommendation='Generate new SECRET_KEY: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"',
        )

        self.check(
            "SECRET_KEY is long enough (50+ chars)",
            len(secret_key) >= 50,
            severity="warning",
            recommendation="Use longer SECRET_KEY for better security",
        )

        self.check(
            "SECRET_KEY has variety of characters",
            len(set(secret_key)) >= 20,
            severity="warning",
            recommendation="Use more diverse characters in SECRET_KEY",
        )

    def check_debug_mode(self):
        """Check DEBUG mode setting."""
        print(f"\n{Colors.BOLD}2. Debug Mode{Colors.END}")

        is_production = self.environment == "production"

        self.check(
            (
                "DEBUG is False in production"
                if is_production
                else "DEBUG setting configured"
            ),
            not settings.DEBUG if is_production else True,
            recommendation="Set DEBUG=False in production environment",
        )

    def check_allowed_hosts(self):
        """Check ALLOWED_HOSTS configuration."""
        print(f"\n{Colors.BOLD}3. Allowed Hosts{Colors.END}")

        allowed_hosts = settings.ALLOWED_HOSTS
        is_production = self.environment == "production"

        self.check(
            "ALLOWED_HOSTS is configured",
            len(allowed_hosts) > 0,
            recommendation="Set ALLOWED_HOSTS in settings",
        )

        self.check(
            (
                "ALLOWED_HOSTS is not wildcard in production"
                if is_production
                else "ALLOWED_HOSTS configured"
            ),
            "*" not in allowed_hosts if is_production else True,
            recommendation="Set specific domains in ALLOWED_HOSTS, not '*'",
        )

    def check_https_settings(self):
        """Check HTTPS/TLS configuration."""
        print(f"\n{Colors.BOLD}4. HTTPS/TLS Configuration{Colors.END}")

        is_production = self.environment == "production"

        if is_production:
            self.check(
                "SECURE_SSL_REDIRECT enabled",
                getattr(settings, "SECURE_SSL_REDIRECT", False),
                recommendation="Set SECURE_SSL_REDIRECT=True in production",
            )

            self.check(
                "SESSION_COOKIE_SECURE enabled",
                getattr(settings, "SESSION_COOKIE_SECURE", False),
                recommendation="Set SESSION_COOKIE_SECURE=True in production",
            )

            self.check(
                "CSRF_COOKIE_SECURE enabled",
                getattr(settings, "CSRF_COOKIE_SECURE", False),
                recommendation="Set CSRF_COOKIE_SECURE=True in production",
            )

            hsts_seconds = getattr(settings, "SECURE_HSTS_SECONDS", 0)
            self.check(
                "HSTS enabled (31536000+ seconds)",
                hsts_seconds >= 31536000,
                severity="warning",
                recommendation="Set SECURE_HSTS_SECONDS=31536000 (1 year)",
            )

            self.check(
                "HSTS includeSubDomains enabled",
                getattr(settings, "SECURE_HSTS_INCLUDE_SUBDOMAINS", False),
                severity="warning",
                recommendation="Set SECURE_HSTS_INCLUDE_SUBDOMAINS=True",
            )
        else:
            print(f"   {Colors.YELLOW}→ HTTPS checks skipped (development){Colors.END}")

    def check_security_headers(self):
        """Check security headers configuration."""
        print(f"\n{Colors.BOLD}5. Security Headers{Colors.END}")

        self.check(
            "X_FRAME_OPTIONS configured",
            hasattr(settings, "X_FRAME_OPTIONS"),
            severity="warning",
            recommendation="Set X_FRAME_OPTIONS='DENY' or 'SAMEORIGIN'",
        )

        self.check(
            "SECURE_CONTENT_TYPE_NOSNIFF enabled",
            getattr(settings, "SECURE_CONTENT_TYPE_NOSNIFF", False),
            severity="warning",
            recommendation="Set SECURE_CONTENT_TYPE_NOSNIFF=True",
        )

        self.check(
            "SECURE_BROWSER_XSS_FILTER enabled",
            getattr(settings, "SECURE_BROWSER_XSS_FILTER", False),
            severity="warning",
            recommendation="Set SECURE_BROWSER_XSS_FILTER=True",
        )

    def check_csrf_protection(self):
        """Check CSRF protection."""
        print(f"\n{Colors.BOLD}6. CSRF Protection{Colors.END}")

        middleware = settings.MIDDLEWARE
        csrf_middleware = "django.middleware.csrf.CsrfViewMiddleware"

        self.check(
            "CsrfViewMiddleware enabled",
            csrf_middleware in middleware,
            recommendation=f"Add '{csrf_middleware}' to MIDDLEWARE",
        )

    def check_database_security(self):
        """Check database security settings."""
        print(f"\n{Colors.BOLD}7. Database Security{Colors.END}")

        db_engine = settings.DATABASES["default"]["ENGINE"]
        is_production = self.environment == "production"

        if is_production:
            self.check(
                "Using PostgreSQL in production",
                "postgresql" in db_engine,
                severity="warning",
                recommendation="Use PostgreSQL instead of SQLite in production",
            )

        # Check for default/weak database passwords
        db_password = settings.DATABASES["default"].get("PASSWORD", "")
        if db_password:
            self.check(
                "Database password is not empty",
                db_password != "",
                recommendation="Set strong database password",
            )

    def check_session_security(self):
        """Check session security settings."""
        print(f"\n{Colors.BOLD}8. Session Security{Colors.END}")

        self.check(
            "SESSION_COOKIE_HTTPONLY enabled",
            getattr(settings, "SESSION_COOKIE_HTTPONLY", False),
            recommendation="Set SESSION_COOKIE_HTTPONLY=True",
        )

        session_samesite = getattr(settings, "SESSION_COOKIE_SAMESITE", None)
        self.check(
            "SESSION_COOKIE_SAMESITE configured",
            session_samesite in ["Strict", "Lax"],
            severity="warning",
            recommendation="Set SESSION_COOKIE_SAMESITE='Strict' or 'Lax'",
        )

    def check_middleware_order(self):
        """Check middleware configuration and order."""
        print(f"\n{Colors.BOLD}9. Middleware Configuration{Colors.END}")

        middleware = settings.MIDDLEWARE
        required_middleware = [
            "django.middleware.security.SecurityMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
        ]

        for mw in required_middleware:
            self.check(
                f"{mw.split('.')[-1]} present",
                mw in middleware,
                recommendation=f"Add '{mw}' to MIDDLEWARE",
            )

    def check_password_hashers(self):
        """Check password hashing configuration."""
        print(f"\n{Colors.BOLD}10. Password Security{Colors.END}")

        hashers = getattr(settings, "PASSWORD_HASHERS", [])

        if hashers:
            first_hasher = hashers[0] if hashers else ""
            self.check(
                "Strong password hasher (Argon2 or PBKDF2)",
                "Argon2" in first_hasher or "PBKDF2" in first_hasher,
                severity="warning",
                recommendation="Use Argon2PasswordHasher as first hasher",
            )
        else:
            print(f"   {Colors.YELLOW}→ Using Django default hashers{Colors.END}")

    def run_django_checks(self):
        """Run Django's built-in security checks."""
        print(f"\n{Colors.BOLD}11. Django Security Checks{Colors.END}")

        try:
            # Capture output
            import sys
            from io import StringIO

            old_stdout = sys.stdout
            sys.stdout = StringIO()

            # Run Django check
            call_command("check", "--deploy", verbosity=0)

            output = sys.stdout.getvalue()
            sys.stdout = old_stdout

            if "System check identified no issues" in output or not output.strip():
                print(f"✅ {Colors.GREEN}Django deployment checks passed{Colors.END}")
                self.checks_passed += 1
            else:
                print(f"⚠️ {Colors.YELLOW}Django identified some issues{Colors.END}")
                if self.verbose:
                    print(output)
                self.checks_warning += 1

        except Exception as e:
            print(f"❌ {Colors.RED}Error running Django checks: {e}{Colors.END}")
            self.checks_failed += 1

    def print_summary(self):
        """Print final summary."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
        print(f"{Colors.BOLD}📊 SECURITY CHECK SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")

        total_checks = self.checks_passed + self.checks_failed + self.checks_warning

        print(f"Total Checks: {Colors.BOLD}{total_checks}{Colors.END}")
        print(f"✅ Passed: {Colors.GREEN}{Colors.BOLD}{self.checks_passed}{Colors.END}")
        print(
            f"⚠️  Warnings: {Colors.YELLOW}{Colors.BOLD}{self.checks_warning}{Colors.END}"
        )
        print(f"❌ Failed: {Colors.RED}{Colors.BOLD}{self.checks_failed}{Colors.END}\n")

        if self.checks_failed > 0:
            print(f"{Colors.RED}{Colors.BOLD}❌ SECURITY CHECKS FAILED{Colors.END}\n")
            print(f"{Colors.BOLD}Critical Issues to Fix:{Colors.END}")
            for i, issue in enumerate(self.issues, 1):
                print(f"\n{i}. {issue['name']}")
                print(f"   → {issue['recommendation']}")
            print()
            return False
        elif self.checks_warning > 0:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  PASSED WITH WARNINGS{Colors.END}\n")
            print(f"Consider addressing the warnings above.\n")
            return True
        else:
            print(
                f"{Colors.GREEN}{Colors.BOLD}✅ ALL SECURITY CHECKS PASSED!{Colors.END}\n"
            )
            return True

    def run_all_checks(self):
        """Run all security checks."""
        self.print_header()

        self.check_secret_key()
        self.check_debug_mode()
        self.check_allowed_hosts()
        self.check_https_settings()
        self.check_security_headers()
        self.check_csrf_protection()
        self.check_database_security()
        self.check_session_security()
        self.check_middleware_order()
        self.check_password_hashers()
        self.run_django_checks()

        return self.print_summary()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate security settings before deployment"
    )
    parser.add_argument(
        "--environment",
        choices=["development", "production", "staging"],
        default="development",
        help="Environment to check (default: development)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )

    args = parser.parse_args()

    checker = SecurityChecker(environment=args.environment, verbose=args.verbose)
    success = checker.run_all_checks()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
