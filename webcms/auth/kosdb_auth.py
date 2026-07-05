"""
KosDB Authentication Bridge

Bridge WebCMS authentication with KosDB user system.
Syncs users, authenticates against KosDB, maps privileges to WebCMS roles.
"""

import hashlib
import secrets
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime

from webcms.database.kosdb_client import KosDBClient, KosDBConfig


class KosDBAuthBridge:
    """
    Bridge between WebCMS auth and KosDB auth systems.
    
    Supports two modes:
    1. Sync mode: WebCMS users synced to KosDB
    2. Proxy mode: Authenticate directly against KosDB
    """
    
    def __init__(self, kosdb_client: KosDBClient, sync_mode: bool = True):
        self.kosdb = kosdb_client
        self.sync_mode = sync_mode
        self._ensure_system_tables()
    
    def _ensure_system_tables(self):
        """Ensure KosDB has required auth tables."""
        # Check if _system database exists
        result = self.kosdb.execute("SHOW DATABASES")
        
        # Create system database if needed
        if "_system" not in result:
            self.kosdb.execute("CREATE DATABASE _system")
        
        # Use system database
        self.kosdb.execute("USE _system")
        
        # Check for users table
        result = self.kosdb.execute("SHOW TABLES")
        if "_users" not in result:
            self._create_users_table()
        
        if "_privileges" not in result:
            self._create_privileges_table()
    
    def _create_users_table(self):
        """Create users table in KosDB."""
        self.kosdb.execute("""
            CREATE TABLE _users (
                id INT PRIMARY KEY,
                username TEXT INDEX,
                email TEXT INDEX,
                password_hash TEXT,
                is_admin INT,
                is_active INT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
    
    def _create_privileges_table(self):
        """Create privileges table in KosDB."""
        self.kosdb.execute("""
            CREATE TABLE _privileges (
                id INT PRIMARY KEY,
                username TEXT INDEX,
                db_pattern TEXT,
                table_pattern TEXT,
                privileges TEXT,
                granted_by TEXT,
                granted_at TEXT
            )
        """)
    
    def sync_user_to_kosdb(self, user_data: Dict[str, Any]) -> bool:
        """
        Sync WebCMS user to KosDB.
        
        Args:
            user_data: User data from WebCMS
        
        Returns:
            True if synced successfully
        """
        if not self.sync_mode:
            return True
        
        # Check if user exists
        result = self.kosdb.select(
            "_users",
            columns=["id"],
            where={"username": user_data["username"]}
        )
        
        user_record = {
            "id": user_data.get("id", self._get_next_user_id()),
            "username": user_data["username"],
            "email": user_data.get("email", ""),
            "password_hash": user_data["password_hash"],
            "is_admin": 1 if user_data.get("is_superuser") else 0,
            "is_active": 1 if user_data.get("is_active", True) else 0,
            "created_at": user_data.get("created_at", datetime.utcnow().isoformat()),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if result["rows"]:
            # Update existing user
            self.kosdb.update(
                "_users",
                set_clause={
                    "email": user_record["email"],
                    "password_hash": user_record["password_hash"],
                    "is_admin": user_record["is_admin"],
                    "is_active": user_record["is_active"],
                    "updated_at": user_record["updated_at"]
                },
                where={"username": user_record["username"]}
            )
        else:
            # Insert new user
            self.kosdb.insert("_users", [
                user_record["id"],
                user_record["username"],
                user_record["email"],
                user_record["password_hash"],
                user_record["is_admin"],
                user_record["is_active"],
                user_record["created_at"],
                user_record["updated_at"]
            ])
        
        # Sync privileges
        self._sync_user_privileges(user_data)
        
        return True
    
    def _sync_user_privileges(self, user_data: Dict[str, Any]):
        """Sync user privileges to KosDB."""
        username = user_data["username"]
        
        # Clear existing privileges
        self.kosdb.execute(f"DELETE FROM _privileges WHERE username='{username}'")
        
        # Add new privileges based on roles
        roles = user_data.get("roles", [])
        privileges = []
        
        for role in roles:
            if role == "admin":
                privileges.append({
                    "db_pattern": "*",
                    "table_pattern": "*",
                    "privileges": "ALL"
                })
            elif role == "editor":
                privileges.extend([
                    {"db_pattern": "*", "table_pattern": "posts", "privileges": "SELECT,INSERT,UPDATE,DELETE"},
                    {"db_pattern": "*", "table_pattern": "pages", "privileges": "SELECT,INSERT,UPDATE,DELETE"},
                    {"db_pattern": "*", "table_pattern": "media", "privileges": "SELECT,INSERT,DELETE"}
                ])
            elif role == "author":
                privileges.append({
                    "db_pattern": "*",
                    "table_pattern": "posts",
                    "privileges": "SELECT,INSERT,UPDATE"
                })
        
        for priv in privileges:
            self.kosdb.insert("_privileges", [
                self._get_next_privilege_id(),
                username,
                priv["db_pattern"],
                priv["table_pattern"],
                priv["privileges"],
                "system",
                datetime.utcnow().isoformat()
            ])
    
    def authenticate_against_kosdb(self, username: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """
        Authenticate user against KosDB.
        
        Args:
            username: Username
            password: Plain text password
        
        Returns:
            Tuple of (success, user_data)
        """
        # Get user from KosDB
        result = self.kosdb.select(
            "_users",
            where={"username": username}
        )
        
        if not result["rows"]:
            return False, None
        
        user_row = result["rows"][0]
        stored_hash = user_row[3] if len(user_row) > 3 else ""
        
        # Verify password (using same hash as WebCMS)
        if self._verify_password(password, stored_hash):
            return True, {
                "id": user_row[0],
                "username": user_row[1],
                "email": user_row[2],
                "is_superuser": bool(user_row[4]),
                "is_active": bool(user_row[5])
            }
        
        return False, None
    
    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash."""
        # Use WebCMS password hasher
        from webcms.auth.password import PasswordHasher
        hasher = PasswordHasher()
        return hasher.verify_password(password, stored_hash)
    
    def check_kosdb_privilege(self, username: str, db: str, table: str, 
                               privilege: str) -> bool:
        """
        Check if user has privilege in KosDB.
        
        Args:
            username: Username
            db: Database name
            table: Table name
            privilege: Privilege to check (SELECT, INSERT, etc.)
        
        Returns:
            True if user has privilege
        """
        # Check if user is admin
        result = self.kosdb.select(
            "_users",
            columns=["is_admin"],
            where={"username": username}
        )
        
        if result["rows"] and result["rows"][0]:
            is_admin = result["rows"][0][0]
            if is_admin:
                return True
        
        # Check specific privileges
        result = self.kosdb.select(
            "_privileges",
            where={"username": username}
        )
        
        for row in result.get("rows", []):
            db_pattern = row[2] if len(row) > 2 else ""
            table_pattern = row[3] if len(row) > 3 else ""
            privileges = row[4] if len(row) > 4 else ""
            
            # Check pattern match
            if self._match_pattern(db, db_pattern) and \
               self._match_pattern(table, table_pattern):
                if "ALL" in privileges or privilege in privileges:
                    return True
        
        return False
    
    def _match_pattern(self, name: str, pattern: str) -> bool:
        """Check if name matches pattern (* = wildcard)."""
        if pattern == "*":
            return True
        return name == pattern
    
    def _get_next_user_id(self) -> int:
        """Get next user ID."""
        result = self.kosdb.execute("SELECT MAX(id) FROM _users")
        # Parse result
        if result and "row(s) in set" in result:
            # Extract number from result
            lines = result.split('\n')
            for line in lines:
                if '|' in line and not line.startswith('+-'):
                    val = line.split('|')[1].strip()
                    if val and val != 'NULL':
                        return int(val) + 1
        return 1
    
    def _get_next_privilege_id(self) -> int:
        """Get next privilege ID."""
        result = self.kosdb.execute("SELECT MAX(id) FROM _privileges")
        if result and "row(s) in set" in result:
            lines = result.split('\n')
            for line in lines:
                if '|' in line and not line.startswith('+-'):
                    val = line.split('|')[1].strip()
                    if val and val != 'NULL':
                        return int(val) + 1
        return 1
    
    def create_kosdb_user(self, username: str, password: str, 
                          is_admin: bool = False) -> Tuple[bool, str]:
        """
        Create user directly in KosDB.
        
        Args:
            username: Username
            password: Plain text password
            is_admin: Whether user is admin
        
        Returns:
            Tuple of (success, message)
        """
        from webcms.auth.password import PasswordHasher
        
        # Hash password
        hasher = PasswordHasher()
        password_hash = hasher.hash_password(password)
        
        # Check if user exists
        result = self.kosdb.select(
            "_users",
            where={"username": username}
        )
        
        if result["rows"]:
            return False, f"User '{username}' already exists"
        
        # Insert user
        self.kosdb.insert("_users", [
            self._get_next_user_id(),
            username,
            "",  # email
            password_hash,
            1 if is_admin else 0,
            1,  # is_active
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat()
        ])
        
        # Grant admin privileges if admin
        if is_admin:
            self.kosdb.insert("_privileges", [
                self._get_next_privilege_id(),
                username,
                "*",
                "*",
                "ALL",
                "system",
                datetime.utcnow().isoformat()
            ])
        
        return True, f"User '{username}' created in KosDB"
    
    def delete_kosdb_user(self, username: str) -> bool:
        """
        Delete user from KosDB.
        
        Args:
            username: Username to delete
        
        Returns:
            True if deleted
        """
        # Delete privileges first
        self.kosdb.execute(f"DELETE FROM _privileges WHERE username='{username}'")
        
        # Delete user
        result = self.kosdb.execute(f"DELETE FROM _users WHERE username='{username}'")
        
        return "Deleted" in result or "deleted" in result
    
    def list_kosdb_users(self) -> List[Dict]:
        """
        List all KosDB users.
        
        Returns:
            List of user dictionaries
        """
        result = self.kosdb.execute("SELECT * FROM _users")
        users = []
        
        # Parse table result
        lines = result.split('\n')
        in_table = False
        columns = []
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('+-') and line.endswith('-+'):
                in_table = not in_table
                continue
            
            if in_table and line.startswith('|'):
                cells = [c.strip() for c in line.split('|')[1:-1]]
                
                if not columns:
                    columns = cells
                else:
                    user = {}
                    for i, col in enumerate(columns):
                        if i < len(cells):
                            user[col] = cells[i]
                    if user.get('id'):
                        users.append(user)
        
        return users


class KosDBAuthenticator:
    """
    Authenticator that uses KosDB as the backend.
    Can be used as drop-in replacement for WebCMS auth.
    """
    
    def __init__(self, kosdb_config: KosDBConfig):
        self.kosdb = KosDBClient(kosdb_config)
        self.bridge = KosDBAuthBridge(self.kosdb, sync_mode=False)
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[Dict], List[str]]:
        """
        Authenticate user.
        
        Returns:
            Tuple of (success, user_info, privileges)
        """
        success, user_data = self.bridge.authenticate_against_kosdb(username, password)
        
        if not success:
            return False, None, []
        
        # Get privileges
        privileges = self._get_user_privileges(username)
        
        return True, user_data, privileges
    
    def _get_user_privileges(self, username: str) -> List[str]:
        """Get user privileges from KosDB."""
        result = self.kosdb.select(
            "_privileges",
            where={"username": username}
        )
        
        privs = []
        for row in result.get("rows", []):
            priv_str = row[4] if len(row) > 4 else ""
            privs.extend(priv_str.split(','))
        
        return list(set(privs))
    
    def create_user(self, username: str, password: str, 
                    is_admin: bool = False) -> Tuple[bool, str]:
        """Create user."""
        return self.bridge.create_kosdb_user(username, password, is_admin)
    
    def delete_user(self, username: str) -> bool:
        """Delete user."""
        return self.bridge.delete_kosdb_user(username)
    
    def check_privilege(self, username: str, db: str, table: str, 
                        privilege: str) -> bool:
        """Check user privilege."""
        return self.bridge.check_kosdb_privilege(username, db, table, privilege)
    
    def close(self):
        """Close connection."""
        self.kosdb.close()