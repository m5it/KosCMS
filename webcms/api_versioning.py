"""
API Versioning Support

Provides API versioning for backward compatibility
"""

import re
from typing import Dict, List, Optional, Callable, Any
from functools import wraps
from dataclasses import dataclass


@dataclass
class APIVersion:
    """API version definition."""
    major: int
    minor: int
    patch: int
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def __lt__(self, other: 'APIVersion') -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
    
    def __le__(self, other: 'APIVersion') -> bool:
        return (self.major, self.minor, self.patch) <= (other.major, other.minor, other.patch)
    
    def __gt__(self, other: 'APIVersion') -> bool:
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)
    
    def __ge__(self, other: 'APIVersion') -> bool:
        return (self.major, self.minor, self.patch) >= (other.major, other.minor, other.patch)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, APIVersion):
            return False
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)


class VersionedAPI:
    """Versioned API endpoint."""
    
    def __init__(self, path: str, version: APIVersion, handler: Callable):
        self.path = path
        self.version = version
        self.handler = handler
        self.deprecated = False
        self.removed_in: Optional[APIVersion] = None
    
    def deprecate(self, removed_in: Optional[APIVersion] = None):
        """Mark endpoint as deprecated."""
        self.deprecated = True
        self.removed_in = removed_in


class APIVersionManager:
    """Manages API versions."""
    
    CURRENT_VERSION = APIVersion(1, 0, 0)
    MIN_SUPPORTED_VERSION = APIVersion(1, 0, 0)
    
    def __init__(self):
        self._endpoints: Dict[str, Dict[str, VersionedAPI]] = {}
        self._version_changes: Dict[str, List[Dict]] = {}
    
    def register(self, path: str, version: str, handler: Callable) -> VersionedAPI:
        """
        Register an API endpoint.
        
        Args:
            path: API path (e.g., '/users')
            version: Version string (e.g., '1.0.0')
            handler: Endpoint handler function
        
        Returns:
            VersionedAPI instance
        """
        api_version = self._parse_version(version)
        
        if path not in self._endpoints:
            self._endpoints[path] = {}
        
        versioned = VersionedAPI(path, api_version, handler)
        self._endpoints[path][version] = versioned
        
        return versioned
    
    def _parse_version(self, version: str) -> APIVersion:
        """Parse version string."""
        match = re.match(r'(\d+)\.(\d+)\.(\d+)', version)
        if match:
            return APIVersion(
                int(match.group(1)),
                int(match.group(2)),
                int(match.group(3))
            )
        return APIVersion(1, 0, 0)
    
    def get_handler(self, path: str, version: Optional[str] = None) -> Optional[Callable]:
        """
        Get handler for path and version.
        
        Args:
            path: API path
            version: Requested version (None = current)
        
        Returns:
            Handler function or None
        """
        if path not in self._endpoints:
            return None
        
        if version is None:
            # Use latest version
            versions = sorted(
                self._endpoints[path].values(),
                key=lambda v: v.version,
                reverse=True
            )
            return versions[0].handler if versions else None
        
        # Exact version match
        if version in self._endpoints[path]:
            return self._endpoints[path][version].handler
        
        # Find compatible version
        requested = self._parse_version(version)
        
        compatible = [
            v for v in self._endpoints[path].values()
            if v.version.major == requested.major and v.version <= requested
        ]
        
        if compatible:
            return max(compatible, key=lambda v: v.version).handler
        
        return None
    
    def get_version_info(self, path: str, version: str) -> Optional[Dict]:
        """Get version information for endpoint."""
        if path not in self._endpoints or version not in self._endpoints[path]:
            return None
        
        endpoint = self._endpoints[path][version]
        
        return {
            'path': endpoint.path,
            'version': str(endpoint.version),
            'deprecated': endpoint.deprecated,
            'removed_in': str(endpoint.removed_in) if endpoint.removed_in else None
        }
    
    def list_versions(self, path: Optional[str] = None) -> List[str]:
        """List available versions."""
        if path:
            if path not in self._endpoints:
                return []
            return list(self._endpoints[path].keys())
        
        # All unique versions
        versions = set()
        for endpoints in self._endpoints.values():
            versions.update(endpoints.keys())
        
        return sorted(versions, key=lambda v: self._parse_version(v))
    
    def deprecate_endpoint(self, path: str, version: str, removed_in: Optional[str] = None):
        """Mark endpoint as deprecated."""
        if path in self._endpoints and version in self._endpoints[path]:
            removed_version = self._parse_version(removed_in) if removed_in else None
            self._endpoints[path][version].deprecate(removed_version)
    
    def add_changelog(self, version: str, changes: List[Dict]):
        """
        Add changelog entry.
        
        Args:
            version: Version string
            changes: List of change dictionaries
        """
        self._version_changes[version] = changes
    
    def get_changelog(self, from_version: Optional[str] = None, 
                      to_version: Optional[str] = None) -> List[Dict]:
        """
        Get changelog between versions.
        
        Args:
            from_version: Start version (inclusive)
            to_version: End version (inclusive)
        
        Returns:
            List of changelog entries
        """
        entries = []
        
        for version, changes in self._version_changes.items():
            version_obj = self._parse_version(version)
            
            if from_version:
                from_obj = self._parse_version(from_version)
                if version_obj < from_obj:
                    continue
            
            if to_version:
                to_obj = self._parse_version(to_version)
                if version_obj > to_obj:
                    continue
            
            entries.append({
                'version': version,
                'changes': changes
            })
        
        return sorted(entries, key=lambda e: self._parse_version(e['version']))
    
    def check_compatibility(self, version: str) -> Dict:
        """
        Check if version is compatible.
        
        Args:
            version: Version string to check
        
        Returns:
            Compatibility information
        """
        requested = self._parse_version(version)
        
        return {
            'version': str(requested),
            'supported': requested >= self.MIN_SUPPORTED_VERSION,
            'current': str(self.CURRENT_VERSION),
            'deprecated': requested < self.CURRENT_VERSION,
            'breaking_changes': requested.major < self.CURRENT_VERSION.major
        }


def versioned_api(version: str, deprecated: bool = False):
    """
    Decorator to mark API endpoint with version.
    
    Args:
        version: API version
        deprecated: Whether endpoint is deprecated
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Add version info to response
            result = func(*args, **kwargs)
            
            if hasattr(result, 'headers'):
                result.headers['X-API-Version'] = version
                if deprecated:
                    result.headers['Deprecation'] = 'true'
            
            return result
        
        wrapper._api_version = version
        wrapper._deprecated = deprecated
        
        return wrapper
    return decorator


# Global instance
version_manager = APIVersionManager()


def register_version(path: str, version: str, handler: Callable) -> VersionedAPI:
    """Register versioned endpoint."""
    return version_manager.register(path, version, handler)


def get_versioned_handler(path: str, version: Optional[str] = None) -> Optional[Callable]:
    """Get versioned handler."""
    return version_manager.get_handler(path, version)


# Export
__all__ = [
    'APIVersion',
    'VersionedAPI',
    'APIVersionManager',
    'version_manager',
    'versioned_api',
    'register_version',
    'get_versioned_handler'
]
