"""
WebCMS Dependency Injection Container

Simple DI container for managing dependencies.
"""

from typing import Dict, Any, Callable, Optional


class Container:
    """Dependency injection container."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, bool] = {}
    
    def register(self, name: str, service: Any, singleton: bool = True) -> None:
        """
        Register a service.
        
        Args:
            name: Service identifier
            service: Service instance or factory
            singleton: Whether to reuse instance
        """
        if callable(service) and not isinstance(service, type):
            self._factories[name] = service
            self._singletons[name] = singleton
        else:
            self._services[name] = service
            self._singletons[name] = singleton
    
    def get(self, name: str) -> Any:
        """
        Get service by name.
        
        Args:
            name: Service identifier
        
        Returns:
            Service instance
        
        Raises:
            KeyError: If service not found
        """
        if name in self._services:
            return self._services[name]
        
        if name in self._factories:
            instance = self._factories[name]()
            if self._singletons.get(name, True):
                self._services[name] = instance
            return instance
        
        raise KeyError(f"Service '{name}' not found")
    
    def has(self, name: str) -> bool:
        """Check if service exists."""
        return name in self._services or name in self._factories
    
    def remove(self, name: str) -> None:
        """Remove service from container."""
        self._services.pop(name, None)
        self._factories.pop(name, None)
        self._singletons.pop(name, None)
    
    def clear(self) -> None:
        """Clear all services."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()