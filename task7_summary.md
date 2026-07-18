# Task 7/10: Workflows - COMPLETED

## Changes Made

### 1. webcms/workflow/kosdb_storage.py (NEW)
- Created KosDB storage backend for workflows
- `KosDBWorkflowStorage` class with methods:
  - `save_definition()` - Persists workflow definitions to KosDB
  - `get_definition()` - Retrieves single definition
  - `list_definitions()` - Lists all workflow definitions
  - `save_instance()` - Persists workflow instances with content titles
  - `get_instance()` - Retrieves single instance
  - `list_instances()` - Lists all instances
  - `delete_instance()` - Removes instance
- Auto-creates `workflow_definitions` and `workflow_instances` tables
- Serializes states/transitions as JSON
- Tracks available actions and reviewer assignments

### 2. webcms/workflow/manager.py (UPDATED)
- Added `db` parameter to constructor
- `_default_storage()` now returns KosDB storage if db provided
- `_ensure_default_workflow()` ensures default exists on init
- Added sync methods for admin API:
  - `list_definitions()` - Returns dict format for API
  - `list_instances()` - Returns dict format with content titles
  - `get_instance()` - Returns single instance as dict
  - `transition()` - Sync workflow transition with validation
  - `assign()` - Sync reviewer assignment
  - `create_instance()` - Sync instance creation
  - `delete_instance()` - Sync instance deletion
- Original async methods preserved for async code

### 3. webcms/admin/admin_api.py (UPDATED)
- `list_workflow_instances()` - Uses `WM(db=self.db)` 
- `list_workflow_definitions()` - Uses `WM(db=self.db)`
- `workflow_transition()` - Now passes user_id and comment, returns structured response
- `workflow_assign()` - Returns structured response with success flag

## API Endpoints

- `GET /api/v1/admin/workflows/instances` - Returns workflow instances
- `GET /api/v1/admin/workflows/definitions` - Returns workflow definitions
- `POST /api/v1/admin/workflows/{id}/transition` - Transitions workflow state
- `POST /api/v1/admin/workflows/{id}/assign` - Assigns reviewer

## Response Formats

### Workflow Definitions
```json
{
  "definitions": [
    {
      "id": "default-editorial",
      "name": "Default Editorial Workflow",
      "description": "Workflow for post, page",
      "states": [...],
      "transitions": [...],
      "is_default": true
    }
  ]
}
```

### Workflow Instances
```json
{
  "instances": [
    {
      "id": "uuid",
      "workflow_id": "default-editorial",
      "content_id": "post-123",
      "content_type": "post",
      "content_title": "My Post",
      "state": "draft",
      "reviewer": "username",
      "reviewer_id": "user-uuid",
      "assigned_reviewers": ["user-uuid"],
      "available_actions": [
        {"action": "review", "label": "Submit for Review", "requires_comment": false}
      ],
      "history": [...],
      "updated_at": "2025-01-22T..."
    }
  ]
}
```

### Transition Response
```json
{
  "success": true,
  "id": "instance-uuid",
  "from_state": "draft",
  "to_state": "review",
  "message": "Transitioned from draft to review"
}
```

### Assign Response
```json
{
  "success": true,
  "id": "instance-uuid",
  "assigned": true,
  "reviewer_id": "user-uuid"
}
```

## KosDB Tables

### workflow_definitions
- workflow_id (PRIMARY KEY)
- name, description
- content_types (JSON)
- states (JSON)
- transitions (JSON)
- is_default
- created_at

### workflow_instances
- instance_id (PRIMARY KEY)
- workflow_id, content_id, content_type
- content_title
- current_state
- assigned_reviewers (JSON)
- scheduled_publish
- history (JSON)
- available_actions (JSON)
- reviewer_id, reviewer_name
- updated_at, created_at

## WorkflowManager UI Compatibility

The React WorkflowManager expects:
- `data.definitions` with workflow templates ✓
- `data.instances` with current workflows ✓
- `available_actions` for state transitions ✓
- `reviewer` assignment capability ✓
- Transition endpoints returning structured data ✓

All requirements met.
