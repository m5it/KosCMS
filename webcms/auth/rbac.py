"""
Role-Based Access Control (RBAC)

User roles and permissions management.
"""

from enum import Enum, auto
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field


class Permission(Enum):
    """System permissions."""
    # Content permissions
    CREATE_POST = "create_post"
    EDIT_POST = "edit_post"
    DELETE_POST = "delete_post"
    PUBLISH_POST = "publish_post"
    
    # Page permissions
    CREATE_PAGE = "create_page"
    EDIT_PAGE = "edit_page"
    DELETE_PAGE = "delete_page"
    
    # User permissions
    MANAGE_USERS = "manage_users"
    EDIT_USER = "edit_user"
    DELETE_USER = "delete_user"
    
    # Media permissions
    UPLOAD_MEDIA = "upload_media"
    DELETE_MEDIA = "delete_media"
    
    # Plugin permissions
    MANAGE_PLUGINS = "manage_plugins"
    INSTALL_PLUGIN = "install_plugin"
    
    # Theme permissions
    MANAGE_THEMES = "manage_themes"
    EDIT_THEME = "edit_theme"
    
    # System permissions
    VIEW_ADMIN = "view_admin"
    MANAGE_SETTINGS = "manage_settings"
    VIEW_LOGS = "view_logs"


@dataclass
class Role:
    """User role with permissions."""
    name: str
    description: str
    permissions: Set[Permission] = field(default_factory=set)
    is_default: bool = False
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if role has permission."""
        return permission in self.permissions
    
    def add_permission(self, permission: Permission) -> None:
        """Add permission to role."""
        self.permissions.add(permission)
    
    def remove_permission(self, permission: Permission) -> None:
        """Remove permission from role."""
        self.permissions.discard(permission)


class RBACManager:
    """Role and permission management."""
    
    def __init__(self):
        self.roles: Dict[str, Role] = {}
        self._create_default_roles()
    
    def _create_default_roles(self) -> None:
        """Create default system roles."""
        # Admin - full access
        admin = Role(
            name="admin",
            description="Administrator with full access",
            permissions=set(Permission),
            is_default=False
        )
        self.roles["admin"] = admin
        
        # Editor - content management
        editor = Role(
            name="editor",
            description="Can create and edit all content",
            permissions={
                Permission.CREATE_POST, Permission.EDIT_POST,
                Permission.DELETE_POST, Permission.PUBLISH_POST,
                Permission.CREATE_PAGE, Permission.EDIT_PAGE,
                Permission.DELETE_PAGE, Permission.UPLOAD_MEDIA,
                Permission.DELETE_MEDIA, Permission.VIEW_ADMIN
            },
            is_default=False
        )
        self.roles["editor"] = editor
        
        # Author - own content only
        author = Role(
            name="author",
            description="Can create and edit own posts",
            permissions={
                Permission.CREATE_POST, Permission.EDIT_POST,
                Permission.UPLOAD_MEDIA, Permission.VIEW_ADMIN
            },
            is_default=False
        )
        self.roles["author"] = author
        
        # Subscriber - read only
        subscriber = Role(
            name="subscriber",
            description="Can view content and comment",
            permissions=set(),
            is_default=True
        )
        self.roles["subscriber"] = subscriber
    
    def get_role(self, name: str) -> Optional[Role]:
        """Get role by name."""
        return self.roles.get(name)
    
    def create_role(self, name: str, description: str, 
                    permissions: List[Permission]) -> Role:
        """
        Create new role.
        
        Args:
            name: Role identifier
            description: Role description
            permissions: List of permissions
        
        Returns:
            Created role
        """
        if name in self.roles:
            raise ValueError(f"Role '{name}' already exists")
        
        role = Role(
            name=name,
            description=description,
            permissions=set(permissions)
        )
        self.roles[name] = role
        return role
    
    def delete_role(self, name: str) -> bool:
        """
        Delete role.
        
        Returns:
            True if deleted, False if default role
        """
        if name in self.roles:
            if self.roles[name].is_default:
                return False
            del self.roles[name]
            return True
        return False
    
    def get_all_roles(self) -> List[Role]:
        """Get all roles."""
        return list(self.roles.values())
    
    def check_permission(self, user_roles: List[str], 
                         permission: Permission) -> bool:
        """
        Check if user has permission through any role.
        
        Args:
            user_roles: List of user's role names
            permission: Permission to check
        
        Returns:
            True if user has permission
        """
        for role_name in user_roles:
            role = self.get_role(role_name)
            if role and role.has_permission(permission):
                return True
        return False
    
    def get_user_permissions(self, user_roles: List[str]) -> Set[Permission]:
        """
        Get all permissions for user.
        
        Args:
            user_roles: List of user's role names
        
        Returns:
            Set of all permissions
        """
        permissions: Set[Permission] = set()
        for role_name in user_roles:
            role = self.get_role(role_name)
            if role:
                permissions.update(role.permissions)
        return permissions