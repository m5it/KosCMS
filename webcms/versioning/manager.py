"""
Version Manager for WebCMS

Handles version creation, storage, retrieval, rollback, and pruning.
"""

import json
import logging
from typing import Dict, List, Optional, Any

from .models import Version
from .diff import DiffViewer

logger = logging.getLogger("webcms.versioning")


class VersionManager:
    """Manages content versioning lifecycle."""

    def __init__(self, storage_backend=None, max_versions=50):
        self.storage = storage_backend or self._default_storage()
        self.max_versions = max_versions
        self.diff_viewer = DiffViewer()

    def _default_storage(self):
        """Create default in-memory/file storage."""
        return _FileStorage("versions.json")

    async def create_version(self, content_id, content_type, data,
                            user_id=None, username=None, comment=None):
        """Create a new version snapshot."""
        versions = await self.list_versions(content_id, content_type)
        version_number = 1
        if versions:
            version_number = max(v.version_number for v in versions) + 1

        version = Version(
            content_id=content_id,
            content_type=content_type,
            data=data,
            user_id=user_id,
            username=username,
            version_number=version_number,
            comment=comment
        )

        await self.storage.save(version)
        await self._prune_versions(content_id, content_type)

        logger.info(f"Created version {version_number} for {content_type}:{content_id}")
        return version

    async def list_versions(self, content_id, content_type, limit=100):
        """List all versions for a content item."""
        versions = await self.storage.list(content_id, content_type)
        versions.sort(key=lambda v: v.version_number)
        return versions[:limit]

    async def get_version(self, version_id):
        """Get a specific version by ID."""
        return await self.storage.get(version_id)

    async def get_version_by_number(self, content_id, content_type, version_number):
        """Get a specific version by number."""
        versions = await self.list_versions(content_id, content_type)
        for v in versions:
            if v.version_number == version_number:
                return v
        return None

    async def rollback(self, content_id, content_type, version_number,
                      user_id=None, username=None, comment=None):
        """Rollback content to a specific version."""
        target = await self.get_version_by_number(content_id, content_type, version_number)
        if not target:
            return None

        rollback_comment = comment or f"Rolled back to version {version_number}"

        new_version = await self.create_version(
            content_id=content_id,
            content_type=content_type,
            data=target.data,
            user_id=user_id,
            username=username,
            comment=rollback_comment
        )

        return new_version

    async def compare_versions(self, version_id1, version_id2, field="content"):
        """Compare two versions."""
        v1 = await self.get_version(version_id1)
        v2 = await self.get_version(version_id2)

        if not v1 or not v2:
            return {"error": "One or both versions not found"}

        old_text = str(v1.data.get(field, ""))
        new_text = str(v2.data.get(field, ""))

        return {
            "version_1": v1.version_number,
            "version_2": v2.version_number,
            "field": field,
            "unified_diff": self.diff_viewer.text_diff(old_text, new_text),
            "word_diff": self.diff_viewer.word_diff(old_text, new_text),
            "structured_diff": self.diff_viewer.structured_diff(v1.data, v2.data)
        }

    async def delete_version(self, version_id):
        """Delete a specific version."""
        return await self.storage.delete(version_id)

    async def _prune_versions(self, content_id, content_type):
        """Remove old versions keeping only max_versions."""
        versions = await self.list_versions(content_id, content_type)
        if len(versions) <= self.max_versions:
            return

        to_delete = versions[:-self.max_versions]
        for version in to_delete:
            await self.storage.delete(version.version_id)
            logger.info(f"Pruned version {version.version_number} for {content_type}:{content_id}")

    async def get_audit_trail(self, content_id, content_type):
        """Get audit trail of all changes."""
        versions = await self.list_versions(content_id, content_type)
        return [v.to_dict() for v in versions]


class _FileStorage:
    """Simple file-based version storage."""

    def __init__(self, filepath):
        self.filepath = filepath
        self._memory = {}
        self._load()

    def _load(self):
        """Load versions from file."""
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
                self._memory = {
                    vid: Version.from_dict(vdata)
                    for vid, vdata in data.items()
                }
        except (FileNotFoundError, json.JSONDecodeError):
            self._memory = {}

    async def save(self, version):
        """Save a version."""
        self._memory[version.version_id] = version
        self._persist()

    async def list(self, content_id, content_type):
        """List versions for content."""
        return [
            v for v in self._memory.values()
            if v.content_id == content_id and v.content_type == content_type
        ]

    async def get(self, version_id):
        """Get version by ID."""
        return self._memory.get(version_id)

    async def delete(self, version_id):
        """Delete version by ID."""
        if version_id in self._memory:
            del self._memory[version_id]
            self._persist()
            return True
        return False

    def _persist(self):
        """Persist to file."""
        with open(self.filepath, 'w') as f:
            data = {
                vid: v.to_dict()
                for vid, v in self._memory.items()
            }
            json.dump(data, f, indent=2, default=str)
