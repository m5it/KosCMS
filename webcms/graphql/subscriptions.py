"""
GraphQL subscriptions for real-time updates.
"""

import asyncio
from typing import Dict, Any


class SubscriptionManager:
    """Simple async subscription manager."""

    def __init__(self):
        self._channels: Dict[str, asyncio.Queue] = {}

    async def publish(self, channel: str, payload: Any):
        """Publish event to channel."""
        queue = self._channels.get(channel)
        if queue:
            await queue.put(payload)

    async def subscribe(self, channel: str):
        """Subscribe to channel and yield events."""
        queue = asyncio.Queue()
        self._channels[channel] = queue
        try:
            while True:
                yield await queue.get()
        finally:
            del self._channels[channel]


# Global subscription manager
subscription_manager = SubscriptionManager()
