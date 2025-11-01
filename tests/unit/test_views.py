"""
Unit tests for main app views
"""

import json
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

import pytest

from apps.main.performance import PerformanceMetric, alert_manager, performance_metrics

# TODO: These models need to be created in apps/main/models.py
# WebPushSubscription, ErrorLog


User = get_user_model()


class PerformanceViewsTest(TestCase):
    """Test performance monitoring views"""

    def setUp(self):
        self.client = Client()

    def test_performance_metrics_recording(self):
        """Test recording performance metrics"""
        # Record a metric using the performance_metrics instance
        metric = performance_metrics.record_metric(
            name="response_time", value=350, unit="ms"
        )

        self.assertEqual(metric.name, "response_time")
        self.assertEqual(metric.value, 350)
        self.assertEqual(metric.unit, "ms")
        self.assertEqual(metric.status, "normal")

    def test_health_check_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["status"], "healthy")


@pytest.mark.skip(reason="WebPushSubscription model not yet implemented")
class WebPushViewsTest(TestCase):
    """Test web push notification views - TODO: implement"""

    pass
    #     ).exists())

    #     response_data = response.json()
    #     self.assertTrue(response_data['success'])
    #     self.assertEqual(response_data['message'], 'Successfully unsubscribed')

    # def test_webpush_log(self):
    #     """Test webpush log endpoint"""
    #     data = {
    #         'event': 'received',
    #         'timestamp': 1234567890,
    #         'data': {'title': 'Test notification'}
    #     }

    #     response = self.client.post(
    #         reverse('api_webpush_log'),
    #         data=json.dumps(data),
    #         content_type='application/json'
    #     )

    #     self.assertEqual(response.status_code, 200)


class ErrorLoggingViewsTest(TestCase):
    """Test error logging views"""

    def setUp(self):
        self.client = Client()

    # def test_log_error(self):
    #     """Test error logging endpoint"""
    #     data = {
    #         'level': 'ERROR',
    #         'message': 'Test error message',
    #         'url': '/test/',
    #         'additional_data': {'stack': 'Error stack trace'}
    #     }

    #     response = self.client.post(
    #         reverse('api_error_log'),
    #         data=json.dumps(data),
    #         content_type='application/json'
    #     )

    #     self.assertEqual(response.status_code, 201)
    #     self.assertTrue(ErrorLog.objects.filter(
    #         level='ERROR',
    #         message='Test error message'
    #     ).exists())


class HomeViewTest(TestCase):
    """Test home and main views"""

    def setUp(self):
        self.client = Client()

    def test_home_view(self):
        """Test home page renders correctly"""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Portfolio")

    def test_personal_view(self):
        """Test personal page"""
        response = self.client.get(reverse("main:personal"))
        self.assertEqual(response.status_code, 200)

    def test_search_view(self):
        """Test search functionality"""
        response = self.client.get(reverse("main:search"), {"q": "test"})
        self.assertEqual(response.status_code, 200)
