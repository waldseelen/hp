"""
Unit tests for main app models
"""
import pytest
from django.test import TestCase
from django.utils import timezone
from apps.main.models import (
    PersonalInfo, SocialLink, AITool, CybersecurityResource,
    PerformanceMetric, WebPushSubscription, ErrorLog, NotificationLog
)


class PersonalInfoModelTest(TestCase):
    """Test PersonalInfo model"""
    
    def setUp(self):
        self.personal_info = PersonalInfo.objects.create(
            key='name',
            value='Test User',
            type='text',
            order=1
        )
    
    def test_personal_info_creation(self):
        """Test PersonalInfo model creation"""
        self.assertEqual(self.personal_info.key, 'name')
        self.assertEqual(self.personal_info.value, 'Test User')
        self.assertEqual(self.personal_info.type, 'text')
        self.assertEqual(self.personal_info.order, 1)
        self.assertTrue(self.personal_info.is_visible)
    
    def test_str_method(self):
        """Test __str__ method"""
        self.assertEqual(str(self.personal_info), 'name (Text)')


class PerformanceMetricModelTest(TestCase):
    """Test PerformanceMetric model"""
    
    def setUp(self):
        self.metric = PerformanceMetric.objects.create(
            metric_type='lcp',
            value=2.5,
            url='/test/',
            user_agent='Test Agent',
            ip_address='127.0.0.1'
        )
    
    def test_performance_metric_creation(self):
        """Test PerformanceMetric model creation"""
        self.assertEqual(self.metric.metric_type, 'lcp')
        self.assertEqual(self.metric.value, 2.5)
        self.assertEqual(self.metric.url, '/test/')
        self.assertIsNotNone(self.metric.timestamp)
    
    def test_str_method(self):
        """Test __str__ method"""
        self.assertEqual(str(self.metric), 'Largest Contentful Paint: 2.5 (desktop)')


class WebPushSubscriptionModelTest(TestCase):
    """Test WebPushSubscription model"""
    
    def setUp(self):
        self.subscription = WebPushSubscription.objects.create(
            endpoint='https://test.endpoint.com',
            p256dh='test_p256dh_key',
            auth='test_auth_key',
            user_agent='Test Browser'
        )
    
    def test_subscription_creation(self):
        """Test WebPushSubscription model creation"""
        self.assertEqual(self.subscription.endpoint, 'https://test.endpoint.com')
        self.assertEqual(self.subscription.p256dh, 'test_p256dh_key')
        self.assertEqual(self.subscription.auth, 'test_auth_key')
        self.assertTrue(self.subscription.is_active)
    
    def test_str_method(self):
        """Test __str__ method"""
        self.assertIn('Push Subscription', str(self.subscription))


class ErrorLogModelTest(TestCase):
    """Test ErrorLog model"""
    
    def setUp(self):
        self.error = ErrorLog.objects.create(
            level='ERROR',
            message='Test error message',
            url='/error-page/',
            user_agent='Test Browser'
        )
    
    def test_error_log_creation(self):
        """Test ErrorLog model creation"""
        self.assertEqual(self.error.level, 'ERROR')
        self.assertEqual(self.error.message, 'Test error message')
        self.assertEqual(self.error.url, '/error-page/')
        self.assertIsNotNone(self.error.created_at)
    
    def test_str_method(self):
        """Test __str__ method"""
        self.assertEqual(str(self.error), 'ERROR: Test error message...')