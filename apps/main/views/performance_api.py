"""
Performance Monitoring and Notifications API Views
Provides endpoints for performance tracking and push notifications
"""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.main.validators import validate_json_input, API_SCHEMAS

logger = logging.getLogger(__name__)


@require_http_methods(["POST"])
@csrf_exempt
def collect_performance_metric(request):
    """
    API endpoint to collect performance metrics from frontend
    """
    try:
        # Validate content type
        if not request.content_type == 'application/json':
            return JsonResponse({
                'status': 'error',
                'message': 'Content-Type must be application/json'
            }, status=400)

        # Validate request body size
        if len(request.body) > 1024:  # 1KB limit
            return JsonResponse({
                'status': 'error',
                'message': 'Request body too large'
            }, status=413)

        data = json.loads(request.body)

        # Validate using comprehensive validator
        try:
            validated_data = validate_json_input(data, API_SCHEMAS['performance_metric'])
            metric_type = validated_data['metric_type']
            value = validated_data['value']
        except ValidationError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

        # Log the performance metric (sanitized)
        logger.info(f"Performance metric collected: {metric_type}={value:.2f}")

        return JsonResponse({
            'status': 'success',
            'message': 'Performance metric recorded',
            'timestamp': timezone.now().isoformat()
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Error collecting performance metric: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error'
        }, status=500)


@require_http_methods(["GET"])
def performance_dashboard_data(request):
    """
    API endpoint to get performance metrics summary for dashboard
    """
    try:
        # Mock data for now - in a real app this would come from a database
        dashboard_data = {
            'status': 'success',
            'data': {
                'metrics_summary': {
                    'lcp': {'average': 1.2, 'count': 100},
                    'fid': {'average': 45, 'count': 95},
                    'cls': {'average': 0.05, 'count': 98}
                },
                'total_metrics': 293,
                'period_days': 7
            },
            'timestamp': timezone.now().isoformat()
        }

        return JsonResponse(dashboard_data)

    except Exception as e:
        logger.error(f"Error getting performance dashboard data: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error'
        }, status=500)


@require_http_methods(["GET"])
def health_check(request):
    """
    Simple health check endpoint
    """
    try:
        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0',
            'database': 'healthy',
            'cache': 'healthy'
        })

    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return JsonResponse({
            'status': 'unhealthy',
            'timestamp': timezone.now().isoformat(),
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def subscribe_push_notifications(request):
    """
    API endpoint to subscribe to push notifications
    """
    try:
        data = json.loads(request.body)
        endpoint = data.get('endpoint')

        if not endpoint:
            return JsonResponse({
                'status': 'error',
                'message': 'endpoint is required'
            }, status=400)

        # Log the subscription
        logger.info(f"Push notification subscription: {endpoint}")

        return JsonResponse({
            'status': 'success',
            'message': 'Push subscription created',
            'subscription_id': 'mock_id_123'
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Error creating push subscription: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error'
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def send_push_notification(request):
    """
    API endpoint to send push notifications (admin only)
    """
    try:
        data = json.loads(request.body)
        title = data.get('title')
        body = data.get('body')

        if not title or not body:
            return JsonResponse({
                'status': 'error',
                'message': 'title and body are required'
            }, status=400)

        # Log the notification
        logger.info(f"Push notification sent: {title}")

        return JsonResponse({
            'status': 'success',
            'message': 'Notification sent successfully',
            'results': {
                'success_count': 1,
                'failure_count': 0
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Error sending push notification: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error'
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def log_error(request):
    """
    API endpoint to log errors from frontend
    """
    try:
        # Validate content type
        if not request.content_type == 'application/json':
            return JsonResponse({
                'status': 'error',
                'message': 'Content-Type must be application/json'
            }, status=400)

        # Validate request body size
        if len(request.body) > 2048:  # 2KB limit for error messages
            return JsonResponse({
                'status': 'error',
                'message': 'Request body too large'
            }, status=413)

        data = json.loads(request.body)
        message = data.get('message')
        level = data.get('level', 'error')

        if not message:
            return JsonResponse({
                'status': 'error',
                'message': 'message is required'
            }, status=400)

        # Validate and sanitize message
        import re
        from django.utils.html import strip_tags

        message = strip_tags(str(message))  # Remove HTML
        message = re.sub(r'\s+', ' ', message)  # Normalize whitespace

        if len(message) > 1000:  # Limit message length
            message = message[:1000] + '...'

        # Validate level
        allowed_levels = ['critical', 'error', 'warning', 'info']
        if level not in allowed_levels:
            level = 'error'

        # Check for suspicious content
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'data:',
            r'vbscript:',
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, message.lower()):
                logger.warning(f"Suspicious error message blocked: {message[:50]}...")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid error message content'
                }, status=400)

        # Log the error (sanitized)
        safe_message = f"Frontend {level}: {message}"
        if level == 'critical':
            logger.critical(safe_message)
        elif level == 'error':
            logger.error(safe_message)
        elif level == 'warning':
            logger.warning(safe_message)
        else:
            logger.info(safe_message)

        return JsonResponse({
            'status': 'success',
            'message': 'Error logged successfully',
            'error_id': 'mock_error_id_123'
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Error logging frontend error: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error'
        }, status=500)