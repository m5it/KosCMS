"""
Media Manager

File uploads with validation and image processing.
Includes WebP conversion support.
"""

import os
try:
    import imghdr
except ModuleNotFoundError:
    from webcms.compat import imghdr
from datetime import datetime
from pathlib import Path
from pathlib import Path
from typing import BinaryIO, List, Optional, Tuple
from PIL import Image

try:
    from sqlalchemy.orm import Session
    from webcms.models.media import Media
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

from .storage import StorageBackend, LocalStorage, WebPSupport
from .transform import ImageTransform


class WebPConfig:
    """WebP conversion configuration."""
    
    def __init__(self, quality: int = 85, method: int = 4,
                 lossless: bool = False):
        self.quality = quality
        self.method = method  # 0-6, higher = slower but better
        self.lossless = lossless


class MediaManager:
    """Media file management with WebP support."""
    
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
    ALLOWED_MIME_TYPES = {
        'image/jpeg', 'image/png', 'image/gif', 
        'image/webp', 'image/svg+xml'
    }
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self, db: Optional[Session] = None, storage: Optional[StorageBackend] = None):
        self.db = db
        self.storage = storage or LocalStorage("media")
        self.webp_config = WebPConfig()
        self.transform = ImageTransform(webp_quality=85)
        self._in_memory_files = []
    
    def _is_kosdb(self) -> bool:
        """Check if database is KosDB."""
        if self.db is None:
            return False
        has_methods = all(
            hasattr(self.db, method) 
            for method in ['execute', 'query', 'list_tables']
        )
        return has_methods
    
    def _is_sqlalchemy(self) -> bool:
        """Check if database is SQLAlchemy."""
        if not HAS_SQLALCHEMY:
            return False
        return hasattr(self.db, 'query') and callable(getattr(self.db, 'query'))
    
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
        Process and optimize image using ImageTransform.
        
        Returns:
            Tuple of (width, height)
        """
        try:
            with Image.open(file_path) as img:
                original_width, original_height = img.size
                
                # Resize if needed
                if original_width > max_width or original_height > max_height:
                    self.transform.resize(file_path, file_path, 
                                       (max_width, max_height))
                
                # Get final dimensions
                with Image.open(file_path) as final_img:
                    return final_img.size
        except Exception as e:
            print(f"Error processing image: {e}")
            return (0, 0)
    
    def convert_to_webp(self, file_path: Path, quality: Optional[int] = None) -> Optional[Path]:
        """
        Convert image to WebP format.
        
        Returns:
            Path to WebP file or None
        """
        try:
            webp_path = file_path.with_suffix('.webp')
            self.transform.convert_to_webp(file_path, webp_path, 
                                        quality or self.webp_config.quality)
            return webp_path
        except Exception as e:
            print(f"Error converting to WebP: {e}")
            return None
    
    def get_webp_url(self, original_url: str, accept_header: str) -> str:
        """
        Get WebP URL if browser supports it.
        
        Returns:
            WebP URL or original URL
        """
        if not WebPSupport.supports_webp(accept_header):
            return original_url
        
        # Try to find WebP version
        original_path = Path(original_url)
        webp_path = original_path.with_suffix('.webp')
        
        if self.storage.exists(str(webp_path.relative_to(self.storage.base_path))):
            return str(webp_path)
        
        return original_url
    
    def upload(self, file_data: BinaryIO, filename: str,
               content_type: str, user_id: str,
               folder: str = "") -> Dict:
        """
        Upload and process media file.
        
        Returns:
            Media metadata dict
        """
        # Validate
        file_size = len(file_data.read())
        file_data.seek(0)
        
        is_valid, error = self.validate_file(filename, file_size, content_type)
        if not is_valid:
            return {"error": error}
        
        # Save to storage
        url = self.storage.save(file_data, filename, folder)
        
        # Get file info
        file_path = Path(self.storage.base_path) / folder / filename
        width, height = 0, 0
        
        if content_type.startswith('image/'):
            width, height = self.process_image(file_path)
            
            # Create WebP version
            if content_type in ['image/jpeg', 'image/png']:
                self.convert_to_webp(file_path)
        
        # Create media record
        media_data = {
            "id": str(datetime.utcnow().timestamp()),
            "filename": filename,
            "url": url,
            "content_type": content_type,
            "size": file_size,
            "width": width,
            "height": height,
            "user_id": user_id,
            "folder": folder,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self._in_memory_files.append(media_data)
        return media_data
    
    def delete(self, media_id: str) -> bool:
        """Delete media file."""
        # Find in memory
        for i, media in enumerate(self._in_memory_files):
            if media['id'] == media_id:
                # Delete from storage
                try:
                    filename = media['filename']
                    folder = media.get('folder', '')
                    path = os.path.join(folder, filename) if folder else filename
                    self.storage.delete(path)
                except Exception:
                    pass
                
                self._in_memory_files.pop(i)
                return True
        
        return False
    
    def get_file(self, media_id: str) -> Optional[Dict]:
        """Get media file metadata."""
        for media in self._in_memory_files:
            if media['id'] == media_id:
                return media
        return None
    
    def list_files(self, folder: str = "", limit: int = 20, offset: int = 0) -> List[Dict]:
        """List media files."""
        files = self._in_memory_files
        
        if folder:
            files = [f for f in files if f.get('folder') == folder]
        
        return files[offset:offset+limit]
    
    def get_usage(self, media_id: str) -> List[Dict]:
        """Get usage information for media file."""
        # Placeholder - would query content for references
        return []
    
    def get_stats(self) -> Dict:
        """Get media statistics."""
        total_size = sum(f.get('size', 0) for f in self._in_memory_files)
        images = sum(1 for f in self._in_memory_files 
                    if f.get('content_type', '').startswith('image/'))
        
        return {
            "total_files": len(self._in_memory_files),
            "total_size": total_size,
            "images": images,
            "storage_used_mb": round(total_size / (1024 * 1024), 2)
        }
