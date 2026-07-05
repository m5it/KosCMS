"""
Hook System

Event-driven hook architecture for plugins.
"""

from enum import Enum, auto
from typing import Dict, List, Callable, Any


class HookType(Enum):
    """Built-in hook types."""
    PRE_INIT = "pre_init"
    POST_INIT = "post_init"
    
    PRE_REQUEST = "pre_request"
    POST_REQUEST = "post_request"
    
    PRE_SAVE = "pre_save"
    POST_SAVE = "post_save"
    
    PRE_DELETE = "pre_delete"
    POST_DELETE = "post_delete"
    
    PRE_RENDER = "pre_render"
    POST_RENDER = "post_render"
    
    TEMPLATE_RENDER = "template_render"
    
    CONTENT_FILTER = "content_filter"
    
    ADMIN_MENU = "admin_menu"
    ADMIN_WIDGETS = "admin_widgets"
    
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTER = "user_register"


class HookManager:
    """Central hook management system."""
    
    def __init__(self):
        self._hooks: Dict[str, List[Callable]] = {}
        self._filters: Dict[str, List[Callable]] = {}
    
    def register(self, event: str, callback: Callable, priority: int = 10) -> None:
        """
        Register hook callback.
        
        Args:
            event: Hook name
            callback: Function to call
            priority: Lower = earlier execution
        """
        if event not in self._hooks:
            self._hooks[event] = []
        
        # Insert by priority
        self._hooks[event].append((priority, callback))
        self._hooks[event].sort(key=lambda x: x[0])
    
    def unregister(self, event: str, callback: Callable) -> bool:
        """Unregister hook callback."""
        if event not in self._hooks:
            return False
        
        self._hooks[event] = [
            (p, cb) for p, cb in self._hooks[event] 
            if cb != callback
        ]
        return True
    
    def trigger(self, event: str, *args, **kwargs) -> List[Any]:
        """
        Trigger hook callbacks.
        
        Returns:
            List of results from each callback
        """
        results = []
        
        for priority, callback in self._hooks.get(event, []):
            try:
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                # Log error but continue
                print(f"Hook error in {event}: {e}")
        
        return results
    
    def filter(self, tag: str, value: Any, *args, **kwargs) -> Any:
        """
        Apply filter hooks to value.
        
        Filters modify a value through a chain of functions.
        
        Args:
            tag: Filter name
            value: Initial value
            *args, **kwargs: Additional arguments
        
        Returns:
            Filtered value
        """
        for priority, callback in self._filters.get(tag, []):
            try:
                value = callback(value, *args, **kwargs)
            except Exception as e:
                print(f"Filter error in {tag}: {e}")
        
        return value
    
    def register_filter(self, tag: str, callback: Callable, priority: int = 10) -> None:
        """Register filter callback."""
        if tag not in self._filters:
            self._filters[tag] = []
        
        self._filters[tag].append((priority, callback))
        self._filters[tag].sort(key=lambda x: x[0])
    
    def has_hooks(self, event: str) -> bool:
        """Check if event has registered hooks."""
        return event in self._hooks and len(self._hooks[event]) > 0
    
    def get_registered_events(self) -> List[str]:
        """Get list of registered events."""
        return list(self._hooks.keys())