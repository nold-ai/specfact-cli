"""
Unit tests for enhanced watch mode with hash-based change detection.
"""

from __future__ import annotations

from pathlib import Path

from specfact_cli.sync.watcher_enhanced import FileHashCache, compute_file_hash


class TestComputeFileHash:
    """Test compute_file_hash function."""

    def test_compute_hash_existing_file(self, tmp_path: Path) -> None:
        """Test computing hash for existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        file_hash = compute_file_hash(test_file)
        assert file_hash is not None
        assert len(file_hash) == 64  # SHA256 hex digest length

    def test_compute_hash_nonexistent_file(self, tmp_path: Path) -> None:
        """Test computing hash for non-existent file."""
        test_file = tmp_path / "nonexistent.txt"
        file_hash = compute_file_hash(test_file)
        assert file_hash is None

    def test_compute_hash_consistent(self, tmp_path: Path) -> None:
        """Test that hash is consistent for same content."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        hash1 = compute_file_hash(test_file)
        hash2 = compute_file_hash(test_file)
        assert hash1 == hash2

    def test_compute_hash_different_content(self, tmp_path: Path) -> None:
        """Test that hash differs for different content."""
        test_file1 = tmp_path / "test1.txt"
        test_file2 = tmp_path / "test2.txt"
        test_file1.write_text("content 1")
        test_file2.write_text("content 2")
        hash1 = compute_file_hash(test_file1)
        hash2 = compute_file_hash(test_file2)
        assert hash1 != hash2


class TestFileHashCache:
    """Test FileHashCache class."""

    def test_cache_creation(self, tmp_path: Path) -> None:
        """Test creating a hash cache."""
        cache_file = tmp_path / "cache.json"
        cache = FileHashCache(cache_file=cache_file)
        assert cache.cache_file == cache_file
        assert len(cache.hashes) == 0

    def test_set_and_get_hash(self, tmp_path: Path) -> None:
        """Test setting and getting file hash."""
        cache_file = tmp_path / "cache.json"
        cache = FileHashCache(cache_file=cache_file)
        test_path = Path("test.py")
        test_hash = "abc123"

        cache.set_hash(test_path, test_hash)
        assert cache.get_hash(test_path) == test_hash

    def test_has_changed(self, tmp_path: Path) -> None:
        """Test has_changed method."""
        cache_file = tmp_path / "cache.json"
        cache = FileHashCache(cache_file=cache_file)
        test_path = Path("test.py")

        # New file (no cached hash)
        assert cache.has_changed(test_path, "hash1") is True

        # Same hash (no change)
        cache.set_hash(test_path, "hash1")
        assert cache.has_changed(test_path, "hash1") is False

        # Different hash (changed)
        assert cache.has_changed(test_path, "hash2") is True

    def test_save_and_load_cache(self, tmp_path: Path) -> None:
        """Test saving and loading cache."""
        cache_file = tmp_path / "cache.json"
        cache = FileHashCache(cache_file=cache_file)
        test_path = Path("test.py")
        test_hash = "abc123"

        cache.set_hash(test_path, test_hash)
        cache.save()

        # Create new cache and load
        new_cache = FileHashCache(cache_file=cache_file)
        new_cache.load()
        assert new_cache.get_hash(test_path) == test_hash

    def test_dependencies(self, tmp_path: Path) -> None:
        """Test dependency tracking."""
        cache_file = tmp_path / "cache.json"
        cache = FileHashCache(cache_file=cache_file)
        test_path = Path("test.py")
        deps = [Path("dep1.py"), Path("dep2.py")]

        cache.set_dependencies(test_path, deps)
        assert cache.get_dependencies(test_path) == deps
