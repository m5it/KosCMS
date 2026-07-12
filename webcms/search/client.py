"""
Elasticsearch client with connection management.
"""

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError


class ElasticsearchClient:
    """Elasticsearch client wrapper."""

    def __init__(self, hosts=None, index_prefix="webcms"):
        self.hosts = hosts or ["http://localhost:9200"]
        self.index_prefix = index_prefix
        self._client = None

    def connect(self):
        """Connect to Elasticsearch."""
        if self._client is None:
            self._client = Elasticsearch(self.hosts)
        return self._client

    def ping(self):
        """Check Elasticsearch connectivity."""
        try:
            return self.connect().ping()
        except Exception:
            return False

    def index_name(self, content_type):
        """Get index name for content type."""
        return f"{self.index_prefix}_{content_type}"

    def close(self):
        """Close client connection."""
        if self._client:
            self._client.close()
            self._client = None
