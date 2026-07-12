#!/usr/bin/env python3
"""Integration tests for notification system."""

import pytest
from webcms.notifications import NotificationManager


class MockAdapter:
    async def send(self, to_email, subject, html_body, text_body=None, from_email=None):
        return {"success": True}


@pytest.mark.asyncio
async def test_email_notification():
    manager = NotificationManager(email_adapter=MockAdapter())
    result = await manager.notify(
        user_id="user1",
        event_type="welcome",
        subject="Welcome",
        context={"username": "Alice", "email": "alice@example.com"}
    )
    assert "email" in result
    assert "in_app" in result


@pytest.mark.asyncio
async def test_digest_queue():
    manager = NotificationManager(email_adapter=MockAdapter())
    manager.preferences.update_preferences("user1", {
        "email": {"enabled": True, "digest": "daily"}
    })
    queued = await manager.send_digest("daily")
    assert queued["queued"] == 1

    processed = await manager.process_email_queue()
    assert processed["sent"] == 1
