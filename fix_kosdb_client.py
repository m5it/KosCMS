import base64
from pathlib import Path

p = Path("webcms/database/kosdb_client.py")
content = p.read_text()

# Find the broken area and fix it
# The issue is that close_all method got removed

# First, let's find where the pool class ends
fix_marker = """                elif not self._closed:
    def __exit__(self, *args):
        self.close()"""

correct_code = """                elif not self._closed:
                    self.pool.put(conn)
    
    def close_all(self):
        \"\"\"Close all connections in pool.\"\"\"
        self._closed = True
        
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except queue.Empty:
                break


class KosDBClient:
    \"\"\"High-level KosDB client.\"\"\"
    
    def __init__(self, config: Optional[KosDBConfig] = None):
        self.config = config or KosDBConfig()
        self.pool = KosDBConnectionPool(self.config)
    
    def execute(self, command: str) -> str:
        \"\"\"
        Execute command.
        
        Args:
            command: SQL-like command
        
        Returns:
            Server response
        \"\"\"
        with self.pool.acquire() as conn:
            return conn.execute(command)
    
    def query(self, command: str) -> Dict[str, Any]:
        \"\"\"
        Execute query and return parsed results.
        
        Args:
            command: SELECT query
        
        Returns:
            Dict with columns, rows, count
        \"\"\"
        with self.pool.acquire() as conn:
            return conn.query(command)
    
    def select(self, table: str, columns: List[str] = None,
               where: Dict[str, Any] = None,
               order_by: str = None,
               limit: int = None) -> Dict[str, Any]:
        \"\"\"
        Build and execute SELECT query.
        
        Args:
            table: Table name
            columns: Column names (None for *)
            where: Where conditions
            order_by: Order by clause
            limit: Limit results
        
        Returns:
            Query results
        \"\"\"
        cols = \", \".join(columns) if columns else \"*\"
        cmd = f\"SELECT {cols} FROM {table}\"
        
        if where:
            conditions = \" AND \".join(f\"{k}='{v}'\" for k, v in where.items())
            cmd += f\" WHERE {conditions}\"
        
        if order_by:
            cmd += f\" ORDER BY {order_by}\"
        
        if limit:
            cmd += f\" LIMIT {limit}\"
        
        return self.query(cmd)
    
    def insert(self, table: str, values: List[Any]) -> str:
        \"\"\"Execute INSERT.\"\"\"
        vals = \", \".join(f\"'{v}'\" if isinstance(v, str) else str(v) for v in values)
        cmd = f\"INSERT INTO {table} VALUES ({vals})\"
        return self.execute(cmd)
    
    def update(self, table: str, set_clause: Dict[str, Any],
               where: Dict[str, Any] = None) -> str:
        \"\"\"Execute UPDATE.\"\"\"
        sets = \", \".join(f\"{k}='{v}'\" if isinstance(v, str) else f\"{k}={v}\"
                        for k, v in set_clause.items())
        cmd = f\"UPDATE {table} SET {sets}\"
        
        if where:
            conditions = \" AND \".join(f\"{k}='{v}'\" for k, v in where.items())
            cmd += f\" WHERE {conditions}\"
        
        return self.execute(cmd)
    
    def delete(self, table: str, where: Dict[str, Any] = None) -> str:
        \"\"\"Execute DELETE.\"\"\"
        cmd = f\"DELETE FROM {table}\"
        
        if where:
            conditions = \" AND \".join(f\"{k}='{v}'\" for k, v in where.items())
            cmd += f\" WHERE {conditions}\"
        
        return self.execute(cmd)
    
    def create_table(self, table: str, columns: List[str]) -> str:
        \"\"\"Create table.\"\"\"
        cols = \", \".join(columns)
        cmd = f\"CREATE TABLE {table} ({cols})\"
        return self.execute(cmd)
    
    def drop_table(self, table: str) -> str:
        \"\"\"Drop table.\"\"\"
        return self.execute(f\"DROP TABLE {table}\")
    
    def list_tables(self) -> List[str]:
        \"\"\"List all tables.\"\"\"
        result = self.execute(\"SHOW TABLES\")
        if result.startswith(\"ERROR\"):
            return []
        return [line.strip() for line in result.split('\\\\n')
                if line.strip() and not line.strip().startswith(\"OK\")]
    
    def close(self):
        \"\"\"Close client and pool.\"\"\"
        self.pool.close_all()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()

    @contextmanager
    def transaction(self):
        \"\"\"
        Context manager for batch operations with a single pooled connection.
        
        Acquires one connection from the pool and yields it for multiple
        query()/execute() calls. This avoids repeated pool acquire/release
        and ping overhead during batch operations.
        
        If the connection dies during the transaction, it will attempt
        reconnection once before raising an error.
        
        Usage:
            with client.transaction() as conn:
                conn.execute(\"INSERT INTO users VALUES (1, 'Alice')\")
                conn.execute(\"INSERT INTO users VALUES (2, 'Bob')\")
                result = conn.query(\"SELECT * FROM users\")
        
        Yields:
            KosDBConnection: Pooled connection ready for operations
        
        Raises:
            RuntimeError: If connection cannot be established or reconnected
        \"\"\"
        conn = None
        
        try:
            # Acquire single connection from pool - this is the optimization:
            # one acquire/release cycle instead of N for N operations
            with self.pool.acquire() as conn:
                # Verify connection is alive before starting transaction
                if not conn.ping():
                    logger.debug(\"Connection stale, reconnecting before transaction\")
                    conn.close()
                    if not conn.connect():
                        raise RuntimeError(\"Failed to establish connection for transaction\")
                
                # Wrap connection to handle auto-reconnect on failure
                class _ReconnectingConnection:
                    def __init__(self, inner_conn, client):
                        self._conn = inner_conn
                        self._client = client
                        self._reconnected = False
                    
                    def _ensure_alive(self):
                        \"\"\"Check connection and reconnect if needed (once).\"\"\"
                        if not self._conn.ping() and not self._reconnected:
                            logger.warning(\"Connection lost during transaction, attempting reconnect\")
                            self._conn.close()
                            if self._conn.connect():
                                self._reconnected = True
                                logger.info(\"Successfully reconnected during transaction\")
                            else:
                                raise RuntimeError(\"Connection lost and reconnection failed\")
                    
                    def execute(self, command: str) -> str:
                        self._ensure_alive()
                        return self._conn.execute(command)
                    
                    def query(self, command: str) -> Dict[str, Any]:
                        self._ensure_alive()
                        return self._conn.query(command)
                    
                    # Expose underlying connection attributes if needed
                    @property
                    def connected(self):
                        return self._conn.connected
                    
                    @property
                    def config(self):
                        return self._conn.config
                
                # Yield wrapped connection with auto-reconnect capability
                yield _ReconnectingConnection(conn, self)
                
        except Exception as e:
            logger.error(f\"Transaction failed: {e}\")
            raise
        finally:
            # Connection is automatically released by pool.acquire() context manager
            # No explicit cleanup needed here - the pool handles it
            logger.debug(\"Transaction complete, connection released to pool\")
"""

if fix_marker in content:
    content = content.replace(fix_marker, correct_code)
    p.write_text(content)
    print("Fixed kosdb_client.py")
else:
    print("Marker not found - file may already be fixed or different structure")
    # Let's check what's there
    lines = content.splitlines()
    for i, line in enumerate(lines[340:360], start=341):
        print(f"{i}: {repr(line)}")
