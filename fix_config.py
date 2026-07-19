from pathlib import Path

p = Path("webcms/database/kosdb_client.py")
content = p.read_text()

# Fix the corrupted config class
old_config = '''@dataclass
class KosDBConfig:
    """KosDB connection configuration."""
    # Query timeout
    query_timeout: float = 30.0
    
    # Ping optimization: skip ping if connection used within this many seconds
    max_ping_interval: float = 5.0
    
    # Reconnection settings
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    # Query timeout
    query_timeout: float = 30.0'''

new_config = '''@dataclass
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
    max_ping_interval: float = 5.0'''

if old_config in content:
    content = content.replace(old_config, new_config)
    p.write_text(content)
    print("Fixed config class")
else:
    print("Config pattern not found")
