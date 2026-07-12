#!/usr/bin/env python3
"""Test workflow system"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from webcms.workflow import WorkflowManager


async def test_workflow():
    print('Testing WorkflowManager...')
    manager = WorkflowManager()

    default = await manager.get_default_workflow()
    await manager.create_workflow_definition(default)
    print(f'Created workflow: {default.name}')

    instance = await manager.start_workflow(
        content_id='post-1',
        content_type='post',
        workflow_id=default.workflow_id
    )
    print(f'Started workflow instance in state: {instance.current_state}')

    await manager.assign_reviewers(instance.instance_id, ['reviewer1', 'reviewer2'])
    print('Assigned reviewers')

    success, error = await manager.transition(
        instance.instance_id, 'review',
        user_id='author1', username='Author', comment='Ready for review'
    )
    print(f'Transition to review: {success is not None}')

    success, error = await manager.transition(
        instance.instance_id, 'approved',
        user_id='reviewer1', username='Reviewer One', comment='Looks good'
    )
    print(f'Transition to approved: {success is not None}')

    success, error = await manager.transition(
        instance.instance_id, 'published',
        user_id='editor1', username='Editor'
    )
    print(f'Transition to published: {success is not None}')

    from datetime import datetime, timedelta
    start = datetime.utcnow()
    end = start + timedelta(days=30)
    calendar = await manager.get_content_calendar(start, end)
    print(f'Content calendar: {len(calendar)} items')

    notifications = manager.notifications.get_notifications()
    print(f'Notifications generated: {len(notifications)}')

    print('Workflow system verified!')


if __name__ == '__main__':
    asyncio.run(test_workflow())
