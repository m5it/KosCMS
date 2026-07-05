#!/usr/bin/env python3
"""
WebCMS Entry Point

Run the WebCMS application server.
"""

import sys
import argparse
from pathlib import Path

# Add webcms to path
sys.path.insert(0, str(Path(__file__).parent))

from webcms.app_factory import create_app


def main():
    parser = argparse.ArgumentParser(description="WebCMS Server")
    parser.add_argument("--config", "-c", help="Path to config file")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", "-p", type=int, default=8000, help="Bind port")
    parser.add_argument("--debug", "-d", action="store_true", help="Debug mode")
    parser.add_argument("--ssl-cert", help="SSL certificate file")
    parser.add_argument("--ssl-key", help="SSL private key file")
    
    args = parser.parse_args()
    
    # Create application
    app = create_app(args.config)
    
    # Run server
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug,
        ssl_context=(args.ssl_cert, args.ssl_key) if args.ssl_cert else None
    )


if __name__ == "__main__":
    main()