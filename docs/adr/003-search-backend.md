# ADR 003: Search Backend

## Status

Accepted

## Context

WebCMS needed full-text search, faceted navigation, and typo tolerance.

## Decision

We integrated Elasticsearch for search indexing and queries, with a local analytics layer for query suggestions and popular query tracking.

## Consequences

- Positive: Fast, scalable search with rich query capabilities
- Positive: Faceted search improves content discovery
- Negative: Adds operational complexity of Elasticsearch cluster
