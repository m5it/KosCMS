
"""
Tests for WebP Support (v1.1.0)

Image conversion and media processing.
"""

import pytest
import tempfile
from pathlib import Path
from PIL import Image
from io import BytesIO

from webcms.media.transform import ImageTransform
from webcms.media.manager import WebPConfig


class TestImageTransform:
    """Test image transformation."""
    
    @pytest.fixture
    def test_image(self):
        """Create test image."""
        img = Image.new('RGB', (100, 100), color='red')
        buffer = BytesIO()
        img.save(buffer, 'JPEG')
        buffer.seek(0)
        return buffer
    
    @pytest.fixture
    def temp_dir(self):
        """Create temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_resize(self, test_image, temp_dir):
        """Test image resize."""
        transform = ImageTransform()
        
        source = temp_dir / "source.jpg"
        output = temp_dir / "resized.jpg"
        
        # Save test image
        img = Image.open(test_image)
        img.save(source)
        
        result = transform.resize(source, output, (50, 50))
        
        assert result is True
        assert output.exists()
        
        # Verify size
        resized = Image.open(output)
        assert resized.size[0] <= 50
        assert resized.size[1] <= 50
    
    def test_convert_to_webp(self, test_image, temp_dir):
        """Test WebP conversion."""
        transform = ImageTransform(webp_quality=85)
        
        source = temp_dir / "source.jpg"
        output = temp_dir / "output.webp"
        
        img = Image.open(test_image)
        img.save(source)
        
        result = transform.convert_to_webp(source, output)
        
        assert result is True
        assert output.exists()
        assert output.suffix == ".webp"
        
        # Verify it's WebP
        webp_img = Image.open(output)
        assert webp_img.format == "WEBP"
    
    def test_generate_variations(self, test_image, temp_dir):
        """Test variation generation."""
        transform = ImageTransform()
        
        source = temp_dir / "source.jpg"
        output_dir = temp_dir / "variations"
        output_dir.mkdir()
        
        img = Image.open(test_image)
        img.save(source)
        
        sizes = [(100, 100), (50, 50)]
        formats = ["jpeg", "webp"]
        
        created = transform.generate_variations(source, output_dir, sizes, formats)
        
        assert len(created) == 4  # 2 sizes * 2 formats
    
    def test_get_image_info(self, test_image, temp_dir):
        """Test image info extraction."""
        transform = ImageTransform()
        
        source = temp_dir / "source.jpg"
        img = Image.open(test_image)
        img.save(source)
        
        info = transform.get_image_info(source)
        
        assert info["width"] == 100
        assert info["height"] == 100
        assert info["format"] == "JPEG"


class TestWebPConfig:
    """Test WebP configuration."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = WebPConfig()
        
        assert config.quality == 85
        assert config.method == 4
        assert config.lossless is False
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = WebPConfig(quality=90, method=6, lossless=True)
        
        assert config.quality == 90
        assert config.method == 6
        assert config.lossless is True
