from pathlib import Path

path = Path("webcms/app_factory.py")
text = path.read_text()

# Define the correct import block
import_block = '''"""\nApplication Factory\n\nCreate and configure WebCMS application instance with KosDB support.\n"""\n\nfrom webcms import Application, __version__\nfrom webcms.database import init_db, KosDBClient, KosDBConfig\nfrom webcms.database.kosdb_replication import KosDBReplicationManager, ReplicationConfig, ReplicationRole\nfrom webcms.security import SecurityMiddleware, HTTPSRedirectMiddleware\nfrom webcms.security.middleware import CSPConfig\nfrom webcms.core.response import Response\nfrom webcms.admin.api import create_api\nfrom webcms.admin.routes import admin_routes\nfrom webcms.admin.kosdb_admin import register_kosdb_admin\n'''

# Replace everything from the docstring end to the first def create_app
start_marker = '"""\n\nfrom webcms import'
end_marker = '\ndef create_app('
start = text.find(start_marker)
end = text.find(end_marker)

if start == -1 or end == -1:
    print("Could not find markers")
    print("start", start, "end", end)
    raise SystemExit(1)

new_text = text[:start] + '"""\n\n' + import_block.split('\n\n', 1)[1] + '\n' + text[end:]
path.write_text(new_text)
print("Imports fixed")
