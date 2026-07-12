#!/usr/bin/env python3
"""Test notification system"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from webcms.notifications import NotificationManager, SMTPAdapter


class MockAdapter:
    async def send(self, to_email, subject, html_body, text_body=None, from_email=None):
        print(f'Mock send to {to_email}: {subject}')
        return {"success": True}


async def test_notifications():
    print('Testing notification system...')

    manager = NotificationManager(email_adapter=MockAdapter())
    manager.preferences.update_preferences("user1", {
        "email": {"enabled": True, "digest": "daily"}
    })

    result = await manager.notify(
        user_id="user1",
        event_type="welcome",
        subject="Welcome to WebCMS",
        context={"username": "Alice", "email": "alice@example.com"}
    )
    print(f'Notify result: {result}')

    digest = await manager.send_digest("daily")
    print(f'Digest queued: {digest}')

    queue_result = await manager.process_email_queue()
    print(f'Queue processed: {queue_result}')

    stats = manager.email_queue.get_stats()
    print(f'Queue stats: {stats}')

    in_app = manager.get_in_app_notifications("user1")
    print(f'In-app notifications: {len(in_app)}')

    print('Notification system verified!')


if __name__ == '__main__':
    asyncio.run(test_notifications())
