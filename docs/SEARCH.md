
# Full-Text Search Documentation

WebCMS v1.1.0 introduces full-text search using SQLite FTS5.

## Overview

The search system automatically indexes content as it's created, updated, or deleted. No manual reindexing is required for normal operations.

## Quick Start

```python
from webcms.content.search_service import SearchService

service = SearchService(db)

# Search posts and pages
results = service.search("python tutorial")

# Filter by content type
results = service.search("django", content_type="post")

# Limit results
results = service.search("web development", limit=50)
```

## API Usage

### Search Endpoint

```
GET /api/v1/search?q=python&limit=20
```

Response:
```json
{
  "query": "python",
  "total": 15,
  "results": [
    {
      "search": {
        "content_id": "post:abc123",
        "content_type": "post",
        "title": "Python Tutorial",
        "excerpt": "Learn Python...",
        "rank": 1.5
      },
      "content": { ... }
    }
  ]
}
```

## Configuration

No additional configuration required. Search index is stored in `webcms_search.db`.

## Reindexing

If needed, manually reindex all content:

```python
service = SearchService(db)
count = service.reindex_all()
print(f"Indexed {count} items")
```

## Advanced Usage

### Custom Indexing

```python
from webcms.search.indexer import ContentIndexer

indexer = ContentIndexer()
indexer.index_post(post)  # Index single post
indexer.index_page(page)  # Index single page
```

### Search Suggestions

```python
suggestions = service.get_suggestions("pyt", limit=5)
# Returns: ["Python Tutorial", "Python Guide", ...]
```

## Performance

- Index updates are synchronous (immediate)
- Search queries use FTS5 ranking
- Auto-generated excerpts from content
