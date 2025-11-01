"""
WebSocket Connection Pool Management
Advanced connection pooling and management for WebSocket connections
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection"""

    channel_name: str
    user_id: Optional[int]
    room_name: Optional[str]
    connected_at: float
    last_activity: float
    message_count: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    ip_address: str = ""
    user_agent: str = ""


class ConnectionPool:
    """
    Advanced WebSocket connection pool manager
    Features:
    - Connection tracking and statistics
    - Rate limiting per connection/user
    - Automatic cleanup of stale connections
    - Connection health monitoring
    - Resource usage tracking
    """

    def __init__(self, max_connections=1000, cleanup_interval=300):
        self.max_connections = max_connections
        self.cleanup_interval = cleanup_interval

        # Connection storage
        self.connections: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[int, Set[str]] = defaultdict(set)
        self.room_connections: Dict[str, Set[str]] = defaultdict(set)

        # Rate limiting
        self.message_rates: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.connection_rates: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10))

        # Statistics
        self.total_connections_made = 0
        self.total_messages_sent = 0
        self.total_bytes_transferred = 0

        # Cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()

    def add_connection(
        self,
        channel_name: str,
        user_id: Optional[int] = None,
        room_name: Optional[str] = None,
        ip_address: str = "",
        user_agent: str = "",
    ) -> bool:
        """
        Add a new connection to the pool
        Returns False if connection limit is reached
        """
        if len(self.connections) >= self.max_connections:
            logger.warning(f"Connection limit reached ({self.max_connections})")
            return False

        # Check rate limiting for IP
        if self._is_ip_rate_limited(ip_address):
            logger.warning(f"IP rate limited: {ip_address}")
            return False

        current_time = time.time()

        # Add to connection rates for IP
        self.connection_rates[ip_address].append(current_time)

        # Create connection info
        connection_info = ConnectionInfo(
            channel_name=channel_name,
            user_id=user_id,
            room_name=room_name,
            connected_at=current_time,
            last_activity=current_time,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Store connection
        self.connections[channel_name] = connection_info

        # Update indexes
        if user_id:
            self.user_connections[user_id].add(channel_name)

        if room_name:
            self.room_connections[room_name].add(channel_name)

        self.total_connections_made += 1

        logger.info(
            f"Connection added: {channel_name} (User: {user_id}, Room: {room_name})"
        )
        return True

    def remove_connection(self, channel_name: str) -> bool:
        """
        Remove a connection from the pool
        """
        if channel_name not in self.connections:
            return False

        connection_info = self.connections[channel_name]

        # Remove from indexes
        if connection_info.user_id:
            self.user_connections[connection_info.user_id].discard(channel_name)
            if not self.user_connections[connection_info.user_id]:
                del self.user_connections[connection_info.user_id]

        if connection_info.room_name:
            self.room_connections[connection_info.room_name].discard(channel_name)
            if not self.room_connections[connection_info.room_name]:
                del self.room_connections[connection_info.room_name]

        # Remove connection
        del self.connections[channel_name]

        # Clean up message rates
        if channel_name in self.message_rates:
            del self.message_rates[channel_name]

        logger.info(f"Connection removed: {channel_name}")
        return True

    def update_activity(
        self, channel_name: str, bytes_sent: int = 0, bytes_received: int = 0
    ) -> bool:
        """
        Update connection activity
        """
        if channel_name not in self.connections:
            return False

        connection_info = self.connections[channel_name]
        connection_info.last_activity = time.time()
        connection_info.message_count += 1
        connection_info.bytes_sent += bytes_sent
        connection_info.bytes_received += bytes_received

        self.total_messages_sent += 1
        self.total_bytes_transferred += bytes_sent + bytes_received

        return True

    def is_rate_limited(self, channel_name: str) -> bool:
        """
        Check if a connection is rate limited
        """
        current_time = time.time()
        rates = self.message_rates[channel_name]

        # Add current message
        rates.append(current_time)

        # Check rate limit (max 60 messages per minute)
        one_minute_ago = current_time - 60
        recent_messages = sum(1 for timestamp in rates if timestamp > one_minute_ago)

        return recent_messages > 60

    def _is_ip_rate_limited(self, ip_address: str) -> bool:
        """
        Check if an IP address is rate limited for connections
        """
        current_time = time.time()
        rates = self.connection_rates[ip_address]

        # Check rate limit (max 5 connections per minute)
        one_minute_ago = current_time - 60
        recent_connections = sum(1 for timestamp in rates if timestamp > one_minute_ago)

        return recent_connections > 5

    def get_user_connections(self, user_id: int) -> List[str]:
        """
        Get all connections for a user
        """
        return list(self.user_connections.get(user_id, set()))

    def get_room_connections(self, room_name: str) -> List[str]:
        """
        Get all connections in a room
        """
        return list(self.room_connections.get(room_name, set()))

    def get_connection_info(self, channel_name: str) -> Optional[ConnectionInfo]:
        """
        Get connection information
        """
        return self.connections.get(channel_name)

    def get_statistics(self) -> Dict:
        """
        Get pool statistics
        """
        current_time = time.time()

        # Calculate active connections by time ranges
        active_1min = 0
        active_5min = 0
        active_15min = 0

        for conn in self.connections.values():
            time_since_activity = current_time - conn.last_activity
            if time_since_activity < 60:
                active_1min += 1
            if time_since_activity < 300:
                active_5min += 1
            if time_since_activity < 900:
                active_15min += 1

        return {
            "total_connections": len(self.connections),
            "authenticated_connections": len(
                [conn for conn in self.connections.values() if conn.user_id]
            ),
            "active_connections_1min": active_1min,
            "active_connections_5min": active_5min,
            "active_connections_15min": active_15min,
            "unique_users": len(self.user_connections),
            "active_rooms": len(self.room_connections),
            "total_connections_made": self.total_connections_made,
            "total_messages_sent": self.total_messages_sent,
            "total_bytes_transferred": self.total_bytes_transferred,
            "average_messages_per_connection": (
                self.total_messages_sent / max(self.total_connections_made, 1)
            ),
        }

    def cleanup_stale_connections(self, max_idle_time: int = 3600) -> int:
        """
        Clean up stale connections (inactive for more than max_idle_time seconds)
        """
        current_time = time.time()
        stale_connections = []

        for channel_name, conn in self.connections.items():
            if current_time - conn.last_activity > max_idle_time:
                stale_connections.append(channel_name)

        for channel_name in stale_connections:
            self.remove_connection(channel_name)

        if stale_connections:
            logger.info(f"Cleaned up {len(stale_connections)} stale connections")

        return len(stale_connections)

    def _start_cleanup_task(self):
        """
        Start the cleanup task
        """

        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(self.cleanup_interval)
                    self.cleanup_stale_connections()
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_loop())

    def stop_cleanup_task(self):
        """
        Stop the cleanup task
        """
        if self._cleanup_task:
            self._cleanup_task.cancel()

    async def broadcast_to_room(self, room_name: str, message: dict):
        """
        Broadcast a message to all connections in a room
        """
        channel_layer = get_channel_layer()
        connections = self.get_room_connections(room_name)

        for channel_name in connections:
            try:
                await channel_layer.send(channel_name, message)
            except Exception as e:
                logger.error(f"Error sending message to {channel_name}: {e}")
                # Remove failed connection
                self.remove_connection(channel_name)

    async def broadcast_to_user(self, user_id: int, message: dict):
        """
        Broadcast a message to all connections of a user
        """
        channel_layer = get_channel_layer()
        connections = self.get_user_connections(user_id)

        for channel_name in connections:
            try:
                await channel_layer.send(channel_name, message)
            except Exception as e:
                logger.error(f"Error sending message to {channel_name}: {e}")
                # Remove failed connection
                self.remove_connection(channel_name)


# Global connection pool instance
connection_pool = ConnectionPool()


def get_connection_pool() -> ConnectionPool:
    """
    Get the global connection pool instance
    """
    return connection_pool
