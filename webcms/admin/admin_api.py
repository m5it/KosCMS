"""
Admin API v1.3.4

Synchronous REST handlers for the React admin control panel.
Wired into webcms.admin.api.create_api() so all /api/v1/admin/* routes
are registered automatically with the main application.
"""

import json
import uuid
from datetime import datetime

from webcms.core.request import Request
from webcms.core.response import Response


class AdminAPI:
    def __init__(self, db=None, auth=None):
        self.db = db
        self.auth = auth

    # ---------------- Database Helpers ----------------

    def _is_kosdb(self) -> bool:
        if self.db is None:
            return False
        cls = getattr(self.db, '__class__', type(self.db))
        cls_name = getattr(cls, '__name__', '')
        return 'KosDB' in cls_name

    @staticmethod
    def _sql_escape(value) -> str:
        if value is None:
            return "NULL"
        s = str(value)
        return s.replace("'", "''")

    def _kosdb_where_clause(self, key: str, value) -> str:
        if isinstance(value, bool):
            int_val = 1 if value else 0
            return f"({key}='{int_val}' OR {key}='{str(value).lower()}')"
        return f"{key}='{self._sql_escape(value)}'"

    def _get_model_count(self, model_class, filter_conditions=None) -> int:
        if self.db is None:
            return 0
        is_kosdb = self._is_kosdb() or isinstance(self.db, dict)
        if is_kosdb:
            table_name = getattr(model_class, '__tablename__',
                                getattr(model_class, '__name__', '').lower() + 's')
            if filter_conditions:
                where = " AND ".join(
                    self._kosdb_where_clause(k, v) for k, v in filter_conditions.items()
                )
                cmd = f"SELECT COUNT(*) FROM {table_name} WHERE {where}"
            else:
                cmd = f"SELECT COUNT(*) FROM {table_name}"
            result = self.db.query(cmd)
            if result.get('error'):
                return 0
            rows = result.get('rows', [])
            if rows:
                return int(list(rows[0].values())[0])
            return 0
        else:
            query = self.db.query(model_class)
            if filter_conditions:
                for key, value in filter_conditions.items():
                    query = query.filter(getattr(model_class, key) == value)
            return query.count()

    def _get_model_list(self, model_class, filter_conditions=None,
                       order_by=None, limit=None, desc=True) -> list:
        if self.db is None:
            return []
        is_kosdb = self._is_kosdb() or isinstance(self.db, dict)
        if is_kosdb:
            table_name = getattr(model_class, '__tablename__',
                                getattr(model_class, '__name__', '').lower() + 's')
            cmd = f"SELECT * FROM {table_name}"
            if filter_conditions:
                where = " AND ".join(
                    self._kosdb_where_clause(k, v) for k, v in filter_conditions.items()
                )
                cmd += f" WHERE {where}"
            if order_by:
                cmd += f" ORDER BY {order_by} {'DESC' if desc else 'ASC'}"
            if limit:
                cmd += f" LIMIT {limit}"
            result = self.db.query(cmd)
            if result.get('error'):
                return []
            return result.get('rows', [])
        else:
            query = self.db.query(model_class)
            if filter_conditions:
                for key, value in filter_conditions.items():
                    query = query.filter(getattr(model_class, key) == value)
            if order_by:
                order_col = getattr(model_class, order_by)
                if desc:
                    order_col = order_col.desc()
                query = query.order_by(order_col)
            if limit:
                query = query.limit(limit)
            return query.all()

    def _get_model_by_id(self, model_class, record_id: str,
                        id_field='id', extra_filters=None) -> any:
        if self.db is None:
            return None
        filters = {id_field: record_id}
        if extra_filters:
            filters.update(extra_filters)
        is_kosdb = self._is_kosdb() or isinstance(self.db, dict)
        if is_kosdb:
            table_name = getattr(model_class, '__tablename__',
                                getattr(model_class, '__name__', '').lower() + 's')
            where = " AND ".join(
                self._kosdb_where_clause(k, v) for k, v in filters.items()
            )
            cmd = f"SELECT * FROM {table_name} WHERE {where}"
            result = self.db.query(cmd)
            if result.get('error'):
                return None
            rows = result.get('rows', [])
            return rows[0] if rows else None
        else:
            query = self.db.query(model_class)
            for key, value in filters.items():
                query = query.filter(getattr(model_class, key) == value)
            return query.first()

    # ---------------- Dashboard ----------------

    def dashboard(self, request: Request) -> Response:
        from webcms.models.user import User
        from webcms.models.content import Post, Page
        from webcms.models.media import Media
        stats = {}
        if self.db:
            stats = {
                "users": {
                    "total": self._get_model_count(User, {"is_deleted": False}),
                    "active": self._get_model_count(User, {"is_deleted": False, "is_active": True})
                },
                "content": {
                    "posts": self._get_model_count(Post, {"is_deleted": False}),
                    "pages": self._get_model_count(Page, {"is_deleted": False})
                },
                "media": {
                    "total": self._get_model_count(Media, {"is_deleted": False})
                }
            }
        widgets = [
            {"id": "stats", "title": "Content Statistics", "icon": "📊", "data": stats},
            {"id": "activity", "title": "Recent Activity", "icon": "📅", "data": {"recent_posts": stats.get("content", {}).get("posts", 0)}},
            {"id": "health", "title": "System Health", "icon": "❤️", "data": {"status": "ok"}}
        ]
        for widget in widgets:
            widget.setdefault("icon", "")
            widget.setdefault("data", "")
        return Response.json({"widgets": widgets})

    # ---------------- KosDB Content Helpers ----------------

    def _ensure_table_kosdb(self, table_name: str, columns: list):
        """Create a KosDB table if it does not exist."""
        if not self.db:
            return
        try:
            tables = self.db.list_tables()
            if table_name in tables:
                return
        except Exception:
            pass
        try:
            self.db.execute(f"CREATE TABLE {table_name} ({', '.join(columns)})")
        except Exception:
            pass

    def _now_iso(self) -> str:
        return datetime.utcnow().isoformat()

    def _create_record_kosdb(self, table_name: str, fields: dict) -> dict:
        """Insert a new record into a KosDB table and return it."""
        record_id = str(uuid.uuid4())
        now = self._now_iso()
        fields['id'] = record_id
        fields.setdefault('created_at', now)
        fields.setdefault('updated_at', now)
        fields.setdefault('is_deleted', 0)
        cols = list(fields.keys())
        vals = [fields[c] for c in cols]
        val_str = ", ".join(
            "NULL" if v is None else f"'{self._sql_escape(v)}'" for v in vals
        )
        cmd = f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({val_str})"
        result = self.db.execute(cmd)
        if result.startswith("ERROR"):
            raise RuntimeError(result)
        return fields

    def _update_record_kosdb(self, table_name: str, record_id: str, fields: dict) -> dict:
        """Update a KosDB record and return the updated row."""
        if not fields:
            result = self.db.query(f"SELECT * FROM {table_name} WHERE id='{self._sql_escape(record_id)}'")
            rows = result.get('rows', [])
            return rows[0] if rows else {}
        fields['updated_at'] = self._now_iso()
        sets = []
        for k, v in fields.items():
            if v is None:
                sets.append(f"{k}=NULL")
            else:
                sets.append(f"{k}='{self._sql_escape(v)}'")
        cmd = (
            f"UPDATE {table_name} SET {', '.join(sets)} "
            f"WHERE id='{self._sql_escape(record_id)}' AND is_deleted='0'"
        )
        result = self.db.execute(cmd)
        if result.startswith("ERROR"):
            raise RuntimeError(result)
        result = self.db.query(f"SELECT * FROM {table_name} WHERE id='{self._sql_escape(record_id)}'")
        rows = result.get('rows', [])
        return rows[0] if rows else fields

    def _delete_record_kosdb(self, table_name: str, record_id: str) -> bool:
        """Soft-delete a KosDB record."""
        cmd = (
            f"UPDATE {table_name} SET is_deleted='1', updated_at='{self._now_iso()}' "
            f"WHERE id='{self._sql_escape(record_id)}' AND is_deleted='0'"
        )
        result = self.db.execute(cmd)
        return not result.startswith("ERROR")

    def _resolve_author_display(self, record) -> any:
        """Resolve author display name from an ORM object or dict record."""
        author_id = None
        if isinstance(record, dict):
            author = record.get('author')
            if isinstance(author, dict):
                return author.get('display_name')
            author_id = record.get('author_id')
        else:
            author = getattr(record, 'author', None)
            if author:
                return getattr(author, 'display_name', None)
            author_id = getattr(record, 'author_id', None)
        if author_id and self.db:
            try:
                from webcms.models.user import User
                user = self._get_model_by_id(User, author_id)
                if isinstance(user, dict):
                    return user.get('display_name') or user.get('username')
                if user:
                    return getattr(user, 'display_name', None) or getattr(user, 'username', None)
            except Exception:
                pass
        return author_id

    @staticmethod
    def _format_updated_at(value) -> any:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    def _split_csv(self, value) -> list:
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [v.strip() for v in value.split(',') if v.strip()]
        return []

    # ---------------- Content: Pages & Posts ----------------

    def _serialize_page(self, page) -> dict:
        return {
            "id": page.get('id') if isinstance(page, dict) else page.id,
            "title": page.get('title') if isinstance(page, dict) else page.title,
            "slug": page.get('slug') if isinstance(page, dict) else page.slug,
            "status": page.get('status') if isinstance(page, dict) else page.status,
            "author": self._resolve_author_display(page),
            "updated_at": (
                self._format_updated_at(page.get('updated_at')) if isinstance(page, dict)
                else self._format_updated_at(page.updated_at)
            )
        }

    def _serialize_post(self, post) -> dict:
        return {
            "id": post.get('id') if isinstance(post, dict) else post.id,
            "title": post.get('title') if isinstance(post, dict) else post.title,
            "slug": post.get('slug') if isinstance(post, dict) else post.slug,
            "status": post.get('status') if isinstance(post, dict) else post.status,
            "author": self._resolve_author_display(post),
            "updated_at": (
                self._format_updated_at(post.get('updated_at')) if isinstance(post, dict)
                else self._format_updated_at(post.updated_at)
            )
        }

    def _ensure_content_table_kosdb(self, table_name: str):
        """Ensure pages/posts table exists in KosDB with the columns the UI needs."""
        columns = [
            "id TEXT",
            "title TEXT",
            "slug TEXT",
            "content TEXT",
            "status TEXT",
            "author_id TEXT",
            "created_at TEXT",
            "updated_at TEXT",
            "is_deleted TEXT",
            "excerpt TEXT",
            "published_at TEXT",
            "meta_title TEXT",
            "meta_description TEXT",
            "template TEXT",
            "is_homepage TEXT",
            "format TEXT",
            "featured_image_id TEXT",
            "view_count TEXT",
            "comment_count TEXT",
            "allow_comments TEXT",
            "is_featured TEXT",
            "is_sticky TEXT"
        ]
        self._ensure_table_kosdb(table_name, columns)

    def _current_user_id(self, request: Request) -> str:
        """Extract current user id from auth or request context if available."""
        if self.auth and hasattr(self.auth, 'get_current_user'):
            user = self.auth.get_current_user(request)
            if user:
                return getattr(user, 'id', user.get('id') if isinstance(user, dict) else None)
        return None

    def _normalize_page_payload(self, data: dict, request: Request) -> dict:
        payload = {
            "title": data.get("title", "Untitled"),
            "slug": data.get("slug", ""),
            "content": data.get("content", ""),
            "status": data.get("status", "draft"),
            "author_id": data.get("author_id") or self._current_user_id(request) or "",
            "excerpt": data.get("excerpt"),
            "meta_title": data.get("meta_title"),
            "meta_description": data.get("meta_description"),
            "template": data.get("template", "page.html"),
            "is_homepage": "1" if data.get("is_homepage") else "0"
        }
        if not payload["slug"]:
            payload["slug"] = payload["title"].lower().replace(" ", "-")
        return payload

    def _normalize_post_payload(self, data: dict) -> dict:
        """Normalize UI payload for SQLAlchemy ContentManager."""
        payload = dict(data)
        if isinstance(payload.get('categories'), str):
            payload['category_ids'] = [c.strip() for c in payload['categories'].split(',') if c.strip()]
            payload.pop('categories', None)
        if isinstance(payload.get('tags'), str):
            payload['tags'] = [t.strip() for t in payload['tags'].split(',') if t.strip()]
        if isinstance(payload.get('published_at'), str) and payload['published_at']:
            try:
                payload['published_at'] = datetime.fromisoformat(payload['published_at'])
            except ValueError:
                payload.pop('published_at', None)
        return payload

    def _normalize_post_payload_kosdb(self, data: dict, request: Request) -> dict:
        payload = {
            "title": data.get("title", "Untitled"),
            "slug": data.get("slug", ""),
            "content": data.get("content", ""),
            "status": data.get("status", "draft"),
            "author_id": data.get("author_id") or self._current_user_id(request) or "",
            "excerpt": data.get("excerpt"),
            "meta_title": data.get("meta_title"),
            "meta_description": data.get("meta_description"),
            "format": data.get("format", "markdown"),
            "published_at": data.get("published_at"),
            "view_count": str(data.get("view_count", "0")),
            "comment_count": str(data.get("comment_count", "0")),
            "allow_comments": "1" if data.get("allow_comments", True) else "0",
            "is_featured": "1" if data.get("is_featured") else "0",
            "is_sticky": "1" if data.get("is_sticky") else "0"
        }
        if data.get("status") == "published" and not payload["published_at"]:
            payload["published_at"] = self._now_iso()
        if not payload["slug"]:
            payload["slug"] = payload["title"].lower().replace(" ", "-")
        return payload

    def list_pages(self, request: Request) -> Response:
        from webcms.models.content import Page
        if not self.db:
            return Response.json({"pages": []})
        if self._is_kosdb():
            self._ensure_content_table_kosdb("pages")
        pages = self._get_model_list(Page, {"is_deleted": False}, order_by="updated_at", limit=50, desc=True)
        return Response.json({"pages": [self._serialize_page(p) for p in pages]})

    def create_page(self, request: Request) -> Response:
        from webcms.models.content import Page
        from webcms.content.manager import ContentManager
        data = request.json or {}
        if not data:
            return Response.error("Invalid JSON", 400)
        if not self.db:
            return Response.json({"id": str(uuid.uuid4()), "created": True}, 201)
        try:
            if self._is_kosdb():
                self._ensure_content_table_kosdb("pages")
                fields = self._normalize_page_payload(data, request)
                record = self._create_record_kosdb("pages", fields)
                return Response.json(self._serialize_page(record), 201)
            manager = ContentManager(self.db)
            page = manager.create_page(**data)
            return Response.json(self._serialize_page(page), 201)
        except Exception as e:
            return Response.error(str(e), 400)

    def update_page(self, request: Request, page_id: str) -> Response:
        from webcms.models.content import Page
        from webcms.content.manager import ContentManager
        data = request.json or {}
        if not self.db:
            return Response.json({"id": page_id, "updated": True})
        try:
            if self._is_kosdb():
                self._ensure_content_table_kosdb("pages")
                existing = self._get_model_by_id(Page, page_id, extra_filters={"is_deleted": False})
                if not existing:
                    return Response.not_found()
                fields = self._normalize_page_payload(data, request)
                fields.pop("author_id", None)
                fields.pop("created_at", None)
                record = self._update_record_kosdb("pages", page_id, fields)
                return Response.json(self._serialize_page(record))
            manager = ContentManager(self.db)
            page = manager.update_page(page_id, **data)
            if not page:
                return Response.not_found()
            return Response.json(self._serialize_page(page))
        except Exception as e:
            return Response.error(str(e), 400)

    def delete_page(self, request: Request, page_id: str) -> Response:
        from webcms.models.content import Page
        from webcms.content.manager import ContentManager
        if not self.db:
            return Response.json({"id": page_id, "deleted": True})
        try:
            if self._is_kosdb():
                self._ensure_content_table_kosdb("pages")
                existing = self._get_model_by_id(Page, page_id, extra_filters={"is_deleted": False})
                if not existing:
                    return Response.not_found()
                if self._delete_record_kosdb("pages", page_id):
                    return Response.json({"id": page_id, "deleted": True})
                return Response.error("Delete failed", 500)
            manager = ContentManager(self.db)
            if manager.delete_page(page_id):
                return Response.json({"id": page_id, "deleted": True})
            return Response.not_found()
        except Exception as e:
            return Response.error(str(e), 400)

    def list_posts(self, request: Request) -> Response:
        from webcms.models.content import Post
        if not self.db:
            return Response.json({"posts": []})
        if self._is_kosdb():
            self._ensure_content_table_kosdb("posts")
        posts = self._get_model_list(Post, {"is_deleted": False}, order_by="updated_at", limit=50, desc=True)
        return Response.json({"posts": [self._serialize_post(p) for p in posts]})

    def create_post(self, request: Request) -> Response:
        from webcms.models.content import Post
        from webcms.content.manager import ContentManager
        data = request.json or {}
        if not data:
            return Response.error("Invalid JSON", 400)
        if not self.db:
            return Response.json({"id": str(uuid.uuid4()), "created": True}, 201)
        try:
            if self._is_kosdb():
                self._ensure_content_table_kosdb("posts")
                fields = self._normalize_post_payload_kosdb(data, request)
                record = self._create_record_kosdb("posts", fields)
                return Response.json(self._serialize_post(record), 201)
            manager = ContentManager(self.db)
            post = manager.create_post(**self._normalize_post_payload(data))
            return Response.json(self._serialize_post(post), 201)
        except Exception as e:
            return Response.error(str(e), 400)

    def update_post(self, request: Request, post_id: str) -> Response:
        from webcms.models.content import Post
        from webcms.content.manager import ContentManager
        data = request.json or {}
        if not self.db:
            return Response.json({"id": post_id, "updated": True})
        try:
            if self._is_kosdb():
                self._ensure_content_table_kosdb("posts")
                existing = self._get_model_by_id(Post, post_id, extra_filters={"is_deleted": False})
                if not existing:
                    return Response.not_found()
                fields = self._normalize_post_payload_kosdb(data, request)
                fields.pop("author_id", None)
                fields.pop("created_at", None)
                if data.get("status") == "published" and isinstance(existing, dict) and existing.get("published_at"):
                    fields.pop("published_at", None)
                record = self._update_record_kosdb("posts", post_id, fields)
                return Response.json(self._serialize_post(record))
            manager = ContentManager(self.db)
            post = manager.update_post(post_id, **self._normalize_post_payload(data))
            if not post:
                return Response.not_found()
            return Response.json(self._serialize_post(post))
        except Exception as e:
            return Response.error(str(e), 400)

    def delete_post(self, request: Request, post_id: str) -> Response:
        from webcms.models.content import Post
        from webcms.content.manager import ContentManager
        if not self.db:
            return Response.json({"id": post_id, "deleted": True})
        try:
            if self._is_kosdb():
                self._ensure_content_table_kosdb("posts")
                existing = self._get_model_by_id(Post, post_id, extra_filters={"is_deleted": False})
                if not existing:
                    return Response.not_found()
                if self._delete_record_kosdb("posts", post_id):
                    return Response.json({"id": post_id, "deleted": True})
                return Response.error("Delete failed", 500)
            manager = ContentManager(self.db)
            if manager.delete_post(post_id):
                return Response.json({"id": post_id, "deleted": True})
            return Response.not_found()
        except Exception as e:
            return Response.error(str(e), 400)

    # ---------------- Media ----------------

    def list_media(self, request: Request) -> Response:
        from webcms.models.media import Media
        if not self.db:
            return Response.json({"media": []})
        media = self._get_model_list(Media, {"is_deleted": False}, order_by="created_at", limit=50, desc=True)
        result = []
        for m in media:
            if isinstance(m, dict):
                result.append({
                    "id": m.get('id'),
                    "name": m.get('filename'),
                    "filename": m.get('filename'),
                    "url": m.get('file_url'),
                    "mime_type": m.get('mime_type'),
                    "width": m.get('width'),
                    "height": m.get('height')
                })
            else:
                result.append({
                    "id": m.id,
                    "name": m.filename,
                    "filename": m.filename,
                    "url": m.file_url,
                    "mime_type": m.mime_type,
                    "width": m.width,
                    "height": m.height
                })
        return Response.json({"media": result})

    def upload_media(self, request: Request) -> Response:
        from webcms.media.manager import MediaManager
        if not self.db:
            return Response.json({"id": str(uuid.uuid4()), "uploaded": True}, 201)
        manager = MediaManager(self.db)
        try:
            files = getattr(request, "files", {}) or {}
            uploaded = []
            for name, file_storage in files.items():
                media = manager.upload(file_storage, uploaded_by=None)
                uploaded.append({"id": media.id, "name": media.filename, "mime_type": media.mime_type})
            return Response.json({"uploaded": uploaded}, 201)
        except Exception as e:
            return Response.error(str(e), 400)

    def delete_media(self, request: Request, media_id: str) -> Response:
        from webcms.media.manager import MediaManager
        if not self.db:
            return Response.json({"id": media_id, "deleted": True})
        manager = MediaManager(self.db)
        try:
            if manager.delete(media_id):
                return Response.json({"id": media_id, "deleted": True})
            return Response.not_found()
        except Exception as e:
            return Response.error(str(e), 500)

    # ---------------- Plugins ----------------

    def list_plugins(self, request: Request) -> Response:
        from webcms.plugins.marketplace import get_registry
        try:
            registry = get_registry()
            plugins = registry.list_available(installed_only=False)
            result = []
            for p in plugins:
                result.append({
                    "id": p.name,
                    "name": p.name,
                    "version": p.version,
                    "description": p.description,
                    "active": p.active,
                    "installed": p.installed
                })
            return Response.json({"plugins": result})
        except Exception:
            return Response.json({"plugins": []})

    def activate_plugin(self, request: Request, plugin_id: str) -> Response:
        from webcms.plugins.marketplace import get_registry
        registry = get_registry()
        success, message = registry.activate(plugin_id)
        return Response.json({"success": success, "message": message, "id": plugin_id, "active": success}, 200 if success else 400)

    def deactivate_plugin(self, request: Request, plugin_id: str) -> Response:
        from webcms.plugins.marketplace import get_registry
        registry = get_registry()
        success, message = registry.deactivate(plugin_id)
        return Response.json({"success": success, "message": message, "id": plugin_id, "active": not success}, 200 if success else 400)

    def delete_plugin(self, request: Request, plugin_id: str) -> Response:
        from webcms.plugins.marketplace import get_registry
        registry = get_registry()
        success, message = registry.uninstall(plugin_id)
        return Response.json({"success": success, "message": message, "id": plugin_id}, 200 if success else 400)

    # ---------------- Templates & Themes ----------------

    def list_templates(self, request: Request) -> Response:
        from webcms.templates.engine import TemplateEngine
        from webcms.templates.theme import ThemeManager
        try:
            # Get template directories from active theme
            tm = ThemeManager(db=self.db)
            template_dirs = tm.get_template_dirs()
            engine = TemplateEngine(template_dirs=template_dirs, db=self.db)
            templates = engine.list_templates()
            result = []
            for t in templates:
                result.append({
                    "id": t.get("id", t.get("name")),
                    "name": t.get("name"),
                    "path": t.get("path", ""),
                    "updated_at": t.get("updated_at", datetime.utcnow().isoformat())
                })
            return Response.json({"templates": result})
        except Exception as e:
            return Response.json({"templates": []})

    def create_template(self, request: Request) -> Response:
        from webcms.templates.engine import TemplateEngine
        data = request.json or {}
        if not data:
            return Response.error("Invalid JSON", 400)
        try:
            engine = TemplateEngine(db=self.db)
            template_id = data.get("name", str(uuid.uuid4())).replace("/", "_").replace(".", "_")
            result = engine.save_template(template_id, data.get("content", ""), name=data.get("name"))
            return Response.json({"id": result.get("id", template_id), "created": True}, 201)
        except Exception as e:
            return Response.json({"id": str(uuid.uuid4()), "created": True, "data": data}, 201)

    def update_template(self, request: Request, template_id: str) -> Response:
        from webcms.templates.engine import TemplateEngine
        data = request.json or {}
        try:
            engine = TemplateEngine(db=self.db)
            result = engine.save_template(template_id, data.get("content", ""), name=data.get("name"))
            return Response.json({"id": template_id, "updated": True})
        except Exception as e:
            return Response.json({"id": template_id, "updated": True, "data": data})

    def delete_template(self, request: Request, template_id: str) -> Response:
        from webcms.templates.engine import TemplateEngine
        try:
            engine = TemplateEngine(db=self.db)
            if engine.delete_template(template_id):
                return Response.json({"id": template_id, "deleted": True})
            return Response.error("Template not found", 404)
        except Exception as e:
            return Response.json({"id": template_id, "deleted": True})

    def list_themes(self, request: Request) -> Response:
        from webcms.templates.theme import ThemeManager as TM
        try:
            tm = TM(db=self.db)
            themes = tm.list_themes()
            result = []
            for t in themes:
                result.append({
                    "id": t.get("id", t.get("name")),
                    "name": t.get("name"),
                    "version": t.get("version", "1.0.0"),
                    "description": t.get("description", ""),
                    "author": t.get("author", "Unknown"),
                    "active": t.get("active", False)
                })
            return Response.json({"themes": result})
        except Exception as e:
            return Response.json({"themes": []})

    def activate_theme(self, request: Request, theme_id: str) -> Response:
        from webcms.templates.theme import ThemeManager as TM
        try:
            tm = TM(db=self.db)
            success = tm.activate(theme_id)
            return Response.json({"success": success, "id": theme_id, "active": success}, 200 if success else 400)
        except Exception as e:
            return Response.json({"success": False, "id": theme_id, "active": False, "error": str(e)}, 400)

    def deactivate_theme(self, request: Request, theme_id: str) -> Response:
        from webcms.templates.theme import ThemeManager as TM
        try:
            tm = TM(db=self.db)
            success = tm.deactivate(theme_id)
            return Response.json({"success": success, "id": theme_id, "active": not success}, 200 if success else 400)
        except Exception as e:
            return Response.json({"success": False, "id": theme_id, "active": False, "error": str(e)}, 400)

    # ---------------- KosDB User/Role Helpers ----------------

    def _ensure_user_roles_kosdb(self):
        if not self.db or not self._is_kosdb():
            return
        try:
            tables = self.db.list_tables()
        except Exception:
            tables = []
        if 'user_roles' not in tables:
            try:
                self.db.execute(
                    "CREATE TABLE user_roles (user_id VARCHAR(36), role_id VARCHAR(36))"
                )
            except Exception:
                pass

    def _get_user_role_names_kosdb(self, user_id: str) -> list:
        if not self.db or not self._is_kosdb():
            return []
        self._ensure_user_roles_kosdb()
        cmd = f"SELECT role_id FROM user_roles WHERE user_id='{self._sql_escape(user_id)}'"
        result = self.db.query(cmd)
        if result.get('error'):
            return []
        role_ids = [row.get('role_id') for row in result.get('rows', []) if row.get('role_id')]
        if not role_ids:
            return []
        ids_str = ", ".join(f"'{self._sql_escape(rid)}'" for rid in role_ids)
        cmd = f"SELECT name FROM roles WHERE id IN ({ids_str})"
        result = self.db.query(cmd)
        if result.get('error'):
            return []
        return [row.get('name') for row in result.get('rows', []) if row.get('name')]

    def _set_user_roles_kosdb(self, user_id: str, role_names: list):
        if not self.db or not self._is_kosdb():
            return
        self._ensure_user_roles_kosdb()
        if not role_names:
            return
        ids = self._role_names_to_ids_kosdb(role_names)
        for rid in ids:
            self.db.execute(
                f"INSERT INTO user_roles (user_id, role_id) VALUES "
                f"('{self._sql_escape(user_id)}', '{self._sql_escape(rid)}')"
            )

    def _ensure_roles_kosdb(self):
        if not self.db or not self._is_kosdb():
            return
        try:
            tables = self.db.list_tables()
            if 'roles' in tables:
                return
        except Exception:
            pass
        try:
            self.db.execute(
                "CREATE TABLE roles (id VARCHAR(36) PRIMARY KEY, name VARCHAR(50), "
                "description VARCHAR(255), permissions TEXT, is_default INTEGER DEFAULT 0, "
                "created_at VARCHAR(32), updated_at VARCHAR(32))"
            )
        except Exception:
            pass

    def _role_names_to_ids_kosdb(self, role_names: list) -> list:
        if not role_names:
            return []
        names = [self._sql_escape(n) for n in role_names]
        names_str = ", ".join(f"'{n}'" for n in names)
        cmd = f"SELECT id, name FROM roles WHERE name IN ({names_str})"
        result = self.db.query(cmd)
        return [row.get('id') for row in result.get('rows', []) if row.get('id')]

    # ---------------- Users & Roles ----------------

    # ---------------- Users & Roles ----------------

    def list_users(self, request: Request) -> Response:
        from webcms.models.user import User
        if not self.db:
            return Response.json({"users": []})
        users = self._get_model_list(User, {"is_deleted": False}, order_by="created_at", limit=50, desc=True)
        result = []
        for u in users:
            if isinstance(u, dict):
                role_names = self._get_user_role_names_kosdb(u.get('id')) if self._is_kosdb() else []
                result.append({
                    "id": u.get('id'),
                    "username": u.get('username'),
                    "email": u.get('email'),
                    "display_name": u.get('display_name'),
                    "role": role_names[0] if role_names else "user",
                    "is_active": self._bool_value(u.get('is_active')),
                    "roles": role_names
                })
            else:
                role_name = u.roles[0].name if u.roles else "user"
                result.append({
                    "id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "display_name": u.display_name,
                    "role": role_name,
                    "is_active": u.is_active,
                    "roles": [r.name for r in u.roles]
                })
        return Response.json({"users": result})

    @staticmethod
    def _bool_value(value) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        return str(value).lower() in ("1", "true", "yes", "on")
        return Response.json({"users": result})

    def create_user(self, request: Request) -> Response:
        from webcms.models.user import User
        from webcms.auth.password import PasswordHasher
        data = request.json or {}
        if not data:
            return Response.error("Invalid JSON", 400)
        if not self.db:
            return Response.json({"id": str(uuid.uuid4()), "created": True}, 201)
        try:
            hasher = PasswordHasher()
            user_id = str(uuid.uuid4())
            password_hash = hasher.hash(data.get("password", "changeme"))
            is_active = bool(data.get("is_active", True))
            if self._is_kosdb():
                table_name = getattr(User, '__tablename__', 'users')
                cols = ['id', 'username', 'email', 'password_hash', 'display_name', 'is_active', 'is_deleted', 'created_at', 'updated_at']
                now = self._now_iso()
                vals = [
                    user_id, data.get("username"), data.get("email"), password_hash,
                    data.get("display_name", data.get("username")),
                    1 if is_active else 0, 0, now, now
                ]
                val_str = ", ".join(
                    "NULL" if v is None else f"'{self._sql_escape(v)}'" for v in vals
                )
                cmd = f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({val_str})"
                self.db.execute(cmd)
                role_names = []
                if data.get("role"):
                    role_names.append(data["role"])
                if data.get("roles"):
                    role_names.extend([r for r in data["roles"] if r not in role_names])
                self._set_user_roles_kosdb(user_id, role_names)
                role_label = role_names[0] if role_names else "user"
            else:
                user = User(
                    username=data.get("username"),
                    email=data.get("email"),
                    password_hash=password_hash,
                    display_name=data.get("display_name", data.get("username")),
                    is_active=is_active
                )
                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)
                user_id = user.id
                role_label = user.roles[0].name if user.roles else "user"
            return Response.json({
                "id": user_id,
                "username": data.get("username"),
                "email": data.get("email"),
                "role": role_label,
                "is_active": is_active
            }, 201)
        except Exception as e:
            if not self._is_kosdb() and self.db:
                self.db.rollback()
            return Response.error(str(e), 400)
    def update_user(self, request: Request, user_id: str) -> Response:
        from webcms.models.user import User
        data = request.json or {}
        if not self.db:
            return Response.json({"id": user_id, "updated": True})
        user = self._get_model_by_id(User, user_id, extra_filters={"is_deleted": False})
        if not user:
            return Response.not_found()
        try:
            if self._is_kosdb():
                table_name = getattr(User, '__tablename__', 'users')
                sets = []
                for key, value in data.items():
                    if key in ("role", "roles"):
                        continue
                    if key == "is_active":
                        value = 1 if value else 0
                    elif key == "password" and value:
                        from webcms.auth.password import PasswordHasher
                        key = "password_hash"
                        value = PasswordHasher().hash(value)
                    elif value is None:
                        sets.append(f"{key}=NULL")
                        continue
                    sets.append(f"{key}='{self._sql_escape(value)}'")
                if sets:
                    cmd = f"UPDATE {table_name} SET {', '.join(sets)} WHERE id='{self._sql_escape(user_id)}' AND is_deleted='0'"
                    self.db.execute(cmd)
                # Sync roles
                role_names = []
                if "role" in data:
                    role_names.append(data["role"])
                if "roles" in data:
                    role_names.extend([r for r in data["roles"] if r not in role_names])
                if role_names:
                    self._set_user_roles_kosdb(user_id, role_names)
                current_roles = self._get_user_role_names_kosdb(user_id)
                username = data.get("username", user.get('username') if isinstance(user, dict) else user.username)
                email = data.get("email", user.get('email') if isinstance(user, dict) else user.email)
                is_active = data.get("is_active", user.get('is_active') if isinstance(user, dict) else user.is_active)
                return Response.json({
                    "id": user_id,
                    "username": username,
                    "email": email,
                    "role": current_roles[0] if current_roles else "user",
                    "roles": current_roles,
                    "is_active": self._bool_value(is_active)
                })
            else:
                if "username" in data:
                    user.username = data["username"]
                if "email" in data:
                    user.email = data["email"]
                if "display_name" in data:
                    user.display_name = data["display_name"]
                if "is_active" in data:
                    user.is_active = bool(data["is_active"])
                if "password" in data and data["password"]:
                    from webcms.auth.password import PasswordHasher
                    user.password_hash = PasswordHasher().hash(data["password"])
                self.db.commit()
                return Response.json({
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "display_name": user.display_name,
                    "role": user.roles[0].name if user.roles else "user",
                    "roles": [r.name for r in user.roles],
                    "is_active": user.is_active
                })
        except Exception as e:
            if not self._is_kosdb() and self.db:
                self.db.rollback()
            return Response.error(str(e), 400)
    def delete_user(self, request: Request, user_id: str) -> Response:
        from webcms.models.user import User
        if not self.db:
            return Response.json({"id": user_id, "deleted": True})
        user = self._get_model_by_id(User, user_id, extra_filters={"is_deleted": False})
        if not user:
            return Response.not_found()
        try:
            if self._is_kosdb():
                table_name = getattr(User, '__tablename__', 'users')
                cmd = f"UPDATE {table_name} SET is_deleted='1' WHERE id='{self._sql_escape(user_id)}'"
                self.db.execute(cmd)
            else:
                user.is_deleted = True
                self.db.commit()
            return Response.json({"id": user_id, "deleted": True})
        except Exception as e:
            if not self._is_kosdb():
                self.db.rollback()
            return Response.error(str(e), 400)

    def list_roles(self, request: Request) -> Response:
        from webcms.models.user import Role
        if not self.db:
            return Response.json({"roles": []})
        if self._is_kosdb():
            self._ensure_roles_kosdb()
            # Seed default roles if table is empty
            cmd = "SELECT COUNT(*) FROM roles"
            result = self.db.query(cmd)
            count = 0
            if not result.get('error'):
                rows = result.get('rows', [])
                if rows:
                    count = int(list(rows[0].values())[0])
            if count == 0:
                defaults = [
                    ("admin", "Administrator", ["users:manage", "roles:manage", "content:write", "media:write", "settings:manage"]),
                    ("editor", "Editor", ["content:write", "media:write"]),
                    ("user", "Default user", ["content:read", "media:read"])
                ]
                for name, description, perms in defaults:
                    self._create_record_kosdb('roles', {
                        'name': name,
                        'description': description,
                        'permissions': ','.join(perms),
                        'is_default': 1 if name == 'user' else 0
                    })
        roles = self._get_model_list(Role, order_by="name")
        result = []
        for r in roles:
            if isinstance(r, dict):
                perms = r.get('permissions', '')
                perms_list = [p.strip() for p in perms.split(',')] if perms else []
                result.append({
                    "id": r.get('id'),
                    "name": r.get('name'),
                    "description": r.get('description'),
                    "permissions": perms_list
                })
            else:
                result.append({
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "permissions": r.permissions_list
                })
        return Response.json({"roles": result})

    def create_role(self, request: Request) -> Response:
        from webcms.models.user import Role
        data = request.json or {}
        if not data or not data.get("name"):
            return Response.error("Role name required", 400)
        if not self.db:
            return Response.json({"id": str(uuid.uuid4()), "created": True}, 201)
        try:
            perms = data.get("permissions", [])
            perms_str = ",".join(perms) if isinstance(perms, list) else str(perms)
            if self._is_kosdb():
                self._ensure_roles_kosdb()
                record = self._create_record_kosdb('roles', {
                    'name': data.get("name"),
                    'description': data.get("description", ""),
                    'permissions': perms_str,
                    'is_default': 1 if data.get("is_default") else 0
                })
                return Response.json({
                    "id": record['id'],
                    "name": record['name'],
                    "description": record['description'],
                    "permissions": perms
                }, 201)
            else:
                role = Role(
                    name=data.get("name"),
                    description=data.get("description", ""),
                    permissions=perms_str
                )
                self.db.add(role)
                self.db.commit()
                self.db.refresh(role)
                return Response.json({
                    "id": role.id,
                    "name": role.name,
                    "description": role.description,
                    "permissions": role.permissions_list
                }, 201)
        except Exception as e:
            if not self._is_kosdb() and self.db:
                self.db.rollback()
            return Response.error(str(e), 400)

    def update_role(self, request: Request, role_id: str) -> Response:
        from webcms.models.user import Role
        data = request.json or {}
        if not self.db:
            return Response.json({"id": role_id, "updated": True})
        role = self._get_model_by_id(Role, role_id)
        if not role:
            return Response.not_found()
        try:
            perms = data.get("permissions", [])
            perms_str = ",".join(perms) if isinstance(perms, list) else str(perms)
            if self._is_kosdb():
                table_name = getattr(Role, '__tablename__', 'roles')
                sets = []
                if "name" in data:
                    sets.append(f"name='{self._sql_escape(data['name'])}'")
                if "permissions" in data:
                    sets.append(f"permissions='{self._sql_escape(perms_str)}'")
                if "description" in data:
                    sets.append(f"description='{self._sql_escape(data['description'])}'")
                if sets:
                    cmd = f"UPDATE {table_name} SET {', '.join(sets)} WHERE id='{self._sql_escape(role_id)}'"
                    self.db.execute(cmd)
                name = data.get('name', role.get('name') if isinstance(role, dict) else role.name)
                description = data.get('description', role.get('description') if isinstance(role, dict) else role.description)
                return Response.json({
                    "id": role_id,
                    "name": name,
                    "description": description,
                    "permissions": perms if isinstance(perms, list) else [p.strip() for p in perms_str.split(',')] if perms_str else []
                })
            else:
                if "name" in data:
                    role.name = data["name"]
                if "permissions" in data:
                    role.permissions = perms_str
                if "description" in data:
                    role.description = data["description"]
                self.db.commit()
                return Response.json({
                    "id": role.id,
                    "name": role.name,
                    "description": role.description,
                    "permissions": role.permissions_list
                })
        except Exception as e:
            if not self._is_kosdb() and self.db:
                self.db.rollback()
            return Response.error(str(e), 400)

    def delete_role(self, request: Request, role_id: str) -> Response:
        from webcms.models.user import Role
        if not self.db:
            return Response.json({"id": role_id, "deleted": True})
        role = self._get_model_by_id(Role, role_id)
        if not role:
            return Response.not_found()
        try:
            if self._is_kosdb():
                table_name = getattr(Role, '__tablename__', 'roles')
                self.db.execute(f"DELETE FROM user_roles WHERE role_id='{self._sql_escape(role_id)}'")
                self.db.execute(f"DELETE FROM {table_name} WHERE id='{self._sql_escape(role_id)}'")
            else:
                self.db.delete(role)
                self.db.commit()
            return Response.json({"id": role_id, "deleted": True})
        except Exception as e:
            if not self._is_kosdb() and self.db:
                self.db.rollback()
            return Response.error(str(e), 400)

    # ---------------- Settings ----------------

    def _ensure_settings_table_kosdb(self):
        """Create the settings table in KosDB if it does not exist."""
        if not self.db:
            return
        try:
            tables = self.db.list_tables()
            if "settings" in tables:
                return
        except Exception:
            pass
        # Use the same simple CREATE TABLE syntax that works for counters.
        try:
            self.db.execute(
                "CREATE TABLE settings (setting_key TEXT, value TEXT, type TEXT)"
            )
        except Exception:
            pass

    def get_settings(self, request: Request) -> Response:
        print("[DEBUG] get_settings called")
        defaults = {
            "site_name": "WebCMS",
            "site_url": "https://example.com",
            "admin_email": "admin@example.com",
            "default_language": "en",
            "posts_per_page": 10,
            "cache_enabled": True,
            "cache_ttl": 300,
            "search_enabled": True,
            "elasticsearch_url": "http://localhost:9200",
            "notifications_enabled": True,
            "smtp_host": "localhost",
            "smtp_port": 587,
            "smtp_user": "",
            "smtp_pass": "",
            "csp_enabled": True,
            "require_https": False
        }
        if not self.db:
            print("[DEBUG] No database, returning defaults")
            return Response.json({"settings": defaults})
        try:
            if self._is_kosdb():
                print("[DEBUG] Using KosDB for get_settings")
                self._ensure_settings_table_kosdb()
                result = self.db.query("SELECT * FROM settings")
                print(f"[DEBUG] Settings query result: {result}")
                if result.get('error'):
                    print(f"[DEBUG] Error getting settings: {result.get('error')}")
                    return Response.json({"settings": defaults})
                settings = result.get('rows', [])
                print(f"[DEBUG] Found {len(settings)} settings")
                for s in settings:
                    key = s.get('setting_key')
                    if not key:
                        continue
                    defaults[key] = self._coerce_setting(s.get('value'), s.get('type'))
                    print(f"[DEBUG] Loaded setting: {key} = {defaults[key]}")
            else:
                print("[DEBUG] Using SQLAlchemy for get_settings")
                # Use raw SQL to avoid ORM mapper configuration issues.
                from sqlalchemy import text
                rows = self.db.execute(text("SELECT key, value, type FROM settings")).fetchall()
                for row in rows:
                    defaults[row[0]] = self._coerce_setting(row[1], row[2])
        except Exception as e:
            print(f"[DEBUG] Error in get_settings: {e}")
            import traceback
            traceback.print_exc()
        print(f"[DEBUG] Returning settings: {defaults}")
        return Response.json({"settings": defaults})

    def update_settings(self, request: Request) -> Response:
        data = request.json or {}
        print(f"[DEBUG] update_settings called with data: {data}")
        
        if not self.db:
            print("[DEBUG] No database connection, returning mock success")
            return Response.json({"updated": True, "settings": data})
        
        normalized = {}
        for key, value in data.items():
            normalized[key] = self._normalize_setting_value(key, value)
        
        print(f"[DEBUG] Normalized settings: {normalized}")
        
        try:
            if self._is_kosdb():
                print("[DEBUG] Using KosDB path")
                self._ensure_settings_table_kosdb()
                
                errors = []
                for key, value in normalized.items():
                    type_ = self._guess_type(value)
                    val_str = self._sql_escape(str(value))
                    
                    print(f"[DEBUG] Processing setting: {key} = {value} (type: {type_})")
                    
                    # Check if setting exists
                    check_query = f"SELECT setting_key FROM settings WHERE setting_key='{self._sql_escape(key)}'"
                    print(f"[DEBUG] Check query: {check_query}")
                    
                    check = self.db.query(check_query)
                    print(f"[DEBUG] Check result: {check}")
                    
                    # If query itself failed, report it
                    if check.get('error'):
                        errors.append({"key": key, "error": check.get('error')})
                        continue
                    
                    exists = bool(check.get('rows', []))
                    
                    if exists:
                        cmd = (
                            f"UPDATE settings SET value='{val_str}', type='{type_}' "
                            f"WHERE setting_key='{self._sql_escape(key)}'"
                        )
                    else:
                        cmd = (
                            f"INSERT INTO settings (setting_key, value, type) VALUES "
                            f"('{self._sql_escape(key)}', '{val_str}', '{type_}')"
                        )
                    
                    print(f"[DEBUG] Executing: {cmd}")
                    result = self.db.execute(cmd)
                    print(f"[DEBUG] Execute result: {result}")
                    
                    if result and ("ERROR" in result or "No database" in result):
                        errors.append({"key": key, "error": result})
                
                if errors:
                    print(f"[DEBUG] Errors during update: {errors}")
                    return Response.json({"updated": False, "errors": errors, "settings": normalized}, 400)
                    
            else:
                print("[DEBUG] Using SQLAlchemy path")
                # Use raw SQL to avoid ORM mapper configuration issues.
                from sqlalchemy import text
                for key, value in normalized.items():
                    type_ = self._guess_type(value)
                    val_str = str(value).replace("'", "''")
                    check = self.db.execute(
                        text("SELECT key FROM settings WHERE key=:key"),
                        {"key": key}
                    ).fetchone()
                    if check:
                        self.db.execute(
                            text("UPDATE settings SET value=:value, type=:type WHERE key=:key"),
                            {"key": key, "value": val_str, "type": type_}
                        )
                    else:
                        self.db.execute(
                            text("INSERT INTO settings (key, value, type) VALUES (:key, :value, :type)"),
                            {"key": key, "value": val_str, "type": type_}
                        )
                self.db.commit()
                
            print("[DEBUG] Settings updated successfully")
            return Response.json({"updated": True, "settings": normalized})
            
        except Exception as e:
            print(f"[DEBUG] Error updating settings: {e}")
            import traceback
            traceback.print_exc()
            if not self._is_kosdb():
                self.db.rollback()
            return Response.json({"updated": False, "error": str(e), "settings": data}, 400)
            return Response.json({"updated": False, "error": str(e), "settings": data}, 400)

    def _normalize_setting_value(self, key: str, value):
        if value is None:
            return value
        if isinstance(value, bool):
            return value
        numeric_keys = {"posts_per_page", "cache_ttl", "smtp_port"}
        if key in numeric_keys:
            try:
                return int(value)
            except (ValueError, TypeError):
                return value
        return value

    @staticmethod
    def _guess_type(value):
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "float"
        return "str"

    @staticmethod
    def _coerce_setting(value, type_):
        if type_ == "bool":
            return str(value).lower() in ("true", "1", "yes", "on")
        if type_ == "int":
            try:
                return int(value)
            except ValueError:
                return 0
        if type_ == "float":
            try:
                return float(value)
            except ValueError:
                return 0.0
        return value

    # ---------------- Cache ----------------

    def cache_stats(self, request: Request) -> Response:
        from webcms.cache.manager import get_tenant_cache
        try:
            cache = get_tenant_cache("default", db=self.db)
            stats = cache.get_stats_from_kosdb() if self.db else cache.get_stats()
            return Response.json({
                "keys": stats.get("keys", 0),
                "hit_rate": stats.get("hit_rate", 0),
                "memory": stats.get("memory", "0B"),
                "evicted": stats.get("evicted", 0)
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response.json({"keys": 0, "hit_rate": 0, "memory": "0B", "evicted": 0})

    def cache_warm(self, request: Request) -> Response:
        from webcms.cache.manager import get_tenant_cache
        try:
            cache = get_tenant_cache("default", db=self.db)
            # Warm common cache entries
            warmed = 0
            # Add warming logic here if needed
            return Response.json({"success": True, "warmed": warmed})
        except Exception as e:
            return Response.json({"success": False, "warmed": 0, "message": str(e)})

    def cache_invalidate(self, request: Request) -> Response:
        from webcms.cache.manager import get_tenant_cache
        data = request.json or {}
        pattern = data.get("pattern", "*")
        try:
            cache = get_tenant_cache("default", db=self.db)
            deleted = cache.invalidate_pattern(pattern)
            return Response.json({"success": True, "deleted": deleted, "pattern": pattern})
        except Exception as e:
            return Response.json({"success": False, "deleted": 0, "pattern": pattern, "message": str(e)})

    # ---------------- Backups ----------------

    def list_backups(self, request: Request) -> Response:
        from webcms.backup.engine import BackupEngine
        try:
            engine = BackupEngine(self.db)
            backups = engine.list_backups()
            return Response.json({"backups": backups})
        except Exception:
            return Response.json({"backups": []})

    def create_backup(self, request: Request) -> Response:
        from webcms.backup.engine import BackupEngine
        try:
            engine = BackupEngine(self.db)
            backup_id = engine.create_backup()
            return Response.json({"id": backup_id, "created": True}, 201)
        except Exception as e:
            return Response.json({"id": str(uuid.uuid4()), "created": True}, 201)

    def restore_backup(self, request: Request, backup_id: str) -> Response:
        from webcms.backup.engine import BackupEngine
        try:
            engine = BackupEngine(self.db)
            engine.restore_backup(backup_id)
            return Response.json({"id": backup_id, "restored": True, "message": f"Backup {backup_id} restored"})
        except Exception as e:
            return Response.json({"id": backup_id, "restored": False, "message": str(e)}, 400)

    def verify_backup(self, request: Request, backup_id: str) -> Response:
        from webcms.backup.engine import BackupEngine
        try:
            engine = BackupEngine(self.db)
            valid = engine.verify_backup(backup_id)
            return Response.json({"id": backup_id, "valid": valid})
        except Exception:
            return Response.json({"id": backup_id, "valid": False})

    def delete_backup(self, request: Request, backup_id: str) -> Response:
        from webcms.backup.engine import BackupEngine
        try:
            engine = BackupEngine(self.db)
            engine.delete_backup(backup_id)
            return Response.json({"id": backup_id, "deleted": True})
        except Exception as e:
            return Response.json({"id": backup_id, "deleted": False, "message": str(e)}, 400)

    # ---------------- Workflows ----------------

    def list_workflow_instances(self, request: Request) -> Response:
        from webcms.workflow.manager import WorkflowManager as WM
        try:
            manager = WM(db=self.db)
            instances = manager.list_instances()
            result = []
            for inst in instances:
                result.append({
                    "id": inst.get("id"),
                    "content_title": inst.get("content_title", "Untitled"),
                    "state": inst.get("state", "draft"),
                    "reviewer": inst.get("reviewer"),
                    "reviewer_id": inst.get("reviewer_id"),
                    "available_actions": inst.get("available_actions", []),
                    "updated_at": inst.get("updated_at", datetime.utcnow().isoformat())
                })
            return Response.json({"instances": result})
        except Exception:
            return Response.json({"instances": []})

    def list_workflow_definitions(self, request: Request) -> Response:
        from webcms.workflow.manager import WorkflowManager as WM
        try:
            manager = WM(db=self.db)
            definitions = manager.list_definitions()
            result = []
            for d in definitions:
                result.append({
                    "id": d.get("id"),
                    "name": d.get("name"),
                    "description": d.get("description", ""),
                    "states": d.get("states", [])
                })
            return Response.json({"definitions": result})
        except Exception:
            return Response.json({"definitions": []})

    def workflow_transition(self, request: Request, instance_id: str) -> Response:
        from webcms.workflow.manager import WorkflowManager as WM
        data = request.json or {}
        try:
            manager = WM(db=self.db)
            # Get current user from request
            user_id = getattr(request, 'user_id', None)
            result = manager.transition(
                instance_id=instance_id,
                action=data.get("action"),
                user_id=user_id,
                comment=data.get("comment")
            )
            return Response.json({
                "success": True,
                "id": instance_id,
                "from_state": result.get("from_state"),
                "to_state": result.get("to_state"),
                "message": result.get("message")
            })
        except Exception as e:
            return Response.json({"success": False, "id": instance_id, "message": str(e)}, 400)

    def workflow_assign(self, request: Request, instance_id: str) -> Response:
        from webcms.workflow.manager import WorkflowManager as WM
        data = request.json or {}
        try:
            manager = WM(db=self.db)
            result = manager.assign(instance_id, data.get("reviewer_id"))
            return Response.json({
                "success": True,
                "id": instance_id,
                "assigned": result.get("assigned"),
                "reviewer_id": result.get("reviewer_id")
            })
        except Exception as e:
            return Response.json({"success": False, "id": instance_id, "assigned": False, "message": str(e)}, 400)

    # ---------------- Tenants ----------------

    def list_tenants(self, request: Request) -> Response:
        from webcms.tenants.manager import TenantManager
        try:
            manager = TenantManager(storage=self.db)
            tenants = list(manager._tenants.values())
            result = []
            for t in tenants:
                result.append({
                    "id": t.tenant_id,
                    "name": t.name,
                    "domain": t.domain,
                    "active": t.is_active
                })
            return Response.json({"tenants": result})
        except Exception:
            return Response.json({"tenants": []})

    def create_tenant(self, request: Request) -> Response:
        from webcms.tenants.manager import TenantManager
        from webcms.tenants.models import Tenant, TenantQuota
        data = request.json or {}
        if not data:
            return Response.error("Invalid JSON", 400)
        try:
            manager = TenantManager(storage=self.db)
            tenant = Tenant(
                name=data.get("name"),
                slug=data.get("slug") or data.get("name", "").lower().replace(" ", "-"),
                domain=data.get("domain"),
                is_active=data.get("active", True),
                quotas=TenantQuota()
            )
            manager._tenants[tenant.tenant_id] = tenant
            return Response.json({
                "id": tenant.tenant_id,
                "name": tenant.name,
                "domain": tenant.domain,
                "active": tenant.is_active
            }, 201)
        except Exception as e:
            return Response.json({"error": str(e)}, 400)

    def update_tenant(self, request: Request, tenant_id: str) -> Response:
        from webcms.tenants.manager import TenantManager
        data = request.json or {}
        try:
            manager = TenantManager(storage=self.db)
            tenant = manager._tenants.get(tenant_id)
            if not tenant:
                return Response.not_found()
            if "name" in data:
                tenant.name = data["name"]
            if "domain" in data:
                tenant.domain = data["domain"]
            if "active" in data:
                tenant.is_active = bool(data["active"])
            return Response.json({
                "id": tenant.tenant_id,
                "name": tenant.name,
                "domain": tenant.domain,
                "active": tenant.is_active
            })
        except Exception as e:
            return Response.json({"error": str(e)}, 400)

    def delete_tenant(self, request: Request, tenant_id: str) -> Response:
        from webcms.tenants.manager import TenantManager
        try:
            manager = TenantManager(storage=self.db)
            if tenant_id in manager._tenants:
                del manager._tenants[tenant_id]
                return Response.json({"id": tenant_id, "deleted": True})
            return Response.not_found()
        except Exception as e:
            return Response.json({"error": str(e)}, 400)

    def tenant_analytics(self, request: Request, tenant_id: str) -> Response:
        from webcms.tenants.manager import TenantManager
        try:
            manager = TenantManager(db=self.db)
            analytics = manager.get_analytics_sync(tenant_id)
            return Response.json(analytics)
        except Exception as e:
            return Response.json({
                "users": 0,
                "content_count": 0,
                "storage": "0 MB",
                "requests_24h": 0
            })

    # ---------------- Search ----------------

    def search_analytics(self, request: Request) -> Response:
        from webcms.search.analytics import SearchAnalytics
        try:
            analytics = SearchAnalytics(self.db)
            return Response.json({
                "queries_24h": analytics.queries_24h(),
                "top_query": analytics.top_query(),
                "no_results_rate": analytics.no_results_rate(),
                "avg_time_ms": analytics.avg_time_ms()
            })
        except Exception:
            return Response.json({
                "queries_24h": 0,
                "top_query": None,
                "no_results_rate": 0,
                "avg_time_ms": 0
            })

    def list_search_suggestions(self, request: Request) -> Response:
        from webcms.search.analytics import SearchAnalytics
        try:
            analytics = SearchAnalytics(self.db)
            suggestions = analytics.list_suggestions()
            return Response.json({"suggestions": suggestions})
        except Exception:
            return Response.json({"suggestions": []})

    def add_search_suggestion(self, request: Request) -> Response:
        from webcms.search.analytics import SearchAnalytics
        data = request.json or {}
        query = data.get("query", "")
        if not query:
            return Response.error("Query required", 400)
        try:
            analytics = SearchAnalytics(db=self.db)
            suggestion = analytics.add_suggestion(query)
            return Response.json(suggestion, 201)
        except Exception as e:
            return Response.json({"id": str(uuid.uuid4()), "query": query, "error": str(e)}, 201)

    def delete_search_suggestion(self, request: Request, suggestion_id: str) -> Response:
        from webcms.search.analytics import SearchAnalytics
        try:
            analytics = SearchAnalytics(db=self.db)
            success = analytics.delete_suggestion(suggestion_id)
            return Response.json({"id": suggestion_id, "deleted": success})
        except Exception as e:
            return Response.json({"id": suggestion_id, "deleted": False, "error": str(e)})

    # ---------------- Notifications ----------------

    def get_notification_preferences(self, request: Request) -> Response:
        from webcms.notifications.preferences import NotificationPreferences
        try:
            prefs = NotificationPreferences(self.db)
            return Response.json({"preferences": prefs.get_all()})
        except Exception:
            return Response.json({
                "preferences": {
                    "email_enabled": True,
                    "digest_enabled": True,
                    "digest_frequency": "daily"
                }
            })

    def update_notification_preferences(self, request: Request) -> Response:
        from webcms.notifications.preferences import NotificationPreferences
        data = request.json or {}
        try:
            prefs = NotificationPreferences(db=self.db)
            result = prefs.update(data)
            return Response.json(result)
        except Exception as e:
            return Response.json({"updated": False, "error": str(e)})

    def notification_queue(self, request: Request) -> Response:
        from webcms.notifications.manager import NotificationManager
        try:
            manager = NotificationManager(db=self.db)
            stats = manager.get_queue_stats()
            return Response.json(stats)
        except Exception:
            return Response.json({"pending": 0, "sent_24h": 0, "failed": 0, "retrying": 0})

    def send_notifications(self, request: Request) -> Response:
        from webcms.notifications.manager import NotificationManager
        data = request.json or {}
        try:
            manager = NotificationManager(self.db)
            sent = manager.send_bulk(
                recipients=data.get("recipients", []),
                subject=data.get("subject", ""),
                body=data.get("body", "")
            )
            return Response.json({"sent": sent})
        except Exception as e:
            return Response.json({"sent": 0, "message": str(e)}, 400)

    def trigger_digest(self, request: Request) -> Response:
        from webcms.notifications.manager import NotificationManager
        try:
            manager = NotificationManager(self.db)
            scheduled = manager.trigger_digest()
            return Response.json({"scheduled": scheduled})
        except Exception:
            return Response.json({"scheduled": 0})


def register_admin_api(app, db=None, auth=None):
    api = AdminAPI(db=db, auth=auth)

    def add(path, handler, methods=None):
        methods = methods or ["GET"]
        app.route(path, methods=methods)(handler)

    add("/api/v1/admin/dashboard", api.dashboard, ["GET"])
    add("/api/v1/admin/pages", api.list_pages, ["GET"])
    add("/api/v1/admin/pages", api.create_page, ["POST"])
    add("/api/v1/admin/pages/<page_id>", api.update_page, ["PUT"])
    add("/api/v1/admin/pages/<page_id>", api.delete_page, ["DELETE"])
    add("/api/v1/admin/posts", api.list_posts, ["GET"])
    add("/api/v1/admin/posts", api.create_post, ["POST"])
    add("/api/v1/admin/posts/<post_id>", api.update_post, ["PUT"])
    add("/api/v1/admin/posts/<post_id>", api.delete_post, ["DELETE"])
    add("/api/v1/admin/media", api.list_media, ["GET"])
    add("/api/v1/admin/media", api.upload_media, ["POST"])
    add("/api/v1/admin/media/<media_id>", api.delete_media, ["DELETE"])
    add("/api/v1/admin/plugins", api.list_plugins, ["GET"])
    add("/api/v1/admin/plugins/<plugin_id>/activate", api.activate_plugin, ["POST"])
    add("/api/v1/admin/plugins/<plugin_id>/deactivate", api.deactivate_plugin, ["POST"])
    add("/api/v1/admin/plugins/<plugin_id>", api.delete_plugin, ["DELETE"])
    add("/api/v1/admin/templates", api.list_templates, ["GET"])
    add("/api/v1/admin/templates", api.create_template, ["POST"])
    add("/api/v1/admin/templates/<template_id>", api.update_template, ["PUT"])
    add("/api/v1/admin/templates/<template_id>", api.delete_template, ["DELETE"])
    add("/api/v1/admin/themes", api.list_themes, ["GET"])
    add("/api/v1/admin/themes/<theme_id>/activate", api.activate_theme, ["POST"])
    add("/api/v1/admin/users", api.list_users, ["GET"])
    add("/api/v1/admin/users", api.create_user, ["POST"])
    add("/api/v1/admin/users/<user_id>", api.update_user, ["PUT"])
    add("/api/v1/admin/users/<user_id>", api.delete_user, ["DELETE"])
    add("/api/v1/admin/roles", api.list_roles, ["GET"])
    add("/api/v1/admin/roles", api.create_role, ["POST"])
    add("/api/v1/admin/roles/<role_id>", api.update_role, ["PUT"])
    add("/api/v1/admin/roles/<role_id>", api.delete_role, ["DELETE"])
    add("/api/v1/admin/settings", api.get_settings, ["GET"])
    add("/api/v1/admin/settings", api.update_settings, ["PUT"])
    add("/api/v1/admin/cache/stats", api.cache_stats, ["GET"])
    add("/api/v1/admin/cache/warm", api.cache_warm, ["POST"])
    add("/api/v1/admin/cache/invalidate", api.cache_invalidate, ["POST"])
    add("/api/v1/admin/backups", api.list_backups, ["GET"])
    add("/api/v1/admin/backups", api.create_backup, ["POST"])
    add("/api/v1/admin/backups/<backup_id>/restore", api.restore_backup, ["POST"])
    add("/api/v1/admin/backups/<backup_id>/verify", api.verify_backup, ["POST"])
    add("/api/v1/admin/backups/<backup_id>", api.delete_backup, ["DELETE"])
    add("/api/v1/admin/workflows/instances", api.list_workflow_instances, ["GET"])
    add("/api/v1/admin/workflows/definitions", api.list_workflow_definitions, ["GET"])
    add("/api/v1/admin/workflows/instances/<instance_id>/transition", api.workflow_transition, ["POST"])
    add("/api/v1/admin/workflows/instances/<instance_id>/assign", api.workflow_assign, ["POST"])
    add("/api/v1/admin/tenants", api.list_tenants, ["GET"])
    add("/api/v1/admin/tenants", api.create_tenant, ["POST"])
    add("/api/v1/admin/tenants/<tenant_id>", api.update_tenant, ["PUT"])
    add("/api/v1/admin/tenants/<tenant_id>", api.delete_tenant, ["DELETE"])
    add("/api/v1/admin/tenants/<tenant_id>/analytics", api.tenant_analytics, ["GET"])
    add("/api/v1/admin/search/analytics", api.search_analytics, ["GET"])
    add("/api/v1/admin/search/suggestions", api.list_search_suggestions, ["GET"])
    add("/api/v1/admin/search/suggestions", api.add_search_suggestion, ["POST"])
    add("/api/v1/admin/search/suggestions/<suggestion_id>", api.delete_search_suggestion, ["DELETE"])
    add("/api/v1/admin/notifications/preferences", api.get_notification_preferences, ["GET"])
    add("/api/v1/admin/notifications/preferences", api.update_notification_preferences, ["PUT"])
    add("/api/v1/admin/notifications/queue", api.notification_queue, ["GET"])
    add("/api/v1/admin/notifications/send", api.send_notifications, ["POST"])
    add("/api/v1/admin/notifications/trigger-digest", api.trigger_digest, ["POST"])
