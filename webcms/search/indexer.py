"""
Elasticsearch index management and document indexing.
"""

import json
from datetime import datetime


class SearchIndexer:
    """Manages Elasticsearch indices and documents."""

    def __init__(self, es_client):
        self.es = es_client

    def create_index(self, content_type, mappings=None):
        """Create index with mappings."""
        index = self.es.index_name(content_type)
        default_mappings = {
            "properties": {
                "id": {"type": "keyword"},
                "title": {"type": "text", "analyzer": "standard"},
                "content": {"type": "text", "analyzer": "standard"},
                "excerpt": {"type": "text"},
                "slug": {"type": "keyword"},
                "status": {"type": "keyword"},
                "author_id": {"type": "keyword"},
                "author_name": {"type": "keyword"},
                "tags": {"type": "keyword"},
                "categories": {"type": "keyword"},
                "published_at": {"type": "date"},
                "created_at": {"type": "date"}
            }
        }
        body = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": mappings or default_mappings
        }
        return self.es.connect().indices.create(index=index, body=body, ignore=400)

    def delete_index(self, content_type):
        """Delete index."""
        index = self.es.index_name(content_type)
        return self.es.connect().indices.delete(index=index, ignore=[400, 404])

    def index_document(self, content_type, doc_id, document):
        """Index a document."""
        index = self.es.index_name(content_type)
        document["indexed_at"] = datetime.utcnow().isoformat()
        return self.es.connect().index(index=index, id=doc_id, body=document)

    def delete_document(self, content_type, doc_id):
        """Delete document from index."""
        index = self.es.index_name(content_type)
        return self.es.connect().delete(index=index, id=doc_id, ignore=[400, 404])

    def refresh_index(self, content_type):
        """Refresh index for immediate search."""
        index = self.es.index_name(content_type)
        return self.es.connect().indices.refresh(index=index)

    def index_exists(self, content_type):
        """Check if index exists."""
        index = self.es.index_name(content_type)
        return self.es.connect().indices.exists(index=index)


# Compatibility alias for existing code
ContentIndexer = SearchIndexer
