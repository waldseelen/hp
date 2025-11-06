"""
Unit tests for Portfolio Analytics Models.

Tests cover:
- UserJourney (step tracking, GDPR 90-day expiration)
- ConversionFunnel (funnel completion, drop-off tracking)
- ABTestAssignment (variant assignment, conversion tracking)

Target: 12-15 comprehensive tests for analytics and testing.
"""

from datetime import timedelta

from django.utils import timezone

import pytest

from apps.portfolio.models import ABTestAssignment, ConversionFunnel, UserJourney

# ============================================================================
# USERJOURNEY MODEL TESTS (Step Tracking, GDPR)
# ============================================================================


@pytest.mark.django_db
class TestUserJourneyModel:
    """Test UserJourney model - user path tracking with GDPR compliance."""

    def test_user_journey_creation(self):
        """Test basic user journey creation."""
        journey = UserJourney.objects.create(
            anonymous_id="anon_123",
            session_id="session_456",
            entry_page="/",
        )
        assert journey.anonymous_id == "anon_123"
        assert journey.entry_page == "/"
        assert journey.total_pages_visited == 0

    def test_user_journey_gdpr_90_day_expiration(self):
        """Test GDPR 90-day expiration auto-set."""
        journey = UserJourney.objects.create(
            anonymous_id="anon_gdpr",
            session_id="session_gdpr",
            entry_page="/",
        )
        # Should auto-set expires_at to 90 days from creation
        expected_expiry = timezone.now() + timedelta(days=90)
        # Allow 1 minute tolerance
        assert abs((journey.expires_at - expected_expiry).total_seconds()) < 60

    def test_user_journey_step_tracking(self):
        """Test journey step tracking."""
        journey = UserJourney.objects.create(
            anonymous_id="anon_steps",
            session_id="session_steps",
            entry_page="/home",
        )

        # Simulate step tracking
        journey.pages_visited = ["/home", "/about", "/blog", "/contact"]
        journey.total_pages_visited = len(journey.pages_visited)
        journey.exit_page = "/contact"
        journey.save()

        assert journey.total_pages_visited == 4
        assert journey.exit_page == "/contact"


# ============================================================================
# CONVERSIONFUNNEL MODEL TESTS (Funnel Completion, Drop-Off)
# ============================================================================


@pytest.mark.django_db
class TestConversionFunnelModel:
    """Test ConversionFunnel model - multi-step conversion tracking."""

    def test_conversion_funnel_creation(self):
        """Test basic conversion funnel creation."""
        funnel = ConversionFunnel.objects.create(
            funnel_name="signup_funnel",
            anonymous_id="anon_funnel",
            current_step="landing",
            current_step_order=1,
        )
        assert funnel.funnel_name == "signup_funnel"
        assert funnel.current_step == "landing"
        assert not funnel.is_completed

    def test_conversion_funnel_step_completion(self):
        """Test completing funnel steps."""
        funnel = ConversionFunnel.objects.create(
            funnel_name="checkout_funnel",
            anonymous_id="anon_checkout",
            current_step="cart",
            current_step_order=1,
        )

        # Complete step 1
        funnel.complete_step("cart", 1)
        assert funnel.current_step == "cart"
        assert len(funnel.steps_completed) == 1

        # Complete step 2
        funnel.complete_step("shipping", 2)
        assert funnel.current_step == "shipping"
        assert len(funnel.steps_completed) == 2

        # Complete final step
        funnel.complete_step("payment", 3, is_final=True)
        assert funnel.is_completed
        assert funnel.completed_at is not None

    def test_conversion_funnel_drop_off(self):
        """Test drop-off tracking."""
        funnel = ConversionFunnel.objects.create(
            funnel_name="signup_funnel",
            anonymous_id="anon_dropout",
            current_step="email",
            current_step_order=2,
            drop_off_step="password",
        )
        assert not funnel.is_completed
        assert funnel.drop_off_step == "password"

    def test_conversion_funnel_90_day_expiration(self):
        """Test GDPR 90-day expiration."""
        funnel = ConversionFunnel.objects.create(
            funnel_name="test_funnel",
            anonymous_id="anon_expire",
            current_step="start",
            current_step_order=1,
        )
        expected_expiry = timezone.now() + timedelta(days=90)
        assert abs((funnel.expires_at - expected_expiry).total_seconds()) < 60


# ============================================================================
# ABTESTASSIGNMENT MODEL TESTS (Variant Assignment, Conversion)
# ============================================================================


@pytest.mark.django_db
class TestABTestAssignmentModel:
    """Test ABTestAssignment model - A/B testing and conversion tracking."""

    def test_ab_test_assignment_creation(self):
        """Test basic A/B test assignment creation."""
        assignment = ABTestAssignment.objects.create(
            test_name="homepage_hero_test",
            anonymous_id="anon_ab_123",
            variant="A",
        )
        assert assignment.test_name == "homepage_hero_test"
        assert assignment.variant == "A"
        assert not assignment.has_converted

    def test_ab_test_variant_assignment(self):
        """Test variant assignment (A, B, C)."""
        for variant in ["A", "B", "C"]:
            assignment = ABTestAssignment.objects.create(
                test_name="button_color_test",
                anonymous_id=f"anon_{variant}",
                variant=variant,
            )
            assert assignment.variant == variant

    def test_ab_test_conversion_tracking(self):
        """Test conversion tracking."""
        assignment = ABTestAssignment.objects.create(
            test_name="pricing_test",
            anonymous_id="anon_convert",
            variant="B",
        )
        assert not assignment.has_converted

        # Record conversion
        assignment.record_conversion(conversion_type="purchase", conversion_value=99.99)

        assert assignment.has_converted
        assert assignment.converted_at is not None
        assert assignment.conversion_type == "purchase"
        assert assignment.conversion_value == 99.99

    def test_ab_test_unique_assignment(self):
        """Test unique constraint on test_name + anonymous_id."""
        ABTestAssignment.objects.create(
            test_name="unique_test",
            anonymous_id="anon_unique",
            variant="A",
        )

        # Creating duplicate should raise IntegrityError
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            ABTestAssignment.objects.create(
                test_name="unique_test",
                anonymous_id="anon_unique",
                variant="B",
            )

    def test_ab_test_90_day_expiration(self):
        """Test GDPR 90-day expiration."""
        assignment = ABTestAssignment.objects.create(
            test_name="test_expire",
            anonymous_id="anon_expire_ab",
            variant="A",
        )
        expected_expiry = timezone.now() + timedelta(days=90)
        assert abs((assignment.expires_at - expected_expiry).total_seconds()) < 60

    def test_ab_test_gdpr_consent(self):
        """Test GDPR consent flag."""
        assignment = ABTestAssignment.objects.create(
            test_name="gdpr_test",
            anonymous_id="anon_gdpr",
            variant="A",
            gdpr_consent=True,
        )
        assert assignment.gdpr_consent
