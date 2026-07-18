"""
Content Manager with KosDB support

Provides SQLAlchemy-like interface for KosDB backend
"""

from datetime import datetime
from typing import List, Optional, Dict, Any


class KosDBContentManager:
    """Content management operations with KosDB backend."""
    
    def __init__(self, db=None):
        self.db = db
        self._ensure_tables()
    
    def _is_kosdb(self) -> bool:
        """Check if database is KosDB."""
        if self.db is None:
            return False
        has_methods = all(
            hasattr(self.db, method) 
            for method in ['execute', 'query', 'list_tables']
        )
        return has_methods
    
    def _ensure_tables(self):
        """Ensure content tables exist."""
        if not self.db or not self._is_kosdb():
            return
        
        try:
            tables = self.db.list_tables()
        except Exception:
            tables = []
        
        # Pages table
        if 'pages' not in tables:
            try:
                self.db.execute("""
                    CREATE TABLE pages (
                        id TEXT PRIMARY KEY,
                        title TEXT,
                        slug TEXT,
                        content TEXT,
                        author_id TEXT,
                        status TEXT DEFAULT 'draft',
                        template TEXT DEFAULT 'page.html',
                        meta_title TEXT,
                        meta_description TEXT,
                        is_homepage TEXT DEFAULT '0',
                        is_deleted TEXT DEFAULT '0',
                        created_at TEXT,
                        updated_at TEXT
                    )
                """)
            except Exception:
                pass
        
        # Posts table
        if 'posts' not in tables:
            try:
                self.db.execute("""
                    CREATE TABLE posts (
                        id TEXT PRIMARY KEY,
                        title TEXT,
                        slug TEXT,
                        content TEXT,
                        author_id TEXT,
                        status TEXT DEFAULT 'draft',
                        format TEXT DEFAULT 'markdown',
                        excerpt TEXT,
                        meta_title TEXT,
                        meta_description TEXT,
                        allow_comments TEXT DEFAULT '1',
                        is_featured TEXT DEFAULT '0',
                        is_sticky TEXT DEFAULT '0',
                        is_deleted TEXT DEFAULT '0',
                        published_at TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                """)
            except Exception:
                pass
    
    def _row_to_page(self, row: Dict) -> Dict:
        """Convert row to page dict."""
        return {
            "id": row['id'],
            "title": row['title'],
            "slug": row['slug'],
            "content": row['content'],
            "author_id": row['author_id'],
            "status": row.get('status', 'draft'),
            "template": row.get('template', 'page.html'),
            "meta_title": row.get('meta_title'),
            "meta_description": row.get('meta_description'),
            "is_homepage": row.get('is_homepage') == '1',
            "is_deleted": row.get('is_deleted') == '1',
            "created_at": row.get('created_at'),
            "updated_at": row.get('updated_at')
        }
    
    def _row_to_post(self, row: Dict) -> Dict:
        """Convert row to post dict."""
        return {
            "id": row['id'],
            "title": row['title'],
            "slug": row['slug'],
            "content": row['content'],
            "author_id": row['author_id'],
            "status": row.get('status', 'draft'),
            "format": row.get('format', 'markdown'),
            "excerpt": row.get('excerpt'),
            "meta_title": row.get('meta_title'),
            "meta_description": row.get('meta_description'),
            "allow_comments": row.get('allow_comments') == '1',
            "is_featured": row.get('is_featured') == '1',
            "is_sticky": row.get('is_sticky') == '1',
            "is_deleted": row.get('is_deleted') == '1',
            "published_at": row.get('published_at'),
            "created_at": row.get('created_at'),
            "updated_at": row.get('updated_at')
        }
    
    def list_pages(self, status: Optional[str] = None,
                   limit: int = 20, offset: int = 0) -> List[Dict]:
        """List pages with pagination."""
        if not self.db or not self._is_kosdb():
            return []
        
        try:
            sql = "SELECT * FROM pages WHERE is_deleted='0'"
            if status:
                sql += f" AND status='{status}'"
            sql += f" ORDER BY created_at DESC LIMIT {limit} OFFSET {offset}"
            
            result = self.db.query(sql)
            return [self._row_to_page(row) for row in result.get('rows', [])]
        except Exception:
            return []
    
    def list_posts(self, status: Optional[str] = None,
                   limit: int = 20, offset: int = 0) -> List[Dict]:
        """List posts with pagination."""
        if not self.db or not self._is_kosdb():
            return []
        
        try:
            sql = "SELECT * FROM posts WHERE is_deleted='0'"
            if status:
                sql += f" AND status='{status}'"
            sql += f" ORDER BY created_at DESC LIMIT {limit} OFFSET {offset}"
            
            result = self.db.query(sql)
            return [self._row_to_post(row) for row in result.get('rows', [])]
        except Exception:
            return []
    
    def get_page(self, page_id: Optional[str] = None,
                 slug: Optional[str] = None) -> Optional[Dict]:
        """Get page by ID or slug."""
        if not self.db or not self._is_kosdb():
            return None
        
        try:
            if page_id:
                result = self.db.query(f"SELECT * FROM pages WHERE id='{page_id}' AND is_deleted='0'")
            elif slug:
                result = self.db.query(f"SELECT * FROM pages WHERE slug='{slug}' AND is_deleted='0'")
            else:
                return None
            
            rows = result.get('rows', [])
            if rows:
                return self._row_to_page(rows[0])
        except Exception:
            pass
        return None
    
    def get_post(self, post_id: Optional[str] = None,
                 slug: Optional[str] = None) -> Optional[Dict]:
        """Get post by ID or slug."""
        if not self.db or not self._is_kosdb():
            return None
        
        try:
            if post_id:
                result = self.db.query(f"SELECT * FROM posts WHERE id='{post_id}' AND is_deleted='0'")
            elif slug:
                result = self.db.query(f"SELECT * FROM posts WHERE slug='{slug}' AND is_deleted='0'")
            else:
                return None
            
            rows = result.get('rows', [])
            if rows:
                return self._row_to_post(rows[0])
        except Exception:
            pass
        return None
    
    def create_page(self, title: str, slug: str, content: str,
                    author_id: str, **kwargs) -> Dict:
        """Create new page."""
        import uuid
        page_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        page_data = {
            "id": page_id,
            "title": title,
            "slug": slug,
            "content": content,
            "author_id": author_id,
            "status": kwargs.get("status", "draft"),
            "template": kwargs.get("template", "page.html"),
            "meta_title": kwargs.get("meta_title", ""),
            "meta_description": kwargs.get("meta_description", ""),
            "is_homepage": '1' if kwargs.get("is_homepage") else '0',
            "is_deleted": '0',
            "created_at": now,
            "updated_at": now
        }
        
        if self.db and self._is_kosdb():
            try:
                self.db.execute(f"""
                    INSERT INTO pages (id, title, slug, content, author_id, status, template,
                        meta_title, meta_description, is_homepage, is_deleted, created_at, updated_at)
                    VALUES (
                        '{page_data['id']}', '{page_data['title']}', '{page_data['slug']}',
                        '{page_data['content']}', '{page_data['author_id']}', '{page_data['status']}',
                        '{page_data['template']}', '{page_data['meta_title']}', '{page_data['meta_description']}',
                        '{page_data['is_homepage']}', '{page_data['is_deleted']}',
                        '{page_data['created_at']}', '{page_data['updated_at']}'
                    )
                """)
            except Exception as e:
                print(f"Error creating page: {e}")
        
        return page_data
    
    def create_post(self, title: str, slug: str, content: str,
                    author_id: str, **kwargs) -> Dict:
        """Create new post."""
        import uuid
        post_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        post_data = {
            "id": post_id,
            "title": title,
            "slug": slug,
            "content": content,
            "author_id": author_id,
            "status": kwargs.get("status", "draft"),
            "format": kwargs.get("format", "markdown"),
            "excerpt": kwargs.get("excerpt", ""),
            "meta_title": kwargs.get("meta_title", ""),
            "meta_description": kwargs.get("meta_description", ""),
            "allow_comments": '1' if kwargs.get("allow_comments", True) else '0',
            "is_featured": '1' if kwargs.get("is_featured") else '0',
            "is_sticky": '1' if kwargs.get("is_sticky") else '0',
            "is_deleted": '0',
            "published_at": now if kwargs.get("status") == "published" else "",
            "created_at": now,
            "updated_at": now
        }
        
        if self.db and self._is_kosdb():
            try:
                self.db.execute(f"""
                    INSERT INTO posts (id, title, slug, content, author_id, status, format,
                        excerpt, meta_title, meta_description, allow_comments, is_featured,
                        is_sticky, is_deleted, published_at, created_at, updated_at)
                    VALUES (
                        '{post_data['id']}', '{post_data['title']}', '{post_data['slug']}',
                        '{post_data['content']}', '{post_data['author_id']}', '{post_data['status']}',
                        '{post_data['format']}', '{post_data['excerpt']}', '{post_data['meta_title']}',
                        '{post_data['meta_description']}', '{post_data['allow_comments']}',
                        '{post_data['is_featured']}', '{post_data['is_sticky']}', '{post_data['is_deleted']}',
                        '{post_data['published_at']}', '{post_data['created_at']}', '{post_data['updated_at']}'
                    )
                """)
            except Exception as e:
                print(f"Error creating post: {e}")
        
        return post_data
    
    def update_page(self, page_id: str, **kwargs) -> Optional[Dict]:
        """Update page."""
        page = self.get_page(page_id=page_id)
        if not page:
            return None
        
        updates = []
        for key, value in kwargs.items():
            if key in ['title', 'slug', 'content', 'status', 'template', 'meta_title', 'meta_description']:
                updates.append(f"{key}='{value}'")
        
        if updates:
            updates.append(f"updated_at='{datetime.utcnow().isoformat()}'")
            update_sql = ", ".join(updates)
            
            if self.db and self._is_kosdb():
                try:
                    self.db.execute(f"UPDATE pages SET {update_sql} WHERE id='{page_id}'")
                except Exception as e:
                    print(f"Error updating page: {e}")
        
        return self.get_page(page_id=page_id)
    
    def update_post(self, post_id: str, **kwargs) -> Optional[Dict]:
        """Update post."""
        post = self.get_post(post_id=post_id)
        if not post:
            return None
        
        updates = []
        for key, value in kwargs.items():
            if key in ['title', 'slug', 'content', 'status', 'format', 'excerpt', 
                       'meta_title', 'meta_description', 'allow_comments', 
                       'is_featured', 'is_sticky']:
                if isinstance(value, bool):
                    value = '1' if value else '0'
                updates.append(f"{key}='{value}'")
        
        if updates:
            updates.append(f"updated_at='{datetime.utcnow().isoformat()}'")
            update_sql = ", ".join(updates)
            
            if self.db and self._is_kosdb():
                try:
                    self.db.execute(f"UPDATE posts SET {update_sql} WHERE id='{post_id}'")
                except Exception as e:
                    print(f"Error updating post: {e}")
        
        return self.get_post(post_id=post_id)
    
    def delete_page(self, page_id: str, soft: bool = True) -> bool:
        """Delete page."""
        if soft:
            if self.db and self._is_kosdb():
                try:
                    self.db.execute(f"UPDATE pages SET is_deleted='1', updated_at='{datetime.utcnow().isoformat()}' WHERE id='{page_id}'")
                    return True
                except Exception:
                    pass
        else:
            if self.db and self._is_kosdb():
                try:
                    self.db.execute(f"DELETE FROM pages WHERE id='{page_id}'")
                    return True
                except Exception:
                    pass
        return False
    
    def delete_post(self, post_id: str, soft: bool = True) -> bool:
        """Delete post."""
        if soft:
            if self.db and self._is_kosdb():
                try:
                    self.db.execute(f"UPDATE posts SET is_deleted='1', updated_at='{datetime.utcnow().isoformat()}' WHERE id='{post_id}'")
                    return True
                except Exception:
                    pass
        else:
            if self.db and self._is_kosdb():
                try:
                    self.db.execute(f"DELETE FROM posts WHERE id='{post_id}'")
                    return True
                except Exception:
                    pass
        return False
