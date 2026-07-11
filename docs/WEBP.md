
# WebP Image Support

WebCMS v1.1.0 includes automatic WebP conversion for optimized image delivery.

## Features

- Automatic WebP conversion on upload
- Browser capability detection
- Multiple size variations with WebP
- Quality configuration
- Fallback to original format

## Quick Start

```python
from webcms.media.manager import MediaManager

manager = MediaManager(db)

# Upload image - automatically creates WebP version
media = manager.upload(file_data, "photo.jpg", "image/jpeg", user_id)

# Convert existing image to WebP
webp_media = manager.convert_to_webp(media)
```

## Browser Detection

Serve WebP to supported browsers:

```python
# In your view/request handler
accept_header = request.headers.get("Accept", "")
url = manager.get_webp_url(media, accept_header)

# Returns WebP URL if browser supports it, otherwise original
```

## Generate Variations

Create multiple sizes with WebP versions:

```python
sizes = [(300, 300), (600, 600), (1200, 800)]
variations = manager.generate_variations_with_webp(media, sizes)

# Creates both JPEG and WebP for each size
# Returns list of Media objects
```

## Configuration

Configure WebP quality in code:

```python
from webcms.media.manager import WebPConfig

config = WebPConfig(
    quality=85,      # 0-100, higher is better quality
    method=4,        # 0-6, compression method
    lossless=False   # True for lossless compression
)

webp_media = manager.convert_to_webp(media, config)
```

## ImageTransform

Direct image transformation:

```python
from webcms.media.transform import ImageTransform

transform = ImageTransform(webp_quality=85)

# Convert to WebP
transform.convert_to_webp(source_path, output_path, quality=90)

# Resize and convert
transform.resize(source_path, output_path, (800, 600), "WEBP")
```

## API Response

Images include WebP information:

```json
{
  "id": "media-123",
  "filename": "photo.jpg",
  "url": "/media/2024/01/photo.jpg",
  "webp_url": "/media/2024/01/photo.webp",
  "mime_type": "image/jpeg",
  "width": 1920,
  "height": 1080
}
```

## Requirements

WebP support is built into Pillow 10.0+. No additional dependencies required.

## Performance

- WebP typically 25-35% smaller than JPEG
- Quality 85 provides good balance
- Method 4 offers good compression speed
- Consider lossless for graphics/text images
