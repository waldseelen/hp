"""
Health Check System for Docker Containers
==========================================

Provides comprehensive health checks for Django application components:
- Database connectivity
- Cache connectivity
- File system access
- External service dependencies
- Django application status

Used by Docker HEALTHCHECK directive and monitoring systems.
"""

import logging
import os
import time
from typing import Any, Dict

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


class HealthChecker:
    """Comprehensive health check system."""

    def __init__(self):
        self.checks = [
            self.check_database,
            self.check_cache,
            self.check_filesystem,
            self.check_external_services,
            self.check_django_setup,
        ]

    def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

            response_time = (time.time() - start_time) * 1000  # ms

            if result and result[0] == 1:
                status = "healthy" if response_time < 100 else "slow"
                return {
                    "name": "database",
                    "status": status,
                    "response_time_ms": round(response_time, 2),
                    "details": f"Database responding in {response_time:.2f}ms",
                }
            else:
                return {
                    "name": "database",
                    "status": "unhealthy",
                    "error": "Invalid database response",
                }

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"name": "database", "status": "unhealthy", "error": str(e)}

    def check_cache(self) -> Dict[str, Any]:
        """Check cache connectivity."""
        try:
            start_time = time.time()
            test_key = "health_check_test"
            test_value = "test_value"

            # Test cache write/read
            cache.set(test_key, test_value, 10)
            retrieved_value = cache.get(test_key)
            cache.delete(test_key)

            response_time = (time.time() - start_time) * 1000  # ms

            if retrieved_value == test_value:
                return {
                    "name": "cache",
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "details": f"Cache responding in {response_time:.2f}ms",
                }
            else:
                return {
                    "name": "cache",
                    "status": "unhealthy",
                    "error": "Cache write/read test failed",
                }

        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {"name": "cache", "status": "unhealthy", "error": str(e)}

    def check_filesystem(self) -> Dict[str, Any]:
        """Check filesystem access for media and logs."""
        try:
            # Check media directory
            media_path = getattr(settings, "MEDIA_ROOT", "/app/media")
            if not os.path.exists(media_path):
                os.makedirs(media_path, exist_ok=True)

            # Test write access
            test_file = os.path.join(media_path, ".health_check")
            with open(test_file, "w") as f:
                f.write("health_check")

            # Test read access
            with open(test_file, "r") as f:
                content = f.read()

            # Cleanup
            os.remove(test_file)

            if content == "health_check":
                return {
                    "name": "filesystem",
                    "status": "healthy",
                    "details": "Media directory read/write access confirmed",
                }
            else:
                return {
                    "name": "filesystem",
                    "status": "unhealthy",
                    "error": "File content verification failed",
                }

        except Exception as e:
            logger.error(f"Filesystem health check failed: {e}")
            return {"name": "filesystem", "status": "unhealthy", "error": str(e)}

    def check_external_services(self) -> Dict[str, Any]:
        """Check external service dependencies."""
        try:
            import requests

            # Check critical external services
            services = []

            # Example: Check Google Fonts (used in templates)
            try:
                response = requests.get(
                    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
                    timeout=5,
                )
                services.append(
                    {
                        "name": "google_fonts",
                        "status": (
                            "healthy" if response.status_code == 200 else "unhealthy"
                        ),
                        "status_code": response.status_code,
                    }
                )
            except requests.RequestException:
                services.append(
                    {
                        "name": "google_fonts",
                        "status": "unhealthy",
                        "error": "Connection timeout or failed",
                    }
                )

            # Overall status
            all_healthy = all(service["status"] == "healthy" for service in services)

            return {
                "name": "external_services",
                "status": "healthy" if all_healthy else "degraded",
                "services": services,
                "details": f"Checked {len(services)} external services",
            }

        except ImportError:
            return {
                "name": "external_services",
                "status": "skipped",
                "details": "requests library not available",
            }
        except Exception as e:
            logger.error(f"External services health check failed: {e}")
            return {"name": "external_services", "status": "unhealthy", "error": str(e)}

    def check_django_setup(self) -> Dict[str, Any]:
        """Check Django application setup and configuration."""
        try:
            import django

            # Check Django version
            django_version = django.get_version()

            # Check critical settings
            critical_settings = [
                "SECRET_KEY",
                "ALLOWED_HOSTS",
                "DATABASES",
            ]

            missing_settings = []
            for setting in critical_settings:
                if not hasattr(settings, setting) or not getattr(settings, setting):
                    missing_settings.append(setting)

            if missing_settings:
                return {
                    "name": "django_setup",
                    "status": "unhealthy",
                    "error": f"Missing critical settings: {', '.join(missing_settings)}",
                    "django_version": django_version,
                }

            return {
                "name": "django_setup",
                "status": "healthy",
                "django_version": django_version,
                "debug": settings.DEBUG,
                "details": "Django application properly configured",
            }

        except Exception as e:
            logger.error(f"Django setup health check failed: {e}")
            return {"name": "django_setup", "status": "unhealthy", "error": str(e)}

    def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all health checks and return comprehensive status

        REFACTORED: Complexity reduced from C:16 to B:4
        """
        start_time = time.time()

        # Execute all checks
        results = self._execute_checks()

        # Calculate overall status
        overall_status = self._calculate_overall_status(results)

        # Build response
        total_time = time.time() - start_time
        return self._build_response(overall_status, results, total_time)

    def _execute_checks(self) -> list:
        """
        Execute all health checks

        Complexity: 3
        """
        results = []

        for check in self.checks:
            try:
                result = check()
                results.append(result)
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                results.append(
                    {"name": check.__name__, "status": "error", "error": str(e)}
                )

        return results

    def _calculate_overall_status(self, results: list) -> str:
        """
        Calculate overall health status

        Complexity: 4
        """
        statuses = [result["status"] for result in results]

        if all(status == "healthy" for status in statuses):
            return "healthy"
        elif any(status == "unhealthy" for status in statuses):
            return "unhealthy"
        else:
            return "degraded"

    def _build_response(
        self, overall_status: str, results: list, total_time: float
    ) -> Dict[str, Any]:
        """
        Build health check response

        Complexity: 2
        """
        summary = self._build_summary(results)

        return {
            "status": overall_status,
            "timestamp": time.time(),
            "response_time": round(total_time * 1000, 2),
            "checks": results,
            "summary": summary,
        }

    def _build_summary(self, results: list) -> Dict[str, int]:
        """
        Build summary statistics

        Complexity: 1
        """
        return {
            "total_checks": len(results),
            "healthy": len([r for r in results if r["status"] == "healthy"]),
            "unhealthy": len([r for r in results if r["status"] == "unhealthy"]),
            "degraded": len([r for r in results if r["status"] == "degraded"]),
            "errors": len([r for r in results if r["status"] == "error"]),
        }


# Initialize health checker
health_checker = HealthChecker()


@csrf_exempt
@never_cache
def health_check_view(request):
    """
    Health check endpoint for Docker and monitoring systems.

    Returns:
        - 200: All systems healthy
        - 503: One or more systems unhealthy
        - 500: Health check system error
    """
    try:
        health_data = health_checker.run_all_checks()

        # Determine HTTP status code
        if health_data["status"] == "healthy":
            status_code = 200
        elif health_data["status"] == "degraded":
            status_code = 200  # Still functional
        else:
            status_code = 503  # Service unavailable

        return JsonResponse(health_data, status=status_code)

    except Exception as e:
        logger.error(f"Health check endpoint failed: {e}")
        return JsonResponse(
            {"status": "error", "error": str(e), "timestamp": time.time()}, status=500
        )


@csrf_exempt
@never_cache
def readiness_check_view(request):
    """
    Readiness check - lighter version for Kubernetes readiness probes.
    Only checks critical systems needed for the app to serve requests.
    """
    try:
        # Quick checks only
        checks = [health_checker.check_database, health_checker.check_django_setup]

        results = []
        for check in checks:
            result = check()
            results.append(result)

        # All critical systems must be healthy
        all_healthy = all(result["status"] == "healthy" for result in results)

        status_data = {
            "ready": all_healthy,
            "timestamp": time.time(),
            "checks": results,
        }

        return JsonResponse(status_data, status=200 if all_healthy else 503)

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JsonResponse(
            {"ready": False, "error": str(e), "timestamp": time.time()}, status=503
        )


@csrf_exempt
@never_cache
def liveness_check_view(request):
    """
    Liveness check - minimal check to verify the application is running.
    Used by Kubernetes liveness probes.
    """
    return JsonResponse({"alive": True, "timestamp": time.time()}, status=200)
