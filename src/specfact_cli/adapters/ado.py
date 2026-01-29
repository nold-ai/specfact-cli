"""
Azure DevOps bridge adapter for DevOps backlog tracking.

This adapter implements the BridgeAdapter interface to sync OpenSpec change proposals
with Azure DevOps work items, enabling bidirectional sync (OpenSpec ↔ ADO Work Items) for
project planning alignment with specifications.

This follows the backlog adapter patterns established by the GitHub adapter.
"""

from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from beartype import beartype
from icontract import ensure, require
from rich.console import Console

from specfact_cli.adapters.backlog_base import BacklogAdapterMixin
from specfact_cli.adapters.base import BridgeAdapter
from specfact_cli.backlog.adapters.base import BacklogAdapter
from specfact_cli.backlog.filters import BacklogFilters
from specfact_cli.backlog.mappers.ado_mapper import AdoFieldMapper
from specfact_cli.common.logger_setup import LoggerSetup
from specfact_cli.models.backlog_item import BacklogItem
from specfact_cli.models.bridge import BridgeConfig
from specfact_cli.models.capabilities import ToolCapabilities
from specfact_cli.models.change import ChangeProposal, ChangeTracking
from specfact_cli.runtime import debug_log_operation, debug_print, is_debug_mode
from specfact_cli.utils.auth_tokens import get_token, set_token


_MAX_RESPONSE_BODY_LOG = 2048

console = Console()


def _log_ado_patch_failure(
    response: requests.Response | None,
    operations: list[dict[str, Any]],
    url: str,
    context: str = "",
) -> str:
    """
    Log ADO PATCH failure to debug log (when debug on) and return user-facing message.

    Parses response body (JSON message or truncated text), extracts patch paths,
    redacts/truncates for debug log, and builds a user message with ADO text and hint.
    """
    paths = [op.get("path", "") for op in operations if isinstance(op, dict)]
    snippet = ""
    if response is not None:
        try:
            body = response.json()
            snippet = str(body.get("message", response.text[:500]))
        except Exception:
            snippet = (response.text or "")[:_MAX_RESPONSE_BODY_LOG]
        snippet = snippet[:_MAX_RESPONSE_BODY_LOG]
        snippet = str(LoggerSetup.redact_secrets(snippet))

    if is_debug_mode():
        debug_log_operation(
            "ado_patch",
            url,
            "failed",
            error=context or snippet[:500],
            extra={"response_body": snippet, "patch_paths": paths},
        )

    return _build_ado_user_message(response)


def _build_ado_user_message(response: requests.Response | None) -> str:
    """Build user-facing error message from ADO response and append mapping hint."""
    hint = " Check custom field mapping; see ado_custom.yaml or documentation."
    if response is None:
        return f"Azure DevOps request failed.{hint}"
    try:
        body = response.json()
        msg = body.get("message", "") or (response.text or "")[:500]
    except Exception:
        msg = (response.text or "")[:500]
    if not msg:
        return f"Azure DevOps request failed (HTTP {getattr(response, 'status_code', '')}).{hint}"

    m = re.search(r"Cannot find field\s+([^\s]+)", msg, re.IGNORECASE)
    if m:
        field = m.group(1).strip().rstrip(".")
        user_msg = f"Field '{field}' not found.{hint}"
    else:
        user_msg = f"{msg}{hint}"
    return user_msg


class AdoAdapter(BridgeAdapter, BacklogAdapterMixin, BacklogAdapter):
    """
    Azure DevOps bridge adapter implementing BridgeAdapter interface.

    This adapter provides bidirectional sync (OpenSpec ↔ ADO Work Items) for
    DevOps backlog tracking. It creates and updates ADO work items from
    OpenSpec change proposals, and imports ADO work items as OpenSpec change proposals.

    This follows the backlog adapter patterns established by the GitHub adapter.
    """

    def __init__(
        self,
        org: str | None = None,
        project: str | None = None,
        team: str | None = None,
        base_url: str | None = None,
        api_token: str | None = None,
        work_item_type: str | None = None,
    ) -> None:
        """
        Initialize Azure DevOps adapter.

        Args:
            org: Azure DevOps organization name (optional, can be provided via env/CLI)
            project: Azure DevOps project name (optional, can be provided via env/CLI)
            team: Azure DevOps team name (optional, defaults to project name for iteration lookup)
            base_url: Azure DevOps base URL (optional, defaults to https://dev.azure.com)
            api_token: Azure DevOps PAT (optional, uses AZURE_DEVOPS_TOKEN env var or stored auth token)
            work_item_type: Work item type (optional, derived from process template if not provided)
        """
        self.org = org
        self.project = project
        # Don't default team to project here - will be resolved in _get_current_iteration if needed
        self.team = team
        self.auth_scheme: str | None = None

        # Token resolution: explicit token > env var > stored token
        if api_token:
            self.api_token = api_token
            self.auth_scheme = "basic"
        elif os.environ.get("AZURE_DEVOPS_TOKEN"):
            self.api_token = os.environ.get("AZURE_DEVOPS_TOKEN")
            self.auth_scheme = "basic"
        elif stored_token := get_token("azure-devops", allow_expired=False):
            # Valid, non-expired token found
            self.api_token = stored_token.get("access_token")
            token_type = (stored_token.get("token_type") or "bearer").lower()
            self.auth_scheme = "bearer" if token_type == "bearer" else "basic"
        elif stored_token_expired := get_token("azure-devops", allow_expired=True):
            # Token exists but is expired - try to refresh using persistent cache
            expires_at = stored_token_expired.get("expires_at", "unknown")
            token_type = (stored_token_expired.get("token_type") or "bearer").lower()
            if token_type == "bearer":
                # OAuth token expired - try automatic refresh using persistent cache (like Azure CLI)
                refreshed_token = self._try_refresh_oauth_token()
                if refreshed_token:
                    self.api_token = refreshed_token.get("access_token")
                    self.auth_scheme = "bearer"
                    # Update stored token with refreshed token
                    set_token("azure-devops", refreshed_token)
                    debug_print(f"[dim]OAuth token automatically refreshed (was expired at {expires_at})[/dim]")
                else:
                    # Refresh failed - provide helpful guidance
                    console.print(
                        f"[yellow]⚠[/yellow] Stored OAuth token expired at {expires_at}. "
                        "Attempting automatic refresh..."
                    )
                    console.print("[yellow]⚠[/yellow] Automatic refresh failed. OAuth tokens expire after ~1 hour.")
                    console.print(
                        "[dim]Options:[/dim]\n"
                        "  1. Use a Personal Access Token (PAT) with longer expiration (up to 1 year):\n"
                        "     - Create PAT: https://dev.azure.com/{org}/_usersSettings/tokens\n"
                        "     - Store PAT: specfact auth azure-devops --pat your_pat_token\n"
                        "  2. Re-authenticate: specfact auth azure-devops\n"
                        "  3. Use --ado-token option with a valid token"
                    )
                    self.api_token = None
                    self.auth_scheme = None
            else:
                # PAT token - no expiration tracking, assume still valid
                self.api_token = stored_token_expired.get("access_token")
                self.auth_scheme = "basic"
        else:
            self.api_token = None
            self.auth_scheme = None

        # Base URL defaults to Azure DevOps Services (cloud)
        # Normalize base_url: remove trailing slashes
        # Note: For Azure DevOps Services (cloud), base_url should be "https://dev.azure.com"
        # For Azure DevOps Server (on-premise), base_url might be "https://server" or "https://server/collection"
        raw_base_url = base_url or "https://dev.azure.com"
        self.base_url = raw_base_url.rstrip("/")
        self.work_item_type = work_item_type

    def _is_on_premise(self) -> bool:
        """
        Detect if this is Azure DevOps Server (on-premise) vs Azure DevOps Services (cloud).

        Returns:
            True if on-premise (base_url doesn't contain dev.azure.com), False if cloud
        """
        return "dev.azure.com" not in self.base_url.lower()

    def _build_ado_url(self, path: str, api_version: str = "7.1") -> str:
        """
        Build Azure DevOps API URL with proper formatting.

        Supports both:
        - Azure DevOps Services (cloud): https://dev.azure.com/{org}/{project}/_apis/...
        - Azure DevOps Server (on-premise): https://{server}/tfs/{collection}/{project}/_apis/...
                                          or https://{server}/{collection}/{project}/_apis/...

        Args:
            path: API path (e.g., "_apis/wit/workitems", "_apis/wit/wiql")
            api_version: API version (default: "7.1")

        Returns:
            Full URL with proper format based on cloud vs on-premise

        Note:
            For project-based permissions in larger organizations, org must be part of the
            _apis URL path before the project. This ensures proper permission scoping.
            Format: {base_url}/{org}/{project}/_apis/...
        """
        if not self.project:
            raise ValueError(f"project required to build ADO URL (project={self.project!r})")

        # Normalize base_url (remove trailing slashes)
        base_url_normalized = self.base_url.rstrip("/")

        # Normalize path (remove leading slashes)
        path_normalized = path.lstrip("/")

        is_on_premise = self._is_on_premise()

        if is_on_premise:
            # Azure DevOps Server (on-premise)
            # Format could be:
            # - https://server/tfs/collection/{project}/_apis/... (older TFS format)
            # - https://server/collection/{project}/_apis/... (newer format)
            # - https://server/{project}/_apis/... (if collection in base_url)

            base_lower = base_url_normalized.lower()
            has_tfs = "/tfs/" in base_lower

            # Check if base_url already includes a collection path
            # If base_url contains /tfs/ or has more than just protocol + domain, collection is likely included
            parts = [p for p in base_url_normalized.rstrip("/").split("/") if p and p not in ["http:", "https:"]]
            # Collection is in base_url if:
            # 1. It contains /tfs/ (older TFS format: server/tfs/collection)
            # 2. It has more than 1 part after protocol (e.g., server/collection)
            has_collection_in_base = has_tfs or len(parts) > 1

            if has_collection_in_base:
                # Collection already in base_url, but for project-based permissions, we still need org in path
                # Include org before project to ensure proper permission scoping
                if self.org:
                    url = f"{base_url_normalized}/{self.org}/{self.project}/{path_normalized}?api-version={api_version}"
                else:
                    # Fallback: if org not provided but collection in base_url, use project directly
                    console.print(
                        "[yellow]Warning:[/yellow] Collection in base_url but org not provided. Using project directly."
                    )
                    url = f"{base_url_normalized}/{self.project}/{path_normalized}?api-version={api_version}"
            elif self.org:
                # Collection not in base_url, need to add it
                # For on-premise, typically use /tfs/{collection} format unless explicitly newer format
                # But if base_url doesn't have /tfs/, use newer format
                if "/tfs" in base_url_normalized.lower() or not has_tfs:
                    # If base_url mentions tfs anywhere or we're not sure, use /tfs/ format
                    # Actually, if has_tfs is False, we should use newer format
                    url = f"{base_url_normalized}/{self.org}/{self.project}/{path_normalized}?api-version={api_version}"
                else:
                    # Use /tfs/ format for older TFS servers
                    url = f"{base_url_normalized}/tfs/{self.org}/{self.project}/{path_normalized}?api-version={api_version}"
            else:
                # No org provided, assume collection is in base_url or use project directly
                console.print(
                    "[yellow]Warning:[/yellow] On-premise detected but org (collection) not provided. Assuming collection is in base_url."
                )
                url = f"{base_url_normalized}/{self.project}/{path_normalized}?api-version={api_version}"
        else:
            # Azure DevOps Services (cloud)
            # Format: https://dev.azure.com/{org}/{project}/_apis/...
            if not self.org:
                raise ValueError(f"org required for Azure DevOps Services (cloud) (org={self.org!r})")
            url = f"{base_url_normalized}/{self.org}/{self.project}/{path_normalized}?api-version={api_version}"

        return url

    # BacklogAdapterMixin abstract method implementations

    @beartype
    @require(lambda status: isinstance(status, str) and len(status) > 0, "Status must be non-empty string")
    @ensure(lambda result: isinstance(result, str) and len(result) > 0, "Must return non-empty status string")
    def map_backlog_status_to_openspec(self, status: str) -> str:
        """
        Map ADO work item state to OpenSpec change status.

        Args:
            status: ADO work item state (e.g., "New", "Active", "Closed", "Removed", "Rejected")

        Returns:
            OpenSpec change status (proposed, in-progress, applied, deprecated, discarded)

        Note:
            This implements the tool-agnostic status mapping pattern for Azure DevOps.
        """
        status_lower = status.lower()

        # Map ADO states to OpenSpec status
        if status_lower in ("new", "proposed"):
            return "proposed"
        if status_lower in ("active", "in progress", "in-progress", "committed"):
            return "in-progress"
        if status_lower in ("closed", "done", "completed", "resolved"):
            return "applied"
        if status_lower in ("removed", "deprecated"):
            return "deprecated"
        if status_lower in ("rejected", "discarded"):
            return "discarded"

        # Default: treat as proposed
        return "proposed"

    @beartype
    @require(lambda status: isinstance(status, str) and len(status) > 0, "Status must be non-empty string")
    @ensure(lambda result: isinstance(result, str), "Must return status string")
    def map_openspec_status_to_backlog(self, status: str) -> str:
        """
        Map OpenSpec change status to ADO work item state.

        Args:
            status: OpenSpec change status (proposed, in-progress, applied, deprecated, discarded)

        Returns:
            ADO work item state string

        Note:
            This implements the tool-agnostic status mapping pattern for Azure DevOps.
        """
        if status == "proposed":
            return "New"
        if status == "in-progress":
            return "Active"
        if status == "applied":
            return "Closed"
        if status == "deprecated":
            return "Removed"
        if status == "discarded":
            return "Rejected"

        # Default: New
        return "New"

    def _normalize_description(self, fields: dict[str, Any]) -> str:
        """
        Normalize ADO description field to markdown.

        Args:
            fields: ADO work item fields dict

        Returns:
            Markdown-formatted description string
        """
        description_raw = fields.get("System.Description", "") or ""
        if description_raw and ("<" in description_raw and ">" in description_raw):
            description_raw = self._html_to_markdown(description_raw)
        if description_raw:
            import html

            description_raw = html.unescape(description_raw)
        return description_raw

    @beartype
    @require(lambda item_data: isinstance(item_data, dict), "Item data must be dict")
    @ensure(lambda result: isinstance(result, dict), "Must return dict with extracted fields")
    def extract_change_proposal_data(self, item_data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract change proposal data from ADO work item.

        Parses ADO work item fields to extract:
        - Title (from System.Title)
        - Description (from System.Description)
        - Rationale (from Why section in description)
        - Other optional fields (timeline, owner, stakeholders, dependencies)

        Args:
            item_data: ADO work item data (dict from API response)

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
            This implements the tool-agnostic metadata extraction pattern for Azure DevOps.
            Future backlog adapters should implement similar parsing for their tools.

            Change ID extraction priority:
            1. Description footer (legacy format): *OpenSpec Change Proposal: `id`*
            2. Comments (new format): **Change ID**: `id` in OpenSpec Change Proposal Reference comment
            3. Work item ID (fallback)
        """
        if not isinstance(item_data, dict):
            msg = "ADO work item data must be dict"
            raise ValueError(msg)

        # Extract fields from ADO work item
        fields = item_data.get("fields", {})
        if not fields:
            msg = "ADO work item must have fields"
            raise ValueError(msg)

        # Extract title
        title = fields.get("System.Title", "Untitled Change Proposal")
        if not title:
            msg = "ADO work item must have System.Title"
            raise ValueError(msg)

        # Extract description (normalize HTML → Markdown if needed)
        description_raw = self._normalize_description(fields)

        description = ""
        rationale = ""
        impact = ""

        import re

        # Parse markdown sections (Why, What Changes)
        if description_raw:
            # Extract "Why" section (stop at What Changes or OpenSpec footer)
            why_match = re.search(
                r"##\s+Why\s*\n(.*?)(?=\n##\s+What\s+Changes\s|\n##\s+Impact\s|\n---\s*\n\*OpenSpec Change Proposal:|\Z)",
                description_raw,
                re.DOTALL | re.IGNORECASE,
            )
            if why_match:
                rationale = why_match.group(1).strip()

            # Extract "What Changes" section (stop at OpenSpec footer)
            what_match = re.search(
                r"##\s+What\s+Changes\s*\n(.*?)(?=\n##\s+Impact\s|\n---\s*\n\*OpenSpec Change Proposal:|\Z)",
                description_raw,
                re.DOTALL | re.IGNORECASE,
            )
            if what_match:
                description = what_match.group(1).strip()
            elif not why_match:
                # If no sections found, use entire description (but remove footer)
                body_clean = re.sub(r"\n---\s*\n\*OpenSpec Change Proposal:.*", "", description_raw, flags=re.DOTALL)
                description = body_clean.strip()

            impact_match = re.search(
                r"##\s+Impact\s*\n(.*?)(?=\n---\s*\n\*OpenSpec Change Proposal:|\Z)",
                description_raw,
                re.DOTALL | re.IGNORECASE,
            )
            if impact_match:
                impact = impact_match.group(1).strip()

        # Extract change ID from OpenSpec metadata footer, comments, or work item ID
        change_id = None

        # First, check description for OpenSpec metadata footer (legacy format)
        if description_raw:
            # Look for OpenSpec metadata footer: *OpenSpec Change Proposal: `{change_id}`*
            change_id_match = re.search(r"OpenSpec Change Proposal:\s*`([^`]+)`", description_raw, re.IGNORECASE)
            if change_id_match:
                change_id = change_id_match.group(1)

        # If not found in description, check comments (new format - OpenSpec info in comments)
        if not change_id:
            work_item_id = item_data.get("id")
            if work_item_id and self.org and self.project:
                comments = self._get_work_item_comments(self.org, self.project, work_item_id)
                # Look for OpenSpec Change Proposal Reference comment
                openspec_patterns = [
                    r"\*\*Change ID\*\*[:\s]+`([a-z0-9-]+)`",
                    r"Change ID[:\s]+`([a-z0-9-]+)`",
                    r"OpenSpec Change Proposal[:\s]+`?([a-z0-9-]+)`?",
                    r"\*OpenSpec Change Proposal:\s*`([a-z0-9-]+)`",
                ]
                for comment in comments:
                    comment_text = comment.get("text", "") or comment.get("body", "")
                    for pattern in openspec_patterns:
                        match = re.search(pattern, comment_text, re.IGNORECASE | re.DOTALL)
                        if match:
                            change_id = match.group(1)
                            break
                    if change_id:
                        break

        # Fallback to work item ID if still not found
        if not change_id:
            change_id = str(item_data.get("id", "unknown"))

        # Extract status from System.State
        ado_state = fields.get("System.State", "New")
        status = self.map_backlog_status_to_openspec(ado_state)

        # Extract created_at timestamp
        created_at = fields.get("System.CreatedDate")
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
        timeline = None
        owner = None
        stakeholders = []
        dependencies = []

        # Try to extract from description sections
        if description_raw:
            # Extract "When" section (timeline)
            when_match = re.search(r"##\s+When\s*\n(.*?)(?=\n##|\Z)", description_raw, re.DOTALL | re.IGNORECASE)
            if when_match:
                timeline = when_match.group(1).strip()

            # Extract "Who" section (owner, stakeholders)
            who_match = re.search(r"##\s+Who\s*\n(.*?)(?=\n##|\Z)", description_raw, re.DOTALL | re.IGNORECASE)
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
        assigned_to = fields.get("System.AssignedTo")
        if assigned_to:
            if isinstance(assigned_to, dict):
                assignee_name = assigned_to.get("displayName") or assigned_to.get("uniqueName", "")
            else:
                assignee_name = str(assigned_to)
            if assignee_name and not owner:
                owner = assignee_name
            if assignee_name:
                stakeholders.append(assignee_name)

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
        Detect if this is an Azure DevOps repository.

        Args:
            repo_path: Path to repository root
            bridge_config: Optional bridge configuration (for cross-repo detection)

        Returns:
            True if Azure DevOps repository detected, False otherwise
        """
        # Check bridge config for external ADO repo
        return bool(bridge_config and bridge_config.adapter.value == "ado")

    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    @ensure(lambda result: isinstance(result, ToolCapabilities), "Must return ToolCapabilities")
    def get_capabilities(self, repo_path: Path, bridge_config: BridgeConfig | None = None) -> ToolCapabilities:
        """
        Get Azure DevOps adapter capabilities.

        Args:
            repo_path: Path to repository root
            bridge_config: Optional bridge configuration (for cross-repo detection)

        Returns:
            ToolCapabilities instance for Azure DevOps adapter
        """
        return ToolCapabilities(
            tool="ado",
            version=None,  # ADO version not applicable
            layout="api",  # Azure DevOps uses API-based integration
            specs_dir="",  # Not applicable for Azure DevOps
            has_external_config=True,  # Uses API tokens
            has_custom_hooks=False,
            supported_sync_modes=[
                "bidirectional",
                "export-only",
            ],  # Azure DevOps adapter: bidirectional sync (OpenSpec ↔ ADO Work Items) and export-only for change proposals
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
        Import artifact from Azure DevOps.

        Supports importing ADO work items as OpenSpec change proposals.

        Args:
            artifact_key: Artifact key ("ado_work_item" for importing work items)
            artifact_path: ADO work item data (dict from API response)
            project_bundle: Project bundle to update
            bridge_config: Bridge configuration (may contain external_base_path for cross-repo support)

        Raises:
            ValueError: If artifact_key is not "ado_work_item" or if required data is missing
            NotImplementedError: If artifact_key is not supported

        Note:
            This method implements the backlog adapter import pattern.
        """
        if artifact_key != "ado_work_item":
            msg = f"Unsupported artifact key for import: {artifact_key}. Supported: ado_work_item"
            raise NotImplementedError(msg)

        if not isinstance(artifact_path, dict):
            msg = "ADO work item import requires dict (API response), not Path"
            raise ValueError(msg)

        # Check bridge_config.external_base_path for cross-repo support
        if bridge_config and bridge_config.external_base_path:
            # Cross-repo import: use external_base_path for OpenSpec repository
            pass  # Path operations will respect external_base_path in OpenSpec adapter

        # Import ADO work item as change proposal using backlog adapter pattern
        proposal = self.import_backlog_item_as_proposal(artifact_path, "ado", bridge_config)

        if not proposal:
            msg = "Failed to import ADO work item as change proposal"
            raise ValueError(msg)

        # Enhance source_tracking with ADO-specific metadata
        if proposal.source_tracking and isinstance(proposal.source_tracking.source_metadata, dict):
            fields = artifact_path.get("fields", {})
            # Add ADO-specific metadata to source_metadata
            proposal.source_tracking.source_metadata.update(
                {
                    "org": self.org or "",
                    "project": self.project or "",
                    "work_item_type": fields.get("System.WorkItemType", ""),
                    "state": fields.get("System.State", ""),
                }
            )
            # Also update source_state if not already set
            if "source_state" not in proposal.source_tracking.source_metadata:
                proposal.source_tracking.source_metadata["source_state"] = fields.get("System.State", "")

            raw_title = fields.get("System.Title", "") or ""
            raw_body = self._normalize_description(fields)
            proposal.source_tracking.source_metadata["raw_title"] = raw_title
            proposal.source_tracking.source_metadata["raw_body"] = raw_body
            proposal.source_tracking.source_metadata["raw_format"] = "markdown"
            proposal.source_tracking.source_metadata.setdefault("source_type", "ado")

            source_repo = ""
            if self.org and self.project:
                source_repo = f"{self.org}/{self.project}"
                proposal.source_tracking.source_metadata.setdefault("source_repo", source_repo)

            entry_id = artifact_path.get("id")
            entry = {
                "source_id": str(entry_id) if entry_id is not None else None,
                "source_url": artifact_path.get("_links", {}).get("html", {}).get("href", ""),
                "source_type": "ado",
                "source_repo": source_repo,
                "source_metadata": {"last_synced_status": proposal.status},
            }
            entries = proposal.source_tracking.source_metadata.get("backlog_entries")
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
                proposal.source_tracking.source_metadata["backlog_entries"] = entries

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
    @ensure(lambda result: isinstance(result, dict), "Must return dict with work item data")
    def export_artifact(
        self,
        artifact_key: str,
        artifact_data: Any,  # ChangeProposal - TODO: use proper type when dependency implemented
        bridge_config: BridgeConfig | None = None,
    ) -> dict[str, Any]:
        """
        Export artifact to Azure DevOps (create or update work item).

        Args:
            artifact_key: Artifact key ("change_proposal" or "change_status")
            artifact_data: Change proposal data (dict for now, ChangeProposal type when dependency implemented)
            bridge_config: Bridge configuration (may contain org, project)

        Returns:
            Dict with work item data: {"work_item_id": int, "work_item_url": str, "state": str}

        Raises:
            ValueError: If required configuration is missing
            requests.RequestException: If Azure DevOps API call fails
        """
        import re as _re

        if not self.api_token:
            msg = (
                "Azure DevOps API token required. Options:\n"
                "  1. Set AZURE_DEVOPS_TOKEN environment variable\n"
                "  2. Provide via --ado-token option\n"
                "  3. Run `specfact auth azure-devops` for device code authentication"
            )
            raise ValueError(msg)

        # Resolve organization/project from instance (not stored in bridge_config for security)
        org = self.org
        project = self.project

        if not org or not project:
            msg = (
                "Azure DevOps organization and project required. "
                "Provide via --ado-org and --ado-project or bridge config"
            )
            raise ValueError(msg)

        if artifact_key == "change_proposal":
            return self._create_work_item_from_proposal(artifact_data, org, project)
        if artifact_key == "change_status":
            return self._update_work_item_status(artifact_data, org, project)
        if artifact_key == "change_proposal_update":
            # Extract work item ID from source_tracking (support list or dict for backward compatibility)
            # Use three-level matching to handle ADO URL GUIDs and project name differences
            source_tracking = artifact_data.get("source_tracking", {})
            work_item_id = None
            target_repo = f"{org}/{project}"

            # Handle list of entries (multi-repository support)
            if isinstance(source_tracking, list):
                # Find entry for this repository using three-level matching
                for entry in source_tracking:
                    if not isinstance(entry, dict):
                        continue

                    entry_repo = entry.get("source_repo")
                    entry_type = entry.get("source_type", "").lower()

                    # Primary match: exact source_repo match
                    if entry_repo == target_repo:
                        work_item_id = entry.get("source_id")
                        break

                    # Secondary match: extract from source_url if source_repo not set
                    if not entry_repo:
                        source_url = entry.get("source_url", "")
                        # Try ADO URL pattern - match by org (GUIDs in URLs)
                        if source_url and "/" in target_repo:
                            try:
                                parsed = urlparse(source_url)
                                if parsed.hostname and parsed.hostname.lower() == "dev.azure.com":
                                    target_org = target_repo.split("/")[0]
                                    ado_org_match = _re.search(r"dev\.azure\.com/([^/]+)/", source_url)
                                    if ado_org_match and ado_org_match.group(1) == target_org:
                                        # Org matches - this is likely the same ADO organization
                                        work_item_id = entry.get("source_id")
                                        break
                            except Exception:
                                pass

                    # Tertiary match: for ADO, only match by org when project is truly unknown (GUID-only URLs)
                    # This prevents cross-project matches when both entry_repo and target_repo have project names
                    if entry_repo and target_repo and entry_type == "ado":
                        entry_org = entry_repo.split("/")[0] if "/" in entry_repo else None
                        target_org = target_repo.split("/")[0] if "/" in target_repo else None
                        entry_project = entry_repo.split("/", 1)[1] if "/" in entry_repo else None
                        target_project = target_repo.split("/", 1)[1] if "/" in target_repo else None

                        # Only use org-only match when:
                        # 1. Org matches
                        # 2. source_id exists
                        # 3. AND (project is unknown in entry OR project is unknown in target OR both contain GUIDs)
                        # This prevents matching org/project-a with org/project-b when both have known project names
                        source_url = entry.get("source_url", "")
                        entry_has_guid = source_url and _re.search(
                            r"dev\.azure\.com/[^/]+/[0-9a-f-]{36}", source_url, _re.IGNORECASE
                        )
                        project_unknown = (
                            not entry_project  # Entry has no project part
                            or not target_project  # Target has no project part
                            or entry_has_guid  # Entry URL contains GUID (project name unknown)
                            or (
                                entry_project and len(entry_project) == 36 and "-" in entry_project
                            )  # Entry project is a GUID
                            or (
                                target_project and len(target_project) == 36 and "-" in target_project
                            )  # Target project is a GUID
                        )

                        if (
                            entry_org
                            and target_org
                            and entry_org == target_org
                            and entry.get("source_id")
                            and project_unknown
                        ):
                            work_item_id = entry.get("source_id")
                            break

            # Handle single dict (backward compatibility)
            elif isinstance(source_tracking, dict):
                work_item_id = source_tracking.get("source_id")

            if not work_item_id:
                msg = (
                    f"Work item ID required for content update (missing in source_tracking for repository {target_repo}). "
                    "Work item must be created first."
                )
                raise ValueError(msg)

            # Ensure work_item_id is an integer for API call
            if isinstance(work_item_id, str):
                try:
                    work_item_id = int(work_item_id)
                except ValueError:
                    msg = f"Invalid work item ID format: {work_item_id}"
                    raise ValueError(msg) from None

            return self._update_work_item_body(artifact_data, org, project, work_item_id)
        if artifact_key == "change_proposal_comment":
            # Add comment only (no body/state update) - used for adding status info to work items
            source_tracking = artifact_data.get("source_tracking", {})
            work_item_id = None

            # Handle list of entries (multi-repository support)
            if isinstance(source_tracking, list):
                target_repo = f"{org}/{project}"
                for entry in source_tracking:
                    if isinstance(entry, dict):
                        entry_repo = entry.get("source_repo")
                        if entry_repo == target_repo:
                            work_item_id = entry.get("source_id")
                            break
                        if not entry_repo:
                            source_url = entry.get("source_url", "")
                            if source_url and target_repo in source_url:
                                work_item_id = entry.get("source_id")
                                break
            elif isinstance(source_tracking, dict):
                work_item_id = source_tracking.get("source_id")

            if not work_item_id:
                msg = "Work item ID required for comment (missing in source_tracking for this repository)"
                raise ValueError(msg)

            # Ensure work_item_id is an integer for API call
            if isinstance(work_item_id, str):
                try:
                    work_item_id = int(work_item_id)
                except ValueError:
                    msg = f"Invalid work item ID format: {work_item_id}"
                    raise ValueError(msg) from None

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
                self._add_work_item_comment(org, project, work_item_id, comment_note)
            return {
                "work_item_id": work_item_id,
                "comment_added": True,
            }
        if artifact_key == "code_change_progress":
            # Extract work item ID from source_tracking (support list or dict for backward compatibility)
            source_tracking = artifact_data.get("source_tracking", {})
            work_item_id = None

            # Handle list of entries (multi-repository support)
            if isinstance(source_tracking, list):
                # Find entry for this repository
                target_repo = f"{org}/{project}"
                for entry in source_tracking:
                    if isinstance(entry, dict):
                        entry_repo = entry.get("source_repo")
                        if entry_repo == target_repo:
                            work_item_id = entry.get("source_id")
                            break
                        # Backward compatibility: if no source_repo, try to extract from source_url
                        if not entry_repo:
                            source_url = entry.get("source_url", "")
                            if source_url and target_repo in source_url:
                                work_item_id = entry.get("source_id")
                                break
            # Handle single dict (backward compatibility)
            elif isinstance(source_tracking, dict):
                work_item_id = source_tracking.get("source_id")

            if not work_item_id:
                msg = "Work item ID required for progress comment (missing in source_tracking for this repository)"
                raise ValueError(msg)

            # Ensure work_item_id is an integer for API call
            if isinstance(work_item_id, str):
                try:
                    work_item_id = int(work_item_id)
                except ValueError:
                    msg = f"Invalid work item ID format: {work_item_id}"
                    raise ValueError(msg) from None

            # Extract sanitize flag from artifact_data or bridge_config
            sanitize = artifact_data.get("sanitize", False)
            if bridge_config and hasattr(bridge_config, "sanitize"):
                sanitize = bridge_config.sanitize if bridge_config.sanitize is not None else sanitize

            return self._add_progress_comment(artifact_data, org, project, work_item_id, sanitize=sanitize)
        msg = (
            f"Unsupported artifact key: {artifact_key}. "
            "Supported: change_proposal, change_status, change_proposal_update, change_proposal_comment, code_change_progress"
        )
        raise ValueError(msg)

    @beartype
    @require(lambda item_ref: isinstance(item_ref, str) and len(item_ref) > 0, "Item reference must be non-empty")
    @ensure(lambda result: isinstance(result, dict), "Must return dict with work item data")
    def fetch_backlog_item(self, item_ref: str) -> dict[str, Any]:
        """
        Fetch ADO work item data by ID or URL.

        Args:
            item_ref: Work item ID or URL

        Returns:
            Work item data dict from Azure DevOps API
        """
        org, project, work_item_id = self._parse_work_item_reference(item_ref)
        work_item_data = self._get_work_item_data(work_item_id, org, project)
        if not work_item_data:
            msg = f"Work item not found: {item_ref}"
            raise ValueError(msg)
        return work_item_data

    @beartype
    @require(lambda item_ref: isinstance(item_ref, str) and len(item_ref) > 0, "Item reference must be non-empty")
    @ensure(lambda result: isinstance(result, tuple) and len(result) == 3, "Must return org, project, work item ID")
    def _parse_work_item_reference(self, item_ref: str) -> tuple[str, str, int]:
        """
        Parse work item reference into org, project, and ID.

        Args:
            item_ref: Work item ID or URL

        Returns:
            Tuple of (org, project, work_item_id)
        """
        import re as _re

        cleaned = item_ref.strip().lstrip("#")
        url_match = _re.search(r"dev\.azure\.com/([^/]+)/([^/]+)/.*?/(\d+)", cleaned, _re.IGNORECASE)
        if url_match:
            return url_match.group(1), url_match.group(2), int(url_match.group(3))

        if cleaned.isdigit():
            if not self.org or not self.project:
                msg = "org and project required when work item reference is numeric"
                raise ValueError(msg)
            return self.org, self.project, int(cleaned)

        msg = f"Unsupported ADO work item reference format: {item_ref}"
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
        Generate bridge configuration for Azure DevOps adapter.

        Args:
            repo_path: Path to repository root

        Returns:
            BridgeConfig instance for Azure DevOps adapter
        """
        from specfact_cli.models.bridge import BridgeConfig

        return BridgeConfig.preset_ado()

    @beartype
    @require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
    @require(lambda bundle_dir: bundle_dir.exists(), "Bundle directory must exist")
    @ensure(lambda result: result is None, "Azure DevOps adapter does not support change tracking loading")
    def load_change_tracking(
        self, bundle_dir: Path, bridge_config: BridgeConfig | None = None
    ) -> ChangeTracking | None:
        """
        Load change tracking (not supported by Azure DevOps adapter).

        Azure DevOps adapter uses `import_artifact` with artifact_key="ado_work_item" to
        import individual work items as change proposals. Use that method instead.

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
        Save change tracking (not supported by Azure DevOps adapter).

        Azure DevOps adapter uses `export_artifact` to sync individual proposals to ADO
        work items. Use that method instead.

        Args:
            bundle_dir: Path to bundle directory
            change_tracking: ChangeTracking instance to save
            bridge_config: Optional bridge configuration
        """
        # Not supported - Azure DevOps adapter uses export_artifact for individual proposals

    @beartype
    @require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
    @require(lambda bundle_dir: bundle_dir.exists(), "Bundle directory must exist")
    @require(lambda change_name: isinstance(change_name, str) and len(change_name) > 0, "Change name must be non-empty")
    @ensure(lambda result: result is None, "Azure DevOps adapter does not support change proposal loading")
    def load_change_proposal(
        self, bundle_dir: Path, change_name: str, bridge_config: BridgeConfig | None = None
    ) -> ChangeProposal | None:
        """
        Load change proposal (not supported by Azure DevOps adapter).

        Azure DevOps adapter uses `import_artifact` with artifact_key="ado_work_item" to
        import work items as change proposals. Use that method instead.

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
        Save change proposal (not supported by Azure DevOps adapter).

        Azure DevOps adapter uses `export_artifact` and `import_artifact` for bidirectional
        sync. Use `export_artifact` with artifact_key="change_proposal" to create
        ADO work items, or `import_artifact` with artifact_key="ado_work_item" to
        import work items as change proposals.

        Args:
            bundle_dir: Path to bundle directory
            proposal: ChangeProposal instance to save
            bridge_config: Optional bridge configuration
        """
        # Not supported - Azure DevOps adapter uses export_artifact/import_artifact for sync
        # Use export_artifact(artifact_key="change_proposal", ...) to create ADO work items

    def _get_work_item_type(self, org: str, project: str) -> str:
        """
        Get default work item type for the project.

        Derives work item type from process template (Scrum/Kanban/Agile) or uses override.

        Args:
            org: Azure DevOps organization
            project: Azure DevOps project

        Returns:
            Work item type string (e.g., "Product Backlog Item", "User Story")
        """
        # If work item type is explicitly provided, use it
        if self.work_item_type:
            return self.work_item_type

        # Try to derive from process template
        try:
            # Ensure API token is available
            if not self.api_token:
                # Can't derive from process template without token, use default
                return "User Story"

            # Get process template from project
            url = f"{self.base_url}/{org}/_apis/projects/{project}?api-version=7.1"
            headers = {
                "Content-Type": "application/json",
                **self._auth_headers(),
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            project_data = response.json()

            # Get process template ID
            process_template_id = project_data.get("processTemplate", {}).get("templateTypeId")
            if process_template_id:
                # Map template ID to work item type
                # Scrum template ID: 6b724908-ef14-45cf-84f8-768b5384da45
                # Agile template ID: adcc42ab-9882-485e-a3e4-38fb9b8c5e4e
                # Kanban template ID: 27450541-8e31-4150-ab7e-3f4854565ce3
                template_id_str = str(process_template_id).lower()
                # Check for Scrum template (exact match or contains scrum)
                if "6b724908" in template_id_str or "scrum" in template_id_str:
                    return "Product Backlog Item"
                # Default to User Story for Agile/Kanban
                return "User Story"
        except Exception:
            # If we can't determine, default to User Story
            pass

        # Default: User Story (works for Agile and Kanban)
        return "User Story"

    def _html_to_markdown(self, html_content: str) -> str:
        """
        Convert basic HTML to markdown for ADO work items.

        This is a simple converter for common HTML patterns. For full HTML-to-markdown
        conversion, consider using a library like html2text or markdownify.

        Args:
            html_content: HTML content from ADO work item

        Returns:
            Markdown-formatted content
        """
        # Simple HTML-to-markdown conversion for common patterns
        # Replace common HTML tags with markdown equivalents
        import html
        import re

        # Remove HTML comments
        html_content = re.sub(r"<!--.*?-->", "", html_content, flags=re.DOTALL)

        # Convert headings (h1-h6)
        def replace_heading(match: re.Match) -> str:
            level = int(match.group(1))
            content = match.group(2)
            return f"\n{'#' * level} {content}\n"

        html_content = re.sub(
            r"<h([1-6])[^>]*>(.*?)</h[1-6]>",
            replace_heading,
            html_content,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # Convert bold
        html_content = re.sub(r"<strong>(.*?)</strong>", r"**\1**", html_content, flags=re.DOTALL)
        html_content = re.sub(r"<b>(.*?)</b>", r"**\1**", html_content, flags=re.DOTALL)

        # Convert italic
        html_content = re.sub(r"<em>(.*?)</em>", r"*\1*", html_content, flags=re.DOTALL)
        html_content = re.sub(r"<i>(.*?)</i>", r"*\1*", html_content, flags=re.DOTALL)

        # Convert code blocks
        html_content = re.sub(r"<pre><code>(.*?)</code></pre>", r"```\n\1\n```", html_content, flags=re.DOTALL)
        html_content = re.sub(r"<code>(.*?)</code>", r"`\1`", html_content, flags=re.DOTALL)

        # Convert links
        html_content = re.sub(r'<a href="([^"]+)">(.*?)</a>', r"[\2](\1)", html_content, flags=re.DOTALL)

        # Convert lists (basic support)
        html_content = re.sub(r"<li>(.*?)</li>", r"- \1", html_content, flags=re.DOTALL)
        html_content = re.sub(r"<ul>|</ul>|<ol>|</ol>", "", html_content)

        # Convert paragraphs
        html_content = re.sub(r"<p>(.*?)</p>", r"\1\n\n", html_content, flags=re.DOTALL)

        # Convert line breaks
        html_content = re.sub(r"<br\s*/?>", "\n", html_content)

        # Remove remaining HTML tags
        html_content = re.sub(r"<[^>]+>", "", html_content)

        # Clean up extra whitespace
        html_content = re.sub(r"\n{3,}", "\n\n", html_content)

        return html.unescape(html_content.strip())

    def _encode_pat(self, token: str) -> str:
        """
        Encode PAT for Basic authentication.

        Args:
            token: Azure DevOps PAT

        Returns:
            Base64-encoded token for Basic auth
        """
        import base64

        return base64.b64encode(f":{token}".encode()).decode()

    def _try_refresh_oauth_token(self) -> dict[str, Any] | None:
        """
        Attempt to refresh expired OAuth token using persistent token cache.

        This uses the same persistent cache as the auth command, allowing automatic
        token refresh without user interaction (like Azure CLI).

        Returns:
            Refreshed token data dict if successful, None if refresh failed
        """
        try:
            from azure.identity import (  # type: ignore[reportMissingImports]
                DeviceCodeCredential,
                TokenCachePersistenceOptions,
            )

            # Use the same cache name as auth command for shared cache
            # Try encrypted first, fall back to unencrypted if libsecret unavailable
            cache_options = None
            try:
                try:
                    cache_options = TokenCachePersistenceOptions(
                        name="specfact-azure-devops",
                        allow_unencrypted_storage=False,  # Prefer encrypted
                    )
                except Exception:
                    # Encrypted cache not available, try unencrypted
                    cache_options = TokenCachePersistenceOptions(
                        name="specfact-azure-devops",
                        allow_unencrypted_storage=True,  # Fallback: unencrypted
                    )
            except Exception:
                # Persistent cache completely unavailable, can't refresh
                return None

            # Create credential with same cache - it will use cached refresh token
            credential = DeviceCodeCredential(cache_persistence_options=cache_options)
            # Use the same resource and scopes as auth command
            # Note: Refresh tokens are automatically obtained via persistent token cache
            # offline_access is a reserved scope and cannot be explicitly requested
            azure_devops_resource = "499b84ac-1321-427f-aa17-267ca6975798/.default"
            azure_devops_scopes = [azure_devops_resource]
            token = credential.get_token(*azure_devops_scopes)

            # Return refreshed token data
            from datetime import UTC, datetime

            expires_at = datetime.fromtimestamp(token.expires_on, tz=UTC).isoformat()
            return {
                "access_token": token.token,
                "token_type": "bearer",
                "expires_at": expires_at,
                "resource": azure_devops_resource,
                "issued_at": datetime.now(tz=UTC).isoformat(),
            }
        except Exception:
            # Refresh failed (no cached refresh token, refresh token expired, etc.)
            return None

    def _auth_headers(self) -> dict[str, str]:
        """Return authorization headers based on token type."""
        if not self.api_token:
            return {}
        if self.auth_scheme == "bearer":
            return {"Authorization": f"Bearer {self.api_token}"}
        return {"Authorization": f"Basic {self._encode_pat(self.api_token)}"}

    def _work_item_exists(self, work_item_id: int | str, org: str, project: str) -> bool:
        """
        Check if a work item exists in Azure DevOps.

        Args:
            work_item_id: Work item ID to check
            org: Azure DevOps organization
            project: Azure DevOps project

        Returns:
            True if work item exists, False otherwise (including if deleted)
        """
        if not self.api_token:
            return False

        # Ensure work_item_id is an integer
        if isinstance(work_item_id, str):
            try:
                work_item_id = int(work_item_id)
            except ValueError:
                return False

        url = f"{self.base_url}/{org}/{project}/_apis/wit/workitems/{work_item_id}?api-version=7.1"
        headers = {
            "Accept": "application/json",
            **self._auth_headers(),
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            # 200 = exists, 404 = doesn't exist (including deleted)
            if response.status_code == 200:
                # Check if work item is deleted (System.State == "Removed")
                work_item_data = response.json()
                fields = work_item_data.get("fields", {})
                state = fields.get("System.State", "")
                # Consider "Removed" as non-existent for our purposes
                return state != "Removed"
            return False
        except requests.RequestException:
            # On any error, assume it doesn't exist (safer to allow creation)
            return False

    def _get_work_item_data(self, work_item_id: int | str, org: str, project: str) -> dict[str, Any] | None:
        """
        Get current work item data from Azure DevOps.

        Args:
            work_item_id: Work item ID to fetch
            org: Azure DevOps organization
            project: Azure DevOps project

        Returns:
            Work item data dict with fields (title, state, etc.) or None if not found
        """
        if not self.api_token:
            return None

        # Ensure work_item_id is an integer
        if isinstance(work_item_id, str):
            try:
                work_item_id = int(work_item_id)
            except ValueError:
                return None

        url = f"{self.base_url}/{org}/{project}/_apis/wit/workitems/{work_item_id}?api-version=7.1"
        headers = {
            "Accept": "application/json",
            **self._auth_headers(),
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                work_item_data = response.json()
                fields = work_item_data.get("fields", {})
                return {
                    "title": fields.get("System.Title", ""),
                    "state": fields.get("System.State", ""),
                    "description": fields.get("System.Description", ""),
                }
            return None
        except requests.RequestException:
            return None

    def _find_work_item_by_change_id(self, change_id: str, org: str, project: str) -> dict[str, Any] | None:
        """
        Find an existing ADO work item by OpenSpec change_id embedded in the description.

        Args:
            change_id: OpenSpec change ID (used in footer marker)
            org: Azure DevOps organization
            project: Azure DevOps project

        Returns:
            Source tracking entry dict if found, otherwise None.
        """
        if not self.api_token or not change_id:
            return None

        project_escaped = project.replace("'", "''")
        change_id_escaped = change_id.replace("'", "''")
        wiql = {
            "query": (
                "Select [System.Id] From WorkItems "
                f"Where [System.TeamProject] = '{project_escaped}' "
                f"And [System.Description] Contains 'OpenSpec Change Proposal: `{change_id_escaped}`'"
            )
        }
        url = f"{self.base_url}/{org}/{project}/_apis/wit/wiql?api-version=7.1"
        headers = {
            "Content-Type": "application/json",
            **self._auth_headers(),
        }

        try:
            response = requests.post(url, json=wiql, headers=headers, timeout=10)
            if is_debug_mode():
                debug_log_operation(
                    "ado_wiql",
                    url,
                    str(response.status_code),
                    error=None if response.ok else (response.text[:200] if response.text else None),
                )
            if response.status_code != 200:
                return None
            work_items = response.json().get("workItems", [])
            work_item_ids = [item.get("id") for item in work_items if item.get("id")]
            if not work_item_ids:
                return None
            work_item_id = min(work_item_ids)
            work_item_url = f"{self.base_url}/{org}/{project}/_workitems/edit/{work_item_id}"
            return {
                "source_id": str(work_item_id),
                "source_url": work_item_url,
                "source_type": "ado",
                "source_repo": f"{org}/{project}",
            }
        except requests.RequestException as e:
            if is_debug_mode():
                debug_log_operation("ado_wiql", url, "error", error=str(e))
            return None

    def _create_work_item_from_proposal(
        self,
        proposal_data: dict[str, Any],  # ChangeProposal - TODO: use proper type
        org: str,
        project: str,
    ) -> dict[str, Any]:
        """
        Create ADO work item from change proposal.

        Args:
            proposal_data: Change proposal data (dict with title, description, rationale, status, etc.)
            org: Azure DevOps organization
            project: Azure DevOps project

        Returns:
            Dict with work item data: {"work_item_id": int, "work_item_url": str, "state": str}
        """
        import re as _re

        title = proposal_data.get("title", "Untitled Change Proposal")
        description = proposal_data.get("description", "")
        rationale = proposal_data.get("rationale", "")
        impact = proposal_data.get("impact", "")
        status = proposal_data.get("status", "proposed")
        change_id = proposal_data.get("change_id", "unknown")
        raw_title, raw_body = self._extract_raw_fields(proposal_data)
        if raw_title:
            title = raw_title

        # Build properly formatted work item description (prefer raw content when available)
        if raw_body:
            body = raw_body
        else:
            body_parts = []

            display_title = _re.sub(r"^\[change\]\s*", "", title, flags=_re.IGNORECASE).strip()
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

            if impact:
                body_parts.append("## Impact")
                body_parts.append("")
                impact_lines = impact.strip().split("\n")
                for line in impact_lines:
                    body_parts.append(line)
                body_parts.append("")

            # If no content, add placeholder
            if not body_parts or (not rationale and not description and not impact):
                body_parts.append("No description provided.")
                body_parts.append("")

            # Add OpenSpec metadata footer
            body_parts.append("---")
            body_parts.append(f"*OpenSpec Change Proposal: `{change_id}`*")

            body = "\n".join(body_parts)

        # Get work item type
        work_item_type = self._get_work_item_type(org, project)

        # Map status to ADO state
        # Check if source_state and source_type are provided (from cross-adapter sync)
        source_state = proposal_data.get("source_state")
        source_type = proposal_data.get("source_type")
        if source_state and source_type and source_type != "ado":
            # Use generic cross-adapter state mapping (preserves original state from source adapter)
            ado_state = self.map_backlog_state_between_adapters(source_state, source_type, self)
        else:
            # Use OpenSpec status mapping (default behavior)
            ado_state = self.map_openspec_status_to_backlog(status)

        # Ensure API token is available
        if not self.api_token:
            msg = "Azure DevOps API token is required"
            raise ValueError(msg)

        # Create work item via Azure DevOps API
        url = f"{self.base_url}/{org}/{project}/_apis/wit/workitems/${work_item_type}?api-version=7.1"
        headers = {
            "Content-Type": "application/json-patch+json",
            **self._auth_headers(),
        }

        # Build JSON Patch document for work item creation
        # Set multilineFieldsFormat to Markdown for proper rendering (ADO supports Markdown as of July 2025)
        patch_document = [
            {"op": "add", "path": "/fields/System.Title", "value": title},
            {"op": "add", "path": "/fields/System.Description", "value": body},
            {"op": "add", "path": "/fields/System.State", "value": ado_state},
            {
                "op": "add",
                "path": "/multilineFieldsFormat/System.Description",
                "value": "Markdown",
            },  # Set format to Markdown
        ]

        try:
            response = requests.patch(url, json=patch_document, headers=headers, timeout=30)
            if is_debug_mode():
                debug_log_operation(
                    "ado_patch",
                    url,
                    str(response.status_code),
                    error=None if response.ok else (response.text[:200] if response.text else None),
                )
            response.raise_for_status()
            work_item_data = response.json()

            work_item_id = work_item_data.get("id")
            work_item_url = work_item_data.get("_links", {}).get("html", {}).get("href", "")

            # Store ADO metadata in source_tracking if provided
            source_tracking = proposal_data.get("source_tracking")
            if source_tracking:
                if isinstance(source_tracking, dict):
                    source_tracking.update(
                        {
                            "source_id": work_item_id,
                            "source_url": work_item_url,
                            "source_repo": f"{org}/{project}",
                            "source_metadata": {
                                "org": org,
                                "project": project,
                                "work_item_type": work_item_type,
                                "state": ado_state,
                            },
                        }
                    )
                elif isinstance(source_tracking, list):
                    # Add new entry to list
                    source_tracking.append(
                        {
                            "source_id": work_item_id,
                            "source_url": work_item_url,
                            "source_repo": f"{org}/{project}",
                            "source_metadata": {
                                "org": org,
                                "project": project,
                                "work_item_type": work_item_type,
                                "state": ado_state,
                            },
                        }
                    )

            return {
                "work_item_id": work_item_id,
                "work_item_url": work_item_url,
                "state": ado_state,
            }
        except requests.RequestException as e:
            resp = getattr(e, "response", None)
            user_msg = _log_ado_patch_failure(resp, patch_document, url)
            e.ado_user_message = user_msg
            console.print(f"[bold red]✗[/bold red] {user_msg}")
            raise

    def _update_work_item_status(
        self,
        proposal_data: dict[str, Any],  # ChangeProposal with source_tracking
        org: str,
        project: str,
    ) -> dict[str, Any]:
        """
        Update ADO work item status based on change proposal status.

        Args:
            proposal_data: Change proposal data with source_tracking containing work item ID
            org: Azure DevOps organization
            project: Azure DevOps project

        Returns:
            Dict with updated work item data: {"work_item_id": int, "work_item_url": str, "state": str}
        """
        # Get work item ID from source_tracking
        source_tracking = proposal_data.get("source_tracking", {})

        # Normalize to find the entry for this repository
        target_repo = f"{org}/{project}"
        work_item_id = None

        if isinstance(source_tracking, dict):
            # Single dict entry (backward compatibility)
            work_item_id = source_tracking.get("source_id")
        elif isinstance(source_tracking, list):
            # List of entries - find the one matching this repository
            for entry in source_tracking:
                if isinstance(entry, dict):
                    entry_repo = entry.get("source_repo")
                    if entry_repo == target_repo:
                        work_item_id = entry.get("source_id")
                        break
                    # Backward compatibility: if no source_repo, try to extract from source_url
                    if not entry_repo:
                        source_url = entry.get("source_url", "")
                        if source_url and target_repo in source_url:
                            work_item_id = entry.get("source_id")
                            break

        if not work_item_id:
            msg = (
                f"Work item ID not found in source_tracking for repository {target_repo}. "
                "Work item must be created first."
            )
            raise ValueError(msg)

        # Ensure work_item_id is an integer for API call
        if isinstance(work_item_id, str):
            try:
                work_item_id = int(work_item_id)
            except ValueError:
                msg = f"Invalid work item ID format: {work_item_id}"
                raise ValueError(msg) from None

        status = proposal_data.get("status", "proposed")

        # Map status to ADO state
        # Check if source_state and source_type are provided (from cross-adapter sync)
        source_state = proposal_data.get("source_state")
        source_type = proposal_data.get("source_type")
        if source_state and source_type and source_type != "ado":
            # Use generic cross-adapter state mapping (preserves original state from source adapter)
            ado_state = self.map_backlog_state_between_adapters(source_state, source_type, self)
        else:
            # Use OpenSpec status mapping (default behavior)
            ado_state = self.map_openspec_status_to_backlog(status)

        # Ensure API token is available
        if not self.api_token:
            msg = "Azure DevOps API token is required"
            raise ValueError(msg)

        # Update work item state via Azure DevOps API
        url = f"{self.base_url}/{org}/{project}/_apis/wit/workitems/{work_item_id}?api-version=7.1"
        headers = {
            "Content-Type": "application/json-patch+json",
            **self._auth_headers(),
        }
        patch_document = [{"op": "replace", "path": "/fields/System.State", "value": ado_state}]

        try:
            response = requests.patch(url, json=patch_document, headers=headers, timeout=30)
            response.raise_for_status()
            work_item_data = response.json()

            work_item_url = work_item_data.get("_links", {}).get("html", {}).get("href", "")

            return {
                "work_item_id": work_item_id,
                "work_item_url": work_item_url,
                "state": ado_state,
            }
        except requests.RequestException as e:
            resp = getattr(e, "response", None)
            user_msg = _log_ado_patch_failure(resp, patch_document, url)
            console.print(f"[bold red]✗[/bold red] {user_msg}")
            raise

    def _update_work_item_body(
        self,
        proposal_data: dict[str, Any],  # ChangeProposal - TODO: use proper type
        org: str,
        project: str,
        work_item_id: int,
    ) -> dict[str, Any]:
        """
        Update ADO work item body/description from change proposal.

        Args:
            proposal_data: Change proposal data (dict with title, description, rationale, status, etc.)
            org: Azure DevOps organization
            project: Azure DevOps project
            work_item_id: Work item ID to update

        Returns:
            Dict with updated work item data: {"work_item_id": int, "work_item_url": str, "state": str}
        """
        import re as _re

        title = proposal_data.get("title", "Untitled Change Proposal")
        description = proposal_data.get("description", "")
        rationale = proposal_data.get("rationale", "")
        impact = proposal_data.get("impact", "")
        status = proposal_data.get("status", "proposed")
        change_id = proposal_data.get("change_id", "unknown")
        raw_title, raw_body = self._extract_raw_fields(proposal_data)
        if raw_title:
            title = raw_title

        # Build properly formatted work item description (same format as creation)
        if raw_body:
            body = raw_body
        else:
            body_parts = []

            display_title = _re.sub(r"^\[change\]\s*", "", title, flags=_re.IGNORECASE).strip()
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

            if impact:
                body_parts.append("## Impact")
                body_parts.append("")
                impact_lines = impact.strip().split("\n")
                for line in impact_lines:
                    body_parts.append(line)
                body_parts.append("")

            # If no content, add placeholder
            if not body_parts or (not rationale and not description and not impact):
                body_parts.append("No description provided.")
                body_parts.append("")

            # Add OpenSpec metadata footer
            body_parts.append("---")
            body_parts.append(f"*OpenSpec Change Proposal: `{change_id}`*")

            body = "\n".join(body_parts)

        # Map status to ADO state
        # Check if source_state and source_type are provided (from cross-adapter sync)
        source_state = proposal_data.get("source_state")
        source_type = proposal_data.get("source_type")
        if source_state and source_type and source_type != "ado":
            # Use generic cross-adapter state mapping (preserves original state from source adapter)
            ado_state = self.map_backlog_state_between_adapters(source_state, source_type, self)
        else:
            # Use OpenSpec status mapping (default behavior)
            ado_state = self.map_openspec_status_to_backlog(status)

        # Ensure API token is available
        if not self.api_token:
            msg = "Azure DevOps API token is required"
            raise ValueError(msg)

        # Update work item body and state via Azure DevOps API
        url = f"{self.base_url}/{org}/{project}/_apis/wit/workitems/{work_item_id}?api-version=7.1"
        headers = {
            "Content-Type": "application/json-patch+json",
            **self._auth_headers(),
        }

        # Build JSON Patch document for work item update
        # Set multilineFieldsFormat to Markdown for proper rendering
        patch_document = [
            {"op": "replace", "path": "/fields/System.Title", "value": title},
            {"op": "replace", "path": "/fields/System.Description", "value": body},
            {"op": "replace", "path": "/fields/System.State", "value": ado_state},
            {
                "op": "add",
                "path": "/multilineFieldsFormat/System.Description",
                "value": "Markdown",
            },  # Set format to Markdown
        ]

        try:
            response = requests.patch(url, json=patch_document, headers=headers, timeout=30)
            response.raise_for_status()
            work_item_data = response.json()

            work_item_url = work_item_data.get("_links", {}).get("html", {}).get("href", "")

            return {
                "work_item_id": work_item_id,
                "work_item_url": work_item_url,
                "state": ado_state,
            }
        except requests.RequestException as e:
            resp = getattr(e, "response", None)
            user_msg = _log_ado_patch_failure(resp, patch_document, url)
            console.print(f"[bold red]✗[/bold red] {user_msg}")
            raise

    @beartype
    @require(lambda proposal: isinstance(proposal, (dict, ChangeProposal)), "Proposal must be dict or ChangeProposal")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def sync_status_to_ado(
        self,
        proposal: dict[str, Any] | ChangeProposal,
        org: str,
        project: str,
        bridge_config: BridgeConfig | None = None,
    ) -> dict[str, Any]:
        """
        Sync OpenSpec change status to ADO work item state.

        Updates ADO work item state based on OpenSpec change proposal status.

        Args:
            proposal: Change proposal (dict or ChangeProposal instance)
            org: Azure DevOps organization
            project: Azure DevOps project
            bridge_config: Optional bridge configuration (for cross-repo support)

        Returns:
            Dict with sync result: {"work_item_id": int, "work_item_url": str, "state_updated": bool}

        Raises:
            ValueError: If work item ID not found in source_tracking
            requests.RequestException: If Azure DevOps API call fails
        """
        # Extract status and source_tracking
        if isinstance(proposal, ChangeProposal):
            status = proposal.status
            source_tracking = proposal.source_tracking
        else:
            status = proposal.get("status", "proposed")
            source_tracking = proposal.get("source_tracking")

        if not source_tracking:
            msg = "Source tracking required for status sync (work item must be created first)"
            raise ValueError(msg)

        # Get work item ID from source_tracking (handle both dict and list formats)
        work_item_id = None
        target_repo = f"{org}/{project}"

        if isinstance(source_tracking, dict):
            work_item_id = source_tracking.get("source_id")
        elif isinstance(source_tracking, list):
            for entry in source_tracking:
                if isinstance(entry, dict):
                    entry_repo = entry.get("source_repo")
                    if entry_repo == target_repo:
                        work_item_id = entry.get("source_id")
                        break
                    if not entry_repo:
                        source_url = entry.get("source_url", "")
                        if source_url and target_repo in source_url:
                            work_item_id = entry.get("source_id")
                            break

        if not work_item_id:
            msg = f"Work item ID not found in source_tracking for repository {target_repo}"
            raise ValueError(msg)

        # Ensure work_item_id is an integer
        if isinstance(work_item_id, str):
            try:
                work_item_id = int(work_item_id)
            except ValueError:
                msg = f"Invalid work item ID format: {work_item_id}"
                raise ValueError(msg) from None

        # Map OpenSpec status to ADO state
        ado_state = self.map_openspec_status_to_backlog(status)

        # Ensure API token is available
        if not self.api_token:
            msg = "Azure DevOps API token is required"
            raise ValueError(msg)

        # Update work item state via Azure DevOps API
        url = f"{self.base_url}/{org}/{project}/_apis/wit/workitems/{work_item_id}?api-version=7.1"
        headers = {
            "Content-Type": "application/json-patch+json",
            **self._auth_headers(),
        }

        # Build JSON Patch document for state update
        patch_document = [{"op": "replace", "path": "/fields/System.State", "value": ado_state}]

        try:
            response = requests.patch(url, json=patch_document, headers=headers, timeout=30)
            response.raise_for_status()
            work_item_data = response.json()

            work_item_url = work_item_data.get("_links", {}).get("html", {}).get("href", "")

            return {
                "work_item_id": work_item_id,
                "work_item_url": work_item_url,
                "state_updated": True,
                "new_state": ado_state,
            }
        except requests.RequestException as e:
            resp = getattr(e, "response", None)
            user_msg = _log_ado_patch_failure(resp, patch_document, url)
            e.ado_user_message = user_msg
            console.print(f"[bold red]✗[/bold red] {user_msg}")
            raise

    @beartype
    @require(lambda work_item_data: isinstance(work_item_data, dict), "Work item data must be dict")
    @require(lambda proposal: isinstance(proposal, (dict, ChangeProposal)), "Proposal must be dict or ChangeProposal")
    @ensure(lambda result: isinstance(result, str), "Must return resolved status string")
    def sync_status_from_ado(
        self,
        work_item_data: dict[str, Any],
        proposal: dict[str, Any] | ChangeProposal,
        strategy: str = "prefer_openspec",
    ) -> str:
        """
        Sync ADO work item state to OpenSpec change proposal.

        Maps ADO work item state to OpenSpec status and resolves conflicts if status differs.

        Args:
            work_item_data: ADO work item data (dict from API response)
            proposal: Change proposal (dict or ChangeProposal instance)
            strategy: Conflict resolution strategy (prefer_openspec, prefer_backlog, merge)

        Returns:
            Resolved OpenSpec status string
        """
        # Extract ADO state from work item fields
        fields = work_item_data.get("fields", {})
        ado_state = fields.get("System.State", "New")

        # Map ADO state to OpenSpec status
        openspec_status_from_ado = self.map_backlog_status_to_openspec(ado_state)

        # Get current OpenSpec status
        if isinstance(proposal, ChangeProposal):
            openspec_status = proposal.status
        else:
            openspec_status = proposal.get("status", "proposed")

        # Resolve conflict if status differs
        return self.resolve_status_conflict(openspec_status, openspec_status_from_ado, strategy)

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
            target_repo: Target repository identifier (e.g., "org/project") to filter source_tracking entries

        Returns:
            Comment text or empty string if no comment needed
        """
        if status == "applied":
            # Try to extract branch information from source_tracking
            branch_info = None
            if target_repo and isinstance(source_tracking, list):
                # Find entry for target repository
                target_entry = next(
                    (e for e in source_tracking if isinstance(e, dict) and e.get("source_repo") == target_repo),
                    None,
                )
                if target_entry:
                    branch_info = self._extract_branch_from_source_tracking(target_entry, code_repo_path)
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
            code_repo_path: Path to code repository for branch verification

        Returns:
            Branch name if found, None otherwise
        """
        # Try to infer from change_id (common pattern: feature/<change-id>)
        change_id = entry.get("change_id")
        if change_id:
            # Common branch naming patterns
            possible_branches = [
                f"feature/{change_id}",
                f"bugfix/{change_id}",
                f"hotfix/{change_id}",
            ]
            # Check each possible branch in code repo
            if code_repo_path:
                for branch in possible_branches:
                    if self._verify_branch_exists(branch, code_repo_path):
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

            # Method 1: Check if we're currently on this branch (fastest check)
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip() == branch_name:
                return True

            # Method 2: Use git rev-parse to check if branch exists (most reliable)
            result = subprocess.run(
                ["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{branch_name}"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                return True

            # Method 3: Use git show-ref for branch checking
            result = subprocess.run(
                ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                return True

            # Method 4: Fallback - check using git branch --list (for compatibility)
            result = subprocess.run(
                ["git", "branch", "--list", branch_name],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            # Check if branch exists locally
            if result.returncode == 0 and result.stdout.strip():
                # Parse branch names from output (handles both "* branch" and "  branch" formats)
                branches = []
                for line in result.stdout.split("\n"):
                    line = line.strip()
                    if line:
                        # Remove asterisk and any leading/trailing whitespace
                        branch = line.replace("*", "").strip()
                        if branch:
                            branches.append(branch)
                # Check if exact branch name matches (after normalization)
                if branch_name in branches:
                    return True

            # Method 5: Use git branch -a to list all branches (including current)
            result = subprocess.run(
                ["git", "branch", "-a"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                # Parse all branch names from output
                all_branches = []
                for line in result.stdout.split("\n"):
                    line = line.strip()
                    if line:
                        # Remove markers like "*", "remotes/", etc.
                        # Handle formats: "* branch", "  branch", "remotes/origin/branch"
                        if line.startswith("*"):
                            branch = line[1:].strip()
                        elif line.startswith("remotes/"):
                            # Extract branch name from remote format: remotes/origin/branch
                            parts = line.split("/")
                            branch = "/".join(parts[2:]) if len(parts) >= 3 else line.replace("remotes/", "").strip()
                        else:
                            branch = line.strip()
                        if branch and branch not in all_branches:
                            all_branches.append(branch)
                # Check if branch name matches
                if branch_name in all_branches:
                    return True

            # Also check remote branches explicitly
            result = subprocess.run(
                ["git", "branch", "-r", "--list", f"*/{branch_name}"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                # Extract branch name from remote branch format
                remote_branches = []
                for line in result.stdout.split("\n"):
                    line = line.strip()
                    if line and "/" in line:
                        # Remove remote prefix but keep full branch path
                        parts = line.split("/", 1)
                        if len(parts) == 2:
                            remote_branches.append(parts[1])
                if branch_name in remote_branches:
                    return True

            return False
        except Exception as e:
            # If we can't check (git not available, etc.), return False to be safe
            self.console.log(f"[bold yellow]Warning:[/bold yellow] Error checking branch existence: {e}")
            return False

    def _get_work_item_comments(self, org: str, project: str, work_item_id: int) -> list[dict[str, Any]]:
        """
        Fetch comments for an Azure DevOps work item.

        Args:
            org: Azure DevOps organization
            project: Azure DevOps project
            work_item_id: Work item ID

        Returns:
            List of comment dicts with 'text' or 'body' field, or empty list on error
        """
        if not self.api_token:
            return []

        url = f"{self.base_url}/{org}/{project}/_apis/wit/workitems/{work_item_id}/comments?api-version=7.1"
        headers = {
            "Accept": "application/json",
            **self._auth_headers(),
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            # ADO API returns comments in a 'comments' array within the response
            response_data = response.json()
            return response_data.get("comments", [])
        except requests.RequestException:
            # Return empty list on error - comments are optional
            return []

    @beartype
    @require(lambda org: isinstance(org, str) and org, "Organization must be non-empty string")
    @require(lambda project: isinstance(project, str) and project, "Project must be non-empty string")
    @require(
        lambda work_item_id: isinstance(work_item_id, int) and work_item_id > 0, "Work item ID must be positive int"
    )
    @require(
        lambda comment_text: isinstance(comment_text, str) and comment_text, "Comment text must be non-empty string"
    )
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def _add_work_item_comment(
        self,
        org: str,
        project: str,
        work_item_id: int,
        comment_text: str,
    ) -> dict[str, Any]:
        """
        Add a comment to an Azure DevOps work item.

        Args:
            org: Azure DevOps organization
            project: Azure DevOps project
            work_item_id: Work item ID
            comment_text: Comment text (markdown supported)

        Returns:
            Dict with comment data: {"work_item_id": int, "comment_id": int, "comment_added": bool}

        Raises:
            ValueError: If API token is missing
            requests.RequestException: If Azure DevOps API call fails
        """
        if not self.api_token:
            msg = "Azure DevOps API token is required"
            raise ValueError(msg)

        # Azure DevOps API for adding comments to work items
        url = f"{self.base_url}/{org}/{project}/_apis/wit/workitems/{work_item_id}/comments?api-version=7.1"
        headers = {
            "Content-Type": "application/json",
            **self._auth_headers(),
        }

        # Build request body for comment
        comment_body = {"text": comment_text}

        try:
            response = requests.post(url, json=comment_body, headers=headers, timeout=30)
            response.raise_for_status()
            comment_data = response.json()

            comment_id = comment_data.get("id")

            return {
                "work_item_id": work_item_id,
                "comment_id": comment_id,
                "comment_added": True,
            }
        except requests.RequestException as e:
            resp = getattr(e, "response", None)
            user_msg = _log_ado_patch_failure(resp, [], url)
            e.ado_user_message = user_msg
            console.print(f"[bold red]✗[/bold red] {user_msg}")
            raise

    @beartype
    @require(lambda proposal_data: isinstance(proposal_data, dict), "Proposal data must be dict")
    @require(lambda org: isinstance(org, str) and org, "Organization must be non-empty string")
    @require(lambda project: isinstance(project, str) and project, "Project must be non-empty string")
    @require(
        lambda work_item_id: isinstance(work_item_id, int) and work_item_id > 0, "Work item ID must be positive int"
    )
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def _add_progress_comment(
        self,
        proposal_data: dict[str, Any],  # ChangeProposal with progress_data
        org: str,
        project: str,
        work_item_id: int,
        sanitize: bool = False,
    ) -> dict[str, Any]:
        """
        Add progress comment to Azure DevOps work item based on code changes.

        Args:
            proposal_data: Change proposal data with progress_data (dict with code change info)
            org: Azure DevOps organization
            project: Azure DevOps project
            work_item_id: Azure DevOps work item ID
            sanitize: If True, sanitize sensitive information in progress comment (for public repos)

        Returns:
            Dict with updated work item data: {"work_item_id": int, "work_item_url": str, "comment_added": bool}

        Raises:
            requests.RequestException: If Azure DevOps API call fails
        """
        progress_data = proposal_data.get("progress_data", {})
        if not progress_data:
            # No progress data provided
            return {
                "work_item_id": work_item_id,
                "work_item_url": f"{self.base_url}/{org}/{project}/_workitems/edit/{work_item_id}",
                "comment_added": False,
            }

        from specfact_cli.utils.code_change_detector import format_progress_comment

        comment_text = format_progress_comment(progress_data, sanitize=sanitize)

        try:
            self._add_work_item_comment(org, project, work_item_id, comment_text)
            return {
                "work_item_id": work_item_id,
                "work_item_url": f"{self.base_url}/{org}/{project}/_workitems/edit/{work_item_id}",
                "comment_added": True,
            }
        except requests.RequestException as e:
            msg = f"Failed to add progress comment to Azure DevOps work item #{work_item_id}: {e}"
            console.print(f"[bold red]✗[/bold red] {msg}")
            raise

    # BacklogAdapter interface implementations

    def _get_current_iteration(self) -> str | None:
        """
        Get the current active iteration for the team.

        Returns:
            Current iteration path if found, None otherwise

        Raises:
            requests.RequestException: If API call fails
        """
        if not self.org or not self.project:
            return None

        # If team is not set, fetch the default team from the project
        team_to_use = self.team
        if not team_to_use:
            # Try to get the default team for the project
            try:
                # Get teams for the project: /{org}/_apis/projects/{projectId}/teams
                # First, we need the project ID - URL encode project name in case it has spaces
                from urllib.parse import quote

                project_encoded = quote(self.project, safe="")
                project_url = f"{self.base_url}/{self.org}/_apis/projects/{project_encoded}"
                project_params = {"api-version": "7.1"}
                project_headers = {
                    **self._auth_headers(),
                    "Accept": "application/json",
                }
                project_response = requests.get(project_url, headers=project_headers, params=project_params, timeout=30)
                project_response.raise_for_status()
                project_data = project_response.json()
                project_id = project_data.get("id")

                if project_id:
                    # Get teams for the project
                    teams_url = f"{self.base_url}/{self.org}/_apis/projects/{project_id}/teams"
                    teams_response = requests.get(teams_url, headers=project_headers, params=project_params, timeout=30)
                    teams_response.raise_for_status()
                    teams_data = teams_response.json()
                    teams = teams_data.get("value", [])
                    if teams:
                        # Use the first team (usually the default team)
                        team_to_use = teams[0].get("name")
                        # Cache it for future use
                        self.team = team_to_use
            except requests.RequestException:
                # If team lookup fails, we can't proceed
                return None

        if not team_to_use:
            return None

        # Team iterations API: /{org}/{project}/{team}/_apis/work/teamsettings/iterations?$timeframe=current
        # URL encode team name in case it has spaces or special characters
        from urllib.parse import quote

        team_encoded = quote(team_to_use, safe="")
        url = f"{self.base_url}/{self.org}/{self.project}/{team_encoded}/_apis/work/teamsettings/iterations"
        params = {"$timeframe": "current", "api-version": "7.1"}
        headers = {
            **self._auth_headers(),
            "Accept": "application/json",
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            iterations = data.get("value", [])
            if iterations:
                # Return the first current iteration path
                return iterations[0].get("path")
        except requests.HTTPError as e:
            # Log the error for debugging but don't fail completely
            # The team might not exist or might have a different name
            if e.response is not None and e.response.status_code == 404 and team_to_use != self.project:
                # Team not found - try with project name as fallback
                # Retry with project name (URL encoded)
                project_encoded = quote(self.project, safe="")
                fallback_url = (
                    f"{self.base_url}/{self.org}/{self.project}/{project_encoded}/_apis/work/teamsettings/iterations"
                )
                try:
                    fallback_response = requests.get(fallback_url, headers=headers, params=params, timeout=30)
                    fallback_response.raise_for_status()
                    fallback_data = fallback_response.json()
                    fallback_iterations = fallback_data.get("value", [])
                    if fallback_iterations:
                        return fallback_iterations[0].get("path")
                except requests.RequestException:
                    pass
        except requests.RequestException:
            # Fail silently - will be handled by caller
            pass
        return None

    def _list_available_iterations(self) -> list[str]:
        """
        List all available iteration paths for the team.

        Returns:
            List of iteration paths (empty list if unavailable)

        Raises:
            requests.RequestException: If API call fails
        """
        if not self.org or not self.project:
            return []

        # If team is not set, try to get it (same logic as _get_current_iteration)
        team_to_use = self.team
        if not team_to_use:
            # Try to get the default team for the project (same logic as _get_current_iteration)
            try:
                from urllib.parse import quote

                project_encoded = quote(self.project, safe="")
                project_url = f"{self.base_url}/{self.org}/_apis/projects/{project_encoded}"
                project_params = {"api-version": "7.1"}
                project_headers = {
                    **self._auth_headers(),
                    "Accept": "application/json",
                }
                project_response = requests.get(project_url, headers=project_headers, params=project_params, timeout=30)
                project_response.raise_for_status()
                project_data = project_response.json()
                project_id = project_data.get("id")

                if project_id:
                    teams_url = f"{self.base_url}/{self.org}/_apis/projects/{project_id}/teams"
                    teams_response = requests.get(teams_url, headers=project_headers, params=project_params, timeout=30)
                    teams_response.raise_for_status()
                    teams_data = teams_response.json()
                    teams = teams_data.get("value", [])
                    if teams:
                        team_to_use = teams[0].get("name")
                        self.team = team_to_use
            except requests.RequestException:
                return []

        if not team_to_use:
            return []

        # Team iterations API: /{org}/{project}/{team}/_apis/work/teamsettings/iterations
        # URL encode team name in case it has spaces or special characters
        from urllib.parse import quote

        team_encoded = quote(team_to_use, safe="")
        url = f"{self.base_url}/{self.org}/{self.project}/{team_encoded}/_apis/work/teamsettings/iterations"
        params = {"api-version": "7.1"}
        headers = {
            **self._auth_headers(),
            "Accept": "application/json",
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            iterations = data.get("value", [])
            return [it.get("path", "") for it in iterations if it.get("path")]
        except requests.RequestException:
            # Fail silently - will be handled by caller
            pass
        return []

    def _resolve_sprint_filter(
        self,
        sprint_filter: str | None,
        items: list[BacklogItem],
    ) -> tuple[str | None, list[BacklogItem]]:
        """
        Resolve sprint filter with path matching and ambiguity detection.

        Args:
            sprint_filter: Sprint filter value (name or full path)
            items: List of backlog items to filter

        Returns:
            Tuple of (resolved_iteration_path, filtered_items)

        Raises:
            ValueError: If ambiguous sprint name match is detected
        """
        if not sprint_filter:
            # No sprint filter - try to get current iteration
            current_iteration = self._get_current_iteration()
            if current_iteration:
                # Filter by current iteration path
                filtered = [item for item in items if item.iteration and item.iteration == current_iteration]
                return current_iteration, filtered
            # No current iteration found - return all items
            console.print("[yellow]⚠ No current iteration found; returning all items[/yellow]")
            return None, items

        # Check if sprint_filter contains path separator (full path)
        has_path_separator = "\\" in sprint_filter or "/" in sprint_filter

        if has_path_separator:
            # Full iteration path - match directly
            filtered = [item for item in items if item.iteration and item.iteration == sprint_filter]
            return sprint_filter, filtered
        # Name-only - check for ambiguity
        matching_items = [
            item
            for item in items
            if item.sprint
            and BacklogFilters.normalize_filter_value(item.sprint)
            == BacklogFilters.normalize_filter_value(sprint_filter)
        ]

        if not matching_items:
            # No matches
            return sprint_filter, []

        # Check for ambiguous iteration paths
        unique_iterations = {item.iteration for item in matching_items if item.iteration}

        if len(unique_iterations) > 1:
            # Ambiguous - multiple iteration paths with same sprint name
            iteration_list = "\n".join(f"  - {it}" for it in sorted(unique_iterations))
            msg = (
                f"Ambiguous sprint name '{sprint_filter}' matches multiple iteration paths:\n"
                f"{iteration_list}\n"
                f"Please use a full iteration path (e.g., 'Project\\Iteration\\Sprint 01') instead."
            )
            raise ValueError(msg)

        # Single unique iteration path - safe to use
        iteration_path = unique_iterations.pop() if unique_iterations else None
        return iteration_path, matching_items

    @beartype
    @ensure(lambda result: isinstance(result, str) and len(result) > 0, "Must return non-empty adapter name")
    def name(self) -> str:
        """Get the adapter name."""
        return "ado"

    @beartype
    @require(lambda format_type: isinstance(format_type, str) and len(format_type) > 0, "Format type must be non-empty")
    @ensure(lambda result: isinstance(result, bool), "Must return boolean")
    def supports_format(self, format_type: str) -> bool:
        """Check if adapter supports the specified format."""
        return format_type.lower() == "markdown"

    @beartype
    @require(lambda filters: isinstance(filters, BacklogFilters), "Filters must be BacklogFilters instance")
    @ensure(lambda result: isinstance(result, list), "Must return list of BacklogItem")
    @ensure(
        lambda result, filters: all(isinstance(item, BacklogItem) for item in result), "All items must be BacklogItem"
    )
    def fetch_backlog_items(self, filters: BacklogFilters) -> list[BacklogItem]:
        """
        Fetch Azure DevOps work items matching the specified filters.

        Uses ADO Work Items API to query work items.
        """
        if not self.api_token:
            msg = (
                "Azure DevOps API token required to fetch backlog items.\n"
                "Options:\n"
                "  1. Set AZURE_DEVOPS_TOKEN environment variable\n"
                "  2. Use --ado-token option\n"
                "  3. Store token via specfact auth azure-devops"
            )
            raise ValueError(msg)

        if not self.org:
            msg = (
                "org (organization) required to fetch backlog items.\n"
                "For Azure DevOps Services (cloud), org is always required.\n"
                "For Azure DevOps Server (on-premise), org is the collection name.\n"
                "Provide via --ado-org option or ensure it's set in adapter configuration."
            )
            raise ValueError(msg)

        if not self.project:
            msg = "project required to fetch backlog items. Provide via --ado-project option."
            raise ValueError(msg)

        # Build WIQL (Work Item Query Language) query
        # WIQL syntax: SELECT fields FROM WorkItems WHERE conditions
        # Use @project macro to reference the project context in project-scoped queries
        wiql_parts = ["SELECT [System.Id], [System.Title], [System.State], [System.WorkItemType]"]
        wiql_parts.append("FROM WorkItems")
        # Use @project macro for project context (ADO automatically resolves this in project-scoped queries)
        wiql_parts.append("WHERE [System.TeamProject] = @project")

        conditions = []

        # Note: ADO WIQL doesn't support case-insensitive matching directly
        # We'll apply case-insensitive filtering post-fetch for state and assignee
        # For iteration, we handle sprint resolution separately

        if filters.area:
            conditions.append(f"[System.AreaPath] = '{filters.area}'")

        # Handle sprint/iteration filtering
        # If sprint is provided, resolve it (may become iteration path)
        # If neither sprint nor iteration provided, default to current iteration
        resolved_iteration = None
        if filters.iteration:
            # Check if iteration is the special value "current"
            if filters.iteration.lower() == "current":
                current_iteration = self._get_current_iteration()
                if current_iteration:
                    resolved_iteration = current_iteration
                    conditions.append(f"[System.IterationPath] = '{resolved_iteration}'")
                else:
                    # Provide helpful error message with suggestions
                    available_iterations = self._list_available_iterations()
                    suggestions = ""
                    if available_iterations:
                        examples = available_iterations[:5]
                        suggestions = "\n[cyan]Available iteration paths (showing first 5):[/cyan]\n"
                        for it_path in examples:
                            suggestions += f"  • {it_path}\n"
                        if len(available_iterations) > 5:
                            suggestions += f"  ... and {len(available_iterations) - 5} more\n"

                    error_msg = (
                        f"[red]Error:[/red] No current iteration found.\n\n"
                        f"{suggestions}"
                        f"[cyan]Tips:[/cyan]\n"
                        f"  • Specify a full iteration path: [bold]--iteration 'Project\\Sprint 1'[/bold]\n"
                        f"  • Use [bold]--sprint[/bold] with just the sprint name for automatic matching\n"
                        f"  • Check your project's iteration paths in Azure DevOps: Project Settings → Boards → Iterations\n"
                        f"  • Ensure your team has an active iteration configured"
                    )
                    console.print(error_msg)
                    raise ValueError("No current iteration found")
            else:
                # Use iteration path as-is (must be exact full path from ADO)
                resolved_iteration = filters.iteration
                conditions.append(f"[System.IterationPath] = '{resolved_iteration}'")
        elif filters.sprint:
            # Sprint will be resolved post-fetch to handle ambiguity
            pass
        else:
            # No sprint/iteration - try current iteration
            current_iteration = self._get_current_iteration()
            if current_iteration:
                resolved_iteration = current_iteration
                conditions.append(f"[System.IterationPath] = '{resolved_iteration}'")
            else:
                console.print("[yellow]⚠ No current iteration found and no sprint/iteration filter provided[/yellow]")

        if conditions:
            wiql_parts.append("AND " + " AND ".join(conditions))

        wiql = " ".join(wiql_parts)

        # Execute WIQL query
        # POST to project-level endpoint: {org}/{project}/_apis/wit/wiql?api-version=7.1
        url = self._build_ado_url("_apis/wit/wiql", api_version="7.1")
        headers = {
            **self._auth_headers(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {"query": wiql}

        # Debug: Log URL construction and auth status for troubleshooting
        debug_print(f"[dim]ADO WIQL URL: {url}[/dim]")
        if "Authorization" in headers:
            auth_header_preview = (
                headers["Authorization"][:20] + "..."
                if len(headers["Authorization"]) > 20
                else headers["Authorization"]
            )
            debug_print(f"[dim]ADO Auth: {auth_header_preview}[/dim]")
        else:
            debug_print("[yellow]Warning: No Authorization header in request[/yellow]")

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
        except requests.HTTPError as e:
            # Provide user-friendly error message
            user_friendly_msg = None
            if e.response is not None:
                try:
                    error_json = e.response.json()
                    error_message = error_json.get("message", "")

                    # Check for iteration path errors
                    if "TF51011" in error_message or "iteration path does not exist" in error_message.lower():
                        # Extract the problematic iteration path from the error
                        import re

                        match = re.search(r"«'([^']+)'»", error_message)
                        bad_path = match.group(1) if match else (resolved_iteration if resolved_iteration else None)

                        # Try to get available iterations for helpful suggestions
                        available_iterations = self._list_available_iterations()
                        suggestions = ""
                        if available_iterations:
                            # Show first 5 available iterations as examples
                            examples = available_iterations[:5]
                            suggestions = "\n[cyan]Available iteration paths (showing first 5):[/cyan]\n"
                            for it_path in examples:
                                suggestions += f"  • {it_path}\n"
                            if len(available_iterations) > 5:
                                suggestions += f"  ... and {len(available_iterations) - 5} more\n"

                        user_friendly_msg = (
                            f"[red]Error:[/red] The iteration path does not exist in Azure DevOps.\n"
                            f"[yellow]Provided path:[/yellow] {bad_path}\n\n"
                            f"{suggestions}"
                            f"[cyan]Tips:[/cyan]\n"
                            f"  • Use [bold]--iteration current[/bold] to automatically use the current active iteration\n"
                            f"  • Use [bold]--sprint[/bold] with just the sprint name (e.g., 'Sprint 01') for automatic matching\n"
                            f"  • The iteration path must match exactly as shown in Azure DevOps (including project name)\n"
                            f"  • Check your project's iteration paths in Azure DevOps: Project Settings → Boards → Iterations"
                        )
                    elif "400" in str(e.response.status_code) or "Bad Request" in str(e):
                        user_friendly_msg = (
                            f"[red]Error:[/red] Invalid request to Azure DevOps API.\n"
                            f"[yellow]Details:[/yellow] {error_message}\n\n"
                            f"Please check your parameters and try again."
                        )
                except Exception:
                    pass

            # If we have a user-friendly message, use it; otherwise fall back to detailed technical error
            if user_friendly_msg:
                console.print(user_friendly_msg)
                # Still raise the exception for proper error handling
                raise ValueError(f"Iteration path error: {resolved_iteration}") from e

            # Fallback to detailed technical error
            error_detail = ""
            if e.response is not None:
                try:
                    error_json = e.response.json()
                    error_detail = f"\nResponse: {error_json}"
                except Exception:
                    error_detail = f"\nResponse status: {e.response.status_code}"

            error_msg = (
                f"Azure DevOps API error: {e}{error_detail}\n"
                f"URL: {url}\n"
                f"Organization: {self.org}\n"
                f"Project: {self.project}\n"
                f"Base URL: {self.base_url}\n"
                f"Expected format: https://dev.azure.com/{{org}}/{{project}}/_apis/wit/wiql?api-version=7.1\n"
                f"If using Azure DevOps Server (on-premise), base_url format may differ."
            )
            # Create new exception with better message
            new_exception = requests.HTTPError(error_msg)
            new_exception.response = e.response
            raise new_exception from e
        query_result = response.json()

        work_item_ids = [item["id"] for item in query_result.get("workItems", [])]

        if not work_item_ids:
            return []

        # Fetch work item details
        # Note: GET workitems by IDs uses organization-level endpoint, not project-level
        # Format: https://dev.azure.com/{organization}/_apis/wit/workitems?ids={ids}&api-version={version}
        items: list[BacklogItem] = []
        batch_size = 200  # ADO API limit

        # Build organization-level URL for work items batch fetch
        base_url_normalized = self.base_url.rstrip("/")
        is_on_premise = self._is_on_premise()

        # For work items batch GET, URL is at organization level (not project level)
        if is_on_premise:
            # On-premise: if base_url has collection, use it; otherwise add org
            parts = [p for p in base_url_normalized.split("/") if p and p not in ["http:", "https:"]]
            has_collection_in_base = "/tfs/" in base_url_normalized.lower() or len(parts) > 1

            if has_collection_in_base:
                # Collection already in base_url
                workitems_base_url = base_url_normalized
            elif self.org:
                # Need to add collection
                if "/tfs" in base_url_normalized.lower():
                    workitems_base_url = f"{base_url_normalized}/tfs/{self.org}"
                else:
                    workitems_base_url = f"{base_url_normalized}/{self.org}"
            else:
                workitems_base_url = base_url_normalized
        else:
            # Cloud: organization level
            if not self.org:
                raise ValueError(f"org required for Azure DevOps Services (cloud) (org={self.org!r})")
            workitems_base_url = f"{base_url_normalized}/{self.org}"

        for i in range(0, len(work_item_ids), batch_size):
            batch = work_item_ids[i : i + batch_size]
            ids_str = ",".join(str(wi_id) for wi_id in batch)

            # Work items batch GET is at organization level, not project level
            # Format: {org}/_apis/wit/workitems?ids={ids}&api-version=7.1
            url = f"{workitems_base_url}/_apis/wit/workitems?api-version=7.1"
            params = {"ids": ids_str, "$expand": "all"}

            # Headers for work items batch GET (organization-level endpoint)
            workitems_headers = {
                **self._auth_headers(),
                "Accept": "application/json",
            }

            # Debug: Log URL construction for troubleshooting
            debug_print(f"[dim]ADO WorkItems URL: {url}&ids={ids_str}[/dim]")

            try:
                response = requests.get(url, headers=workitems_headers, params=params, timeout=30)
                if is_debug_mode():
                    debug_log_operation(
                        "ado_workitems_get",
                        url,
                        str(response.status_code),
                        error=None if response.ok else (response.text[:200] if response.text else None),
                    )
                response.raise_for_status()
            except requests.HTTPError as e:
                if is_debug_mode():
                    debug_log_operation(
                        "ado_workitems_get",
                        url,
                        "error",
                        error=str(e.response.status_code) if e.response is not None else str(e),
                    )
                # Provide better error message with URL details
                error_detail = ""
                if e.response is not None:
                    try:
                        error_json = e.response.json()
                        error_detail = f"\nResponse: {error_json}"
                    except Exception:
                        error_detail = f"\nResponse status: {e.response.status_code}"

                error_msg = (
                    f"Azure DevOps API error: {e}{error_detail}\n"
                    f"URL: {url}\n"
                    f"Organization: {self.org}\n"
                    f"Project: {self.project}\n"
                    f"Base URL: {self.base_url}\n"
                    f"Expected format: https://dev.azure.com/{{org}}/{{project}}/_apis/wit/workitems?ids={{ids}}&api-version=7.1\n"
                    f"If using Azure DevOps Server (on-premise), base_url format may differ."
                )
                # Create new exception with better message
                new_exception = requests.HTTPError(error_msg)
                new_exception.response = e.response
                raise new_exception from e
            work_items_data = response.json()

            # Convert ADO work items to BacklogItem
            from specfact_cli.backlog.converter import convert_ado_work_item_to_backlog_item

            for work_item in work_items_data.get("value", []):
                backlog_item = convert_ado_work_item_to_backlog_item(
                    work_item,
                    provider="ado",
                    base_url=self.base_url,
                    org=self.org,
                    project_name=self.project,
                )
                items.append(backlog_item)

        # Apply post-fetch filters that ADO API doesn't support directly
        filtered_items = items

        # Case-insensitive state filtering
        if filters.state:
            normalized_state = BacklogFilters.normalize_filter_value(filters.state)
            filtered_items = [
                item for item in filtered_items if BacklogFilters.normalize_filter_value(item.state) == normalized_state
            ]

        # Case-insensitive assignee filtering (match against displayName, uniqueName, or mail)
        if filters.assignee:
            normalized_assignee = BacklogFilters.normalize_filter_value(filters.assignee)
            filtered_items = [
                item
                for item in filtered_items
                if any(
                    BacklogFilters.normalize_filter_value(assignee) == normalized_assignee
                    for assignee in item.assignees
                )
            ]

        if filters.labels:
            filtered_items = [item for item in filtered_items if any(label in item.tags for label in filters.labels)]

        # Sprint filtering with path matching and ambiguity detection
        if filters.sprint:
            try:
                _, filtered_items = self._resolve_sprint_filter(filters.sprint, filtered_items)
            except ValueError as e:
                # Ambiguous sprint match - raise with clear error message
                console.print(f"[red]Error:[/red] {e}")
                raise

        if filters.release:
            normalized_release = BacklogFilters.normalize_filter_value(filters.release)
            filtered_items = [
                item
                for item in filtered_items
                if item.release and BacklogFilters.normalize_filter_value(item.release) == normalized_release
            ]

        if filters.search:
            # Search filtering not directly supported by ADO WIQL, skip for now
            pass

        # Apply limit if specified
        if filters.limit is not None and len(filtered_items) > filters.limit:
            filtered_items = filtered_items[: filters.limit]

        return filtered_items

    @beartype
    def add_comment(self, item: BacklogItem, comment: str) -> bool:
        """
        Add a comment to an Azure DevOps work item.

        Args:
            item: BacklogItem to add comment to
            comment: Comment text to add

        Returns:
            True if comment was added successfully, False otherwise
        """
        if not self.api_token:
            return False

        if not self.org or not self.project:
            return False

        work_item_id = int(item.id)
        try:
            self._add_work_item_comment(self.org, self.project, work_item_id, comment)
            return True
        except Exception:
            return False

    @beartype
    @require(lambda item: isinstance(item, BacklogItem), "Item must be BacklogItem")
    @require(
        lambda update_fields: update_fields is None or isinstance(update_fields, list),
        "Update fields must be None or list",
    )
    @ensure(lambda result: isinstance(result, BacklogItem), "Must return BacklogItem")
    @ensure(
        lambda result, item: result.id == item.id and result.provider == item.provider,
        "Updated item must preserve id and provider",
    )
    def update_backlog_item(self, item: BacklogItem, update_fields: list[str] | None = None) -> BacklogItem:
        """
        Update an Azure DevOps work item.

        Updates the work item title and/or description based on update_fields.
        """
        if not self.api_token:
            msg = "Azure DevOps API token required to update backlog items"
            raise ValueError(msg)

        if not self.org or not self.project:
            msg = "org and project required to update backlog items"
            raise ValueError(msg)

        work_item_id = int(item.id)
        url = self._build_ado_url(f"_apis/wit/workitems/{work_item_id}", api_version="7.1")
        headers = {
            **self._auth_headers(),
            "Content-Type": "application/json-patch+json",
        }

        # Build update operations
        operations = []

        if update_fields is None or "title" in update_fields:
            operations.append({"op": "replace", "path": "/fields/System.Title", "value": item.title})

        # Use AdoFieldMapper for field writeback (honor custom field mappings)
        custom_mapping_file = os.environ.get("SPECFACT_ADO_CUSTOM_MAPPING")
        ado_mapper = AdoFieldMapper(custom_mapping_file=custom_mapping_file)
        canonical_fields: dict[str, Any] = {
            "description": item.body_markdown,
            "acceptance_criteria": item.acceptance_criteria,
            "story_points": item.story_points,
            "business_value": item.business_value,
            "priority": item.priority,
            "value_points": item.value_points,
            "work_item_type": item.work_item_type,
        }

        # Map canonical fields to ADO fields (uses custom mappings if provided)
        ado_fields = ado_mapper.map_from_canonical(canonical_fields)

        # Get reverse mapping to find ADO field names for canonical fields
        # Use same preference logic as map_from_canonical: prefer System.* over Microsoft.VSTS.Common.*
        field_mappings = ado_mapper._get_field_mappings()
        reverse_mappings: dict[str, str] = {}
        for ado_field, canonical in field_mappings.items():
            if canonical not in reverse_mappings:
                # First mapping for this canonical field - use it
                reverse_mappings[canonical] = ado_field
            else:
                # Multiple mappings exist - prefer System.* over Microsoft.VSTS.Common.*
                current_ado_field = reverse_mappings[canonical]
                # Prefer System.* fields for write operations (more common in Scrum)
                if ado_field.startswith("System.") and not current_ado_field.startswith("System."):
                    reverse_mappings[canonical] = ado_field

        # Update description (body_markdown) - always use System.Description
        if update_fields is None or "body" in update_fields or "body_markdown" in update_fields:
            import re

            # Never send null: ADO rejects null for /fields/System.Description (HTTP 400)
            raw_body = item.body_markdown
            markdown_content = raw_body if raw_body is not None else ""
            # Convert TODO markers to proper Markdown checkboxes for ADO rendering
            todo_pattern = r"^(\s*)[-*]\s*\[TODO[:\s]+([^\]]+)\](.*)$"
            markdown_content = re.sub(
                todo_pattern,
                r"\1- [ ] \2",
                markdown_content,
                flags=re.MULTILINE | re.IGNORECASE,
            )

            description_field = reverse_mappings.get("description", "System.Description")
            # Set multiline field format to Markdown first (optional; many ADO instances return 400 for this path)
            operations.append({"op": "add", "path": f"/multilineFieldsFormat/{description_field}", "value": "Markdown"})
            operations.append({"op": "replace", "path": f"/fields/{description_field}", "value": markdown_content})

        # Update acceptance criteria using mapped field name (honors custom mappings)
        if update_fields is None or "acceptance_criteria" in update_fields:
            acceptance_criteria_field = reverse_mappings.get("acceptance_criteria")
            # Check if field exists in mapped fields (means it's available in ADO) and has value
            if acceptance_criteria_field and item.acceptance_criteria and acceptance_criteria_field in ado_fields:
                operations.append(
                    {"op": "replace", "path": f"/fields/{acceptance_criteria_field}", "value": item.acceptance_criteria}
                )

        # Update story points using mapped field name (honors custom mappings)
        if update_fields is None or "story_points" in update_fields:
            story_points_field = reverse_mappings.get("story_points")
            # Check if field exists in mapped fields (means it's available in ADO) and has value
            # Handle both Microsoft.VSTS.Common.StoryPoints and Microsoft.VSTS.Scheduling.StoryPoints
            if story_points_field and item.story_points is not None and story_points_field in ado_fields:
                operations.append(
                    {"op": "replace", "path": f"/fields/{story_points_field}", "value": item.story_points}
                )

        # Update business value using mapped field name (honors custom mappings)
        if update_fields is None or "business_value" in update_fields:
            business_value_field = reverse_mappings.get("business_value")
            # Check if field exists in mapped fields (means it's available in ADO) and has value
            if business_value_field and item.business_value is not None and business_value_field in ado_fields:
                operations.append(
                    {"op": "replace", "path": f"/fields/{business_value_field}", "value": item.business_value}
                )

        # Update priority using mapped field name (honors custom mappings)
        if update_fields is None or "priority" in update_fields:
            priority_field = reverse_mappings.get("priority")
            # Check if field exists in mapped fields (means it's available in ADO) and has value
            if priority_field and item.priority is not None and priority_field in ado_fields:
                operations.append({"op": "replace", "path": f"/fields/{priority_field}", "value": item.priority})

        if update_fields is None or "state" in update_fields:
            operations.append({"op": "replace", "path": "/fields/System.State", "value": item.state})

        # Update work item
        try:
            response = requests.patch(url, headers=headers, json=operations, timeout=30)
            response.raise_for_status()
        except requests.HTTPError as e:
            user_msg = _log_ado_patch_failure(e.response, operations, url)
            e.ado_user_message = user_msg
            response = None
            if e.response and e.response.status_code in (400, 422):
                error_message = ""
                try:
                    error_json = e.response.json()
                    error_message = error_json.get("message", "")
                except Exception:
                    pass

                # First retry: omit multilineFieldsFormat entirely (only /fields/ updates).
                # Many ADO instances reject /multilineFieldsFormat/ path with 400 Bad Request.
                operations_no_format = [
                    op for op in operations if not (op.get("path") or "").startswith("/multilineFieldsFormat/")
                ]
                if operations_no_format != operations:
                    try:
                        resp = requests.patch(url, headers=headers, json=operations_no_format, timeout=30)
                        resp.raise_for_status()
                        response = resp
                    except requests.HTTPError as retry_error:
                        _log_ado_patch_failure(
                            retry_error.response,
                            operations_no_format,
                            url,
                            context=str(retry_error),
                        )

                if response is None and (
                    "already exists" in error_message.lower() or "cannot add" in error_message.lower()
                ):
                    # Second: try "replace" instead of "add" for multilineFieldsFormat
                    operations_replace = []
                    for op in operations:
                        path = op.get("path") or ""
                        if path.startswith("/multilineFieldsFormat/"):
                            operations_replace.append({"op": "replace", "path": path, "value": op["value"]})
                        else:
                            operations_replace.append(op)
                    try:
                        resp = requests.patch(url, headers=headers, json=operations_replace, timeout=30)
                        resp.raise_for_status()
                        response = resp
                    except requests.HTTPError:
                        pass

                if response is None:
                    # Third: HTML fallback (no multilineFieldsFormat, description as HTML)
                    import re as _re

                    console.print("[yellow]⚠ Markdown format not supported, converting description to HTML[/yellow]")
                    operations_html = [
                        op for op in operations if not (op.get("path") or "").startswith("/multilineFieldsFormat/")
                    ]
                    description_field = reverse_mappings.get("description", "System.Description")
                    desc_path = f"/fields/{description_field}"
                    for op in operations_html:
                        if op.get("path") == desc_path:
                            markdown_for_html = op.get("value") or ""
                            todo_pattern = r"^(\s*)[-*]\s*\[TODO[:\s]+([^\]]+)\](.*)$"
                            markdown_for_html = _re.sub(
                                todo_pattern,
                                r"\1- [ ] \2",
                                markdown_for_html,
                                flags=_re.MULTILINE | _re.IGNORECASE,
                            )
                            try:
                                import markdown

                                op["value"] = markdown.markdown(markdown_for_html, extensions=["fenced_code", "tables"])
                            except ImportError:
                                pass
                            break
                    try:
                        resp = requests.patch(url, headers=headers, json=operations_html, timeout=30)
                        resp.raise_for_status()
                        response = resp
                    except requests.HTTPError:
                        console.print(f"[bold red]✗[/bold red] {user_msg}")
                        raise

            if response is None:
                console.print(f"[bold red]✗[/bold red] {user_msg}")
                raise

        updated_work_item = response.json()

        # Store format metadata in provider_fields for round-trip
        if hasattr(item, "provider_fields") and isinstance(item.provider_fields, dict):
            item.provider_fields["description_format"] = "Markdown"
            item.provider_fields["description_markdown"] = item.body_markdown

        # Convert back to BacklogItem
        from specfact_cli.backlog.converter import convert_ado_work_item_to_backlog_item

        return convert_ado_work_item_to_backlog_item(
            updated_work_item,
            provider="ado",
            base_url=self.base_url,
            org=self.org,
            project_name=self.project,
        )
