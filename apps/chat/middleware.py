"""
WebSocket Authentication Middleware
Custom middleware for handling WebSocket authentication and session management
"""

import logging
from urllib.parse import parse_qs

from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.models import Session
from django.utils import timezone

from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

logger = logging.getLogger(__name__)


class WebSocketAuthMiddleware(BaseMiddleware):
    """
    Custom WebSocket authentication middleware that supports:
    - Session-based authentication
    - Token-based authentication
    - Anonymous user handling
    - Connection logging and monitoring
    """

    def __init__(self, inner):
        super().__init__(inner)
        self.connections = {}  # Track active connections

    async def __call__(self, scope, receive, send):
        # Only process WebSocket connections
        if scope["type"] != "websocket":
            return await super().__call__(scope, receive, send)

        # Authenticate the user
        scope["user"] = await self.get_user(scope)

        # Add connection tracking
        connection_id = f"{scope['client'][0]}:{scope['client'][1]}"
        self.connections[connection_id] = {
            "user": scope["user"],
            "connected_at": timezone.now(),
            "path": scope.get("path", ""),
        }

        logger.info(
            f"WebSocket connection established: {connection_id} for user {scope['user']}"
        )

        # Wrap send to track disconnections
        original_send = send

        async def wrapped_send(message):
            if message["type"] == "websocket.disconnect":
                if connection_id in self.connections:
                    duration = (
                        timezone.now() - self.connections[connection_id]["connected_at"]
                    )
                    logger.info(
                        f"WebSocket connection closed: {connection_id}, duration: {duration}"
                    )
                    del self.connections[connection_id]
            return await original_send(message)

        return await super().__call__(scope, receive, wrapped_send)

    @database_sync_to_async
    def get_user(self, scope):
        """
        Get user from session or token authentication
        """
        try:
            # Try session-based authentication first
            user = self.get_user_from_session(scope)
            if user and user.is_authenticated:
                return user

            # Try token-based authentication
            user = self.get_user_from_token(scope)
            if user and user.is_authenticated:
                return user

            # Return anonymous user
            return AnonymousUser()

        except Exception as e:
            logger.error(f"Authentication error in WebSocket: {e}")
            return AnonymousUser()

    def get_user_from_session(self, scope):  # noqa: C901
        """
        Extract user from Django session
        """
        try:
            # Get session key from cookies
            cookies = {}
            for header_name, header_value in scope.get("headers", []):
                if header_name == b"cookie":
                    cookie_str = header_value.decode("utf-8")
                    for cookie in cookie_str.split(";"):
                        if "=" in cookie:
                            key, value = cookie.strip().split("=", 1)
                            cookies[key] = value
                    break

            session_key = cookies.get("sessionid")
            if not session_key:
                return AnonymousUser()

            # Get session data
            try:
                session = Session.objects.get(session_key=session_key)
                if session.expire_date < timezone.now():
                    return AnonymousUser()

                session_data = session.get_decoded()
                user_id = session_data.get("_auth_user_id")

                if user_id:
                    return User.objects.get(id=user_id)

            except (Session.DoesNotExist, User.DoesNotExist):
                pass

            return AnonymousUser()

        except Exception as e:
            logger.error(f"Session authentication error: {e}")
            return AnonymousUser()

    def get_user_from_token(self, scope):
        """
        Extract user from authentication token (query params or headers)
        """
        try:
            # Check query parameters for token
            query_string = scope.get("query_string", b"").decode("utf-8")
            query_params = parse_qs(query_string)
            token = query_params.get("token", [None])[0]

            if not token:
                # Check headers for authorization token
                for header_name, header_value in scope.get("headers", []):
                    if header_name == b"authorization":
                        auth_header = header_value.decode("utf-8")
                        if auth_header.startswith("Bearer "):
                            token = auth_header[7:]  # Remove "Bearer " prefix
                        break

            if token:
                # Validate token (implement your token validation logic here)
                # For now, this is a placeholder - you should implement proper token validation
                # For example, JWT validation or API key lookup
                return self.validate_token(token)

            return AnonymousUser()

        except Exception as e:
            logger.error(f"Token authentication error: {e}")
            return AnonymousUser()

    def validate_token(self, token):
        """
        Validate authentication token
        Implement your token validation logic here
        """
        # Placeholder implementation
        # You should implement proper token validation based on your requirements
        # This could be JWT validation, API key lookup, etc.
        return AnonymousUser()

    def get_active_connections(self):
        """
        Get statistics about active connections
        """
        return {
            "total_connections": len(self.connections),
            "authenticated_connections": len(
                [
                    conn
                    for conn in self.connections.values()
                    if conn["user"].is_authenticated
                ]
            ),
            "anonymous_connections": len(
                [
                    conn
                    for conn in self.connections.values()
                    if not conn["user"].is_authenticated
                ]
            ),
            "connections": list(self.connections.values()),
        }


# Create the middleware stack
def WebSocketAuthMiddlewareStack(inner):
    """
    Create WebSocket middleware stack with authentication
    """
    return WebSocketAuthMiddleware(AuthMiddlewareStack(inner))
