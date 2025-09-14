"""
Unit tests for main app views
"""
import json
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, Mock
from apps.main.models import PerformanceMetric, WebPushSubscription, ErrorLog


User = get_user_model()


class PerformanceViewsTest(TestCase):
    """Test performance monitoring views"""
    
    def setUp(self):
        self.client = Client()
    
    def test_collect_performance_metric(self):
        """Test performance metric collection endpoint"""
        data = {
            'metric_type': 'lcp',
            'value': 2.5,
            'url': '/test/',
            'additional_data': {'viewport': '1920x1080'}
        }
        
        response = self.client.post(
            reverse('api_performance_collect'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertTrue(PerformanceMetric.objects.filter(
            metric_type='lcp',
            value=2.5
        ).exists())
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get(reverse('health_check'))
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('database', data['checks'])
        self.assertIn('cache', data['checks'])


class WebPushViewsTest(TestCase):
    """Test web push notification views"""
    
    def setUp(self):
        self.client = Client()
    
    # def test_get_vapid_public_key(self):
    #     """Test VAPID public key endpoint"""
    #     with patch('apps.main.views.settings.WEBPUSH_SETTINGS', {'VAPID_PUBLIC_KEY': 'test_key'}):
    #         response = self.client.get(reverse('api_webpush_vapid_key'))
    #         self.assertEqual(response.status_code, 200)
            
    #         data = response.json()
    #         self.assertEqual(data['publicKey'], 'test_key')
    
    # def test_subscribe_push_notifications(self):
    #     """Test push subscription endpoint"""
    #     data = {
    #         'endpoint': 'https://test.endpoint.com',
    #         'keys': {
    #             'p256dh': 'test_p256dh',
    #             'auth': 'test_auth'
    #         }
    #     }
        
    #     response = self.client.post(
    #         reverse('api_webpush_subscribe'),
    #         data=json.dumps(data),
    #         content_type='application/json'
    #     )
        
    #     self.assertEqual(response.status_code, 201)
    #     self.assertTrue(WebPushSubscription.objects.filter(
    #         endpoint='https://test.endpoint.com'
    #     ).exists())
    
    # def test_webpush_unsubscribe(self):
    #     """Test webpush unsubscribe endpoint"""
    #     # Create a test subscription
    #     subscription = WebPushSubscription.objects.create(
    #         endpoint='https://test.endpoint.com',
    #         p256dh='test_p256dh',
    #         auth='test_auth'
    #     )
        
    #     data = {
    #         'endpoint': 'https://test.endpoint.com'
    #     }
        
    #     response = self.client.post(
    #         reverse('api_webpush_unsubscribe'),
    #         data=json.dumps(data),
    #         content_type='application/json'
    #     )
        
    #     self.assertEqual(response.status_code, 200)
    #     self.assertFalse(WebPushSubscription.objects.filter(
    #         endpoint='https://test.endpoint.com'
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
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Portfolio')
    
    def test_personal_view(self):
        """Test personal page"""
        response = self.client.get(reverse('main:personal'))
        self.assertEqual(response.status_code, 200)
    
    def test_search_view(self):
        """Test search functionality"""
        response = self.client.get(reverse('main:search'), {'q': 'test'})
        self.assertEqual(response.status_code, 200)