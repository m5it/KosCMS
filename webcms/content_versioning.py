"""
Content Versioning System

Provides version history and rollback capabilities for content
"""

import json
import difflib
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import uuid


@dataclass
class ContentVersion:
    """Represents a content version."""
    id: str
    content_id: str
    version_number: int
    title: str
    content: str
    author_id: str
    author_name: str
    created_at: str
    change_summary: Optional[str] = None
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class ContentVersionManager:
    """Manages content versioning."""
    
    def __init__(self, db=None):
        self.db = db
        self._ensure_table()
    
    def _ensure_table(self):
        """Ensure versions table exists."""
        if not self.db:
            return
        
        try:
            tables = self.db.list_tables()
            if 'content_versions' not in tables:
                self.db.execute("""
                    CREATE TABLE content_versions (
                        id TEXT PRIMARY KEY,
                        content_id TEXT NOT NULL,
                        version_number INTEGER NOT NULL,
                        title TEXT,
                        content TEXT,
                        author_id TEXT,
                        author_name TEXT,
                        created_at TEXT NOT NULL,
                        change_summary TEXT,
                        metadata TEXT,
                        UNIQUE(content_id, version_number)
                    )
                """)
                
                # Create index for faster lookups
                self.db.execute("""
                    CREATE INDEX idx_content_versions_content_id 
                    ON content_versions(content_id)
                """)
        except Exception as e:
            print(f"Warning: Could not create versions table: {e}")
    
    def create_version(self, content_id: str, title: str, content: str,
                      author_id: str, author_name: str,
                      change_summary: Optional[str] = None,
                      metadata: Optional[Dict] = None) -> ContentVersion:
        """
        Create a new version of content.
        
        Args:
            content_id: Content identifier
            title: Content title
            content: Content body
            author_id: Author user ID
            author_name: Author display name
            change_summary: Optional change description
            metadata: Optional metadata
        
        Returns:
            Created version
        """
        # Get next version number
        version_number = self._get_next_version_number(content_id)
        
        version = ContentVersion(
            id=str(uuid.uuid4()),
            content_id=content_id,
            version_number=version_number,
            title=title,
            content=content,
            author_id=author_id,
            author_name=author_name,
            created_at=datetime.utcnow().isoformat(),
            change_summary=change_summary,
            metadata=metadata
        )
        
        # Save to database
        if self.db:
            try:
                meta_json = json.dumps(metadata) if metadata else '{}'
                self.db.execute(f"""
                    INSERT INTO content_versions 
                    (id, content_id, version_number, title, content, author_id, 
                     author_name, created_at, change_summary, metadata)
                    VALUES (
                        '{version.id}',
                        '{version.content_id}',
                        {version.version_number},
                        '{version.title.replace("'", "''")}',
                        '{version.content.replace("'", "''")}',
                        '{version.author_id}',
                        '{version.author_name.replace("'", "''")}',
                        '{version.created_at}',
                        '{(version.change_summary or '').replace("'", "''")}',
                        '{meta_json}'
                    )
                """)
            except Exception as e:
                print(f"Error saving version: {e}")
        
        return version
    
    def _get_next_version_number(self, content_id: str) -> int:
        """Get next version number for content."""
        if not self.db:
            return 1
        
        try:
            result = self.db.query(f"""
                SELECT MAX(version_number) as max_version 
                FROM content_versions 
                WHERE content_id = '{content_id}'
            """)
            max_version = result.get('rows', [{}])[0].get('max_version', 0)
            return (max_version or 0) + 1
        except Exception:
            return 1
    
    def get_versions(self, content_id: str, limit: int = 50) -> List[ContentVersion]:
        """
        Get version history for content.
        
        Args:
            content_id: Content identifier
            limit: Maximum versions to return
        
        Returns:
            List of versions
        """
        if not self.db:
            return []
        
        try:
            result = self.db.query(f"""
                SELECT * FROM content_versions 
                WHERE content_id = '{content_id}'
                ORDER BY version_number DESC
                LIMIT {limit}
            """)
            
            versions = []
            for row in result.get('rows', []):
                versions.append(ContentVersion(
                    id=row['id'],
                    content_id=row['content_id'],
                    version_number=row['version_number'],
                    title=row['title'],
                    content=row['content'],
                    author_id=row['author_id'],
                    author_name=row['author_name'],
                    created_at=row['created_at'],
                    change_summary=row.get('change_summary'),
                    metadata=json.loads(row['metadata']) if row.get('metadata') else None
                ))
            
            return versions
            
        except Exception as e:
            print(f"Error fetching versions: {e}")
            return []
    
    def get_version(self, content_id: str, version_number: int) -> Optional[ContentVersion]:
        """
        Get specific version.
        
        Args:
            content_id: Content identifier
            version_number: Version number
        
        Returns:
            Version or None
        """
        if not self.db:
            return None
        
        try:
            result = self.db.query(f"""
                SELECT * FROM content_versions 
                WHERE content_id = '{content_id}' 
                AND version_number = {version_number}
            """)
            
            rows = result.get('rows', [])
            if not rows:
                return None
            
            row = rows[0]
            return ContentVersion(
                id=row['id'],
                content_id=row['content_id'],
                version_number=row['version_number'],
                title=row['title'],
                content=row['content'],
                author_id=row['author_id'],
                author_name=row['author_name'],
                created_at=row['created_at'],
                change_summary=row.get('change_summary'),
                metadata=json.loads(row['metadata']) if row.get('metadata') else None
            )
            
        except Exception as e:
            print(f"Error fetching version: {e}")
            return None
    
    def compare_versions(self, content_id: str, version_a: int, 
                         version_b: int) -> Dict:
        """
        Compare two versions.
        
        Args:
            content_id: Content identifier
            version_a: First version number
            version_b: Second version number
        
        Returns:
            Comparison results with diff
        """
        v1 = self.get_version(content_id, version_a)
        v2 = self.get_version(content_id, version_b)
        
        if not v1 or not v2:
            return {'error': 'One or both versions not found'}
        
        # Generate diffs
        title_diff = list(difflib.unified_diff(
            v1.title.splitlines(keepends=True),
            v2.title.splitlines(keepends=True),
            fromfile=f'v{version_a}',
            tofile=f'v{version_b}'
        ))
        
        content_diff = list(difflib.unified_diff(
            v1.content.splitlines(keepends=True),
            v2.content.splitlines(keepends=True),
            fromfile=f'v{version_a}',
            tofile=f'v{version_b}'
        ))
        
        return {
            'version_a': version_a,
            'version_b': version_b,
            'title_changes': len(title_diff) > 0,
            'content_changes': len(content_diff) > 0,
            'title_diff': ''.join(title_diff),
            'content_diff': ''.join(content_diff),
            'author_a': v1.author_name,
            'author_b': v2.author_name,
            'date_a': v1.created_at,
            'date_b': v2.created_at
        }
    
    def restore_version(self, content_id: str, version_number: int,
                       restored_by: str) -> Optional[ContentVersion]:
        """
        Restore content to a previous version.
        
        Args:
            content_id: Content identifier
            version_number: Version to restore
            restored_by: User restoring the version
        
        Returns:
            New version created from restore
        """
        version = self.get_version(content_id, version_number)
        if not version:
            return None
        
        # Create new version with restored content
        return self.create_version(
            content_id=content_id,
            title=version.title,
            content=version.content,
            author_id=restored_by,
            author_name='System',
            change_summary=f'Restored from version {version_number}',
            metadata={'restored_from': version_number}
        )
    
    def delete_version(self, content_id: str, version_number: int) -> bool:
        """
        Delete a specific version.
        
        Args:
            content_id: Content identifier
            version_number: Version to delete
        
        Returns:
            True if deleted
        """
        if not self.db:
            return False
        
        try:
            self.db.execute(f"""
                DELETE FROM content_versions 
                WHERE content_id = '{content_id}' 
                AND version_number = {version_number}
            """)
            return True
        except Exception:
            return False
    
    def cleanup_old_versions(self, content_id: str, keep_count: int = 20) -> int:
        """
        Clean up old versions keeping only recent ones.
        
        Args:
            content_id: Content identifier
            keep_count: Number of versions to keep
        
        Returns:
            Number of versions deleted
        """
        if not self.db:
            return 0
        
        try:
            result = self.db.execute(f"""
                DELETE FROM content_versions 
                WHERE content_id = '{content_id}' 
                AND version_number <= (
                    SELECT MAX(version_number) - {keep_count} 
                    FROM content_versions 
                    WHERE content_id = '{content_id}'
                )
            """)
            return result.get('rowcount', 0)
        except Exception:
            return 0
    
    def get_version_stats(self, content_id: str) -> Dict:
        """
        Get version statistics.
        
        Args:
            content_id: Content identifier
        
        Returns:
            Version statistics
        """
        if not self.db:
            return {}
        
        try:
            result = self.db.query(f"""
                SELECT 
                    COUNT(*) as total_versions,
                    MAX(version_number) as latest_version,
                    MIN(created_at) as first_version_date,
                    MAX(created_at) as latest_version_date
                FROM content_versions 
                WHERE content_id = '{content_id}'
            """)
            
            row = result.get('rows', [{}])[0]
            return {
                'total_versions': row.get('total_versions', 0),
                'latest_version': row.get('latest_version', 0),
                'first_version_date': row.get('first_version_date'),
                'latest_version_date': row.get('latest_version_date')
            }
        except Exception:
            return {}


# Global instance
version_manager = ContentVersionManager()


def track_content_change(content_id: str, title: str, content: str,
                        author_id: str, author_name: str,
                        change_summary: Optional[str] = None) -> ContentVersion:
    """Track a content change."""
    return version_manager.create_version(
        content_id=content_id,
        title=title,
        content=content,
        author_id=author_id,
        author_name=author_name,
        change_summary=change_summary
    )


# Export
__all__ = [
    'ContentVersion',
    'ContentVersionManager',
    'version_manager',
    'track_content_change'
]
