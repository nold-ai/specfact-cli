"""
Source tracking data models.

This module defines models for tracking links between specifications
and actual code/tests with hash-based change detection.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, Field


class SourceTracking(BaseModel):
    """Links specs to actual code/tests with hash-based change detection."""

    implementation_files: list[str] = Field(
        default_factory=list, description="Paths to source files (relative to repo root)"
    )
    test_files: list[str] = Field(default_factory=list, description="Paths to test files (relative to repo root)")
    file_hashes: dict[str, str] = Field(default_factory=dict, description="File path → SHA256 hash mapping")
    last_synced: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO timestamp of last sync",
    )
    source_functions: list[str] = Field(
        default_factory=list,
        description="Source function mappings (format: 'file.py::func')",
    )
    test_functions: list[str] = Field(
        default_factory=list,
        description="Test function mappings (format: 'test_file.py::test_func')",
    )

    @beartype
    @require(lambda self, file_path: isinstance(file_path, Path), "File path must be Path")
    @ensure(lambda self, file_path, result: isinstance(result, str) and len(result) == 64, "Hash must be SHA256 hex")
    def compute_hash(self, file_path: Path) -> str:
        """
        Compute SHA256 hash for change detection.

        Args:
            file_path: Path to file to hash

        Returns:
            SHA256 hash as hex string (64 characters)
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return hashlib.sha256(file_path.read_bytes()).hexdigest()

    @beartype
    @require(lambda self, file_path: isinstance(file_path, Path), "File path must be Path")
    @ensure(lambda self, file_path, result: isinstance(result, bool), "Must return bool")
    def has_changed(self, file_path: Path) -> bool:
        """
        Check if file changed since last sync.

        Args:
            file_path: Path to file to check

        Returns:
            True if file hash changed, False otherwise
        """
        if not file_path.exists():
            return True  # File deleted
        current_hash = self.compute_hash(file_path)
        stored_hash = self.file_hashes.get(str(file_path))
        return stored_hash != current_hash

    @beartype
    @require(lambda self, file_path: isinstance(file_path, Path), "File path must be Path")
    @ensure(lambda result: result is None, "Must return None")
    def update_hash(self, file_path: Path) -> None:
        """
        Update stored hash for a file.

        Args:
            file_path: Path to file to update
        """
        if file_path.exists():
            self.file_hashes[str(file_path)] = self.compute_hash(file_path)
        elif str(file_path) in self.file_hashes:
            # File deleted, remove from tracking
            del self.file_hashes[str(file_path)]

    @beartype
    @ensure(lambda result: result is None, "Must return None")
    def update_sync_timestamp(self) -> None:
        """Update last_synced timestamp to current time."""
        self.last_synced = datetime.now(UTC).isoformat()
