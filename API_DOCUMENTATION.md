# WebCMS Admin API Documentation

## Base URL
```
/api/v1/admin
```

## Authentication
All endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

## Response Format
All responses are JSON with the following structure:
```json
{
  "data": {},           // Response data
  "error": null,        // Error message if failed
  "success": true       // Boolean indicating success
}
```

---

## Dashboard

### Get Dashboard Stats
```http
GET /api/v1/admin/dashboard
```

**Response:**
```json
{
  "widgets": [
    {
      "id": "stats",
      "title": "Content Statistics",
      "icon": "📊",
      "data": {
        "users": {"total": 100, "active": 80},
        "content": {"posts": 50, "pages": 20},
        "media": {"total": 200}
      }
    }
  ]
}
```

---

## Content Management

### Pages

#### List Pages
```http
GET /api/v1/admin/pages
```

**Response:**
```json
{
  "pages": [
    {
      "id": "uuid",
      "title": "Page Title",
      "slug": "page-slug",
      "status": "published",
      "author": "Author Name",
      "updated_at": "2024-01-15T10:30:00"
    }
  ]
}
```

#### Create Page
```http
POST /api/v1/admin/pages
Content-Type: application/json

{
  "title": "New Page",
  "slug": "new-page",
  "content": "Page content...",
  "status": "draft",
  "template": "page.html"
}
```

#### Update Page
```http
PUT /api/v1/admin/pages/{page_id}
Content-Type: application/json

{
  "title": "Updated Title",
  "content": "Updated content..."
}
```

#### Delete Page
```http
DELETE /api/v1/admin/pages/{page_id}
```

### Posts

#### List Posts
```http
GET /api/v1/admin/posts
```

**Response:**
```json
{
  "posts": [
    {
      "id": "uuid",
      "title": "Post Title",
      "slug": "post-slug",
      "status": "published",
      "author": "Author Name",
      "updated_at": "2024-01-15T10:30:00"
    }
  ]
}
```

#### Create Post
```http
POST /api/v1/admin/posts
Content-Type: application/json

{
  "title": "New Post",
  "slug": "new-post",
  "content": "Post content...",
  "status": "draft",
  "format": "markdown"
}
```

#### Update Post
```http
PUT /api/v1/admin/posts/{post_id}
Content-Type: application/json

{
  "title": "Updated Title",
  "status": "published"
}
```

#### Delete Post
```http
DELETE /api/v1/admin/posts/{post_id}
```

---

## Media Management

### List Media
```http
GET /api/v1/admin/media
```

**Response:**
```json
{
  "media": [
    {
      "id": "uuid",
      "name": "image.jpg",
      "filename": "image.jpg",
      "url": "/uploads/image.jpg",
      "mime_type": "image/jpeg",
      "width": 1920,
      "height": 1080
    }
  ]
}
```

### Upload Media
```http
POST /api/v1/admin/media
Content-Type: multipart/form-data

file: <binary data>
```

### Delete Media
```http
DELETE /api/v1/admin/media/{media_id}
```

---

## User Management

### List Users
```http
GET /api/v1/admin/users
```

**Response:**
```json
{
  "users": [
    {
      "id": "uuid",
      "username": "johndoe",
      "email": "john@example.com",
      "display_name": "John Doe",
      "role": "admin",
      "roles": ["admin"],
      "is_active": true
    }
  ]
}
```

### Create User
```http
POST /api/v1/admin/users
Content-Type: application/json

{
  "username": "newuser",
  "email": "new@example.com",
  "password": "securepassword",
  "display_name": "New User",
  "role": "user",
  "is_active": true
}
```

### Update User
```http
PUT /api/v1/admin/users/{user_id}
Content-Type: application/json

{
  "email": "updated@example.com",
  "is_active": false
}
```

### Delete User
```http
DELETE /api/v1/admin/users/{user_id}
```

---

## Role Management

### List Roles
```http
GET /api/v1/admin/roles
```

**Response:**
```json
{
  "roles": [
    {
      "id": "uuid",
      "name": "admin",
      "description": "Administrator",
      "permissions": ["users:manage", "content:write"]
    }
  ]
}
```

### Create Role
```http
POST /api/v1/admin/roles
Content-Type: application/json

{
  "name": "editor",
  "description": "Content Editor",
  "permissions": ["content:write", "media:write"]
}
```

### Update Role
```http
PUT /api/v1/admin/roles/{role_id}
Content-Type: application/json

{
  "permissions": ["content:read", "content:write"]
}
```

### Delete Role
```http
DELETE /api/v1/admin/roles/{role_id}
```

---

## Plugin Management

### List Plugins
```http
GET /api/v1/admin/plugins
```

**Response:**
```json
{
  "plugins": [
    {
      "id": "plugin-name",
      "name": "Plugin Name",
      "version": "1.0.0",
      "description": "Plugin description",
      "active": true,
      "installed": true
    }
  ]
}
```

### Activate Plugin
```http
POST /api/v1/admin/plugins/{plugin_id}/activate
```

### Deactivate Plugin
```http
POST /api/v1/admin/plugins/{plugin_id}/deactivate
```

### Delete Plugin
```http
DELETE /api/v1/admin/plugins/{plugin_id}
```

---

## Template Management

### List Templates
```http
GET /api/v1/admin/templates
```

**Response:**
```json
{
  "templates": [
    {
      "id": "home",
      "name": "Home",
      "path": "templates/home.html",
      "updated_at": "2024-01-15T10:30:00"
    }
  ]
}
```

### Create Template
```http
POST /api/v1/admin/templates
Content-Type: application/json

{
  "name": "New Template",
  "content": "<html>...</html>"
}
```

### Update Template
```http
PUT /api/v1/admin/templates/{template_id}
Content-Type: application/json

{
  "content": "<html>Updated...</html>"
}
```

### Delete Template
```http
DELETE /api/v1/admin/templates/{template_id}
```

---

## Theme Management

### List Themes
```http
GET /api/v1/admin/themes
```

**Response:**
```json
{
  "themes": [
    {
      "id": "default",
      "name": "Default Theme",
      "version": "1.0.0",
      "description": "Default theme",
      "author": "WebCMS",
      "active": true
    }
  ]
}
```

### Activate Theme
```http
POST /api/v1/admin/themes/{theme_id}/activate
```

---

## Workflow Management

### List Workflow Instances
```http
GET /api/v1/admin/workflows/instances
```

**Response:**
```json
{
  "instances": [
    {
      "id": "uuid",
      "content_title": "Post Title",
      "state": "review",
      "reviewer": "John Doe",
      "available_actions": ["approve", "reject"]
    }
  ]
}
```

### List Workflow Definitions
```http
GET /api/v1/admin/workflows/definitions
```

### Workflow Transition
```http
POST /api/v1/admin/workflows/instances/{instance_id}/transition
Content-Type: application/json

{
  "action": "approve",
  "comment": "Looks good!"
}
```

### Workflow Assign
```http
POST /api/v1/admin/workflows/instances/{instance_id}/assign
Content-Type: application/json

{
  "reviewer_id": "user-uuid"
}
```

---

## Cache Management

### Get Cache Stats
```http
GET /api/v1/admin/cache/stats
```

**Response:**
```json
{
  "keys": 100,
  "hit_rate": 0.85,
  "memory": "50MB",
  "evicted": 10
}
```

### Warm Cache
```http
POST /api/v1/admin/cache/warm
```

### Invalidate Cache
```http
POST /api/v1/admin/cache/invalidate
Content-Type: application/json

{
  "pattern": "*"
}
```

---

## Backup Management

### List Backups
```http
GET /api/v1/admin/backups
```

**Response:**
```json
{
  "backups": [
    {
      "id": "backup-123",
      "name": "Backup 2024-01-15",
      "type": "full",
      "status": "completed",
      "size": 10485760,
      "created_at": "2024-01-15T10:00:00"
    }
  ]
}
```

### Create Backup
```http
POST /api/v1/admin/backups
```

### Restore Backup
```http
POST /api/v1/admin/backups/{backup_id}/restore
```

### Verify Backup
```http
POST /api/v1/admin/backups/{backup_id}/verify
```

### Delete Backup
```http
DELETE /api/v1/admin/backups/{backup_id}
```

---

## Tenant Management

### List Tenants
```http
GET /api/v1/admin/tenants
```

**Response:**
```json
{
  "tenants": [
    {
      "id": "uuid",
      "name": "Tenant Name",
      "domain": "tenant.example.com",
      "active": true
    }
  ]
}
```

### Create Tenant
```http
POST /api/v1/admin/tenants
Content-Type: application/json

{
  "name": "New Tenant",
  "slug": "new-tenant",
  "domain": "new.example.com"
}
```

### Update Tenant
```http
PUT /api/v1/admin/tenants/{tenant_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "active": false
}
```

### Delete Tenant
```http
DELETE /api/v1/admin/tenants/{tenant_id}
```

### Get Tenant Analytics
```http
GET /api/v1/admin/tenants/{tenant_id}/analytics
```

---

## Search Management

### Get Search Analytics
```http
GET /api/v1/admin/search/analytics
```

**Response:**
```json
{
  "queries_24h": 150,
  "top_query": "webcms",
  "no_results_rate": 0.05,
  "avg_time_ms": 45
}
```

### List Search Suggestions
```http
GET /api/v1/admin/search/suggestions
```

### Add Search Suggestion
```http
POST /api/v1/admin/search/suggestions
Content-Type: application/json

{
  "query": "popular search term"
}
```

### Delete Search Suggestion
```http
DELETE /api/v1/admin/search/suggestions/{suggestion_id}
```

---

## Notification Management

### Get Notification Preferences
```http
GET /api/v1/admin/notifications/preferences
```

**Response:**
```json
{
  "preferences": {
    "email_enabled": true,
    "digest_enabled": true,
    "digest_frequency": "daily"
  }
}
```

### Update Notification Preferences
```http
PUT /api/v1/admin/notifications/preferences
Content-Type: application/json

{
  "email_enabled": false
}
```

### Get Notification Queue
```http
GET /api/v1/admin/notifications/queue
```

### Send Notifications
```http
POST /api/v1/admin/notifications/send
Content-Type: application/json

{
  "recipients": ["user1@example.com", "user2@example.com"],
  "subject": "Notification Subject",
  "body": "Notification body..."
}
```

### Trigger Digest
```http
POST /api/v1/admin/notifications/trigger-digest
```

---

## Settings

### Get Settings
```http
GET /api/v1/admin/settings
```

**Response:**
```json
{
  "settings": {
    "site_name": "My Site",
    "site_url": "https://example.com",
    "admin_email": "admin@example.com",
    "default_language": "en",
    "posts_per_page": 10,
    "cache_enabled": true
  }
}
```

### Update Settings
```http
PUT /api/v1/admin/settings
Content-Type: application/json

{
  "site_name": "New Site Name",
  "posts_per_page": 20
}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 404 | Not Found |
| 500 | Server Error |

## Rate Limiting

API requests are limited to:
- 100 requests per minute for read operations
- 20 requests per minute for write operations

## Support

For API support, contact: api-support@webcms.example.com
