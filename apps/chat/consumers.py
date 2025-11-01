"""
WebSocket Consumers for real-time chat and notifications
"""

import json
import logging

from django.utils import timezone

from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for chat functionality
    Handles real-time messaging between users
    """

    async def connect(self):
        """
        Handle WebSocket connection
        """
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.user = self.scope["user"]

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        # Send welcome message
        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection_established",
                    "message": f"Connected to room: {self.room_name}",
                    "user": (
                        str(self.user) if self.user.is_authenticated else "Anonymous"
                    ),
                    "timestamp": timezone.now().isoformat(),
                }
            )
        )

        logger.info(f"User {self.user} connected to chat room: {self.room_name}")

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection
        """
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        logger.info(f"User {self.user} disconnected from chat room: {self.room_name}")

    async def receive(self, text_data):
        """
        Handle messages from WebSocket
        """
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get("type", "chat_message")

            if message_type == "chat_message":
                await self.handle_chat_message(text_data_json)
            elif message_type == "typing_indicator":
                await self.handle_typing_indicator(text_data_json)
            elif message_type == "user_status":
                await self.handle_user_status(text_data_json)
            else:
                await self.send_error(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await self.send_error("Internal server error")

    async def handle_chat_message(self, data):
        """
        Handle chat message
        """
        message = data.get("message", "").strip()
        if not message:
            await self.send_error("Message cannot be empty")
            return

        # Rate limiting (simple implementation)
        if len(message) > 1000:
            await self.send_error("Message too long (max 1000 characters)")
            return

        # Save message to database (if needed)
        # await self.save_message(message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "user": str(self.user) if self.user.is_authenticated else "Anonymous",
                "user_id": self.user.id if self.user.is_authenticated else None,
                "timestamp": timezone.now().isoformat(),
            },
        )

    async def handle_typing_indicator(self, data):
        """
        Handle typing indicator
        """
        is_typing = data.get("is_typing", False)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "typing_indicator",
                "user": str(self.user) if self.user.is_authenticated else "Anonymous",
                "user_id": self.user.id if self.user.is_authenticated else None,
                "is_typing": is_typing,
                "timestamp": timezone.now().isoformat(),
            },
        )

    async def handle_user_status(self, data):
        """
        Handle user status updates
        """
        status = data.get("status", "online")

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_status",
                "user": str(self.user) if self.user.is_authenticated else "Anonymous",
                "user_id": self.user.id if self.user.is_authenticated else None,
                "status": status,
                "timestamp": timezone.now().isoformat(),
            },
        )

    async def send_error(self, message):
        """
        Send error message to client
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "message": message,
                    "timestamp": timezone.now().isoformat(),
                }
            )
        )

    # Group message handlers
    async def chat_message(self, event):
        """
        Send chat message to WebSocket
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_message",
                    "message": event["message"],
                    "user": event["user"],
                    "user_id": event.get("user_id"),
                    "timestamp": event["timestamp"],
                }
            )
        )

    async def typing_indicator(self, event):
        """
        Send typing indicator to WebSocket
        """
        # Don't send typing indicator to the sender
        if event.get("user_id") != (
            self.user.id if self.user.is_authenticated else None
        ):
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "typing_indicator",
                        "user": event["user"],
                        "user_id": event.get("user_id"),
                        "is_typing": event["is_typing"],
                        "timestamp": event["timestamp"],
                    }
                )
            )

    async def user_status(self, event):
        """
        Send user status to WebSocket
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_status",
                    "user": event["user"],
                    "user_id": event.get("user_id"),
                    "status": event["status"],
                    "timestamp": event["timestamp"],
                }
            )
        )


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications
    """

    async def connect(self):
        """
        Handle WebSocket connection for notifications
        """
        self.user = self.scope["user"]

        if self.user.is_authenticated:
            # Create personal notification group
            self.notification_group_name = f"notifications_{self.user.id}"

            # Join notification group
            await self.channel_layer.group_add(
                self.notification_group_name, self.channel_name
            )

            await self.accept()

            # Send connection confirmation
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "connection_established",
                        "message": "Connected to notifications",
                        "user": str(self.user),
                        "timestamp": timezone.now().isoformat(),
                    }
                )
            )

            logger.info(f"User {self.user} connected to notifications")
        else:
            # Reject connection for unauthenticated users
            await self.close(code=4001)

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection
        """
        if hasattr(self, "notification_group_name"):
            # Leave notification group
            await self.channel_layer.group_discard(
                self.notification_group_name, self.channel_name
            )

            logger.info(f"User {self.user} disconnected from notifications")

    async def receive(self, text_data):
        """
        Handle messages from WebSocket
        """
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get("type", "unknown")

            if message_type == "mark_as_read":
                await self.handle_mark_as_read(text_data_json)
            elif message_type == "get_unread_count":
                await self.handle_get_unread_count()
            else:
                await self.send_error(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling notification WebSocket message: {e}")
            await self.send_error("Internal server error")

    async def handle_mark_as_read(self, data):
        """
        Handle marking notifications as read
        """
        notification_id = data.get("notification_id")
        if notification_id:
            # Mark specific notification as read
            # await self.mark_notification_as_read(notification_id)
            pass
        else:
            # Mark all notifications as read
            # await self.mark_all_notifications_as_read()
            pass

        await self.send(
            text_data=json.dumps(
                {
                    "type": "marked_as_read",
                    "notification_id": notification_id,
                    "timestamp": timezone.now().isoformat(),
                }
            )
        )

    async def handle_get_unread_count(self):
        """
        Handle getting unread notification count
        """
        # count = await self.get_unread_notification_count()
        count = 0  # Placeholder

        await self.send(
            text_data=json.dumps(
                {
                    "type": "unread_count",
                    "count": count,
                    "timestamp": timezone.now().isoformat(),
                }
            )
        )

    async def send_error(self, message):
        """
        Send error message to client
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "message": message,
                    "timestamp": timezone.now().isoformat(),
                }
            )
        )

    # Group message handlers
    async def notification_message(self, event):
        """
        Send notification to WebSocket
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "notification",
                    "title": event["title"],
                    "message": event["message"],
                    "category": event.get("category", "general"),
                    "priority": event.get("priority", "normal"),
                    "data": event.get("data", {}),
                    "timestamp": event["timestamp"],
                }
            )
        )
