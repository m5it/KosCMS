"""
Elasticsearch search with highlighting, filters, and fuzzy matching.
"""


class Searcher:
    """Performs searches against Elasticsearch."""

    def __init__(self, es_client):
        self.es = es_client

    def _build_query(self, query_text, filters=None, fuzzy=True):
        """Build Elasticsearch query."""
        must_clauses = [
            {
                "multi_match": {
                    "query": query_text,
                    "fields": ["title^3", "content^2", "excerpt", "tags^2", "categories"],
                    "fuzziness": "AUTO" if fuzzy else "0"
                }
            }
        ]

        filter_clauses = []
        if filters:
            if filters.get("status"):
                filter_clauses.append({"term": {"status": filters["status"]}})
            if filters.get("author_id"):
                filter_clauses.append({"term": {"author_id": filters["author_id"]}})
            if filters.get("tags"):
                filter_clauses.append({"terms": {"tags": filters["tags"]}})
            if filters.get("date_from") or filters.get("date_to"):
                date_range = {"range": {"published_at": {}}}
                if filters.get("date_from"):
                    date_range["range"]["published_at"]["gte"] = filters["date_from"]
                if filters.get("date_to"):
                    date_range["range"]["published_at"]["lte"] = filters["date_to"]
                filter_clauses.append(date_range)

        return {
            "query": {
                "bool": {
                    "must": must_clauses,
                    "filter": filter_clauses
                }
            },
            "highlight": {
                "fields": {
                    "title": {},
                    "content": {"fragment_size": 150, "number_of_fragments": 3},
                    "excerpt": {}
                }
            },
            "aggs": {
                "authors": {"terms": {"field": "author_name", "size": 10}},
                "tags": {"terms": {"field": "tags", "size": 20}},
                "categories": {"terms": {"field": "categories", "size": 20}},
                "statuses": {"terms": {"field": "status", "size": 10}}
            }
        }

    def search(self, query_text, content_types=None, filters=None,
               page=1, per_page=20, fuzzy=True):
        """Search across indices with pagination."""
        content_types = content_types or ["post", "page"]
        indices = ",".join(self.es.index_name(ct) for ct in content_types)

        body = self._build_query(query_text, filters, fuzzy)
        body["from"] = (page - 1) * per_page
        body["size"] = per_page

        response = self.es.connect().search(index=indices, body=body)
        return self._format_results(response, page, per_page)

    def _format_results(self, response, page, per_page):
        """Format Elasticsearch response."""
        hits = response.get("hits", {})
        total = hits.get("total", {}).get("value", 0)
        results = []

        for hit in hits.get("hits", []):
            source = hit.get("_source", {})
            source["_id"] = hit.get("_id")
            source["_score"] = hit.get("_score")
            source["highlight"] = hit.get("highlight", {})
            results.append(source)

        aggregations = response.get("aggregations", {})
        facets = {
            key: [bucket for bucket in agg.get("buckets", [])]
            for key, agg in aggregations.items()
        }

        return {
            "results": results,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
            "facets": facets
        }

    def suggest(self, query_text, content_types=None, size=5):
        """Get search suggestions."""
        content_types = content_types or ["post"]
        indices = ",".join(self.es.index_name(ct) for ct in content_types)

        body = {
            "suggest": {
                "title-suggest": {
                    "prefix": query_text,
                    "completion": {
                        "field": "title",
                        "size": size
                    }
                }
            },
            "size": 0
        }

        try:
            response = self.es.connect().search(index=indices, body=body)
            suggestions = response.get("suggest", {}).get("title-suggest", [{}])[0].get("options", [])
            return [opt.get("text") for opt in suggestions]
        except Exception:
            return []
