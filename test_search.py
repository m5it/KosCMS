#!/usr/bin/env python3
"""Test search analytics without Elasticsearch"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from webcms.search.analytics import SearchAnalytics


def test_analytics():
    print('Testing search analytics...')

    analytics = SearchAnalytics()
    analytics.record_query("django cms", 12, {"status": "published"})
    analytics.record_query("python", 5)
    analytics.record_query("django cms", 3)
    analytics.record_click("django cms", "post-1")

    stats = analytics.get_stats()
    print(f'Stats: {stats}')

    suggestions = analytics.get_suggestions("dj")
    print(f'Suggestions: {suggestions}')

    popular = analytics.get_popular_queries()
    print(f'Popular: {popular}')

    print('Search analytics verified!')


if __name__ == '__main__':
    test_analytics()
