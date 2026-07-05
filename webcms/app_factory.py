"""
Application Factory

Create and configure WebCMS application instance with KosDB support.
"""

from webcms import Application
from webcms.database import init_db, KosDBClient, KosDBConfig
from webcms.database.kosdb_replication import KosDBReplicationManager, ReplicationConfig, ReplicationRole
from webcms.security import SecurityMiddleware, HTTPSRedirectMiddleware
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
            port=kosdb_config.get("port", 9999),
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
    app.use(SecurityMiddleware(
        content_security_policy=security_config.get("csp"),
        strict_transport_security=security_config.get("hsts", True)
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
        if "kosdb" in app.container._services:
            kosdb = app.container.get("kosdb")
            result = kosdb.query("SELECT * FROM pages WHERE is_homepage = 1 LIMIT 1")
            if result.get("rows"):
                return "<h1>Welcome to WebCMS with KosDB!</h1>"
        
        return "<h1>Welcome to WebCMS</h1><p>Your homepage is not set up yet.</p>"
    
    @app.route("/health", methods=["GET"])
    def health(request):
        """Health check endpoint."""
        status = {
            "status": "healthy",
            "version": "1.0.0",
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
            "webcms": "1.0.0",
            "database_type": "kosdb" if "kosdb" in app.container._services else "sql",
            "features": {
                "kosdb": "kosdb" in app.container._services,
                "replication": "replication" in app.container._services
            }
        }
    
    return app