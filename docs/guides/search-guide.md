# WebCMS Search Guide

## Overview

WebCMS uses Elasticsearch for fast, faceted content search with typo tolerance.

## Basic Search

```bash
curl /api/v1/search?q=webcms
```

## Filters

Filter by status, author, tags, or date range:

```bash
curl "/api/v1/search?q=webcms&status=published&author_id=1&tags=python,django&date_from=2026-01-01"
```

## Facets

Search responses include facets for authors, tags, categories, and statuses. Use these to build faceted navigation UI.

## Suggestions

```bash
curl /api/v1/search/suggest?q=web
```

## Fuzzy Matching

Fuzzy matching is enabled by default. Disable with `fuzzy=false`.

## Admin Search UI

Visit `/admin/search` in the admin panel for a visual search interface with filters and facet navigation.
