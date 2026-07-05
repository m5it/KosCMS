"""
WebCMS Router

URL routing with pattern matching and parameter extraction.
"""

import re
from typing import Dict, List, Callable, Optional, Tuple, Any


class Router:
    """URL Router with pattern matching."""
    
    def __init__(self):
        self.routes: List[Dict[str, Any]] = []
        self.static_routes: Dict[str, Dict[str, Any]] = {}
    
    def add(self, path: str, handler: Callable, methods: List[str]) -> None:
        """
        Add a route.
        
        Args:
            path: URL pattern (e.g., '/users/{id}')
            handler: Function to handle request
            methods: HTTP methods allowed
        """
        route = {
            "path": path,
            "handler": handler,
            "methods": [m.upper() for m in methods],
            "pattern": self._compile_pattern(path)
        }
        
        # Static routes optimization
        if "{" not in path:
            if path not in self.static_routes:
                self.static_routes[path] = {}
            for method in route["methods"]:
                self.static_routes[path][method] = handler
        else:
            self.routes.append(route)
    
    def _compile_pattern(self, path: str) -> re.Pattern:
        """Compile path pattern to regex."""
        # Convert {param} to regex groups
        pattern = re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", path)
        return re.compile(f"^{pattern}$")
    
    def match(self, path: str, method: str) -> Tuple[Optional[Callable], Dict[str, str]]:
        """
        Match URL path to handler.
        
        Returns:
            Tuple of (handler, params) or (None, {})
        """
        method = method.upper()
        
        # Check static routes first
        if path in self.static_routes:
            if method in self.static_routes[path]:
                return self.static_routes[path][method], {}
            elif "GET" in self.static_routes[path] and method == "HEAD":
                return self.static_routes[path]["GET"], {}
        
        # Check dynamic routes
        for route in self.routes:
            match = route["pattern"].match(path)
            if match:
                if method in route["methods"]:
                    return route["handler"], match.groupdict()
                elif "GET" in route["methods"] and method == "HEAD":
                    return route["handler"], match.groupdict()
        
        return None, {}
    
    def url_for(self, handler: Callable, **kwargs) -> Optional[str]:
        """Generate URL for handler."""
        for route in self.routes:
            if route["handler"] is handler:
                path = route["path"]
                for key, value in kwargs.items():
                    path = path.replace(f"{{{key}}}", str(value))
                return path
        
        # Check static routes
        for path, methods in self.static_routes.items():
            if handler in methods.values():
                return path
        
        return None
    
    def get_routes(self) -> List[Dict[str, Any]]:
        """Get all registered routes."""
        all_routes = []
        for path, methods in self.static_routes.items():
            for method, handler in methods.items():
                all_routes.append({
                    "path": path,
                    "method": method,
                    "handler": handler.__name__
                })
        for route in self.routes:
            for method in route["methods"]:
                all_routes.append({
                    "path": route["path"],
                    "method": method,
                    "handler": route["handler"].__name__
                })
        return all_routes