"""
Unit tests for RepositorySync - Contract-First approach.

Most validation is covered by @beartype and @icontract decorators.
Only edge cases and business logic are tested here.
"""

from __future__ import annotations

from pathlib import Path

from specfact_cli.sync.repository_sync import RepositorySync, RepositorySyncResult


class TestRepositorySync:
    """Test cases for RepositorySync - focused on edge cases and business logic."""

    def test_detect_code_changes_with_src_dir(self, tmp_path: Path) -> None:
        """Test detecting code changes in src/ directory."""
        # Create src directory structure
        src_dir = tmp_path / "src" / "module"
        src_dir.mkdir(parents=True)
        python_file = src_dir / "module.py"
        python_file.write_text("def test_function():\n    pass\n")

        sync = RepositorySync(tmp_path)
        changes = sync.detect_code_changes(tmp_path)

        # Should detect python file
        relative_path = str(python_file.relative_to(tmp_path))
        change_found = any(change["relative_path"] == relative_path for change in changes)
        assert change_found, f"Expected {relative_path} in changes"

    def test_detect_code_changes_no_src_dir(self, tmp_path: Path) -> None:
        """Test detecting code changes when src/ directory doesn't exist."""
        sync = RepositorySync(tmp_path)
        changes = sync.detect_code_changes(tmp_path)

        # Should return empty list
        assert isinstance(changes, list)
        assert len(changes) == 0

    def test_sync_repository_changes_no_changes(self, tmp_path: Path) -> None:
        """Test sync with no code changes."""
        sync = RepositorySync(tmp_path)
        result = sync.sync_repository_changes(tmp_path)

        assert isinstance(result, RepositorySyncResult)
        assert result.status == "success"
        assert len(result.code_changes) == 0
        assert len(result.plan_updates) == 0
        assert len(result.deviations) == 0

    def test_get_file_hash(self, tmp_path: Path) -> None:
        """Test file hash calculation."""
        test_file = tmp_path / "test.py"
        test_content = "# Test file\nprint('hello')\n"
        test_file.write_text(test_content)

        sync = RepositorySync(tmp_path)
        file_hash = sync._get_file_hash(test_file)

        assert file_hash != "", "File hash should not be empty for non-empty file"
        assert len(file_hash) == 64, "SHA256 hash should be 64 characters (hex)"

    def test_get_file_hash_nonexistent_file(self, tmp_path: Path) -> None:
        """Test file hash calculation for nonexistent file."""
        sync = RepositorySync(tmp_path)
        nonexistent_file = tmp_path / "nonexistent.py"
        file_hash = sync._get_file_hash(nonexistent_file)

        assert file_hash == "", "File hash should be empty for nonexistent file"

    def test_track_deviations_no_manual_plan(self, tmp_path: Path) -> None:
        """Test deviation tracking when manual plan doesn't exist."""
        sync = RepositorySync(tmp_path)
        target = tmp_path / ".specfact"
        target.mkdir(exist_ok=True)

        deviations = sync.track_deviations([], target)

        # Should return empty list
        assert isinstance(deviations, list)
        assert len(deviations) == 0
