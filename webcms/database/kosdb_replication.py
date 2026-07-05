"""
KosDB Replication Integration

Monitor replication status, handle failover, configure replication setups.
"""

import socket
import threading
import time
import json
import logging
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass
from enum import Enum

from .kosdb_client import KosDBClient, KosDBConfig


logger = logging.getLogger("webcms.kosdb.replication")


class ReplicationRole(Enum):
    """Replication role."""
    STANDALONE = "standalone"
    MASTER = "master"
    SLAVE = "slave"
    MASTER_MASTER = "master_master"


class ReplicationStatus(Enum):
    """Replication connection status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    SYNCING = "syncing"
    ERROR = "error"


@dataclass
class ReplicationConfig:
    """Replication configuration."""
    server_id: int = 1
    role: ReplicationRole = ReplicationRole.STANDALONE
    master_host: Optional[str] = None
    master_port: Optional[int] = None
    replication_port: Optional[int] = None
    peer_host: Optional[str] = None
    peer_port: Optional[int] = None
    auto_failover: bool = False
    sync_interval: float = 1.0


@dataclass
class ReplicationStats:
    """Replication statistics."""
    status: ReplicationStatus
    binlog_position: int = 0
    last_sync_time: Optional[float] = None
    lag_seconds: float = 0.0
    connected_slaves: int = 0
    bytes_replicated: int = 0
    error_message: Optional[str] = None


class KosDBReplicationManager:
    """
    Manages KosDB replication for WebCMS.
    
    Handles:
    - Master-slave replication
    - Master-master replication
    - Failover and recovery
    - Status monitoring
    """
    
    def __init__(self, kosdb_client: KosDBClient, config: ReplicationConfig):
        self.kosdb = kosdb_client
        self.config = config
        self.stats = ReplicationStats(status=ReplicationStatus.DISCONNECTED)
        
        # Replication threads
        self._replication_thread: Optional[threading.Thread] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False
        
        # Callbacks
        self._status_callbacks: List[Callable] = []
        self._failover_callbacks: List[Callable] = []
        
        # Failover state
        self._is_failed_over = False
        self._original_master: Optional[tuple] = None
    
    def start(self):
        """Start replication management."""
        if self._running:
            return
        
        self._running = True
        
        # Start based on role
        if self.config.role == ReplicationRole.SLAVE:
            self._start_slave_replication()
        elif self.config.role == ReplicationRole.MASTER_MASTER:
            self._start_master_master()
        elif self.config.role == ReplicationRole.MASTER:
            self._start_master_server()
        
        # Start monitoring
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        logger.info(f"Replication manager started with role: {self.config.role.value}")
    
    def stop(self):
        """Stop replication."""
        self._running = False
        
        if self._replication_thread:
            self._replication_thread.join(timeout=5)
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        logger.info("Replication manager stopped")
    
    def _start_slave_replication(self):
        """Start as slave - connect to master."""
        if not self.config.master_host or not self.config.master_port:
            logger.error("Master host/port not configured for slave")
            return
        
        self._replication_thread = threading.Thread(
            target=self._slave_replication_loop,
            daemon=True
        )
        self._replication_thread.start()
    
    def _start_master_server(self):
        """Start replication server on master."""
        if not self.config.replication_port:
            logger.info("No replication port configured, running as standalone master")
            return
        
        # KosDB handles this internally, we just monitor
        self.stats.status = ReplicationStatus.CONNECTED
    
    def _start_master_master(self):
        """Start master-master replication."""
        if not self.config.peer_host or not self.config.peer_port:
            logger.error("Peer host/port not configured for master-master")
            return
        
        self._replication_thread = threading.Thread(
            target=self._master_master_loop,
            daemon=True
        )
        self._replication_thread.start()
    
    def _slave_replication_loop(self):
        """Slave replication loop."""
        while self._running:
            try:
                self.stats.status = ReplicationStatus.CONNECTING
                
                # Connect to master replication port
                master_repl_port = self.config.master_port + 1000  # Default offset
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                sock.connect((self.config.master_host, master_repl_port))
                
                # Authenticate as replication user
                sock.sendall(b"USER repl\n")
                response = sock.recv(1024).decode().strip()
                
                sock.sendall(b"PASS repl\n")  # Default password
                response = sock.recv(1024).decode().strip()
                
                if not response.startswith("OK"):
                    raise Exception("Replication auth failed")
                
                self.stats.status = ReplicationStatus.CONNECTED
                
                # Request binlog stream
                sock.sendall(f"BINLOG STREAM FROM {self.stats.binlog_position}\n".encode())
                
                # Receive and apply binlog events
                while self._running:
                    data = sock.recv(4096)
                    if not data:
                        break
                    
                    events = self._parse_binlog_events(data.decode())
                    for event in events:
                        self._apply_binlog_event(event)
                        self.stats.binlog_position = event.get("position", 0)
                        self.stats.bytes_replicated += len(json.dumps(event))
                    
                    self.stats.last_sync_time = time.time()
                
                sock.close()
                
            except Exception as e:
                logger.error(f"Replication error: {e}")
                self.stats.status = ReplicationStatus.ERROR
                self.stats.error_message = str(e)
                time.sleep(5)  # Retry delay
    
    def _master_master_loop(self):
        """Master-master replication loop."""
        while self._running:
            try:
                self.stats.status = ReplicationStatus.CONNECTING
                
                # Connect to peer
                peer_repl_port = self.config.peer_port + 1000
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                sock.connect((self.config.peer_host, peer_repl_port))
                
                # Bi-directional sync
                self.stats.status = ReplicationStatus.SYNCING
                
                while self._running:
                    # Poll for changes from peer
                    sock.sendall(b"POLL\n")
                    data = sock.recv(4096)
                    
                    if data:
                        events = self._parse_binlog_events(data.decode())
                        for event in events:
                            self._apply_binlog_event(event)
                    
                    # Send our changes to peer
                    local_events = self._get_local_binlog_events()
                    if local_events:
                        sock.sendall(json.dumps(local_events).encode())
                    
                    time.sleep(self.config.sync_interval)
                
                sock.close()
                
            except Exception as e:
                logger.error(f"Master-master error: {e}")
                self.stats.status = ReplicationStatus.ERROR
                time.sleep(5)
    
    def _parse_binlog_events(self, data: str) -> List[Dict]:
        """Parse binlog events from data."""
        events = []
        for line in data.strip().split('\n'):
            if line:
                try:
                    event = json.loads(line)
                    events.append(event)
                except json.JSONDecodeError:
                    pass
        return events
    
    def _apply_binlog_event(self, event: Dict):
        """Apply a binlog event to local database."""
        operation = event.get("operation")
        table = event.get("table")
        data = event.get("data", {})
        
        try:
            if operation == "INSERT":
                values = list(data.get("row", {}).values())
                self.kosdb.insert(table, values)
            elif operation == "UPDATE":
                set_clause = data.get("set_clause", {})
                where = data.get("where", {})
                self.kosdb.update(table, set_clause, where)
            elif operation == "DELETE":
                where = data.get("where", {})
                self.kosdb.delete(table, where)
            elif operation == "CREATE_TABLE":
                columns = data.get("columns", [])
                self.kosdb.create_table(table, columns)
            elif operation == "DROP_TABLE":
                self.kosdb.drop_table(table)
        except Exception as e:
            logger.error(f"Failed to apply event: {e}")
    
    def _get_local_binlog_events(self) -> List[Dict]:
        """Get local binlog events to send to peer."""
        # In real implementation, read from local binlog file
        return []
    
    def _monitor_loop(self):
        """Monitor replication status."""
        while self._running:
            # Update lag calculation
            if self.stats.last_sync_time:
                self.stats.lag_seconds = time.time() - self.stats.last_sync_time
            
            # Check for failover conditions
            if self.config.auto_failover and self.config.role == ReplicationRole.SLAVE:
                if self.stats.status == ReplicationStatus.ERROR:
                    self._attempt_failover()
            
            # Notify status callbacks
            for callback in self._status_callbacks:
                try:
                    callback(self.stats)
                except Exception as e:
                    logger.error(f"Status callback error: {e}")
            
            time.sleep(1)
    
    def _attempt_failover(self):
        """Attempt failover to become master."""
        if self._is_failed_over:
            return
        
        logger.warning("Attempting failover...")
        
        # Promote self to master
        self._original_master = (self.config.master_host, self.config.master_port)
        self.config.role = ReplicationRole.MASTER
        self.config.master_host = None
        self.config.master_port = None
        
        self._is_failed_over = True
        self.stats.status = ReplicationStatus.CONNECTED
        
        # Notify failover callbacks
        for callback in self._failover_callbacks:
            try:
                callback("promoted_to_master", self._original_master)
            except Exception as e:
                logger.error(f"Failover callback error: {e}")
        
        logger.info("Failover complete - now acting as master")
    
    def recover_from_failover(self):
        """Recover original master after it comes back."""
        if not self._is_failed_over or not self._original_master:
            return False
        
        logger.info("Recovering from failover...")
        
        # Demote back to slave
        self.config.role = ReplicationRole.SLAVE
        self.config.master_host, self.config.master_port = self._original_master
        
        self._is_failed_over = False
        
        # Restart replication
        self._start_slave_replication()
        
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get current replication status."""
        return {
            "role": self.config.role.value,
            "status": self.stats.status.value,
            "binlog_position": self.stats.binlog_position,
            "lag_seconds": self.stats.lag_seconds,
            "connected_slaves": self.stats.connected_slaves,
            "bytes_replicated": self.stats.bytes_replicated,
            "is_failed_over": self._is_failed_over,
            "error": self.stats.error_message
        }
    
    def on_status_change(self, callback: Callable):
        """Register status change callback."""
        self._status_callbacks.append(callback)
    
    def on_failover(self, callback: Callable):
        """Register failover callback."""
        self._failover_callbacks.append(callback)
    
    def force_sync(self) -> bool:
        """Force immediate synchronization."""
        if self.config.role != ReplicationRole.SLAVE:
            return False
        
        # Trigger immediate sync
        # In real implementation, send signal to replication thread
        return True
    
    def get_binlog_status(self) -> Dict[str, Any]:
        """Get binlog status from KosDB."""
        result = self.kosdb.execute("SHOW MASTER STATUS")
        
        # Parse result
        status = {
            "position": 0,
            "server_id": self.config.server_id,
            "connected_slaves": 0
        }
        
        # Extract from table format
        lines = result.split('\n')
        for line in lines:
            if "Binlog Position" in line:
                try:
                    status["position"] = int(line.split(':')[1].strip())
                except:
                    pass
            elif "Connected Slaves" in line:
                try:
                    status["connected_slaves"] = int(line.split(':')[1].strip())
                except:
                    pass
        
        return status


class ReplicationFailoverManager:
    """
    Manages automatic failover for KosDB replication.
    
    Monitors master health and promotes slaves when needed.
    """
    
    def __init__(self, slaves: List[KosDBReplicationManager]):
        self.slaves = slaves
        self._master_healthy = True
        self._active_slave: Optional[KosDBReplicationManager] = None
    
    def check_master_health(self, master_client: KosDBClient) -> bool:
        """Check if master is healthy."""
        try:
            result = master_client.execute("SHOW MASTER STATUS")
            return "ERROR" not in result
        except Exception as e:
            logger.error(f"Master health check failed: {e}")
            return False
    
    def elect_new_master(self) -> Optional[KosDBReplicationManager]:
        """Elect a new master from slaves."""
        # Select slave with most up-to-date data
        best_slave = None
        best_position = -1
        
        for slave in self.slaves:
            status = slave.get_status()
            if status["binlog_position"] > best_position:
                best_position = status["binlog_position"]
                best_slave = slave
        
        if best_slave:
            self._active_slave = best_slave
            best_slave._attempt_failover()
        
        return best_slave
    
    def promote_slave(self, slave: KosDBReplicationManager) -> bool:
        """Promote a specific slave to master."""
        if slave in self.slaves:
            self._active_slave = slave
            slave._attempt_failover()
            return True
        return False