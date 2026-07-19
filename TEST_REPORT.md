# Task 7/7 Test Report

## Server Startup
```bash
cd webcms
python -m webcms.cli.commands serve --host 127.0.0.1 --port 43805 --debug
```
Server responds on http://127.0.0.1:43805/

## Test Commands and Expected Responses

### 1. Change site name and verify persistence
```bash
curl -X PUT http://127.0.0.1:43805/api/v1/admin/settings \
  -H "Content-Type: application/json" \
  -d '{"site_name":"Test Site Alpha"}'
```
Expected: `200 OK` with `{"updated": true, "settings": {"site_name": "Test Site Alpha"}}`

```bash
curl http://127.0.0.1:43805/api/v1/admin/settings
```
Expected: `200 OK` with `settings.site_name == "Test Site Alpha"`

### 2. Create and update a page
```bash
curl -X POST http://127.0.0.1:43805/api/v1/admin/pages \
  -H "Content-Type: application/json" \
  -d '{"title":"Hello Page","slug":"hello-page-1","content":"Initial content"}'
```
Expected: `201 Created` with page JSON including `id`, `title`, `slug`.

```bash
curl -X PUT http://127.0.0.1:43805/api/v1/admin/pages/hello-page-1 \
  -H "Content-Type: application/json" \
  -d '{"title":"Hello Page Updated","content":"Updated content"}'
```
Expected: `200 OK` with updated page JSON.

### 3. Activate/deactivate a plugin
```bash
curl -X POST http://127.0.0.1:43805/api/v1/admin/plugins/contact_form/activate
curl -X POST http://127.0.0.1:43805/api/v1/admin/plugins/contact_form/deactivate
```
Expected: `200 OK` with `{"success": true, "message": "Plugin activated/deactivated", "id": "contact_form", "active": true/false}`

### 4. Create and edit a template
```bash
curl -X POST http://127.0.0.1:43805/api/v1/admin/templates \
  -H "Content-Type: application/json" \
  -d '{"name":"test-template","content":"<html><body>{{content}}</body></html>"}'
```
Expected: `201 Created` with `{"id": "test-template", "created": true}`

```bash
curl -X PUT http://127.0.0.1:43805/api/v1/admin/templates/test-template \
  -H "Content-Type: application/json" \
  -d '{"name":"test-template","content":"<html><body><h1>{{title}}</h1>{{content}}</body></html>"}'
```
Expected: `200 OK` with `{"id": "test-template", "updated": true}`

## KosDB / SQLAlchemy Errors Captured and Fixed

1. **Settings read failed**: `DatabaseManager` has no `execute()`. Fixed by adding `_sa_session()` helper and using ORM session.
2. **Settings update failed**: SQLite DateTime columns received ISO strings. Fixed by passing `datetime.utcnow()` objects.
3. **Page list/create/update failed**: `DatabaseManager` passed to `ContentManager` which expects a session. Fixed `_get_model_*` helpers and page handlers to use `_sa_session()`.
4. **Page creation foreign key error**: `author_id` was a non-existent user. Added `_ensure_system_user()` to create a default `system` user.
5. **Page update 404**: route passed slug but `update_page` expected UUID. Fixed to lookup by slug fallback.
6. **GET pages detached instance error**: `_resolve_author_display` lazy-loaded `author` after session close. Fixed to use `author_id` only.
7. **Template/plugin routes 404**: Router only supported `{param}` syntax, not Flask `<param>`. Fixed `Router._compile_pattern` to support both and process `<param>` before `{param}` to avoid regex collisions.
