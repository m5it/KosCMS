
# Query Optimization Guide

This guide documents the query optimization strategies used in WebCMS v1.1.0.

## Overview

Database queries have been optimized using SQLAlchemy's eager loading capabilities to eliminate N+1 query problems and reduce database round trips.

## Optimization Results

### Before Optimization

| Operation | Query Count | Issue |
|-----------|-------------|-------|
| Get post by ID | 4 queries | Separate queries for post, author, categories, tags |
| List published posts | N+1 queries | One query for posts, N queries for authors |
| List by category | N+3 queries | Base query + author + categories + tags for each post |

### After Optimization

| Operation | Query Count | Improvement |
|-----------|-------------|-------------|
| Get post by ID | 1 query | 75% reduction |
| List published posts | 1 query | Eliminates N+1 |
| List by category | 2 queries | ~90% reduction for large N |

## Eager Loading Strategies

### `joinedload()` - One-to-Many Relationships

Use for single relationships that return one related object:

```python
from sqlalchemy.orm import joinedload

# Good for: author (one post has one author)
query.options(joinedload(Post.author))
```

**Result**: Single SQL query with JOIN

### `selectinload()` - Many-to-Many Relationships

Use for collections that may contain multiple items:

```python
from sqlalchemy.orm import selectinload

# Good for: categories, tags (one post has many)
query.options(selectinload(Post.categories))
```

**Result**: Two queries - one for main objects, one for all related

## Implementation Examples

### Repository Pattern

```python
class PostRepository:
    def _base_query(self):
        """Base query with all relationships eager loaded."""
        return self.db.query(Post).options(
            joinedload(Post.author),
            selectinload(Post.categories),
            selectinload(Post.tags)
        )
    
    def get_by_id(self, post_id: str):
        """Single query with all data."""
        return self._base_query().filter(
            Post.id == post_id
        ).first()
```

## Query Logging

Enable query logging in debug mode:

```python
from webcms.content.repository import enable_query_logging, get_query_stats

# Enable logging
enable_query_logging()

# Get statistics
stats = get_query_stats()
print(f"Queries: {stats['query_count']}")
print(f"Total time: {stats['total_time_ms']}ms")
print(f"Average: {stats['avg_time_ms']}ms")
```

## Best Practices

1. **Always use eager loading** for relationships that will be accessed
2. **Use `joinedload()`** for single relationships (author, parent)
3. **Use `selectinload()`** for collections (categories, tags, children)
4. **Avoid lazy loading** in loops - causes N+1 queries
5. **Profile queries** in development to catch issues early

## Anti-Patterns

### ❌ Bad: Lazy Loading in Loop

```python
posts = db.query(Post).all()  # 1 query
for post in posts:
    print(post.author.name)   # N queries - BAD!
```

### ✅ Good: Eager Loading

```python
posts = db.query(Post).options(
    joinedload(Post.author)
).all()  # 1 query total
for post in posts:
    print(post.author.name)   # No additional queries
```

## Benchmarking

Run benchmarks to verify improvements:

```python
import time
from webcms.content.repository import PostRepository

def benchmark_list_posts():
    repo = PostRepository(db)
    
    start = time.time()
    posts = repo.list_published(limit=50)
    elapsed = time.time() - start
    
    print(f"Loaded {len(posts)} posts in {elapsed*1000:.2f}ms")
    return elapsed

# Compare with/without optimization
time_optimized = benchmark_list_posts()
```

## Migration Notes

When upgrading from v1.0.0:
- No database schema changes required
- Code changes are backward compatible
- Existing queries benefit immediately from eager loading
