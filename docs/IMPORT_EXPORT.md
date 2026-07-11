
# Content Import/Export Guide

WebCMS v1.1.0 supports importing and exporting content in JSON and CSV formats.

## Export

### JSON Export

```python
from webcms.content.exchange import ContentExporter, ExportOptions

exporter = ContentExporter(db)

options = ExportOptions(
    format="json",
    content_types=["post", "page"],  # Export both
    status="published"  # Only published content
)

data = exporter.export(options)
```

### CSV Export

```python
options = ExportOptions(
    format="csv",
    content_types=["post"]
)

csv_data = exporter.export(options)
# Returns CSV with headers: type,id,title,slug,content,excerpt,status,created_at,author_id,categories,tags
```

### API Export

```
POST /api/v1/content/export
Content-Type: application/json

{
  "format": "json",
  "content_types": ["post"],
  "status": "published"
}
```

## Import

### JSON Import

```python
from webcms.content.exchange import ContentImporter

importer = ContentImporter(db)

json_data = '''
{
  "posts": [
    {
      "title": "Imported Post",
      "slug": "imported-post",
      "content": "Content here",
      "status": "published"
    }
  ]
}
'''

result = importer.import_content(json_data)
print(f"Imported: {result.imported}, Skipped: {result.skipped}")
```

### CSV Import

```python
csv_data = '''type,id,title,slug,content,excerpt,status,created_at,author_id
post,post-1,Title,slug,Content,,published,2024-01-01,user-1'''

result = importer.import_content(csv_data)
```

### API Import

```
POST /api/v1/content/import
Content-Type: application/json

{
  "posts": [...],
  "pages": [...]
}
```

## Format Detection

The importer automatically detects format:

```python
format_type = importer.detect_format(data)
# Returns: "json" or "csv"
```

## Validation

- Duplicate slugs are skipped
- Required fields: title, slug, content
- Categories and tags are auto-created
- Schema validation prevents malformed data

## Error Handling

```python
result = importer.import_content(data)

if not result.success:
    for error in result.errors:
        print(f"Error: {error}")
```
