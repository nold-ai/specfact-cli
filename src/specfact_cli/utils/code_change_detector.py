"""
Code change detection utilities for tracking implementation progress.

This module provides utilities to detect code changes (git commits, file modifications)
related to change proposals and generate progress summaries.
"""

from __future__ import annotations

import hashlib
import logging
import subprocess
from datetime import datetime


try:
    from datetime import UTC
except ImportError:
    UTC = UTC  # type: ignore[assignment]
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.common.logger_setup import LoggerSetup
from specfact_cli.utils.contract_predicates import repo_path_exists


logger = LoggerSetup.get_logger(__name__) or logging.getLogger(__name__)


@beartype
@require(lambda repo_path: isinstance(repo_path, Path), "Repository path must be Path")
@require(repo_path_exists, "Repository path must exist")
@require(lambda change_id: isinstance(change_id, str) and len(change_id) > 0, "Change ID must be non-empty string")
@ensure(lambda result: isinstance(result, dict), "Must return dict")
def detect_code_changes(
    repo_path: Path,
    change_id: str,
    since_timestamp: str | None = None,
) -> dict[str, Any]:
    """
    Detect code changes related to a change proposal.

    Args:
        repo_path: Path to git repository
        change_id: Change proposal ID to search for in commits
        since_timestamp: ISO 8601 timestamp to search commits since (optional)

    Returns:
        Dict with keys:
            - `has_changes`: bool - Whether any changes were detected
            - `commits`: list[dict] - List of commit dicts with keys: hash, message, author, date, files
            - `files_changed`: list[str] - List of file paths that changed
            - `summary`: str - Human-readable summary of changes
            - `detection_timestamp`: str - ISO 8601 timestamp of detection

    Note:
        Searches git commit messages for change_id and file paths that might be related.
        Falls back to file monitoring if git is not available.
    """
    result: dict[str, Any] = {
        "has_changes": False,
        "commits": [],
        "files_changed": [],
        "summary": "",
        "detection_timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }

    try:
        subprocess.run(
            ["git", "--version"],
            capture_output=True,
            check=True,
            timeout=5,
            cwd=repo_path,
        )
    except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
        logger.warning("Git not available, skipping code change detection")
        return result

    git_dir = repo_path / ".git"
    if not git_dir.exists() and not (repo_path / ".git").is_dir():
        logger.warning(f"Not a git repository: {repo_path}")
        return result

    try:
        _fill_detect_code_changes_from_git(repo_path, change_id, since_timestamp, result)
    except subprocess.TimeoutExpired:
        logger.warning("Git command timed out during code change detection")
    except subprocess.SubprocessError as e:
        logger.warning(f"Git command failed: {e}")
    except Exception as e:
        logger.warning(f"Unexpected error during code change detection: {e}")

    return result


def _fill_detect_code_changes_from_git(
    repo_path: Path, change_id: str, since_timestamp: str | None, result: dict[str, Any]
) -> None:
    since_arg = ["--since", since_timestamp] if since_timestamp else []
    git_log_cmd = [
        "git",
        "log",
        "--all",
        "--grep",
        change_id,
        "--format=%H|%an|%ae|%ad|%s",
        "--date=iso",
        *since_arg,
    ]
    log_result = subprocess.run(
        git_log_cmd,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        cwd=repo_path,
    )
    if log_result.returncode != 0:
        logger.warning(f"Git log failed: {log_result.stderr}")
        return

    commits: list[dict[str, Any]] = []
    files_changed_set: set[str] = set()
    for line in log_result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("|", 4)
        if len(parts) < 5:
            continue
        commit_hash, author_name, author_email, commit_date, commit_message = parts
        files_result = subprocess.run(
            ["git", "show", "--name-only", "--format=", commit_hash],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            cwd=repo_path,
        )
        commit_files: list[str] = []
        if files_result.returncode == 0:
            commit_files = [
                f.strip() for f in files_result.stdout.strip().split("\n") if f.strip() and not f.startswith("commit")
            ]
            files_changed_set.update(commit_files)
        commits.append(
            {
                "hash": commit_hash,
                "message": commit_message,
                "author": author_name,
                "email": author_email,
                "date": commit_date,
                "files": commit_files,
            }
        )

    if not commits:
        return
    result["has_changes"] = True
    result["commits"] = commits
    result["files_changed"] = sorted(files_changed_set)
    summary_parts = [
        f"Detected {len(commits)} commit(s) related to '{change_id}'",
        f"Changed {len(result['files_changed'])} file(s)",
        f"Latest: {commits[0]['hash'][:8]} by {commits[0]['author']}",
    ]
    result["summary"] = ". ".join(summary_parts) + "."


@beartype
@require(lambda progress_data: isinstance(progress_data, dict), "Progress data must be dict")
@ensure(lambda result: isinstance(result, str), "Must return string")
def format_progress_comment(progress_data: dict[str, Any], sanitize: bool = False) -> str:
    """
    Format progress comment from code change detection data.

    Args:
        progress_data: Dict from detect_code_changes() or manual progress data
        sanitize: If True, sanitize sensitive information (commit messages, file paths, author emails)

    Returns:
        Formatted markdown comment text
    """
    comment_parts = ["## 📝 Implementation Progress"]
    _append_progress_commits(comment_parts, progress_data, sanitize)
    _append_progress_files(comment_parts, progress_data, sanitize)
    if progress_data.get("summary"):
        comment_parts.append("")
        comment_parts.append(f"*{progress_data['summary']}*")

    if progress_data.get("detection_timestamp"):
        comment_parts.append("")
        detection_timestamp = progress_data["detection_timestamp"]
        if sanitize and "T" in detection_timestamp:
            detection_timestamp = detection_timestamp.split("T")[0]
        comment_parts.append(f"*Detected: {detection_timestamp}*")

    return "\n".join(comment_parts)


def _append_progress_commits(comment_parts: list[str], progress_data: dict[str, Any], sanitize: bool) -> None:
    if not progress_data.get("commits"):
        return
    import re

    commits = progress_data["commits"]
    comment_parts.extend(["", f"**Commits**: {len(commits)} commit(s) detected", ""])
    for commit in commits[:5]:
        commit_hash_short = commit.get("hash", "")[:8]
        commit_message = commit.get("message", "")
        commit_author = commit.get("author", "")
        commit_date = commit.get("date", "")
        if sanitize:
            commit_message = re.sub(r"(?i)\b(internal|confidential|private|secret)\b", "", commit_message)
            commit_message = re.sub(r"(?i)\b(competitive|strategy|positioning)\b.*", "", commit_message)
            if len(commit_message) > 100:
                commit_message = commit_message[:97] + "..."
            if "@" in commit_author:
                commit_author = commit_author.split("@")[0]
            if " " in commit_date:
                commit_date = commit_date.split(" ")[0]
        comment_parts.append(f"- `{commit_hash_short}` - {commit_message} ({commit_author}, {commit_date})")
    if len(commits) > 5:
        comment_parts.append(f"- ... and {len(commits) - 5} more commit(s)")


def _append_progress_files(comment_parts: list[str], progress_data: dict[str, Any], sanitize: bool) -> None:
    if not progress_data.get("files_changed"):
        return
    files = progress_data["files_changed"]
    comment_parts.extend(["", f"**Files Changed**: {len(files)} file(s)", ""])
    if sanitize:
        file_types: dict[str, int] = {}
        for file_path in files:
            if "." in file_path:
                ext = file_path.split(".")[-1]
                file_types[ext] = file_types.get(ext, 0) + 1
            else:
                file_types["(no extension)"] = file_types.get("(no extension)", 0) + 1
        for ext, count in sorted(file_types.items())[:10]:
            comment_parts.append(f"- {count} {ext} file(s)")
        if len(file_types) > 10:
            comment_parts.append(f"- ... and {len(file_types) - 10} more file type(s)")
    else:
        for file_path in files[:10]:
            comment_parts.append(f"- `{file_path}`")
        if len(files) > 10:
            comment_parts.append(f"- ... and {len(files) - 10} more file(s)")


@beartype
@require(lambda comment_text: isinstance(comment_text, str), "Comment text must be string")
@ensure(lambda result: isinstance(result, str), "Must return string")
def calculate_comment_hash(comment_text: str) -> str:
    """
    Calculate hash of comment text to detect duplicates.

    Args:
        comment_text: Comment text to hash

    Returns:
        SHA-256 hash (first 16 characters)
    """
    hash_obj = hashlib.sha256(comment_text.encode("utf-8"))
    return hash_obj.hexdigest()[:16]
