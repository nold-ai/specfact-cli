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

        # Parse markdown sections (Why, What Changes)
        if body:
            # Extract "Why" section (stop at next section or footer)
            why_match = re.search(r"##\s+Why\s*\n(.*?)(?=\n##|\n---|\Z)", body, re.DOTALL | re.IGNORECASE)
            if why_match:
                rationale = why_match.group(1).strip()

            # Extract "What Changes" section (stop at next section or footer)
            what_match = re.search(r"##\s+What\s+Changes\s*\n(.*?)(?=\n##|\n---|\Z)", body, re.DOTALL | re.IGNORECASE)
            if what_match:
                description = what_match.group(1).strip()
            elif not why_match:
                # If no sections found, use entire body as description (but remove footer)
                body_clean = re.sub(r"\n---\s*\n\*OpenSpec Change Proposal:.*", "", body, flags=re.DOTALL)
                description = body_clean.strip()

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
            when_match = re.search(r"##\s+When\s*\n(.*?)(?=\n##|\Z)", body, re.DOTALL | re.IGNORECASE)
            if when_match:
                timeline = when_match.group(1).strip()

            # Extract "Who" section (owner, stakeholders)
            who_match = re.search(r"##\s+Who\s*\n(.*?)(?=\n##|\Z)", body, re.DOTALL | re.IGNORECASE)
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
                comment_text = self._get_status_comment(status, title, source_tracking)
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
        comment_text = self._get_status_comment(status, title, source_tracking)

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
        change_id = proposal_data.get("change_id", "unknown")
        status = proposal_data.get("status", "proposed")

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

        # Extract sections to preserve (anything after the OpenSpec metadata footer or sections not in proposal)
        preserved_sections = []
        if current_body:
            # Split body by OpenSpec metadata footer
            parts = current_body.split("---")
            if len(parts) > 1:
                # Everything after the first "---" (metadata footer) should be preserved
                # But we need to be careful - the footer might appear in the proposal content
                # Look for the OpenSpec Change Proposal marker
                metadata_marker = f"*OpenSpec Change Proposal: `{change_id}`*"
                if metadata_marker in current_body:
                    # Split at the metadata marker
                    _, after_marker = current_body.split(metadata_marker, 1)
                    # Preserve sections that come after the marker
                    if after_marker.strip():
                        # Extract sections that should be preserved (acceptance criteria, etc.)
                        preserved_content = after_marker.strip()
                        # Only preserve if it looks like additional content (has headers or checklists)
                        if "##" in preserved_content or "- [" in preserved_content or "* [" in preserved_content:
                            preserved_sections.append(preserved_content)
                else:
                    # No marker found - check for acceptance criteria or other sections
                    # Look for sections that aren't "Why" or "What Changes"
                    lines = current_body.split("\n")
                    in_preserved_section = False
                    preserved_lines = []
                    for line in lines:
                        line_stripped = line.strip()
                        # Start preserving after we've seen the metadata footer or if we see acceptance criteria
                        if (
                            line_stripped.startswith("---")
                            or "acceptance" in line_stripped.lower()
                            or "criteria" in line_stripped.lower()
                        ):
                            in_preserved_section = True
                        if in_preserved_section and not line_stripped.startswith("*OpenSpec Change Proposal"):
                            preserved_lines.append(line)
                    if preserved_lines:
                        preserved_sections.append("\n".join(preserved_lines).strip())

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

        # Add preserved sections (acceptance criteria, etc.)
        for preserved in preserved_sections:
            if preserved.strip():
                body_parts.append("")  # Blank line before preserved section
                body_parts.append(preserved.strip())

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

            # Add comment if issue was closed due to status change
            if "state" in payload and payload["state"] == "closed" and current_state == "open":
                source_tracking = proposal_data.get("source_tracking", {})
                comment_text = self._get_status_comment(status, title, source_tracking)
                if comment_text:
                    # Add note that this was closed due to status change
                    status_change_note = (
                        f"{comment_text}\n\n"
                        f"*Note: This issue was automatically closed because the change proposal "
                        f"status changed to `{status}`. This issue was updated from an OpenSpec change proposal.*"
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
        self, status: str, title: str, source_tracking: dict[str, Any] | list[dict[str, Any]] | None = None
    ) -> str:
        """
        Get comment text for status change.

        Args:
            status: Change proposal status
            title: Change proposal title
            source_tracking: Source tracking entry (dict) or list of entries to extract branch info

        Returns:
            Comment text or empty string if no comment needed
        """
        if status == "applied":
            # Try to extract branch information from source_tracking
            branch_info = self._extract_branch_from_source_tracking(source_tracking)
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
        self, source_tracking: dict[str, Any] | list[dict[str, Any]] | None
    ) -> str | None:
        """
        Extract branch information from source tracking entry.

        Args:
            source_tracking: Source tracking entry (dict) or list of entries

        Returns:
            Branch name if found, None otherwise
        """
        if not source_tracking:
            return None

        # Handle list of entries - try to find one with branch info
        if isinstance(source_tracking, list):
            for entry in source_tracking:
                if isinstance(entry, dict):
                    branch = self._get_branch_from_entry(entry)
                    if branch:
                        return branch
            return None

        # Handle single dict entry
        if isinstance(source_tracking, dict):
            return self._get_branch_from_entry(source_tracking)

        return None

    def _get_branch_from_entry(self, entry: dict[str, Any]) -> str | None:
        """
        Extract branch from a single source tracking entry.

        Args:
            entry: Source tracking entry dict

        Returns:
            Branch name if found, None otherwise
        """
        # Check source_metadata for branch
        source_metadata = entry.get("source_metadata", {})
        if isinstance(source_metadata, dict):
            branch = source_metadata.get("branch") or source_metadata.get("source_branch")
            if branch:
                return branch

        # Check for branch field directly in entry
        branch = entry.get("branch") or entry.get("source_branch")
        if branch:
            return branch

        # Try to infer from change_id (common pattern: feature/<change-id>)
        change_id = entry.get("change_id")
        if change_id:
            # Common branch naming patterns
            possible_branches = [
                f"feature/{change_id}",
                f"bugfix/{change_id}",
                f"hotfix/{change_id}",
            ]
            # Return the first one as a reasonable default (could be enhanced to check git)
            return possible_branches[0]

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
