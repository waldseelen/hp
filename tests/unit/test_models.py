"""
Unit tests for main app models
"""

from django.test import TestCase
from django.utils import timezone

import pytest

from apps.main.models import AITool, CybersecurityResource, PersonalInfo, SocialLink

# Import from performance module instead
from apps.main.performance import PerformanceMetric, performance_metrics

# TODO: These models need to be created in apps/main/models.py
# WebPushSubscription, ErrorLog, NotificationLog


class PersonalInfoModelTest(TestCase):
    """Test PersonalInfo model"""

    def setUp(self):
        self.personal_info = PersonalInfo.objects.create(
            key="name", value="Test User", type="text", order=1
        )

    def test_personal_info_creation(self):
        """Test PersonalInfo model creation"""
        self.assertEqual(self.personal_info.key, "name")
        self.assertEqual(self.personal_info.value, "Test User")
        self.assertEqual(self.personal_info.type, "text")
        self.assertEqual(self.personal_info.order, 1)
        self.assertTrue(self.personal_info.is_visible)

    def test_str_method(self):
        """Test __str__ method"""
        self.assertEqual(str(self.personal_info), "name (Text)")


class PerformanceMetricModelTest(TestCase):
    """Test PerformanceMetric model (from performance.py)"""

    def setUp(self):
        # Use the dataclass PerformanceMetric
        self.metric = PerformanceMetric(
            name="lcp", value=2.5, unit="s", timestamp=timezone.now()
        )

    def test_performance_metric_creation(self):
        """Test PerformanceMetric dataclass creation"""
        self.assertEqual(self.metric.name, "lcp")
        self.assertEqual(self.metric.value, 2.5)
        self.assertEqual(self.metric.unit, "s")
        self.assertIsNotNone(self.metric.timestamp)

    def test_metric_to_dict(self):
        """Test PerformanceMetric to_dict method"""
        metric_dict = self.metric.to_dict()
        self.assertEqual(metric_dict["name"], "lcp")
        self.assertEqual(metric_dict["value"], 2.5)


@pytest.mark.skip(reason="WebPushSubscription model not yet implemented")
class WebPushSubscriptionModelTest(TestCase):
    """Test WebPushSubscription model"""

    def setUp(self):
        # TODO: Create WebPushSubscription Django model
        pass


@pytest.mark.skip(reason="ErrorLog model not yet implemented")
class ErrorLogModelTest(TestCase):
    """Test ErrorLog model"""

    def setUp(self):
        # TODO: Create ErrorLog Django model
        pass
