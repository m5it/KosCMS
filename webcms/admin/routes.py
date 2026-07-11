"""
Admin Routes

Server-side rendered admin pages.
"""

from webcms.core.request import Request
from webcms.core.response import Response


def admin_routes(app):
    """Register admin routes."""
    
    @app.route("/admin", methods=["GET"])
    def admin_index(request):
        """Admin dashboard."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>WebCMS Admin</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: -apple-system, system-ui, sans-serif;
                    background: #f5f5f5;
                }
                .admin-layout {
                    display: flex;
                    min-height: 100vh;
                }
                .sidebar {
                    width: 250px;
                    background: #1a1a2e;
                    color: white;
                    padding: 1rem;
                }
                .sidebar h1 {
                    font-size: 1.5rem;
                    margin-bottom: 2rem;
                    color: #e94560;
                }
                .nav-menu {
                    list-style: none;
                }
                .nav-menu li {
                    margin-bottom: 0.5rem;
                }
                .nav-menu a {
                    color: #a0a0a0;
                    text-decoration: none;
                    display: block;
                    padding: 0.75rem 1rem;
                    border-radius: 4px;
                    transition: all 0.2s;
                }
                .nav-menu a:hover, .nav-menu a.active {
                    background: #0f3460;
                    color: white;
                }
                .main-content {
                    flex: 1;
                    padding: 2rem;
                }
                .header {
                    background: white;
                    padding: 1.5rem;
                    border-radius: 8px;
                    margin-bottom: 2rem;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 1.5rem;
                }
                .stat-card {
                    background: white;
                    padding: 1.5rem;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .stat-card h3 {
                    color: #666;
                    font-size: 0.9rem;
                    text-transform: uppercase;
                    margin-bottom: 0.5rem;
                }
                .stat-card .value {
                    font-size: 2rem;
                    font-weight: bold;
                    color: #1a1a2e;
                }
            </style>
        </head>
        <body>
            <div class="admin-layout">
                <aside class="sidebar">
                    <h1>🔧 WebCMS</h1>
                    <nav>
                        <ul class="nav-menu">
                            <li><a href="/admin" class="active">Dashboard</a></li>
                            <li><a href="/admin/posts">Posts</a></li>
                            <li><a href="/admin/pages">Pages</a></li>
                            <li><a href="/admin/media">Media</a></li>
                            <li><a href="/admin/users">Users</a></li>
                            <li><a href="/admin/plugins">Plugins</a></li>
                            <li><a href="/admin/themes">Themes</a></li>
                            <li><a href="/admin/settings">Settings</a></li>
                        </ul>
                    </nav>
                </aside>
                <main class="main-content">
                    <div class="header">
                        <h2>Dashboard</h2>
                    </div>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <h3>Total Posts</h3>
                            <div class="value" id="post-count">-</div>
                        </div>
                        <div class="stat-card">
                            <h3>Published</h3>
                            <div class="value" id="published-count">-</div>
                        </div>
                        <div class="stat-card">
                            <h3>Users</h3>
                            <div class="value" id="user-count">-</div>
                        </div>
                        <div class="stat-card">
                            <h3>Media Files</h3>
                            <div class="value" id="media-count">-</div>
                        </div>
                    </div>
                </main>
            </div>
            <script>
                // Fetch dashboard stats
                fetch('/api/v1/dashboard')
                    .then(r => r.json())
                    .then(data => {
                        if (data.content && data.content.posts) {
                            document.getElementById('post-count').textContent = 
                                data.content.posts.total || 0;
                            document.getElementById('published-count').textContent = 
                                data.content.posts.published || 0;
                        }
                        if (data.users) {
                            document.getElementById('user-count').textContent = 
                                data.users.total || 0;
                        }
                        if (data.media) {
                            document.getElementById('media-count').textContent = 
                                data.media.total_files || 0;
                        }
                    })
                    .catch(e => {
                        console.error('Failed to load stats:', e);
                    });
            </script>
        </body>
        </html>
        """
        return Response.html(html)
    
    @app.route("/admin/posts", methods=["GET"])
    def admin_posts(request):
        """Posts management."""
        return _admin_layout("Posts", "<p>Post management interface</p>")
    
    @app.route("/admin/pages", methods=["GET"])
    def admin_pages(request):
        """Pages management."""
        return _admin_layout("Pages", "<p>Pages management interface</p>")
    
    @app.route("/admin/media", methods=["GET"])
    def admin_media(request):
        """Media management."""
        return _admin_layout("Media", "<p>Media library interface</p>")
    
    @app.route("/admin/users", methods=["GET"])
    def admin_users(request):
        """Users management."""
        return _admin_layout("Users", "<p>User management interface</p>")
    
    @app.route("/admin/plugins", methods=["GET"])
    def admin_plugins(request):
        """Plugins management."""
        return _admin_layout("Plugins", "<p>Plugin management interface</p>")
    
    @app.route("/admin/themes", methods=["GET"])
    def admin_themes(request):
        """Themes management."""
        return _admin_layout("Themes", "<p>Theme management interface</p>")
    
    @app.route("/admin/settings", methods=["GET"])
    def admin_settings(request):
        """Settings page."""
        return _admin_layout("Settings", "<p>System settings interface</p>")
    
    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login(request):
        """Admin login page."""
        if request.method == "POST":
            # Handle login
            return Response.redirect("/admin")
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - WebCMS</title>
            <style>
                body {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    background: #1a1a2e;
                    font-family: sans-serif;
                }
                .login-box {
                    background: white;
                    padding: 2rem;
                    border-radius: 8px;
                    width: 100%;
                    max-width: 400px;
                }
                h1 { color: #e94560; margin-bottom: 1.5rem; }
                input {
                    width: 100%;
                    padding: 0.75rem;
                    margin-bottom: 1rem;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                button {
                    width: 100%;
                    padding: 0.75rem;
                    background: #e94560;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
            </style>
        </head>
        <body>
            <div class="login-box">
                <h1>WebCMS Login</h1>
                <form method="post">
                    <input type="text" name="username" placeholder="Username" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit">Login</button>
                </form>
            </div>
        </body>
        </html>
        """
        return Response.html(html)
    
    return app


def _admin_layout(title, content):
    """Generate admin page layout."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - WebCMS Admin</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, system-ui, sans-serif;
                background: #f5f5f5;
            }}
            .admin-layout {{
                display: flex;
                min-height: 100vh;
            }}
            .sidebar {{
                width: 250px;
                background: #1a1a2e;
                color: white;
                padding: 1rem;
            }}
            .sidebar h1 {{
                font-size: 1.5rem;
                margin-bottom: 2rem;
                color: #e94560;
            }}
            .nav-menu {{
                list-style: none;
            }}
            .nav-menu li {{
                margin-bottom: 0.5rem;
            }}
            .nav-menu a {{
                color: #a0a0a0;
                text-decoration: none;
                display: block;
                padding: 0.75rem 1rem;
                border-radius: 4px;
                transition: all 0.2s;
            }}
            .nav-menu a:hover, .nav-menu a.active {{
                background: #0f3460;
                color: white;
            }}
            .main-content {{
                flex: 1;
                padding: 2rem;
            }}
            .header {{
                background: white;
                padding: 1.5rem;
                border-radius: 8px;
                margin-bottom: 2rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
        </style>
    </head>
    <body>
        <div class="admin-layout">
            <aside class="sidebar">
                <h1>🔧 WebCMS</h1>
                <nav>
                    <ul class="nav-menu">
                        <li><a href="/admin">Dashboard</a></li>
                        <li><a href="/admin/posts">Posts</a></li>
                        <li><a href="/admin/pages">Pages</a></li>
                        <li><a href="/admin/media">Media</a></li>
                        <li><a href="/admin/users">Users</a></li>
                        <li><a href="/admin/plugins">Plugins</a></li>
                        <li><a href="/admin/themes">Themes</a></li>
                        <li><a href="/admin/settings">Settings</a></li>
                    </ul>
                </nav>
            </aside>
            <main class="main-content">
                <div class="header">
                    <h2>{title}</h2>
                </div>
                {content}
            </main>
        </div>
    </body>
    </html>
    """
    return Response.html(html)
