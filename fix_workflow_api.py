#!/usr/bin/env python3
"""Fix workflow API endpoints in admin_api.py"""

with open('webcms/admin/admin_api.py', 'r') as f:
    content = f.read()

# Fix workflow_transition to pass correct parameters
old_transition = '''    def workflow_transition(self, request: Request, instance_id: str) -> Response:
        from webcms.workflow.manager import WorkflowManager as WM
        data = request.json or {}
        try:
            manager = WM(self.db)
            manager.transition(instance_id, data.get("action"))
            return Response.json({"id": instance_id, "message": f"Transitioned to {data.get('action')}"})
        except Exception as e:
            return Response.json({"id": instance_id, "message": str(e)}, 400)'''

new_transition = '''    def workflow_transition(self, request: Request, instance_id: str) -> Response:
        from webcms.workflow.manager import WorkflowManager as WM
        data = request.json or {}
        try:
            manager = WM(db=self.db)
            # Get current user from request
            user_id = getattr(request, 'user_id', None)
            result = manager.transition(
                instance_id=instance_id,
                action=data.get("action"),
                user_id=user_id,
                comment=data.get("comment")
            )
            return Response.json({
                "success": True,
                "id": instance_id,
                "from_state": result.get("from_state"),
                "to_state": result.get("to_state"),
                "message": result.get("message")
            })
        except Exception as e:
            return Response.json({"success": False, "id": instance_id, "message": str(e)}, 400)'''

if old_transition in content:
    content = content.replace(old_transition, new_transition)
    print("Fixed workflow_transition")
else:
    print("Could not find workflow_transition")

# Fix workflow_assign to pass correct parameters
old_assign = '''    def workflow_assign(self, request: Request, instance_id: str) -> Response:
        from webcms.workflow.manager import WorkflowManager as WM
        data = request.json or {}
        try:
            manager = WM(self.db)
            manager.assign(instance_id, data.get("reviewer_id"))
            return Response.json({"id": instance_id, "assigned": True})
        except Exception as e:
            return Response.json({"id": instance_id, "assigned": False, "message": str(e)}, 400)'''

new_assign = '''    def workflow_assign(self, request: Request, instance_id: str) -> Response:
        from webcms.workflow.manager import WorkflowManager as WM
        data = request.json or {}
        try:
            manager = WM(db=self.db)
            result = manager.assign(instance_id, data.get("reviewer_id"))
            return Response.json({
                "success": True,
                "id": instance_id,
                "assigned": result.get("assigned"),
                "reviewer_id": result.get("reviewer_id")
            })
        except Exception as e:
            return Response.json({"success": False, "id": instance_id, "assigned": False, "message": str(e)}, 400)'''

if old_assign in content:
    content = content.replace(old_assign, new_assign)
    print("Fixed workflow_assign")
else:
    print("Could not find workflow_assign")

# Also fix list_workflow_instances and list_workflow_definitions to use db= parameter
content = content.replace('manager = WM(self.db)', 'manager = WM(db=self.db)')

with open('webcms/admin/admin_api.py', 'w') as f:
    f.write(content)

print("All workflow API fixes applied")
