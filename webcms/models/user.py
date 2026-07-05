"""
User Models

User, Role, Permission with many-to-many relationships.
"""

from sqlalchemy import Column, String, Boolean, Text, Table, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin


# Association table for User-Role many-to-many
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', String(36), ForeignKey('users.id'), primary_key=True),
    Column('role_id', String(36), ForeignKey('roles.id'), primary_key=True)
)


class Permission:
    """Permission constants."""
    CREATE_POST = 'create_post'
    EDIT_POST = 'edit_post'
    DELETE_POST = 'delete_post'
    PUBLISH_POST = 'publish_post'
    CREATE_PAGE = 'create_page'
    EDIT_PAGE = 'edit_page'
    DELETE_PAGE = 'delete_page'
    MANAGE_USERS = 'manage_users'
    MANAGE_ROLES = 'manage_roles'
    UPLOAD_MEDIA = 'upload_media'
    DELETE_MEDIA = 'delete_media'
    MANAGE_PLUGINS = 'manage_plugins'
    MANAGE_THEMES = 'manage_themes'
    VIEW_ADMIN = 'view_admin'
    MANAGE_SETTINGS = 'manage_settings'


class User(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """User model."""
    
    __tablename__ = 'users'
    
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    last_login = Column(String(50), nullable=True)
    login_count = Column(String(10), default='0')
    
    # Relationships
    roles = relationship('Role', secondary=user_roles, back_populates='users')
    posts = relationship('Post', back_populates='author', 
                        foreign_keys='Post.author_id')
    pages = relationship('Page', back_populates='author',
                        foreign_keys='Page.author_id')
    audit_logs = relationship('AuditLog', back_populates='user')
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has permission."""
        if self.is_superuser:
            return True
        
        for role in self.roles:
            if permission in role.permissions_list:
                return True
        return False
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has role."""
        return any(r.name == role_name for r in self.roles)
    
    def __repr__(self):
        return f"<User {self.username}>"


class Role(Base, UUIDMixin, TimestampMixin):
    """Role model."""
    
    __tablename__ = 'roles'
    
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    permissions = Column(Text, default='')  # Comma-separated permissions
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    users = relationship('User', secondary=user_roles, back_populates='roles')
    
    @property
    def permissions_list(self):
        """Get permissions as list."""
        return [p.strip() for p in self.permissions.split(',') if p.strip()]
    
    def add_permission(self, permission: str):
        """Add permission to role."""
        perms = self.permissions_list
        if permission not in perms:
            perms.append(permission)
            self.permissions = ','.join(perms)
    
    def remove_permission(self, permission: str):
        """Remove permission from role."""
        perms = [p for p in self.permissions_list if p != permission]
        self.permissions = ','.join(perms)
    
    def __repr__(self):
        return f"<Role {self.name}>"


class UserRole:
    """UserRole association."""
    pass