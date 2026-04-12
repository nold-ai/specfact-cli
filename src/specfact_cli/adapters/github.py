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
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlparse

import requests
from beartype import beartype
from icontract import ensure, require
from rich.console import Console

from specfact_cli.adapters.backlog_base import BacklogAdapterMixin
from specfact_cli.adapters.base import BridgeAdapter
from specfact_cli.backlog.adapters.base import BacklogAdapter
from specfact_cli.backlog.filters import BacklogFilters
from specfact_cli.backlog.mappers.github_mapper import GitHubFieldMapper
from specfact_cli.models.backlog_item import BacklogItem
from specfact_cli.models.bridge import BridgeConfig
from specfact_cli.models.capabilities import ToolCapabilities
from specfact_cli.models.change import ChangeProposal, ChangeTracking
from specfact_cli.models.source_tracking import SourceTracking
from specfact_cli.registry.bridge_registry import BRIDGE_PROTOCOL_REGISTRY
from specfact_cli.runtime import debug_log_operation, is_debug_mode
from specfact_cli.utils.auth_tokens import get_token
from specfact_cli.utils.icontract_helpers import (
    ensure_backlog_update_preserves_identity,
    require_bundle_dir_exists,
    require_repo_path_exists,
    require_repo_path_is_dir,
)


@dataclass
class _IssueBodyRenderInput:
    title: str
    description: str
    rationale: str
    impact: str
    change_id: str
    raw_body: str | None
    preserved_sections: list[str] | None = None


@dataclass
class _IssueStatusCommentInput:
    proposal_data: dict[str, Any]
    repo_owner: str
    repo_name: str
    issue_number: int
    code_repo_path: Path | None
    payload: dict[str, Any]
    current_state: str
    status: str
    title: str


@dataclass(frozen=True)
class _SignificantChangeCommentInput:
    repo_owner: str
    repo_name: str
    issue_number: int
    change_id: str
    title: str
    description: str
    rationale: str


console = Console()


def _as_str_dict(obj: dict[Any, Any]) -> dict[str, Any]:
    """Narrow a runtime ``dict`` to ``dict[str, Any]`` for static analysis."""
    return cast(dict[str, Any], obj)


def _github_resolve_linked_issue_id_from_dict(linked: dict[str, Any]) -> str:
    linked_id = str(linked.get("id") or linked.get("number") or "").strip()
    if linked_id:
        return linked_id
    linked_url = str(linked.get("url") or "")
    linked_match = re.search(r"/issues/(\d+)", linked_url, flags=re.IGNORECASE)
    return linked_match.group(1) if linked_match else ""


def _github_tuple_for_linked_relation(relation: str, issue_id: str, linked_id: str) -> tuple[str, str, str]:
    rel = relation.strip().lower()
    if rel in {"blocks", "block"}:
        return issue_id, linked_id, "blocks"
    if rel in {"blocked_by", "blocked by"}:
        return linked_id, issue_id, "blocks"
    if rel in {"parent", "parent_of"}:
        return linked_id, issue_id, "parent"
    if rel in {"child", "child_of"}:
        return issue_id, linked_id, "parent"
    return issue_id, linked_id, "relates"


def _github_linked_issue_edge(issue_id: str, linked: dict[str, Any]) -> tuple[str, str, str] | None:
    relation = str(linked.get("relation") or linked.get("type") or "").strip().lower()
    linked_id = _github_resolve_linked_issue_id_from_dict(linked)
    if not linked_id:
        return None
    return _github_tuple_for_linked_relation(relation, issue_id, linked_id)


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


class GitHubAdapter(BridgeAdapter, BacklogAdapterMixin, BacklogAdapter):
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
        token_source = "none"
        if api_token:
            self.api_token = api_token
            token_source = "explicit"
        elif os.environ.get("GITHUB_TOKEN"):
            self.api_token = os.environ.get("GITHUB_TOKEN")
            token_source = "env"
        elif stored_token:
            self.api_token = stored_token.get("access_token")
            token_source = "stored"
        elif use_gh_cli:
            self.api_token = _get_github_token_from_gh_cli()
            if self.api_token:
                token_source = "gh_cli"
        else:
            self.api_token = None

        env_api_url = os.environ.get("GITHUB_API_URL")
        stored_api_url = stored_token.get("api_base_url") if stored_token else None
        if token_source == "stored":
            self.base_url = stored_api_url or env_api_url or "https://api.github.com"
        else:
            self.base_url = env_api_url or stored_api_url or "https://api.github.com"

    @staticmethod
    def _is_feature_branch(branch: str) -> bool:
        """Return whether the branch name matches a work branch prefix."""
        return any(prefix in branch for prefix in ["feature/", "bugfix/", "hotfix/"])

    @staticmethod
    def _dedupe_strings(values: list[str]) -> list[str]:
        """Preserve order while removing duplicate strings."""
        unique_values: list[str] = []
        seen: set[str] = set()
        for value in values:
            if value and value not in seen:
                unique_values.append(value)
                seen.add(value)
        return unique_values

    @staticmethod
    def _normalize_change_id_words(change_id: str) -> tuple[str, list[str]]:
        """Return normalized change id and significant component words."""
        normalized_change_id = change_id.lower().replace("-", "").replace("_", "")
        change_id_words = [word for word in change_id.lower().replace("-", "_").split("_") if len(word) > 3]
        return normalized_change_id, change_id_words

    def _match_branch_for_change_id(self, branches: list[str], change_id: str | None) -> str | None:
        """Prefer a branch whose name best matches the active change id."""
        if not change_id:
            return None
        normalized_change_id, change_id_words = self._normalize_change_id_words(change_id)
        for branch in branches:
            if not self._is_feature_branch(branch):
                continue
            normalized_branch = branch.lower().replace("-", "").replace("_", "").replace("/", "")
            if normalized_change_id in normalized_branch:
                return branch
            if change_id_words:
                branch_words = [
                    word for word in branch.lower().replace("-", "_").replace("/", "_").split("_") if len(word) > 3
                ]
                if sum(1 for word in change_id_words if word in branch_words) >= 2:
                    return branch
        return None

    def _preferred_branch(self, branches: list[str], change_id: str | None = None) -> str | None:
        """Pick the best branch from a candidate list."""
        deduped_branches = self._dedupe_strings(branches)
        change_branch = self._match_branch_for_change_id(deduped_branches, change_id)
        if change_branch:
            return change_branch
        for branch in deduped_branches:
            if self._is_feature_branch(branch):
                return branch
        return deduped_branches[0] if deduped_branches else None

    @staticmethod
    def _entry_branch_candidates(entry: dict[str, Any]) -> list[str]:
        """Collect branch-like fields from a source-tracking entry."""
        source_metadata = entry.get("source_metadata")
        metadata_dict: dict[str, Any] = source_metadata if isinstance(source_metadata, dict) else {}
        values = [
            entry.get("branch"),
            entry.get("source_branch"),
            metadata_dict.get("branch"),
            metadata_dict.get("source_branch"),
        ]
        return [value for value in values if isinstance(value, str) and value.strip()]

    def _run_git_lines(self, repo_path: Path, args: list[str], timeout: int = 10) -> list[str]:
        """Run a git command and return non-empty output lines."""
        result = subprocess.run(
            ["git", *args],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode != 0:
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def _find_feature_branch_from_commits(
        self,
        repo_path: Path,
        commit_hashes: list[str],
        change_id: str | None = None,
    ) -> str | None:
        """Resolve the best branch for a sequence of commit hashes."""
        for commit_hash in commit_hashes:
            branch = self._find_branch_containing_commit(commit_hash, repo_path)
            if branch and self._is_feature_branch(branch):
                return branch
        if commit_hashes:
            return self._find_branch_containing_commit(commit_hashes[0], repo_path)
        return None

    @staticmethod
    def _coerce_issue_datetime(value: Any) -> str:
        """Normalize GitHub timestamp values to ISO strings."""
        if not value:
            return datetime.now(UTC).isoformat()
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).isoformat()
        except (ValueError, AttributeError):
            return datetime.now(UTC).isoformat()

    def _resolve_issue_state(self, proposal_data: dict[str, Any], status: str) -> str:
        """Resolve the GitHub issue state from cross-adapter or OpenSpec state."""
        source_state = proposal_data.get("source_state")
        source_type = proposal_data.get("source_type")
        if source_state and source_type and source_type != "github":
            from specfact_cli.adapters.registry import AdapterRegistry

            source_adapter = AdapterRegistry.get_adapter(source_type)
            if source_adapter and hasattr(source_adapter, "map_backlog_state_between_adapters"):
                return source_adapter.map_backlog_state_between_adapters(source_state, source_type, self)  # type: ignore[attr-defined]
        should_close = status in ("applied", "deprecated", "discarded")
        return "closed" if should_close else "open"

    @staticmethod
    def _resolve_state_reason(status: str) -> str | None:
        """Resolve GitHub state_reason for a proposal status."""
        if status == "applied":
            return "completed"
        if status in ("deprecated", "discarded"):
            return "not_planned"
        return None

    @staticmethod
    def _collect_issue_body_lines(section_title: str, section_body: str) -> list[str]:
        """Render a markdown section while preserving original line breaks."""
        if not section_body:
            return []
        lines = [f"## {section_title}", ""]
        lines.extend(section_body.strip().split("\n"))
        lines.append("")
        return lines

    def _render_issue_body(self, body_in: _IssueBodyRenderInput) -> str:
        """Render GitHub issue body from proposal fields and optional preserved sections."""
        title = body_in.title
        description = body_in.description
        rationale = body_in.rationale
        impact = body_in.impact
        change_id = body_in.change_id
        raw_body = body_in.raw_body
        preserved_sections = body_in.preserved_sections
        if raw_body:
            return raw_body

        body_parts: list[str] = []
        display_title = re.sub(r"^\[change\]\s*", "", title, flags=re.IGNORECASE).strip()
        if display_title:
            body_parts.extend([f"# {display_title}", ""])

        body_parts.extend(self._collect_issue_body_lines("Why", rationale))
        body_parts.extend(self._collect_issue_body_lines("What Changes", description))
        body_parts.extend(self._collect_issue_body_lines("Impact", impact))

        if not body_parts or (not rationale and not description):
            body_parts.extend(["No description provided.", ""])

        preview = "\n".join(body_parts)
        for preserved in preserved_sections or []:
            preserved_clean = preserved.strip()
            if preserved_clean and preserved_clean not in preview:
                body_parts.extend(["", preserved_clean])

        if not any("OpenSpec Change Proposal:" in line for line in body_parts):
            body_parts.extend(["---", f"*OpenSpec Change Proposal: `{change_id}`*"])
        return "\n".join(body_parts)

    @staticmethod
    def _extract_markdown_section(body: str, heading: str, stop_pattern: str) -> str:
        """Extract a markdown section body until the next relevant heading or footer."""
        if not body:
            return ""
        match = re.search(
            rf"##\s+{heading}\s*\n(.*?)(?={stop_pattern}|\Z)",
            body,
            re.DOTALL | re.IGNORECASE,
        )
        return match.group(1).strip() if match else ""

    @staticmethod
    def _body_without_openspec_footer(body: str) -> str:
        """Strip the OpenSpec metadata footer from a GitHub issue body."""
        return re.sub(r"\n---\s*\n\*OpenSpec Change Proposal:.*", "", body, flags=re.DOTALL).strip()

    def _extract_issue_sections(self, body: str) -> tuple[str, str, str]:
        """Extract rationale, description, and impact sections from issue body markdown."""
        rationale = self._extract_markdown_section(
            body,
            "Why",
            r"\n##\s+What\s+Changes\s|\n##\s+Impact\s|\n---\s*\n\*OpenSpec Change Proposal:",
        )
        description = self._extract_markdown_section(
            body,
            r"What\s+Changes",
            r"\n##\s+Impact\s|\n---\s*\n\*OpenSpec Change Proposal:",
        )
        impact = self._extract_markdown_section(
            body,
            "Impact",
            r"\n---\s*\n\*OpenSpec Change Proposal:",
        )
        if not description and not rationale:
            description = self._body_without_openspec_footer(body)
        return rationale, description, impact

    @staticmethod
    def _extract_change_id_from_body(body: str) -> str | None:
        """Extract change id from legacy body footer if present."""
        change_id_match = re.search(r"OpenSpec Change Proposal:\s*`([^`]+)`", body, re.IGNORECASE)
        return change_id_match.group(1) if change_id_match else None

    def _extract_change_id_from_comments(self, issue_number: Any) -> str | None:
        """Extract change id from issue comments using known OpenSpec comment formats."""
        if not issue_number or not self.repo_owner or not self.repo_name:
            return None
        openspec_patterns = [
            r"\*\*Change ID\*\*[:\s]+`([a-z0-9-]+)`",
            r"Change ID[:\s]+`([a-z0-9-]+)`",
            r"OpenSpec Change Proposal[:\s]+`?([a-z0-9-]+)`?",
            r"\*OpenSpec Change Proposal:\s*`([a-z0-9-]+)`",
        ]
        comments = self._get_issue_comments(self.repo_owner, self.repo_name, issue_number)
        for comment in comments:
            comment_body = str(comment.get("body", ""))
            for pattern in openspec_patterns:
                match = re.search(pattern, comment_body, re.IGNORECASE | re.DOTALL)
                if match:
                    return match.group(1)
        return None

    def _extract_stakeholders_from_body(self, body: str) -> tuple[str | None, list[str]]:
        """Extract owner and stakeholders from a `## Who` section."""
        owner: str | None = None
        stakeholders: list[str] = []
        who_content = self._extract_markdown_section(body, "Who", r"\n##\s")
        if not who_content:
            return owner, stakeholders
        owner_match = re.search(r"(?:Owner|owner):\s*(.+)", who_content, re.IGNORECASE)
        if owner_match:
            owner = owner_match.group(1).strip()
        stakeholders_match = re.search(r"(?:Stakeholders|stakeholders):\s*(.+)", who_content, re.IGNORECASE)
        if stakeholders_match:
            stakeholders = [s.strip() for s in re.split(r"[,\n]", stakeholders_match.group(1).strip()) if s.strip()]
        return owner, stakeholders

    def _extract_optional_issue_fields(
        self, item_data: dict[str, Any], body: str
    ) -> tuple[str | None, str | None, list[str]]:
        """Extract optional timeline, owner, and stakeholder values from issue data."""
        timeline = self._extract_markdown_section(body, "When", r"\n##\s") if body else None
        owner, stakeholders = self._extract_stakeholders_from_body(body)
        assignees_raw = item_data.get("assignees", [])
        assignees = assignees_raw if isinstance(assignees_raw, list) else []
        if assignees and not owner:
            first = assignees[0]
            owner = _as_str_dict(first).get("login", "") if isinstance(first, dict) else str(first)
        if assignees:
            stakeholders.extend(
                _as_str_dict(assignee).get("login", "") if isinstance(assignee, dict) else str(assignee)
                for assignee in assignees
            )
        return timeline, owner, self._dedupe_strings(stakeholders)

    def _extract_change_id_from_issue(self, item_data: dict[str, Any], body: str) -> str:
        """Resolve change id from body, comments, or issue number fallback."""
        change_id = self._extract_change_id_from_body(body)
        if not change_id:
            change_id = self._extract_change_id_from_comments(item_data.get("number"))
        return change_id or str(item_data.get("number", "unknown"))

    def _status_from_labels(self, labels: list[Any]) -> str:
        """Resolve OpenSpec status from GitHub labels."""
        label_names = [
            _as_str_dict(label).get("name", "") if isinstance(label, dict) else str(label) for label in labels
        ]
        for label_name in label_names:
            mapped_status = self.map_backlog_status_to_openspec(label_name)
            if mapped_status != "proposed":
                return mapped_status
        return "proposed"

    @staticmethod
    def _labels_from_payload(issue_type: str, priority: str, story_points: Any) -> list[str]:
        """Build the GitHub labels for provider-agnostic create_issue payloads."""
        labels = [issue_type] if issue_type else []
        if priority:
            labels.append(f"priority:{priority.lower()}")
        if story_points is not None:
            labels.append(f"story-points:{story_points}")
        return labels

    def _build_issue_search_query(self, filters: BacklogFilters) -> str:
        """Build the GitHub search query for backlog issue fetches."""
        query_parts = [f"repo:{self.repo_owner}/{self.repo_name}", "type:issue"]
        if filters.state:
            normalized_state = BacklogFilters.normalize_filter_value(filters.state) or filters.state
            query_parts.append(f"state:{normalized_state}")
        if filters.assignee:
            assignee_value = filters.assignee.lstrip("@")
            normalized_assignee_value = BacklogFilters.normalize_filter_value(assignee_value)
            query_parts.append("assignee:@me" if normalized_assignee_value == "me" else f"assignee:{assignee_value}")
        if filters.labels:
            query_parts.extend(f"label:{label}" for label in filters.labels)
        if filters.search:
            query_parts.append(filters.search)
        return " ".join(query_parts)

    def _search_github_issues(self, query: str) -> list[BacklogItem]:
        """Run a GitHub issue search and convert results to backlog items."""
        from specfact_cli.backlog.converter import convert_github_issue_to_backlog_item

        url = f"{self.base_url}/search/issues"
        headers = {
            "Authorization": f"token {self.api_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        params = {"q": query, "per_page": 100}
        items: list[BacklogItem] = []
        page = 1
        while True:
            params["page"] = page
            response = self._request_with_retry(lambda: requests.get(url, headers=headers, params=params, timeout=30))
            response.raise_for_status()
            issues = response.json().get("items", [])
            if not issues:
                return items
            items.extend(convert_github_issue_to_backlog_item(issue, provider="github") for issue in issues)
            if len(issues) < 100:
                return items
            page += 1

    @staticmethod
    def _graph_type_alias_map() -> dict[str, str]:
        """Return normalized graph type aliases."""
        return {
            "epic": "epic",
            "feature": "feature",
            "story": "story",
            "user story": "story",
            "task": "task",
            "bug": "bug",
            "sub-task": "sub_task",
            "sub task": "sub_task",
            "subtask": "sub_task",
        }

    @staticmethod
    def _normalize_graph_value_with_aliases(raw_value: str, alias_map: dict[str, str]) -> str | None:
        """Normalize a graph-type string against the alias map."""
        normalized = raw_value.strip().lower().replace("_", " ").replace("-", " ")
        if not normalized:
            return None
        if normalized in alias_map:
            return alias_map[normalized]
        for separator in (":", "/"):
            if separator in normalized:
                suffix = normalized.split(separator)[-1].strip()
                if suffix in alias_map:
                    return alias_map[suffix]
        for token, mapped in alias_map.items():
            if normalized.startswith(f"{token} ") or normalized.endswith(f" {token}"):
                return mapped
        return None

    @staticmethod
    def _project_type_config(provider_fields: dict[str, Any] | None) -> tuple[str, str, dict[str, Any]] | None:
        """Extract GitHub Projects v2 type configuration if present."""
        if not isinstance(provider_fields, dict):
            return None
        pf = _as_str_dict(provider_fields)
        project_cfg_raw = pf.get("github_project_v2")
        if not isinstance(project_cfg_raw, dict):
            return None
        project_cfg = _as_str_dict(project_cfg_raw)
        project_id = str(project_cfg.get("project_id") or "").strip()
        type_field_id = str(project_cfg.get("type_field_id") or "").strip()
        option_map = project_cfg.get("type_option_ids")
        if not project_id or not type_field_id or not isinstance(option_map, dict):
            return None
        return project_id, type_field_id, option_map

    @staticmethod
    def _body_relationship_matches(body: str) -> list[tuple[str, str, str]]:
        """Extract body-defined relationships as normalized edge tuples."""
        patterns = [
            (r"(?im)\bblocks?\s+#(\d+)\b", "blocks", False),
            (r"(?im)\bblocked\s+by\s+#(\d+)\b", "blocks", True),
            (r"(?im)\bdepends\s+on\s+#(\d+)\b", "blocks", True),
            (r"(?im)\bparent\s*[:#]?\s*#(\d+)\b", "parent", True),
            (r"(?im)\bchild(?:ren)?\s*[:#]?\s*#(\d+)\b", "parent", False),
            (r"(?im)\b(?:related\s+to|relates?\s+to|refs?|references?)\s+#(\d+)\b", "relates", False),
        ]
        matches: list[tuple[str, str, str]] = []
        for pattern, relation_type, reverse in patterns:
            for match in re.finditer(pattern, body):
                linked_id = match.group(1)
                matches.append((linked_id, relation_type, "reverse" if reverse else "forward"))
        return matches

    @staticmethod
    def _normalize_graph_item_type(raw_value: str) -> str | None:
        """Normalize GitHub issue type aliases to graph item types."""
        return GitHubAdapter._normalize_graph_value_with_aliases(
            raw_value,
            GitHubAdapter._graph_type_alias_map(),
        )

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
    @ensure(lambda result: isinstance(result, str), "Must return issue state string")
    def map_openspec_status_to_issue_state(self, status: str) -> str:
        """
        Map OpenSpec change status to GitHub issue state (open/closed).

        Args:
            status: OpenSpec change status (proposed, in-progress, applied, deprecated, discarded)

        Returns:
            GitHub issue state: "open" or "closed"

        Note:
            This method is used for cross-adapter state mapping where we need the
            actual issue state, not labels. For label mapping, use map_openspec_status_to_backlog().
        """
        # Map OpenSpec status to GitHub issue state
        # "applied", "deprecated", "discarded" → closed
        # "proposed", "in-progress" → open
        if status in ("applied", "deprecated", "discarded"):
            return "closed"
        return "open"

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

            For cross-adapter state mapping (issue state, not labels), use map_openspec_status_to_issue_state().
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
        - Change ID (from body footer or comments)
        - Other optional fields (timeline, owner, stakeholders, dependencies)

        Args:
            item_data: GitHub issue data (dict from API response)

        Returns:
            Dict with change proposal fields:
            - title: str
            - description: str (What Changes section)
            - rationale: str (Why section)
            - change_id: str (extracted from body footer or comments)
            - status: str (mapped to OpenSpec status)
            - Other optional fields

        Raises:
            ValueError: If required fields are missing or data is malformed

        Note:
            This implements the tool-agnostic metadata extraction pattern for GitHub.
            Future backlog adapters should implement similar parsing for their tools.

            Change ID extraction priority:
            1. Body footer (legacy format): *OpenSpec Change Proposal: `id`*
            2. Comments (new format): **Change ID**: `id` in OpenSpec Change Proposal Reference comment
            3. Issue number (fallback, normalized during shared proposal import)
        """
        if not isinstance(item_data, dict):
            msg = "GitHub issue data must be dict"
            raise ValueError(msg)

        # Extract title
        title = item_data.get("title", "Untitled Change Proposal")
        if not title:
            msg = "GitHub issue must have a title"
            raise ValueError(msg)

        body = item_data.get("body", "") or ""
        rationale, description, impact = self._extract_issue_sections(body)
        change_id = self._extract_change_id_from_issue(item_data, body)
        labels = item_data.get("labels", [])
        status = self._status_from_labels(labels if isinstance(labels, list) else [])
        created_at = self._coerce_issue_datetime(item_data.get("created_at"))
        timeline, owner, stakeholders = self._extract_optional_issue_fields(item_data, body)
        dependencies: list[str] = []

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
            "stakeholders": stakeholders,
            "dependencies": dependencies,
        }

    @beartype
    @require(require_repo_path_exists, "Repository path must exist")
    @require(require_repo_path_is_dir, "Repository path must be a directory")
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
                # Use proper URL parsing to avoid substring matching vulnerabilities
                # Look for URL patterns in git config and validate the hostname
                # Match: https?://, ssh://, git://, and scp-style git@host:path URLs
                url_pattern = re.compile(r"url\s*=\s*(https?://[^\s]+|ssh://[^\s]+|git://[^\s]+|git@[^:]+:[^\s]+)")
                # Official GitHub SSH hostnames
                github_ssh_hosts = {"github.com", "ssh.github.com"}
                for match in url_pattern.finditer(config_content):
                    url_str = match.group(1)
                    # Handle scp-style git@ format: git@github.com:user/repo.git or git@ssh.github.com:user/repo.git
                    if url_str.startswith("git@"):
                        host_part = url_str.split(":")[0].replace("git@", "").lower()
                        if host_part in github_ssh_hosts:
                            return True
                    else:
                        # Parse HTTP/HTTPS/SSH/GIT URLs properly
                        parsed = urlparse(url_str)
                        if parsed.hostname:
                            hostname_lower = parsed.hostname.lower()
                            # Check for GitHub hostnames (github.com for all schemes, ssh.github.com for SSH)
                            if hostname_lower == "github.com":
                                return True
                            if parsed.scheme == "ssh" and hostname_lower == "ssh.github.com":
                                return True
            except Exception:
                pass

        # Check bridge config for external GitHub repo
        return bool(bridge_config and bridge_config.adapter.value == "github")

    @beartype
    @require(require_repo_path_exists, "Repository path must exist")
    @require(require_repo_path_is_dir, "Repository path must be a directory")
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
        issue_payload = self._require_import_issue_payload(artifact_key, artifact_path)

        # Check bridge_config.external_base_path for cross-repo support
        if bridge_config and bridge_config.external_base_path:
            # Cross-repo import: use external_base_path for OpenSpec repository
            pass  # Path operations will respect external_base_path in OpenSpec adapter

        # Import GitHub issue as change proposal using backlog adapter pattern
        proposal = self.import_backlog_item_as_proposal(issue_payload, "github", bridge_config)

        if not proposal:
            msg = "Failed to import GitHub issue as change proposal"
            raise ValueError(msg)

        self._persist_imported_issue_metadata(proposal, issue_payload)

        # Add proposal to project bundle change tracking
        self._attach_imported_proposal(project_bundle, proposal)

    @staticmethod
    def _require_import_issue_payload(artifact_key: str, artifact_path: Path | dict[str, Any]) -> dict[str, Any]:
        """Validate artifact type and payload shape for GitHub issue imports."""
        if artifact_key != "github_issue":
            msg = f"Unsupported artifact key for import: {artifact_key}. Supported: github_issue"
            raise NotImplementedError(msg)
        if isinstance(artifact_path, dict):
            return artifact_path
        msg = "GitHub issue import requires dict (API response), not Path"
        raise ValueError(msg)

    def _persist_imported_issue_metadata(self, proposal: ChangeProposal, issue_payload: dict[str, Any]) -> None:
        """Store raw issue data and backlog linkage metadata for round-trip sync."""
        if not proposal.source_tracking or not isinstance(proposal.source_tracking.source_metadata, dict):
            return
        source_metadata = proposal.source_tracking.source_metadata
        self._store_raw_issue_metadata(source_metadata, issue_payload)
        self._store_import_backlog_entry(source_metadata, issue_payload, proposal.status)

    @staticmethod
    def _store_raw_issue_metadata(source_metadata: dict[str, Any], issue_payload: dict[str, Any]) -> None:
        """Preserve the raw GitHub issue title/body in source metadata."""
        source_metadata["raw_title"] = issue_payload.get("title") or ""
        source_metadata["raw_body"] = issue_payload.get("body") or ""
        source_metadata["raw_format"] = "markdown"
        source_metadata.setdefault("source_type", "github")

    def _store_import_backlog_entry(
        self,
        source_metadata: dict[str, Any],
        issue_payload: dict[str, Any],
        proposal_status: str,
    ) -> None:
        """Record or refresh the backlog entry metadata for an imported GitHub issue."""
        source_repo = self._extract_repo_from_issue(issue_payload)
        if source_repo:
            source_metadata.setdefault("source_repo", source_repo)
        entry = self._build_import_backlog_entry(issue_payload, source_repo, proposal_status)
        if not entry.get("source_id"):
            return
        entries = source_metadata.get("backlog_entries")
        source_metadata["backlog_entries"] = self._merged_backlog_entries(entries, entry, source_repo)

    @staticmethod
    def _build_import_backlog_entry(
        issue_payload: dict[str, Any],
        source_repo: str | None,
        proposal_status: str,
    ) -> dict[str, Any]:
        """Build the normalized backlog-entry record for an imported GitHub issue."""
        entry_id = issue_payload.get("number") or issue_payload.get("id")
        github_state = str(issue_payload.get("state", "open") or "open").lower()
        return {
            "source_id": str(entry_id) if entry_id is not None else None,
            "source_url": issue_payload.get("html_url") or issue_payload.get("url") or "",
            "source_type": "github",
            "source_repo": source_repo or "",
            "source_metadata": {
                "last_synced_status": proposal_status,
                "source_state": github_state,
            },
        }

    @staticmethod
    def _merged_backlog_entries(
        existing_entries: Any,
        entry: dict[str, Any],
        source_repo: str | None,
    ) -> list[dict[str, Any]]:
        """Merge an imported backlog entry into the existing list by repo or source id."""
        normalized_entries: list[dict[str, Any]] = (
            [_as_str_dict(existing) for existing in existing_entries if isinstance(existing, dict)]
            if isinstance(existing_entries, list)
            else []
        )
        for existing in normalized_entries:
            if source_repo and existing.get("source_repo") == source_repo:
                existing.update(entry)
                return normalized_entries
            if not source_repo and existing.get("source_id") == entry.get("source_id"):
                existing.update(entry)
                return normalized_entries
        normalized_entries.append(entry)
        return normalized_entries

    @staticmethod
    def _attach_imported_proposal(project_bundle: Any, proposal: ChangeProposal) -> None:
        """Attach imported proposal to the project bundle change-tracking map when present."""
        if not hasattr(project_bundle, "change_tracking"):
            return
        if not project_bundle.change_tracking:
            from specfact_cli.models.change import ChangeTracking

            project_bundle.change_tracking = ChangeTracking()
        project_bundle.change_tracking.proposals[proposal.name] = proposal

    def _issue_number_from_source_tracking_model(self, source_tracking: SourceTracking, target_repo: str) -> Any | None:
        source_metadata = source_tracking.source_metadata
        if not isinstance(source_metadata, dict):
            return None
        if source_metadata.get("source_repo") == target_repo:
            return source_metadata.get("source_id")
        source_url = source_metadata.get("source_url", "")
        if source_url and target_repo in str(source_url):
            return source_metadata.get("source_id")
        return source_metadata.get("source_id")

    def _issue_number_from_tracking_entries(self, entries: list[Any], target_repo: str) -> Any | None:
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            ed = _as_str_dict(entry)
            entry_repo = ed.get("source_repo")
            if entry_repo == target_repo:
                return ed.get("source_id")
            if not entry_repo:
                source_url = ed.get("source_url", "")
                if source_url and target_repo in source_url:
                    return ed.get("source_id")
        return None

    def _resolve_issue_number_from_tracking(
        self,
        source_tracking: SourceTracking | dict[str, Any] | list[Any],
        repo_owner: str,
        repo_name: str,
    ) -> Any | None:
        """Resolve issue number for a specific repository from source_tracking (list or dict)."""
        target_repo = f"{repo_owner}/{repo_name}"
        if isinstance(source_tracking, SourceTracking):
            return self._issue_number_from_source_tracking_model(source_tracking, target_repo)
        if isinstance(source_tracking, list):
            return self._issue_number_from_tracking_entries(source_tracking, target_repo)
        if isinstance(source_tracking, dict):
            return _as_str_dict(source_tracking).get("source_id")
        return None

    def _handle_proposal_comment_artifact(
        self,
        artifact_data: Any,
        repo_owner: str,
        repo_name: str,
    ) -> dict[str, Any]:
        """Handle the change_proposal_comment artifact key sub-case."""
        source_tracking = artifact_data.get("source_tracking", {})
        issue_number = self._resolve_issue_number_from_tracking(source_tracking, repo_owner, repo_name)
        if not issue_number:
            msg = "Issue number required for comment (missing in source_tracking for this repository)"
            raise ValueError(msg)

        status = artifact_data.get("status", "proposed")
        title = artifact_data.get("title", "Untitled Change Proposal")
        change_id = artifact_data.get("change_id", "")
        code_repo_path_str = artifact_data.get("_code_repo_path")
        code_repo_path = Path(code_repo_path_str) if code_repo_path_str else None

        # Add change_id to source_tracking entries for branch inference
        if isinstance(source_tracking, list):
            st_list: list[Any] = []
            for entry in source_tracking:
                if not isinstance(entry, dict):
                    st_list.append(entry)
                    continue
                ed = _as_str_dict(entry)
                entry_copy = dict(ed)
                if not entry_copy.get("change_id"):
                    entry_copy["change_id"] = change_id
                st_list.append(entry_copy)
            source_tracking_resolved = st_list
        elif isinstance(source_tracking, dict):
            st_dict: dict[str, Any] = dict(_as_str_dict(source_tracking))
            if not st_dict.get("change_id"):
                st_dict["change_id"] = change_id
            source_tracking_resolved = st_dict
        else:
            source_tracking_resolved = source_tracking

        comment_text = self._get_status_comment(status, title, source_tracking_resolved, code_repo_path)
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

    def _handle_code_change_progress_artifact(
        self,
        artifact_data: Any,
        repo_owner: str,
        repo_name: str,
        bridge_config: BridgeConfig | None,
    ) -> dict[str, Any]:
        """Handle the code_change_progress artifact key sub-case."""
        source_tracking = artifact_data.get("source_tracking", {})
        issue_number = self._resolve_issue_number_from_tracking(source_tracking, repo_owner, repo_name)
        if not issue_number:
            msg = "Issue number required for progress comment (missing in source_tracking for this repository)"
            raise ValueError(msg)

        sanitize = artifact_data.get("sanitize", False)
        if bridge_config and hasattr(bridge_config, "sanitize"):
            sanitize = bridge_config.sanitize if bridge_config.sanitize is not None else sanitize  # type: ignore[attr-defined]

        return self._add_progress_comment(artifact_data, repo_owner, repo_name, int(issue_number), sanitize=sanitize)

    def _export_change_proposal_update_artifact(
        self, artifact_data: Any, repo_owner: str, repo_name: str
    ) -> dict[str, Any]:
        source_tracking = artifact_data.get("source_tracking", {})
        issue_number = self._resolve_issue_number_from_tracking(source_tracking, repo_owner, repo_name)
        if not issue_number:
            msg = "Issue number required for content update (missing in source_tracking for this repository)"
            raise ValueError(msg)
        code_repo_path_str = artifact_data.get("_code_repo_path")
        code_repo_path = Path(code_repo_path_str) if code_repo_path_str else None
        return self._update_issue_body(artifact_data, repo_owner, repo_name, int(issue_number), code_repo_path)

    def _export_github_artifact_dispatch(
        self,
        artifact_key: str,
        artifact_data: Any,
        repo_owner: str,
        repo_name: str,
        bridge_config: BridgeConfig | None,
    ) -> dict[str, Any]:
        if artifact_key == "change_proposal":
            return self._create_issue_from_proposal(artifact_data, repo_owner, repo_name)
        if artifact_key == "change_status":
            return self._update_issue_status(artifact_data, repo_owner, repo_name)
        if artifact_key == "change_proposal_update":
            return self._export_change_proposal_update_artifact(artifact_data, repo_owner, repo_name)
        if artifact_key == "change_proposal_comment":
            return self._handle_proposal_comment_artifact(artifact_data, repo_owner, repo_name)
        if artifact_key == "code_change_progress":
            return self._handle_code_change_progress_artifact(artifact_data, repo_owner, repo_name, bridge_config)
        msg = f"Unsupported artifact key: {artifact_key}. Supported: change_proposal, change_status, change_proposal_update, code_change_progress"
        raise ValueError(msg)

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
                "  5. Run `specfact backlog auth github` for device code authentication"
            )
            raise ValueError(msg)

        # Resolve repository owner/name from config or instance
        repo_owner = self.repo_owner or (bridge_config and getattr(bridge_config, "repo_owner", None))
        repo_name = self.repo_name or (bridge_config and getattr(bridge_config, "repo_name", None))

        if not repo_owner or not repo_name:
            msg = "GitHub repository owner and name required. Provide via --repo-owner and --repo-name or bridge config"
            raise ValueError(msg)

        return self._export_github_artifact_dispatch(artifact_key, artifact_data, repo_owner, repo_name, bridge_config)

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
        if is_debug_mode():
            debug_log_operation(
                "github_api_get",
                url,
                str(response.status_code),
                error=None if response.ok else (response.text[:200] if response.text else None),
            )
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
            source_metadata = _as_str_dict(source_tracking).get("source_metadata")
        elif source_tracking is not None and hasattr(source_tracking, "source_metadata"):
            source_metadata = source_tracking.source_metadata

        if isinstance(source_metadata, dict):
            sm = _as_str_dict(source_metadata)
            raw_title = raw_title or sm.get("raw_title")
            raw_body = raw_body or sm.get("raw_body")

        return raw_title, raw_body

    @beartype
    @require(require_repo_path_exists, "Repository path must exist")
    @require(require_repo_path_is_dir, "Repository path must be a directory")
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
    @require(require_bundle_dir_exists, "Bundle directory must exist")
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
    @require(require_bundle_dir_exists, "Bundle directory must exist")
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
    @require(require_bundle_dir_exists, "Bundle directory must exist")
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
    @require(require_bundle_dir_exists, "Bundle directory must exist")
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

        body = self._render_issue_body(
            _IssueBodyRenderInput(title, description, rationale, impact, change_id, raw_body)
        )

        # Check for API token before making request
        if not self.api_token:
            msg = (
                "GitHub API token required to create issues. Options:\n"
                "  1. Set GITHUB_TOKEN environment variable\n"
                "  2. Use --github-token option\n"
                "  3. Use GitHub CLI authentication (gh auth login)\n"
                "  4. Store token via specfact backlog auth github"
            )
            raise ValueError(msg)

        # Create issue via GitHub API
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/issues"
        headers = {
            "Authorization": f"token {self.api_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        # Determine issue state based on proposal status
        # Check if source_state and source_type are provided (from cross-adapter sync)
        issue_state = self._resolve_issue_state(proposal_data, status)
        state_reason = self._resolve_state_reason(status)

        payload = {
            "title": title,
            "body": body,
            "labels": self._get_labels_for_status(status),
            "state": issue_state,
        }
        if state_reason:
            payload["state_reason"] = state_reason

        try:
            response = self._request_with_retry(
                lambda: requests.post(url, json=payload, headers=headers, timeout=30),
                retry_on_ambiguous_transport=False,
            )
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
        target_repo = f"{repo_owner}/{repo_name}"
        issue_number = self._resolve_issue_number_from_tracking(source_tracking, repo_owner, repo_name)

        if not issue_number:
            msg = (
                f"Issue number not found in source_tracking for repository {target_repo}. Issue must be created first."
            )
            raise ValueError(msg)

        status = proposal_data.get("status", "proposed")
        title = proposal_data.get("title", "Untitled")

        # Map status to GitHub issue state and comment
        # Check if source_state and source_type are provided (from cross-adapter sync)
        issue_state = self._resolve_issue_state(proposal_data, status)
        should_close = issue_state == "closed"
        source_tracking = proposal_data.get("source_tracking", {})
        # Note: code_repo_path not available in _update_issue_status context
        comment_text = self._get_status_comment(status, title, source_tracking, None)

        # Map status to GitHub state_reason
        state_reason = self._resolve_state_reason(status)

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
            response = self._request_with_retry(lambda: requests.patch(url, json=payload, headers=headers, timeout=30))
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

    def _get_issue_comments(self, repo_owner: str, repo_name: str, issue_number: int) -> list[dict[str, Any]]:
        """
        Fetch comments for a GitHub issue.

        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            issue_number: Issue number

        Returns:
            List of comment dicts with 'body' field, or empty list on error
        """
        if not self.api_token:
            return []

        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/issues/{issue_number}/comments"
        headers = {
            "Authorization": f"token {self.api_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            # Return empty list on error - comments are optional
            return []

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
            self._request_with_retry(
                lambda: requests.post(url, json=payload, headers=headers, timeout=30),
                retry_on_ambiguous_transport=False,
            )
        except requests.RequestException as e:
            # Log but don't fail - comment is non-critical
            console.print(f"[yellow]⚠[/yellow] Failed to add comment to issue #{issue_number}: {e}")

    def _fetch_issue_snapshot(self, repo_owner: str, repo_name: str, issue_number: int) -> tuple[str, str, str]:
        """Fetch current issue body, title, and state for preservation-aware updates."""
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/issues/{issue_number}"
        headers = {
            "Authorization": f"token {self.api_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            issue_data = response.json()
            return (
                issue_data.get("body", "") or "",
                issue_data.get("title", "") or "",
                issue_data.get("state", "open"),
            )
        except requests.RequestException:
            return "", "", "open"

    @staticmethod
    def _preserved_issue_sections(current_body: str, change_id: str) -> list[str]:
        """Extract non-OpenSpec sections to preserve during issue body rewrites."""
        if not current_body:
            return []
        metadata_marker = f"*OpenSpec Change Proposal: `{change_id}`*"
        if metadata_marker not in current_body:
            return []
        _, after_marker = current_body.split(metadata_marker, 1)
        preserved_content = after_marker.strip()
        if preserved_content and (
            "##" in preserved_content or "- [" in preserved_content or "* [" in preserved_content
        ):
            return [preserved_content]
        return []

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
        change_id = str(proposal_data.get("change_id", "unknown"))
        status = proposal_data.get("status", "proposed")
        raw_title, raw_body = self._extract_raw_fields(proposal_data)
        if raw_title:
            title = raw_title

        current_body, current_title, current_state = self._fetch_issue_snapshot(repo_owner, repo_name, issue_number)
        preserved_sections = self._preserved_issue_sections(current_body, change_id)
        body = self._render_issue_body(
            _IssueBodyRenderInput(title, description, rationale, impact, change_id, raw_body, preserved_sections)
        )

        # Update issue body via GitHub API PATCH
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/issues/{issue_number}"
        headers = {
            "Authorization": f"token {self.api_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        desired_state = self._resolve_issue_state(proposal_data, status)
        state_reason = self._resolve_state_reason(status)
        payload = self._issue_body_update_payload(
            body, title, current_title, current_state, desired_state, state_reason
        )

        try:
            response = self._request_with_retry(lambda: requests.patch(url, json=payload, headers=headers, timeout=30))
            issue_data = response.json()
            self._add_issue_status_comment(
                _IssueStatusCommentInput(
                    proposal_data,
                    repo_owner,
                    repo_name,
                    issue_number,
                    code_repo_path,
                    payload,
                    current_state,
                    status,
                    title,
                )
            )
            self._add_significant_change_comment(
                _SignificantChangeCommentInput(
                    repo_owner,
                    repo_name,
                    issue_number,
                    change_id,
                    title,
                    description,
                    rationale,
                )
            )

            return {
                "issue_number": issue_data["number"],
                "issue_url": issue_data["html_url"],
                "state": issue_data["state"],
            }
        except requests.RequestException as e:
            msg = f"Failed to update GitHub issue #{issue_number} body: {e}"
            console.print(f"[bold red]✗[/bold red] {msg}")
            raise

    @staticmethod
    def _issue_body_update_payload(
        body: str,
        title: str,
        current_title: str,
        current_state: str,
        desired_state: str,
        state_reason: str | None,
    ) -> dict[str, Any]:
        """Build the PATCH payload for issue body/title/state updates."""
        payload: dict[str, Any] = {"body": body}
        if current_title != title:
            payload["title"] = title
        if current_state == desired_state:
            return payload
        payload["state"] = desired_state
        if state_reason:
            payload["state_reason"] = state_reason
        return payload

    def _add_issue_status_comment(self, comment_in: _IssueStatusCommentInput) -> None:
        """Add or refresh the status comment when closing or re-syncing applied issues."""
        proposal_data = comment_in.proposal_data
        repo_owner = comment_in.repo_owner
        repo_name = comment_in.repo_name
        issue_number = comment_in.issue_number
        code_repo_path = comment_in.code_repo_path
        payload = comment_in.payload
        current_state = comment_in.current_state
        status = comment_in.status
        title = comment_in.title
        if not self._should_add_issue_status_comment(payload, current_state, status):
            return
        source_tracking = proposal_data.get("source_tracking", {})
        target_repo = f"{repo_owner}/{repo_name}"
        comment_text = self._get_status_comment(status, title, source_tracking, code_repo_path, target_repo)
        if not comment_text:
            return
        status_change_note = self._status_comment_note(comment_text, payload, current_state, status)
        self._add_issue_comment(repo_owner, repo_name, issue_number, status_change_note)

    @staticmethod
    def _should_add_issue_status_comment(payload: dict[str, Any], current_state: str, status: str) -> bool:
        """Determine whether the issue update should emit a status comment."""
        if payload.get("state") == "closed" and current_state == "open":
            return True
        return status == "applied" and current_state == "closed"

    @staticmethod
    def _status_comment_note(comment_text: str, payload: dict[str, Any], current_state: str, status: str) -> str:
        """Compose the sync status note appended to issue comments."""
        if payload.get("state") == "closed" and current_state == "open":
            return (
                f"{comment_text}\n\n"
                f"*Note: This issue was automatically closed because the change proposal "
                f"status changed to `{status}`. This issue was updated from an OpenSpec change proposal.*"
            )
        return (
            f"{comment_text}\n\n*Note: This issue was updated from an OpenSpec change proposal with status `{status}`.*"
        )

    def _add_significant_change_comment(self, sig: _SignificantChangeCommentInput) -> None:
        """Add a review nudge when proposal text indicates a significant change."""
        repo_owner = sig.repo_owner
        repo_name = sig.repo_name
        issue_number = sig.issue_number
        change_id = sig.change_id
        title = sig.title
        description = sig.description
        rationale = sig.rationale
        if not self._is_significant_issue_update(title, description, rationale):
            return
        comment_text = (
            "**Significant change detected**: This issue has been updated with new proposal content.\n\n"
            f"*Updated: {change_id}*\n\n"
            "Please review the changes above. This update may include breaking changes or major scope modifications."
        )
        self._add_issue_comment(repo_owner, repo_name, issue_number, comment_text)

    @staticmethod
    def _is_significant_issue_update(title: str, description: str, rationale: str) -> bool:
        """Detect whether updated issue text should trigger a significant-change comment."""
        combined_text = f"{title.lower()} {description.lower()} {rationale.lower()}"
        significant_keywords = ["breaking", "major", "scope change"]
        return any(keyword in combined_text for keyword in significant_keywords)

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

        issue_number = self._resolve_issue_number_from_tracking(source_tracking, repo_owner, repo_name)

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
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            current_issue = response.json()
            current_labels = [label.get("name", "") for label in current_issue.get("labels", [])]
            status_labels = ["in-progress", "completed", "deprecated", "wontfix"]
            keep_labels = [label for label in current_labels if label not in status_labels and label != "openspec"]
            all_labels = self._dedupe_strings(keep_labels + new_labels)

            # Update issue labels
            patch_url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/issues/{issue_number}"
            patch_payload = {"labels": all_labels}

            self._request_with_retry(lambda: requests.patch(patch_url, json=patch_payload, headers=headers, timeout=30))

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
        labels_raw = issue_data.get("labels", [])
        labels = labels_raw if isinstance(labels_raw, list) else []
        github_status = "open"  # Default
        if labels:
            label_names = [
                _as_str_dict(label).get("name", "") if isinstance(label, dict) else str(label) for label in labels
            ]
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
                repo_path_to_check = self._find_code_repo_path(source_repo)

        for branch in self._entry_branch_candidates(entry):
            if not repo_path_to_check or self._verify_branch_exists(branch, repo_path_to_check):
                return branch

        if repo_path_to_check:
            detected_branch = self._detect_implementation_branch(entry, repo_path_to_check)
            if detected_branch:
                return detected_branch

        change_id = entry.get("change_id")
        if change_id:
            possible_branches = [f"feature/{change_id}", f"bugfix/{change_id}", f"hotfix/{change_id}"]
            if repo_path_to_check:
                return next(
                    (branch for branch in possible_branches if self._verify_branch_exists(branch, repo_path_to_check)),
                    None,
                )
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
            local_branches = [
                line.replace("*", "").strip()
                for line in self._run_git_lines(repo_path, ["branch", "--list", branch_name], timeout=5)
            ]
            if branch_name in local_branches:
                return True

            remote_branches = [
                parts[1]
                for line in self._run_git_lines(repo_path, ["branch", "-r", "--list", f"*/{branch_name}"], timeout=5)
                for parts in [line.split("/", 1)]
                if len(parts) == 2
            ]
            return branch_name in remote_branches
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
        for candidate in self._code_repo_candidates(repo_name):
            if self._is_matching_repo_candidate(candidate, repo_name):
                return candidate

        return None

    @staticmethod
    def _code_repo_candidates(repo_name: str) -> list[Path]:
        """Build local path candidates for a repository name."""
        cwd = Path.cwd()
        candidates = [cwd, cwd.parent / repo_name]
        grandparent = cwd.parent.parent if cwd.parent != Path("/") else None
        if grandparent:
            candidates.extend(
                sibling for sibling in grandparent.iterdir() if sibling.is_dir() and sibling.name == repo_name
            )
        return candidates

    def _is_matching_repo_candidate(self, candidate: Path, repo_name: str) -> bool:
        """Return whether a local directory looks like the requested code repository."""
        try:
            if not candidate.exists() or not (candidate / ".git").exists() or candidate.name != repo_name:
                return False
            if candidate != Path.cwd():
                return True
            remote_url_lines = self._run_git_lines(candidate, ["remote", "get-url", "origin"], timeout=5)
            return bool(remote_url_lines and repo_name in remote_url_lines[0])
        except Exception:
            return False

    @staticmethod
    def _metadata_values(metadata_dict: dict[str, Any], entry: dict[str, Any], *keys: str) -> list[Any]:
        """Collect candidate metadata values from entry and source metadata."""
        values: list[Any] = []
        for key in keys:
            values.extend([metadata_dict.get(key), entry.get(key)])
        return values

    def _branch_from_metadata(self, entry: dict[str, Any], repo_path: Path, change_id: str | None) -> str | None:
        """Resolve branch from commit and file metadata embedded in a source tracking entry."""
        source_metadata = entry.get("source_metadata", {})
        metadata_dict = source_metadata if isinstance(source_metadata, dict) else {}
        for commit_hash in self._metadata_values(metadata_dict, entry, "commit", "commit_hash"):
            if commit_hash:
                branch = self._find_branch_containing_commit(str(commit_hash), repo_path)
                if branch:
                    return branch
        issue_number = entry.get("source_id")
        if change_id:
            self._current_change_id = change_id
        for files_changed in self._metadata_values(metadata_dict, entry, "files", "files_changed"):
            if files_changed:
                branch = self._find_branch_containing_files(files_changed, repo_path, issue_number)
                if branch:
                    return branch
        return None

    def _branch_from_change_reference(self, change_id: str | None, repo_path: Path, issue_number: Any) -> str | None:
        """Resolve branch from issue-number and change-id commit references."""
        issue_number_text = str(issue_number) if issue_number is not None else None
        if issue_number_text:
            branch = self._find_branch_by_change_id_in_commits("", repo_path, issue_number_text)
            if branch:
                return branch
        if change_id:
            return self._find_branch_by_change_id_in_commits(change_id, repo_path, None)
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

            branch = self._branch_from_metadata(entry, repo_path, change_id)
            if branch:
                return branch
            branch = self._branch_from_change_reference(change_id, repo_path, issue_number)
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

            branches = [
                branch.replace("origin/", "") if branch.startswith("origin/") else branch
                for branch in self._run_git_lines(
                    repo_path,
                    ["branch", "-a", "--contains", commit_hash, "--format=%(refname:short)"],
                    timeout=5,
                )
            ]
            if branches:
                return self._preferred_branch(branches, getattr(self, "_current_change_id", None))

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
            file_args = self._tracked_file_args(files)
            branch = self._branch_for_issue_pattern(
                repo_path, file_args, issue_number, getattr(self, "_current_change_id", None)
            )
            if branch:
                return branch
            change_id = getattr(self, "_current_change_id", None)
            branch = self._branch_for_change_id_files(repo_path, file_args, change_id)
            if branch:
                return branch
            non_main_commits = self._run_git_lines(
                repo_path,
                [
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
            )
            branch = self._find_feature_branch_from_commits(repo_path, non_main_commits[:20], change_id)
            if branch:
                return branch
            fallback_commits = self._run_git_lines(repo_path, ["log", "--all", "--format=%H", "-30", "--", *file_args])
            return self._find_feature_branch_from_commits(repo_path, fallback_commits, change_id)

        except Exception:
            pass

        return None

    @staticmethod
    def _tracked_file_args(files: list[str] | str) -> list[str]:
        """Normalize tracked file arguments for git log commands."""
        normalized_files = [files] if isinstance(files, str) else list(files)
        return normalized_files[:10]

    def _branch_for_issue_pattern(
        self, repo_path: Path, file_args: list[str], issue_number: str | None, change_id: str | None
    ) -> str | None:
        """Find a feature branch from issue-number commit patterns touching target files."""
        if not issue_number:
            return None
        patterns = [f"#{issue_number}", f"fixes #{issue_number}", f"closes #{issue_number}"]
        for pattern in patterns:
            commit_hashes = self._run_git_lines(
                repo_path,
                ["log", "--all", "--grep", pattern, "--format=%H", "--", *file_args],
            )
            if commit_hashes:
                branch = self._find_feature_branch_from_commits(repo_path, commit_hashes, change_id)
                if branch:
                    return branch
        return None

    def _branch_for_change_id_files(self, repo_path: Path, file_args: list[str], change_id: str | None) -> str | None:
        """Find a feature branch from change-id tagged commits touching target files."""
        if not change_id:
            return None
        commit_lines = self._run_git_lines(
            repo_path,
            ["log", "--all", "--grep", change_id, "--format=%H|%s", "-i", "--no-merges", "--", *file_args],
        )
        for line in commit_lines[:10]:
            commit_hash, _, subject = line.partition("|")
            if any(word in subject.lower() for word in ["merge", "chore:", "docs:"]):
                continue
            branch = self._find_branch_containing_commit(commit_hash, repo_path)
            if branch and self._is_feature_branch(branch):
                return branch
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
            if issue_number:
                return self._branch_for_issue_reference(repo_path, change_id, issue_number)
            if change_id:
                return self._branch_for_change_id_reference(repo_path, change_id)

        except Exception:
            pass

        return None

    def _branch_for_issue_reference(self, repo_path: Path, change_id: str, issue_number: str) -> str | None:
        """Find a feature branch from issue-number commit references."""
        patterns = [f"#{issue_number}", f"fixes #{issue_number}", f"closes #{issue_number}"]
        for pattern in patterns:
            commit_hashes = self._run_git_lines(
                repo_path, ["log", "--all", "--grep", pattern, "--format=%H", "-n", "10"]
            )
            branch = self._find_feature_branch_from_commits(repo_path, commit_hashes, change_id)
            if branch:
                return branch
        return None

    def _branch_for_change_id_reference(self, repo_path: Path, change_id: str) -> str | None:
        """Find a feature branch from change-id commit references with implementation-style subjects."""
        commit_lines = self._run_git_lines(
            repo_path,
            ["log", "--all", "--grep", change_id, "--format=%H|%s", "-i", "--no-merges", "-n", "20"],
        )
        for line in commit_lines:
            commit_hash, _, subject = line.partition("|")
            if any(word in subject.lower() for word in ["merge", "chore:", "docs:"]):
                continue
            has_implementation_keyword = any(word in subject.lower() for word in ["implement", "feat:"])
            has_change_id = change_id.lower() in subject.lower()
            if has_implementation_keyword and has_change_id:
                branch = self._find_branch_containing_commit(commit_hash, repo_path)
                if branch and self._is_feature_branch(branch):
                    return branch
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

    # BacklogAdapter interface implementations

    @beartype
    @ensure(lambda result: isinstance(result, str) and len(result) > 0, "Must return non-empty adapter name")
    def name(self) -> str:
        """Get the adapter name."""
        return "github"

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
        Fetch GitHub issues matching the specified filters.

        Uses GitHub Search API to find issues matching the filters.
        """
        if not self.api_token:
            msg = "GitHub API token required to fetch backlog items"
            raise ValueError(msg)

        if not self.repo_owner or not self.repo_name:
            msg = "repo_owner and repo_name required to fetch backlog items"
            raise ValueError(msg)

        if filters.issue_id:
            direct_item = self._fetch_backlog_item_by_id(filters.issue_id)
            direct_items = [direct_item] if direct_item is not None else []
            return self._apply_backlog_post_filters(direct_items, filters)

        items = self._search_github_issues(self._build_issue_search_query(filters))

        return self._apply_backlog_post_filters(items, filters)

    @beartype
    def _fetch_backlog_item_by_id(self, issue_id: str) -> BacklogItem | None:
        """Fetch a single GitHub issue by number for deterministic ID lookup flows."""
        normalized_id = issue_id.strip().lstrip("#")
        if not normalized_id:
            return None

        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/issues/{normalized_id}"
        headers = {
            "Authorization": f"token {self.api_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        try:
            response = self._request_with_retry(lambda: requests.get(url, headers=headers, timeout=30))
            response.raise_for_status()
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code == 404:
                return None
            raise

        issue_payload = response.json()
        if not isinstance(issue_payload, dict):
            return None
        ip = _as_str_dict(issue_payload)
        if ip.get("pull_request") is not None:
            # Backlog issue commands should not resolve pull requests.
            return None

        from specfact_cli.backlog.converter import convert_github_issue_to_backlog_item

        return convert_github_issue_to_backlog_item(issue_payload, provider="github")

    @beartype
    def _apply_backlog_post_filters(self, items: list[BacklogItem], filters: BacklogFilters) -> list[BacklogItem]:
        """Apply post-fetch filters for both search and direct ID lookup paths."""
        filtered_items = self._filter_backlog_items_by_state(items, filters.state)
        filtered_items = self._filter_backlog_items_by_assignee(filtered_items, filters.assignee)
        filtered_items = self._filter_backlog_items_by_labels(filtered_items, filters.labels)
        filtered_items = self._filter_backlog_items_by_attributes(filtered_items, filters)
        return (
            filtered_items[: filters.limit]
            if filters.limit is not None and len(filtered_items) > filters.limit
            else filtered_items
        )

    @staticmethod
    def _filter_backlog_items_by_state(items: list[BacklogItem], raw_state: str | None) -> list[BacklogItem]:
        """Filter backlog items by normalized state."""
        if not raw_state:
            return items
        normalized_state = BacklogFilters.normalize_filter_value(raw_state)
        return [item for item in items if BacklogFilters.normalize_filter_value(item.state) == normalized_state]

    @staticmethod
    def _item_matches_assignee(item: BacklogItem, normalized_assignee: str | None) -> bool:
        """Return whether a backlog item matches the normalized assignee filter."""
        if not normalized_assignee:
            return False
        provider_assignee = ""
        if isinstance(item.provider_fields, dict):
            provider_assignee = str(item.provider_fields.get("assignee_login") or "")
        return any(
            BacklogFilters.normalize_filter_value(assignee) == normalized_assignee
            for assignee in [*item.assignees, provider_assignee]
            if assignee
        )

    @staticmethod
    def _filter_backlog_items_by_assignee(items: list[BacklogItem], assignee_filter: str | None) -> list[BacklogItem]:
        """Filter backlog items by normalized assignee."""
        if not assignee_filter:
            return items
        normalized_assignee = BacklogFilters.normalize_filter_value(assignee_filter.lstrip("@"))
        if normalized_assignee == "me":
            return items
        return [item for item in items if GitHubAdapter._item_matches_assignee(item, normalized_assignee)]

    @staticmethod
    def _filter_backlog_items_by_labels(items: list[BacklogItem], labels: list[str] | None) -> list[BacklogItem]:
        """Filter backlog items by normalized label membership."""
        if not labels:
            return items
        normalized_labels = {
            normalized_label
            for normalized_label in (BacklogFilters.normalize_filter_value(raw_label) for raw_label in labels)
            if normalized_label
        }
        return [
            item
            for item in items
            if any(
                normalized_tag in normalized_labels
                for normalized_tag in (BacklogFilters.normalize_filter_value(tag) for tag in item.tags)
                if normalized_tag
            )
        ]

    @staticmethod
    def _filter_backlog_items_by_attributes(items: list[BacklogItem], filters: BacklogFilters) -> list[BacklogItem]:
        """Filter backlog items by iteration, sprint, and release attributes."""
        filtered_items = items
        for attribute_name, raw_value in (
            ("iteration", filters.iteration),
            ("sprint", filters.sprint),
            ("release", filters.release),
        ):
            if not raw_value:
                continue
            normalized_value = BacklogFilters.normalize_filter_value(raw_value)
            filtered_items = [
                item
                for item in filtered_items
                if getattr(item, attribute_name)
                and BacklogFilters.normalize_filter_value(getattr(item, attribute_name)) == normalized_value
            ]
        return filtered_items

    @staticmethod
    def _linked_issue_edge(issue_id: str, linked: dict[str, Any]) -> tuple[str, str, str] | None:
        """Normalize a provider linked-issue record into a relationship edge."""
        return _github_linked_issue_edge(issue_id, linked)

    def _issue_relationship_edges(self, issue: dict[str, Any], issue_id: str) -> list[tuple[str, str, str]]:
        """Collect relationship edges from provider fields and body text."""
        edges: list[tuple[str, str, str]] = []
        provider_fields = issue.get("provider_fields")
        if isinstance(provider_fields, dict):
            linked_issues = _as_str_dict(provider_fields).get("linked_issues", [])
            if isinstance(linked_issues, list):
                for linked in linked_issues:
                    if isinstance(linked, dict):
                        edge = self._linked_issue_edge(issue_id, linked)
                        if edge:
                            edges.append(edge)
        body = str(issue.get("body_markdown") or issue.get("description") or "")
        for linked_id, relation_type, direction in self._body_relationship_matches(body):
            if direction == "reverse":
                edges.append((linked_id, issue_id, relation_type))
            else:
                edges.append((issue_id, linked_id, relation_type))
        return edges

    @beartype
    def _github_graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        """Execute GitHub GraphQL request and return `data` payload."""
        headers = {
            "Authorization": f"token {self.api_token}",
            "Accept": "application/vnd.github+json",
        }
        response = self._request_with_retry(
            lambda: requests.post(
                f"{self.base_url}/graphql",
                json={"query": query, "variables": variables},
                headers=headers,
                timeout=30,
            )
        )
        payload_raw = response.json()
        if not isinstance(payload_raw, dict):
            raise ValueError("GitHub GraphQL response must be an object")
        payload = _as_str_dict(payload_raw)
        errors = payload.get("errors")
        if isinstance(errors, list) and errors:
            raise ValueError(f"GitHub GraphQL errors: {errors}")
        data = payload.get("data")
        return data if isinstance(data, dict) else {}

    @staticmethod
    @beartype
    def _resolve_github_type_mapping_id(mapping: dict[str, Any], issue_type: str) -> str:
        """
        Resolve GitHub issue-type/project-type mapping id with fallback aliases.

        Default alias fallback:
        - `story` -> `user story` when custom type exists.
        - `story` -> `feature` when `story` is unavailable in the repository.
        """
        normalized = issue_type.strip().lower()
        candidate_keys = [issue_type, normalized]
        if normalized == "story":
            candidate_keys.extend(["user story", "feature", "Feature"])
        for key in candidate_keys:
            mapped = str(mapping.get(key) or "").strip()
            if mapped:
                return mapped
        return ""

    @beartype
    def _try_set_github_issue_type(
        self,
        issue_node_id: str,
        issue_type: str,
        provider_fields: dict[str, Any] | None,
    ) -> None:
        """Best-effort GitHub issue type update using repository issue-type ids."""
        if not issue_node_id or not isinstance(provider_fields, dict):
            return

        pf = _as_str_dict(provider_fields)
        issue_cfg_raw = pf.get("github_issue_types")
        if not isinstance(issue_cfg_raw, dict):
            return
        issue_cfg = _as_str_dict(issue_cfg_raw)
        type_ids = issue_cfg.get("type_ids")
        if not isinstance(type_ids, dict):
            return

        issue_type_id = self._resolve_github_type_mapping_id(type_ids, issue_type)
        if not issue_type_id:
            return

        mutation = (
            "mutation($issueId: ID!, $issueTypeId: ID!) { "
            "updateIssue(input: {id: $issueId, issueTypeId: $issueTypeId}) { issue { id } } "
            "}"
        )
        try:
            self._github_graphql(
                mutation,
                {"issueId": issue_node_id, "issueTypeId": issue_type_id},
            )
        except (requests.RequestException, ValueError) as error:
            console.print(f"[yellow]⚠[/yellow] Could not set GitHub issue Type automatically: {error}")

    @beartype
    def _try_link_github_sub_issue(
        self,
        owner: str,
        repo: str,
        parent_ref: Any,
        sub_issue_node_id: str,
    ) -> None:
        """Best-effort native GitHub parent/sub-issue link using sidebar relationship."""
        if not sub_issue_node_id:
            return

        parent_raw = str(parent_ref or "").strip()
        if not parent_raw:
            return

        parent_number_text = parent_raw.removeprefix("#")
        if not parent_number_text.isdigit():
            return
        parent_number = int(parent_number_text)

        parent_query = (
            "query($owner:String!, $repo:String!, $number:Int!) { "
            "repository(owner:$owner, name:$repo) { issue(number:$number) { id } } "
            "}"
        )
        link_mutation = (
            "mutation($parentIssueId:ID!, $subIssueId:ID!) { "
            "addSubIssue(input:{ issueId:$parentIssueId, subIssueId:$subIssueId, replaceParent:true }) { "
            "issue { id } subIssue { id } "
            "} "
            "}"
        )

        try:
            parent_data = self._github_graphql(
                parent_query,
                {"owner": owner, "repo": repo, "number": parent_number},
            )
            pd = _as_str_dict(parent_data)
            repository = pd.get("repository")
            repository_d = _as_str_dict(repository) if isinstance(repository, dict) else None
            issue = repository_d.get("issue") if repository_d is not None else None
            issue_d = _as_str_dict(issue) if isinstance(issue, dict) else None
            parent_issue_id = str(issue_d.get("id") or "").strip() if issue_d is not None else ""
            if not parent_issue_id:
                return
            self._github_graphql(
                link_mutation,
                {"parentIssueId": parent_issue_id, "subIssueId": sub_issue_node_id},
            )
        except (requests.RequestException, ValueError) as error:
            console.print(f"[yellow]⚠[/yellow] Could not create native GitHub parent/sub-issue link: {error}")

    def _try_set_github_project_type_field(
        self,
        issue_node_id: str,
        issue_type: str,
        provider_fields: dict[str, Any] | None,
    ) -> None:
        """Best-effort GitHub Projects v2 Type field update for created issues."""
        if not issue_node_id or not isinstance(provider_fields, dict):
            return

        project_settings = self._project_type_config(provider_fields)
        if not project_settings:
            return

        project_id, type_field_id, option_map = project_settings

        option_id = self._resolve_github_type_mapping_id(option_map, issue_type)
        if not option_id:
            return

        add_item_mutation = (
            "mutation($projectId: ID!, $contentId: ID!) { "
            "addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) { item { id } }"
            " }"
        )
        set_type_mutation = (
            "mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) { "
            "updateProjectV2ItemFieldValue(input: {"
            "projectId: $projectId, itemId: $itemId, fieldId: $fieldId, "
            "value: { singleSelectOptionId: $optionId }"
            "}) { projectV2Item { id } }"
            " }"
        )

        try:
            add_data = self._github_graphql(
                add_item_mutation,
                {"projectId": project_id, "contentId": issue_node_id},
            )
            add_d = _as_str_dict(add_data)
            add_result = add_d.get("addProjectV2ItemById")
            add_result_d = _as_str_dict(add_result) if isinstance(add_result, dict) else None
            item = add_result_d.get("item") if add_result_d is not None else None
            item_d = _as_str_dict(item) if isinstance(item, dict) else None
            item_id = str(item_d.get("id") or "").strip() if item_d is not None else ""
            if not item_id:
                return
            self._github_graphql(
                set_type_mutation,
                {
                    "projectId": project_id,
                    "itemId": item_id,
                    "fieldId": type_field_id,
                    "optionId": option_id,
                },
            )
        except (requests.RequestException, ValueError) as error:
            console.print(f"[yellow]⚠[/yellow] Could not set GitHub Projects Type field automatically: {error}")

    @beartype
    @require(
        lambda project_id: isinstance(project_id, str) and len(project_id.strip()) > 0, "project_id must be non-empty"
    )
    @require(lambda payload: isinstance(payload, dict), "payload must be dict")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def create_issue(self, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a GitHub issue from provider-agnostic backlog payload."""
        owner, repo = project_id.split("/", 1) if "/" in project_id else (self.repo_owner, self.repo_name)
        if not owner or not repo:
            raise ValueError(
                "GitHub project_id must be '<owner>/<repo>' or adapter must be configured with repo_owner/repo_name"
            )
        if not self.api_token:
            raise ValueError("GitHub API token required to create issues")

        title = self._required_issue_title(payload)
        issue_type = str(payload.get("type") or "task").strip().lower()
        body = self._create_issue_body(payload)
        labels = self._labels_from_payload(
            issue_type, str(payload.get("priority") or "").strip(), payload.get("story_points")
        )
        url = f"{self.base_url}/repos/{owner}/{repo}/issues"
        headers = {
            "Authorization": f"token {self.api_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        response = self._request_with_retry(
            lambda: requests.post(
                url,
                json={"title": title, "body": body, "labels": labels},
                headers=headers,
                timeout=30,
            ),
            retry_on_ambiguous_transport=False,
        )
        created = response.json()
        self._apply_create_issue_post_hooks(owner, repo, created, payload, issue_type)

        canonical_issue_number = str(created.get("number") or created.get("id") or "")
        return {
            "id": canonical_issue_number,
            "key": canonical_issue_number,
            "url": str(created.get("html_url") or created.get("url") or ""),
        }

    def _apply_create_issue_post_hooks(
        self,
        owner: str,
        repo: str,
        created: dict[str, Any],
        payload: dict[str, Any],
        issue_type: str,
    ) -> None:
        issue_node_id = str(created.get("node_id") or "").strip()
        parent_id = payload.get("parent_id")
        if parent_id:
            self._try_link_github_sub_issue(owner, repo, parent_id, issue_node_id)
        provider_fields = payload.get("provider_fields")
        if not isinstance(provider_fields, dict):
            return
        self._try_set_github_issue_type(issue_node_id, issue_type, provider_fields)
        self._try_set_github_project_type_field(issue_node_id, issue_type, provider_fields)

    @staticmethod
    def _required_issue_title(payload: dict[str, Any]) -> str:
        """Return required issue title or raise for missing payload.title."""
        title = str(payload.get("title") or "").strip()
        if not title:
            raise ValueError("payload.title is required")
        return title

    @staticmethod
    def _create_issue_body(payload: dict[str, Any]) -> str:
        """Build GitHub issue body from provider-agnostic payload."""
        description_format = str(payload.get("description_format") or "markdown").strip().lower()
        body = str(payload.get("description") or payload.get("body") or "").strip()
        acceptance_criteria = str(payload.get("acceptance_criteria") or "").strip()
        if acceptance_criteria:
            acceptance_block = (
                f"Acceptance Criteria:\n{acceptance_criteria}"
                if description_format == "classic"
                else f"## Acceptance Criteria\n{acceptance_criteria}"
            )
            body = f"{body}\n\n{acceptance_block}".strip() if body else acceptance_block
        parent_id = payload.get("parent_id")
        if parent_id:
            parent_line = f"Parent: #{parent_id}"
            body = f"{body}\n\n{parent_line}".strip() if body else parent_line
        return body

    def _get_repo_owner_name(self) -> tuple[str | None, str | None]:
        """Query: return current repo_owner and repo_name without mutation."""
        return self.repo_owner, self.repo_name

    def _set_repo_owner_name(self, owner: str | None, repo: str | None) -> None:
        """Command: set repo_owner and repo_name without reading current state."""
        self.repo_owner = owner
        self.repo_name = repo

    @beartype
    @require(lambda project_id: isinstance(project_id, str) and len(project_id) > 0, "project_id must be non-empty")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def fetch_all_issues(self, project_id: str, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Fetch all backlog items as provider-agnostic dictionaries for graph building."""
        saved_owner, saved_repo = self._get_repo_owner_name()
        owner, repo = project_id.split("/", 1) if "/" in project_id else (saved_owner, saved_repo)
        if owner and repo:
            self._set_repo_owner_name(owner, repo)
        try:
            backlog_filters = BacklogFilters(**(filters or {}))
            enriched_items: list[dict[str, Any]] = []
            for item in self.fetch_backlog_items(backlog_filters):
                issue_dict = item.model_dump()
                inferred_type = self._infer_graph_item_type(issue_dict)
                if inferred_type:
                    issue_dict["type"] = inferred_type
                enriched_items.append(issue_dict)
            return enriched_items
        finally:
            self._set_repo_owner_name(saved_owner, saved_repo)

    @beartype
    @require(lambda project_id: isinstance(project_id, str) and len(project_id) > 0, "project_id must be non-empty")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def fetch_relationships(self, project_id: str) -> list[dict[str, Any]]:
        """Fetch relationships for a GitHub backlog project."""
        relationships: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()

        def _add_edge(source_id: str, target_id: str, relation_type: str) -> None:
            source = source_id.strip()
            target = target_id.strip()
            rel = relation_type.strip().lower()
            if not source or not target or source == target:
                return
            key = (source, target, rel)
            if key in seen:
                return
            seen.add(key)
            relationships.append({"source_id": source, "target_id": target, "type": rel})

        issues = self.fetch_all_issues(project_id)
        for issue in issues:
            issue_id = str(issue.get("id") or issue.get("key") or "").strip()
            if not issue_id:
                continue

            for source_id, target_id, relation_type in self._issue_relationship_edges(issue, issue_id):
                _add_edge(source_id, target_id, relation_type)

        return relationships

    @staticmethod
    def _iter_issue_type_candidates(issue_payload: dict[str, Any]) -> Iterator[str]:
        """Yield candidate strings that may encode an issue type."""
        for key in ("type", "work_item_type"):
            value = issue_payload.get(key)
            if isinstance(value, str):
                yield value
            elif isinstance(value, dict):
                vd = _as_str_dict(value)
                for candidate_key in ("name", "title"):
                    candidate_value = vd.get(candidate_key)
                    if isinstance(candidate_value, str):
                        yield candidate_value
        tags = issue_payload.get("tags")
        if isinstance(tags, list):
            for tag in tags:
                if isinstance(tag, str):
                    yield tag

    @beartype
    @ensure(lambda result: result is None or isinstance(result, str), "Type inference must return str or None")
    def _infer_graph_item_type(self, issue_payload: dict[str, Any]) -> str | None:
        """Infer normalized graph item type from GitHub issue payload."""
        for candidate in self._iter_issue_type_candidates(issue_payload):
            mapped = self._normalize_graph_item_type(candidate)
            if mapped:
                return mapped

        title = issue_payload.get("title")
        if isinstance(title, str):
            mapped = self._normalize_graph_item_type(title)
            if mapped:
                return mapped
            for token, mapped_value in self._graph_type_alias_map().items():
                if title.lower().startswith(f"[{token}]"):
                    return mapped_value

        return None

    @beartype
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def supports_add_comment(self) -> bool:
        """Whether this adapter can add comments (requires token and repo)."""
        return bool(self.api_token and self.repo_owner and self.repo_name)

    @beartype
    @require(lambda item: isinstance(item, BacklogItem), "item must be BacklogItem")
    @require(lambda comment: isinstance(comment, str) and bool(comment.strip()), "comment must be non-empty string")
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def add_comment(self, item: BacklogItem, comment: str) -> bool:
        """
        Add a comment to a GitHub issue.

        Args:
            item: BacklogItem to add comment to
            comment: Comment text to add

        Returns:
            True if comment was added successfully, False otherwise
        """
        if not self.api_token:
            return False

        if not self.repo_owner or not self.repo_name:
            return False

        # Extract issue number from item ID or URL
        issue_number: int | None = None
        if item.id.isdigit():
            issue_number = int(item.id)
        elif item.url:
            # Extract from URL like https://github.com/owner/repo/issues/123
            match = re.search(r"/issues/(\d+)", item.url)
            if match:
                issue_number = int(match.group(1))

        if not issue_number:
            return False

        try:
            self._add_issue_comment(self.repo_owner, self.repo_name, issue_number, comment)
            return True
        except Exception:
            return False

    @beartype
    @require(lambda item: isinstance(item, BacklogItem), "item must be BacklogItem")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def get_comments(self, item: BacklogItem) -> list[str]:
        """
        Fetch comments for a GitHub issue.

        Args:
            item: BacklogItem to fetch comments for

        Returns:
            List of comment body strings, or empty list on error
        """
        if not self.repo_owner or not self.repo_name:
            return []
        issue_number: int | None = None
        if item.id.isdigit():
            issue_number = int(item.id)
        elif item.url:
            match = re.search(r"/issues/(\d+)", item.url)
            if match:
                issue_number = int(match.group(1))
        if not issue_number:
            return []
        raw = self._get_issue_comments(self.repo_owner, self.repo_name, issue_number)
        return [str(c.get("body", "")).strip() for c in raw if isinstance(c, dict)]

    @beartype
    @require(lambda item: isinstance(item, BacklogItem), "Item must be BacklogItem")
    @require(
        lambda item, update_fields: update_fields is None or isinstance(update_fields, list),
        "Update fields must be None or list",
    )
    @ensure(lambda result: isinstance(result, BacklogItem), "Must return BacklogItem")
    @ensure(
        lambda result, item: ensure_backlog_update_preserves_identity(result, item),
        "Updated item must preserve id and provider",
    )
    def update_backlog_item(self, item: BacklogItem, update_fields: list[str] | None = None) -> BacklogItem:
        """
        Update a GitHub issue.

        Updates the issue title and/or body based on update_fields.
        """
        if not self.api_token:
            msg = "GitHub API token required to update backlog items"
            raise ValueError(msg)

        if not self.repo_owner or not self.repo_name:
            msg = "repo_owner and repo_name required to update backlog items"
            raise ValueError(msg)

        issue_number = int(item.id)
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}"
        headers = {
            "Authorization": f"token {self.api_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        github_mapper = GitHubFieldMapper()
        canonical_fields = self._canonical_fields_from_item(item, github_mapper)
        github_fields = github_mapper.map_from_canonical(canonical_fields)
        payload = self._issue_update_payload(item, github_fields, update_fields)

        # Update issue
        response = self._request_with_retry(lambda: requests.patch(url, headers=headers, json=payload, timeout=30))
        updated_issue = response.json()

        # Convert back to BacklogItem
        from specfact_cli.backlog.converter import convert_github_issue_to_backlog_item

        return convert_github_issue_to_backlog_item(updated_issue, provider="github")

    @staticmethod
    def _canonical_fields_from_item(
        item: BacklogItem,
        github_mapper: GitHubFieldMapper,
    ) -> dict[str, Any]:
        """Build canonical field payload from refined GitHub issue body or direct item fields."""
        refined_body = item.body_markdown or ""
        has_structured_sections = bool(re.search(r"^##\s+", refined_body, re.MULTILINE))
        if not has_structured_sections:
            return {
                "description": refined_body,
                "acceptance_criteria": item.acceptance_criteria,
                "story_points": item.story_points,
                "business_value": item.business_value,
                "priority": item.priority,
                "value_points": item.value_points,
                "work_item_type": item.work_item_type,
            }
        existing_acceptance_criteria = github_mapper._extract_section(refined_body, "Acceptance Criteria")
        existing_story_points = github_mapper._extract_section(refined_body, "Story Points")
        existing_business_value = github_mapper._extract_section(refined_body, "Business Value")
        existing_priority = github_mapper._extract_section(refined_body, "Priority")
        return {
            "description": github_mapper._extract_default_content(refined_body),
            "acceptance_criteria": existing_acceptance_criteria or item.acceptance_criteria,
            "story_points": int(existing_story_points)
            if existing_story_points and existing_story_points.strip().isdigit()
            else item.story_points,
            "business_value": int(existing_business_value)
            if existing_business_value and existing_business_value.strip().isdigit()
            else item.business_value,
            "priority": int(existing_priority)
            if existing_priority and existing_priority.strip().isdigit()
            else item.priority,
            "value_points": item.value_points,
            "work_item_type": item.work_item_type,
        }

    @staticmethod
    def _issue_update_payload(
        item: BacklogItem, github_fields: dict[str, Any], update_fields: list[str] | None
    ) -> dict[str, Any]:
        """Build GitHub issue update payload from mapped fields."""
        payload: dict[str, Any] = {}
        if update_fields is None or "title" in update_fields:
            payload["title"] = item.title
        if update_fields is None or "body" in update_fields or "body_markdown" in update_fields:
            payload["body"] = github_fields.get("body", item.body_markdown)
        if update_fields is None or "state" in update_fields:
            payload["state"] = item.state
        return payload


BRIDGE_PROTOCOL_REGISTRY.register_implementation("backlog_graph", "github", GitHubAdapter)
