"""
User Manager

User and role management with KosDB support.
"""

import uuid
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any


class UserManager:
    """User and role management with KosDB persistence."""
    
    def __init__(self, db=None):
        self.db = db
        self._users: Dict[str, Dict] = {}
        self._roles: Dict[str, Dict] = {}
        self._ensure_tables()
        self._load_from_kosdb()
    
    def _is_kosdb(self) -> bool:
        """Check if database is KosDB."""
        if self.db is None:
            return False
        has_methods = all(
            hasattr(self.db, method) 
            for method in ['execute', 'query', 'list_tables']
        )
        return has_methods
    
    def _ensure_tables(self):
        """Ensure user tables exist."""
        if not self.db or not self._is_kosdb():
            return
        
        try:
            tables = self.db.list_tables()
        except Exception:
            tables = []
        
        # Users table
        if 'users' not in tables:
            try:
                self.db.execute("""
                    CREATE TABLE users (
                        id TEXT PRIMARY KEY,
                        username TEXT UNIQUE,
                        email TEXT UNIQUE,
                        password_hash TEXT,
                        full_name TEXT,
                        is_active TEXT DEFAULT '1',
                        is_superuser TEXT DEFAULT '0',
                        created_at TEXT,
                        updated_at TEXT
                    )
                """)
            except Exception:
                pass
        
        # Roles table
        if 'roles' not in tables:
            try:
                self.db.execute("""
                    CREATE TABLE roles (
                        id TEXT PRIMARY KEY,
                        name TEXT UNIQUE,
                        description TEXT,
                        permissions TEXT,
                        created_at TEXT
                    )
                """)
            except Exception:
                pass
        
        # User roles table
        if 'user_roles' not in tables:
            try:
                self.db.execute("""
                    CREATE TABLE user_roles (
                        user_id TEXT,
                        role_id TEXT,
                        PRIMARY KEY (user_id, role_id)
                    )
                """)
            except Exception:
                pass
    
    def _load_from_kosdb(self):
        """Load users and roles from KosDB."""
        if not self.db or not self._is_kosdb():
            return
        
        try:
            # Load users
            result = self.db.query("SELECT * FROM users")
            for row in result.get('rows', []):
                self._users[row['id']] = {
                    "id": row['id'],
                    "username": row['username'],
                    "email": row['email'],
                    "full_name": row.get('full_name', ''),
                    "is_active": row.get('is_active') == '1',
                    "is_superuser": row.get('is_superuser') == '1',
                    "created_at": row.get('created_at')
                }
        except Exception:
            pass
        
        try:
            # Load roles
            import json
            result = self.db.query("SELECT * FROM roles")
            for row in result.get('rows', []):
                self._roles[row['id']] = {
                    "id": row['id'],
                    "name": row['name'],
                    "description": row.get('description', ''),
                    "permissions": json.loads(row['permissions']) if row.get('permissions') else []
                }
        except Exception:
            pass
    
    def _save_user_to_kosdb(self, user: Dict):
        """Save user to KosDB."""
        if not self.db or not self._is_kosdb():
            return
        
        now = datetime.utcnow().isoformat()
        try:
            result = self.db.query(f"SELECT id FROM users WHERE id='{user['id']}'")
            
            if result.get('rows'):
                # Update
                self.db.execute(f"""
                    UPDATE users SET
                        username='{user['username']}',
                        email='{user['email']}',
                        full_name='{user.get('full_name', '')}',
                        is_active='{1 if user.get('is_active') else 0}',
                        is_superuser='{1 if user.get('is_superuser') else 0}',
                        updated_at='{now}'
                    WHERE id='{user['id']}'
                """)
            else:
                # Insert
                self.db.execute(f"""
                    INSERT INTO users 
                    (id, username, email, full_name, is_active, is_superuser, created_at, updated_at)
                    VALUES (
                        '{user['id']}',
                        '{user['username']}',
                        '{user['email']}',
                        '{user.get('full_name', '')}',
                        '{1 if user.get('is_active') else 0}',
                        '{1 if user.get('is_superuser') else 0}',
                        '{now}',
                        '{now}'
                    )
                """)
        except Exception:
            pass
    
    def _delete_user_from_kosdb(self, user_id: str):
        """Delete user from KosDB."""
        if not self.db or not self._is_kosdb():
            return
        
        try:
            self.db.execute(f"DELETE FROM users WHERE id='{user_id}'")
            self.db.execute(f"DELETE FROM user_roles WHERE user_id='{user_id}'")
        except Exception:
            pass
    
    def list_users(self) -> List[Dict]:
        """List all users."""
        return list(self._users.values())
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID."""
        return self._users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        for user in self._users.values():
            if user['username'] == username:
                return user
        return None
    
    def create_user(self, username: str, email: str, password: str,
                    full_name: str = "", is_superuser: bool = False) -> Dict:
        """Create new user."""
        user_id = str(uuid.uuid4())
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        user = {
            "id": user_id,
            "username": username,
            "email": email,
            "full_name": full_name,
            "is_active": True,
            "is_superuser": is_superuser,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self._users[user_id] = user
        self._save_user_to_kosdb(user)
        return user
    
    def update_user(self, user_id: str, **updates) -> Optional[Dict]:
        """Update user."""
        user = self._users.get(user_id)
        if not user:
            return None
        
        for key, value in updates.items():
            if key in user:
                user[key] = value
        
        self._save_user_to_kosdb(user)
        return user
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user."""
        if user_id in self._users:
            del self._users[user_id]
            self._delete_user_from_kosdb(user_id)
            return True
        return False
    
    def list_roles(self) -> List[Dict]:
        """List all roles."""
        return [
            {
                "id": role['id'],
                "name": role['name'],
                "description": role.get('description', '')
            }
            for role in self._roles.values()
        ]
    
    def get_role(self, role_id: str) -> Optional[Dict]:
        """Get role by ID."""
        return self._roles.get(role_id)
    
    def create_role(self, name: str, description: str = "",
                    permissions: List[str] = None) -> Dict:
        """Create new role."""
        import json
        role_id = str(uuid.uuid4())
        
        role = {
            "id": role_id,
            "name": name,
            "description": description,
            "permissions": permissions or []
        }
        
        self._roles[role_id] = role
        
        # Save to KosDB
        if self.db and self._is_kosdb():
            try:
                self.db.execute(f"""
                    INSERT INTO roles (id, name, description, permissions, created_at)
                    VALUES (
                        '{role_id}',
                        '{name}',
                        '{description}',
                        '{json.dumps(permissions or [])}',
                        '{datetime.utcnow().isoformat()}'
                    )
                """)
            except Exception:
                pass
        
        return role
    
    def delete_role(self, role_id: str) -> bool:
        """Delete role."""
        if role_id in self._roles:
            del self._roles[role_id]
            
            if self.db and self._is_kosdb():
                try:
                    self.db.execute(f"DELETE FROM roles WHERE id='{role_id}'")
                except Exception:
                    pass
            
            return True
        return False
    
    def assign_role(self, user_id: str, role_id: str) -> bool:
        """Assign role to user."""
        if self.db and self._is_kosdb():
            try:
                self.db.execute(f"""
                    INSERT OR REPLACE INTO user_roles (user_id, role_id)
                    VALUES ('{user_id}', '{role_id}')
                """)
                return True
            except Exception:
                pass
        return False
    
    def remove_role(self, user_id: str, role_id: str) -> bool:
        """Remove role from user."""
        if self.db and self._is_kosdb():
            try:
                self.db.execute(f"""
                    DELETE FROM user_roles 
                    WHERE user_id='{user_id}' AND role_id='{role_id}'
                """)
                return True
            except Exception:
                pass
        return False
    
    def get_user_roles(self, user_id: str) -> List[str]:
        """Get user roles."""
        if self.db and self._is_kosdb():
            try:
                result = self.db.query(f"""
                    SELECT r.name FROM roles r
                    JOIN user_roles ur ON r.id = ur.role_id
                    WHERE ur.user_id = '{user_id}'
                """)
                return [row['name'] for row in result.get('rows', [])]
            except Exception:
                pass
        return []
