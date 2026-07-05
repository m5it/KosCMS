"""
Media Manager

File uploads with validation and image processing.
"""

import os
import imghdr
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, List, Optional, Tuple
from PIL import Image

from sqlalchemy.orm import Session

from webcms.models.media import Media
from .storage import StorageBackend, LocalStorage


class MediaManager:
    """Media file management."""
    
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
    ALLOWED_MIME_TYPES = {
        'image/jpeg', 'image/png', 'image/gif', 
        'image/webp', 'image/svg+xml'
    }
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self, db: Session, storage: Optional[StorageBackend] = None):
        self.db = db
        self.storage = storage or LocalStorage("media")
    
    def validate_file(self, filename: str, file_size: int,
                      content_type: str) -> Tuple[bool, str]:
        """
        Validate uploaded file.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check extension
        ext = Path(filename).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            return False, f"File type '{ext}' not allowed"
        
        # Check size
        if file_size > self.MAX_FILE_SIZE:
            return False, f"File too large (max {self.MAX_FILE_SIZE / 1024 / 1024}MB)"
        
        # Check MIME type
        if content_type not in self.ALLOWED_MIME_TYPES:
            return False, f"Content type '{content_type}' not allowed"
        
        return True, ""
    
    def process_image(self, file_path: Path, max_width: int = 1920,
                      max_height: int = 1080) -> Tuple[int, int]:
        """
        Process and optimize image.
        
        Returns:
            Tuple of (width, height)
        """
        try:
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if too large
                if img.width > max_width or img.height > max_height:
                    img.thumbnail((max_width, max_height), Image.LANCZOS)
                
                # Save optimized
                img.save(file_path, optimize=True, quality=85)
                
                return img.width, img.height
                
        except Exception as e:
            print(f"Image processing error: {e}")
            return 0, 0
    
    def create_thumbnail(self, file_path: Path, size: Tuple[int, int] = (300, 300)) -> Path:
        """Create thumbnail."""
        thumb_path = file_path.parent / f"{file_path.stem}_thumb{file_path.suffix}"
        
        try:
            with Image.open(file_path) as img:
                img.thumbnail(size, Image.LANCZOS)
                img.save(thumb_path, optimize=True, quality=80)
                return thumb_path
        except Exception as e:
            print(f"Thumbnail error: {e}")
            return file_path
    
    def upload(self, file_data: BinaryIO, filename: str,
               content_type: str, user_id: str,
               alt_text: str = None, caption: str = None) -> Optional[Media]:
        """
        Upload and process file.
        
        Args:
            file_data: File binary data
            filename: Original filename
            content_type: MIME type
            user_id: Uploader user ID
            alt_text: Image alt text
            caption: Image caption
        
        Returns:
            Media object or None
        """
        # Get file size
        file_data.seek(0, 2)  # Seek to end
        file_size = file_data.tell()
        file_data.seek(0)  # Reset to beginning
        
        # Validate
        is_valid, error = self.validate_file(filename, file_size, content_type)
        if not is_valid:
            raise ValueError(error)
        
        # Generate safe filename
        safe_name = self._sanitize_filename(filename)
        
        # Save to storage
        folder = datetime.now().strftime("%Y/%m")
        relative_path = self.storage.save(file_data, safe_name, folder)
        
        # Process image
        width, height = 0, 0
        if content_type.startswith("image/"):
            full_path = Path(self.storage.base_path) / relative_path
            width, height = self.process_image(full_path)
            
            # Create thumbnail
            self.create_thumbnail(full_path)
        
        # Create database record
        media = Media(
            filename=Path(relative_path).name,
            original_filename=filename,
            file_path=relative_path,
            file_url=self.storage.get_url(relative_path),
            file_size=file_size,
            mime_type=content_type,
            file_extension=Path(filename).suffix,
            width=width,
            height=height,
            alt_text=alt_text,
            caption=caption,
            storage_type="local",
            uploaded_by=user_id
        )
        
        self.db.add(media)
        self.db.commit()
        self.db.refresh(media)
        
        return media
    
    def get_media(self, media_id: str) -> Optional[Media]:
        """Get media by ID."""
        return self.db.query(Media).filter(
            Media.id == media_id,
            Media.is_deleted == False
        ).first()
    
    def list_media(self, limit: int = 50, offset: int = 0) -> List[Media]:
        """List media files."""
        return self.db.query(Media).filter(
            Media.is_deleted == False
        ).order_by(
            Media.created_at.desc()
        ).offset(offset).limit(limit).all()
    
    def delete_media(self, media_id: str, soft: bool = True) -> bool:
        """Delete media file."""
        media = self.get_media(media_id)
        if not media:
            return False
        
        if soft:
            media.soft_delete()
        else:
            # Delete from storage
            self.storage.delete(media.file_path)
            self.db.delete(media)
        
        self.db.commit()
        return True
    
    def _sanitize_filename(self, filename: str) -> str:
        """Create safe filename."""
        from werkzeug.utils import secure_filename
        import uuid
        
        safe = secure_filename(filename)
        name, ext = os.path.splitext(safe)
        
        # Add UUID to prevent collisions
        return f"{name}_{uuid.uuid4().hex[:8]}{ext}"