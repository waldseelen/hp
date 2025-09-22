"""
Basic analytics tracking for the portfolio site
"""
from django.http import HttpRequest
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class Analytics:
    """Simple analytics tracker"""

    def track_event(self, event_type: str, data: dict = None, request: HttpRequest = None):
        """Track an analytics event"""
        event_data = {
            'type': event_type,
            'timestamp': timezone.now().isoformat(),
            'data': data or {}
        }

        if request:
            event_data.update({
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'ip_address': self._get_client_ip(request),
                'path': request.path,
                'method': request.method,
            })

        # For now, just log the event
        logger.info(f"Analytics Event: {event_data}")

        return event_data

    def track_page_view(self, request: HttpRequest, page_title: str = None, page_path: str = None):
        """Track a page view"""
        if page_path is None:
            page_path = request.path
        return self.track_event('page_view', {
            'title': page_title,
            'url': request.build_absolute_uri(page_path),
            'path': page_path,
        }, request)

    def track_contact_form_submission(self, request: HttpRequest, form_data: dict):
        """Track contact form submission"""
        # Don't log sensitive data
        safe_data = {
            'has_name': bool(form_data.get('name')),
            'has_email': bool(form_data.get('email')),
            'has_message': bool(form_data.get('message')),
            'message_length': len(form_data.get('message', '')),
        }

        return self.track_event('contact_form_submission', safe_data, request)

    def track_playground_code_execution(self, request: HttpRequest, language: str, execution_time: float):
        """Track playground code execution"""
        return self.track_event('playground_code_execution', {
            'language': language,
            'execution_time': execution_time,
        }, request)

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip


# Global analytics instance
analytics = Analytics()