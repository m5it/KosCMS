"""
Search API Endpoint

Search endpoint for content discovery.
"""

from webcms.core.request import Request
from webcms.core.response import Response
from webcms.content.search_service import SearchService


class SearchEndpoint:
    """Search API endpoint."""
    
    methods = ["GET"]
    
    def __init__(self, db=None, auth=None):
        self.db = db
        self.auth = auth
    
    def dispatch(self, request: Request, **kwargs) -> Response:
        """Handle request."""
        if request.method != "GET":
            return Response.error("Method not allowed", 405)
        return self.get(request, **kwargs)
    
    def get(self, request: Request) -> Response:
        """Search content."""
        query = request.get_param("q", "")
        if not query:
            return Response.json({
                "query": "",
                "total": 0,
                "results": []
            })
        
        content_type = request.get_param("type", None)
        limit = min(int(request.get_param("limit", 20)), 100)
        
        service = SearchService(self.db)
        results = service.search(query, content_type, limit)
        
        # Format response
        formatted = []
        for item in results["results"]:
            search_data = item["search"]
            content = item["content"]
            
            formatted.append({
                "id": content.id,
                "type": search_data.content_type,
                "title": search_data.title,
                "excerpt": search_data.excerpt,
                "rank": search_data.rank,
                "url": f"/{search_data.content_type}s/{content.slug}" if hasattr(content, 'slug') else None
            })
        
        return Response.json({
            "query": query,
            "total": results["total"],
            "results": formatted
        })


def register_search_api(app, db, auth):
    """Register search endpoint."""
    endpoint = SearchEndpoint(db=db, auth=auth)
    app.router.add("/api/v1/search", endpoint.dispatch, ["GET"])
    return app
