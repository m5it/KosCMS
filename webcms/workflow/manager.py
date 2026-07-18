"""
Workflow Manager for WebCMS

Manages workflow definitions, instances, transitions, and scheduled publishing.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from .models import WorkflowState, WorkflowTransition, WorkflowDefinition, WorkflowInstance
from .notifications import NotificationManager

logger = logging.getLogger("webcms.workflow")


class WorkflowManager:
    """Manages content workflows."""

    def __init__(self, storage_backend=None, notification_manager=None, db=None):
        self.db = db
        self.storage = storage_backend or self._default_storage()
        self.notifications = notification_manager or NotificationManager()
        self._default_workflow = self._create_default_workflow()
        
        # Ensure default workflow exists
        self._ensure_default_workflow()

    def _default_storage(self):
        """Get default storage backend."""
        if self.db:
            try:
                from .kosdb_storage import KosDBWorkflowStorage
                return KosDBWorkflowStorage(self.db)
            except Exception:
                pass
        return _FileStorage("workflows.json")

    def _ensure_default_workflow(self):
        """Ensure default workflow exists in storage."""
        try:
            existing = self.storage.get_definition(self._default_workflow.workflow_id)
            if not existing:
                self.storage.save_definition(self._default_workflow)
        except Exception:
            pass

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

    # ============ Async Methods (for async code) ============

    async def create_workflow_definition(self, definition: WorkflowDefinition):
        """Create or update workflow definition."""
        self.storage.save_definition(definition)
        return definition

    async def get_default_workflow(self):
        """Get default workflow definition."""
        workflows = self.storage.list_definitions()
        for wf in workflows:
            if wf.is_default:
                return wf
        return self._default_workflow

    async def list_workflow_definitions(self):
        """List all workflow definitions."""
        return self.storage.list_definitions()

    async def start_workflow(self, content_id, content_type, workflow_id=None,
                            user_id=None, username=None):
        """Start a workflow instance for content."""
        if workflow_id:
            workflow = self.storage.get_definition(workflow_id)
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
        self.storage.save_instance(instance)

        return instance

    async def transition(self, instance_id, to_state, user_id=None,
                        username=None, comment=None, user_roles=None):
        """Transition workflow instance to new state."""
        instance = self.storage.get_instance(instance_id)
        if not instance:
            return None, "Instance not found"

        workflow = self.storage.get_definition(instance.workflow_id)
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

        self.storage.save_instance(instance)

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
        instance = self.storage.get_instance(instance_id)
        if not instance:
            return None

        instance.assigned_reviewers = reviewer_ids
        self.storage.save_instance(instance)

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
        instance = self.storage.get_instance(instance_id)
        if not instance:
            return None

        instance.scheduled_publish = publish_time
        self.storage.save_instance(instance)

        await self.notifications.notify_scheduled_publish(
            instance.content_id,
            instance.content_type,
            publish_time,
            instance.assigned_reviewers
        )

        return instance

    async def get_content_calendar(self, start_date, end_date, content_type=None):
        """Get content calendar for date range."""
        instances = self.storage.list_instances()

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
        instances = self.storage.list_instances()

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

    # ============ Sync Methods (for admin API) ============

    def list_definitions(self) -> List[Dict[str, Any]]:
        """List all workflow definitions (sync version)."""
        definitions = self.storage.list_definitions()
        result = []
        for d in definitions:
            result.append({
                "id": d.workflow_id,
                "name": d.name,
                "description": f"Workflow for {', '.join(d.content_types)}",
                "content_types": d.content_types,
                "states": [s.to_dict() for s in d.states],
                "transitions": [t.to_dict() for t in d.transitions],
                "is_default": d.is_default,
                "created_at": d.created_at.isoformat() if hasattr(d, 'created_at') and d.created_at else datetime.utcnow().isoformat()
            })
        return result

    def list_instances(self) -> List[Dict[str, Any]]:
        """List all workflow instances (sync version)."""
        instances = self.storage.list_instances()
        result = []
        for inst in instances:
            # Get content title if available
            content_title = "Untitled"
            if self.db:
                try:
                    from ..database.kosdb import KosDB
                    if isinstance(self.db, KosDB):
                        content_result = self.db.query(f"SELECT title FROM content WHERE id='{inst.content_id}'")
                        if content_result.get('rows'):
                            content_title = content_result['rows'][0].get('title', 'Untitled')
                except Exception:
                    pass
            
            # Get available actions
            workflow = self.storage.get_definition(inst.workflow_id)
            available_actions = []
            if workflow:
                for transition in workflow.transitions:
                    if transition.from_state == inst.current_state:
                        available_actions.append({
                            "action": transition.to_state,
                            "label": transition.name,
                            "requires_comment": transition.requires_comment
                        })
            
            # Get reviewer info
            reviewer = None
            reviewer_id = None
            if inst.assigned_reviewers:
                reviewer_id = inst.assigned_reviewers[0]
                if self.db:
                    try:
                        from ..database.kosdb import KosDB
                        if isinstance(self.db, KosDB):
                            user_result = self.db.query(f"SELECT username FROM users WHERE id='{reviewer_id}'")
                            if user_result.get('rows'):
                                reviewer = user_result['rows'][0].get('username')
                    except Exception:
                        reviewer = reviewer_id
            
            result.append({
                "id": inst.instance_id,
                "workflow_id": inst.workflow_id,
                "content_id": inst.content_id,
                "content_type": inst.content_type,
                "content_title": content_title,
                "state": inst.current_state,
                "reviewer": reviewer,
                "reviewer_id": reviewer_id,
                "assigned_reviewers": inst.assigned_reviewers,
                "available_actions": available_actions,
                "history": inst.history,
                "scheduled_publish": inst.scheduled_publish.isoformat() if inst.scheduled_publish else None,
                "updated_at": inst.created_at.isoformat() if inst.created_at else datetime.utcnow().isoformat(),
                "created_at": inst.created_at.isoformat() if inst.created_at else datetime.utcnow().isoformat()
            })
        return result

    def get_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow instance by ID (sync version)."""
        inst = self.storage.get_instance(instance_id)
        if not inst:
            return None
        
        # Get content title
        content_title = "Untitled"
        if self.db:
            try:
                from ..database.kosdb import KosDB
                if isinstance(self.db, KosDB):
                    content_result = self.db.query(f"SELECT title FROM content WHERE id='{inst.content_id}'")
                    if content_result.get('rows'):
                        content_title = content_result['rows'][0].get('title', 'Untitled')
            except Exception:
                pass
        
        # Get available actions
        workflow = self.storage.get_definition(inst.workflow_id)
        available_actions = []
        if workflow:
            for transition in workflow.transitions:
                if transition.from_state == inst.current_state:
                    available_actions.append({
                        "action": transition.to_state,
                        "label": transition.name,
                        "requires_comment": transition.requires_comment
                    })
        
        return {
            "id": inst.instance_id,
            "workflow_id": inst.workflow_id,
            "content_id": inst.content_id,
            "content_type": inst.content_type,
            "content_title": content_title,
            "state": inst.current_state,
            "assigned_reviewers": inst.assigned_reviewers,
            "available_actions": available_actions,
            "history": inst.history,
            "scheduled_publish": inst.scheduled_publish.isoformat() if inst.scheduled_publish else None,
            "updated_at": inst.created_at.isoformat() if inst.created_at else datetime.utcnow().isoformat()
        }

    def transition(self, instance_id: str, action: str, user_id: str = None, 
                   comment: str = None) -> Dict[str, Any]:
        """Transition workflow instance (sync version)."""
        instance = self.storage.get_instance(instance_id)
        if not instance:
            raise ValueError(f"Instance not found: {instance_id}")
        
        workflow = self.storage.get_definition(instance.workflow_id)
        if not workflow:
            raise ValueError(f"Workflow definition not found: {instance.workflow_id}")
        
        # Validate transition
        transition = workflow.get_transition(instance.current_state, action)
        if not transition:
            raise ValueError(f"Invalid transition: {instance.current_state} -> {action}")
        
        if transition.requires_comment and not comment:
            raise ValueError("Comment required for this transition")
        
        from_state = instance.current_state
        instance.current_state = action
        instance.add_history_entry(from_state, action, user_id, None, comment)
        
        self.storage.save_instance(instance)
        
        return {
            "id": instance_id,
            "from_state": from_state,
            "to_state": action,
            "message": f"Transitioned from {from_state} to {action}"
        }

    def assign(self, instance_id: str, reviewer_id: str) -> Dict[str, Any]:
        """Assign reviewer to workflow instance (sync version)."""
        instance = self.storage.get_instance(instance_id)
        if not instance:
            raise ValueError(f"Instance not found: {instance_id}")
        
        if reviewer_id not in instance.assigned_reviewers:
            instance.assigned_reviewers.append(reviewer_id)
        
        self.storage.save_instance(instance)
        
        return {
            "id": instance_id,
            "assigned": True,
            "reviewer_id": reviewer_id
        }

    def create_instance(self, content_id: str, content_type: str, 
                        workflow_id: str = None) -> Dict[str, Any]:
        """Create new workflow instance (sync version)."""
        if workflow_id:
            workflow = self.storage.get_definition(workflow_id)
        else:
            workflows = self.storage.list_definitions()
            workflow = None
            for wf in workflows:
                if wf.is_default:
                    workflow = wf
                    break
            if not workflow and workflows:
                workflow = workflows[0]
        
        if not workflow:
            raise ValueError("No workflow definition found")
        
        initial_state = workflow.get_initial_state()
        if not initial_state:
            raise ValueError("No initial state defined")
        
        instance = WorkflowInstance(
            instance_id=str(uuid.uuid4()),
            workflow_id=workflow.workflow_id,
            content_id=content_id,
            content_type=content_type,
            current_state=initial_state.state_id
        )
        
        instance.add_history_entry(None, initial_state.state_id, None, None, "Workflow started")
        self.storage.save_instance(instance)
        
        return {
            "id": instance.instance_id,
            "workflow_id": workflow.workflow_id,
            "content_id": content_id,
            "content_type": content_type,
            "state": initial_state.state_id,
            "message": "Workflow instance created"
        }

    def delete_instance(self, instance_id: str) -> bool:
        """Delete workflow instance (sync version)."""
        self.storage.delete_instance(instance_id)
        return True


class _FileStorage:
    """Simple file-based workflow storage."""

    def __init__(self, filepath):
        self.filepath = filepath
        self._definitions = {}
        self._instances = {}
        self._load()
        
        # Create default workflow if none exists
        if not self._definitions:
            self._create_default()

    def _create_default(self):
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

        default = WorkflowDefinition(
            workflow_id="default-editorial",
            name="Default Editorial Workflow",
            content_types=["post", "page"],
            states=states,
            transitions=transitions,
            is_default=True
        )
        
        self._definitions[default.workflow_id] = default
        self._persist()

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

    def save_definition(self, definition):
        self._definitions[definition.workflow_id] = definition
        self._persist()

    def get_definition(self, workflow_id):
        return self._definitions.get(workflow_id)

    def list_definitions(self):
        return list(self._definitions.values())

    def save_instance(self, instance):
        self._instances[instance.instance_id] = instance
        self._persist()

    def get_instance(self, instance_id):
        return self._instances.get(instance_id)

    def list_instances(self):
        return list(self._instances.values())

    def delete_instance(self, instance_id):
        if instance_id in self._instances:
            del self._instances[instance_id]
            self._persist()

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
