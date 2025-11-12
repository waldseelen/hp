"""
Privacy-Compliant Analytics System
GDPR/KVKK compliant user analytics without collecting personal data
"""

import hashlib
import logging
from datetime import datetime, timedelta

from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class PrivacyCompliantAnalytics:
    """
    Analytics system that respects user privacy
    - No personal data collection
    - No cross-site tracking
    - Anonymous session-based tracking
    - GDPR/KVKK compliant
    - User journey tracking
    - Conversion funnel analysis
    - A/B testing support
    """

    def __init__(self):
        self.cache_timeout = 86400  # 24 hours
        self.session_timeout = 1800  # 30 minutes
        self.funnel_timeout = 3600  # 1 hour for funnel tracking
        self.journey_timeout = 7200  # 2 hours for journey tracking

    def get_anonymous_id(self, request):
        """
        Generate anonymous session ID without tracking personal data
        """
        if hasattr(request, "session") and request.session.session_key:
            session_key = request.session.session_key
        else:
            # Generate anonymous ID based on non-personal request data
            user_agent = request.META.get("HTTP_USER_AGENT", "")[:100]
            accept_lang = request.META.get("HTTP_ACCEPT_LANGUAGE", "")[:20]

            # Create anonymous fingerprint (not personally identifiable)
            fingerprint_data = f"{user_agent}:{accept_lang}:{datetime.now().date()}"
            session_key = hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]

        return f"anon_{session_key}"

    def track_page_view(self, request, page_path, page_title=None):
        """
        Track page view with privacy compliance
        """
        try:
            anonymous_id = self.get_anonymous_id(request)
            timestamp = timezone.now()
            device_info = self._get_device_info(request)

            event = {
                "type": "page_view",
                "anonymous_id": anonymous_id,
                "page_path": self._sanitize_path(page_path),
                "page_title": page_title[:100] if page_title else None,
                "timestamp": timestamp.isoformat(),
                "referrer": self._get_sanitized_referrer(request),
                "device_info": device_info,
            }

            # Store in cache for fast access
            self._store_event(event)
            self._update_session(anonymous_id, event)

            # Store in database for persistence (async task in production)
            try:
                self._store_event_to_db(event, request, device_info)
            except Exception as e:
                logger.warning(f"Failed to store event to database: {e}")

            return True

        except Exception as e:
            logger.error(f"Failed to track page view: {e}")
            return False

    def track_event(self, request, event_name, event_data=None):
        """
        Track custom event (clicks, form submissions, etc.)
        """
        try:
            anonymous_id = self.get_anonymous_id(request)
            timestamp = timezone.now()

            event = {
                "type": "custom_event",
                "event_name": event_name,
                "anonymous_id": anonymous_id,
                "timestamp": timestamp.isoformat(),
                "event_data": self._sanitize_event_data(event_data),
                "page_path": self._sanitize_path(request.path),
            }

            self._store_event(event)
            self._update_session(anonymous_id, event)

            return True

        except Exception as e:
            logger.error(f"Failed to track event: {e}")
            return False

    def track_conversion(self, request, conversion_type, conversion_value=None):
        """
        Track conversion events
        """
        try:
            anonymous_id = self.get_anonymous_id(request)

            event = {
                "type": "conversion",
                "conversion_type": conversion_type,
                "conversion_value": conversion_value,
                "anonymous_id": anonymous_id,
                "timestamp": timezone.now().isoformat(),
                "page_path": self._sanitize_path(request.path),
            }

            self._store_event(event)
            self._update_conversion_metrics(conversion_type)

            return True

        except Exception as e:
            logger.error(f"Failed to track conversion: {e}")
            return False

    def _sanitize_path(self, path):
        """Sanitize URL path"""
        if not path:
            return "/"
        path = path.split("?")[0][:200]

        # Remove sensitive patterns
        sensitive_patterns = ["/admin/", "/api/keys/", "/private/"]
        for pattern in sensitive_patterns:
            if pattern in path:
                return "/private/"

        return path

    def _get_sanitized_referrer(self, request):
        """Get sanitized referrer"""
        referrer = request.META.get("HTTP_REFERER", "")
        if not referrer:
            return None

        if any(domain in referrer for domain in ["google.com", "bing.com"]):
            return "search"
        elif any(domain in referrer for domain in ["facebook.com", "twitter.com"]):
            return "social"
        else:
            return "external"

    def _get_device_info(self, request):
        """Get basic device info"""
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        return {
            "is_mobile": "Mobile" in user_agent or "Android" in user_agent,
            "browser_family": self._get_browser_family(user_agent),
            "os_family": self._get_os_family(user_agent),
        }

    def _get_browser_family(self, user_agent):
        """Detect browser family"""
        if "Chrome" in user_agent:
            return "Chrome"
        elif "Firefox" in user_agent:
            return "Firefox"
        elif "Safari" in user_agent:
            return "Safari"
        else:
            return "Other"

    def _get_os_family(self, user_agent):
        """Detect OS family"""
        if "Windows" in user_agent:
            return "Windows"
        elif "Mac" in user_agent:
            return "Mac"
        elif "Android" in user_agent:
            return "Android"
        else:
            return "Other"

    def _update_session(self, anonymous_id, event):
        """Update session data"""
        session_key = f"analytics_session_{anonymous_id}"
        session_data = cache.get(
            session_key,
            {
                "first_visit": timezone.now().isoformat(),
                "page_count": 0,
                "event_count": 0,
            },
        )

        if event["type"] == "page_view":
            session_data["page_count"] += 1
        else:
            session_data["event_count"] += 1

        session_data["last_activity"] = timezone.now().isoformat()
        cache.set(session_key, session_data, self.session_timeout)

    def _sanitize_event_data(self, event_data):
        """Sanitize event data"""
        if not event_data:
            return None

        if isinstance(event_data, dict):
            sanitized = {}
            for key, value in event_data.items():
                if not any(
                    sensitive in key.lower()
                    for sensitive in ["password", "email", "phone"]
                ):
                    sanitized[key] = (
                        str(value)[:100] if isinstance(value, str) else value
                    )
            return sanitized

        return str(event_data)[:100]

    def _store_event(self, event):
        """Store analytics event"""
        try:
            # Store in daily aggregation
            date_key = datetime.now().date().isoformat()
            daily_events_key = f"analytics_daily_{date_key}"

            daily_events = cache.get(daily_events_key, [])
            daily_events.append(event)

            if len(daily_events) > 1000:  # Limit
                daily_events = daily_events[-1000:]

            cache.set(daily_events_key, daily_events, self.cache_timeout)

        except Exception as e:
            logger.error(f"Failed to store event: {e}")

    def _update_conversion_metrics(self, conversion_type):
        """Update conversion metrics"""
        try:
            date_key = datetime.now().date().isoformat()
            metrics_key = f"analytics_conversions_{date_key}"

            conversions = cache.get(metrics_key, {})
            conversions[conversion_type] = conversions.get(conversion_type, 0) + 1

            cache.set(metrics_key, conversions, self.cache_timeout)

        except Exception as e:
            logger.error(f"Failed to update conversion metrics: {e}")

    def get_analytics_summary(self, days=7):
        """Get analytics summary"""
        try:
            summary = {
                "page_views": {},
                "events": {},
                "conversions": {},
                "devices": {"mobile": 0, "desktop": 0},
                "browsers": {},
                "top_pages": {},
            }

            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).date()
                date_key = date.isoformat()

                # Get daily events
                daily_events = cache.get(f"analytics_daily_{date_key}", [])

                for event in daily_events:
                    if event["type"] == "page_view":
                        page_path = event.get("page_path", "unknown")
                        summary["page_views"][date_key] = (
                            summary["page_views"].get(date_key, 0) + 1
                        )
                        summary["top_pages"][page_path] = (
                            summary["top_pages"].get(page_path, 0) + 1
                        )

                        # Device info
                        device_info = event.get("device_info", {})
                        if device_info.get("is_mobile"):
                            summary["devices"]["mobile"] += 1
                        else:
                            summary["devices"]["desktop"] += 1

                        # Browser info
                        browser = device_info.get("browser_family", "Unknown")
                        summary["browsers"][browser] = (
                            summary["browsers"].get(browser, 0) + 1
                        )

                    elif event["type"] == "custom_event":
                        event_name = event.get("event_name", "unknown")
                        summary["events"][event_name] = (
                            summary["events"].get(event_name, 0) + 1
                        )

                # Get conversions
                daily_conversions = cache.get(f"analytics_conversions_{date_key}", {})
                for conv_type, count in daily_conversions.items():
                    summary["conversions"][conv_type] = (
                        summary["conversions"].get(conv_type, 0) + count
                    )

            return summary

        except Exception as e:
            logger.error(f"Failed to get analytics summary: {e}")
            return {}

    def track_user_journey(self, request, step_name, journey_id=None):
        """
        Track user journey through the site
        """
        try:
            anonymous_id = self.get_anonymous_id(request)

            if not journey_id:
                journey_id = f"journey_{anonymous_id}_{int(timezone.now().timestamp())}"

            journey_key = f"user_journey_{journey_id}"
            journey_data = cache.get(
                journey_key,
                {
                    "anonymous_id": anonymous_id,
                    "started_at": timezone.now().isoformat(),
                    "steps": [],
                    "current_step": None,
                },
            )

            step_data = {
                "step_name": step_name,
                "timestamp": timezone.now().isoformat(),
                "page_path": self._sanitize_path(request.path),
                "referrer": self._get_sanitized_referrer(request),
            }

            journey_data["steps"].append(step_data)
            journey_data["current_step"] = step_name
            journey_data["last_activity"] = timezone.now().isoformat()

            cache.set(journey_key, journey_data, self.journey_timeout)

            # Track journey metrics
            self._update_journey_metrics(step_name)

            # Store in database for persistence
            try:
                self._store_journey_to_db(journey_id, anonymous_id, step_name, request)
            except Exception as e:
                logger.warning(f"Failed to store journey to database: {e}")

            return journey_id

        except Exception as e:
            logger.error(f"Failed to track user journey: {e}")
            return None

    def track_funnel_step(self, request, funnel_name, step_name, step_order):
        """
        Track conversion funnel progression
        """
        try:
            anonymous_id = self.get_anonymous_id(request)

            funnel_key = f"funnel_{funnel_name}_{anonymous_id}"
            funnel_data = cache.get(
                funnel_key,
                {
                    "funnel_name": funnel_name,
                    "anonymous_id": anonymous_id,
                    "started_at": timezone.now().isoformat(),
                    "steps_completed": [],
                    "current_step": None,
                    "completed": False,
                },
            )

            # Add current step
            step_info = {
                "step_name": step_name,
                "step_order": step_order,
                "timestamp": timezone.now().isoformat(),
                "time_spent": self._calculate_time_spent(funnel_data),
            }

            funnel_data["steps_completed"].append(step_info)
            funnel_data["current_step"] = step_name
            funnel_data["last_activity"] = timezone.now().isoformat()

            # Check if funnel is completed
            if self._is_funnel_complete(funnel_name, step_order):
                funnel_data["completed"] = True
                funnel_data["completed_at"] = timezone.now().isoformat()
                self.track_conversion(request, f"{funnel_name}_complete")

            cache.set(funnel_key, funnel_data, self.funnel_timeout)

            # Update funnel metrics
            self._update_funnel_metrics(funnel_name, step_name, step_order)

            # Store in database for persistence
            try:
                self._store_funnel_to_db(
                    funnel_name, anonymous_id, step_name, step_order, request
                )
            except Exception as e:
                logger.warning(f"Failed to store funnel to database: {e}")

            return True

        except Exception as e:
            logger.error(f"Failed to track funnel step: {e}")
            return False

    def get_ab_test_variant(self, request, test_name, variants=None):
        """
        Assign and track A/B test variants
        """
        try:
            anonymous_id = self.get_anonymous_id(request)

            if not variants:
                variants = ["A", "B"]

            # Check if user already has a variant
            test_key = f"ab_test_{test_name}_{anonymous_id}"
            existing_variant = cache.get(test_key)

            if existing_variant:
                return existing_variant

            # Assign new variant using consistent hashing
            hash_value = int(
                hashlib.md5(
                    f"{anonymous_id}{test_name}".encode(), usedforsecurity=False
                ).hexdigest(),
                16,
            )
            variant_index = hash_value % len(variants)
            assigned_variant = variants[variant_index]

            # Store assignment
            cache.set(test_key, assigned_variant, 86400 * 30)  # 30 days

            # Track assignment
            self.track_event(
                request,
                "ab_test_assignment",
                {"test_name": test_name, "variant": assigned_variant},
            )

            # Update test metrics
            self._update_ab_test_metrics(test_name, assigned_variant, "assignment")

            # Store in database for persistence
            try:
                self._store_ab_test_to_db(
                    test_name, anonymous_id, assigned_variant, request
                )
            except Exception as e:
                logger.warning(f"Failed to store A/B test to database: {e}")

            return assigned_variant

        except Exception as e:
            logger.error(f"Failed to get A/B test variant: {e}")
            return variants[0] if variants else "A"

    def track_ab_test_conversion(
        self, request, test_name, conversion_type="conversion"
    ):
        """
        Track conversions for A/B tests
        """
        try:
            anonymous_id = self.get_anonymous_id(request)
            test_key = f"ab_test_{test_name}_{anonymous_id}"
            variant = cache.get(test_key)

            if variant:
                # Track conversion
                self.track_event(
                    request,
                    "ab_test_conversion",
                    {
                        "test_name": test_name,
                        "variant": variant,
                        "conversion_type": conversion_type,
                    },
                )

                # Update test metrics
                self._update_ab_test_metrics(test_name, variant, conversion_type)

                return True

        except Exception as e:
            logger.error(f"Failed to track A/B test conversion: {e}")

        return False

    def get_funnel_analytics(self, funnel_name, days=7):
        """
        Get funnel conversion analytics
        """
        try:
            analytics_data = {
                "funnel_name": funnel_name,
                "steps": {},
                "conversion_rate": 0,
                "drop_off_points": [],
                "average_time": 0,
            }

            # Aggregate funnel data from cache
            date_key = datetime.now().date().isoformat()
            funnel_metrics_key = f"funnel_metrics_{funnel_name}_{date_key}"
            metrics = cache.get(funnel_metrics_key, {})

            if metrics:
                total_started = metrics.get("total_started", 0)
                total_completed = metrics.get("total_completed", 0)

                if total_started > 0:
                    analytics_data["conversion_rate"] = (
                        total_completed / total_started
                    ) * 100

                # Calculate drop-off points
                steps_data = metrics.get("steps", {})
                prev_count = total_started

                for step_order in sorted(steps_data.keys()):
                    step_count = steps_data[step_order].get("count", 0)
                    if prev_count > 0 and step_count < prev_count:
                        drop_off_rate = ((prev_count - step_count) / prev_count) * 100
                        analytics_data["drop_off_points"].append(
                            {
                                "step": steps_data[step_order].get("name"),
                                "drop_off_rate": drop_off_rate,
                            }
                        )
                    prev_count = step_count

                analytics_data["steps"] = steps_data
                analytics_data["average_time"] = metrics.get("average_time", 0)

            return analytics_data

        except Exception as e:
            logger.error(f"Failed to get funnel analytics: {e}")
            return {}

    def get_ab_test_results(self, test_name):
        """
        Get A/B test results and statistics
        """
        try:
            date_key = datetime.now().date().isoformat()
            test_metrics_key = f"ab_test_metrics_{test_name}_{date_key}"
            metrics = cache.get(test_metrics_key, {})

            results = {
                "test_name": test_name,
                "variants": {},
                "winner": None,
                "confidence": 0,
            }

            if metrics:
                for variant, data in metrics.items():
                    assignments = data.get("assignments", 0)
                    conversions = data.get("conversions", 0)

                    conversion_rate = (
                        (conversions / assignments * 100) if assignments > 0 else 0
                    )

                    results["variants"][variant] = {
                        "assignments": assignments,
                        "conversions": conversions,
                        "conversion_rate": conversion_rate,
                    }

                # Determine winner (simplified - should use statistical significance)
                if len(results["variants"]) > 1:
                    sorted_variants = sorted(
                        results["variants"].items(),
                        key=lambda x: x[1]["conversion_rate"],
                        reverse=True,
                    )

                    if (
                        sorted_variants[0][1]["assignments"] >= 100
                    ):  # Minimum sample size
                        results["winner"] = sorted_variants[0][0]
                        # Simplified confidence calculation
                        diff = (
                            sorted_variants[0][1]["conversion_rate"]
                            - sorted_variants[1][1]["conversion_rate"]
                        )
                        results["confidence"] = min(95, 50 + diff * 5)  # Simplified

            return results

        except Exception as e:
            logger.error(f"Failed to get A/B test results: {e}")
            return {}

    def get_user_journey_insights(self, days=7):
        """
        Get insights from user journey data
        """
        try:
            insights = {
                "common_paths": {},
                "exit_points": {},
                "average_steps": 0,
                "bounce_rate": 0,
            }

            # Aggregate journey data
            total_journeys = 0
            total_steps = 0
            single_step_journeys = 0

            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).date()
                date_key = date.isoformat()

                journey_metrics_key = f"journey_metrics_{date_key}"
                metrics = cache.get(journey_metrics_key, {})

                if metrics:
                    paths = metrics.get("paths", {})
                    for path, count in paths.items():
                        insights["common_paths"][path] = (
                            insights["common_paths"].get(path, 0) + count
                        )

                    exits = metrics.get("exit_points", {})
                    for exit_point, count in exits.items():
                        insights["exit_points"][exit_point] = (
                            insights["exit_points"].get(exit_point, 0) + count
                        )

                    total_journeys += metrics.get("total_journeys", 0)
                    total_steps += metrics.get("total_steps", 0)
                    single_step_journeys += metrics.get("single_step_journeys", 0)

            # Calculate averages
            if total_journeys > 0:
                insights["average_steps"] = total_steps / total_journeys
                insights["bounce_rate"] = (single_step_journeys / total_journeys) * 100

            # Sort and limit results
            insights["common_paths"] = dict(
                sorted(
                    insights["common_paths"].items(), key=lambda x: x[1], reverse=True
                )[:10]
            )

            insights["exit_points"] = dict(
                sorted(
                    insights["exit_points"].items(), key=lambda x: x[1], reverse=True
                )[:5]
            )

            return insights

        except Exception as e:
            logger.error(f"Failed to get user journey insights: {e}")
            return {}

    def _update_journey_metrics(self, step_name):
        """Update journey metrics"""
        try:
            date_key = datetime.now().date().isoformat()
            metrics_key = f"journey_metrics_{date_key}"

            metrics = cache.get(
                metrics_key,
                {
                    "paths": {},
                    "exit_points": {},
                    "total_journeys": 0,
                    "total_steps": 0,
                    "single_step_journeys": 0,
                },
            )

            metrics["total_steps"] += 1
            cache.set(metrics_key, metrics, self.cache_timeout)

        except Exception as e:
            logger.error(f"Failed to update journey metrics: {e}")

    def _update_funnel_metrics(self, funnel_name, step_name, step_order):
        """Update funnel metrics"""
        try:
            date_key = datetime.now().date().isoformat()
            metrics_key = f"funnel_metrics_{funnel_name}_{date_key}"

            metrics = cache.get(
                metrics_key,
                {
                    "total_started": 0,
                    "total_completed": 0,
                    "steps": {},
                    "average_time": 0,
                },
            )

            if step_order == 1:
                metrics["total_started"] += 1

            if step_order not in metrics["steps"]:
                metrics["steps"][step_order] = {"name": step_name, "count": 0}

            metrics["steps"][step_order]["count"] += 1

            cache.set(metrics_key, metrics, self.cache_timeout)

        except Exception as e:
            logger.error(f"Failed to update funnel metrics: {e}")

    def _update_ab_test_metrics(self, test_name, variant, event_type):
        """Update A/B test metrics"""
        try:
            date_key = datetime.now().date().isoformat()
            metrics_key = f"ab_test_metrics_{test_name}_{date_key}"

            metrics = cache.get(metrics_key, {})

            if variant not in metrics:
                metrics[variant] = {"assignments": 0, "conversions": 0}

            if event_type == "assignment":
                metrics[variant]["assignments"] += 1
            else:
                metrics[variant]["conversions"] += 1

            cache.set(metrics_key, metrics, self.cache_timeout)

        except Exception as e:
            logger.error(f"Failed to update A/B test metrics: {e}")

    def _calculate_time_spent(self, funnel_data):
        """Calculate time spent in funnel"""
        try:
            if funnel_data.get("started_at"):
                start_time = datetime.fromisoformat(
                    funnel_data["started_at"].replace("Z", "+00:00")
                )
                return (timezone.now() - start_time).total_seconds()
            return 0
        except (ValueError, TypeError, AttributeError):
            # Invalid timestamp format
            return 0

    def _is_funnel_complete(self, funnel_name, current_step):
        """Check if funnel is complete"""
        # Define funnel completion criteria
        funnel_definitions = {
            "signup": 4,  # 4 steps in signup funnel
            "purchase": 5,  # 5 steps in purchase funnel
            "onboarding": 3,  # 3 steps in onboarding
        }

        return current_step >= funnel_definitions.get(funnel_name, 999)

    def _store_event_to_db(self, event, request, device_info):
        """Store analytics event to database for persistence"""
        # Import here to avoid circular imports
        from .models import AnalyticsEvent

        # Get GDPR consent from session or cookies
        gdpr_consent = getattr(request, "session", {}).get("gdpr_consent", False)

        # Hash IP for geographic insights only (privacy-compliant)
        ip_address = request.META.get("REMOTE_ADDR", "")
        ip_hash = hashlib.sha256(ip_address.encode()).hexdigest() if ip_address else ""

        AnalyticsEvent.objects.create(
            event_type=event.get("type", "unknown"),
            event_name=event.get("event_name", ""),
            anonymous_id=event["anonymous_id"],
            page_path=event.get("page_path", ""),
            page_title=event.get("page_title", ""),
            referrer_type=event.get("referrer", ""),
            device_type="mobile" if device_info.get("is_mobile") else "desktop",
            browser_family=device_info.get("browser_family", ""),
            os_family=device_info.get("os_family", ""),
            event_data=event.get("event_data", {}),
            gdpr_consent=gdpr_consent,
            ip_hash=ip_hash[:64],  # Limit hash length
            timestamp=timezone.now(),
        )

    def _store_journey_to_db(self, journey_id, anonymous_id, step_name, request):
        """Store or update user journey in database"""
        from .models import UserJourney

        gdpr_consent = getattr(request, "session", {}).get("gdpr_consent", False)

        journey, created = UserJourney.objects.get_or_create(
            journey_id=journey_id,
            defaults={
                "anonymous_id": anonymous_id,
                "gdpr_consent": gdpr_consent,
            },
        )

        journey.add_step(step_name, self._sanitize_path(request.path))
        return journey

    def _store_funnel_to_db(
        self, funnel_name, anonymous_id, step_name, step_order, request
    ):
        """Store or update conversion funnel in database"""
        from .models import ConversionFunnel

        gdpr_consent = getattr(request, "session", {}).get("gdpr_consent", False)
        funnel_id = f"funnel_{funnel_name}_{anonymous_id}_{timezone.now().date()}"

        funnel, created = ConversionFunnel.objects.get_or_create(
            funnel_id=funnel_id,
            defaults={
                "anonymous_id": anonymous_id,
                "funnel_name": funnel_name,
                "gdpr_consent": gdpr_consent,
            },
        )

        # Check if this is the final step
        is_final = self._is_funnel_complete(funnel_name, step_order)
        funnel.complete_step(step_name, step_order, is_final)
        return funnel

    def _store_ab_test_to_db(self, test_name, anonymous_id, variant, request):
        """Store A/B test assignment in database"""
        from .models import ABTestAssignment

        gdpr_consent = getattr(request, "session", {}).get("gdpr_consent", False)

        assignment, created = ABTestAssignment.objects.get_or_create(
            test_name=test_name,
            anonymous_id=anonymous_id,
            defaults={
                "variant": variant,
                "gdpr_consent": gdpr_consent,
                "assignment_method": "hash",
            },
        )

        return assignment

    def get_gdpr_compliance_info(self):
        """Get GDPR compliance information for the analytics system"""
        return {
            "data_processing_purposes": [
                "Website performance optimization",
                "User experience improvement",
                "Content personalization",
                "A/B testing for feature development",
            ],
            "data_collected": [
                "Anonymous session identifiers (no personal data)",
                "Page paths and titles visited",
                "Device type and browser family (aggregated)",
                "Interaction events (clicks, form submissions)",
                "Performance metrics timing",
            ],
            "data_not_collected": [
                "Personal identification information",
                "Email addresses or names",
                "Precise location data",
                "Cross-site tracking identifiers",
                "Sensitive personal categories",
            ],
            "retention_period": "90 days maximum",
            "user_rights": [
                "Opt-out of analytics tracking",
                "Data deletion upon request",
                "Access to aggregated data insights",
                "Correction of inaccurate data",
            ],
            "technical_measures": [
                "Anonymous session-based tracking",
                "IP address hashing for geographic insights only",
                "Automatic data expiration (90 days)",
                "No cross-site tracking",
                "Local storage preference respect",
            ],
        }

    def cleanup_expired_data(self):
        """Clean up expired analytics data for GDPR compliance"""
        from .models import (
            ABTestAssignment,
            AnalyticsEvent,
            ConversionFunnel,
            UserJourney,
        )

        cleanup_results = {
            "analytics_events": AnalyticsEvent.cleanup_expired(),
            "user_journeys": UserJourney.objects.filter(
                expires_at__lt=timezone.now()
            ).delete()[0],
            "conversion_funnels": ConversionFunnel.objects.filter(
                expires_at__lt=timezone.now()
            ).delete()[0],
            "ab_test_assignments": ABTestAssignment.objects.filter(
                expires_at__lt=timezone.now()
            ).delete()[0],
        }

        total_cleaned = sum(cleanup_results.values())
        logger.info(f"Cleaned up {total_cleaned} expired analytics records")
        return cleanup_results

    def handle_gdpr_deletion_request(self, anonymous_id):
        """Handle GDPR data deletion request for a specific anonymous ID"""
        from .models import (
            ABTestAssignment,
            AnalyticsEvent,
            ConversionFunnel,
            UserJourney,
        )

        deletion_results = {
            "analytics_events": AnalyticsEvent.objects.filter(
                anonymous_id=anonymous_id
            ).delete()[0],
            "user_journeys": UserJourney.objects.filter(
                anonymous_id=anonymous_id
            ).delete()[0],
            "conversion_funnels": ConversionFunnel.objects.filter(
                anonymous_id=anonymous_id
            ).delete()[0],
            "ab_test_assignments": ABTestAssignment.objects.filter(
                anonymous_id=anonymous_id
            ).delete()[0],
        }

        # Clear cache data
        session_key = f"analytics_session_{anonymous_id}"
        cache.delete(session_key)

        total_deleted = sum(deletion_results.values())
        logger.info(f"Deleted {total_deleted} records for anonymous_id: {anonymous_id}")
        return deletion_results


# Global analytics instance
analytics = PrivacyCompliantAnalytics()
