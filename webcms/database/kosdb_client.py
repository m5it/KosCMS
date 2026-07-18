
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
        """Check if connection is alive."""
        if not self.socket:
            return False
        
        try:
            # Simple ping with SHOW DATABASES
            self._send("SHOW DATABASES")
            response = self._receive()
            return not response.startswith("ERROR")
        except:
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
            
            # Check if connection is alive
            if not conn.ping():
                conn.close()
                conn.connect()
            
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
        return [line.strip() for line in result.split('\n')
                if line.strip() and not line.strip().startswith("OK")]
    
    def close(self):
        """Close client and pool."""
        self.pool.close_all()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
