"""
KosDB Client Adapter

Python client for KosDB LevelDB socket server with connection pooling,
automatic reconnection, and query methods.
"""

import socket
import threading
import queue
import json
import time
import logging
import select
from typing import Optional, Dict, List, Any, Callable
from contextlib import contextmanager
from dataclasses import dataclass


logger = logging.getLogger("webcms.kosdb")


@dataclass
class KosDBConfig:
    """KosDB connection configuration."""
    host: str = "localhost"
    port: int = 9999
    username: str = ""
    password: str = ""
    database: str = "default"
    
    # Pool settings
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    
    # Reconnection settings
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    # Query timeout
    query_timeout: float = 30.0
    
    # Ping optimization: skip ping if connection used within this many seconds (default 5)
    max_ping_interval: float = 5.0


class KosDBConnection:
    """Single KosDB connection."""
    
    def __init__(self, config: KosDBConfig):
        self.config = config
        self.socket: Optional[socket.socket] = None
        self.authenticated = False
        self.lock = threading.RLock()
        self.last_used = time.time()
        self.connected = False
        self._db_selected = False
    
    def connect(self) -> bool:
        """Establish connection to KosDB server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.config.query_timeout)
            self.socket.connect((self.config.host, self.config.port))
            self.connected = True
            self._db_selected = False
            
            # Authenticate
            if not self._authenticate():
                self.close()
                return False
            
            # Select database if specified
            if self.config.database:
                self._select_database(self.config.database)
            
            logger.debug(f"Connected to KosDB at {self.config.host}:{self.config.port}")
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.close()
            return False
    
    def _authenticate(self) -> bool:
        """Authenticate with KosDB server."""
        try:
            # Read welcome message
            welcome = self._receive()
            logger.debug(f"Server welcome: {welcome[:100]}...")
            
            # Try LOGIN command (KosDB v2.3+)
            self._send(f"LOGIN {self.config.username} {self.config.password}")
            login_response = self._receive()
            
            if login_response.startswith("OK"):
                self.authenticated = True
                logger.debug(f"Authenticated as {self.config.username}")
                return True
            
            # Fallback to USER/PASS (KosDB v2.2 and earlier)
            self._send(f"USER {self.config.username}")
            user_response = self._receive()
            
            if not user_response.startswith("OK"):
                logger.error(f"Auth failed: {login_response} / {user_response}")
                return False
            
            self._send(f"PASS {self.config.password}")
            pass_response = self._receive()
            
            if pass_response.startswith("OK"):
                self.authenticated = True
                logger.debug(f"Authenticated as {self.config.username}")
                return True
            else:
                logger.error(f"Authentication failed: {pass_response}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def _select_database(self, database: str) -> bool:
        """Select database."""
        result = self.execute(f"USE {database}")
        self._db_selected = result.startswith("OK")
        return self._db_selected
    
    def _send(self, command: str) -> None:
        """Send command to server."""
        if self.socket:
            self.socket.sendall(command.encode() + b'\n')
    
    def _receive(self) -> str:
        """Receive full response from server."""
        if not self.socket:
            return "ERROR: Not connected"
        
        data = b""
        try:
            self.socket.settimeout(2.0)
            while True:
                try:
                    chunk = self.socket.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    self.socket.settimeout(0.3)
                except socket.timeout:
                    break
        except Exception:
            pass
        finally:
            self.socket.settimeout(self.config.query_timeout)
        
        return data.decode().strip() if data else ""
    
    def execute(self, command: str) -> str:
        """
        Execute SQL-like command.
        
        Args:
            command: SQL command string
        
        Returns:
            Server response string
        """
        with self.lock:
            if not self.connected:
                if not self.connect():
                    return "ERROR: Connection failed"
            
            try:
                self._send(command)
                response = self._receive()
                self.last_used = time.time()
                return response
                
            except socket.timeout:
                logger.warning("Query timeout")
                return "ERROR: Query timeout"
            except Exception as e:
                logger.error(f"Execute error: {e}")
                self.connected = False
                return f"ERROR: {e}"
    
    def query(self, command: str) -> Dict[str, Any]:
        """
        Execute query and parse results.
        
        Args:
            command: SELECT or other query
        
        Returns:
            Parsed results as dict with columns and rows
        """
        response = self.execute(command)
        
        if response.startswith("ERROR"):
            return {"error": response, "columns": [], "rows": []}
        
        if response == "Empty set":
            return {"columns": [], "rows": [], "count": 0}
        
        # Parse table format
        return self._parse_table_response(response)
    
    def _parse_table_response(self, response: str) -> Dict[str, Any]:
        """Parse tabular response into structured data."""
        lines = response.split('\n')
        
        if len(lines) < 3:
            return {"columns": [], "rows": [], "raw": response}
        
        columns = []
        rows = []
        header_seen = False
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('+') and line.endswith('+'):
                if header_seen:
                    continue
                continue
            
            if line.startswith('|'):
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                
                if not columns:
                    columns = cells
                    header_seen = True
                else:
                    row = {}
                    for i, col in enumerate(columns):
                        if i < len(cells):
                            row[col] = cells[i]
                    rows.append(row)
        
        count = len(rows)
        for line in lines:
            if "row(s) in set" in line:
                try:
                    count = int(line.split()[0])
                except:
                    pass
        
        return {
            "columns": columns,
            "rows": rows,
            "count": count
        }
    
    def ping(self) -> bool:
        """
        Check if connection is alive using TCP keepalive.
        
        Uses select.select() and MSG_PEEK to detect if the connection
        has been closed by the peer without sending any command.
        This eliminates the round-trip of sending SHOW DATABASES.
        
        Returns:
            True if connection appears alive, False if dead/closed
        """
        if not self.socket:
            return False
        
        try:
            # Check if socket has any data waiting (peer might have sent something)
            readable, _, exceptional = select.select(
                [self.socket], [], [], 0
            )
            
            if exceptional:
                # Exceptional condition means error
                return False
            
            if readable:
                # Data available - use MSG_PEEK to check without consuming
                try:
                    data = self.socket.recv(1, socket.MSG_PEEK)
                    if len(data) == 0:
                        # Empty data means connection closed by peer
                        logger.debug("Ping detected closed connection (empty recv)")
                        return False
                    # Has data, connection is alive
                    return True
                except (OSError, socket.error):
                    return False
            
            # No data waiting and no exception - connection is likely alive
            # We can't be 100% sure without sending data, but this is the
            # trade-off for eliminating the round-trip
            return True
            
        except Exception as e:
            logger.debug(f"Ping check failed: {e}")
            return False
    
    def close(self) -> None:
        """Close connection."""
        try:
            if self.socket:
                self._send("QUIT")
                self.socket.close()
        except:
            pass
        finally:
            self.socket = None
            self.connected = False
            self.authenticated = False
            self._db_selected = False
    
    @contextmanager
    def transaction(self):
        """
        Context manager for manual transaction control.
        
        Yields the connection itself, allowing the caller to send
        BEGIN/COMMIT commands as regular execute() calls.
        
        Usage:
            with conn.transaction() as c:
                c.execute("BEGIN")
                c.execute("INSERT INTO ...")
                c.execute("COMMIT")
        
        Yields:
            KosDBConnection: This connection instance
        """
        try:
            yield self
        except Exception:
            # Re-raise without handling - caller manages transaction state
            raise
    
    def pipeline(self, commands: List[str]) -> List[str]:
        """
        Execute multiple commands in a pipeline.
        
        Sends all commands without waiting for individual responses,
        then collects all responses. This eliminates network round-trip
        idle time between commands.
        
        Args:
            commands: List of SQL commands to execute
        
        Returns:
            List of response strings, one per command
        
        Usage:
            results = conn.pipeline([
                "INSERT INTO users VALUES (1, 'Alice')",
                "INSERT INTO users VALUES (2, 'Bob')",
                "SELECT * FROM users"
            ])
        """
        with self.lock:
            if not self.connected:
                if not self.connect():
                    return [f"ERROR: Connection failed"] * len(commands)
            
            try:
                # Send all commands without waiting for responses
                for cmd in commands:
                    self._send(cmd)
                
                # Collect all responses
                results = []
                for _ in commands:
                    response = self._receive()
                    results.append(response)
                
                self.last_used = time.time()
                return results
                
            except socket.timeout:
                logger.warning("Pipeline timeout")
                return [f"ERROR: Pipeline timeout"] * len(commands)
            except Exception as e:
                logger.error(f"Pipeline error: {e}")
                self.connected = False
                return [f"ERROR: {e}"] * len(commands)


class KosDBConnectionPool:
    """Connection pool for KosDB."""
    
    def __init__(self, config: KosDBConfig):
        self.config = config
        self.pool: queue.Queue = queue.Queue(maxsize=config.pool_size)
        self.overflow_count = 0
        self.lock = threading.RLock()
        self._closed = False
        
        # Initialize pool
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Create initial connections."""
        for _ in range(self.config.pool_size):
            conn = KosDBConnection(self.config)
            if conn.connect():
                self.pool.put(conn)
                logger.debug("Added connection to pool")
    
    @contextmanager
    def acquire(self):
        """
        Acquire connection from pool.
        
        Usage:
            with pool.acquire() as conn:
                result = conn.execute("SELECT * FROM users")
        """
        conn = None
        is_overflow = False
        
        try:
            # Try to get from pool
            try:
                conn = self.pool.get(timeout=self.config.pool_timeout)
            except queue.Empty:
                # Create overflow connection
                with self.lock:
                    if self.overflow_count < self.config.max_overflow:
                        conn = KosDBConnection(self.config)
                        if conn.connect():
                            is_overflow = True
                            self.overflow_count += 1
                        else:
                            raise RuntimeError("Failed to create overflow connection")
                    else:
                        raise RuntimeError("Connection pool exhausted")
            
            # Check if connection is alive - skip TCP keepalive check if recently used
            # The TCP check is lightweight (select + MSG_PEEK) but we still skip it
            # for very recent connections to minimize any overhead
            time_since_used = time.time() - conn.last_used
            should_check = time_since_used > self.config.max_ping_interval
            
            if should_check:
                logger.debug(f"Connection idle for {time_since_used:.2f}s, TCP keepalive check")
                if not conn.ping():
                    conn.close()
                    conn.connect()
            else:
                logger.debug(f"Skipping TCP check, connection used {time_since_used:.2f}s ago "
                           f"(max_ping_interval={self.config.max_ping_interval}s)")
            
            if self.config.database and not conn._db_selected:
                conn.execute(f"USE {self.config.database}")
            
            yield conn
            
        finally:
            if conn:
                if is_overflow:
                    conn.close()
                    with self.lock:
                        self.overflow_count -= 1
                elif not self._closed:
                    self.pool.put(conn)
    
    def close_all(self):
        """Close all connections in pool."""
        self._closed = True
        
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except queue.Empty:
                break


class KosDBClient:
    """High-level KosDB client."""
    
    def __init__(self, config: Optional[KosDBConfig] = None):
        self.config = config or KosDBConfig()
        self.pool = KosDBConnectionPool(self.config)
    
    def execute(self, command: str) -> str:
        """
        Execute command.
        
        Args:
            command: SQL-like command
        
        Returns:
            Server response
        """
        with self.pool.acquire() as conn:
            return conn.execute(command)
    
    def query(self, command: str) -> Dict[str, Any]:
        """
        Execute query and return parsed results.
        
        Args:
            command: SELECT query
        
        Returns:
            Dict with columns, rows, count
        """
        with self.pool.acquire() as conn:
            return conn.query(command)
    
    def select(self, table: str, columns: List[str] = None,
               where: Dict[str, Any] = None,
               order_by: str = None,
               limit: int = None) -> Dict[str, Any]:
        """
        Build and execute SELECT query.
        
        Args:
            table: Table name
            columns: Column names (None for *)
            where: Where conditions
            order_by: Order by clause
            limit: Limit results
        
        Returns:
            Query results
        """
        cols = ", ".join(columns) if columns else "*"
        cmd = f"SELECT {cols} FROM {table}"
        
        if where:
            conditions = " AND ".join(f"{k}='{v}'" for k, v in where.items())
            cmd += f" WHERE {conditions}"
        
        if order_by:
            cmd += f" ORDER BY {order_by}"
        
        if limit:
            cmd += f" LIMIT {limit}"
        
        return self.query(cmd)
    
    def insert(self, table: str, values: List[Any]) -> str:
        """Execute INSERT."""
        vals = ", ".join(f"'{v}'" if isinstance(v, str) else str(v) for v in values)
        cmd = f"INSERT INTO {table} VALUES ({vals})"
        return self.execute(cmd)
    
    def update(self, table: str, set_clause: Dict[str, Any],
               where: Dict[str, Any] = None) -> str:
        """Execute UPDATE."""
        sets = ", ".join(f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}"
                        for k, v in set_clause.items())
        cmd = f"UPDATE {table} SET {sets}"
        
        if where:
            conditions = " AND ".join(f"{k}='{v}'" for k, v in where.items())
            cmd += f" WHERE {conditions}"
        
        return self.execute(cmd)
    
    def delete(self, table: str, where: Dict[str, Any] = None) -> str:
        """Execute DELETE."""
        cmd = f"DELETE FROM {table}"
        
        if where:
            conditions = " AND ".join(f"{k}='{v}'" for k, v in where.items())
            cmd += f" WHERE {conditions}"
        
        return self.execute(cmd)
    
    def create_table(self, table: str, columns: List[str]) -> str:
        """Create table."""
        cols = ", ".join(columns)
        cmd = f"CREATE TABLE {table} ({cols})"
        return self.execute(cmd)
    
    def drop_table(self, table: str) -> str:
        """Drop table."""
        return self.execute(f"DROP TABLE {table}")
    
    def list_tables(self) -> List[str]:
        """List all tables."""
        result = self.execute("SHOW TABLES")
        if result.startswith("ERROR"):
            return []
        return [line.strip() for line in result.split('\\n')
                if line.strip() and not line.strip().startswith("OK")]
    
    def close(self):
        """Close client and pool."""
        self.pool.close_all()
    
    @contextmanager
    def transaction(self, pipeline: bool = False):
        """
        Context manager for batch operations with a single pooled connection.
        
        Acquires one connection from the pool and yields it for multiple
        query()/execute() calls. This avoids repeated pool acquire/release
        and ping overhead during batch operations.
        
        If the connection dies during the transaction, it will attempt
        reconnection once before raising an error.
        
        Args:
            pipeline: If True, buffers execute() calls and sends them all at once
                     when the context exits. query() calls still execute immediately.
                     This reduces round-trips for write-heavy transactions.
        
        Usage:
            # Normal transaction (immediate execution)
            with client.transaction() as conn:
                conn.execute("INSERT INTO users VALUES (1, 'Alice')")
                result = conn.query("SELECT * FROM users")
            
            # Pipelined transaction (buffered execution)
            with client.transaction(pipeline=True) as conn:
                conn.execute("BEGIN")
                conn.execute("INSERT INTO users VALUES (1, 'Alice')")
                conn.execute("INSERT INTO users VALUES (2, 'Bob')")
                conn.execute("COMMIT")
                # All commands sent at once when context exits
        
        Yields:
            KosDBConnection or _PipelinedConnection: Pooled connection ready for operations
        
        Raises:
            RuntimeError: If connection cannot be established or reconnected
        """
        conn = None
        
        try:
            # Acquire single connection from pool - this is the optimization:
            # one acquire/release cycle instead of N for N operations
            with self.pool.acquire() as conn:
                # Verify connection is alive before starting transaction
                if not conn.ping():
                    logger.debug("Connection stale, reconnecting before transaction")
                    conn.close()
                    if not conn.connect():
                        raise RuntimeError("Failed to establish connection for transaction")
                
                if pipeline:
                    # Yield pipelined connection that buffers execute() calls
                    pipelined_conn = _PipelinedConnection(conn)
                    try:
                        yield pipelined_conn
                    finally:
                        # Flush any buffered commands when exiting context
                        pipelined_conn._flush()
                else:
                    # Yield wrapped connection with auto-reconnect capability
                    yield _ReconnectingConnection(conn, self)
                
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            raise
        finally:
            # Connection is automatically released by pool.acquire() context manager
            # No explicit cleanup needed here - the pool handles it
            logger.debug("Transaction complete, connection released to pool")


class _ReconnectingConnection:
    """
    Wrapper for KosDBConnection that provides auto-reconnect capability.
    
    Used in non-pipelined transactions to handle connection failures gracefully.
    """
    
    def __init__(self, inner_conn, client):
        self._conn = inner_conn
        self._client = client
        self._reconnected = False
    
    def _ensure_alive(self):
        """Check connection and reconnect if needed (once)."""
        if not self._conn.ping() and not self._reconnected:
            logger.warning("Connection lost during transaction, attempting reconnect")
            self._conn.close()
            if self._conn.connect():
                self._reconnected = True
                logger.info("Successfully reconnected during transaction")
            else:
                raise RuntimeError("Connection lost and reconnection failed")
    
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


class _PipelinedConnection:
    """
    Wrapper for KosDBConnection that buffers execute() calls for pipelining.
    
    Used in pipelined transactions to reduce round-trips for write-heavy operations.
    query() calls execute immediately for backward compatibility.
    """
    
    def __init__(self, inner_conn):
        self._conn = inner_conn
        self._buffer: List[str] = []
        self._results: List[str] = []
        self._flushed = False
    
    def execute(self, command: str) -> str:
        """
        Buffer execute() call for pipelined execution.
        
        Commands are collected and sent all at once when the transaction
        context exits.
        
        Args:
            command: SQL command to execute
        
        Returns:
            Placeholder response ("OK (buffered)") - actual results available
            after context exits via get_buffered_results()
        """
        if self._flushed:
            raise RuntimeError("Cannot execute after pipeline has been flushed")
        
        self._buffer.append(command)
        logger.debug(f"Buffered command: {command[:50]}...")
        
        # Return placeholder - actual result comes after flush
        return "OK (buffered)"
    
    def query(self, command: str) -> Dict[str, Any]:
        """
        Execute query immediately (not buffered).
        
        query() calls need immediate results, so they bypass the buffer
        and execute directly on the underlying connection.
        
        Args:
            command: SELECT or other query
        
        Returns:
            Parsed results as dict with columns and rows
        """
        # Flush any pending writes before query to maintain consistency
        if self._buffer:
            self._flush()
        
        return self._conn.query(command)
    
    def _flush(self):
        """Send all buffered commands and collect responses."""
        if self._flushed or not self._buffer:
            return
        
        self._flushed = True
        
        try:
            # Use the underlying connection's pipeline method
            self._results = self._conn.pipeline(self._buffer)
            logger.debug(f"Flushed {len(self._buffer)} commands, got {len(self._results)} results")
        except Exception as e:
            logger.error(f"Pipeline flush failed: {e}")
            # Mark results as errors for all buffered commands
            self._results = [f"ERROR: Pipeline flush failed: {e}"] * len(self._buffer)
    
    def get_buffered_results(self) -> List[str]:
        """
        Get results from buffered execute() calls.
        
        Should be called after the transaction context exits to retrieve
        the actual server responses for buffered commands.
        
        Returns:
            List of response strings, one per buffered execute() call
        """
        if not self._flushed:
            raise RuntimeError("Pipeline not yet flushed - call within context")
        return self._results
    
    # Expose underlying connection attributes if needed
    @property
    def connected(self):
        return self._conn.connected
    
    @property
    def config(self):
        return self._conn.config
