"""
Image Transform

Image processing with WebP support and quality settings.
"""

from pathlib import Path
from typing import Tuple, Optional
from PIL import Image


class ImageTransform:
    """Image transformation with WebP support."""
    
    def __init__(self, quality: int = 85, webp_quality: int = 85):
        self.quality = quality
        self.webp_quality = webp_quality
        self.webp_method = 4  # 0-6, higher = slower but better compression
    
    def resize(self, image_path: Path, output_path: Path,
               size: Tuple[int, int], format_type: str = None) -> bool:
        """
        Resize image and save.
        
        Args:
            image_path: Source image path
            output_path: Destination path
            size: (width, height) tuple
            format_type: Output format (JPEG, PNG, WEBP)
        
        Returns:
            True if successful
        """
        try:
            with Image.open(image_path) as img:
                # Convert mode if needed
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Resize
                img.thumbnail(size, Image.LANCZOS)
                
                # Determine format
                if not format_type:
                    format_type = output_path.suffix.upper().replace('.', '')
                    if format_type == 'JPG':
                        format_type = 'JPEG'
                
                # Save with appropriate settings
                if format_type == 'WEBP':
                    img.save(
                        output_path, 'WEBP',
                        quality=self.webp_quality,
                        method=self.webp_method
                    )
                elif format_type == 'JPEG':
                    img.save(output_path, 'JPEG', 
                            quality=self.quality, optimize=True)
                else:
                    img.save(output_path, format_type)
                
                return True
                
        except Exception as e:
            print(f"Transform error: {e}")
            return False
    
    def convert_to_webp(self, image_path: Path, 
                        output_path: Path,
                        quality: int = None) -> bool:
        """
        Convert image to WebP format.
        
        Args:
            image_path: Source image path
            output_path: Destination WebP path
            quality: WebP quality (overrides default)
        
        Returns:
            True if successful
        """
        quality = quality or self.webp_quality
        
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                img.save(
                    output_path,
                    'WEBP',
                    quality=quality,
                    method=self.webp_method
                )
                return True
                
        except Exception as e:
            print(f"WebP conversion error: {e}")
            return False
    
    def generate_variations(self, image_path: Path, output_dir: Path,
                          sizes: list, formats: list = None) -> list:
        """
        Generate multiple size and format variations.
        
        Args:
            image_path: Source image
            output_dir: Output directory
            sizes: List of (width, height) tuples
            formats: List of formats ['jpeg', 'webp']
        
        Returns:
            List of created file paths
        """
        formats = formats or ['jpeg', 'webp']
        created = []
        
        base_name = image_path.stem
        
        for width, height in sizes:
            for fmt in formats:
                ext = '.webp' if fmt == 'webp' else '.jpg'
                filename = f"{base_name}_{width}x{height}{ext}"
                output_path = output_dir / filename
                
                if self.resize(image_path, output_path, 
                              (width, height), fmt.upper()):
                    created.append(output_path)
        
        return created
    
    def get_image_info(self, image_path: Path) -> dict:
        """Get image metadata."""
        try:
            with Image.open(image_path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "size_bytes": image_path.stat().st_size
                }
        except Exception:
            return {}
