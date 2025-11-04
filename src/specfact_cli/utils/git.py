"""
Git operations utilities.

This module provides helpers for common Git operations used by the CLI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import git
from beartype import beartype
from git import Repo
from icontract import ensure, require


class GitOperations:
    """Helper class for Git operations."""

    @beartype
    @require(lambda repo_path: isinstance(repo_path, (Path, str)), "Repo path must be Path or str")
    def __init__(self, repo_path: Path | str = ".") -> None:
        """
        Initialize Git operations.

        Args:
            repo_path: Path to the Git repository
        """
        self.repo_path = Path(repo_path)
        self.repo: Repo | None = None

        if self._is_git_repo():
            self.repo = Repo(self.repo_path)

    def _is_git_repo(self) -> bool:
        """
        Check if path is a Git repository.

        Returns:
            True if path is a Git repository
        """
        try:
            _ = Repo(self.repo_path)
            return True
        except git.exc.InvalidGitRepositoryError:
            return False

    def init(self) -> None:
        """Initialize a new Git repository."""
        self.repo = Repo.init(self.repo_path)

    @beartype
    @require(
        lambda branch_name: isinstance(branch_name, str) and len(branch_name) > 0,
        "Branch name must be non-empty string",
    )
    @require(lambda self: self.repo is not None, "Git repository must be initialized")
    def create_branch(self, branch_name: str, checkout: bool = True) -> None:
        """
        Create a new branch.

        Args:
            branch_name: Name of the new branch
            checkout: Whether to checkout the new branch

        Raises:
            ValueError: If repository is not initialized
        """
        if self.repo is None:
            raise ValueError("Git repository not initialized")

        new_branch = self.repo.create_head(branch_name)
        if checkout:
            new_branch.checkout()

    @beartype
    @require(
        lambda branch_name: isinstance(branch_name, str) and len(branch_name) > 0,
        "Branch name must be non-empty string",
    )
    @require(lambda self: self.repo is not None, "Git repository must be initialized")
    def checkout(self, branch_name: str) -> None:
        """
        Checkout an existing branch.

        Args:
            branch_name: Name of the branch to checkout

        Raises:
            ValueError: If repository is not initialized
        """
        if self.repo is None:
            raise ValueError("Git repository not initialized")

        self.repo.heads[branch_name].checkout()

    @beartype
    @require(lambda files: isinstance(files, (list, Path, str)), "Files must be list, Path, or str")
    @require(lambda self: self.repo is not None, "Git repository must be initialized")
    def add(self, files: list[Path | str] | Path | str) -> None:
        """
        Add files to the staging area.

        Args:
            files: File(s) to add

        Raises:
            ValueError: If repository is not initialized
        """
        if self.repo is None:
            raise ValueError("Git repository not initialized")

        if isinstance(files, (Path, str)):
            files = [files]

        for file_path in files:
            self.repo.index.add([str(file_path)])

    @beartype
    @require(lambda message: isinstance(message, str) and len(message) > 0, "Commit message must be non-empty string")
    @require(lambda self: self.repo is not None, "Git repository must be initialized")
    @ensure(lambda result: result is not None, "Must return commit object")
    def commit(self, message: str) -> Any:
        """
        Commit staged changes.

        Args:
            message: Commit message

        Returns:
            Commit object

        Raises:
            ValueError: If repository is not initialized
        """
        if self.repo is None:
            raise ValueError("Git repository not initialized")

        return self.repo.index.commit(message)

    @beartype
    @require(lambda remote: isinstance(remote, str) and len(remote) > 0, "Remote name must be non-empty string")
    @require(
        lambda branch: branch is None or (isinstance(branch, str) and len(branch) > 0),
        "Branch name must be None or non-empty string",
    )
    @require(lambda self: self.repo is not None, "Git repository must be initialized")
    def push(self, remote: str = "origin", branch: str | None = None) -> None:
        """
        Push commits to remote repository.

        Args:
            remote: Remote name (default: origin)
            branch: Branch name (default: current branch)

        Raises:
            ValueError: If repository is not initialized
        """
        if self.repo is None:
            raise ValueError("Git repository not initialized")

        if branch is None:
            branch = self.repo.active_branch.name

        origin = self.repo.remote(name=remote)
        origin.push(branch)

    @beartype
    @require(lambda self: self.repo is not None, "Git repository must be initialized")
    @ensure(lambda result: isinstance(result, str) and len(result) > 0, "Must return non-empty branch name")
    def get_current_branch(self) -> str:
        """
        Get the name of the current branch.

        Returns:
            Current branch name

        Raises:
            ValueError: If repository is not initialized
        """
        if self.repo is None:
            raise ValueError("Git repository not initialized")

        return self.repo.active_branch.name

    @beartype
    @require(lambda self: self.repo is not None, "Git repository must be initialized")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    @ensure(lambda result: all(isinstance(b, str) for b in result), "All items must be strings")
    def list_branches(self) -> list[str]:
        """
        List all branches.

        Returns:
            List of branch names

        Raises:
            ValueError: If repository is not initialized
        """
        if self.repo is None:
            raise ValueError("Git repository not initialized")

        return [str(head) for head in self.repo.heads]

    @beartype
    @require(lambda self: self.repo is not None, "Git repository must be initialized")
    @ensure(lambda result: isinstance(result, bool), "Must return boolean")
    def is_clean(self) -> bool:
        """
        Check if the working directory is clean.

        Returns:
            True if working directory is clean

        Raises:
            ValueError: If repository is not initialized
        """
        if self.repo is None:
            raise ValueError("Git repository not initialized")

        return not self.repo.is_dirty()

    @beartype
    @require(lambda self: self.repo is not None, "Git repository must be initialized")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    @ensure(lambda result: all(isinstance(f, str) for f in result), "All items must be strings")
    def get_changed_files(self) -> list[str]:
        """
        Get list of changed files.

        Returns:
            List of changed file paths

        Raises:
            ValueError: If repository is not initialized
        """
        if self.repo is None:
            raise ValueError("Git repository not initialized")

        return [item.a_path for item in self.repo.index.diff(None) if item.a_path is not None]
