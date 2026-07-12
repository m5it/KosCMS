"""
GraphQL schema for WebCMS
"""

import graphene
from graphene import ObjectType, String, Int, ID, List, Boolean, Field, Mutation
from .types import (
    UserType, PostType, PageType, MediaType,
    CategoryType, TagType, SearchResultType,
    WorkflowInstanceType, VersionType
)


class Query(ObjectType):
    """GraphQL queries."""
    hello = String(name=String(default_value="World"))

    # Content queries
    posts = List(PostType, status=String(), limit=Int(default_value=20), offset=Int(default_value=0))
    post = Field(PostType, id=ID(), slug=String())
    pages = List(PageType, status=String(), limit=Int(default_value=20), offset=Int(default_value=0))
    page = Field(PageType, id=ID(), slug=String())

    # User & media queries
    users = List(UserType, limit=Int(default_value=20), offset=Int(default_value=0))
    user = Field(UserType, id=ID(), username=String())
    media = List(MediaType, limit=Int(default_value=20), offset=Int(default_value=0))
    media_item = Field(MediaType, id=ID())

    # Taxonomy queries
    categories = List(CategoryType)
    tags = List(TagType)

    # Search
    search = List(SearchResultType, query=String(required=True), limit=Int(default_value=10))

    # Workflow
    workflows = List(WorkflowInstanceType, content_type=String(), state=String())
    workflow = Field(WorkflowInstanceType, instance_id=ID(required=True))

    # Versions
    versions = List(VersionType, content_id=ID(required=True), content_type=String(required=True))

    def resolve_hello(self, info, name):
        return f"Hello, {name}!"

    def resolve_posts(self, info, status=None, limit=20, offset=0):
        # Placeholder: real implementation queries content service
        return [
            PostType(
                id="1", title="Welcome Post", slug="welcome",
                content="Welcome to WebCMS", excerpt="Welcome...",
                status="published", is_featured=True
            )
        ]

    def resolve_post(self, info, id=None, slug=None):
        return PostType(id=id or "1", title="Welcome Post", slug=slug or "welcome")

    def resolve_pages(self, info, status=None, limit=20, offset=0):
        return [PageType(id="1", title="About", slug="about", status="published")]

    def resolve_page(self, info, id=None, slug=None):
        return PageType(id=id or "1", title="About", slug=slug or "about")

    def resolve_users(self, info, limit=20, offset=0):
        return [UserType(id="1", username="admin", email="admin@example.com")]

    def resolve_user(self, info, id=None, username=None):
        return UserType(id=id or "1", username=username or "admin")

    def resolve_media(self, info, limit=20, offset=0):
        return [MediaType(id="1", filename="logo.png", file_url="/media/logo.png", mime_type="image/png")]

    def resolve_media_item(self, info, id):
        return MediaType(id=id, filename="logo.png", file_url="/media/logo.png", mime_type="image/png")

    def resolve_categories(self, info):
        return [CategoryType(id="1", name="General", slug="general")]

    def resolve_tags(self, info):
        return [TagType(id="1", name="webcms", slug="webcms")]

    def resolve_search(self, info, query, limit=10):
        return [SearchResultType(id="1", title="Welcome", content_type="post", excerpt="Welcome", score=1.0)]

    def resolve_workflows(self, info, content_type=None, state=None):
        return []

    def resolve_workflow(self, info, instance_id):
        return None

    def resolve_versions(self, info, content_id, content_type):
        return []


class CreatePost(Mutation):
    """Create post mutation."""
    class Arguments:
        title = String(required=True)
        slug = String(required=True)
        content = String(required=True)
        excerpt = String()
        status = String(default_value="draft")
        author_id = ID(required=True)
        category_ids = List(ID)
        tag_ids = List(ID)

    post = Field(PostType)

    def mutate(self, info, title, slug, content, author_id, **kwargs):
        return CreatePost(
            post=PostType(
                id="new-post-id",
                title=title,
                slug=slug,
                content=content,
                status=kwargs.get("status", "draft")
            )
        )


class UpdatePost(Mutation):
    """Update post mutation."""
    class Arguments:
        id = ID(required=True)
        title = String()
        content = String()
        status = String()

    post = Field(PostType)

    def mutate(self, info, id, **kwargs):
        return UpdatePost(
            post=PostType(id=id, title=kwargs.get("title", "Updated Post"))
        )


class DeletePost(Mutation):
    """Delete post mutation."""
    class Arguments:
        id = ID(required=True)

    success = Boolean()

    def mutate(self, info, id):
        return DeletePost(success=True)


class CreatePage(Mutation):
    """Create page mutation."""
    class Arguments:
        title = String(required=True)
        slug = String(required=True)
        content = String(required=True)
        status = String(default_value="draft")

    page = Field(PageType)

    def mutate(self, info, title, slug, content, status="draft"):
        return CreatePage(page=PageType(id="new-page-id", title=title, slug=slug, status=status))


class UpdatePage(Mutation):
    """Update page mutation."""
    class Arguments:
        id = ID(required=True)
        title = String()
        content = String()
        status = String()

    page = Field(PageType)

    def mutate(self, info, id, **kwargs):
        return UpdatePage(page=PageType(id=id, title=kwargs.get("title", "Updated Page")))


class DeletePage(Mutation):
    """Delete page mutation."""
    class Arguments:
        id = ID(required=True)

    success = Boolean()

    def mutate(self, info, id):
        return DeletePage(success=True)


class Mutation(ObjectType):
    """GraphQL mutations."""
    create_post = CreatePost.Field()
    update_post = UpdatePost.Field()
    delete_post = DeletePost.Field()
    create_page = CreatePage.Field()
    update_page = UpdatePage.Field()
    delete_page = DeletePage.Field()


class Subscription(ObjectType):
    """GraphQL subscriptions."""
    post_created = Field(PostType)
    post_updated = Field(PostType)
    workflow_changed = Field(WorkflowInstanceType)

    def subscribe_post_created(self, info):
        return None

    def subscribe_post_updated(self, info):
        return None

    def subscribe_workflow_changed(self, info):
        return None


schema = graphene.Schema(query=Query, mutation=Mutation, subscription=Subscription)
