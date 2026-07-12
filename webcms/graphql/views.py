"""
GraphQL views and GraphiQL endpoint for WebCMS
"""

import json
from webcms.core.request import Request
from webcms.core.response import Response
from .schema import schema
from .middleware import PermissionMiddleware, ComplexityMiddleware


class GraphQLView:
    """GraphQL HTTP endpoint."""

    def __init__(self, max_complexity=1000):
        self.schema = schema
        self.middleware = [
            PermissionMiddleware(),
            ComplexityMiddleware(max_complexity=max_complexity)
        ]

    async def handle(self, request: Request):
        """Handle GraphQL request."""
        try:
            data = request.json or {}
            query = data.get("query", "")
            variables = data.get("variables", {})
            operation_name = data.get("operationName")

            result = self.schema.execute(
                query,
                variables=variables,
                operation_name=operation_name,
                middleware=self.middleware,
                context=request
            )

            response = {
                "data": result.data if result.data else None
            }
            if result.errors:
                response["errors"] = [
                    {"message": str(e)} for e in result.errors
                ]

            return Response.json(response)
        except Exception as e:
            return Response.error(str(e), 500)


GRAPHIQL_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>WebCMS GraphiQL</title>
    <link rel="stylesheet" href="https://unpkg.com/graphiql/graphiql.min.css" />
</head>
<body style="margin:0;">
    <div id="graphiql" style="height:100vh;"></div>
    <script crossorigin src="https://unpkg.com/react/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom/umd/react-dom.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/graphiql/graphiql.min.js"></script>
    <script>
        const fetcher = GraphiQL.createFetcher({
            url: '/graphql',
            headers: { 'Content-Type': 'application/json' }
        });
        ReactDOM.render(
            React.createElement(GraphiQL, { fetcher: fetcher }),
            document.getElementById('graphiql')
        );
    </script>
</body>
</html>"""


class GraphiQLView:
    """GraphiQL explorer endpoint."""

    async def handle(self, request: Request):
        return Response.html(GRAPHIQL_HTML)
