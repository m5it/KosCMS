"""
KosDB Admin Tools

Admin panel extensions for KosDB management.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from webcms.core.request import Request
from webcms.core.response import Response
from webcms.database.kosdb_client import KosDBClient


class KosDBAdminAPI:
    """REST API endpoints for KosDB admin operations."""
    
    def __init__(self, kosdb_client: KosDBClient):
        self.kosdb = kosdb_client
    
    def register_routes(self, app):
        """Register API routes."""
        
        @app.route("/api/v1/kosdb/databases", methods=["GET"])
        def list_databases(request):
            """List all databases."""
            result = self.kosdb.execute("SHOW DATABASES")
            databases = [line.strip() for line in result.split('\n') if line.strip()]
            return Response.json({"databases": databases})
        
        @app.route("/api/v1/kosdb/databases", methods=["POST"])
        def create_database(request):
            """Create database."""
            data = request.json
            if not data or 'name' not in data:
                return Response.error("Database name required", 400)
            
            result = self.kosdb.execute(f"CREATE DATABASE {data['name']}")
            return Response.json({"message": result})
        
        @app.route("/api/v1/kosdb/tables", methods=["GET"])
        def list_tables(request):
            """List tables in current database."""
            result = self.kosdb.execute("SHOW TABLES")
            tables = [line.strip() for line in result.split('\n') if line.strip()]
            return Response.json({"tables": tables})
        
        @app.route("/api/v1/kosdb/query", methods=["POST"])
        def execute_query(request):
            """Execute SQL query."""
            data = request.json
            if not data or 'query' not in data:
                return Response.error("Query required", 400)
            
            query = data['query']
            
            # Security: Only allow SELECT for now
            if not query.strip().upper().startswith('SELECT'):
                return Response.error("Only SELECT queries allowed", 403)
            
            result = self.kosdb.query(query)
            return Response.json(result)
        
        @app.route("/api/v1/kosdb/replication/status", methods=["GET"])
        def replication_status(request):
            """Get replication status."""
            result = self.kosdb.execute("SHOW MASTER STATUS")
            return Response.json({"status": result})
        
        @app.route("/api/v1/kosdb/users", methods=["GET"])
        def list_users(request):
            """List KosDB users."""
            result = self.kosdb.execute("SHOW USERS")
            users = [line.strip() for line in result.split('\n') if line.strip()]
            return Response.json({"users": users})
        
        return app


class KosDBAdminPages:
    """Admin page handlers for KosDB."""
    
    def __init__(self, kosdb_client: KosDBClient):
        self.kosdb = kosdb_client
    
    def register_routes(self, app):
        """Register admin page routes."""
        
        @app.route("/admin/kosdb", methods=["GET"])
        def kosdb_dashboard(request):
            """KosDB admin dashboard."""
            html = self._render_dashboard()
            return Response.html(html)
        
        @app.route("/admin/kosdb/query", methods=["GET"])
        def kosdb_query_page(request):
            """Query executor page."""
            html = self._render_query_page()
            return Response.html(html)
        
        @app.route("/admin/kosdb/browser", methods=["GET"])
        def kosdb_browser(request):
            """Database browser page."""
            html = self._render_browser()
            return Response.html(html)
        
        @app.route("/admin/kosdb/replication", methods=["GET"])
        def kosdb_replication(request):
            """Replication management page."""
            html = self._render_replication_page()
            return Response.html(html)
        
        return app
    
    def _render_dashboard(self) -> str:
        """Render KosDB dashboard HTML."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>KosDB Admin - WebCMS</title>
            <style>
                body { font-family: sans-serif; margin: 0; background: #f5f5f5; }
                .header { background: #1a1a2e; color: white; padding: 1rem; }
                .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
                .card { background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; }
                h1 { margin: 0; color: #e94560; }
                .nav { display: flex; gap: 1rem; margin: 1rem 0; }
                .nav a { color: #007bff; text-decoration: none; }
                .nav a:hover { text-decoration: underline; }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #ddd; }
                th { background: #f8f9fa; }
                .btn { background: #007bff; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; }
                .btn:hover { background: #0056b3; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔌 KosDB Administration</h1>
            </div>
            <div class="container">
                <div class="nav">
                    <a href="/admin/kosdb">Dashboard</a>
                    <a href="/admin/kosdb/browser">Database Browser</a>
                    <a href="/admin/kosdb/query">Query Executor</a>
                    <a href="/admin/kosdb/replication">Replication</a>
                </div>
                
                <div class="grid">
                    <div class="card">
                        <h3>Database Status</h3>
                        <p id="db-status">Loading...</p>
                    </div>
                    <div class="card">
                        <h3>Tables</h3>
                        <p id="table-count">Loading...</p>
                    </div>
                    <div class="card">
                        <h3>Replication</h3>
                        <p id="repl-status">Loading...</p>
                    </div>
                </div>
                
                <div class="card">
                    <h3>Quick Actions</h3>
                    <button class="btn" onclick="createDatabase()">Create Database</button>
                    <button class="btn" onclick="backupDatabase()">Backup</button>
                    <button class="btn" onclick="optimizeDatabase()">Optimize</button>
                </div>
            </div>
            
            <script>
                // Load status
                fetch('/api/v1/kosdb/databases')
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('db-status').textContent = 
                            data.databases.length + ' databases';
                    });
                
                fetch('/api/v1/kosdb/tables')
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('table-count').textContent = 
                            data.tables.length + ' tables';
                    });
                
                fetch('/api/v1/kosdb/replication/status')
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('repl-status').textContent = 
                            data.status.includes('ERROR') ? 'Not configured' : 'Active';
                    });
                
                function createDatabase() {
                    const name = prompt('Database name:');
                    if (name) {
                        fetch('/api/v1/kosdb/databases', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({name})
                        }).then(() => location.reload());
                    }
                }
                
                function backupDatabase() {
                    alert('Backup functionality would be implemented here');
                }
                
                function optimizeDatabase() {
                    alert('Optimize functionality would be implemented here');
                }
            </script>
        </body>
        </html>
        """
    
    def _render_query_page(self) -> str:
        """Render query executor page."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>KosDB Query - WebCMS</title>
            <style>
                body { font-family: sans-serif; margin: 0; background: #f5f5f5; }
                .header { background: #1a1a2e; color: white; padding: 1rem; }
                .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
                .card { background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem; }
                textarea { width: 100%; height: 150px; font-family: monospace; padding: 1rem; }
                .btn { background: #007bff; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 4px; cursor: pointer; margin-top: 1rem; }
                .results { margin-top: 1rem; overflow-x: auto; }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 0.5rem; border: 1px solid #ddd; }
                th { background: #f8f9fa; }
                .error { color: #dc3545; padding: 1rem; background: #f8d7da; border-radius: 4px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔍 KosDB Query Executor</h1>
            </div>
            <div class="container">
                <div class="card">
                    <h3>SQL Query</h3>
                    <textarea id="query" placeholder="SELECT * FROM users WHERE id = 1"></textarea>
                    <button class="btn" onclick="executeQuery()">Execute</button>
                </div>
                
                <div class="card results" id="results" style="display: none;">
                    <h3>Results</h3>
                    <div id="results-content"></div>
                </div>
            </div>
            
            <script>
                function executeQuery() {
                    const query = document.getElementById('query').value;
                    
                    fetch('/api/v1/kosdb/query', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({query})
                    })
                    .then(r => r.json())
                    .then(data => {
                        const resultsDiv = document.getElementById('results');
                        const contentDiv = document.getElementById('results-content');
                        
                        resultsDiv.style.display = 'block';
                        
                        if (data.error) {
                            contentDiv.innerHTML = '<div class="error">' + data.error + '</div>';
                            return;
                        }
                        
                        if (data.columns && data.columns.length > 0) {
                            let html = '<table><thead><tr>';
                            data.columns.forEach(col => {
                                html += '<th>' + col + '</th>';
                            });
                            html += '</tr></thead><tbody>';
                            
                            data.rows.forEach(row => {
                                html += '<tr>';
                                row.forEach(cell => {
                                    html += '<td>' + (cell || '') + '</td>';
                                });
                                html += '</tr>';
                            });
                            
                            html += '</tbody></table>';
                            html += '<p>' + data.count + ' row(s)</p>';
                            contentDiv.innerHTML = html;
                        } else {
                            contentDiv.innerHTML = '<p>No results</p>';
                        }
                    });
                }
            </script>
        </body>
        </html>
        """
    
    def _render_browser(self) -> str:
        """Render database browser."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>KosDB Browser - WebCMS</title>
            <style>
                body { font-family: sans-serif; margin: 0; background: #f5f5f5; }
                .header { background: #1a1a2e; color: white; padding: 1rem; }
                .container { max-width: 1400px; margin: 0 auto; padding: 2rem; display: flex; gap: 1rem; }
                .sidebar { width: 250px; background: white; border-radius: 8px; padding: 1rem; }
                .content { flex: 1; background: white; border-radius: 8px; padding: 1rem; }
                .tree-item { padding: 0.5rem; cursor: pointer; }
                .tree-item:hover { background: #f8f9fa; }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 0.75rem; border-bottom: 1px solid #ddd; }
                th { background: #f8f9fa; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🗄️ KosDB Database Browser</h1>
            </div>
            <div class="container">
                <div class="sidebar">
                    <h3>Databases</h3>
                    <div id="db-tree">Loading...</div>
                </div>
                <div class="content">
                    <h3>Table Data</h3>
                    <div id="table-data">Select a table to view data</div>
                </div>
            </div>
            
            <script>
                // Load databases
                fetch('/api/v1/kosdb/databases')
                    .then(r => r.json())
                    .then(data => {
                        const tree = document.getElementById('db-tree');
                        tree.innerHTML = '';
                        
                        data.databases.forEach(db => {
                            const div = document.createElement('div');
                            div.className = 'tree-item';
                            div.textContent = '📁 ' + db;
                            div.onclick = () => loadTables(db);
                            tree.appendChild(div);
                        });
                    });
                
                function loadTables(db) {
                    // Would load tables for selected database
                    document.getElementById('table-data').innerHTML = 
                        '<p>Tables for ' + db + '</p>';
                }
            </script>
        </body>
        </html>
        """
    
    def _render_replication_page(self) -> str:
        """Render replication management page."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>KosDB Replication - WebCMS</title>
            <style>
                body { font-family: sans-serif; margin: 0; background: #f5f5f5; }
                .header { background: #1a1a2e; color: white; padding: 1rem; }
                .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
                .card { background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem; }
                .status-active { color: #28a745; }
                .status-error { color: #dc3545; }
                .btn { background: #007bff; color: white; padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; }
                pre { background: #f8f9fa; padding: 1rem; border-radius: 4px; overflow-x: auto; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔄 KosDB Replication</h1>
            </div>
            <div class="container">
                <div class="card">
                    <h3>Replication Status</h3>
                    <div id="status">Loading...</div>
                </div>
                
                <div class="card">
                    <h3>Master Status</h3>
                    <pre id="master-status">Loading...</pre>
                </div>
                
                <div class="card">
                    <h3>Actions</h3>
                    <button class="btn" onclick="startReplication()">Start Replication</button>
                    <button class="btn" onclick="stopReplication()">Stop Replication</button>
                    <button class="btn" onclick="forceSync()">Force Sync</button>
                </div>
            </div>
            
            <script>
                function loadStatus() {
                    fetch('/api/v1/kosdb/replication/status')
                        .then(r => r.json())
                        .then(data => {
                            document.getElementById('status').innerHTML = 
                                '<p class="status-active">● Active</p>' +
                                '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                            document.getElementById('master-status').textContent = data.status;
                        });
                }
                
                loadStatus();
                setInterval(loadStatus, 5000);
                
                function startReplication() { alert('Start replication'); }
                function stopReplication() { alert('Stop replication'); }
                function forceSync() { alert('Force sync'); }
            </script>
        </body>
        </html>
        """


def register_kosdb_admin(app, kosdb_client: KosDBClient):
    """Register all KosDB admin components."""
    api = KosDBAdminAPI(kosdb_client)
    pages = KosDBAdminPages(kosdb_client)
    
    api.register_routes(app)
    pages.register_routes(app)
    
    return app