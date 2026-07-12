#!/usr/bin/env python3
"""Integration tests for GraphQL API."""

import pytest
from webcms.graphql import schema


@pytest.mark.asyncio
async def test_graphql_hello():
    result = schema.execute('{ hello(name: "WebCMS") }')
    assert result.data == {"hello": "Hello, WebCMS!"}


@pytest.mark.asyncio
async def test_graphql_posts_query():
    result = schema.execute('{ posts { id title slug status } }')
    assert "posts" in result.data
    assert len(result.data["posts"]) > 0


@pytest.mark.asyncio
async def test_graphql_create_post_mutation():
    result = schema.execute('''
        mutation {
            createPost(title: "Test", slug: "test", content: "Hello", authorId: "1") {
                post { id title }
            }
        }
    ''')
    assert result.data["createPost"]["post"]["title"] == "Test"
