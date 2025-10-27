"""
Push Notification Service for Django Portfolio Application

This module provides push notification functionality integrated with the Django app.
Handles web push subscriptions and notification delivery using py-webpush.

Features:
- Web push subscription management
- Notification sending with VAPID authentication
- Batch notification delivery
- Error handling and logging
- Integration with Django models
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from django.db.models import Q, QuerySet

try:
    from pywebpush import webpush, WebPushException
except ImportError:
    webpush = None
    WebPushException = Exception

from ..models import WebPushSubscription, NotificationLog

logger = logging.getLogger(__name__)


class PushNotificationService:
    """
    Service class for handling web push notifications
    """

    def __init__(self):
        """Initialize the push notification service"""
        self.vapid_private_key = getattr(settings, 'WEBPUSH_SETTINGS', {}).get('VAPID_PRIVATE_KEY')
        self.vapid_public_key = getattr(settings, 'WEBPUSH_SETTINGS', {}).get('VAPID_PUBLIC_KEY')
        self.vapid_subject = getattr(settings, 'WEBPUSH_SETTINGS', {}).get('VAPID_SUBJECT', 'mailto:admin@localhost')

        if not self.vapid_private_key:
            logger.warning("VAPID private key not configured. Push notifications will not work.")

    def send_notification_to_subscription(
        self,
        subscription: 'WebPushSubscription',
        title: str,
        body: str,
        icon: Optional[str] = None,
        image: Optional[str] = None,
        badge: Optional[str] = None,
        url: Optional[str] = None,
        tag: Optional[str] = None,
        actions: Optional[List[Dict[str, str]]] = None,
        notification_type: str = 'custom',
        additional_data: Optional[Dict[str, Any]] = None,
        ttl: int = 86400  # 24 hours
    ) -> Dict[str, Any]:
        """
        Send a push notification to a single subscription

        Args:
            subscription: WebPushSubscription instance
            title: Notification title
            body: Notification body
            icon: Icon URL
            image: Image URL
            badge: Badge URL
            url: Click URL
            tag: Notification tag for grouping
            actions: List of action buttons
            notification_type: Type of notification
            additional_data: Additional payload data
            ttl: Time to live in seconds

        Returns:
            Dict with success status and details
        """
        if not webpush:
            return {
                'success': False,
                'error': 'pywebpush not installed',
                'subscription_id': subscription.id
            }

        if not subscription.enabled:
            return {
                'success': False,
                'error': 'Subscription disabled',
                'subscription_id': subscription.id
            }

        # Prepare notification payload
        payload = {
            'title': title,
            'body': body,
            'icon': icon or '/static/icons/icon-192x192.png',
            'badge': badge or '/static/icons/badge-72x72.png',
            'data': {
                'url': url or '/',
                'type': notification_type,
                'timestamp': timezone.now().isoformat(),
                **(additional_data or {})
            }
        }

        if image:
            payload['image'] = image
        if tag:
            payload['tag'] = tag
        if actions:
            payload['actions'] = actions

        # Prepare subscription data for pywebpush
        subscription_data = {
            'endpoint': subscription.endpoint,
            'keys': {
                'p256dh': subscription.p256dh,
                'auth': subscription.auth
            }
        }

        # VAPID configuration
        vapid_claims = {
            'sub': self.vapid_subject
        }

        try:
            # Send the notification
            response = webpush(
                subscription_info=subscription_data,
                data=json.dumps(payload),
                vapid_private_key=self.vapid_private_key,
                vapid_claims=vapid_claims,
                ttl=ttl
            )

            # Update subscription last used timestamp
            subscription.last_used = timezone.now()
            subscription.save(update_fields=['last_used'])

            # Log successful notification
            NotificationLog.objects.create(
                subscription=subscription,
                title=title,
                body=body,
                notification_type=notification_type,
                status='sent',
                response_code=response.status_code if hasattr(response, 'status_code') else 200,
                sent_at=timezone.now()
            )

            return {
                'success': True,
                'subscription_id': subscription.id,
                'response_code': response.status_code if hasattr(response, 'status_code') else 200
            }

        except WebPushException as e:
            error_message = str(e)

            # Log failed notification
            NotificationLog.objects.create(
                subscription=subscription,
                title=title,
                body=body,
                notification_type=notification_type,
                status='failed',
                error_message=error_message,
                sent_at=timezone.now()
            )

            # Handle specific error cases
            if '410' in error_message or 'Expired' in error_message:
                # Subscription expired, disable it
                subscription.enabled = False
                subscription.save(update_fields=['enabled'])
                logger.info(f"Disabled expired subscription: {subscription.id}")

            return {
                'success': False,
                'error': error_message,
                'subscription_id': subscription.id
            }

        except Exception as e:
            error_message = str(e)
            logger.error(f"Unexpected error sending push notification: {error_message}")

            # Log error
            NotificationLog.objects.create(
                subscription=subscription,
                title=title,
                body=body,
                notification_type=notification_type,
                status='error',
                error_message=error_message,
                sent_at=timezone.now()
            )

            return {
                'success': False,
                'error': error_message,
                'subscription_id': subscription.id
            }

    def send_notification_to_subscriptions(
        self,
        subscriptions: Union[List['WebPushSubscription'], 'QuerySet'],
        title: str,
        body: str,
        icon: Optional[str] = None,
        image: Optional[str] = None,
        badge: Optional[str] = None,
        url: Optional[str] = None,
        tag: Optional[str] = None,
        actions: Optional[List[Dict[str, str]]] = None,
        notification_type: str = 'custom',
        additional_data: Optional[Dict[str, Any]] = None,
        topics: Optional[List[str]] = None,
        max_concurrent: int = 10
    ) -> Dict[str, Any]:
        """
        Send a push notification to multiple subscriptions

        Args:
            subscriptions: List or QuerySet of WebPushSubscription instances
            title: Notification title
            body: Notification body
            icon: Icon URL
            image: Image URL
            badge: Badge URL
            url: Click URL
            tag: Notification tag
            actions: Action buttons
            notification_type: Notification type
            additional_data: Additional payload data
            topics: Filter subscriptions by topics (if provided)
            max_concurrent: Maximum concurrent sends

        Returns:
            Dict with results summary
        """
        # Filter subscriptions if topics specified
        if topics:
            subscriptions = subscriptions.filter(
                Q(topics__overlap=topics) | Q(topics__isnull=True)
            )

        # Ensure we have enabled subscriptions only
        subscriptions = subscriptions.filter(enabled=True)

        total_count = subscriptions.count() if hasattr(subscriptions, 'count') else len(subscriptions)
        success_count = 0
        failure_count = 0
        results = []

        logger.info(f"Sending push notification to {total_count} subscriptions")

        # Send notifications (in batches if needed for large numbers)
        for subscription in subscriptions:
            result = self.send_notification_to_subscription(
                subscription=subscription,
                title=title,
                body=body,
                icon=icon,
                image=image,
                badge=badge,
                url=url,
                tag=tag,
                actions=actions,
                notification_type=notification_type,
                additional_data=additional_data
            )

            results.append(result)

            if result['success']:
                success_count += 1
            else:
                failure_count += 1

        return {
            'total_count': total_count,
            'success_count': success_count,
            'failure_count': failure_count,
            'success_rate': (success_count / total_count * 100) if total_count > 0 else 0,
            'results': results
        }

    def send_broadcast_notification(
        self,
        title: str,
        body: str,
        icon: Optional[str] = None,
        image: Optional[str] = None,
        badge: Optional[str] = None,
        url: Optional[str] = None,
        tag: Optional[str] = None,
        actions: Optional[List[Dict[str, str]]] = None,
        notification_type: str = 'broadcast',
        additional_data: Optional[Dict[str, Any]] = None,
        topics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send a broadcast notification to all active subscriptions

        Args:
            title: Notification title
            body: Notification body
            icon: Icon URL
            image: Image URL
            badge: Badge URL
            url: Click URL
            tag: Notification tag
            actions: Action buttons
            notification_type: Notification type
            additional_data: Additional payload data
            topics: Filter by topics

        Returns:
            Dict with broadcast results
        """
        subscriptions = WebPushSubscription.objects.filter(enabled=True)

        return self.send_notification_to_subscriptions(
            subscriptions=subscriptions,
            title=title,
            body=body,
            icon=icon,
            image=image,
            badge=badge,
            url=url,
            tag=tag,
            actions=actions,
            notification_type=notification_type,
            additional_data=additional_data,
            topics=topics
        )

    def get_subscription_stats(self) -> Dict[str, Any]:
        """
        Get statistics about push subscriptions

        Returns:
            Dict with subscription statistics
        """
        total_subscriptions = WebPushSubscription.objects.count()
        active_subscriptions = WebPushSubscription.objects.filter(enabled=True).count()
        disabled_subscriptions = total_subscriptions - active_subscriptions

        # Recent activity (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        recent_subscriptions = WebPushSubscription.objects.filter(
            created_at__gte=week_ago
        ).count()

        # Browser breakdown
        browser_stats = WebPushSubscription.objects.values('browser').annotate(
            count=WebPushSubscription.objects.filter(
                browser=WebPushSubscription.objects.values('browser')
            ).count()
        ).order_by('-count')

        return {
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'disabled_subscriptions': disabled_subscriptions,
            'recent_subscriptions': recent_subscriptions,
            'browser_breakdown': list(browser_stats)
        }

    def get_notification_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Get statistics about sent notifications

        Args:
            days: Number of days to look back

        Returns:
            Dict with notification statistics
        """
        since_date = timezone.now() - timedelta(days=days)

        total_sent = NotificationLog.objects.filter(
            sent_at__gte=since_date
        ).count()

        successful = NotificationLog.objects.filter(
            sent_at__gte=since_date,
            status='sent'
        ).count()

        failed = NotificationLog.objects.filter(
            sent_at__gte=since_date,
            status__in=['failed', 'error']
        ).count()

        success_rate = (successful / total_sent * 100) if total_sent > 0 else 0

        # Type breakdown
        type_stats = NotificationLog.objects.filter(
            sent_at__gte=since_date
        ).values('notification_type').annotate(
            count=NotificationLog.objects.filter(
                sent_at__gte=since_date,
                notification_type=NotificationLog.objects.values('notification_type')
            ).count()
        ).order_by('-count')

        return {
            'period_days': days,
            'total_sent': total_sent,
            'successful': successful,
            'failed': failed,
            'success_rate': success_rate,
            'type_breakdown': list(type_stats)
        }

    def cleanup_expired_subscriptions(self) -> int:
        """
        Clean up expired or invalid subscriptions

        Returns:
            Number of subscriptions disabled
        """
        # This would typically involve checking with push services
        # For now, we'll disable subscriptions that haven't been used in 90 days
        cutoff_date = timezone.now() - timedelta(days=90)

        expired_subs = WebPushSubscription.objects.filter(
            enabled=True,
            last_used__lt=cutoff_date
        )

        count = expired_subs.update(enabled=False)
        logger.info(f"Disabled {count} expired subscriptions")

        return count

    def test_notification(self, endpoint: str) -> Dict[str, Any]:
        """
        Send a test notification to a specific endpoint

        Args:
            endpoint: Push endpoint URL

        Returns:
            Dict with test result
        """
        try:
            subscription = WebPushSubscription.objects.get(endpoint=endpoint)

            return self.send_notification_to_subscription(
                subscription=subscription,
                title="Test Notification",
                body="This is a test push notification from your portfolio site.",
                notification_type="test",
                url="/"
            )

        except WebPushSubscription.DoesNotExist:
            return {
                'success': False,
                'error': 'Subscription not found'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
