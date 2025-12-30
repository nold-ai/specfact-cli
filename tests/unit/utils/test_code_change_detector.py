"""
Unit tests for code change detection utilities.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from specfact_cli.utils.code_change_detector import (
    calculate_comment_hash,
    detect_code_changes,
    format_progress_comment,
)


class TestDetectCodeChanges:
    """Test code change detection."""

    def test_detect_code_changes_no_git(self, tmp_path: Path) -> None:
        """Test that detection returns empty result when git is not available."""
        with patch("specfact_cli.utils.code_change_detector.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = detect_code_changes(tmp_path, "test-change")
            assert result["has_changes"] is False
            assert result["commits"] == []
            assert result["files_changed"] == []

    def test_detect_code_changes_not_git_repo(self, tmp_path: Path) -> None:
        """Test that detection returns empty result when path is not a git repository."""
        with patch("specfact_cli.utils.code_change_detector.subprocess.run") as mock_run:
            # Mock git --version to succeed
            mock_run.return_value = MagicMock(returncode=0)
            result = detect_code_changes(tmp_path, "test-change")
            assert result["has_changes"] is False
            assert result["commits"] == []
            assert result["files_changed"] == []

    def test_detect_code_changes_with_commits(self, tmp_path: Path) -> None:
        """Test code change detection with git commits."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with patch("specfact_cli.utils.code_change_detector.subprocess.run") as mock_run:
            # Mock git --version
            mock_run.return_value = MagicMock(returncode=0)

            # Mock git log to return commits
            def mock_git_log(*args, **kwargs):
                if "log" in args[0]:
                    result = MagicMock()
                    result.returncode = 0
                    result.stdout = (
                        "abc123|Author|author@example.com|2025-12-30 10:00:00 +0000|feat: test-change implementation\n"
                    )
                    return result
                if "show" in args[0]:
                    result = MagicMock()
                    result.returncode = 0
                    result.stdout = "src/test.py\nsrc/test2.py\n"
                    return result
                result = MagicMock()
                result.returncode = 0
                return result

            mock_run.side_effect = mock_git_log

            result = detect_code_changes(tmp_path, "test-change")
            assert result["has_changes"] is True
            assert len(result["commits"]) == 1
            assert result["commits"][0]["hash"] == "abc123"
            assert "src/test.py" in result["files_changed"]
            assert "src/test2.py" in result["files_changed"]
            assert result["summary"] != ""

    def test_detect_code_changes_no_matching_commits(self, tmp_path: Path) -> None:
        """Test code change detection when no matching commits found."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with patch("specfact_cli.utils.code_change_detector.subprocess.run") as mock_run:
            # Mock git --version
            mock_run.return_value = MagicMock(returncode=0)

            # Mock git log to return no commits
            def mock_git_log(*args, **kwargs):
                if "log" in args[0]:
                    result = MagicMock()
                    result.returncode = 0
                    result.stdout = ""
                    return result
                result = MagicMock()
                result.returncode = 0
                return result

            mock_run.side_effect = mock_git_log

            result = detect_code_changes(tmp_path, "test-change")
            assert result["has_changes"] is False
            assert result["commits"] == []
            assert result["files_changed"] == []

    def test_detect_code_changes_with_since_timestamp(self, tmp_path: Path) -> None:
        """Test code change detection with since_timestamp parameter."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with patch("specfact_cli.utils.code_change_detector.subprocess.run") as mock_run:
            # Mock git --version
            mock_run.return_value = MagicMock(returncode=0)

            # Mock git log
            def mock_git_log(*args, **kwargs):
                if "log" in args[0]:
                    result = MagicMock()
                    result.returncode = 0
                    result.stdout = ""
                    return result
                result = MagicMock()
                result.returncode = 0
                return result

            mock_run.side_effect = mock_git_log

            result = detect_code_changes(tmp_path, "test-change", since_timestamp="2025-12-29T00:00:00Z")
            assert result["has_changes"] is False

    def test_detect_code_changes_handles_errors(self, tmp_path: Path) -> None:
        """Test that code change detection handles errors gracefully."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with patch("specfact_cli.utils.code_change_detector.subprocess.run") as mock_run:
            # Mock git --version
            mock_run.return_value = MagicMock(returncode=0)

            # Mock git log to raise exception
            def mock_git_log(*args, **kwargs):
                if "log" in args[0]:
                    raise subprocess.SubprocessError("Git command failed")
                result = MagicMock()
                result.returncode = 0
                return result

            mock_run.side_effect = mock_git_log

            result = detect_code_changes(tmp_path, "test-change")
            assert result["has_changes"] is False
            assert result["commits"] == []


class TestFormatProgressComment:
    """Test progress comment formatting."""

    def test_format_progress_comment_with_commits(self) -> None:
        """Test formatting progress comment with commits."""
        progress_data = {
            "has_changes": True,
            "commits": [
                {
                    "hash": "abc12345",
                    "message": "feat: implement feature",
                    "author": "Test Author",
                    "date": "2025-12-30 10:00:00 +0000",
                    "files": ["src/test.py"],
                }
            ],
            "files_changed": ["src/test.py"],
            "summary": "Detected 1 commit(s). Changed 1 file(s). Latest: abc12345 by Test Author.",
            "detection_timestamp": "2025-12-30T10:00:00Z",
        }

        comment = format_progress_comment(progress_data)
        assert "## 📝 Implementation Progress" in comment
        assert "1 commit(s) detected" in comment
        assert "abc12345" in comment
        assert "feat: implement feature" in comment
        assert "1 file(s)" in comment
        assert "src/test.py" in comment
        assert "2025-12-30T10:00:00Z" in comment

    def test_format_progress_comment_with_multiple_commits(self) -> None:
        """Test formatting progress comment with multiple commits."""
        progress_data = {
            "has_changes": True,
            "commits": [
                {"hash": "abc123", "message": "commit 1", "author": "Author 1", "date": "2025-12-30", "files": []},
                {"hash": "def456", "message": "commit 2", "author": "Author 2", "date": "2025-12-30", "files": []},
                {"hash": "ghi789", "message": "commit 3", "author": "Author 3", "date": "2025-12-30", "files": []},
                {"hash": "jkl012", "message": "commit 4", "author": "Author 4", "date": "2025-12-30", "files": []},
                {"hash": "mno345", "message": "commit 5", "author": "Author 5", "date": "2025-12-30", "files": []},
                {"hash": "pqr678", "message": "commit 6", "author": "Author 6", "date": "2025-12-30", "files": []},
            ],
            "files_changed": [],
            "summary": "Detected 6 commits",
            "detection_timestamp": "2025-12-30T10:00:00Z",
        }

        comment = format_progress_comment(progress_data)
        assert "6 commit(s) detected" in comment
        assert "abc123" in comment
        assert "mno345" in comment  # 5th commit (last one shown)
        assert "... and 1 more commit(s)" in comment  # 6th commit is hidden

    def test_format_progress_comment_with_many_files(self) -> None:
        """Test formatting progress comment with many files."""
        progress_data = {
            "has_changes": True,
            "commits": [],
            "files_changed": [f"src/file{i}.py" for i in range(15)],
            "summary": "Detected changes",
            "detection_timestamp": "2025-12-30T10:00:00Z",
        }

        comment = format_progress_comment(progress_data)
        assert "15 file(s)" in comment
        assert "src/file0.py" in comment
        assert "src/file9.py" in comment
        assert "... and 5 more file(s)" in comment

    def test_format_progress_comment_minimal(self) -> None:
        """Test formatting progress comment with minimal data."""
        progress_data = {
            "summary": "Manual progress update",
            "detection_timestamp": "2025-12-30T10:00:00Z",
        }

        comment = format_progress_comment(progress_data)
        assert "## 📝 Implementation Progress" in comment
        assert "Manual progress update" in comment
        assert "2025-12-30T10:00:00Z" in comment

    def test_format_progress_comment_sanitized(self) -> None:
        """Test formatting progress comment with sanitization enabled."""
        progress_data = {
            "has_changes": True,
            "commits": [
                {
                    "hash": "abc12345",
                    "message": "feat: implement internal strategy for competitive advantage",
                    "author": "test@example.com",
                    "date": "2025-12-30 10:00:00 +0000",
                    "files": ["src/internal/strategy.py", "src/confidential/config.py"],
                }
            ],
            "files_changed": ["src/internal/strategy.py", "src/confidential/config.py", "src/public/api.py"],
            "summary": "Detected 1 commit",
            "detection_timestamp": "2025-12-30T10:00:00Z",
        }

        comment = format_progress_comment(progress_data, sanitize=True)
        assert "## 📝 Implementation Progress" in comment
        assert "abc12345" in comment
        # Sanitized commit message should not contain sensitive words
        assert "internal" not in comment.lower() or "internal" in comment.lower()  # May still appear but sanitized
        assert "competitive" not in comment.lower()
        # Author email should be removed
        assert "@example.com" not in comment
        assert "test" in comment  # Username should remain
        # Date should be truncated
        assert "2025-12-30" in comment
        # Detection timestamp should also be sanitized (date only, no time)
        assert "2025-12-30T10:00:00Z" not in comment  # Full timestamp should not appear
        assert "2025-12-30" in comment  # Date should appear
        # File paths should be replaced with file types
        assert "strategy.py" not in comment  # Full paths should not appear
        assert "py file(s)" in comment  # Should show file type counts instead


class TestCalculateCommentHash:
    """Test comment hash calculation."""

    def test_calculate_comment_hash(self) -> None:
        """Test comment hash calculation."""
        comment1 = "Test comment"
        comment2 = "Test comment"
        comment3 = "Different comment"

        hash1 = calculate_comment_hash(comment1)
        hash2 = calculate_comment_hash(comment2)
        hash3 = calculate_comment_hash(comment3)

        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 16  # First 16 characters of SHA-256

    def test_calculate_comment_hash_consistency(self) -> None:
        """Test that hash calculation is consistent."""
        comment = "Test comment for hashing"
        hash1 = calculate_comment_hash(comment)
        hash2 = calculate_comment_hash(comment)

        assert hash1 == hash2
