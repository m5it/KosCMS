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

from sqlalchemy.orm import Session

from webcms.models.media import Media
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
    
    def __init__(self, db: Session, storage: Optional[StorageBackend] = None):
        self.db = db
        self.storage = storage or LocalStorage("media")
        self.webp_config = WebPConfig()
        self.transform = ImageTransform(webp_quality=85)
    
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
                    return final_img.width, final_img.height
                
        except Exception as e:
            print(f"Image processing error: {e}")
            return 0, 0
    
    def create_thumbnail(self, file_path: Path, 
                         size: Tuple[int, int] = (300, 300)) -> Path:
        """Create thumbnail using ImageTransform."""
        thumb_path = file_path.parent / f"{file_path.stem}_thumb{file_path.suffix}"
        
        if self.transform.resize(file_path, thumb_path, size):
            return thumb_path
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
    
    def convert_to_webp(self, media: Media, 
                        config: Optional[WebPConfig] = None) -> Optional[Media]:
        """
        Convert image to WebP format.
        
        Args:
            media: Source media object
            config: WebP conversion config
        
        Returns:
            New Media object for WebP version
        """
        if not media.mime_type.startswith("image/"):
            return None
        
        config = config or self.webp_config
        
        try:
            source_path = Path(self.storage.base_path) / media.file_path
            
            # Generate WebP filename
            base_name = Path(media.filename).stem
            webp_filename = f"{base_name}.webp"
            folder = Path(media.file_path).parent
            
            # Create WebP version using transform
            webp_path = Path(self.storage.base_path) / folder / webp_filename
            
            if self.transform.convert_to_webp(source_path, webp_path, 
                                              config.quality):
                
                # Create media record
                webp_media = Media(
                    filename=webp_filename,
                    original_filename=webp_filename,
                    file_path=str(Path(folder) / webp_filename),
                    file_url=self.storage.get_url(str(Path(folder) / webp_filename)),
                    file_size=webp_path.stat().st_size,
                    mime_type="image/webp",
                    file_extension=".webp",
                    width=media.width,
                    height=media.height,
                    alt_text=media.alt_text,
                    caption=media.caption,
                    storage_type="local",
                    uploaded_by=media.uploaded_by,
                    parent_id=media.id  # Link to original
                )
                
                self.db.add(webp_media)
                self.db.commit()
                self.db.refresh(webp_media)
                
                return webp_media
            
        except Exception as e:
            print(f"WebP conversion error: {e}")
        
        return None
    
    def generate_variations_with_webp(self, media: Media,
                                      sizes: List[Tuple[int, int]] = None) -> List[Media]:
        """
        Generate image variations with WebP versions.
        
        Args:
            media: Source media object
            sizes: List of (width, height) tuples
        
        Returns:
            List of created media objects
        """
        if not media.mime_type.startswith("image/"):
            return []
        
        sizes = sizes or [(300, 300), (600, 600), (1200, 800)]
        created = []
        
        try:
            source_path = Path(self.storage.base_path) / media.file_path
            
            for width, height in sizes:
                # Generate JPEG version
                jpeg = self._create_variation(media, source_path, 
                                              width, height, "JPEG")
                if jpeg:
                    created.append(jpeg)
                    
                    # Generate WebP version
                    webp = self._create_variation(media, source_path,
                                                  width, height, "WEBP")
                    if webp:
                        created.append(webp)
            
            return created
            
        except Exception as e:
            print(f"Variation generation error: {e}")
            return created
    
    def _create_variation(self, media: Media, source_path: Path,
                        width: int, height: int, 
                        format_type: str) -> Optional[Media]:
        """Create single image variation."""
        try:
            # Generate filename
            base_name = Path(media.filename).stem
            ext = ".webp" if format_type == "WEBP" else ".jpg"
            var_filename = f"{base_name}_{width}x{height}{ext}"
            folder = Path(media.file_path).parent
            var_path = Path(self.storage.base_path) / folder / var_filename
            
            # Use transform for resize and conversion
            if format_type == "WEBP":
                success = self.transform.convert_to_webp(
                    source_path, var_path, self.webp_config.quality
                )
                mime = "image/webp"
            else:
                success = self.transform.resize(
                    source_path, var_path, (width, height), "JPEG"
                )
                mime = "image/jpeg"
            
            if not success:
                return None
            
            # Get dimensions
            info = self.transform.get_image_info(var_path)
            
            # Create media record
            var_media = Media(
                filename=var_filename,
                original_filename=var_filename,
                file_path=str(Path(folder) / var_filename),
                file_url=self.storage.get_url(str(Path(folder) / var_filename)),
                file_size=var_path.stat().st_size,
                mime_type=mime,
                file_extension=ext,
                width=info.get("width", width),
                height=info.get("height", height),
                alt_text=media.alt_text,
                caption=media.caption,
                storage_type="local",
                uploaded_by=media.uploaded_by,
                parent_id=media.id
            )
            
            self.db.add(var_media)
            self.db.flush()
            
            return var_media
                
        except Exception as e:
            print(f"Variation creation error: {e}")
            return None
    
    def get_webp_url(self, media: Media, accept_header: str = "") -> Optional[str]:
        """
        Get WebP URL if browser supports it.
        
        Args:
            media: Media object
            accept_header: HTTP Accept header
        
        Returns:
            WebP URL if supported, otherwise original URL
        """
        if not media.mime_type.startswith("image/"):
            return media.file_url
        
        # Use WebPSupport utility
        supports_webp = WebPSupport.supports_webp(accept_header)
        
        if not supports_webp:
            return media.file_url
        
        # Look for existing WebP version
        webp = self.db.query(Media).filter(
            Media.parent_id == media.id,
            Media.mime_type == "image/webp",
            Media.is_deleted == False
        ).first()
        
        if webp:
            return webp.file_url
        
        # Return original if no WebP version exists
        return media.file_url
    
    def _sanitize_filename(self, filename: str) -> str:
        """Create safe filename."""
        from werkzeug.utils import secure_filename
        import uuid
        
        safe = secure_filename(filename)
        name, ext = os.path.splitext(safe)
        
        # Add UUID to prevent collisions
        return f"{name}_{uuid.uuid4().hex[:8]}{ext}"
