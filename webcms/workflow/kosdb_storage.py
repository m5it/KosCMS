"""
KosDB Storage Backend for Workflow Manager
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from .models import WorkflowState, WorkflowTransition, WorkflowDefinition, WorkflowInstance


class KosDBWorkflowStorage:
    """KosDB-backed storage for workflows."""

    def __init__(self, db):
        self.db = db
        self._ensure_tables()

    def _is_kosdb(self) -> bool:
        """Check if database is KosDB."""
        if self.db is None:
            return False
        # Check for KosDB by looking for required methods
        has_methods = all(
            hasattr(self.db, method) 
            for method in ['execute', 'query', 'list_tables']
        )
        return has_methods

    def _ensure_tables(self):
        """Ensure workflow tables exist."""
        if not self.db or not self._is_kosdb():
            return

        try:
            tables = self.db.list_tables()
        except Exception:
            tables = []

        # Workflow definitions table
        if 'workflow_definitions' not in tables:
            try:
                self.db.execute("""
                    CREATE TABLE workflow_definitions (
                        workflow_id TEXT PRIMARY KEY,
                        name TEXT,
                        description TEXT,
                        content_types TEXT,
                        states TEXT,
                        transitions TEXT,
                        is_default TEXT,
                        created_at TEXT
                    )
                """)
            except Exception:
                pass

        # Workflow instances table
        if 'workflow_instances' not in tables:
            try:
                self.db.execute("""
                    CREATE TABLE workflow_instances (
                        instance_id TEXT PRIMARY KEY,
                        workflow_id TEXT,
                        content_id TEXT,
                        content_type TEXT,
                        content_title TEXT,
                        current_state TEXT,
                        assigned_reviewers TEXT,
                        scheduled_publish TEXT,
                        history TEXT,
                        available_actions TEXT,
                        reviewer_id TEXT,
                        reviewer_name TEXT,
                        updated_at TEXT,
                        created_at TEXT
                    )
                """)
            except Exception:
                pass

    def _serialize_states(self, states: List[WorkflowState]) -> str:
        """Serialize states to JSON."""
        return json.dumps([s.to_dict() for s in states])

    def _deserialize_states(self, data: str) -> List[WorkflowState]:
        """Deserialize states from JSON."""
        if not data:
            return []
        states_data = json.loads(data)
        return [WorkflowState(**s) for s in states_data]

    def _serialize_transitions(self, transitions: List[WorkflowTransition]) -> str:
        """Serialize transitions to JSON."""
        return json.dumps([t.to_dict() for t in transitions])

    def _deserialize_transitions(self, data: str) -> List[WorkflowTransition]:
        """Deserialize transitions from JSON."""
        if not data:
            return []
        trans_data = json.loads(data)
        return [WorkflowTransition(**t) for t in trans_data]

    def save_definition(self, definition: WorkflowDefinition):
        """Save workflow definition."""
        if not self.db or not self._is_kosdb():
            return

        now = datetime.utcnow().isoformat()
        try:
            # Check if exists
            result = self.db.query(f"SELECT workflow_id FROM workflow_definitions WHERE workflow_id='{definition.workflow_id}'")
            
            content_types = json.dumps(definition.content_types)
            states = self._serialize_states(definition.states)
            transitions = self._serialize_transitions(definition.transitions)
            
            if result.get('rows'):
                # Update
                self.db.execute(f"""
                    UPDATE workflow_definitions SET
                        name='{definition.name}',
                        content_types='{content_types}',
                        states='{states}',
                        transitions='{transitions}',
                        is_default='{1 if definition.is_default else 0}',
                        created_at='{now}'
                    WHERE workflow_id='{definition.workflow_id}'
                """)
            else:
                # Insert
                self.db.execute(f"""
                    INSERT INTO workflow_definitions 
                    (workflow_id, name, content_types, states, transitions, is_default, created_at)
                    VALUES (
                        '{definition.workflow_id}',
                        '{definition.name}',
                        '{content_types}',
                        '{states}',
                        '{transitions}',
                        '{1 if definition.is_default else 0}',
                        '{now}'
                    )
                """)
        except Exception:
            pass

    def get_definition(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get workflow definition by ID."""
        if not self.db or not self._is_kosdb():
            return None

        try:
            result = self.db.query(f"SELECT * FROM workflow_definitions WHERE workflow_id='{workflow_id}'")
            if result.get('rows'):
                row = result['rows'][0]
                return WorkflowDefinition(
                    workflow_id=row['workflow_id'],
                    name=row['name'],
                    content_types=json.loads(row['content_types']),
                    states=self._deserialize_states(row['states']),
                    transitions=self._deserialize_transitions(row['transitions']),
                    is_default=row['is_default'] == '1' or row['is_default'] == 1
                )
        except Exception:
            pass
        return None

    def list_definitions(self) -> List[WorkflowDefinition]:
        """List all workflow definitions."""
        if not self.db or not self._is_kosdb():
            return []

        definitions = []
        try:
            result = self.db.query("SELECT * FROM workflow_definitions")
            for row in result.get('rows', []):
                try:
                    definitions.append(WorkflowDefinition(
                        workflow_id=row['workflow_id'],
                        name=row['name'],
                        content_types=json.loads(row.get('content_types', '[]')),
                        states=self._deserialize_states(row.get('states', '[]')),
                        transitions=self._deserialize_transitions(row.get('transitions', '[]')),
                        is_default=row.get('is_default') == '1' or row.get('is_default') == 1
                    ))
                except Exception:
                    continue
        except Exception:
            pass
        return definitions

    def save_instance(self, instance: WorkflowInstance):
        """Save workflow instance."""
        if not self.db or not self._is_kosdb():
            return

        now = datetime.utcnow().isoformat()
        try:
            # Check if exists
            result = self.db.query(f"SELECT instance_id FROM workflow_instances WHERE instance_id='{instance.instance_id}'")
            
            history = json.dumps(instance.history) if instance.history else '[]'
            reviewers = json.dumps(instance.assigned_reviewers) if instance.assigned_reviewers else '[]'
            scheduled = instance.scheduled_publish.isoformat() if instance.scheduled_publish else None
            
            # Get content title from content_id if available
            content_title = "Untitled"
            try:
                content_result = self.db.query(f"SELECT title FROM content WHERE id='{instance.content_id}'")
                if content_result.get('rows'):
                    content_title = content_result['rows'][0].get('title', 'Untitled')
            except Exception:
                pass
            
            # Get available actions based on current state
            available_actions = self._get_available_actions(instance)
            
            # Get reviewer info
            reviewer_id = instance.assigned_reviewers[0] if instance.assigned_reviewers else None
            reviewer_name = None
            if reviewer_id:
                try:
                    user_result = self.db.query(f"SELECT username FROM users WHERE id='{reviewer_id}'")
                    if user_result.get('rows'):
                        reviewer_name = user_result['rows'][0].get('username')
                except Exception:
                    pass

            if result.get('rows'):
                # Update
                self.db.execute(f"""
                    UPDATE workflow_instances SET
                        workflow_id='{instance.workflow_id}',
                        content_id='{instance.content_id}',
                        content_type='{instance.content_type}',
                        content_title='{content_title}',
                        current_state='{instance.current_state}',
                        assigned_reviewers='{reviewers}',
                        scheduled_publish='{scheduled or ''}',
                        history='{history}',
                        available_actions='{json.dumps(available_actions)}',
                        reviewer_id='{reviewer_id or ''}',
                        reviewer_name='{reviewer_name or ''}',
                        updated_at='{now}'
                    WHERE instance_id='{instance.instance_id}'
                """)
            else:
                # Insert
                created = instance.created_at.isoformat() if instance.created_at else now
                self.db.execute(f"""
                    INSERT INTO workflow_instances 
                    (instance_id, workflow_id, content_id, content_type, content_title,
                     current_state, assigned_reviewers, scheduled_publish, history,
                     available_actions, reviewer_id, reviewer_name, updated_at, created_at)
                    VALUES (
                        '{instance.instance_id}',
                        '{instance.workflow_id}',
                        '{instance.content_id}',
                        '{instance.content_type}',
                        '{content_title}',
                        '{instance.current_state}',
                        '{reviewers}',
                        '{scheduled or ''}',
                        '{history}',
                        '{json.dumps(available_actions)}',
                        '{reviewer_id or ''}',
                        '{reviewer_name or ''}',
                        '{now}',
                        '{created}'
                    )
                """)
        except Exception:
            pass

    def _get_available_actions(self, instance: WorkflowInstance) -> List[str]:
        """Get available actions for instance based on current state."""
        # Get workflow definition
        workflow = self.get_definition(instance.workflow_id)
        if not workflow:
            return []
        
        actions = []
        for transition in workflow.transitions:
            if transition.from_state == instance.current_state:
                actions.append(transition.to_state)
        return actions

    def get_instance(self, instance_id: str) -> Optional[WorkflowInstance]:
        """Get workflow instance by ID."""
        if not self.db or not self._is_kosdb():
            return None

        try:
            result = self.db.query(f"SELECT * FROM workflow_instances WHERE instance_id='{instance_id}'")
            if result.get('rows'):
                row = result['rows'][0]
                scheduled = None
                if row.get('scheduled_publish'):
                    try:
                        scheduled = datetime.fromisoformat(row['scheduled_publish'])
                    except Exception:
                        pass
                
                created = datetime.utcnow()
                if row.get('created_at'):
                    try:
                        created = datetime.fromisoformat(row['created_at'])
                    except Exception:
                        pass

                return WorkflowInstance(
                    instance_id=row['instance_id'],
                    workflow_id=row['workflow_id'],
                    content_id=row['content_id'],
                    content_type=row['content_type'],
                    current_state=row['current_state'],
                    assigned_reviewers=json.loads(row['assigned_reviewers']) if row.get('assigned_reviewers') else [],
                    scheduled_publish=scheduled,
                    history=json.loads(row['history']) if row.get('history') else [],
                    created_at=created
                )
        except Exception:
            pass
        return None

    def list_instances(self) -> List[WorkflowInstance]:
        """List all workflow instances."""
        if not self.db or not self._is_kosdb():
            return []

        instances = []
        try:
            result = self.db.query("SELECT * FROM workflow_instances")
            for row in result.get('rows', []):
                try:
                    scheduled = None
                    if row.get('scheduled_publish'):
                        try:
                            scheduled = datetime.fromisoformat(row['scheduled_publish'])
                        except Exception:
                            pass
                    
                    created = datetime.utcnow()
                    if row.get('created_at'):
                        try:
                            created = datetime.fromisoformat(row['created_at'])
                        except Exception:
                            pass

                    instances.append(WorkflowInstance(
                        instance_id=row['instance_id'],
                        workflow_id=row['workflow_id'],
                        content_id=row['content_id'],
                        content_type=row['content_type'],
                        current_state=row['current_state'],
                        assigned_reviewers=json.loads(row['assigned_reviewers']) if row.get('assigned_reviewers') else [],
                        scheduled_publish=scheduled,
                        history=json.loads(row['history']) if row.get('history') else [],
                        created_at=created
                    ))
                except Exception:
                    continue
        except Exception:
            pass
        return instances

    def delete_instance(self, instance_id: str):
        """Delete workflow instance."""
        if not self.db or not self._is_kosdb():
            return

        try:
            self.db.execute(f"DELETE FROM workflow_instances WHERE instance_id='{instance_id}'")
        except Exception:
            pass
