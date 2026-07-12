"""
Workflow API endpoints for WebCMS
"""

from datetime import datetime
from webcms.core.request import Request
from webcms.core.response import Response
from .manager import WorkflowManager


class WorkflowAPI:
    """Workflow API endpoints."""

    def __init__(self, workflow_manager=None):
        self.manager = workflow_manager or WorkflowManager()

    async def list_definitions(self, request: Request):
        """List workflow definitions."""
        try:
            definitions = await self.manager.list_workflow_definitions()
            return Response.json({
                "workflows": [wf.to_dict() for wf in definitions]
            })
        except Exception as e:
            return Response.error(str(e), 500)

    async def list_instances(self, request: Request):
        """List workflow instances."""
        try:
            instances = await self.manager.storage.list_instances()
            return Response.json({
                "instances": [inst.to_dict() for inst in instances]
            })
        except Exception as e:
            return Response.error(str(e), 500)

    async def start_workflow(self, request: Request, content_type: str, content_id: str):
        """Start workflow for content."""
        data = request.json or {}
        try:
            instance = await self.manager.start_workflow(
                content_id=content_id,
                content_type=content_type,
                workflow_id=data.get("workflow_id"),
                user_id=data.get("user_id"),
                username=data.get("username")
            )
            if not instance:
                return Response.error("Failed to start workflow", 400)
            return Response.json(instance.to_dict(), 201)
        except Exception as e:
            return Response.error(str(e), 500)

    async def transition(self, request: Request, instance_id: str):
        """Transition workflow instance."""
        data = request.json or {}
        try:
            instance, error = await self.manager.transition(
                instance_id=instance_id,
                to_state=data.get("to_state"),
                user_id=data.get("user_id"),
                username=data.get("username"),
                comment=data.get("comment"),
                user_roles=data.get("roles", [])
            )
            if error:
                return Response.error(error, 400)
            return Response.json(instance.to_dict())
        except Exception as e:
            return Response.error(str(e), 500)

    async def assign_reviewers(self, request: Request, instance_id: str):
        """Assign reviewers to workflow instance."""
        data = request.json or {}
        try:
            instance = await self.manager.assign_reviewers(
                instance_id=instance_id,
                reviewer_ids=data.get("reviewer_ids", [])
            )
            if not instance:
                return Response.not_found()
            return Response.json(instance.to_dict())
        except Exception as e:
            return Response.error(str(e), 500)

    async def schedule_publish(self, request: Request, instance_id: str):
        """Schedule content publishing."""
        data = request.json or {}
        try:
            publish_time_str = data.get("publish_time")
            if not publish_time_str:
                return Response.error("publish_time required", 400)

            publish_time = datetime.fromisoformat(publish_time_str)
            instance = await self.manager.schedule_publish(
                instance_id=instance_id,
                publish_time=publish_time
            )
            if not instance:
                return Response.not_found()
            return Response.json(instance.to_dict())
        except Exception as e:
            return Response.error(str(e), 500)

    async def get_calendar(self, request: Request):
        """Get content calendar."""
        try:
            start_str = request.get_param("start")
            end_str = request.get_param("end")
            content_type = request.get_param("type")

            if not start_str or not end_str:
                return Response.error("start and end required", 400)

            start = datetime.fromisoformat(start_str)
            end = datetime.fromisoformat(end_str)

            calendar = await self.manager.get_content_calendar(
                start_date=start,
                end_date=end,
                content_type=content_type
            )
            return Response.json({"calendar": calendar})
        except Exception as e:
            return Response.error(str(e), 500)


def register_workflow_api(app, workflow_manager=None):
    """Register workflow API routes."""
    api = WorkflowAPI(workflow_manager)

    @app.route("/api/v1/workflows", methods=["GET"])
    def list_definitions(request):
        return api.list_definitions(request)

    @app.route("/api/v1/workflow-instances", methods=["GET"])
    def list_instances(request):
        return api.list_instances(request)

    @app.route("/api/v1/<content_type>/<content_id>/workflow", methods=["POST"])
    def start_workflow(request, content_type, content_id):
        return api.start_workflow(request, content_type, content_id)

    @app.route("/api/v1/workflow-instances/<instance_id>/transition", methods=["POST"])
    def transition(request, instance_id):
        return api.transition(request, instance_id)

    @app.route("/api/v1/workflow-instances/<instance_id>/reviewers", methods=["POST"])
    def assign_reviewers(request, instance_id):
        return api.assign_reviewers(request, instance_id)

    @app.route("/api/v1/workflow-instances/<instance_id>/schedule", methods=["POST"])
    def schedule_publish(request, instance_id):
        return api.schedule_publish(request, instance_id)

    @app.route("/api/v1/workflow-calendar", methods=["GET"])
    def get_calendar(request):
        return api.get_calendar(request)
