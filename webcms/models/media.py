"""
Media Models

File uploads and media library.
"""

from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin


class Media(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Media file model."""
    
    __tablename__ = 'media'
    
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_url = Column(String(500), nullable=False)
    
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_extension = Column(String(20), nullable=False)
    
    width = Column(Integer, nullable=True)  # For images
    height = Column(Integer, nullable=True)
    
    alt_text = Column(String(255), nullable=True)
    caption = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    
    storage_type = Column(String(20), default='local', nullable=False)  # local, s3, azure
    
    # Relationships
    uploaded_by = Column(String(36), ForeignKey('users.id'), nullable=False)
    uploader = relationship('User')
    
    def __repr__(self):
        return f"<Media {self.filename}>"


class MediaFolder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Media folder organization."""
    
    __tablename__ = 'media_folders'
    
    name = Column(String(100), nullable=False)
    path = Column(String(500), nullable=False)
    
    parent_id = Column(String(36), ForeignKey('media_folders.id'), nullable=True)
    parent = relationship('MediaFolder', remote_side='MediaFolder.id',
                         backref='children')
    
    def __repr__(self):
        return f"<MediaFolder {self.name}>"