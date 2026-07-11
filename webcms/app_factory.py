"""
Application Factory

Create and configure WebCMS application instance with KosDB support.
"""

from webcms import Application
from webcms.database import init_db, KosDBClient, KosDBConfig
from webcms.database.kosdb_replication import KosDBReplicationManager, ReplicationConfig, ReplicationRole
from webcms.security import SecurityMiddleware, HTTPSRedirectMiddleware
from webcms.security.middleware import CSPConfig
from webcms.admin.api import create_api
from webcms.admin.routes import admin_routes
from webcms.admin.kosdb_admin import register_kosdb_admin


def create_app(config_path: str = None) -> Application:
    """
    Create configured WebCMS application.
    
    Args:
        config_path: Path to configuration file
    
    Returns:
        Configured Application instance
    """
    # Create application
    app = Application(config_path)
    
    # Initialize database based on type
    db_config = app.config.get("database", {})
    db_url = db_config.get("url", "sqlite:///webcms.db")
    
    if db_url.startswith("kosdb://"):
        # Use KosDB
        kosdb_config = db_config.get("kosdb", {})
        config = KosDBConfig(
            host=kosdb_config.get("host", "localhost"),
            port=kosdb_config.get("port", 5555),
            username=kosdb_config.get("username", "admin"),
            password=kosdb_config.get("password", "admin"),
            database=kosdb_config.get("database", "webcms"),
            pool_size=kosdb_config.get("pool_size", 10)
        )
        
        # Create KosDB client
        kosdb = KosDBClient(config)
        app.container.register("kosdb", kosdb)
        
        # Setup replication if enabled
        repl_config = kosdb_config.get("replication", {})
        if repl_config.get("enabled", False):
            role_map = {
                "standalone": ReplicationRole.STANDALONE,
                "master": ReplicationRole.MASTER,
                "slave": ReplicationRole.SLAVE,
                "master_master": ReplicationRole.MASTER_MASTER
            }
            
            repl = KosDBReplicationManager(
                kosdb,
                ReplicationConfig(
                    server_id=repl_config.get("server_id", 1),
                    role=role_map.get(repl_config.get("role", "standalone")),
                    master_host=repl_config.get("master_host"),
                    master_port=repl_config.get("master_port"),
                    peer_host=repl_config.get("peer_host"),
                    peer_port=repl_config.get("peer_port")
                )
            )
            repl.start()
            app.container.register("replication", repl)
        
        # Register KosDB admin
        register_kosdb_admin(app, kosdb)
        
    else:
        # Use standard SQLAlchemy
        db = init_db(
            db_url,
            pool_size=db_config.get("pool_size", 10),
            max_overflow=db_config.get("max_overflow", 20),
            echo=db_config.get("echo", False)
        )
        app.container.register("db", db)
    
    # Add security middleware
    security_config = app.config.get("security", {})
    
    # HTTPS redirect
    if app.config.get("server", {}).get("ssl_cert"):
        app.use(HTTPSRedirectMiddleware(enabled=True))
    
    # Security headers
    csp_dict = security_config.get("csp")
    if csp_dict is None or csp_dict == {}:
        csp_config = CSPConfig()
    elif isinstance(csp_dict, dict):
        # Filter only valid CSPConfig fields
        valid_fields = {'default_src', 'script_src', 'style_src', 'img_src', 
                       'font_src', 'connect_src', 'media_src', 'object_src',
                       'frame_src', 'frame_ancestors', 'form_action', 'base_uri',
                       'report_uri', 'report_only', 'upgrade_insecure'}
        filtered = {k: v for k, v in csp_dict.items() if k in valid_fields}
        csp_config = CSPConfig(**filtered)
    else:
        csp_config = csp_dict
    
    app.use(SecurityMiddleware(
        csp_config=csp_config,
        hsts_enabled=security_config.get("hsts", True)
    ))
    
    # Register admin routes
    admin_routes(app)
    
    # Register API
    if "db" in app.container._services:
        create_api(app, app.container.get("db"), None)
    
    # Public routes
    @app.route("/", methods=["GET"])
    def home(request):
        """Homepage."""
        kosdb_connected = "kosdb" in app.container._services
        cls = "connected" if kosdb_connected else "disconnected"
        status = "Connected" if kosdb_connected else "Disconnected"
        
        # Build HTML with string concatenation to avoid format issues
        html = (
            '<!DOCTYPE html>\n'
            '<html lang="en">\n'
            '<head>\n'
            '    <meta charset="UTF-8">\n'
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            '    <title>Hello World - WebCMS</title>\n'
            '    <style>\n'
            '        * { margin: 0; padding: 0; box-sizing: border-box; }\n'
            '        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; \n'
            '               display: flex; justify-content: center; align-items: center; min-height: 100vh;\n'
            '               background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #333; }\n'
            '        .card { background: white; border-radius: 16px; padding: 48px; text-align: center;\n'
            '                box-shadow: 0 20px 60px rgba(0,0,0,0.3); max-width: 500px; width: 90%; }\n'
            '        h1 { font-size: 2.5em; margin-bottom: 12px; color: #667eea; }\n'
            '        p { font-size: 1.1em; color: #666; margin-bottom: 24px; }\n'
            '        .status { display: inline-block; padding: 8px 20px; border-radius: 24px; font-size: 0.9em; font-weight: 600; }\n'
            '        .connected { background: #d4edda; color: #155724; }\n'
            '        .disconnected { background: #f8d7da; color: #721c24; }\n'
            '        .links { margin-top: 24px; }\n'
            '        .links a { color: #667eea; text-decoration: none; margin: 0 12px; font-weight: 500; }\n'
            '        .links a:hover { text-decoration: underline; }\n'
            '    </style>\n'
            '</head>\n'
            '<body>\n'
            '    <div class="card">\n'
            '        <h1>Hello World!</h1>\n'
            '        <p>Welcome to <strong>WebCMS</strong> - A Modern Python Content Management System</p>\n'
            f'        <span class="status {cls}">KosDB: {status}</span>\n'
            '        <div class="links">\n'
            '            <a href="/health">Health Check</a>\n'
            '            <a href="/api/v1/status">API Status</a>\n'
            '        </div>\n'
            '    </div>\n'
            '</body>\n'
            '</html>'
        )
        return html
    
    @app.route("/health", methods=["GET"])
    def health(request):
        """Health check endpoint."""
        status = {
            "status": "healthy",
            "version": "1.1.0",
            "database": "kosdb" if "kosdb" in app.container._services else "sql"
        }
        
        if "kosdb" in app.container._services:
            kosdb = app.container.get("kosdb")
            try:
                result = kosdb.execute("SHOW DATABASES")
                status["kosdb_connected"] = not result.startswith("ERROR")
            except:
                status["kosdb_connected"] = False
        
        return status
    
    @app.route("/api/v1/status", methods=["GET"])
    def status(request):
        """Detailed status endpoint."""
        return {
            "webcms": "1.1.0",
            "database_type": "kosdb" if "kosdb" in app.container._services else "sql",
            "features": {
                "kosdb": "kosdb" in app.container._services,
                "replication": "replication" in app.container._services
            }
        }
    
    return app
