#!/usr/bin/env python3
"""Test GraphQL schema"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from webcms.graphql import schema


def test_graphql():
    print('Testing GraphQL schema...')

    # Test simple query
    result = schema.execute('{ hello(name: "WebCMS") }')
    print(f'Query result: {result.data}')

    # Test posts query
    result = schema.execute('{ posts { id title slug status } }')
    print(f'Posts query: {result.data}')

    # Test mutation
    result = schema.execute('''
        mutation {
            createPost(title: "Test Post", slug: "test-post", content: "Hello", authorId: "1") {
                post { id title slug }
            }
        }
    ''')
    print(f'Mutation result: {result.data}')

    # Test complexity with deep query
    deep_query = '{ posts { author { username } categories { name } tags { name } } }'
    result = schema.execute(deep_query, middleware=[])
    print(f'Deep query: {result.data}')

    print('GraphQL schema verified!')


if __name__ == '__main__':
    test_graphql()
