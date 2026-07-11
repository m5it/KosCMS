"""
Content Exchange

Import and export functionality for content.
Supports JSON and CSV formats with validation.
"""

import json
import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict

from sqlalchemy.orm import Session

from webcms.models.content import Post, Page, Category, Tag
from webcms.models.user import User


@dataclass
class ExportOptions:
    """Export configuration."""
    format: str = "json"  # json, csv
    content_types: List[str] = None  # post, page
    status: Optional[str] = None
    author_id: Optional[str] = None
    category_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


@dataclass
class ImportResult:
    """Import operation result."""
    success: bool
    imported: int
    errors: List[str]
    skipped: int


class ContentExporter:
    """Export content to various formats."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def export(self, options: ExportOptions) -> Union[str, bytes]:
        """
        Export content based on options.
        
        Returns:
            JSON string or CSV bytes
        """
        if options.format == "json":
            return self._export_json(options)
        elif options.format == "csv":
            return self._export_csv(options)
        else:
            raise ValueError(f"Unsupported format: {options.format}")
    
    def _build_query(self, model_class, options: ExportOptions):
        """Build filtered query."""
        query = self.db.query(model_class).filter(
            model_class.is_deleted == False
        )
        
        if options.status:
            query = query.filter(model_class.status == options.status)
        
        if options.author_id:
            query = query.filter(model_class.author_id == options.author_id)
        
        if options.date_from:
            query = query.filter(model_class.created_at >= options.date_from)
        
        if options.date_to:
            query = query.filter(model_class.created_at <= options.date_to)
        
        return query
    
    def _export_json(self, options: ExportOptions) -> str:
        """Export to JSON format."""
        data = {
            "meta": {
                "exported_at": datetime.utcnow().isoformat(),
                "format_version": "1.0"
            },
            "posts": [],
            "pages": []
        }
        
        content_types = options.content_types or ["post", "page"]
        
        if "post" in content_types:
            posts = self._build_query(Post, options).all()
            data["posts"] = [self._post_to_dict(p) for p in posts]
        
        if "page" in content_types:
            pages = self._build_query(Page, options).all()
            data["pages"] = [self._page_to_dict(p) for p in pages]
        
        return json.dumps(data, indent=2, default=str)
    
    def _export_csv(self, options: ExportOptions) -> str:
        """Export to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "type", "id", "title", "slug", "content", "excerpt",
            "status", "created_at", "author_id", "categories", "tags"
        ])
        
        content_types = options.content_types or ["post", "page"]
        
        if "post" in content_types:
            for post in self._build_query(Post, options).all():
                writer.writerow(self._post_to_csv_row(post))
        
        if "page" in content_types:
            for page in self._build_query(Page, options).all():
                writer.writerow(self._page_to_csv_row(page))
        
        return output.getvalue()
    
    def _post_to_dict(self, post: Post) -> Dict[str, Any]:
        """Convert post to dictionary."""
        return {
            "id": post.id,
            "title": post.title,
            "slug": post.slug,
            "content": post.content,
            "excerpt": post.excerpt,
            "status": post.status,
            "format": post.format,
            "published_at": post.published_at.isoformat() if post.published_at else None,
            "created_at": post.created_at.isoformat(),
            "author_id": post.author_id,
            "categories": [{"id": c.id, "name": c.name} for c in post.categories],
            "tags": [{"id": t.id, "name": t.name} for t in post.tags],
            "is_featured": post.is_featured,
            "allow_comments": post.allow_comments
        }
    
    def _page_to_dict(self, page: Page) -> Dict[str, Any]:
        """Convert page to dictionary."""
        return {
            "id": page.id,
            "title": page.title,
            "slug": page.slug,
            "content": page.content,
            "excerpt": page.excerpt,
            "status": page.status,
            "is_homepage": page.is_homepage,
            "template": page.template,
            "published_at": page.published_at.isoformat() if page.published_at else None,
            "created_at": page.created_at.isoformat(),
            "author_id": page.author_id
        }
    
    def _post_to_csv_row(self, post: Post) -> List:
        """Convert post to CSV row."""
        categories = "|".join([c.name for c in post.categories])
        tags = "|".join([t.name for t in post.tags])
        
        return [
            "post", post.id, post.title, post.slug,
            post.content, post.excerpt or "", post.status,
            post.created_at.isoformat(), post.author_id,
            categories, tags
        ]
    
    def _page_to_csv_row(self, page: Page) -> List:
        """Convert page to CSV row."""
        return [
            "page", page.id, page.title, page.slug,
            page.content, page.excerpt or "", page.status,
            page.created_at.isoformat(), page.author_id, "", ""
        ]


class ContentImporter:
    """Import content from various formats."""
    
    # Schema for validation
    POST_SCHEMA = {
        "required": ["title", "slug", "content"],
        "optional": ["excerpt", "status", "format", "author_id", 
                    "categories", "tags", "is_featured", "allow_comments"]
    }
    
    PAGE_SCHEMA = {
        "required": ["title", "slug", "content"],
        "optional": ["excerpt", "status", "template", "is_homepage", 
                    "author_id"]
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.errors = []
        self.imported = 0
        self.skipped = 0
    
    def detect_format(self, data: Union[str, bytes]) -> str:
        """Detect import format."""
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        
        # Try JSON first
        try:
            json.loads(data)
            return "json"
        except json.JSONDecodeError:
            pass
        
        # Check for CSV characteristics
        if ',' in data and '\n' in data:
            lines = data.strip().split('\n')
            if len(lines) > 1:
                header = lines[0]
                if 'type' in header and 'title' in header:
                    return "csv"
        
        raise ValueError("Unable to detect format")
    
    def import_content(self, data: Union[str, bytes], 
                       format_hint: Optional[str] = None) -> ImportResult:
        """
        Import content from data.
        
        Args:
            data: Content data to import
            format_hint: Optional format hint (json, csv)
        
        Returns:
            ImportResult with status and details
        """
        self.errors = []
        self.imported = 0
        self.skipped = 0
        
        try:
            # Detect format
            fmt = format_hint or self.detect_format(data)
            
            if fmt == "json":
                self._import_json(data)
            elif fmt == "csv":
                self._import_csv(data)
            else:
                raise ValueError(f"Unsupported format: {fmt}")
            
            return ImportResult(
                success=len(self.errors) == 0,
                imported=self.imported,
                errors=self.errors,
                skipped=self.skipped
            )
            
        except Exception as e:
            self.errors.append(f"Import failed: {str(e)}")
            return ImportResult(
                success=False,
                imported=self.imported,
                errors=self.errors,
                skipped=self.skipped
            )
    
    def _import_json(self, data: str):
        """Import from JSON."""
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {str(e)}")
            return
        
        # Handle both wrapped and unwrapped formats
        if "posts" in parsed:
            posts = parsed.get("posts", [])
            pages = parsed.get("pages", [])
        else:
            # Assume single item or array
            items = parsed if isinstance(parsed, list) else [parsed]
            posts = [i for i in items if i.get("type") == "post"]
            pages = [i for i in items if i.get("type") == "page"]
        
        for post_data in posts:
            self._import_post(post_data)
        
        for page_data in pages:
            self._import_page(page_data)
    
    def _import_csv(self, data: str):
        """Import from CSV."""
        reader = csv.reader(io.StringIO(data))
        
        # Skip header
        try:
            header = next(reader)
        except StopIteration:
            self.errors.append("Empty CSV file")
            return
        
        # Validate header
        expected = ["type", "id", "title", "slug", "content"]
        if not all(h in header for h in expected):
            self.errors.append(f"Invalid CSV header. Expected: {expected}")
            return
        
        for row_num, row in enumerate(reader, start=2):
            try:
                if len(row) < 5:
                    self.errors.append(f"Row {row_num}: insufficient columns")
                    continue
                
                item_type = row[0]
                data = {
                    "id": row[1],
                    "title": row[2],
                    "slug": row[3],
                    "content": row[4],
                    "excerpt": row[5] if len(row) > 5 else "",
                    "status": row[6] if len(row) > 6 else "draft",
                }
                
                if item_type == "post":
                    data["categories"] = row[9].split("|") if len(row) > 9 and row[9] else []
                    data["tags"] = row[10].split("|") if len(row) > 10 and row[10] else []
                    self._import_post(data)
                elif item_type == "page":
                    self._import_page(data)
                else:
                    self.errors.append(f"Row {row_num}: unknown type '{item_type}'")
                    
            except Exception as e:
                self.errors.append(f"Row {row_num}: {str(e)}")
    
    def _validate_item(self, data: Dict, schema: Dict) -> bool:
        """Validate item against schema."""
        for field in schema["required"]:
            if field not in data or not data[field]:
                return False
        return True
    
    def _import_post(self, data: Dict):
        """Import a single post."""
        if not self._validate_item(data, self.POST_SCHEMA):
            self.errors.append(f"Invalid post data: missing required fields")
            self.skipped += 1
            return
        
        # Check for existing slug
        existing = self.db.query(Post).filter(Post.slug == data["slug"]).first()
        if existing:
            self.errors.append(f"Post with slug '{data['slug']}' already exists")
            self.skipped += 1
            return
        
        try:
            post = Post(
                title=data["title"],
                slug=data["slug"],
                content=data["content"],
                excerpt=data.get("excerpt"),
                status=data.get("status", "draft"),
                format=data.get("format", "markdown"),
                author_id=data.get("author_id"),
                is_featured=data.get("is_featured", False),
                allow_comments=data.get("allow_comments", True)
            )
            
            # Handle categories
            for cat_name in data.get("categories", []):
                cat = self._get_or_create_category(cat_name)
                post.categories.append(cat)
            
            # Handle tags
            for tag_name in data.get("tags", []):
                tag = self._get_or_create_tag(tag_name)
                post.tags.append(tag)
            
            self.db.add(post)
            self.db.commit()
            self.imported += 1
            
        except Exception as e:
            self.db.rollback()
            self.errors.append(f"Failed to import post '{data.get('title')}': {str(e)}")
            self.skipped += 1
    
    def _import_page(self, data: Dict):
        """Import a single page."""
        if not self._validate_item(data, self.PAGE_SCHEMA):
            self.errors.append(f"Invalid page data: missing required fields")
            self.skipped += 1
            return
        
        # Check for existing slug
        existing = self.db.query(Page).filter(Page.slug == data["slug"]).first()
        if existing:
            self.errors.append(f"Page with slug '{data['slug']}' already exists")
            self.skipped += 1
            return
        
        try:
            page = Page(
                title=data["title"],
                slug=data["slug"],
                content=data["content"],
                excerpt=data.get("excerpt"),
                status=data.get("status", "draft"),
                template=data.get("template", "page.html"),
                is_homepage=data.get("is_homepage", False),
                author_id=data.get("author_id")
            )
            
            self.db.add(page)
            self.db.commit()
            self.imported += 1
            
        except Exception as e:
            self.db.rollback()
            self.errors.append(f"Failed to import page '{data.get('title')}': {str(e)}")
            self.skipped += 1
    
    def _get_or_create_category(self, name: str) -> Category:
        """Get or create category by name."""
        slug = name.lower().replace(" ", "-")
        cat = self.db.query(Category).filter(Category.slug == slug).first()
        if not cat:
            cat = Category(name=name, slug=slug)
            self.db.add(cat)
            self.db.flush()
        return cat
    
    def _get_or_create_tag(self, name: str) -> Tag:
        """Get or create tag by name."""
        slug = name.lower().replace(" ", "-")
        tag = self.db.query(Tag).filter(Tag.slug == slug).first()
        if not tag:
            tag = Tag(name=name, slug=slug)
            self.db.add(tag)
            self.db.flush()
        return tag
