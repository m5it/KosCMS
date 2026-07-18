"""
System Models

Plugins, Themes, Settings and Audit Logging.
"""

from sqlalchemy import Column, String, Text, Boolean, JSON
from sqlalchemy.orm import relationship

from .base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin


class Plugin(Base, UUIDMixin, TimestampMixin):
    """Plugin model."""
    
    __tablename__ = 'plugins'
    
    name = Column(String(100), unique=True, nullable=False)
    version = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    author = Column(String(100), nullable=True)
    
    package_name = Column(String(100), nullable=False)
    entry_point = Column(String(100), nullable=False)
    
    is_active = Column(Boolean, default=False, nullable=False)
    is_builtin = Column(Boolean, default=False, nullable=False)
    
    config = Column(JSON, default=dict, nullable=False)
    permissions = Column(Text, default='', nullable=True)
    
    def __repr__(self):
        return f"<Plugin {self.name}>"


class Theme(Base, UUIDMixin, TimestampMixin):
    """Installed theme model."""
    
    __tablename__ = 'themes'
    
    name = Column(String(100), unique=True, nullable=False)
    version = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    author = Column(String(100), nullable=True)
    
    directory_name = Column(String(100), nullable=False)
    
    is_active = Column(Boolean, default=False, nullable=False)
    is_builtin = Column(Boolean, default=False, nullable=False)
    
    config = Column(JSON, default=dict, nullable=False)
    
    def __repr__(self):
        return f"<Theme {self.name}>"


class AuditLog(Base, UUIDMixin, TimestampMixin):
    """Audit log for system events."""
    
    __tablename__ = 'audit_logs'
    
    action = Column(String(50), nullable=False)  # create, update, delete, login, logout
    entity_type = Column(String(50), nullable=False)  # user, post, page, etc
    entity_id = Column(String(36), nullable=True)
    
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    user_id = Column(String(36), nullable=True)
    user = relationship('User', foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<AuditLog {self.action} {self.entity_type}>"


class Setting(Base, UUIDMixin, TimestampMixin):
    """System setting key/value store."""
    
    __tablename__ = 'settings'
    
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    type = Column(String(20), default='str', nullable=False)  # str, int, float, bool
