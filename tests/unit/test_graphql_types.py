#!/usr/bin/env python3
"""Unit tests for GraphQL schema."""

from webcms.graphql import schema


def test_hello_query():
    result = schema.execute('{ hello }')
    assert result.data == {'hello': 'Hello, World!'}


def test_posts_query():
    result = schema.execute('{ posts { id title } }')
    assert result.data is not None
    assert 'posts' in result.data
