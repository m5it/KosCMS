"""
Search Index Model

SQLAlchemy model for search index metadata.
Tracks indexed content for management.
"""

from sqlalchemy import Column, String, DateTime, Integer, Index
from sqlalchemy.orm import declarative_base

from .base import Base, TimestampMixin


class SearchIndex(Base, TimestampMixin):
    """Search index metadata."""
    
    __tablename__ = 'search_index_meta'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(String(36), nullable=False, index=True)
    content_type = Column(String(20), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    indexed_at = Column(DateTime, nullable=False)
    
    # Composite index for lookups
    __table_args__ = (
        Index('idx_search_content', 'content_type', 'content_id', unique=True),
    )
    
    def __repr__(self):
        return f"<SearchIndex {self.content_type}:{self.content_id}>"
