"""
Workflow Manager for WebCMS

Manages workflow definitions, instances, transitions, and scheduled publishing.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from .models import WorkflowState, WorkflowTransition, WorkflowDefinition, WorkflowInstance
from .notifications import NotificationManager

logger = logging.getLogger("webcms.workflow")


class WorkflowManager:
    """Manages content workflows."""

    def __init__(self, storage_backend=None, notification_manager=None):
        self.storage = storage_backend or self._default_storage()
        self.notifications = notification_manager or NotificationManager()
        self._default_workflow = self._create_default_workflow()

    def _default_storage(self):
        return _FileStorage("workflows.json")

    def _create_default_workflow(self):
        """Create default editorial workflow."""
        states = [
            WorkflowState("draft", "Draft", "Draft", is_initial=True, color="#6c757d"),
            WorkflowState("review", "Review", "In Review", requires_approval=True, color="#fd7e14"),
            WorkflowState("approved", "Approved", "Approved", color="#198754"),
            WorkflowState("published", "Published", "Published", is_final=True, color="#0d6efd"),
            WorkflowState("rejected", "Rejected", "Rejected", color="#dc3545")
        ]

        transitions = [
            WorkflowTransition("submit", "draft", "review", "Submit for Review", required_role="editor"),
            WorkflowTransition("approve", "review", "approved", "Approve", required_role="reviewer"),
            WorkflowTransition("reject", "review", "rejected", "Reject", required_role="reviewer", requires_comment=True),
            WorkflowTransition("publish", "approved", "published", "Publish", required_role="publisher"),
            WorkflowTransition("revise", "rejected", "draft", "Revise", required_role="editor"),
            WorkflowTransition("unpublish", "published", "draft", "Unpublish", required_role="publisher")
        ]

        return WorkflowDefinition(
            workflow_id="default-editorial",
            name="Default Editorial Workflow",
            content_types=["post", "page"],
            states=states,
            transitions=transitions,
            is_default=True
        )

    async def create_workflow_definition(self, definition: WorkflowDefinition):
        """Create or update workflow definition."""
        await self.storage.save_definition(definition)
        return definition

    async def get_default_workflow(self):
        """Get default workflow definition."""
        workflows = await self.storage.list_definitions()
        for wf in workflows:
            if wf.is_default:
                return wf
        return self._default_workflow

    async def list_workflow_definitions(self):
        """List all workflow definitions."""
        return await self.storage.list_definitions()

    async def start_workflow(self, content_id, content_type, workflow_id=None,
                            user_id=None, username=None):
        """Start a workflow instance for content."""
        if workflow_id:
            workflow = await self.storage.get_definition(workflow_id)
        else:
            workflow = await self.get_default_workflow()

        if not workflow:
            return None

        initial_state = workflow.get_initial_state()
        if not initial_state:
            return None

        instance = WorkflowInstance(
            instance_id=None,
            workflow_id=workflow.workflow_id,
            content_id=content_id,
            content_type=content_type,
            current_state=initial_state.state_id
        )

        instance.add_history_entry(None, initial_state.state_id, user_id, username, "Workflow started")
        await self.storage.save_instance(instance)

        return instance

    async def transition(self, instance_id, to_state, user_id=None,
                        username=None, comment=None, user_roles=None):
        """Transition workflow instance to new state."""
        instance = await self.storage.get_instance(instance_id)
        if not instance:
            return None, "Instance not found"

        workflow = await self.storage.get_definition(instance.workflow_id)
        if not workflow:
            return None, "Workflow definition not found"

        transition = workflow.get_transition(instance.current_state, to_state)
        if not transition:
            return None, f"Invalid transition: {instance.current_state} -> {to_state}"

        # Check role permissions
        if transition.required_role and user_roles:
            if transition.required_role not in user_roles:
                return None, f"Requires role: {transition.required_role}"

        if transition.requires_comment and not comment:
            return None, "Comment required for this transition"

        from_state = instance.current_state
        instance.current_state = to_state
        instance.add_history_entry(from_state, to_state, user_id, username, comment)

        await self.storage.save_instance(instance)

        # Send notification
        await self.notifications.notify_state_change(
            instance.content_id,
            instance.content_type,
            from_state,
            to_state,
            instance.assigned_reviewers,
            user_name=username or "System"
        )

        return instance, None

    async def assign_reviewers(self, instance_id, reviewer_ids):
        """Assign reviewers to workflow instance."""
        instance = await self.storage.get_instance(instance_id)
        if not instance:
            return None

        instance.assigned_reviewers = reviewer_ids
        await self.storage.save_instance(instance)

        for reviewer_id in reviewer_ids:
            await self.notifications.notify_review_request(
                instance.content_id,
                instance.content_type,
                reviewer_id,
                reviewer_id,
                "Editor"
            )

        return instance

    async def schedule_publish(self, instance_id, publish_time):
        """Schedule content publishing."""
        instance = await self.storage.get_instance(instance_id)
        if not instance:
            return None

        instance.scheduled_publish = publish_time
        await self.storage.save_instance(instance)

        await self.notifications.notify_scheduled_publish(
            instance.content_id,
            instance.content_type,
            publish_time,
            instance.assigned_reviewers
        )

        return instance

    async def get_content_calendar(self, start_date, end_date, content_type=None):
        """Get content calendar for date range."""
        instances = await self.storage.list_instances()

        calendar = []
        for instance in instances:
            if content_type and instance.content_type != content_type:
                continue

            if instance.scheduled_publish:
                if start_date <= instance.scheduled_publish <= end_date:
                    calendar.append({
                        "instance_id": instance.instance_id,
                        "content_id": instance.content_id,
                        "content_type": instance.content_type,
                        "current_state": instance.current_state,
                        "scheduled_publish": instance.scheduled_publish.isoformat(),
                        "reviewers": instance.assigned_reviewers
                    })

        return calendar

    async def process_scheduled_publishes(self):
        """Publish scheduled content that is due."""
        now = datetime.utcnow()
        instances = await self.storage.list_instances()

        published_count = 0
        for instance in instances:
            if (instance.scheduled_publish and
                instance.scheduled_publish <= now and
                instance.current_state == "approved"):

                await self.transition(
                    instance.instance_id,
                    "published",
                    user_id="system",
                    username="System",
                    comment="Scheduled publish"
                )
                published_count += 1

        return published_count


class _FileStorage:
    """Simple file-based workflow storage."""

    def __init__(self, filepath):
        self.filepath = filepath
        self._definitions = {}
        self._instances = {}
        self._load()

    def _load(self):
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
                self._definitions = {
                    wid: WorkflowDefinition(
                        wid,
                        wdata["name"],
                        wdata.get("content_types", ["post", "page"]),
                        [WorkflowState(**s) for s in wdata.get("states", [])],
                        [WorkflowTransition(**t) for t in wdata.get("transitions", [])],
                        wdata.get("is_default", False)
                    )
                    for wid, wdata in data.get("definitions", {}).items()
                }
                self._instances = {
                    iid: WorkflowInstance(
                        iid,
                        idata["workflow_id"],
                        idata["content_id"],
                        idata["content_type"],
                        idata["current_state"],
                        idata.get("assigned_reviewers", []),
                        datetime.fromisoformat(idata["scheduled_publish"]) if idata.get("scheduled_publish") else None,
                        idata.get("history", []),
                        datetime.fromisoformat(idata["created_at"]) if idata.get("created_at") else None
                    )
                    for iid, idata in data.get("instances", {}).items()
                }
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    async def save_definition(self, definition):
        self._definitions[definition.workflow_id] = definition
        self._persist()

    async def get_definition(self, workflow_id):
        return self._definitions.get(workflow_id)

    async def list_definitions(self):
        return list(self._definitions.values())

    async def save_instance(self, instance):
        self._instances[instance.instance_id] = instance
        self._persist()

    async def get_instance(self, instance_id):
        return self._instances.get(instance_id)

    async def list_instances(self):
        return list(self._instances.values())

    def _persist(self):
        data = {
            "definitions": {
                wid: wf.to_dict() for wid, wf in self._definitions.items()
            },
            "instances": {
                iid: inst.to_dict() for iid, inst in self._instances.items()
            }
        }
        with open(self.filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
