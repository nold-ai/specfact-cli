"""
GitHub bridge adapter for DevOps backlog tracking.

This adapter implements the BridgeAdapter interface to sync OpenSpec change proposals
with GitHub Issues, enabling bidirectional sync (OpenSpec ↔ GitHub Issues) for
project planning alignment with specifications.

This is the first backlog adapter implementation. The architecture is designed
to be extensible for future backlog adapters (Azure DevOps, Jira, Linear, etc.)
following the same patterns.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
from beartype import beartype
from icontract import ensure, require
from rich.console import Console

from specfact_cli.adapters.backlog_base import BacklogAdapterMixin
from specfact_cli.adapters.base import BridgeAdapter
from specfact_cli.models.bridge import BridgeConfig
from specfact_cli.models.capabilities import ToolCapabilities
from specfact_cli.models.change import ChangeProposal, ChangeTracking
from specfact_cli.utils.auth_tokens import get_token


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


class GitHubAdapter(BridgeAdapter, BacklogAdapterMixin):
    """
    GitHub bridge adapter implementing BridgeAdapter interface.

    This adapter provides bidirectional sync (OpenSpec ↔ GitHub Issues) for
    DevOps backlog tracking. It creates and updates GitHub issues from
    OpenSpec change proposals, and imports GitHub issues as OpenSpec change proposals.

    This is the first backlog adapter implementation. Future backlog adapters
    (Azure DevOps, Jira, Linear, etc.) should follow the same patterns defined
    in BacklogAdapterMixin.
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
            api_token: GitHub API token (optional, uses GITHUB_TOKEN env var, stored auth token, or gh CLI)
            use_gh_cli: If True, try to get token from GitHub CLI (`gh auth token`)
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name

        stored_token = get_token("github")

        # Token resolution order: explicit token > env var > stored token > gh CLI (if enabled)
        if api_token:
            self.api_token = api_token
        elif os.environ.get("GITHUB_TOKEN"):
            self.api_token = os.environ.get("GITHUB_TOKEN")
        elif stored_token:
            self.api_token = stored_token.get("access_token")
        elif use_gh_cli:
            self.api_token = _get_github_token_from_gh_cli()
        else:
            self.api_token = None

        env_api_url = os.environ.get("GITHUB_API_URL")
        stored_api_url = stored_token.get("api_base_url") if stored_token else None
        self.base_url = stored_api_url or env_api_url or "https://api.github.com"

    # BacklogAdapterMixin abstract method implementations

    @beartype
    @require(lambda status: isinstance(status, str) and len(status) > 0, "Status must be non-empty string")
    @ensure(lambda result: isinstance(result, str) and len(result) > 0, "Must return non-empty status string")
    def map_backlog_status_to_openspec(self, status: str) -> str:
        """
        Map GitHub issue labels/state to OpenSpec change status.

        Args:
            status: GitHub issue label or state (e.g., "enhancement", "in-progress", "closed")

        Returns:
            OpenSpec change status (proposed, in-progress, applied, deprecated, discarded)

        Note:
            This implements the tool-agnostic status mapping pattern for GitHub.
            Future backlog adapters should implement similar mappings for their tools.
        """
        status_lower = status.lower()

        # Map GitHub labels to OpenSpec status
        if status_lower in ("enhancement", "new", "todo", "open"):
            return "proposed"
        if status_lower in ("in-progress", "in progress", "active", "in development"):
            return "in-progress"
        if status_lower in ("done", "completed", "closed", "resolved"):
            return "applied"
        if status_lower in ("deprecated", "wontfix"):
            return "deprecated"
        if status_lower in ("discarded", "rejected"):
            return "discarded"

        # Default: treat as proposed
        return "proposed"

    @beartype
    @require(lambda status: isinstance(status, str) and len(status) > 0, "Status must be non-empty string")
    @ensure(lambda result: isinstance(result, list), "Must return list of label strings")
    def map_openspec_status_to_backlog(self, status: str) -> list[str]:
        """
        Map OpenSpec change status to GitHub issue labels.

        Args:
            status: OpenSpec change status (proposed, in-progress, applied, deprecated, discarded)

        Returns:
            List of GitHub label names

        Note:
            This implements the tool-agnostic status mapping pattern for GitHub.
            Future backlog adapters should implement similar mappings for their tools.
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

    @beartype
    @require(lambda item_data: isinstance(item_data, dict), "Item data must be dict")
    @ensure(lambda result: isinstance(result, dict), "Must return dict with extracted fields")
    def extract_change_proposal_data(self, item_data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract change proposal data from GitHub issue.

        Parses GitHub issue body/markdown to extract:
        - Title (from issue title)
        - Description (What Changes section)
        - Rationale (Why section)
        - Other optional fields (timeline, owner, stakeholders, dependencies)

        Args:
            item_data: GitHub issue data (dict from API response)

        Returns:
            Dict with change proposal fields:
            - title: str
            - description: str (What Changes section)
            - rationale: str (Why section)
            - status: str (mapped to OpenSpec status)
            - Other optional fields

        Raises:
            ValueError: If required fields are missing or data is malformed

        Note:
            This implements the tool-agnostic metadata extraction pattern for GitHub.
            Future backlog adapters should implement similar parsing for their tools.
        """
        if not isinstance(item_data, dict):
            msg = "GitHub issue data must be dict"
            raise ValueError(msg)

        # Extract title
        title = item_data.get("title", "Untitled Change Proposal")
        if not title:
            msg = "GitHub issue must have a title"
            raise ValueError(msg)

        # Extract body and parse markdown sections
        body = item_data.get("body", "") or ""
        description = ""
        rationale = ""
        impact = ""

        # Parse markdown sections (Why, What Changes)
        if body:
            # Extract "Why" section (stop at What Changes or OpenSpec footer)
            why_match = re.search(
                r"##\s+Why\s*\n(.*?)(?=\n##\s+What\s+Changes\s|\n##\s+Impact\s|\n---\s*\n\*OpenSpec Change Proposal:|\Z)",
                body,
                re.DOTALL | re.IGNORECASE,
            )
            if why_match:
                rationale = why_match.group(1).strip()

            # Extract "What Changes" section (stop at OpenSpec footer)
            what_match = re.search(
                r"##\s+What\s+Changes\s*\n(.*?)(?=\n##\s+Impact\s|\n---\s*\n\*OpenSpec Change Proposal:|\Z)",
                body,
                re.DOTALL | re.IGNORECASE,
            )
            if what_match:
                description = what_match.group(1).strip()
            elif not why_match:
                # If no sections found, use entire body as description (but remove footer)
                body_clean = re.sub(r"\n---\s*\n\*OpenSpec Change Proposal:.*", "", body, flags=re.DOTALL)
                description = body_clean.strip()

            impact_match = re.search(
                r"##\s+Impact\s*\n(.*?)(?=\n---\s*\n\*OpenSpec Change Proposal:|\Z)",
                body,
                re.DOTALL | re.IGNORECASE,
            )
            if impact_match:
                impact = impact_match.group(1).strip()

        # Extract change ID from OpenSpec metadata footer or issue number
        change_id = None
        if body:
            # Look for OpenSpec metadata footer: *OpenSpec Change Proposal: `{change_id}`*
            change_id_match = re.search(r"OpenSpec Change Proposal:\s*`([^`]+)`", body, re.IGNORECASE)
            if change_id_match:
                change_id = change_id_match.group(1)
        if not change_id:
            # Use issue number as fallback
            change_id = str(item_data.get("number", "unknown"))

        # Extract status from labels
        labels = item_data.get("labels", [])
        status = "proposed"  # Default
        if labels:
            # Find status label
            label_names = [label.get("name", "") if isinstance(label, dict) else str(label) for label in labels]
            for label_name in label_names:
                mapped_status = self.map_backlog_status_to_openspec(label_name)
                if mapped_status != "proposed":  # Use first non-default status
                    status = mapped_status
                    break

        # Extract created_at timestamp
        created_at = item_data.get("created_at")
        if created_at:
            # Parse ISO format and convert to ISO string
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                created_at = dt.isoformat()
            except (ValueError, AttributeError):
                created_at = datetime.now(UTC).isoformat()
        else:
            created_at = datetime.now(UTC).isoformat()

        # Extract optional fields (timeline, owner, stakeholders, dependencies)
        # These can be parsed from issue body or extracted from issue metadata
        timeline = None
        owner = None
        stakeholders = []
        dependencies = []

        # Try to extract from body sections
        if body:
            # Extract "When" section (timeline)
            when_match = re.search(r"##\s+When\s*\n(.*?)(?=\n##\s|\Z)", body, re.DOTALL | re.IGNORECASE)
            if when_match:
                timeline = when_match.group(1).strip()

            # Extract "Who" section (owner, stakeholders)
            who_match = re.search(r"##\s+Who\s*\n(.*?)(?=\n##\s|\Z)", body, re.DOTALL | re.IGNORECASE)
            if who_match:
                who_content = who_match.group(1).strip()
                # Try to extract owner (first line or "Owner:" field)
                owner_match = re.search(r"(?:Owner|owner):\s*(.+)", who_content, re.IGNORECASE)
                if owner_match:
                    owner = owner_match.group(1).strip()
                # Extract stakeholders (list items or comma-separated)
                stakeholders_match = re.search(r"(?:Stakeholders|stakeholders):\s*(.+)", who_content, re.IGNORECASE)
                if stakeholders_match:
                    stakeholders_str = stakeholders_match.group(1).strip()
                    stakeholders = [s.strip() for s in re.split(r"[,\n]", stakeholders_str) if s.strip()]

        # Extract assignees as potential owner/stakeholders
        assignees = item_data.get("assignees", [])
        if assignees and not owner:
            # Use first assignee as owner
            owner = assignees[0].get("login", "") if isinstance(assignees[0], dict) else str(assignees[0])
        if assignees:
            # Add assignees to stakeholders
            assignee_logins = [
                assignee.get("login", "") if isinstance(assignee, dict) else str(assignee) for assignee in assignees
            ]
            stakeholders.extend(assignee_logins)

        return {
            "change_id": change_id,
            "title": title,
            "description": description,
            "rationale": rationale,
            "impact": impact,
            "status": status,
            "created_at": created_at,
            "timeline": timeline,
            "owner": owner,
            "stakeholders": list(set(stakeholders)),  # Remove duplicates
            "dependencies": dependencies,
        }

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
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    @ensure(lambda result: isinstance(result, ToolCapabilities), "Must return ToolCapabilities")
    def get_capabilities(self, repo_path: Path, bridge_config: BridgeConfig | None = None) -> ToolCapabilities:
        """
        Get GitHub adapter capabilities.

        Args:
            repo_path: Path to repository root
            bridge_config: Optional bridge configuration (for cross-repo detection)

        Returns:
            ToolCapabilities instance for GitHub adapter
        """
        return ToolCapabilities(
            tool="github",
            version=None,  # GitHub version not applicable
            layout="api",  # GitHub uses API-based integration
            specs_dir="",  # Not applicable for GitHub
            has_external_config=True,  # Uses API tokens
            has_custom_hooks=False,
            supported_sync_modes=[
                "bidirectional",
                "export-only",
            ],  # GitHub adapter: bidirectional sync (OpenSpec ↔ GitHub Issues) and export-only for change proposals
        )

    @beartype
    @require(
        lambda artifact_key: isinstance(artifact_key, str) and len(artifact_key) > 0, "Artifact key must be non-empty"
    )
    @require(lambda artifact_path: isinstance(artifact_path, (Path, dict)), "Artifact path must be Path or dict")
    @ensure(lambda result: result is None, "Must return None")
    def import_artifact(
        self,
        artifact_key: str,
        artifact_path: Path | dict[str, Any],
        project_bundle: Any,  # ProjectBundle - avoid circular import
        bridge_config: BridgeConfig | None = None,
    ) -> None:
        """
        Import artifact from GitHub.

        Supports importing GitHub issues as OpenSpec change proposals.

        Args:
            artifact_key: Artifact key ("github_issue" for importing issues)
            artifact_path: GitHub issue data (dict from API response)
            project_bundle: Project bundle to update
            bridge_config: Bridge configuration (may contain external_base_path for cross-repo support)

        Raises:
            ValueError: If artifact_key is not "github_issue" or if required data is missing
            NotImplementedError: If artifact_key is not supported

        Note:
            This method implements the backlog adapter import pattern. Future backlog
            adapters (ADO, Jira, Linear) should follow the same pattern with their
            respective artifact keys (e.g., "ado_work_item", "jira_issue", "linear_issue").
        """
        if artifact_key != "github_issue":
            msg = f"Unsupported artifact key for import: {artifact_key}. Supported: github_issue"
            raise NotImplementedError(msg)

        if not isinstance(artifact_path, dict):
            msg = "GitHub issue import requires dict (API response), not Path"
            raise ValueError(msg)

        # Check bridge_config.external_base_path for cross-repo support
        if bridge_config and bridge_config.external_base_path:
            # Cross-repo import: use external_base_path for OpenSpec repository
            pass  # Path operations will respect external_base_path in OpenSpec adapter

        # Import GitHub issue as change proposal using backlog adapter pattern
        proposal = self.import_backlog_item_as_proposal(artifact_path, "github", bridge_config)

        if not proposal:
            msg = "Failed to import GitHub issue as change proposal"
            raise ValueError(msg)

        # Persist lossless issue content and backlog metadata for round-trip sync
        if proposal.source_tracking and isinstance(proposal.source_tracking.source_metadata, dict):
            source_metadata = proposal.source_tracking.source_metadata
            raw_title = artifact_path.get("title") or ""
            raw_body = artifact_path.get("body") or ""
            source_metadata["raw_title"] = raw_title
            source_metadata["raw_body"] = raw_body
            source_metadata["raw_format"] = "markdown"
            source_metadata.setdefault("source_type", "github")

            source_repo = self._extract_repo_from_issue(artifact_path)
            if source_repo:
                source_metadata.setdefault("source_repo", source_repo)

            entry_id = artifact_path.get("number") or artifact_path.get("id")
            entry = {
                "source_id": str(entry_id) if entry_id is not None else None,
                "source_url": artifact_path.get("html_url") or artifact_path.get("url") or "",
                "source_type": "github",
                "source_repo": source_repo or "",
                "source_metadata": {"last_synced_status": proposal.status},
            }
            entries = source_metadata.get("backlog_entries")
            if not isinstance(entries, list):
                entries = []
            if entry.get("source_id"):
                updated = False
                for existing in entries:
                    if not isinstance(existing, dict):
                        continue
                    if source_repo and existing.get("source_repo") == source_repo:
                        existing.update(entry)
                        updated = True
                        break
                    if not source_repo and existing.get("source_id") == entry.get("source_id"):
                        existing.update(entry)
                        updated = True
                        break
                if not updated:
                    entries.append(entry)
                source_metadata["backlog_entries"] = entries

        # Add proposal to project bundle change tracking
        if hasattr(project_bundle, "change_tracking"):
            if not project_bundle.change_tracking:
                from specfact_cli.models.change import ChangeTracking

                project_bundle.change_tracking = ChangeTracking()
            project_bundle.change_tracking.proposals[proposal.name] = proposal

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
                "  4. Use --use-gh-cli flag to explicitly use GitHub CLI token\n"
                "  5. Run `specfact auth github` for device code authentication"
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
            # Get code repository path for branch verification
            code_repo_path_str = artifact_data.get("_code_repo_path")
            code_repo_path = Path(code_repo_path_str) if code_repo_path_str else None
            return self._update_issue_body(artifact_data, repo_owner, repo_name, int(issue_number), code_repo_path)
        if artifact_key == "change_proposal_comment":
            # Add comment only (no body/state update) - used for adding branch info to already-closed issues
            source_tracking = artifact_data.get("source_tracking", {})
            issue_number = None

            # Handle list of entries (multi-repository support)
            if isinstance(source_tracking, list):
                target_repo = f"{repo_owner}/{repo_name}"
                for entry in source_tracking:
                    if isinstance(entry, dict):
                        entry_repo = entry.get("source_repo")
                        if entry_repo == target_repo:
                            issue_number = entry.get("source_id")
                            break
                        if not entry_repo:
                            source_url = entry.get("source_url", "")
                            if source_url and target_repo in source_url:
                                issue_number = entry.get("source_id")
                                break
            elif isinstance(source_tracking, dict):
                issue_number = source_tracking.get("source_id")

            if not issue_number:
                msg = "Issue number required for comment (missing in source_tracking for this repository)"
                raise ValueError(msg)

            status = artifact_data.get("status", "proposed")
            title = artifact_data.get("title", "Untitled Change Proposal")
            change_id = artifact_data.get("change_id", "")
            # Get OpenSpec repository path for branch verification
            code_repo_path_str = artifact_data.get("_code_repo_path")
            code_repo_path = Path(code_repo_path_str) if code_repo_path_str else None

            # Add change_id to source_tracking entries for branch inference
            # Create a copy to avoid modifying the original
            if isinstance(source_tracking, list):
                source_tracking_with_id = []
                for entry in source_tracking:
                    entry_copy = dict(entry) if isinstance(entry, dict) else entry
                    if isinstance(entry_copy, dict) and not entry_copy.get("change_id"):
                        entry_copy["change_id"] = change_id
                    source_tracking_with_id.append(entry_copy)
            elif isinstance(source_tracking, dict):
                source_tracking_with_id = dict(source_tracking)
                if not source_tracking_with_id.get("change_id"):
                    source_tracking_with_id["change_id"] = change_id
            else:
                source_tracking_with_id = source_tracking
            comment_text = self._get_status_comment(status, title, source_tracking_with_id, code_repo_path)
            if comment_text:
                comment_note = (
                    f"{comment_text}\n\n"
                    f"*Note: This comment was added from an OpenSpec change proposal with status `{status}`.*"
                )
                self._add_issue_comment(repo_owner, repo_name, int(issue_number), comment_note)
            return {
                "issue_number": int(issue_number),
                "comment_added": True,
            }
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
    @require(lambda item_ref: isinstance(item_ref, str) and len(item_ref) > 0, "Item reference must be non-empty")
    @ensure(lambda result: isinstance(result, dict), "Must return dict with issue data")
    def fetch_backlog_item(self, item_ref: str) -> dict[str, Any]:
        """
        Fetch GitHub issue data by ID or URL.

        Args:
            item_ref: Issue number, owner/repo#number, or issue URL

        Returns:
            Issue data dict from GitHub API
        """
        if not self.api_token:
            msg = "GitHub API token required to fetch backlog items"
            raise ValueError(msg)

        repo_owner, repo_name, issue_number = self._parse_issue_reference(item_ref)
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/issues/{issue_number}"
        headers = {
            "Authorization": f"token {self.api_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def _extract_repo_from_issue(self, issue_data: dict[str, Any]) -> str | None:
        """
        Extract repository identifier (owner/repo) from GitHub issue data.

        Args:
            issue_data: GitHub issue data dict

        Returns:
            Repository identifier string or None if not found
        """
        candidates = [
            issue_data.get("repository_url"),
            issue_data.get("html_url"),
            issue_data.get("url"),
        ]
        for url in candidates:
            if not url:
                continue
            match = re.search(r"github\.com/(?:repos/)?([^/]+)/([^/]+)", url)
            if match:
                return f"{match.group(1)}/{match.group(2)}"
        if self.repo_owner and self.repo_name:
            return f"{self.repo_owner}/{self.repo_name}"
        return None

    @beartype
    @require(lambda item_ref: isinstance(item_ref, str) and len(item_ref) > 0, "Item reference must be non-empty")
    @ensure(lambda result: isinstance(result, tuple) and len(result) == 3, "Must return owner, repo, issue number")
    def _parse_issue_reference(self, item_ref: str) -> tuple[str, str, int]:
        """
        Parse issue reference into owner, repo, and issue number.

        Args:
            item_ref: Issue number, owner/repo#number, or URL

        Returns:
            Tuple of (owner, repo, issue_number)
        """
        cleaned = item_ref.strip().lstrip("#")
        url_match = re.search(
            r"github\.com/(?:repos/)?([^/]+)/([^/]+)/issues/(\d+)",
            cleaned,
            re.IGNORECASE,
        )
        if url_match:
            return url_match.group(1), url_match.group(2), int(url_match.group(3))

        shorthand_match = re.search(r"([^/\s]+)/([^#\s]+)#(\d+)", cleaned)
        if shorthand_match:
            return shorthand_match.group(1), shorthand_match.group(2), int(shorthand_match.group(3))

        if cleaned.isdigit():
            if not self.repo_owner or not self.repo_name:
                msg = "repo_owner and repo_name required when issue reference is numeric"
                raise ValueError(msg)
            return self.repo_owner, self.repo_name, int(cleaned)

        msg = f"Unsupported GitHub issue reference format: {item_ref}"
        raise ValueError(msg)

    def _extract_raw_fields(self, proposal_data: dict[str, Any]) -> tuple[str | None, str | None]:
        """
        Extract lossless title/body content from proposal data.

        Args:
            proposal_data: Change proposal data dict

        Returns:
            Tuple of (raw_title, raw_body)
        """
        raw_title = proposal_data.get("raw_title")
        raw_body = proposal_data.get("raw_body")
        if raw_title and raw_body:
            return raw_title, raw_body

        source_tracking = proposal_data.get("source_tracking")
        source_metadata = None
        if isinstance(source_tracking, dict):
            source_metadata = source_tracking.get("source_metadata")
        elif source_tracking is not None and hasattr(source_tracking, "source_metadata"):
            source_metadata = source_tracking.source_metadata

        if isinstance(source_metadata, dict):
            raw_title = raw_title or source_metadata.get("raw_title")
            raw_body = raw_body or source_metadata.get("raw_body")

        return raw_title, raw_body

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

        GitHub adapter uses `import_artifact` with artifact_key="github_issue" to
        import individual issues as change proposals. Use that method instead.

        Args:
            bundle_dir: Path to bundle directory
            bridge_config: Optional bridge configuration

        Returns:
            None (not supported - use import_artifact instead)
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

        GitHub adapter uses `export_artifact` to sync individual proposals to GitHub
        issues. Use that method instead.

        Args:
            bundle_dir: Path to bundle directory
            change_tracking: ChangeTracking instance to save
            bridge_config: Optional bridge configuration
        """
        # Not supported - GitHub adapter uses export_artifact for individual proposals

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

        GitHub adapter uses `import_artifact` with artifact_key="github_issue" to
        import issues as change proposals. Use that method instead.

        Args:
            bundle_dir: Path to bundle directory
            change_name: Change identifier
            bridge_config: Optional bridge configuration

        Returns:
            None (not supported - use import_artifact instead)
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

        GitHub adapter uses `export_artifact` and `import_artifact` for bidirectional
        sync. Use `export_artifact` with artifact_key="change_proposal" to create
        GitHub issues, or `import_artifact` with artifact_key="github_issue" to
        import issues as change proposals.

        Args:
            bundle_dir: Path to bundle directory
            proposal: ChangeProposal instance to save
            bridge_config: Optional bridge configuration
        """
        # Not supported - GitHub adapter uses export_artifact/import_artifact for sync
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
        impact = proposal_data.get("impact", "")
        status = proposal_data.get("status", "proposed")
        change_id = proposal_data.get("change_id", "unknown")
        raw_title, raw_body = self._extract_raw_fields(proposal_data)
        if raw_title:
            title = raw_title

        # Build properly formatted issue body (prefer raw content when available)
        if raw_body:
            body = raw_body
        else:
            body_parts = []

            display_title = re.sub(r"^\[change\]\s*", "", title, flags=re.IGNORECASE).strip()
            if display_title:
                body_parts.append(f"# {display_title}")
                body_parts.append("")

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

            # Add Impact section if present
            if impact:
                body_parts.append("## Impact")
                body_parts.append("")
                impact_lines = impact.strip().split("\n")
                for line in impact_lines:
                    body_parts.append(line)
                body_parts.append("")

            # If no content, add placeholder
            if not body_parts or (not rationale and not description):
                body_parts.append("No description provided.")
                body_parts.append("")

            # Add OpenSpec metadata footer (avoid duplicates)
            if not any("OpenSpec Change Proposal:" in line for line in body_parts):
                body_parts.append("---")
                body_parts.append(f"*OpenSpec Change Proposal: `{change_id}`*")

            body = "\n".join(body_parts)

        # Create issue via GitHub API
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/issues"
        headers = {
            "Authorization": f"token {self.api_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        # Determine issue state based on proposal status
        # Completed proposals (applied, deprecated, discarded) should be closed
        should_close = status in ("applied", "deprecated", "discarded")
        issue_state = "closed" if should_close else "open"

        # Map status to GitHub state_reason
        state_reason = None
        if status == "applied":
            state_reason = "completed"
        elif status in ("deprecated", "discarded"):
            state_reason = "not_planned"

        payload = {
            "title": title,
            "body": body,
            "labels": self._get_labels_for_status(status),
            "state": issue_state,
        }
        if state_reason:
            payload["state_reason"] = state_reason

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            issue_data = response.json()

            # If issue was created as closed, add a comment explaining why
            if issue_state == "closed":
                source_tracking = proposal_data.get("source_tracking", {})
                # Note: openspec_repo_path not available in _create_issue_from_proposal context
                comment_text = self._get_status_comment(status, title, source_tracking, None)
                if comment_text:
                    # Add note that this was closed immediately upon creation
                    immediate_close_note = (
                        f"{comment_text}\n\n"
                        f"*Note: This issue was automatically closed upon creation because the "
                        f"change proposal has status `{status}`. This issue was created from an "
                        f"OpenSpec change proposal for tracking purposes.*"
                    )
                    self._add_issue_comment(repo_owner, repo_name, issue_data["number"], immediate_close_note)

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
        source_tracking = proposal_data.get("source_tracking", {})
        # Note: code_repo_path not available in _update_issue_status context
        comment_text = self._get_status_comment(status, title, source_tracking, None)

        # Map status to GitHub state_reason
        state_reason = None
        if status == "applied":
            state_reason = "completed"
        elif status in ("deprecated", "discarded"):
            state_reason = "not_planned"

        # Update issue state
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/issues/{issue_number}"
        headers = {
            "Authorization": f"token {self.api_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        payload = {"state": "closed" if should_close else "open"}
        if state_reason:
            payload["state_reason"] = state_reason

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
        code_repo_path: Path | None = None,
    ) -> dict[str, Any]:
        """
        Update GitHub issue body with new proposal content.

        Preserves existing sections that are not part of the proposal (e.g., acceptance criteria checklists).

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
        impact = proposal_data.get("impact", "")
        change_id = proposal_data.get("change_id", "unknown")
        status = proposal_data.get("status", "proposed")
        raw_title, raw_body = self._extract_raw_fields(proposal_data)
        if raw_title:
            title = raw_title

        # Get current issue body, title, and state to preserve sections and check if updates needed
        current_body = ""
        current_title = ""
        current_state = "open"
        try:
            url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/issues/{issue_number}"
            headers = {
                "Authorization": f"token {self.api_token}",
                "Accept": "application/vnd.github.v3+json",
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            issue_data = response.json()
            current_body = issue_data.get("body", "") or ""
            current_title = issue_data.get("title", "") or ""
            current_state = issue_data.get("state", "open")
        except requests.RequestException:
            # If we can't fetch current issue, proceed without preserving sections
            pass

        # Build properly formatted issue body (same format as creation, unless raw content is present)
        if raw_body:
            body = raw_body
        else:
            # Extract sections to preserve (anything after the OpenSpec metadata footer)
            preserved_sections = []
            if current_body:
                metadata_marker = f"*OpenSpec Change Proposal: `{change_id}`*"
                if metadata_marker in current_body:
                    _, after_marker = current_body.split(metadata_marker, 1)
                    if after_marker.strip():
                        preserved_content = after_marker.strip()
                        if "##" in preserved_content or "- [" in preserved_content or "* [" in preserved_content:
                            preserved_sections.append(preserved_content)

            body_parts = []

            display_title = re.sub(r"^\[change\]\s*", "", title, flags=re.IGNORECASE).strip()
            if display_title:
                body_parts.append(f"# {display_title}")
                body_parts.append("")

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

            # Add Impact section if present
            if impact:
                body_parts.append("## Impact")
                body_parts.append("")
                impact_lines = impact.strip().split("\n")
                for line in impact_lines:
                    body_parts.append(line)
                body_parts.append("")  # Blank line

            # If no content, add placeholder
            if not body_parts or (not rationale and not description):
                body_parts.append("No description provided.")
                body_parts.append("")

            # Add preserved sections (acceptance criteria, etc.)
            current_body_preview = "\n".join(body_parts)
            for preserved in preserved_sections:
                if preserved.strip():
                    preserved_clean = preserved.strip()
                    if preserved_clean not in current_body_preview:
                        body_parts.append("")  # Blank line before preserved section
                        body_parts.append(preserved_clean)

            # Add OpenSpec metadata footer (avoid duplicates)
            if not any("OpenSpec Change Proposal:" in line for line in body_parts):
                body_parts.append("---")
                body_parts.append(f"*OpenSpec Change Proposal: `{change_id}`*")

            body = "\n".join(body_parts)

        # Update issue body via GitHub API PATCH
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/issues/{issue_number}"
        headers = {
            "Authorization": f"token {self.api_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        # Determine issue state based on proposal status
        # Completed proposals (applied, deprecated, discarded) should be closed
        should_close = status in ("applied", "deprecated", "discarded")
        desired_state = "closed" if should_close else "open"

        # Map status to GitHub state_reason
        state_reason = None
        if status == "applied":
            state_reason = "completed"
        elif status in ("deprecated", "discarded"):
            state_reason = "not_planned"

        # Always update title if it differs (fixes issues created with wrong title)
        # Also update state if it doesn't match the proposal status
        payload: dict[str, Any] = {
            "body": body,
        }
        if current_title != title:
            payload["title"] = title

        if current_state != desired_state:
            payload["state"] = desired_state
            if state_reason:
                payload["state_reason"] = state_reason

        try:
            response = requests.patch(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            issue_data = response.json()

            # Add comment if issue was closed due to status change, or if already closed with applied status
            should_add_comment = False
            if "state" in payload and payload["state"] == "closed" and current_state == "open":
                # Issue was just closed
                should_add_comment = True
            elif status == "applied" and current_state == "closed":
                # Issue is already closed with applied status - check if we need to add/update comment with branch info
                # Only add if we're updating and status is applied (to include branch info)
                should_add_comment = True

            if should_add_comment:
                source_tracking = proposal_data.get("source_tracking", {})
                # Pass target_repo to filter source_tracking to only check entries for this repository
                target_repo = f"{repo_owner}/{repo_name}"
                comment_text = self._get_status_comment(status, title, source_tracking, code_repo_path, target_repo)
                if comment_text:
                    if "state" in payload and payload["state"] == "closed" and current_state == "open":
                        # Add note that this was closed due to status change
                        status_change_note = (
                            f"{comment_text}\n\n"
                            f"*Note: This issue was automatically closed because the change proposal "
                            f"status changed to `{status}`. This issue was updated from an OpenSpec change proposal.*"
                        )
                    else:
                        # Issue already closed - just add status comment with branch info
                        status_change_note = (
                            f"{comment_text}\n\n"
                            f"*Note: This issue was updated from an OpenSpec change proposal with status `{status}`.*"
                        )
                    self._add_issue_comment(repo_owner, repo_name, issue_number, status_change_note)

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

        Note:
            This method uses the tool-agnostic status mapping pattern from BacklogAdapterMixin.
        """
        return self.map_openspec_status_to_backlog(status)

    @beartype
    @require(lambda proposal: isinstance(proposal, (dict, ChangeProposal)), "Proposal must be dict or ChangeProposal")
    @require(lambda repo_owner: isinstance(repo_owner, str) and len(repo_owner) > 0, "Repo owner must be non-empty")
    @require(lambda repo_name: isinstance(repo_name, str) and len(repo_name) > 0, "Repo name must be non-empty")
    @ensure(lambda result: isinstance(result, dict), "Must return dict with sync result")
    def sync_status_to_github(
        self,
        proposal: dict[str, Any] | ChangeProposal,
        repo_owner: str,
        repo_name: str,
        bridge_config: BridgeConfig | None = None,
    ) -> dict[str, Any]:
        """
        Sync OpenSpec change status to GitHub issue labels.

        Updates GitHub issue labels based on OpenSpec change proposal status.

        Args:
            proposal: Change proposal (dict or ChangeProposal instance)
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            bridge_config: Optional bridge configuration (for cross-repo support)

        Returns:
            Dict with sync result: {"issue_number": int, "issue_url": str, "labels_updated": bool}

        Raises:
            ValueError: If issue number not found in source_tracking
            requests.RequestException: If GitHub API call fails

        Note:
            This implements the tool-agnostic status sync pattern. Future backlog
            adapters should implement similar sync methods for their tools.
        """
        # Extract status and source_tracking
        if isinstance(proposal, ChangeProposal):
            status = proposal.status
            source_tracking = proposal.source_tracking
        else:
            status = proposal.get("status", "proposed")
            source_tracking = proposal.get("source_tracking")

        if not source_tracking:
            msg = "Source tracking required for status sync (issue must be created first)"
            raise ValueError(msg)

        # Get issue number from source_tracking (handle both dict and list formats)
        issue_number = None
        target_repo = f"{repo_owner}/{repo_name}"

        if isinstance(source_tracking, dict):
            issue_number = source_tracking.get("source_id")
        elif isinstance(source_tracking, list):
            for entry in source_tracking:
                if isinstance(entry, dict):
                    entry_repo = entry.get("source_repo")
                    if entry_repo == target_repo:
                        issue_number = entry.get("source_id")
                        break
                    if not entry_repo:
                        source_url = entry.get("source_url", "")
                        if source_url and target_repo in source_url:
                            issue_number = entry.get("source_id")
                            break

        if not issue_number:
            msg = f"Issue number not found in source_tracking for repository {target_repo}"
            raise ValueError(msg)

        # Map OpenSpec status to GitHub labels
        new_labels = self.map_openspec_status_to_backlog(status)

        # Get current issue to retrieve existing labels
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/issues/{issue_number}"
        headers = {
            "Authorization": f"token {self.api_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        try:
            # Get current issue
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            current_issue = response.json()

            # Get current labels (excluding openspec and status labels)
            current_labels = [label.get("name", "") for label in current_issue.get("labels", [])]
            status_labels = ["in-progress", "completed", "deprecated", "wontfix"]
            # Keep non-status labels
            keep_labels = [label for label in current_labels if label not in status_labels and label != "openspec"]

            # Combine: keep non-status labels + new status labels
            all_labels = list(set(keep_labels + new_labels))

            # Update issue labels
            patch_url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/issues/{issue_number}"
            patch_payload = {"labels": all_labels}

            patch_response = requests.patch(patch_url, json=patch_payload, headers=headers, timeout=30)
            patch_response.raise_for_status()

            return {
                "issue_number": current_issue.get("number", issue_number),  # Use API response number (int)
                "issue_url": current_issue.get("html_url", ""),
                "labels_updated": True,
                "new_labels": new_labels,
            }
        except requests.RequestException as e:
            msg = f"Failed to sync status to GitHub issue #{issue_number}: {e}"
            console.print(f"[bold red]✗[/bold red] {msg}")
            raise

    @beartype
    @require(lambda issue_data: isinstance(issue_data, dict), "Issue data must be dict")
    @require(lambda proposal: isinstance(proposal, (dict, ChangeProposal)), "Proposal must be dict or ChangeProposal")
    @ensure(lambda result: isinstance(result, str), "Must return resolved status string")
    def sync_status_from_github(
        self,
        issue_data: dict[str, Any],
        proposal: dict[str, Any] | ChangeProposal,
        strategy: str = "prefer_openspec",
    ) -> str:
        """
        Sync GitHub issue status to OpenSpec change proposal.

        Maps GitHub issue labels to OpenSpec status and resolves conflicts if status differs.

        Args:
            issue_data: GitHub issue data (dict from API response)
            proposal: Change proposal (dict or ChangeProposal instance)
            strategy: Conflict resolution strategy (prefer_openspec, prefer_backlog, merge)

        Returns:
            Resolved OpenSpec status string

        Note:
            This implements the tool-agnostic status sync pattern with conflict resolution.
            Future backlog adapters should implement similar sync methods for their tools.
        """
        # Extract GitHub status from labels
        labels = issue_data.get("labels", [])
        github_status = "open"  # Default
        if labels:
            label_names = [label.get("name", "") if isinstance(label, dict) else str(label) for label in labels]
            for label_name in label_names:
                mapped_status = self.map_backlog_status_to_openspec(label_name)
                if mapped_status != "proposed":  # Use first non-default status
                    github_status = label_name
                    break

        # Map GitHub status to OpenSpec status
        openspec_status_from_github = self.map_backlog_status_to_openspec(github_status)

        # Get current OpenSpec status
        if isinstance(proposal, ChangeProposal):
            openspec_status = proposal.status
        else:
            openspec_status = proposal.get("status", "proposed")

        # Resolve conflict if status differs
        return self.resolve_status_conflict(openspec_status, openspec_status_from_github, strategy)

    def _get_status_comment(
        self,
        status: str,
        title: str,
        source_tracking: dict[str, Any] | list[dict[str, Any]] | None = None,
        code_repo_path: Path | None = None,
        target_repo: str | None = None,
    ) -> str:
        """
        Get comment text for status change.

        Args:
            status: Change proposal status
            title: Change proposal title
            source_tracking: Source tracking entry (dict) or list of entries to extract branch info
            code_repo_path: Path to code repository (where implementation branches are stored) for branch verification
            target_repo: Target repository identifier (e.g., "nold-ai/specfact-cli") to filter source_tracking entries

        Returns:
            Comment text or empty string if no comment needed
        """
        if status == "applied":
            # Try to extract branch information from source_tracking
            # If we have a target_repo, only check entries for that repository
            # Otherwise, check all entries (for backward compatibility)
            branch_info = None
            if target_repo and isinstance(source_tracking, list):
                # Find entry for target repository
                target_entry = next(
                    (e for e in source_tracking if isinstance(e, dict) and e.get("source_repo") == target_repo),
                    None,
                )
                if target_entry:
                    branch_info = self._extract_branch_from_source_tracking(target_entry, code_repo_path)
                # If no target_entry found, don't fall back to other repos - this prevents
                # attaching branch info from unrelated repositories to the wrong GitHub issue
            else:
                # Check branch in code repository (where implementation is stored)
                branch_info = self._extract_branch_from_source_tracking(source_tracking, code_repo_path)
            branch_text = f"\n\n**Implementation Branch**: `{branch_info}`" if branch_info else ""
            return f"✅ Change applied: {title}\n\nThis change proposal has been implemented and applied.{branch_text}"
        if status == "deprecated":
            return (
                f"⚠️ Change deprecated: {title}\n\nThis change proposal has been deprecated and will not be implemented."
            )
        if status == "discarded":
            return f"❌ Change discarded: {title}\n\nThis change proposal has been discarded."
        if status == "in-progress":
            return f"🔄 Change in progress: {title}\n\nImplementation of this change proposal has started."
        return ""

    def _extract_branch_from_source_tracking(
        self,
        source_tracking: dict[str, Any] | list[dict[str, Any]] | None,
        code_repo_path: Path | None = None,
    ) -> str | None:
        """
        Extract branch information from source tracking entry.

        Args:
            source_tracking: Source tracking entry (dict) or list of entries
            code_repo_path: Path to code repository (where implementation branches are stored) for branch verification

        Returns:
            Branch name if found and verified, None otherwise
        """
        if not source_tracking:
            return None

        # Handle list of entries - try to find one with branch info
        if isinstance(source_tracking, list):
            for entry in source_tracking:
                if isinstance(entry, dict):
                    branch = self._get_branch_from_entry(entry, code_repo_path)
                    if branch:
                        return branch
            return None

        # Handle single dict entry
        if isinstance(source_tracking, dict):
            return self._get_branch_from_entry(source_tracking, code_repo_path)

        return None

    def _get_branch_from_entry(self, entry: dict[str, Any], code_repo_path: Path | None = None) -> str | None:
        """
        Extract branch from a single source tracking entry.

        Args:
            entry: Source tracking entry dict
            code_repo_path: Path to code repository (where implementation branches are stored)

        Returns:
            Branch name if found and verified, None otherwise
        """
        # Determine which repository to check based on source_repo
        # If code_repo_path is provided, use it; otherwise try to find it from source_repo
        repo_path_to_check = code_repo_path
        if not repo_path_to_check:
            source_repo = entry.get("source_repo")
            if source_repo:
                # Try to find local path to code repository
                repo_path_to_check = self._find_code_repo_path(source_repo)

        # Check source_metadata for branch
        source_metadata = entry.get("source_metadata", {})
        if isinstance(source_metadata, dict):
            branch = source_metadata.get("branch") or source_metadata.get("source_branch")
            if branch:
                # Verify branch exists in code repo if path available
                if repo_path_to_check:
                    if self._verify_branch_exists(branch, repo_path_to_check):
                        return branch
                else:
                    # No repo path available, return branch as-is
                    return branch

        # Check for branch field directly in entry
        branch = entry.get("branch") or entry.get("source_branch")
        if branch:
            # Verify branch exists in code repo if path available
            if repo_path_to_check:
                if self._verify_branch_exists(branch, repo_path_to_check):
                    return branch
            else:
                # No repo path available, return branch as-is
                return branch

        # Try to detect branch from actual implementation (files changed, commits)
        # This is more accurate than inferring from change_id
        if repo_path_to_check:
            detected_branch = self._detect_implementation_branch(entry, repo_path_to_check)
            if detected_branch:
                return detected_branch

        # Fallback: Try to infer from change_id (common pattern: feature/<change-id>)
        # Only use this if we couldn't detect the actual branch
        change_id = entry.get("change_id")
        if change_id:
            # Common branch naming patterns
            possible_branches = [
                f"feature/{change_id}",
                f"bugfix/{change_id}",
                f"hotfix/{change_id}",
            ]
            # Check each possible branch in code repo
            if repo_path_to_check:
                for branch in possible_branches:
                    if self._verify_branch_exists(branch, repo_path_to_check):
                        return branch
            else:
                # No repo path available, return first as reasonable default
                return possible_branches[0]

        return None

    def _verify_branch_exists(self, branch_name: str, repo_path: Path) -> bool:
        """
        Verify that a branch exists in the given repository.

        Args:
            branch_name: Branch name to check
            repo_path: Path to git repository

        Returns:
            True if branch exists, False otherwise
        """
        try:
            import subprocess

            result = subprocess.run(
                ["git", "branch", "--list", branch_name],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            # Check if branch exists locally (strip whitespace and check exact match)
            if result.returncode == 0:
                branches = [line.strip().replace("*", "").strip() for line in result.stdout.split("\n") if line.strip()]
                if branch_name in branches:
                    return True

            # Also check remote branches
            result = subprocess.run(
                ["git", "branch", "-r", "--list", f"*/{branch_name}"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                # Extract branch name from remote branch format (origin/branch-name)
                # Preserve full branch path after remote prefix (e.g., origin/feature/foo -> feature/foo)
                remote_branches = []
                for line in result.stdout.split("\n"):
                    line = line.strip()
                    if line and "/" in line:
                        # Remove remote prefix (e.g., "origin/" or "upstream/") but keep full branch path
                        parts = line.split("/", 1)  # Split only on first "/"
                        if len(parts) == 2:
                            remote_branches.append(parts[1])  # Keep everything after remote prefix
                if branch_name in remote_branches:
                    return True

            return False
        except Exception:
            # If we can't check (git not available, etc.), return False to be safe
            return False

    def _find_code_repo_path(self, source_repo: str) -> Path | None:
        """
        Find local path to code repository based on source_repo identifier.

        Args:
            source_repo: Repository identifier in format "owner/repo-name" (e.g., "nold-ai/specfact-cli")

        Returns:
            Path to code repository if found, None otherwise
        """
        if not source_repo or "/" not in source_repo:
            return None

        _, repo_name = source_repo.split("/", 1)

        # Strategy 1: Check if current working directory is the code repository
        try:
            cwd = Path.cwd()
            if cwd.name == repo_name and (cwd / ".git").exists():
                # Verify it's the right repo by checking remote
                result = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if result.returncode == 0 and repo_name in result.stdout:
                    return cwd
        except Exception:
            pass

        # Strategy 2: Check parent directory (common structure: parent/repo-name)
        try:
            cwd = Path.cwd()
            parent = cwd.parent
            repo_path = parent / repo_name
            if repo_path.exists() and (repo_path / ".git").exists():
                return repo_path
        except Exception:
            pass

        # Strategy 3: Check sibling directories (common structure: sibling/repo-name)
        try:
            cwd = Path.cwd()
            grandparent = cwd.parent.parent if cwd.parent != Path("/") else None
            if grandparent:
                for sibling in grandparent.iterdir():
                    if sibling.is_dir() and sibling.name == repo_name and (sibling / ".git").exists():
                        return sibling
        except Exception:
            pass

        return None

    def _detect_implementation_branch(self, entry: dict[str, Any], repo_path: Path) -> str | None:
        """
        Detect the actual branch where files from this change were implemented.

        This method looks at the actual implementation (files changed, commits) to find
        which branch contains those changes, rather than inferring from change_id.

        Args:
            entry: Source tracking entry dict
            repo_path: Path to code repository

        Returns:
            Branch name if detected, None otherwise
        """
        if not repo_path.exists() or not (repo_path / ".git").exists():
            return None

        try:
            change_id = entry.get("change_id")
            issue_number = entry.get("source_id")  # GitHub issue number

            # Store change_id for use in _find_branch_containing_files
            if change_id:
                self._current_change_id = change_id

            # Strategy 1: Check source_metadata for commit hash or file paths
            source_metadata = entry.get("source_metadata", {})
            if isinstance(source_metadata, dict):
                # Check for commit hash
                commit_hash = source_metadata.get("commit") or source_metadata.get("commit_hash")
                if commit_hash:
                    branch = self._find_branch_containing_commit(commit_hash, repo_path)
                    if branch:
                        return branch

                # Check for file paths
                files_changed = source_metadata.get("files") or source_metadata.get("files_changed")
                if files_changed:
                    branch = self._find_branch_containing_files(files_changed, repo_path, issue_number)
                    if branch:
                        return branch

            # Strategy 2: Check for commit hash or file paths directly in entry
            commit_hash = entry.get("commit") or entry.get("commit_hash")
            if commit_hash:
                branch = self._find_branch_containing_commit(commit_hash, repo_path)
                if branch:
                    return branch

            files_changed = entry.get("files") or entry.get("files_changed")
            if files_changed:
                branch = self._find_branch_containing_files(files_changed, repo_path, issue_number)
                if branch:
                    return branch

            # Strategy 3: Look for commits that mention the change_id or issue number in commit messages
            # This is the most reliable method when we have an issue number
            if issue_number:
                # Prefer issue number search - it's more specific
                branch = self._find_branch_by_change_id_in_commits("", repo_path, issue_number)
                if branch:
                    return branch
                # If issue number search fails, fall back to change_id search
                # This handles cases where commits mention the change_id but not the issue number
                if change_id:
                    branch = self._find_branch_by_change_id_in_commits(change_id, repo_path, None)
                    if branch:
                        return branch
            elif change_id:
                # Only search by change_id if we don't have an issue number
                # This is less reliable as change_id might match unrelated commits
                branch = self._find_branch_by_change_id_in_commits(change_id, repo_path, None)
                if branch:
                    return branch

        except Exception:
            # If detection fails, return None (will fall back to inference)
            pass
        finally:
            # Clean up temporary attribute
            if hasattr(self, "_current_change_id"):
                delattr(self, "_current_change_id")

        return None

    def _find_branch_containing_commit(self, commit_hash: str, repo_path: Path) -> str | None:
        """
        Find which branch contains a specific commit.

        Args:
            commit_hash: Git commit hash (full or short)
            repo_path: Path to git repository

        Returns:
            Branch name if found, None otherwise
        """
        try:
            # First, verify the commit exists
            result = subprocess.run(
                ["git", "rev-parse", "--verify", f"{commit_hash}^{{commit}}"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode != 0:
                return None

            # Find branches that contain this commit
            # Use --all to include remote branches
            result = subprocess.run(
                ["git", "branch", "-a", "--contains", commit_hash, "--format=%(refname:short)"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                branches = [b.strip() for b in result.stdout.strip().split("\n") if b.strip()]
                # Remove 'origin/' prefix from remote branches for comparison
                local_branches = []
                seen_branches = set()
                for branch in branches:
                    clean_branch = branch.replace("origin/", "") if branch.startswith("origin/") else branch
                    # Deduplicate (remote and local branches might both be present)
                    if clean_branch not in seen_branches:
                        local_branches.append(clean_branch)
                        seen_branches.add(clean_branch)

                # Get change_id from instance attribute if available (set by _detect_implementation_branch)
                change_id = getattr(self, "_current_change_id", None)

                # Strategy 1: Prefer branches that match the change_id in their name
                # This is the most reliable - the branch name often matches the change_id
                if change_id:
                    # Normalize change_id for matching (remove hyphens, underscores, convert to lowercase)
                    normalized_change_id = change_id.lower().replace("-", "").replace("_", "")
                    # Extract key words from change_id (split by common separators and filter out short words)
                    change_id_words = [
                        word
                        for word in change_id.lower().replace("-", "_").split("_")
                        if len(word) > 3  # Only consider words longer than 3 characters
                    ]
                    for branch in local_branches:
                        if any(prefix in branch for prefix in ["feature/", "bugfix/", "hotfix/"]):
                            # Normalize branch name for comparison
                            normalized_branch = branch.lower().replace("-", "").replace("_", "").replace("/", "")
                            # Check if change_id is a substring of branch name
                            if normalized_change_id in normalized_branch:
                                return branch
                            # Also check if key words from change_id appear in branch name
                            # This handles cases where branch name has additional words (e.g., "datamodel")
                            if change_id_words:
                                branch_words = [
                                    word
                                    for word in branch.lower().replace("-", "_").replace("/", "_").split("_")
                                    if len(word) > 3
                                ]
                                # Check if at least 2 key words from change_id appear in branch
                                matching_words = sum(1 for word in change_id_words if word in branch_words)
                                if matching_words >= 2:
                                    return branch

                # Strategy 2: Prefer feature/bugfix/hotfix branches over main/master
                for branch in local_branches:
                    if any(prefix in branch for prefix in ["feature/", "bugfix/", "hotfix/"]):
                        return branch
                # Return first branch if no feature branch found
                return local_branches[0] if local_branches else None

        except Exception:
            pass

        return None

    def _find_branch_containing_files(
        self, files: list[str] | str, repo_path: Path, issue_number: str | None = None
    ) -> str | None:
        """
        Find which branch contains changes to specific files.

        This method looks for the actual implementation branch by:
        1. Finding commits that touch these files
        2. Looking for commits that are NOT on main/master (implementation branches)
        3. Preferring commits that are in feature/bugfix/hotfix branches

        Args:
            files: List of file paths or single file path string
            repo_path: Path to git repository
            issue_number: Optional GitHub issue number to filter commits (e.g., "107")

        Returns:
            Branch name if found, None otherwise
        """
        try:
            if isinstance(files, str):
                files = [files]

            file_args = files[:10]  # Limit to first 10 files to avoid command line length issues

            # If we have an issue number, try to find commits that reference it
            # This helps avoid matching commits from the current working branch
            if issue_number:
                # Search for commits that touch these files AND mention the issue
                patterns = [f"#{issue_number}", f"fixes #{issue_number}", f"closes #{issue_number}"]
                for pattern in patterns:
                    result = subprocess.run(
                        ["git", "log", "--all", "--grep", pattern, "--format=%H", "--", *file_args],
                        cwd=repo_path,
                        capture_output=True,
                        text=True,
                        timeout=10,
                        check=False,
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        # Get the most recent commit (first line)
                        commit_hash = result.stdout.strip().split("\n")[0]
                        branch = self._find_branch_containing_commit(commit_hash, repo_path)
                        if branch:
                            return branch

            # Find commits that touched these files AND mention the change_id in commit message
            # This is the most specific search - finds the actual implementation commit
            change_id = getattr(self, "_current_change_id", None)
            if change_id:
                result = subprocess.run(
                    [
                        "git",
                        "log",
                        "--all",
                        "--grep",
                        change_id,
                        "--format=%H|%s",
                        "-i",
                        "--no-merges",
                        "--",
                        *file_args,
                    ],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                if result.returncode == 0 and result.stdout.strip():
                    # Try each commit until we find one in a feature branch
                    # Skip merge commits - they're not the actual implementation
                    for line in result.stdout.strip().split("\n")[:10]:
                        if "|" in line:
                            commit_hash, subject = line.split("|", 1)
                        else:
                            commit_hash = line
                            subject = ""

                        # Skip merge commits and chore commits - look for actual implementation
                        if any(word in subject.lower() for word in ["merge", "chore:", "docs:"]):
                            continue

                        branch = self._find_branch_containing_commit(commit_hash, repo_path)
                        # Prefer feature/bugfix/hotfix branches
                        if branch and any(prefix in branch for prefix in ["feature/", "bugfix/", "hotfix/"]):
                            return branch

            # Find commits that touched these files, but exclude main/master
            # This helps find the actual implementation branch, not just merged commits
            result = subprocess.run(
                [
                    "git",
                    "log",
                    "--all",
                    "--format=%H",
                    "--not",
                    "--remotes=origin/main",
                    "--not",
                    "--remotes=origin/master",
                    "--",
                    *file_args,
                ],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                # Try each commit until we find one in a feature branch
                for commit_hash in result.stdout.strip().split("\n")[:20]:  # Limit to first 20 commits
                    branch = self._find_branch_containing_commit(commit_hash, repo_path)
                    # Prefer feature/bugfix/hotfix branches
                    if branch and any(prefix in branch for prefix in ["feature/", "bugfix/", "hotfix/"]):
                        return branch

            # Fallback: Find commits that touched these files (including main/master)
            # This might match the current working branch, so use with caution
            result = subprocess.run(
                ["git", "log", "--all", "--format=%H", "-30", "--", *file_args],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                # Try each commit until we find one in a feature branch (not current working branch)
                for commit_hash in result.stdout.strip().split("\n"):
                    branch = self._find_branch_containing_commit(commit_hash, repo_path)
                    # Prefer feature/bugfix/hotfix branches
                    if branch and any(prefix in branch for prefix in ["feature/", "bugfix/", "hotfix/"]):
                        return branch
                # If no feature branch found, return None (don't guess)
                return None

        except Exception:
            pass

        return None

    def _find_branch_by_change_id_in_commits(
        self, change_id: str, repo_path: Path, issue_number: str | None = None
    ) -> str | None:
        """
        Find branch by searching commit messages for change_id or issue number.

        Args:
            change_id: Change proposal ID to search for
            repo_path: Path to git repository
            issue_number: Optional GitHub issue number to search for (e.g., "107")

        Returns:
            Branch name if found, None otherwise
        """
        try:
            # Strategy 1: Search for commits that reference the issue number
            # This is the most reliable method - issue numbers are specific
            if issue_number:
                # Search for patterns like "#107", "fixes #107", "closes #107", etc.
                patterns = [f"#{issue_number}", f"fixes #{issue_number}", f"closes #{issue_number}"]
                for pattern in patterns:
                    result = subprocess.run(
                        ["git", "log", "--all", "--grep", pattern, "--format=%H", "-n", "10"],
                        cwd=repo_path,
                        capture_output=True,
                        text=True,
                        timeout=10,
                        check=False,
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        # Try each commit until we find one in a feature branch
                        for commit_hash in result.stdout.strip().split("\n"):
                            branch = self._find_branch_containing_commit(commit_hash, repo_path)
                            # Prefer feature/bugfix/hotfix branches
                            if branch and any(prefix in branch for prefix in ["feature/", "bugfix/", "hotfix/"]):
                                return branch
                        # If no feature branch found, return the first one
                        commit_hash = result.stdout.strip().split("\n")[0]
                        branch = self._find_branch_containing_commit(commit_hash, repo_path)
                        if branch:
                            return branch
                # If no commits found with issue number, return None
                # Don't fall back to change_id search - it's too unreliable
                return None

            # Strategy 2: Search for commits mentioning the change_id in commit messages
            # Only use this if we don't have an issue number, or if issue number search failed
            # This is less reliable as change_id might match unrelated commits
            if change_id:
                # Search with --no-merges to avoid merge commits, and get commit subjects too
                result = subprocess.run(
                    ["git", "log", "--all", "--grep", change_id, "--format=%H|%s", "-i", "--no-merges", "-n", "20"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                if result.returncode == 0 and result.stdout.strip():
                    # First pass: Look for commits that are clearly implementation commits
                    # These have "implement" or "feat:" AND the change_id in the subject
                    for line in result.stdout.strip().split("\n"):
                        if "|" in line:
                            commit_hash, subject = line.split("|", 1)
                        else:
                            commit_hash = line
                            subject = ""

                        # Skip merge, chore, and docs commits - look for actual implementation
                        if any(word in subject.lower() for word in ["merge", "chore:", "docs:"]):
                            continue

                        # Check if this is clearly an implementation commit
                        # Look for "implement" or "feat:" AND the change_id in the subject
                        # This ensures we find the actual implementation commit, not just any commit mentioning the change_id
                        has_implementation_keyword = any(word in subject.lower() for word in ["implement", "feat:"])
                        has_change_id = change_id.lower() in subject.lower()
                        is_implementation = has_implementation_keyword and has_change_id

                        # Only process commits that are clearly implementation commits
                        if is_implementation:
                            branch = self._find_branch_containing_commit(commit_hash, repo_path)
                            if branch and any(prefix in branch for prefix in ["feature/", "bugfix/", "hotfix/"]):
                                # This is the implementation commit - return its branch immediately
                                return branch

                    # If we didn't find an implementation commit, return None (don't guess)
                    # This is safer than returning a branch from a non-implementation commit
                    return None

        except Exception:
            pass

        return None

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
