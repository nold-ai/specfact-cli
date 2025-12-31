"""
GitHub bridge adapter for DevOps backlog tracking.

This adapter implements the BridgeAdapter interface to sync OpenSpec change proposals
with GitHub Issues, enabling project planning alignment with specifications.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import requests
from beartype import beartype
from icontract import ensure, require
from rich.console import Console

from specfact_cli.adapters.base import BridgeAdapter
from specfact_cli.models.bridge import BridgeConfig
from specfact_cli.models.change import ChangeProposal, ChangeTracking


console = Console()


def _get_github_token_from_gh_cli() -> str | None:
    """
    Get GitHub token from GitHub CLI (`gh auth token`).

    Returns:
        GitHub token string if available, None otherwise

    Note:
        This is useful in enterprise environments where users might not be
        allowed to create Personal Access Tokens (PATs). The GitHub CLI uses
        OAuth authentication which is often more permissive.
    """
    # Check if gh CLI is available
    if not shutil.which("gh"):
        return None

    try:
        # Get token from gh CLI
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0 and result.stdout:
            token = result.stdout.strip()
            if token and len(token) > 10:  # Basic validation
                return token
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass

    return None


class GitHubAdapter(BridgeAdapter):
    """
    GitHub bridge adapter implementing BridgeAdapter interface.

    This adapter provides export-only sync (OpenSpec → GitHub Issues) for
    DevOps backlog tracking. It creates and updates GitHub issues from
    OpenSpec change proposals.
    """

    def __init__(
        self,
        repo_owner: str | None = None,
        repo_name: str | None = None,
        api_token: str | None = None,
        use_gh_cli: bool = True,
    ) -> None:
        """
        Initialize GitHub adapter.

        Args:
            repo_owner: GitHub repository owner (optional, can be auto-detected)
            repo_name: GitHub repository name (optional, can be auto-detected)
            api_token: GitHub API token (optional, uses GITHUB_TOKEN env var or gh CLI)
            use_gh_cli: If True, try to get token from GitHub CLI (`gh auth token`)
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name

        # Token resolution order: explicit token > env var > gh CLI (if enabled)
        if api_token:
            self.api_token = api_token
        elif os.environ.get("GITHUB_TOKEN"):
            self.api_token = os.environ.get("GITHUB_TOKEN")
        elif use_gh_cli:
            self.api_token = _get_github_token_from_gh_cli()
        else:
            self.api_token = None

        self.base_url = "https://api.github.com"

    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def detect(self, repo_path: Path, bridge_config: BridgeConfig | None = None) -> bool:
        """
        Detect if this is a GitHub repository.

        Args:
            repo_path: Path to repository root
            bridge_config: Optional bridge configuration (for cross-repo detection)

        Returns:
            True if GitHub repository detected, False otherwise
        """
        # Check for .git/config with GitHub remote
        git_config = repo_path / ".git" / "config"
        if git_config.exists():
            try:
                config_content = git_config.read_text(encoding="utf-8")
                if "github.com" in config_content.lower():
                    return True
            except Exception:
                pass

        # Check bridge config for external GitHub repo
        return bool(bridge_config and bridge_config.adapter.value == "github")

    @beartype
    @require(
        lambda artifact_key: isinstance(artifact_key, str) and len(artifact_key) > 0, "Artifact key must be non-empty"
    )
    @ensure(lambda result: result is None, "Must return None")
    def import_artifact(
        self,
        artifact_key: str,
        artifact_path: Path | dict[str, Any],
        project_bundle: Any,  # ProjectBundle - avoid circular import
        bridge_config: BridgeConfig | None = None,
    ) -> None:
        """
        Import artifact from GitHub (stub for future - not used in export-only mode).

        Args:
            artifact_key: Artifact key
            artifact_path: Path to artifact or API response dict
            project_bundle: Project bundle to update
            bridge_config: Bridge configuration
        """
        # Not implemented in export-only mode (Phase 1)
        # Future: Import GitHub issues → OpenSpec change proposals

    @beartype
    @require(
        lambda artifact_key: isinstance(artifact_key, str) and len(artifact_key) > 0, "Artifact key must be non-empty"
    )
    @ensure(lambda result: isinstance(result, dict), "Must return dict with issue data")
    def export_artifact(
        self,
        artifact_key: str,
        artifact_data: Any,  # ChangeProposal - TODO: use proper type when dependency implemented
        bridge_config: BridgeConfig | None = None,
    ) -> dict[str, Any]:
        """
        Export artifact to GitHub (create or update issue).

        Args:
            artifact_key: Artifact key ("change_proposal" or "change_status")
            artifact_data: Change proposal data (dict for now, ChangeProposal type when dependency implemented)
            bridge_config: Bridge configuration (may contain repo_owner, repo_name)

        Returns:
            Dict with issue data: {"issue_number": int, "issue_url": str, "state": str}

        Raises:
            ValueError: If required configuration is missing
            requests.RequestException: If GitHub API call fails
        """
        if not self.api_token:
            msg = (
                "GitHub API token required. Options:\n"
                "  1. Set GITHUB_TOKEN environment variable\n"
                "  2. Provide via --github-token option\n"
                "  3. Use GitHub CLI: `gh auth login` (auto-detected if available)\n"
                "  4. Use --use-gh-cli flag to explicitly use GitHub CLI token"
            )
            raise ValueError(msg)

        # Resolve repository owner/name from config or instance
        repo_owner = self.repo_owner or (bridge_config and getattr(bridge_config, "repo_owner", None))
        repo_name = self.repo_name or (bridge_config and getattr(bridge_config, "repo_name", None))

        if not repo_owner or not repo_name:
            msg = "GitHub repository owner and name required. Provide via --repo-owner and --repo-name or bridge config"
            raise ValueError(msg)

        if artifact_key == "change_proposal":
            return self._create_issue_from_proposal(artifact_data, repo_owner, repo_name)
        if artifact_key == "change_status":
            return self._update_issue_status(artifact_data, repo_owner, repo_name)
        if artifact_key == "change_proposal_update":
            # Extract issue number from source_tracking (support list or dict for backward compatibility)
            source_tracking = artifact_data.get("source_tracking", {})
            issue_number = None

            # Handle list of entries (multi-repository support)
            if isinstance(source_tracking, list):
                # Find entry for this repository
                target_repo = f"{repo_owner}/{repo_name}"
                for entry in source_tracking:
                    if isinstance(entry, dict):
                        entry_repo = entry.get("source_repo")
                        if entry_repo == target_repo:
                            issue_number = entry.get("source_id")
                            break
                        # Backward compatibility: if no source_repo, try to extract from source_url
                        if not entry_repo:
                            source_url = entry.get("source_url", "")
                            if source_url and target_repo in source_url:
                                issue_number = entry.get("source_id")
                                break
            # Handle single dict (backward compatibility)
            elif isinstance(source_tracking, dict):
                issue_number = source_tracking.get("source_id")

            if not issue_number:
                msg = "Issue number required for content update (missing in source_tracking for this repository)"
                raise ValueError(msg)
            return self._update_issue_body(artifact_data, repo_owner, repo_name, int(issue_number))
        if artifact_key == "code_change_progress":
            # Extract issue number from source_tracking (support list or dict for backward compatibility)
            source_tracking = artifact_data.get("source_tracking", {})
            issue_number = None

            # Handle list of entries (multi-repository support)
            if isinstance(source_tracking, list):
                # Find entry for this repository
                target_repo = f"{repo_owner}/{repo_name}"
                for entry in source_tracking:
                    if isinstance(entry, dict):
                        entry_repo = entry.get("source_repo")
                        if entry_repo == target_repo:
                            issue_number = entry.get("source_id")
                            break
                        # Backward compatibility: if no source_repo, try to extract from source_url
                        if not entry_repo:
                            source_url = entry.get("source_url", "")
                            if source_url and target_repo in source_url:
                                issue_number = entry.get("source_id")
                                break
            # Handle single dict (backward compatibility)
            elif isinstance(source_tracking, dict):
                issue_number = source_tracking.get("source_id")

            if not issue_number:
                msg = "Issue number required for progress comment (missing in source_tracking for this repository)"
                raise ValueError(msg)

            # Extract sanitize flag from artifact_data or bridge_config
            sanitize = artifact_data.get("sanitize", False)
            if bridge_config and hasattr(bridge_config, "sanitize"):
                sanitize = bridge_config.sanitize if bridge_config.sanitize is not None else sanitize

            return self._add_progress_comment(
                artifact_data, repo_owner, repo_name, int(issue_number), sanitize=sanitize
            )
        msg = f"Unsupported artifact key: {artifact_key}. Supported: change_proposal, change_status, change_proposal_update, code_change_progress"
        raise ValueError(msg)

    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    @ensure(lambda result: isinstance(result, BridgeConfig), "Must return BridgeConfig")
    def generate_bridge_config(self, repo_path: Path) -> BridgeConfig:
        """
        Generate bridge configuration for GitHub adapter.

        Args:
            repo_path: Path to repository root

        Returns:
            BridgeConfig instance for GitHub adapter
        """
        from specfact_cli.models.bridge import BridgeConfig

        return BridgeConfig.preset_github()

    @beartype
    @require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
    @require(lambda bundle_dir: bundle_dir.exists(), "Bundle directory must exist")
    @ensure(lambda result: result is None, "GitHub adapter does not support change tracking loading")
    def load_change_tracking(
        self, bundle_dir: Path, bridge_config: BridgeConfig | None = None
    ) -> ChangeTracking | None:
        """
        Load change tracking (not supported by GitHub adapter).

        GitHub adapter is export-only (OpenSpec → GitHub Issues) and does not
        support loading change tracking from GitHub.

        Args:
            bundle_dir: Path to bundle directory
            bridge_config: Optional bridge configuration

        Returns:
            None (not supported)
        """
        return None

    @beartype
    @require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
    @require(lambda bundle_dir: bundle_dir.exists(), "Bundle directory must exist")
    @require(
        lambda change_tracking: isinstance(change_tracking, ChangeTracking), "Change tracking must be ChangeTracking"
    )
    @ensure(lambda result: result is None, "Must return None")
    def save_change_tracking(
        self, bundle_dir: Path, change_tracking: ChangeTracking, bridge_config: BridgeConfig | None = None
    ) -> None:
        """
        Save change tracking (not supported by GitHub adapter).

        GitHub adapter is export-only (OpenSpec → GitHub Issues) and does not
        support saving change tracking to GitHub.

        Args:
            bundle_dir: Path to bundle directory
            change_tracking: ChangeTracking instance to save
            bridge_config: Optional bridge configuration
        """
        # Not supported - GitHub adapter is export-only

    @beartype
    @require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
    @require(lambda bundle_dir: bundle_dir.exists(), "Bundle directory must exist")
    @require(lambda change_name: isinstance(change_name, str) and len(change_name) > 0, "Change name must be non-empty")
    @ensure(lambda result: result is None, "GitHub adapter does not support change proposal loading")
    def load_change_proposal(
        self, bundle_dir: Path, change_name: str, bridge_config: BridgeConfig | None = None
    ) -> ChangeProposal | None:
        """
        Load change proposal (not supported by GitHub adapter).

        GitHub adapter is export-only (OpenSpec → GitHub Issues) and does not
        support loading change proposals from GitHub.

        Args:
            bundle_dir: Path to bundle directory
            change_name: Change identifier
            bridge_config: Optional bridge configuration

        Returns:
            None (not supported)
        """
        return None

    @beartype
    @require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
    @require(lambda bundle_dir: bundle_dir.exists(), "Bundle directory must exist")
    @require(lambda proposal: isinstance(proposal, ChangeProposal), "Proposal must be ChangeProposal")
    @ensure(lambda result: result is None, "Must return None")
    def save_change_proposal(
        self, bundle_dir: Path, proposal: ChangeProposal, bridge_config: BridgeConfig | None = None
    ) -> None:
        """
        Save change proposal (not supported by GitHub adapter).

        GitHub adapter is export-only (OpenSpec → GitHub Issues) and does not
        support saving change proposals to GitHub. Use `export_artifact` with
        artifact_key="change_proposal" to create GitHub issues instead.

        Args:
            bundle_dir: Path to bundle directory
            proposal: ChangeProposal instance to save
            bridge_config: Optional bridge configuration
        """
        # Not supported - GitHub adapter is export-only
        # Use export_artifact(artifact_key="change_proposal", ...) to create GitHub issues

    def _create_issue_from_proposal(
        self,
        proposal_data: dict[str, Any],  # ChangeProposal - TODO: use proper type
        repo_owner: str,
        repo_name: str,
    ) -> dict[str, Any]:
        """
        Create GitHub issue from change proposal.

        Args:
            proposal_data: Change proposal data (dict with title, description, rationale, status, etc.)
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name

        Returns:
            Dict with issue data: {"issue_number": int, "issue_url": str, "state": str}
        """
        title = proposal_data.get("title", "Untitled Change Proposal")
        description = proposal_data.get("description", "")
        rationale = proposal_data.get("rationale", "")
        status = proposal_data.get("status", "proposed")
        change_id = proposal_data.get("change_id", "unknown")

        # Build properly formatted issue body
        body_parts = []

        # Add Why section (rationale) - preserve markdown formatting
        if rationale:
            body_parts.append("## Why")
            body_parts.append("")
            # Preserve markdown formatting from rationale
            rationale_lines = rationale.strip().split("\n")
            for line in rationale_lines:
                body_parts.append(line)
            body_parts.append("")  # Blank line

        # Add What Changes section (description) - preserve markdown formatting
        if description:
            body_parts.append("## What Changes")
            body_parts.append("")
            # Preserve markdown formatting from description
            description_lines = description.strip().split("\n")
            for line in description_lines:
                body_parts.append(line)
            body_parts.append("")  # Blank line

        # If no content, add placeholder
        if not body_parts or (not rationale and not description):
            body_parts.append("No description provided.")
            body_parts.append("")

        # Add OpenSpec metadata footer
        body_parts.append("---")
        body_parts.append(f"*OpenSpec Change Proposal: `{change_id}`*")

        body = "\n".join(body_parts)

        # Create issue via GitHub API
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/issues"
        headers = {
            "Authorization": f"token {self.api_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        payload = {
            "title": title,
            "body": body,
            "labels": self._get_labels_for_status(status),
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            issue_data = response.json()

            return {
                "issue_number": issue_data["number"],
                "issue_url": issue_data["html_url"],
                "state": issue_data["state"],
            }
        except requests.RequestException as e:
            msg = f"Failed to create GitHub issue: {e}"
            console.print(f"[bold red]✗[/bold red] {msg}")
            raise

    def _update_issue_status(
        self,
        proposal_data: dict[str, Any],  # ChangeProposal with source_tracking
        repo_owner: str,
        repo_name: str,
    ) -> dict[str, Any]:
        """
        Update GitHub issue status based on change proposal status.

        Args:
            proposal_data: Change proposal data with source_tracking (list or dict) containing issue number
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name

        Returns:
            Dict with updated issue data: {"issue_number": int, "issue_url": str, "state": str}
        """
        # Get issue number from source_tracking (handle both dict and list formats)
        source_tracking = proposal_data.get("source_tracking", {})

        # Normalize to find the entry for this repository
        target_repo = f"{repo_owner}/{repo_name}"
        issue_number = None

        if isinstance(source_tracking, dict):
            # Single dict entry (backward compatibility)
            issue_number = source_tracking.get("source_id")
        elif isinstance(source_tracking, list):
            # List of entries - find the one matching this repository
            for entry in source_tracking:
                if isinstance(entry, dict):
                    entry_repo = entry.get("source_repo")
                    if entry_repo == target_repo:
                        issue_number = entry.get("source_id")
                        break
                    # Backward compatibility: if no source_repo, try to extract from source_url
                    if not entry_repo:
                        source_url = entry.get("source_url", "")
                        if source_url and target_repo in source_url:
                            issue_number = entry.get("source_id")
                            break

        if not issue_number:
            msg = (
                f"Issue number not found in source_tracking for repository {target_repo}. Issue must be created first."
            )
            raise ValueError(msg)

        status = proposal_data.get("status", "proposed")
        title = proposal_data.get("title", "Untitled")

        # Map status to GitHub issue state and comment
        should_close = status in ("applied", "deprecated", "discarded")
        comment_text = self._get_status_comment(status, title)

        # Update issue state
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/issues/{issue_number}"
        headers = {
            "Authorization": f"token {self.api_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        payload = {"state": "closed" if should_close else "open"}

        try:
            response = requests.patch(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            issue_data = response.json()

            # Add comment explaining status change
            if comment_text:
                self._add_issue_comment(repo_owner, repo_name, issue_number, comment_text)

            return {
                "issue_number": issue_data["number"],
                "issue_url": issue_data["html_url"],
                "state": issue_data["state"],
            }
        except requests.RequestException as e:
            msg = f"Failed to update GitHub issue #{issue_number}: {e}"
            console.print(f"[bold red]✗[/bold red] {msg}")
            raise

    def _add_issue_comment(self, repo_owner: str, repo_name: str, issue_number: int, comment: str) -> None:
        """
        Add comment to GitHub issue.

        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            issue_number: Issue number
            comment: Comment text
        """
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/issues/{issue_number}/comments"
        headers = {
            "Authorization": f"token {self.api_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        payload = {"body": comment}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            # Log but don't fail - comment is non-critical
            console.print(f"[yellow]⚠[/yellow] Failed to add comment to issue #{issue_number}: {e}")

    def _update_issue_body(
        self,
        proposal_data: dict[str, Any],  # ChangeProposal - TODO: use proper type when dependency implemented
        repo_owner: str,
        repo_name: str,
        issue_number: int,
    ) -> dict[str, Any]:
        """
        Update GitHub issue body with new proposal content.

        Args:
            proposal_data: Change proposal data (dict with title, description, rationale, status, etc.)
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            issue_number: GitHub issue number

        Returns:
            Dict with updated issue data: {"issue_number": int, "issue_url": str, "state": str}

        Raises:
            requests.RequestException: If GitHub API call fails
        """
        title = proposal_data.get("title", "Untitled Change Proposal")
        description = proposal_data.get("description", "")
        rationale = proposal_data.get("rationale", "")
        change_id = proposal_data.get("change_id", "unknown")

        # Build properly formatted issue body (same format as _create_issue_from_proposal)
        body_parts = []

        # Add Why section (rationale) - preserve markdown formatting
        if rationale:
            body_parts.append("## Why")
            body_parts.append("")
            rationale_lines = rationale.strip().split("\n")
            for line in rationale_lines:
                body_parts.append(line)
            body_parts.append("")  # Blank line

        # Add What Changes section (description) - preserve markdown formatting
        if description:
            body_parts.append("## What Changes")
            body_parts.append("")
            description_lines = description.strip().split("\n")
            for line in description_lines:
                body_parts.append(line)
            body_parts.append("")  # Blank line

        # If no content, add placeholder
        if not body_parts or (not rationale and not description):
            body_parts.append("No description provided.")
            body_parts.append("")

        # Add OpenSpec metadata footer
        body_parts.append("---")
        body_parts.append(f"*OpenSpec Change Proposal: `{change_id}`*")

        body = "\n".join(body_parts)

        # Update issue body via GitHub API PATCH
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/issues/{issue_number}"
        headers = {
            "Authorization": f"token {self.api_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        payload = {
            "body": body,
            # Preserve title and other metadata (only update body)
        }

        try:
            response = requests.patch(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            issue_data = response.json()

            # Optionally add comment for significant changes
            title_lower = title.lower()
            description_lower = description.lower()
            rationale_lower = rationale.lower()
            combined_text = f"{title_lower} {description_lower} {rationale_lower}"

            significant_keywords = ["breaking", "major", "scope change"]
            is_significant = any(keyword in combined_text for keyword in significant_keywords)

            if is_significant:
                comment_text = (
                    f"**Significant change detected**: This issue has been updated with new proposal content.\n\n"
                    f"*Updated: {change_id}*\n\n"
                    f"Please review the changes above. This update may include breaking changes or major scope modifications."
                )
                self._add_issue_comment(repo_owner, repo_name, issue_number, comment_text)

            return {
                "issue_number": issue_data["number"],
                "issue_url": issue_data["html_url"],
                "state": issue_data["state"],
            }
        except requests.RequestException as e:
            msg = f"Failed to update GitHub issue #{issue_number} body: {e}"
            console.print(f"[bold red]✗[/bold red] {msg}")
            raise

    def _get_labels_for_status(self, status: str) -> list[str]:
        """
        Get GitHub labels for change proposal status.

        Args:
            status: Change proposal status (proposed, in-progress, applied, deprecated, discarded)

        Returns:
            List of label names
        """
        labels = ["openspec"]
        if status == "in-progress":
            labels.append("in-progress")
        elif status == "applied":
            labels.append("completed")
        elif status == "deprecated":
            labels.append("deprecated")
        elif status == "discarded":
            labels.append("wontfix")
        return labels

    def _get_status_comment(self, status: str, title: str) -> str:
        """
        Get comment text for status change.

        Args:
            status: Change proposal status
            title: Change proposal title

        Returns:
            Comment text or empty string if no comment needed
        """
        if status == "applied":
            return f"✅ Change applied: {title}\n\nThis change proposal has been implemented and applied."
        if status == "deprecated":
            return (
                f"⚠️ Change deprecated: {title}\n\nThis change proposal has been deprecated and will not be implemented."
            )
        if status == "discarded":
            return f"❌ Change discarded: {title}\n\nThis change proposal has been discarded."
        if status == "in-progress":
            return f"🔄 Change in progress: {title}\n\nImplementation of this change proposal has started."
        return ""

    def _add_progress_comment(
        self,
        proposal_data: dict[str, Any],  # ChangeProposal with progress_data
        repo_owner: str,
        repo_name: str,
        issue_number: int,
        sanitize: bool = False,
    ) -> dict[str, Any]:
        """
        Add progress comment to GitHub issue based on code changes.

        Args:
            proposal_data: Change proposal data with progress_data (dict with code change info)
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            issue_number: GitHub issue number
            sanitize: If True, sanitize sensitive information in progress comment (for public repos)

        Returns:
            Dict with updated issue data: {"issue_number": int, "issue_url": str, "comment_added": bool}

        Raises:
            requests.RequestException: If GitHub API call fails
        """
        progress_data = proposal_data.get("progress_data", {})
        if not progress_data:
            # No progress data provided
            return {
                "issue_number": issue_number,
                "issue_url": f"https://github.com/{repo_owner}/{repo_name}/issues/{issue_number}",
                "comment_added": False,
            }

        from specfact_cli.utils.code_change_detector import format_progress_comment

        comment_text = format_progress_comment(progress_data, sanitize=sanitize)

        try:
            self._add_issue_comment(repo_owner, repo_name, issue_number, comment_text)
            return {
                "issue_number": issue_number,
                "issue_url": f"https://github.com/{repo_owner}/{repo_name}/issues/{issue_number}",
                "comment_added": True,
            }
        except requests.RequestException as e:
            msg = f"Failed to add progress comment to GitHub issue #{issue_number}: {e}"
            console.print(f"[bold red]✗[/bold red] {msg}")
            raise
