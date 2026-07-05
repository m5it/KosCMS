# WebCMS - Modern Python Content Management System

A production-ready CMS with plugin architecture, template system, and HTTPS support.

## Features

- **Plugin System**: Hook-based architecture with secure sandbox
- **Theme Engine**: Jinja2 templates with asset pipeline
- **HTTPS/Security**: SSL/TLS, security headers, CSRF/XSS protection
- **Content Management**: Pages, posts, categories, tags with revisions
- **Media Library**: Image processing, multiple storage backends
- **Admin Dashboard**: React-based UI with REST API
- **Authentication**: JWT tokens, RBAC, OAuth2, 2FA support
- **Database**: SQLAlchemy ORM with migrations, soft delete, audit logging

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python run.py --debug

# Or with Docker
docker-compose up -d
```

## Project Structure

```
webcms/
├── core/           # Framework: Application, Router, Middleware
├── models/         # Database: User, Post, Page, Media, etc.
├── auth/           # Authentication: JWT, RBAC, OAuth2
├── templates/      # Theme system with Jinja2
├── plugins/        # Plugin architecture
├── content/        # Content management
├── media/          # File uploads and storage
├── security/       # HTTPS, CSRF, XSS protection
├── admin/          # Admin dashboard and API
├── database/       # Database connection and migrations
└── config/         # Configuration files
```

## Configuration

Edit `config/config.yaml`:

```yaml
app:
  name: MySite
  debug: false
  secret_key: "your-secret-key"

server:
  host: "0.0.0.0"
  port: 8000
  ssl_cert: "ssl/cert.pem"
  ssl_key: "ssl/key.pem"

database:
  url: "postgresql://user:pass@localhost/webcms"
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/dashboard` | Dashboard statistics |
| `GET /api/v1/posts` | List posts |
| `POST /api/v1/posts` | Create post |
| `GET /api/v1/posts/<id>` | Get post |
| `PUT /api/v1/posts/<id>` | Update post |
| `DELETE /api/v1/posts/<id>` | Delete post |
| `GET /api/v1/users` | List users |
| `GET /api/v1/media` | List media files |

## Plugin Development

```python
from webcms.plugins import PluginBase, PluginConfig

class MyPlugin(PluginBase):
    def register(self):
        self.register_hook("post_save", self.on_post_save)
    
    def activate(self):
        return True
    
    def on_post_save(self, post, **kwargs):
        print(f"Post saved: {post.title}")
```

## Security Features

- HTTPS redirect with HSTS
- Content Security Policy headers
- CSRF token validation
- XSS input filtering
- Rate limiting
- SQL injection prevention

## Deployment

```bash
# Production with Docker
docker-compose -f docker-compose.yml up -d

# With systemd
sudo cp systemd/webcms.service /etc/systemd/system/
sudo systemctl enable webcms
sudo systemctl start webcms
```

## License

MIT License