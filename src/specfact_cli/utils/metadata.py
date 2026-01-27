"""
Metadata management for SpecFact CLI.

This module manages metadata stored in ~/.specfact/metadata.json for tracking:
- Last checked CLI version (for template check optimization)
- Last version check timestamp (for PyPI update check rate limiting)
"""

from __future__ import annotations

import contextlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require


@beartype
@ensure(lambda result: isinstance(result, Path) and result.exists(), "Must return existing Path")
def get_metadata_dir() -> Path:
    """
    Get the metadata directory path (~/.specfact/), creating it if needed.

    Returns:
        Path to metadata directory

    Raises:
        OSError: If directory cannot be created
    """
    home_dir = Path.home()
    metadata_dir = home_dir / ".specfact"
    metadata_dir.mkdir(mode=0o755, exist_ok=True)
    return metadata_dir


@beartype
@ensure(lambda result: isinstance(result, Path), "Must return Path")
def get_metadata_file() -> Path:
    """
    Get the path to the metadata file.

    Returns:
        Path to metadata.json file
    """
    metadata_dir = get_metadata_dir()
    return metadata_dir / "metadata.json"


@beartype
@ensure(lambda result: isinstance(result, dict), "Must return dict")
def get_metadata() -> dict[str, Any]:
    """
    Read metadata from ~/.specfact/metadata.json.

    Returns:
        Metadata dictionary, empty dict if file doesn't exist or is corrupted

    Note:
        Gracefully handles file corruption by returning empty dict.
    """
    metadata_file = get_metadata_file()

    if not metadata_file.exists():
        return {}

    try:
        with metadata_file.open(encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
    except (json.JSONDecodeError, OSError, PermissionError):
        # File is corrupted or unreadable, return empty dict
        return {}


@beartype
@ensure(lambda result: result is None, "Must return None")
def update_metadata(**kwargs: Any) -> None:
    """
    Update metadata file with provided key-value pairs.

    Args:
        **kwargs: Key-value pairs to update in metadata (all keys must be strings)

    Raises:
        OSError: If file cannot be written
    """
    # Validate that all keys are strings
    if not all(isinstance(k, str) for k in kwargs):
        msg = "All metadata keys must be strings"
        raise TypeError(msg)

    metadata_file = get_metadata_file()
    metadata = get_metadata()
    metadata.update(kwargs)

    # Write atomically by writing to temp file first, then renaming
    temp_file = metadata_file.with_suffix(".json.tmp")
    try:
        with temp_file.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        temp_file.replace(metadata_file)
    except Exception:
        # Clean up temp file on error
        with contextlib.suppress(Exception):
            temp_file.unlink()
        raise


@beartype
@ensure(lambda result: result is None or isinstance(result, str), "Must return str or None")
def get_last_checked_version() -> str | None:
    """
    Get the last checked CLI version from metadata.

    Returns:
        Version string if set, None otherwise
    """
    metadata = get_metadata()
    return metadata.get("last_checked_version")


@beartype
@ensure(lambda result: result is None or isinstance(result, str), "Must return str or None")
def get_last_version_check_timestamp() -> str | None:
    """
    Get the last version check timestamp from metadata.

    Returns:
        ISO format timestamp string if set, None otherwise
    """
    metadata = get_metadata()
    return metadata.get("last_version_check_timestamp")


@beartype
@require(
    lambda timestamp: timestamp is None or isinstance(timestamp, str),
    "Timestamp must be string or None",
)
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def is_version_check_needed(timestamp: str | None, hours_threshold: int = 24) -> bool:
    """
    Check if version check is needed based on timestamp.

    Args:
        timestamp: ISO format timestamp string or None
        hours_threshold: Hours threshold for checking (default: 24)

    Returns:
        True if check is needed (timestamp is None or >= hours_threshold ago), False otherwise
    """
    if timestamp is None:
        return True

    try:
        last_check = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if last_check.tzinfo is None:
            last_check = last_check.replace(tzinfo=UTC)

        now = datetime.now(UTC)
        time_diff = now - last_check
        hours_elapsed = time_diff.total_seconds() / 3600

        return hours_elapsed >= hours_threshold
    except (ValueError, AttributeError):
        # Invalid timestamp format, treat as needing check
        return True
