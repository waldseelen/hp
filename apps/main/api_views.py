"""
API Views for monitoring and performance tracking
"""
import json
import re
import logging
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.db import connection
from django.utils.html import strip_tags
from .cache_utils import CacheManager


@csrf_protect
@require_http_methods(["POST", "GET"])
def performance_api(request):
    """
    Performance metrics collection endpoint with validation
    """
    logger = logging.getLogger(__name__)
    
    if request.method == 'POST':
        try:
            # Validate content type
            if not request.content_type.startswith('application/json'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Content-Type must be application/json'
                }, status=400)
            
            # Parse and validate JSON
            data = json.loads(request.body)
            
            # Validate required fields and sanitize data
            validated_data = validate_performance_data(data)
            if 'error' in validated_data:
                return JsonResponse({
                    'status': 'error',
                    'message': validated_data['error']
                }, status=400)
            
            # Log performance metrics (safely)
            logger.info(f"Performance metrics received from {request.META.get('REMOTE_ADDR', 'unknown')}")
            
            # Store validated metrics (implement storage as needed)
            # For now, just acknowledge receipt
            return JsonResponse({
                'status': 'ok',
                'message': 'Performance metrics received',
                'timestamp': datetime.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error processing performance data: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'Internal server error'
            }, status=500)
    
    # GET request - return current performance stats
    return JsonResponse({
        'status': 'ok',
        'server_time': datetime.now().isoformat(),
        'version': '1.0.0'
    })


@cache_page(CacheManager.TIMEOUTS['short'])
@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint for monitoring
    """
    try:
        # Basic health check - database connectivity
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'checks': {
                'database': 'ok',
                'server': 'running'
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': 'Database connection failed'
        }, status=503)


@csrf_protect
@require_http_methods(["POST", "GET"])
def notifications_api(request):
    """
    Push notifications handler with validation
    """
    logger = logging.getLogger(__name__)
    
    if request.method == 'POST':
        try:
            # Validate content type
            if not request.content_type.startswith('application/json'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Content-Type must be application/json'
                }, status=400)
            
            data = json.loads(request.body)
            
            # Validate notification data
            validated_data = validate_notification_data(data)
            if 'error' in validated_data:
                return JsonResponse({
                    'status': 'error',
                    'message': validated_data['error']
                }, status=400)
            
            # Log notification data (safely)
            logger.info(f"Notification data received from {request.META.get('REMOTE_ADDR', 'unknown')}")
            
            # Here you would implement actual notification sending
            # For now, just acknowledge receipt
            return JsonResponse({
                'status': 'ok',
                'message': 'Notification processed',
                'timestamp': datetime.now().isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error processing notification: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'Internal server error'
            }, status=500)
    
    # GET request - return notification status
    return JsonResponse({
        'status': 'ok',
        'notifications_enabled': True,
        'timestamp': datetime.now().isoformat()
    })


@csrf_exempt
@require_http_methods(["GET", "POST"])
def analytics_api(request):
    """
    Analytics data endpoint - handles both GET and POST requests
    """
    if request.method == 'GET':
        return JsonResponse({
            'status': 'ok',
            'message': 'Analytics endpoint ready',
            'timestamp': datetime.now().isoformat()
        })
    elif request.method == 'POST':
        try:
            # Handle POST requests for analytics data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()

            # Log analytics data (implement your analytics logic here)
            logger.info(f"Analytics data received: {len(data)} fields")

            return JsonResponse({
                'status': 'ok',
                'message': 'Analytics data processed',
                'timestamp': datetime.now().isoformat()
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error processing analytics data: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'Internal server error'
            }, status=500)


@require_http_methods(["GET"])
def cache_stats_api(request):
    """
    Cache statistics and monitoring endpoint
    """
    try:
        from .cache_utils import CacheMonitor
        
        # Get cache statistics
        stats = CacheMonitor.get_cache_stats()
        
        # Add additional runtime stats
        stats.update({
            'timestamp': datetime.now().isoformat(),
            'cache_keys_info': {
                'home_data_cached': cache.get('home_page_data') is not None,
                'blog_data_cached': cache.get('blog_published_posts') is not None,
                'tools_data_cached': cache.get('tools_visible_tools') is not None
            }
        })
        
        return JsonResponse({
            'status': 'ok',
            'cache_stats': stats
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=500)


def validate_performance_data(data):
    """
    Validate and sanitize performance metrics data
    """
    if not isinstance(data, dict):
        return {'error': 'Data must be a JSON object'}
    
    allowed_fields = {
        'metric_type', 'value', 'url', 'user_agent', 'viewport_size',
        'connection_type', 'device_type', 'additional_data', 'timestamp'
    }
    
    validated_data = {}
    
    # Check for unknown fields
    unknown_fields = set(data.keys()) - allowed_fields
    if unknown_fields:
        return {'error': f'Unknown fields: {", ".join(unknown_fields)}'}
    
    # Validate metric_type
    metric_type = data.get('metric_type')
    if not metric_type:
        return {'error': 'metric_type is required'}
    
    allowed_metrics = {
        'lcp', 'fid', 'cls', 'fcp', 'ttfb', 'long_task', 'resource_load',
        'network_online', 'network_offline', 'cache_hit_rate'
    }
    
    if not isinstance(metric_type, str) or metric_type not in allowed_metrics:
        return {'error': f'Invalid metric_type. Must be one of: {", ".join(allowed_metrics)}'}
    
    validated_data['metric_type'] = strip_tags(metric_type)
    
    # Validate value
    value = data.get('value')
    if value is None:
        return {'error': 'value is required'}
    
    if not isinstance(value, (int, float)) or value < 0:
        return {'error': 'value must be a non-negative number'}
    
    validated_data['value'] = min(value, 1000000)  # Cap at reasonable max
    
    # Validate URL (optional)
    url = data.get('url')
    if url:
        if not isinstance(url, str) or len(url) > 2000:
            return {'error': 'url must be a string under 2000 characters'}
        
        # Basic URL validation
        if not re.match(r'^https?://', url):
            return {'error': 'url must start with http:// or https://'}
        
        validated_data['url'] = strip_tags(url)
    
    # Validate user_agent (optional)
    user_agent = data.get('user_agent')
    if user_agent:
        if not isinstance(user_agent, str) or len(user_agent) > 500:
            return {'error': 'user_agent must be a string under 500 characters'}
        
        validated_data['user_agent'] = strip_tags(user_agent)[:500]
    
    # Validate viewport_size (optional)
    viewport_size = data.get('viewport_size')
    if viewport_size:
        if not isinstance(viewport_size, str):
            return {'error': 'viewport_size must be a string'}
        
        if not re.match(r'^\d+x\d+$', viewport_size):
            return {'error': 'viewport_size must be in format WIDTHxHEIGHT'}
        
        validated_data['viewport_size'] = viewport_size
    
    return validated_data


def validate_notification_data(data):
    """
    Validate and sanitize notification data
    """
    if not isinstance(data, dict):
        return {'error': 'Data must be a JSON object'}
    
    allowed_fields = {
        'subscription', 'topics', 'user_agent', 'url', 'endpoint',
        'message', 'title', 'icon', 'badge'
    }
    
    validated_data = {}
    
    # Check for unknown fields
    unknown_fields = set(data.keys()) - allowed_fields
    if unknown_fields:
        return {'error': f'Unknown fields: {", ".join(unknown_fields)}'}
    
    # Validate subscription data (for push subscriptions)
    subscription = data.get('subscription')
    if subscription:
        if not isinstance(subscription, dict):
            return {'error': 'subscription must be an object'}
        
        required_sub_fields = {'endpoint', 'keys'}
        if not all(field in subscription for field in required_sub_fields):
            return {'error': 'subscription missing required fields'}
        
        # Validate endpoint
        endpoint = subscription.get('endpoint')
        if not isinstance(endpoint, str) or not endpoint.startswith('https://'):
            return {'error': 'subscription endpoint must be a valid HTTPS URL'}
        
        validated_data['subscription'] = subscription
    
    # Validate topics (optional)
    topics = data.get('topics')
    if topics:
        if not isinstance(topics, list):
            return {'error': 'topics must be an array'}
        
        allowed_topics = {'blog_posts', 'portfolio_updates', 'general'}
        for topic in topics:
            if not isinstance(topic, str) or topic not in allowed_topics:
                return {'error': f'Invalid topic. Must be one of: {", ".join(allowed_topics)}'}
        
        validated_data['topics'] = topics
    
    # Validate message content (optional)
    message = data.get('message')
    if message:
        if not isinstance(message, str) or len(message) > 1000:
            return {'error': 'message must be a string under 1000 characters'}
        
        validated_data['message'] = strip_tags(message)
    
    # Validate title (optional)
    title = data.get('title')
    if title:
        if not isinstance(title, str) or len(title) > 200:
            return {'error': 'title must be a string under 200 characters'}
        
        validated_data['title'] = strip_tags(title)
    
    return validated_data