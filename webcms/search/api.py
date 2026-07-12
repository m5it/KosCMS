"""
Search API endpoints.
"""

from webcms.core.request import Request
from webcms.core.response import Response
from .client import ElasticsearchClient
from .indexer import SearchIndexer
from .searcher import Searcher
from .analytics import SearchAnalytics


class SearchAPI:
    """Search API."""

    def __init__(self, es_client=None, analytics=None):
        self.es = es_client or ElasticsearchClient()
        self.indexer = SearchIndexer(self.es)
        self.searcher = Searcher(self.es)
        self.analytics = analytics or SearchAnalytics()

    async def search(self, request: Request):
        """Search endpoint."""
        query = request.get_param("q", "")
        if not query:
            return Response.error("q parameter required", 400)

        content_types = request.get_param("types", "post,page").split(",")
        page = int(request.get_param("page", "1"))
        per_page = min(int(request.get_param("per_page", "20")), 100)
        fuzzy = request.get_param("fuzzy", "true").lower() == "true"

        filters = {}
        if request.get_param("status"):
            filters["status"] = request.get_param("status")
        if request.get_param("author_id"):
            filters["author_id"] = request.get_param("author_id")
        if request.get_param("tags"):
            filters["tags"] = request.get_param("tags").split(",")
        if request.get_param("date_from"):
            filters["date_from"] = request.get_param("date_from")
        if request.get_param("date_to"):
            filters["date_to"] = request.get_param("date_to")

        try:
            results = self.searcher.search(
                query_text=query,
                content_types=content_types,
                filters=filters,
                page=page,
                per_page=per_page,
                fuzzy=fuzzy
            )
            self.analytics.record_query(query, results["total"], filters)
            return Response.json(results)
        except Exception as e:
            return Response.error(str(e), 500)

    async def suggest(self, request: Request):
        """Search suggestions endpoint."""
        query = request.get_param("q", "")
        if not query:
            return Response.json({"suggestions": []})

        try:
            es_suggestions = self.searcher.suggest(query)
            analytics_suggestions = self.analytics.get_suggestions(query)
            combined = list(dict.fromkeys(es_suggestions + [s["query"] for s in analytics_suggestions]))
            return Response.json({"suggestions": combined[:10]})
        except Exception as e:
            return Response.error(str(e), 500)

    async def analytics(self, request: Request):
        """Search analytics endpoint."""
        return Response.json(self.analytics.get_stats())

    async def index_document(self, request: Request, content_type: str):
        """Index document endpoint."""
        data = request.json or {}
        doc_id = data.get("id")
        if not doc_id:
            return Response.error("id required", 400)

        try:
            if not self.indexer.index_exists(content_type):
                self.indexer.create_index(content_type)
            result = self.indexer.index_document(content_type, doc_id, data)
            return Response.json({"indexed": True, "result": result})
        except Exception as e:
            return Response.error(str(e), 500)

    async def create_index(self, request: Request, content_type: str):
        """Create index endpoint."""
        try:
            result = self.indexer.create_index(content_type)
            return Response.json({"created": True, "result": result})
        except Exception as e:
            return Response.error(str(e), 500)

    async def delete_index(self, request: Request, content_type: str):
        """Delete index endpoint."""
        try:
            result = self.indexer.delete_index(content_type)
            return Response.json({"deleted": True, "result": result})
        except Exception as e:
            return Response.error(str(e), 500)


def register_search_api(app, search_api=None):
    """Register search API routes."""
    api = search_api or SearchAPI()

    @app.route("/api/v1/search", methods=["GET"])
    def search(request):
        return api.search(request)

    @app.route("/api/v1/search/suggest", methods=["GET"])
    def suggest(request):
        return api.suggest(request)

    @app.route("/api/v1/search/analytics", methods=["GET"])
    def analytics(request):
        return api.analytics(request)

    @app.route("/api/v1/search/index/<content_type>", methods=["POST"])
    def index_document(request, content_type):
        return api.index_document(request, content_type)

    @app.route("/api/v1/search/index/<content_type>", methods=["PUT"])
    def create_index(request, content_type):
        return api.create_index(request, content_type)

    @app.route("/api/v1/search/index/<content_type>", methods=["DELETE"])
    def delete_index(request, content_type):
        return api.delete_index(request, content_type)
