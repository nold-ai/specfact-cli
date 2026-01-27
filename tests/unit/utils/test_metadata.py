"""
Unit tests for metadata management module.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from specfact_cli.utils.metadata import (
    get_last_checked_version,
    get_last_version_check_timestamp,
    get_metadata,
    get_metadata_dir,
    get_metadata_file,
    is_version_check_needed,
    update_metadata,
)


class TestMetadataManagement:
    """Tests for metadata management functions."""

    def test_get_metadata_dir_creates_directory(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that get_metadata_dir creates directory if it doesn't exist."""
        # Mock home directory
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        metadata_dir = get_metadata_dir()
        assert metadata_dir.exists()
        assert metadata_dir.name == ".specfact"
        assert metadata_dir.parent == mock_home

    def test_get_metadata_file_returns_correct_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that get_metadata_file returns correct path."""
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        metadata_file = get_metadata_file()
        assert metadata_file.name == "metadata.json"
        assert metadata_file.parent.name == ".specfact"
        assert metadata_file.parent.parent == mock_home

    def test_get_metadata_returns_empty_dict_when_file_not_exists(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that get_metadata returns empty dict when file doesn't exist."""
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        metadata = get_metadata()
        assert metadata == {}

    def test_get_metadata_reads_existing_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that get_metadata reads existing metadata file."""
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        metadata_dir = mock_home / ".specfact"
        metadata_dir.mkdir()
        metadata_file = metadata_dir / "metadata.json"
        metadata_file.write_text(json.dumps({"last_checked_version": "1.0.0"}), encoding="utf-8")

        metadata = get_metadata()
        assert metadata == {"last_checked_version": "1.0.0"}

    def test_get_metadata_handles_corrupted_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that get_metadata handles corrupted JSON gracefully."""
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        metadata_dir = mock_home / ".specfact"
        metadata_dir.mkdir()
        metadata_file = metadata_dir / "metadata.json"
        metadata_file.write_text("invalid json content {", encoding="utf-8")

        metadata = get_metadata()
        assert metadata == {}  # Should return empty dict on corruption

    def test_update_metadata_creates_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that update_metadata creates file with new data."""
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        update_metadata(last_checked_version="1.0.0")

        metadata = get_metadata()
        assert metadata["last_checked_version"] == "1.0.0"

    def test_update_metadata_updates_existing_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that update_metadata updates existing file."""
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        # Create initial metadata
        update_metadata(last_checked_version="1.0.0")
        # Update with new data
        update_metadata(last_version_check_timestamp="2026-01-01T00:00:00+00:00")

        metadata = get_metadata()
        assert metadata["last_checked_version"] == "1.0.0"
        assert metadata["last_version_check_timestamp"] == "2026-01-01T00:00:00+00:00"

    def test_get_last_checked_version(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test get_last_checked_version function."""
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        # No version set
        assert get_last_checked_version() is None

        # Set version
        update_metadata(last_checked_version="1.0.0")
        assert get_last_checked_version() == "1.0.0"

    def test_get_last_version_check_timestamp(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test get_last_version_check_timestamp function."""
        mock_home = tmp_path / "home"
        mock_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        # No timestamp set
        assert get_last_version_check_timestamp() is None

        # Set timestamp
        timestamp = "2026-01-01T00:00:00+00:00"
        update_metadata(last_version_check_timestamp=timestamp)
        assert get_last_version_check_timestamp() == timestamp

    def test_is_version_check_needed_no_timestamp(self) -> None:
        """Test is_version_check_needed when timestamp is None."""
        assert is_version_check_needed(None) is True

    def test_is_version_check_needed_recent_timestamp(self) -> None:
        """Test is_version_check_needed when timestamp is recent (< 24 hours)."""
        recent_timestamp = datetime.now(UTC).isoformat()
        assert is_version_check_needed(recent_timestamp) is False

    def test_is_version_check_needed_old_timestamp(self) -> None:
        """Test is_version_check_needed when timestamp is old (>= 24 hours)."""
        old_timestamp = (datetime.now(UTC) - timedelta(hours=25)).isoformat()
        assert is_version_check_needed(old_timestamp) is True

    def test_is_version_check_needed_invalid_timestamp(self) -> None:
        """Test is_version_check_needed with invalid timestamp format."""
        # Invalid timestamp should be treated as needing check
        assert is_version_check_needed("invalid-timestamp") is True
