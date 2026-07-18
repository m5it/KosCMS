"""
Redis client with connection pooling.
"""

try:
    import redis
    from redis.connection import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    ConnectionPool = None


class RedisClient:
    """Redis client wrapper with connection pooling."""

    def __init__(self, host="localhost", port=6379, db=0,
                 password=None, max_connections=50, socket_timeout=5):
        if not REDIS_AVAILABLE:
            raise ImportError("redis module not installed. Install with: pip install redis")
        
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self._pool = None
        self._client = None

    def _get_pool(self):
        if self._pool is None:
            self._pool = ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                max_connections=self.max_connections,
                socket_timeout=self.socket_timeout
            )
        return self._pool

    def get_client(self):
        """Get Redis client from pool."""
        if self._client is None:
            self._client = redis.Redis(connection_pool=self._get_pool())
        return self._client

    def ping(self):
        """Check Redis connectivity."""
        try:
            return self.get_client().ping()
        except Exception as e:
            return False

    def close(self):
        """Close connection pool."""
        if self._pool:
            self._pool.disconnect()
            self._pool = None
        self._client = None


# Global singleton
_redis_client = None


def get_redis_client(host="localhost", port=6379, db=0):
    """Get or create global Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient(host=host, port=port, db=db)
    return _redis_client


def get_redis_client_safe(host="localhost", port=6379, db=0):
    """Get Redis client or None if redis not available."""
    try:
        return get_redis_client(host, port, db)
    except ImportError:
        return None
