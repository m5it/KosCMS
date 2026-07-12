"""
GraphQL types for WebCMS models
"""

import graphene
from graphene import ObjectType, String, Int, ID, List, Boolean, DateTime, Field


class UserType(ObjectType):
    """GraphQL type for users."""
    id = ID()
    username = String()
    email = String()
    display_name = String()
    is_active = Boolean()
    created_at = DateTime()


class CategoryType(ObjectType):
    """GraphQL type for categories."""
    id = ID()
    name = String()
    slug = String()
    description = String()


class TagType(ObjectType):
    """GraphQL type for tags."""
    id = ID()
    name = String()
    slug = String()


class AuthorType(ObjectType):
    """GraphQL type for authors."""
    id = ID()
    username = String()
    display_name = String()


class PostType(ObjectType):
    """GraphQL type for posts."""
    id = ID()
    title = String()
    slug = String()
    content = String()
    excerpt = String()
    status = String()
    published_at = DateTime()
    author = Field(AuthorType)
    categories = List(CategoryType)
    tags = List(TagType)
    is_featured = Boolean()
    created_at = DateTime()
    updated_at = DateTime()


class PageType(ObjectType):
    """GraphQL type for pages."""
    id = ID()
    title = String()
    slug = String()
    content = String()
    status = String()
    published_at = DateTime()
    created_at = DateTime()
    updated_at = DateTime()


class MediaType(ObjectType):
    """GraphQL type for media."""
    id = ID()
    filename = String()
    file_url = String()
    mime_type = String()
    width = Int()
    height = Int()
    created_at = DateTime()


class SearchResultType(ObjectType):
    """GraphQL type for search results."""
    id = ID()
    title = String()
    content_type = String()
    excerpt = String()
    score = graphene.Float()


class VersionType(ObjectType):
    """GraphQL type for content versions."""
    version_id = ID()
    content_id = ID()
    content_type = String()
    version_number = Int()
    user_id = ID()
    username = String()
    comment = String()
    created_at = DateTime()


class WorkflowInstanceType(ObjectType):
    """GraphQL type for workflow instances."""
    instance_id = ID()
    workflow_id = ID()
    content_id = ID()
    content_type = String()
    current_state = String()
    assigned_reviewers = List(String)
    scheduled_publish = DateTime()
    created_at = DateTime()
