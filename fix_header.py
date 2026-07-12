from pathlib import Path

p = Path("webcms/app_factory.py")
text = p.read_text()

# Define the correct header block (first 16 lines)
correct_header = '''"""
Application Factory

Create and configure WebCMS application instance with KosDB support.
"""

from webcms import Application, __version__
from webcms.database import init_db, KosDBClient, KosDBConfig
from webcms.database.kosdb_replication import KosDBReplicationManager, ReplicationConfig, ReplicationRole
from webcms.security import SecurityMiddleware, HTTPSRedirectMiddleware
from webcms.security.middleware import CSPConfig
from webcms.core.response import Response
from webcms.admin.api import create_api
from webcms.admin.routes import admin_routes
from webcms.admin.kosdb_admin import register_kosdb_admin

'''

# Find the start of the real import block
marker = "from webcms import Application"
idx = text.find(marker)
if idx == -1:
    print("Marker not found")
    raise SystemExit(1)

# Find the blank line before def create_app
def_idx = text.find("\ndef create_app")
if def_idx == -1:
    print("def create_app not found")
    raise SystemExit(1)

new_text = correct_header + text[def_idx + 1 :]
p.write_text(new_text)
print("Header fixed")
