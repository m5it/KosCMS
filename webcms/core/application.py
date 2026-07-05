"""
WebCMS Application Core

Main application class handling WSGI/ASGI requests, routing,
and plugin lifecycle management.
"""

import os
import sys
import yaml
import logging
from typing import Dict, List, Callable, Optional, Any
from pathlib import Path

from .request import Request
from .response import Response
from .router import Router
from .middleware import MiddlewareStack
from .container import Container


class Application:
    """Main WebCMS application class."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.root_path = Path(__file__).parent.parent.absolute()
        self.config = self._load_config(config_path)
        self.container = Container()
        self.router = Router()
        self.middleware = MiddlewareStack()
        self.plugins: Dict[str, Any] = {}
        self.hooks: Dict[str, List[Callable]] = {}
        
        self._setup_logging()
        self._init_container()
        
        logging.info(f"WebCMS {self._get_version()} initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from YAML file."""
        if config_path is None:
            config_path = self.root_path / "config" / "config.yaml"
        
        default_config = {
            "app": {
                "name": "WebCMS",
                "debug": False,
                "secret_key": "change-me-in-production",
                "timezone": "UTC"
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "workers": 4
            },
            "database": {
                "url": "sqlite:///webcms.db",
                "pool_size": 10
            }
        }
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                self._deep_update(default_config, user_config)
        
        return default_config
    
    def _deep_update(self, base: Dict, update: Dict) -> None:
        """Recursively update nested dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def _setup_logging(self) -> None:
        """Configure logging."""
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(
            level=logging.DEBUG if self.config["app"]["debug"] else logging.INFO,
            format=log_format
        )
        self.logger = logging.getLogger("webcms")
    
    def _init_container(self) -> None:
        """Initialize dependency injection container."""
        self.container.register("app", self)
        self.container.register("config", self.config)
        self.container.register("router", self.router)
        self.container.register("hooks", self.hooks)
    
    def route(self, path: str, methods: Optional[List[str]] = None):
        """Decorator to register a route."""
        def decorator(func: Callable) -> Callable:
            self.router.add(path, func, methods or ["GET"])
            return func
        return decorator
    
    def wsgi_app(self, environ: Dict, start_response: Callable) -> List[bytes]:
        """WSGI application entry point."""
        request = Request.from_wsgi(environ)
        response = self.middleware.process(request, self._handle_request)
        return response.to_wsgi(start_response)
    
    def _handle_request(self, request: Request) -> Response:
        """Handle request and return response."""
        try:
            handler, params = self.router.match(request.path, request.method)
            
            if handler is None:
                return Response.not_found()
            
            response = handler(request, **params)
            
            if not isinstance(response, Response):
                response = Response(response)
            
            return response
            
        except Exception as e:
            self.logger.exception("Request handling error")
            return Response.error("Internal Server Error", 500)
    
    def run(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        """Run development server."""
        from wsgiref.simple_server import make_server
        
        host = host or self.config["server"]["host"]
        port = port or self.config["server"]["port"]
        
        server = make_server(host, port, self.wsgi_app)
        self.logger.info(f"Server running on http://{host}:{port}")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
    
    def _get_version(self) -> str:
        """Get WebCMS version."""
        from .. import __version__
        return __version__
    
    def __call__(self, environ: Dict, start_response: Callable) -> List[bytes]:
        """Make application callable for WSGI."""
        return self.wsgi_app(environ, start_response)