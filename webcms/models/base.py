"""
Base Model Classes

Mixins for soft delete, timestamps, and audit logging.
"""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Column, DateTime, Boolean, String, event
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TimestampMixin:
    """Add created_at and updated_at timestamps."""
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, 
                       onupdate=datetime.utcnow, nullable=False)


class SoftDeleteMixin:
    """Add soft delete support."""
    
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    def soft_delete(self):
        """Mark as deleted."""
        self.deleted_at = datetime.utcnow()
        self.is_deleted = True
    
    def restore(self):
        """Restore from soft delete."""
        self.deleted_at = None
        self.is_deleted = False


class AuditMixin:
    """Add audit fields."""
    
    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True)
    deleted_by = Column(String(36), nullable=True)


class UUIDMixin:
    """Add UUID primary key."""
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))


# Event listeners for automatic timestamp updates
@event.listens_for(TimestampMixin, 'before_update', propagate=True)
def receive_before_update(mapper, connection, target):
    """Update updated_at on modification."""
    target.updated_at = datetime.utcnow()