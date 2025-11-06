"""
Push Notification Service Helpers
=================================

Helper classes for push notification service using Extract Class pattern.

Complexity reduced: C:16 → A:2 (main method)
"""

import json
import logging
from typing import Any, Dict, List, Optional

from django.utils import timezone

logger = logging.getLogger(__name__)


class PayloadBuilder:
    """
    Build push notification payload

    Complexity: A:5
    """

    @staticmethod
    def build(
        title: str,
        body: str,
        icon: Optional[str] = None,
        image: Optional[str] = None,
        badge: Optional[str] = None,
        url: Optional[str] = None,
        tag: Optional[str] = None,
        actions: Optional[List[Dict[str, str]]] = None,
        notification_type: str = "custom",
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build notification payload with all parameters

        Complexity: A:5
        """
        payload = {
            "title": title,
            "body": body,
            "icon": icon or "/static/icons/icon-192x192.png",
            "badge": badge or "/static/icons/badge-72x72.png",
            "data": {
                "url": url or "/",
                "type": notification_type,
                "timestamp": timezone.now().isoformat(),
                **(additional_data or {}),
            },
        }

        if image:
            payload["image"] = image
        if tag:
            payload["tag"] = tag
        if actions:
            payload["actions"] = actions

        return payload


class SubscriptionValidator:
    """
    Validate subscription status

    Complexity: A:4
    """

    @staticmethod
    def validate(
        subscription: Any, webpush_available: bool
    ) -> tuple[bool, Optional[str], Optional[Dict]]:
        """
        Validate subscription and environment

        Returns:
            (is_valid, error_message, error_response)

        Complexity: A:4
        """
        if not webpush_available:
            return (
                False,
                "pywebpush not installed",
                {
                    "success": False,
                    "error": "pywebpush not installed",
                    "subscription_id": subscription.id,
                },
            )

        if not subscription.enabled:
            return (
                False,
                "Subscription disabled",
                {
                    "success": False,
                    "error": "Subscription disabled",
                    "subscription_id": subscription.id,
                },
            )

        return True, None, None


class SubscriptionDataBuilder:
    """
    Build subscription data for pywebpush

    Complexity: A:1
    """

    @staticmethod
    def build(subscription: Any) -> Dict[str, Any]:
        """
        Build subscription data structure

        Complexity: A:1
        """
        return {
            "endpoint": subscription.endpoint,
            "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
        }


class NotificationLogger:
    """
    Log notification attempts and results

    Complexity: A:5
    """

    def __init__(self, notification_log_model):
        self.NotificationLog = notification_log_model

    def log_success(
        self,
        subscription: Any,
        title: str,
        body: str,
        notification_type: str,
        response_code: int,
    ) -> None:
        """
        Log successful notification

        Complexity: A:1
        """
        self.NotificationLog.objects.create(
            subscription=subscription,
            title=title,
            body=body,
            notification_type=notification_type,
            status="sent",
            response_code=response_code,
            sent_at=timezone.now(),
        )

    def log_failure(
        self,
        subscription: Any,
        title: str,
        body: str,
        notification_type: str,
        error_message: str,
    ) -> None:
        """
        Log failed notification

        Complexity: A:1
        """
        self.NotificationLog.objects.create(
            subscription=subscription,
            title=title,
            body=body,
            notification_type=notification_type,
            status="failed",
            error_message=error_message,
            sent_at=timezone.now(),
        )

    def log_error(
        self,
        subscription: Any,
        title: str,
        body: str,
        notification_type: str,
        error_message: str,
    ) -> None:
        """
        Log error notification

        Complexity: A:1
        """
        self.NotificationLog.objects.create(
            subscription=subscription,
            title=title,
            body=body,
            notification_type=notification_type,
            status="error",
            error_message=error_message,
            sent_at=timezone.now(),
        )


class ErrorHandler:
    """
    Handle push notification errors

    Complexity: A:3
    """

    @staticmethod
    def handle_webpush_error(
        error_message: str, subscription: Any, logger_instance
    ) -> None:
        """
        Handle WebPushException errors, disable expired subscriptions

        Complexity: A:3
        """
        if "410" in error_message or "Expired" in error_message:
            # Subscription expired, disable it
            subscription.enabled = False
            subscription.save(update_fields=["enabled"])
            logger_instance.info(f"Disabled expired subscription: {subscription.id}")


class NotificationSender:
    """
    Orchestrator for sending push notifications

    Complexity: B:7
    """

    def __init__(
        self,
        webpush_func,
        vapid_private_key: str,
        vapid_subject: str,
        notification_log_model,
    ):
        self.webpush = webpush_func
        self.vapid_private_key = vapid_private_key
        self.vapid_subject = vapid_subject
        self.logger = NotificationLogger(notification_log_model)

    def send(
        self,
        subscription: Any,
        payload: Dict[str, Any],
        ttl: int,
        title: str,
        body: str,
        notification_type: str,
    ) -> Dict[str, Any]:
        """
        Send notification using pywebpush

        Complexity: B:7
        """
        # Build subscription data
        subscription_data = SubscriptionDataBuilder.build(subscription)
        vapid_claims = {"sub": self.vapid_subject}

        try:
            # Send the notification
            response = self.webpush(
                subscription_info=subscription_data,
                data=json.dumps(payload),
                vapid_private_key=self.vapid_private_key,
                vapid_claims=vapid_claims,
                ttl=ttl,
            )

            # Update subscription
            subscription.last_used = timezone.now()
            subscription.save(update_fields=["last_used"])

            # Log success
            response_code = (
                response.status_code if hasattr(response, "status_code") else 200
            )
            self.logger.log_success(
                subscription, title, body, notification_type, response_code
            )

            return {
                "success": True,
                "subscription_id": subscription.id,
                "response_code": response_code,
            }

        except Exception as e:
            # Import here to avoid circular dependency
            from pywebpush import WebPushException

            error_message = str(e)

            if isinstance(e, WebPushException):
                # Log failure
                self.logger.log_failure(
                    subscription, title, body, notification_type, error_message
                )

                # Handle expired subscriptions
                ErrorHandler.handle_webpush_error(error_message, subscription, logger)

            else:
                # Log error
                logger.error(
                    f"Unexpected error sending push notification: {error_message}"
                )
                self.logger.log_error(
                    subscription, title, body, notification_type, error_message
                )

            return {
                "success": False,
                "error": error_message,
                "subscription_id": subscription.id,
            }
