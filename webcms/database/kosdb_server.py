"""
KosDB Server Module Wrapper

This module provides the KosDB LevelDB socket server as part of the webcms package.
The actual server implementation is imported from the separate KosDB repository.

Usage:
    python -m webcms.database.kosdb_server

Or programmatically:
    from webcms.database.kosdb_server import main
    main()
"""

import sys
import os

# Add parent KosDB directory to path if it exists
# This allows running without installing KosDB separately
_KOSDB_PATHS = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'KosDB'),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'KosDB'),
    '/opt/KosDB',
    os.path.expanduser('~/KosDB'),
]

for _path in _KOSDB_PATHS:
    if os.path.exists(_path) and _path not in sys.path:
        sys.path.insert(0, _path)
        break

# Try to import from KosDB
try:
    from server import main
    from server import SocketServer as KosDBServer
    from server import ClientHandler
except ImportError as e:
    print(f"Error: Could not import KosDB server from {os.path.dirname(__file__)}")
    print(f"Make sure KosDB is installed or available at one of these locations:")
    for p in _KOSDB_PATHS:
        print(f"  - {p}")
    print(f"\nOriginal error: {e}")
    sys.exit(1)


if __name__ == '__main__':
    main()
