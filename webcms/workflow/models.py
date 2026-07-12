"""
Workflow models for WebCMS
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any


class WorkflowState:
    """State in a workflow."""

    def __init__(self, state_id, name, label, is_initial=False,
                 is_final=False, requires_approval=False, color="#6c757d"):
        self.state_id = state_id
        self.name = name
        self.label = label
        self.is_initial = is_initial
        self.is_final = is_final
        self.requires_approval = requires_approval
        self.color = color

    def to_dict(self):
        return {
            "state_id": self.state_id,
            "name": self.name,
            "label": self.label,
            "is_initial": self.is_initial,
            "is_final": self.is_final,
            "requires_approval": self.requires_approval,
            "color": self.color
        }


class WorkflowTransition:
    """Transition between workflow states."""

    def __init__(self, transition_id, from_state, to_state, name,
                 required_role=None, requires_comment=False):
        self.transition_id = transition_id
        self.from_state = from_state
        self.to_state = to_state
        self.name = name
        self.required_role = required_role
        self.requires_comment = requires_comment

    def to_dict(self):
        return {
            "transition_id": self.transition_id,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "name": self.name,
            "required_role": self.required_role,
            "requires_comment": self.requires_comment
        }


class WorkflowDefinition:
    """Workflow template definition."""

    def __init__(self, workflow_id, name, content_types=None,
                 states=None, transitions=None, is_default=False):
        self.workflow_id = workflow_id or str(uuid.uuid4())
        self.name = name
        self.content_types = content_types or ["post", "page"]
        self.states = states or []
        self.transitions = transitions or []
        self.is_default = is_default
        self.created_at = datetime.utcnow()

    def to_dict(self):
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "content_types": self.content_types,
            "states": [s.to_dict() for s in self.states],
            "transitions": [t.to_dict() for t in self.transitions],
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat()
        }

    def get_initial_state(self):
        for state in self.states:
            if state.is_initial:
                return state
        return self.states[0] if self.states else None

    def get_transition(self, from_state, to_state):
        for t in self.transitions:
            if t.from_state == from_state and t.to_state == to_state:
                return t
        return None


class WorkflowInstance:
    """Active workflow on a content item."""

    def __init__(self, instance_id, workflow_id, content_id, content_type,
                 current_state, assigned_reviewers=None, scheduled_publish=None,
                 history=None, created_at=None):
        self.instance_id = instance_id or str(uuid.uuid4())
        self.workflow_id = workflow_id
        self.content_id = content_id
        self.content_type = content_type
        self.current_state = current_state
        self.assigned_reviewers = assigned_reviewers or []
        self.scheduled_publish = scheduled_publish
        self.history = history or []
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        return {
            "instance_id": self.instance_id,
            "workflow_id": self.workflow_id,
            "content_id": self.content_id,
            "content_type": self.content_type,
            "current_state": self.current_state,
            "assigned_reviewers": self.assigned_reviewers,
            "scheduled_publish": self.scheduled_publish.isoformat() if self.scheduled_publish else None,
            "history": self.history,
            "created_at": self.created_at.isoformat()
        }

    def add_history_entry(self, from_state, to_state, user_id, username, comment=None):
        entry = {
            "from_state": from_state,
            "to_state": to_state,
            "user_id": user_id,
            "username": username,
            "comment": comment,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.history.append(entry)
