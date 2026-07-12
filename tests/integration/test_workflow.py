#!/usr/bin/env python3
"""Integration tests for workflow system."""

import asyncio
import pytest
from webcms.workflow import WorkflowManager


@pytest.mark.asyncio
async def test_full_workflow():
    manager = WorkflowManager()
    default = await manager.get_default_workflow()
    await manager.create_workflow_definition(default)

    instance = await manager.start_workflow(
        content_id="post-1",
        content_type="post",
        workflow_id=default.workflow_id
    )
    assert instance.current_state == "draft"

    await manager.assign_reviewers(instance.instance_id, ["reviewer1"])

    success, error = await manager.transition(
        instance.instance_id, "review",
        user_id="author1", username="Author"
    )
    assert success is not None
    assert error is None

    success, error = await manager.transition(
        instance.instance_id, "approved",
        user_id="reviewer1", username="Reviewer"
    )
    assert success is not None

    success, error = await manager.transition(
        instance.instance_id, "published",
        user_id="editor1", username="Editor"
    )
    assert success is not None
    assert instance.current_state == "published"
