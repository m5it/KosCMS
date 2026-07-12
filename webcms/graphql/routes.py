"""
Route registration for GraphQL endpoints.
"""

from .views import GraphQLView, GraphiQLView


def register_graphql_routes(app):
    """Register GraphQL routes on app."""
    graphql_view = GraphQLView()
    graphiql_view = GraphiQLView()

    @app.route("/graphql", methods=["GET", "POST"])
    def graphql_handler(request):
        return graphql_view.handle(request)

    @app.route("/graphiql", methods=["GET"])
    def graphiql_handler(request):
        return graphiql_view.handle(request)
