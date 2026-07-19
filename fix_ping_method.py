from pathlib import Path

p = Path("webcms/database/kosdb_client.py")
content = p.read_text()

# Fix the corrupted ping() method
old_ping = '''    def ping(self) -> bool:
        """Check if connection is alive."""
        if not self.socket:
            return False
            # Check if connection is alive - skip ping if recently used
            # This optimization avoids a round-trip when connection is likely still good
            time_since_used = time.time() - conn.last_used
            should_ping = time_since_used > self.config.max_ping_interval
            
            if should_ping:
                logger.debug(f"Connection idle for {time_since_used:.2f}s, pinging")
                if not conn.ping():
                    conn.close()
                    conn.connect()
            else:
                logger.debug(f"Skipping ping, connection used {time_since_used:.2f}s ago "
                           f"(max_ping_interval={self.config.max_ping_interval}s)")
            pass
        finally:
            self.socket = None
            self.connected = False
            self.authenticated = False
            self._db_selected = False'''

new_ping = '''    def ping(self) -> bool:
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
            self._db_selected = False'''

if old_ping in content:
    content = content.replace(old_ping, new_ping)
    p.write_text(content)
    print("Fixed ping() method")
else:
    print("Pattern not found - checking current state")
    # Find ping method
    lines = p.read_text().splitlines()
    for i, line in enumerate(lines):
        if "def ping" in line:
            print(f"Found ping at line {i+1}")
            for j in range(i, min(i+20, len(lines))):
                print(f"{j+1:4d}: {lines[j]}")
            break
