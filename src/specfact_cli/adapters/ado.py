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
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, NoReturn, Protocol, cast
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
from specfact_cli.registry.bridge_registry import BRIDGE_PROTOCOL_REGISTRY
from specfact_cli.runtime import debug_log_operation, debug_print, is_debug_mode
from specfact_cli.utils.auth_tokens import get_token, set_token
from specfact_cli.utils.icontract_helpers import (
    ensure_backlog_update_preserves_identity,
    require_bundle_dir_exists,
    require_repo_path_exists,
    require_repo_path_is_dir,
)


_MAX_RESPONSE_BODY_LOG = 2048
_ADO_STABLE_API_VERSION = "7.1"
_ADO_COMMENTS_API_VERSION = "7.1-preview.4"

console = Console()


@dataclass(frozen=True, slots=True)
class _AdoCreatedWorkItemRef:
    work_item_id: int | str
    work_item_url: str
    org: str
    project: str
    work_item_type: str
    ado_state: str


class _AccessTokenLike(Protocol):
    """Typed subset of Azure access token fields used by refresh logic."""

    token: str
    expires_on: int


def _get_access_token(credential: Any, scopes: list[str]) -> _AccessTokenLike:
    """Return a typed Azure access token from a credential object."""
    get_token_fn = cast(Callable[..., _AccessTokenLike], credential.get_token)
    return get_token_fn(*scopes)


def _as_str_dict(obj: dict[Any, Any]) -> dict[str, Any]:
    """Narrow a runtime ``dict`` to ``dict[str, Any]`` for static analysis."""
    return cast(dict[str, Any], obj)


def _normalize_work_item_data(raw: object) -> dict[str, Any] | None:
    """Return work item payload with common top-level fields mirrored from ``fields``."""
    if not isinstance(raw, dict):
        return None

    work_item_data = cast(dict[str, Any], raw)
    fields_raw = work_item_data.get("fields", {})
    fields = cast(dict[str, Any], fields_raw) if isinstance(fields_raw, dict) else {}
    work_item_data.setdefault("title", str(fields.get("System.Title", "") or ""))
    work_item_data.setdefault("state", str(fields.get("System.State", "") or ""))
    work_item_data.setdefault("description", str(fields.get("System.Description", "") or ""))
    return work_item_data


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


def _extract_ado_proposal_markdown_sections(description_raw: str) -> tuple[str, str, str]:
    """Parse Why / What Changes / Impact from OpenSpec-style ADO description."""
    rationale = ""
    description = ""
    impact = ""
    if not description_raw:
        return rationale, description, impact

    why_match = re.search(
        r"##\s+Why\s*\n(.*?)(?=\n##\s+What\s+Changes\s|\n##\s+Impact\s|\n---\s*\n\*OpenSpec Change Proposal:|\Z)",
        description_raw,
        re.DOTALL | re.IGNORECASE,
    )
    if why_match:
        rationale = why_match.group(1).strip()

    what_match = re.search(
        r"##\s+What\s+Changes\s*\n(.*?)(?=\n##\s+Impact\s|\n---\s*\n\*OpenSpec Change Proposal:|\Z)",
        description_raw,
        re.DOTALL | re.IGNORECASE,
    )
    if what_match:
        description = what_match.group(1).strip()
    elif not why_match:
        body_clean = re.sub(r"\n---\s*\n\*OpenSpec Change Proposal:.*", "", description_raw, flags=re.DOTALL)
        description = body_clean.strip()

    impact_match = re.search(
        r"##\s+Impact\s*\n(.*?)(?=\n---\s*\n\*OpenSpec Change Proposal:|\Z)",
        description_raw,
        re.DOTALL | re.IGNORECASE,
    )
    if impact_match:
        impact = impact_match.group(1).strip()

    return rationale, description, impact


def _parse_when_who_markdown(description_raw: str) -> tuple[str | None, str | None, list[str]]:
    """Extract timeline (When), owner, and stakeholders (Who) from description markdown."""
    timeline: str | None = None
    owner: str | None = None
    stakeholders: list[str] = []
    if not description_raw:
        return timeline, owner, stakeholders

    when_match = re.search(r"##\s+When\s*\n(.*?)(?=\n##|\Z)", description_raw, re.DOTALL | re.IGNORECASE)
    if when_match:
        timeline = when_match.group(1).strip()

    who_match = re.search(r"##\s+Who\s*\n(.*?)(?=\n##|\Z)", description_raw, re.DOTALL | re.IGNORECASE)
    if who_match:
        who_content = who_match.group(1).strip()
        owner_match = re.search(r"(?:Owner|owner):\s*(.+)", who_content, re.IGNORECASE)
        if owner_match:
            owner = owner_match.group(1).strip()
        stakeholders_match = re.search(r"(?:Stakeholders|stakeholders):\s*(.+)", who_content, re.IGNORECASE)
        if stakeholders_match:
            stakeholders_str = stakeholders_match.group(1).strip()
            stakeholders = [s.strip() for s in re.split(r"[,\n]", stakeholders_str) if s.strip()]

    return timeline, owner, stakeholders


_OPENSPEC_COMMENT_CHANGE_ID_PATTERNS = (
    r"\*\*Change ID\*\*[:\s]+`([a-z0-9-]+)`",
    r"Change ID[:\s]+`([a-z0-9-]+)`",
    r"OpenSpec Change Proposal[:\s]+`?([a-z0-9-]+)`?",
    r"\*OpenSpec Change Proposal:\s*`([a-z0-9-]+)`",
)


def _git_run_local(repo_path: Path, args: list[str]) -> tuple[int, str]:
    import subprocess

    result = subprocess.run(
        args,
        cwd=repo_path,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    return result.returncode, result.stdout or ""


def _git_current_branch_name(repo_path: Path) -> str | None:
    rc, out = _git_run_local(repo_path, ["git", "rev-parse", "--abbrev-ref", "HEAD"])
    return out.strip() if rc == 0 else None


def _git_branch_exists_via_local_commands(repo_path: Path, branch_name: str) -> bool:
    """Return True if ``branch_name`` exists in the local repo via successive git checks."""
    if _git_current_branch_name(repo_path) == branch_name:
        return True
    ref = f"refs/heads/{branch_name}"
    for verify_cmd in (
        ["git", "rev-parse", "--verify", "--quiet", ref],
        ["git", "show-ref", "--verify", "--quiet", ref],
    ):
        if _git_run_local(repo_path, verify_cmd)[0] == 0:
            return True
    rc, out = _git_run_local(repo_path, ["git", "branch", "--list", branch_name])
    if rc == 0 and out.strip() and branch_name in _parse_git_branch_list_lines(out):
        return True
    rc, out = _git_run_local(repo_path, ["git", "branch", "-a"])
    if rc == 0 and out.strip() and branch_name in _parse_git_branch_all_lines(out):
        return True
    rc, out = _git_run_local(repo_path, ["git", "branch", "-r", "--list", f"*/{branch_name}"])
    return bool(rc == 0 and out.strip() and branch_name in _parse_git_remote_branch_suffixes(out))


def _parse_git_branch_list_lines(stdout: str) -> list[str]:
    branches: list[str] = []
    for line in stdout.split("\n"):
        line = line.strip()
        if line:
            branch = line.replace("*", "").strip()
            if branch:
                branches.append(branch)
    return branches


def _parse_git_branch_all_lines(stdout: str) -> list[str]:
    all_branches: list[str] = []
    for line in stdout.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("*"):
            branch = line[1:].strip()
        elif line.startswith("remotes/"):
            parts = line.split("/")
            branch = "/".join(parts[2:]) if len(parts) >= 3 else line.replace("remotes/", "").strip()
        else:
            branch = line.strip()
        if branch and branch not in all_branches:
            all_branches.append(branch)
    return all_branches


def _parse_git_remote_branch_suffixes(stdout: str) -> list[str]:
    remote_branches: list[str] = []
    for line in stdout.split("\n"):
        line = line.strip()
        if line and "/" in line:
            parts = line.split("/", 1)
            if len(parts) == 2:
                remote_branches.append(parts[1])
    return remote_branches


def _ambiguous_sprint_error_message(sprint_filter: str, unique_iterations: set[str]) -> str:
    iteration_list = "\n".join(f"  - {it}" for it in sorted(unique_iterations))
    return (
        f"Ambiguous sprint name '{sprint_filter}' matches multiple iteration paths:\n"
        f"{iteration_list}\n"
        f"Please use a full iteration path (e.g., 'Project\\Iteration\\Sprint 01') instead."
    )


def _rich_iteration_suggestions_block(available_iterations: list[str], max_examples: int = 5) -> str:
    suggestions = ""
    if available_iterations:
        examples = available_iterations[:max_examples]
        suggestions = "\n[cyan]Available iteration paths (showing first 5):[/cyan]\n"
        for it_path in examples:
            suggestions += f"  • {it_path}\n"
        if len(available_iterations) > max_examples:
            suggestions += f"  ... and {len(available_iterations) - max_examples} more\n"
    return suggestions


def _ado_graph_edge_from_relation(rel_name: str, item_id: str, target_id: str) -> tuple[str, str, str] | None:
    """Map ADO relation name to (source_id, target_id, edge_type) for backlog graph."""
    r = rel_name.lower()
    if "hierarchy-forward" in r:
        return (item_id, target_id, "parent")
    if "hierarchy-reverse" in r:
        return (target_id, item_id, "parent")
    if "dependency-forward" in r or "predecessor-forward" in r:
        return (item_id, target_id, "blocks")
    if "dependency-reverse" in r or "predecessor-reverse" in r:
        return (target_id, item_id, "blocks")
    if "related" in r:
        return (item_id, target_id, "relates")
    return None


def _content_update_match_dev_azure_org(entry: dict[str, Any], target_repo: str) -> Any | None:
    """Match work item id when source_url host is dev.azure.com and org segment matches."""
    source_url = str(entry.get("source_url", "") or "")
    if not source_url or "/" not in target_repo:
        return None
    try:
        parsed = urlparse(source_url)
        if not parsed.hostname or parsed.hostname.lower() != "dev.azure.com":
            return None
        target_org = target_repo.split("/")[0]
        m = re.search(r"dev\.azure\.com/([^/]+)/", source_url)
        if m and m.group(1) == target_org:
            return entry.get("source_id")
    except Exception:
        return None
    return None


def _ado_guid_like_segment(segment: str | None) -> bool:
    return bool(segment and len(segment) == 36 and "-" in segment)


def _ado_project_paths_ambiguous(source_url: str, entry_project: str | None, target_project: str | None) -> bool:
    entry_has_guid = bool(source_url and re.search(r"dev\.azure\.com/[^/]+/[0-9a-f-]{36}", source_url, re.IGNORECASE))
    return (
        not entry_project
        or not target_project
        or entry_has_guid
        or _ado_guid_like_segment(entry_project)
        or _ado_guid_like_segment(target_project)
    )


def _ado_uncertain_org_match_conditions(
    entry: Mapping[str, Any],
    entry_repo: str,
    target_repo: str,
    source_url: str,
) -> bool:
    """True when org matches, source_id exists, and project identity is ambiguous."""
    entry_org = entry_repo.split("/")[0] if "/" in entry_repo else None
    target_org = target_repo.split("/")[0] if "/" in target_repo else None
    entry_project = entry_repo.split("/", 1)[1] if "/" in entry_repo else None
    target_project = target_repo.split("/", 1)[1] if "/" in target_repo else None
    return bool(
        entry_org
        and target_org
        and entry_org == target_org
        and entry.get("source_id")
        and _ado_project_paths_ambiguous(source_url, entry_project, target_project)
    )


def _content_update_match_ado_org_project_uncertain(
    entry: Mapping[str, Any], entry_repo: str, target_repo: str
) -> Any | None:
    """Match by org when project identity is ambiguous (GUID URLs, etc.)."""
    if str(entry.get("source_type", "") or "").lower() != "ado":
        return None
    if not (entry_repo and target_repo):
        return None
    source_url = str(entry.get("source_url", "") or "")
    if not _ado_uncertain_org_match_conditions(entry, entry_repo, target_repo, source_url):
        return None
    return entry.get("source_id")


def _flatten_issue_relation_dicts(item: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect relation dicts from provider_fields and top-level relations."""
    relation_entries: list[dict[str, Any]] = []
    provider_fields = item.get("provider_fields")
    if isinstance(provider_fields, dict):
        pf: dict[str, Any] = provider_fields
        relations = pf.get("relations")
        if isinstance(relations, list):
            relation_entries.extend(r for r in relations if isinstance(r, dict))
    top = item.get("relations")
    if isinstance(top, list):
        relation_entries.extend(r for r in top if isinstance(r, dict))
    return relation_entries


def _markdown_to_html_ado_fallback(value: str) -> str:
    import re as _re

    todo_pattern = r"^(\s*)[-*]\s*\[TODO[:\s]+([^\]]+)\](.*)$"
    normalized_markdown = _re.sub(
        todo_pattern,
        r"\1- [ ] \2",
        value,
        flags=_re.MULTILINE | _re.IGNORECASE,
    )
    try:
        import markdown

        return markdown.markdown(normalized_markdown, extensions=["fenced_code", "tables"])
    except ImportError:
        return normalized_markdown


def _ado_patch_doc_append_acceptance_criteria_create_issue(
    patch_document: list[dict[str, Any]],
    *,
    acceptance_criteria: str,
    acceptance_criteria_field: str,
    field_rendering_format: str,
) -> None:
    if not acceptance_criteria:
        return
    patch_document.append(
        {
            "op": "add",
            "path": f"/multilineFieldsFormat/{acceptance_criteria_field}",
            "value": field_rendering_format,
        }
    )
    patch_document.append(
        {
            "op": "add",
            "path": f"/fields/{acceptance_criteria_field}",
            "value": acceptance_criteria,
        }
    )


def _ado_patch_doc_append_priority_story_points_create_issue(
    patch_document: list[dict[str, Any]],
    *,
    payload: dict[str, Any],
    priority_field: str,
    story_points_field: str,
) -> None:
    priority = payload.get("priority")
    if priority not in (None, ""):
        patch_document.append(
            {
                "op": "add",
                "path": f"/fields/{priority_field}",
                "value": priority,
            }
        )
    story_points = payload.get("story_points")
    if story_points is not None:
        patch_document.append(
            {
                "op": "add",
                "path": f"/fields/{story_points_field}",
                "value": story_points,
            }
        )


def _ado_patch_doc_append_provider_fields_create_issue(
    patch_document: list[dict[str, Any]], payload: dict[str, Any]
) -> None:
    provider_fields_raw = payload.get("provider_fields")
    if not isinstance(provider_fields_raw, dict):
        return
    provider_field_values = _as_str_dict(provider_fields_raw).get("fields")
    if not isinstance(provider_field_values, dict):
        return
    for field_name, field_value in provider_field_values.items():
        normalized_field = str(field_name).strip()
        if not normalized_field:
            continue
        patch_document.append(
            {
                "op": "add",
                "path": f"/fields/{normalized_field}",
                "value": field_value,
            }
        )


def _ado_patch_doc_append_sprint_parent_create_issue(
    patch_document: list[dict[str, Any]],
    *,
    base_url: str,
    org: str,
    project: str,
    payload: dict[str, Any],
) -> None:
    sprint = str(payload.get("sprint") or "").strip()
    if sprint:
        patch_document.append(
            {
                "op": "add",
                "path": "/fields/System.IterationPath",
                "value": sprint,
            }
        )
    parent_id = str(payload.get("parent_id") or "").strip()
    if not parent_id:
        return
    parent_url = f"{base_url}/{org}/{project}/_apis/wit/workItems/{parent_id}"
    patch_document.append(
        {
            "op": "add",
            "path": "/relations/-",
            "value": {"rel": "System.LinkTypes.Hierarchy-Reverse", "url": parent_url},
        }
    )


def _ado_patch_ops_optional_acceptance_criteria(
    item: BacklogItem,
    update_fields: list[str] | None,
    ado_mapper: AdoFieldMapper,
    provider_field_names: set[str],
) -> list[dict[str, Any]]:
    if update_fields is not None and "acceptance_criteria" not in update_fields:
        return []
    operations: list[dict[str, Any]] = []
    acceptance_criteria_field = ado_mapper.resolve_write_target_field("acceptance_criteria", provider_field_names)
    if acceptance_criteria_field and item.acceptance_criteria:
        operations.append(
            {
                "op": "add",
                "path": f"/multilineFieldsFormat/{acceptance_criteria_field}",
                "value": "Markdown",
            }
        )
        operations.append(
            {"op": "replace", "path": f"/fields/{acceptance_criteria_field}", "value": item.acceptance_criteria}
        )
    return operations


def _ado_patch_ops_optional_story_points(
    item: BacklogItem,
    update_fields: list[str] | None,
    ado_mapper: AdoFieldMapper,
    provider_field_names: set[str],
) -> list[dict[str, Any]]:
    if update_fields is not None and "story_points" not in update_fields:
        return []
    operations: list[dict[str, Any]] = []
    story_points_field = ado_mapper.resolve_write_target_field("story_points", provider_field_names)
    if story_points_field and item.story_points is not None and story_points_field in provider_field_names:
        operations.append({"op": "replace", "path": f"/fields/{story_points_field}", "value": item.story_points})
    return operations


def _ado_patch_ops_optional_business_value(
    item: BacklogItem,
    update_fields: list[str] | None,
    ado_mapper: AdoFieldMapper,
    provider_field_names: set[str],
) -> list[dict[str, Any]]:
    if update_fields is not None and "business_value" not in update_fields:
        return []
    operations: list[dict[str, Any]] = []
    business_value_field = ado_mapper.resolve_write_target_field("business_value", provider_field_names)
    if business_value_field and item.business_value is not None and business_value_field in provider_field_names:
        operations.append({"op": "replace", "path": f"/fields/{business_value_field}", "value": item.business_value})
    return operations


def _ado_patch_ops_optional_priority(
    item: BacklogItem,
    update_fields: list[str] | None,
    ado_mapper: AdoFieldMapper,
    provider_field_names: set[str],
) -> list[dict[str, Any]]:
    if update_fields is not None and "priority" not in update_fields:
        return []
    operations: list[dict[str, Any]] = []
    priority_field = ado_mapper.resolve_write_target_field("priority", provider_field_names)
    if priority_field and item.priority is not None and priority_field in provider_field_names:
        operations.append({"op": "replace", "path": f"/fields/{priority_field}", "value": item.priority})
    return operations


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
        self._configure_api_token(api_token)

        # Base URL defaults to Azure DevOps Services (cloud)
        # Normalize base_url: remove trailing slashes
        # Note: For Azure DevOps Services (cloud), base_url should be "https://dev.azure.com"
        # For Azure DevOps Server (on-premise), base_url might be "https://server" or "https://server/collection"
        raw_base_url = base_url or "https://dev.azure.com"
        self.base_url = raw_base_url.rstrip("/")
        self.work_item_type = work_item_type

    def _configure_api_token(self, api_token: str | None) -> None:
        """Resolve PAT / env / keyring token and set ``api_token`` and ``auth_scheme``."""
        if api_token:
            self.api_token = api_token
            self.auth_scheme = "basic"
            return
        env_tok = os.environ.get("AZURE_DEVOPS_TOKEN")
        if env_tok:
            self.api_token = env_tok
            self.auth_scheme = "basic"
            return
        stored_token = get_token("azure-devops", allow_expired=False)
        if stored_token:
            self.api_token = stored_token.get("access_token")
            token_type = (stored_token.get("token_type") or "bearer").lower()
            self.auth_scheme = "bearer" if token_type == "bearer" else "basic"
            return
        stored_token_expired = get_token("azure-devops", allow_expired=True)
        if not stored_token_expired:
            self.api_token = None
            self.auth_scheme = None
            return
        expires_at = stored_token_expired.get("expires_at", "unknown")
        token_type = (stored_token_expired.get("token_type") or "bearer").lower()
        if token_type != "bearer":
            self.api_token = stored_token_expired.get("access_token")
            self.auth_scheme = "basic"
            return
        refreshed_token = self._try_refresh_oauth_token()
        if refreshed_token:
            self.api_token = refreshed_token.get("access_token")
            self.auth_scheme = "bearer"
            set_token("azure-devops", refreshed_token)
            debug_print(f"[dim]OAuth token automatically refreshed (was expired at {expires_at})[/dim]")
            return
        console.print(f"[yellow]⚠[/yellow] Stored OAuth token expired at {expires_at}. Attempting automatic refresh...")
        console.print("[yellow]⚠[/yellow] Automatic refresh failed. OAuth tokens expire after ~1 hour.")
        console.print(
            "[dim]Options:[/dim]\n"
            "  1. Use a Personal Access Token (PAT) with longer expiration (up to 1 year):\n"
            "     - Create PAT: https://dev.azure.com/{org}/_usersSettings/tokens\n"
            "     - Store PAT: specfact backlog auth azure-devops --pat your_pat_token\n"
            "  2. Re-authenticate: specfact backlog auth azure-devops\n"
            "  3. Use --ado-token option with a valid token"
        )
        self.api_token = None
        self.auth_scheme = None

    def _ado_create_patch_document(self, title: str, body: str, ado_state: str) -> list[dict[str, Any]]:
        return [
            {"op": "add", "path": "/fields/System.Title", "value": title},
            {"op": "add", "path": "/fields/System.Description", "value": body},
            {"op": "add", "path": "/fields/System.State", "value": ado_state},
            {
                "op": "add",
                "path": "/multilineFieldsFormat/System.Description",
                "value": "Markdown",
            },
        ]

    def _parse_ado_create_work_item_response(self, work_item_data: dict[str, Any]) -> tuple[Any, str]:
        work_item_id = work_item_data.get("id")
        _links_raw = work_item_data.get("_links", {})
        links = _as_str_dict(_links_raw) if isinstance(_links_raw, dict) else {}
        html_raw = links.get("html", {})
        html = _as_str_dict(html_raw) if isinstance(html_raw, dict) else {}
        return work_item_id, str(html.get("href", ""))

    def _merge_created_work_item_source_tracking(
        self,
        proposal_data: dict[str, Any],
        created: _AdoCreatedWorkItemRef,
    ) -> None:
        tracking_update = {
            "source_id": created.work_item_id,
            "source_url": created.work_item_url,
            "source_repo": f"{created.org}/{created.project}",
            "source_metadata": {
                "org": created.org,
                "project": created.project,
                "work_item_type": created.work_item_type,
                "state": created.ado_state,
            },
        }
        source_tracking = proposal_data.get("source_tracking")
        if isinstance(source_tracking, list):
            cast(list[dict[str, Any]], source_tracking).append(tracking_update)
            return
        if source_tracking is None or (isinstance(source_tracking, dict) and len(source_tracking) == 0):
            proposal_data["source_tracking"] = tracking_update
            return
        if isinstance(source_tracking, dict):
            st = _as_str_dict(source_tracking)
            st.update(tracking_update)
            proposal_data["source_tracking"] = st
            return

    def _is_on_premise(self) -> bool:
        """
        Detect if this is Azure DevOps Server (on-premise) vs Azure DevOps Services (cloud).

        Returns:
            True if on-premise (base_url doesn't contain dev.azure.com), False if cloud
        """
        return "dev.azure.com" not in self.base_url.lower()

    def _build_ado_url_on_premise(self, base_url_normalized: str, path_normalized: str, api_version: str) -> str:
        """Build URL for Azure DevOps Server (on-premise) layouts."""
        base_lower = base_url_normalized.lower()
        has_tfs = "/tfs/" in base_lower
        parts = [p for p in base_url_normalized.rstrip("/").split("/") if p and p not in ["http:", "https:"]]
        has_collection_in_base = has_tfs or len(parts) > 1

        if has_collection_in_base:
            if self.org:
                return f"{base_url_normalized}/{self.org}/{self.project}/{path_normalized}?api-version={api_version}"
            console.print(
                "[yellow]Warning:[/yellow] Collection in base_url but org not provided. Using project directly."
            )
            return f"{base_url_normalized}/{self.project}/{path_normalized}?api-version={api_version}"
        if self.org:
            if "/tfs" in base_url_normalized.lower() or not has_tfs:
                return f"{base_url_normalized}/{self.org}/{self.project}/{path_normalized}?api-version={api_version}"
            return f"{base_url_normalized}/tfs/{self.org}/{self.project}/{path_normalized}?api-version={api_version}"
        console.print(
            "[yellow]Warning:[/yellow] On-premise detected but org (collection) not provided. Assuming collection is in base_url."
        )
        return f"{base_url_normalized}/{self.project}/{path_normalized}?api-version={api_version}"

    def _build_ado_url(self, path: str, api_version: str = _ADO_STABLE_API_VERSION) -> str:
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
            return self._build_ado_url_on_premise(base_url_normalized, path_normalized, api_version)
        if not self.org:
            raise ValueError(f"org required for Azure DevOps Services (cloud) (org={self.org!r})")
        return f"{base_url_normalized}/{self.org}/{self.project}/{path_normalized}?api-version={api_version}"

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
    @ensure(lambda result: isinstance(result, str), "Must return string")
    def _strip_leading_description_heading(self, content: str) -> str:
        """
        Remove a leading Description heading/label from markdown content.

        This prevents duplicated "Description" headers in ADO Description field
        when refinement output includes a scaffold heading like `## Description`.
        """
        if not content:
            return ""
        normalized = content.lstrip()
        normalized = re.sub(r"^(#{1,6}\s+Description\s*)\n+", "", normalized, count=1, flags=re.IGNORECASE)
        normalized = re.sub(r"^Description:\s*\n+", "", normalized, count=1, flags=re.IGNORECASE)
        return normalized.strip()

    def _resolve_change_id_for_proposal_data(self, item_data: dict[str, Any], description_raw: str) -> str:
        """Resolve OpenSpec change id from description footer, comments, or work item id."""
        if description_raw:
            change_id_match = re.search(r"OpenSpec Change Proposal:\s*`([^`]+)`", description_raw, re.IGNORECASE)
            if change_id_match:
                return change_id_match.group(1)

        work_item_id = item_data.get("id")
        if work_item_id and self.org and self.project:
            comments = self._get_work_item_comments(self.org, self.project, work_item_id)
            for comment in comments:
                comment_text = comment.get("text", "") or comment.get("body", "")
                for pattern in _OPENSPEC_COMMENT_CHANGE_ID_PATTERNS:
                    match = re.search(pattern, comment_text, re.IGNORECASE | re.DOTALL)
                    if match:
                        return match.group(1)

        return str(item_data.get("id", "unknown"))

    @staticmethod
    def _apply_assignee_to_owner_stakeholders(
        assigned_to: Any,
        owner: str | None,
        stakeholders: list[str],
    ) -> tuple[str | None, list[str]]:
        if not assigned_to:
            return owner, stakeholders

        if isinstance(assigned_to, dict):
            assignee_dict = cast(dict[str, Any], assigned_to)
            display_name = assignee_dict.get("displayName")
            unique_name = assignee_dict.get("uniqueName")
            if isinstance(display_name, str) and display_name.strip():
                assignee_name = display_name.strip()
            elif isinstance(unique_name, str):
                assignee_name = unique_name
            else:
                assignee_name = ""
        else:
            assignee_name = str(assigned_to)

        if assignee_name and not owner:
            owner = assignee_name
        if assignee_name:
            stakeholders.append(assignee_name)
        return owner, stakeholders

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
            3. Work item ID (fallback, normalized during shared proposal import)
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

        rationale, description, impact = _extract_ado_proposal_markdown_sections(description_raw)
        change_id = self._resolve_change_id_for_proposal_data(item_data, description_raw)

        # Extract status from System.State
        ado_state = fields.get("System.State", "New")
        status = self.map_backlog_status_to_openspec(ado_state)

        # Extract created_at timestamp
        created_at = fields.get("System.CreatedDate")
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                created_at = dt.isoformat()
            except (ValueError, AttributeError):
                created_at = datetime.now(UTC).isoformat()
        else:
            created_at = datetime.now(UTC).isoformat()

        timeline, owner, stakeholders = _parse_when_who_markdown(description_raw)
        dependencies: list[str] = []

        owner, stakeholders = self._apply_assignee_to_owner_stakeholders(
            fields.get("System.AssignedTo"), owner, stakeholders
        )

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
    @require(require_repo_path_exists, "Repository path must exist")
    @require(require_repo_path_is_dir, "Repository path must be a directory")
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
    @require(require_repo_path_exists, "Repository path must exist")
    @require(require_repo_path_is_dir, "Repository path must be a directory")
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

    def _merge_ado_import_fields_into_source_metadata(self, proposal: Any, fields: dict[str, Any]) -> str:
        """Populate source_metadata from ADO work item fields; return ``source_repo`` key."""
        proposal.source_tracking.source_metadata.update(
            {
                "org": self.org or "",
                "project": self.project or "",
                "work_item_type": fields.get("System.WorkItemType", ""),
                "state": fields.get("System.State", ""),
            }
        )
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
        return source_repo

    @staticmethod
    def _ado_backlog_entry_matches_for_merge(ex: dict[str, Any], entry: dict[str, Any], source_repo: str) -> bool:
        if source_repo:
            return ex.get("source_repo") == source_repo
        return ex.get("source_id") == entry.get("source_id")

    def _merge_ado_import_backlog_entries(self, proposal: Any, artifact_path: dict[str, Any], source_repo: str) -> None:
        """Merge or append backlog entry under ``source_metadata.backlog_entries``."""
        entry_id = artifact_path.get("id")
        links_raw = artifact_path.get("_links", {})
        links: dict[str, Any] = links_raw if isinstance(links_raw, dict) else {}
        html_raw = links.get("html", {})
        html: dict[str, Any] = html_raw if isinstance(html_raw, dict) else {}
        href = str(html.get("href", ""))
        entry: dict[str, Any] = {
            "source_id": str(entry_id) if entry_id is not None else None,
            "source_url": href,
            "source_type": "ado",
            "source_repo": source_repo,
            "source_metadata": {"last_synced_status": proposal.status},
        }
        raw_entries = proposal.source_tracking.source_metadata.get("backlog_entries")
        entries: list[dict[str, Any]] = (
            [] if not isinstance(raw_entries, list) else cast(list[dict[str, Any]], raw_entries)
        )
        if not entry.get("source_id"):
            proposal.source_tracking.source_metadata["backlog_entries"] = entries
            return

        updated = False
        for existing in entries:
            if not isinstance(existing, dict):
                continue
            ex: dict[str, Any] = existing
            if self._ado_backlog_entry_matches_for_merge(ex, entry, source_repo):
                ex.update(entry)
                updated = True
                break
        if not updated:
            entries.append(entry)
        proposal.source_tracking.source_metadata["backlog_entries"] = entries

    def _apply_ado_import_source_tracking(self, proposal: Any, artifact_path: dict[str, Any]) -> None:
        """Merge ADO work item metadata and backlog entry into proposal source_tracking."""
        if not proposal.source_tracking or not isinstance(proposal.source_tracking.source_metadata, dict):
            return

        fields_raw = artifact_path.get("fields", {})
        fields: dict[str, Any] = fields_raw if isinstance(fields_raw, dict) else {}
        source_repo = self._merge_ado_import_fields_into_source_metadata(proposal, fields)
        self._merge_ado_import_backlog_entries(proposal, artifact_path, source_repo)

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
        existing_proposals = (
            dict(project_bundle.change_tracking.proposals) if getattr(project_bundle, "change_tracking", None) else {}
        )
        proposal = self.import_backlog_item_as_proposal(
            artifact_path,
            "ado",
            bridge_config,
            existing_proposals=existing_proposals,
        )

        if not proposal:
            msg = "Failed to import ADO work item as change proposal"
            raise ValueError(msg)

        self._apply_ado_import_source_tracking(proposal, artifact_path)

        # Add proposal to project bundle change tracking
        if hasattr(project_bundle, "change_tracking"):
            if not project_bundle.change_tracking:
                from specfact_cli.models.change import ChangeTracking

                project_bundle.change_tracking = ChangeTracking()
            project_bundle.change_tracking.proposals[proposal.name] = proposal

    def _work_item_id_from_source_tracking_basic(self, source_tracking: Any, org: str, project: str) -> Any | None:
        """Resolve work item id from source_tracking list/dict for the target org/project repo."""
        target_repo = f"{org}/{project}"
        if isinstance(source_tracking, list):
            for entry in source_tracking:
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
        elif isinstance(source_tracking, dict):
            return _as_str_dict(source_tracking).get("source_id")
        return None

    def _resolve_work_item_id_for_content_update(self, artifact_data: dict[str, Any], org: str, project: str) -> int:
        """Find work item id for change_proposal_update using multi-level ADO matching."""
        source_tracking = artifact_data.get("source_tracking", {})
        work_item_id: Any = None
        target_repo = f"{org}/{project}"

        if isinstance(source_tracking, list):
            for entry in source_tracking:
                if not isinstance(entry, dict):
                    continue
                ed = _as_str_dict(entry)
                entry_repo = ed.get("source_repo")
                if entry_repo == target_repo:
                    work_item_id = ed.get("source_id")
                    break
                if not entry_repo:
                    work_item_id = _content_update_match_dev_azure_org(entry, target_repo)
                    if work_item_id:
                        break
                    continue
                work_item_id = _content_update_match_ado_org_project_uncertain(ed, str(entry_repo), target_repo)
                if work_item_id:
                    break
        elif isinstance(source_tracking, dict):
            work_item_id = _as_str_dict(source_tracking).get("source_id")

        if not work_item_id:
            msg = (
                f"Work item ID required for content update (missing in source_tracking for repository {target_repo}). "
                "Work item must be created first."
            )
            raise ValueError(msg)

        return self._coerce_work_item_id(work_item_id)

    def _export_change_proposal_comment_artifact(
        self, artifact_data: dict[str, Any], org: str, project: str
    ) -> dict[str, Any]:
        source_tracking = artifact_data.get("source_tracking", {})
        work_item_id = self._work_item_id_from_source_tracking_basic(source_tracking, org, project)

        if not work_item_id:
            msg = "Work item ID required for comment (missing in source_tracking for this repository)"
            raise ValueError(msg)

        work_item_id_int = self._coerce_work_item_id(work_item_id)

        status = artifact_data.get("status", "proposed")
        title = artifact_data.get("title", "Untitled Change Proposal")
        change_id = artifact_data.get("change_id", "")
        code_repo_path_str = artifact_data.get("_code_repo_path")
        code_repo_path = Path(code_repo_path_str) if code_repo_path_str else None

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
            st = _as_str_dict(source_tracking)
            st_dict: dict[str, Any] = dict(st)
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
            self._add_work_item_comment(org, project, work_item_id_int, comment_note)
        return {
            "work_item_id": work_item_id_int,
            "comment_added": True,
        }

    def _export_code_change_progress_artifact(
        self,
        artifact_data: dict[str, Any],
        org: str,
        project: str,
        bridge_config: BridgeConfig | None,
    ) -> dict[str, Any]:
        source_tracking = artifact_data.get("source_tracking", {})
        work_item_id = self._work_item_id_from_source_tracking_basic(source_tracking, org, project)

        if not work_item_id:
            msg = "Work item ID required for progress comment (missing in source_tracking for this repository)"
            raise ValueError(msg)

        work_item_id_int = self._coerce_work_item_id(work_item_id)

        sanitize = artifact_data.get("sanitize", False)
        if bridge_config and hasattr(bridge_config, "sanitize"):
            sanitize = bridge_config.sanitize if bridge_config.sanitize is not None else sanitize  # type: ignore[attr-defined]

        return self._add_progress_comment(artifact_data, org, project, work_item_id_int, sanitize=sanitize)

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
        if not self.api_token:
            msg = (
                "Azure DevOps API token required. Options:\n"
                "  1. Set AZURE_DEVOPS_TOKEN environment variable\n"
                "  2. Provide via --ado-token option\n"
                "  3. Run `specfact backlog auth azure-devops` for device code authentication"
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
            work_item_id = self._resolve_work_item_id_for_content_update(
                cast(dict[str, Any], artifact_data), org, project
            )
            return self._update_work_item_body(artifact_data, org, project, work_item_id)
        if artifact_key == "change_proposal_comment":
            return self._export_change_proposal_comment_artifact(cast(dict[str, Any], artifact_data), org, project)
        if artifact_key == "code_change_progress":
            return self._export_code_change_progress_artifact(
                cast(dict[str, Any], artifact_data), org, project, bridge_config
            )
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
            source_metadata = _as_str_dict(source_tracking).get("source_metadata")
        elif source_tracking is not None and hasattr(source_tracking, "source_metadata"):
            source_metadata = source_tracking.source_metadata

        if isinstance(source_metadata, dict):
            sm = _as_str_dict(source_metadata)
            raw_title = raw_title or sm.get("raw_title")
            raw_body = raw_body or sm.get("raw_body")

        return raw_title, raw_body

    def _build_change_proposal_body(
        self,
        title: str,
        rationale: str,
        description: str,
        impact: str,
        change_id: str,
    ) -> str:
        """Build the canonical markdown body used for ADO change proposal work items."""
        body_parts: list[str] = []
        display_title = re.sub(r"^\[change\]\s*", "", title, flags=re.IGNORECASE).strip()
        if display_title:
            body_parts.extend([f"# {display_title}", ""])

        for heading, content in (("Why", rationale), ("What Changes", description), ("Impact", impact)):
            if not content:
                continue
            body_parts.extend([f"## {heading}", "", *content.strip().split("\n"), ""])

        if not body_parts or not any((rationale, description, impact)):
            body_parts.extend(["No description provided.", ""])

        body_parts.extend(["---", f"*OpenSpec Change Proposal: `{change_id}`*"])
        return "\n".join(body_parts)

    def _resolve_proposal_ado_state(self, proposal_data: dict[str, Any]) -> str:
        """Resolve the ADO state for a proposal, preserving cross-adapter state when present."""
        source_state = proposal_data.get("source_state")
        source_type = proposal_data.get("source_type")
        if source_state and source_type and source_type != "ado":
            return self.map_backlog_state_between_adapters(source_state, source_type, self)
        status = proposal_data.get("status", "proposed")
        return self.map_openspec_status_to_backlog(status)

    def _require_api_token(self) -> None:
        """Ensure an API token is configured before ADO write operations."""
        if not self.api_token:
            raise ValueError("Azure DevOps API token is required")

    def _find_work_item_id_in_source_tracking(self, source_tracking: Any, target_repo: str) -> Any:
        """Locate a work item identifier inside source tracking structures."""
        if isinstance(source_tracking, dict):
            return _as_str_dict(source_tracking).get("source_id")

        if isinstance(source_tracking, list):
            for entry in source_tracking:
                if not isinstance(entry, dict):
                    continue
                ed = _as_str_dict(entry)
                entry_repo = ed.get("source_repo")
                if entry_repo == target_repo:
                    return ed.get("source_id")
                source_url = ed.get("source_url", "")
                if not entry_repo and source_url and target_repo in source_url:
                    return ed.get("source_id")

        return None

    def _coerce_work_item_id(self, work_item_id: Any) -> int:
        """Normalize source-tracking work item IDs to integers."""
        if isinstance(work_item_id, int):
            return work_item_id
        if isinstance(work_item_id, str):
            try:
                return int(work_item_id)
            except ValueError:
                raise ValueError(f"Invalid work item ID format: {work_item_id}") from None
        raise ValueError(f"Invalid work item ID format: {work_item_id}")

    def _get_source_tracking_work_item_id(self, source_tracking: Any, target_repo: str) -> int:
        """Resolve the tracked work item ID for the target repository."""
        work_item_id = self._find_work_item_id_in_source_tracking(source_tracking, target_repo)
        if not work_item_id:
            msg = (
                f"Work item ID not found in source_tracking for repository {target_repo}. "
                "Work item must be created first."
            )
            raise ValueError(msg)
        return self._coerce_work_item_id(work_item_id)

    def _patch_work_item(
        self,
        org: str,
        project: str,
        work_item_id: int,
        patch_document: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Patch an ADO work item and return the response payload."""
        self._require_api_token()
        url = f"{self.base_url}/{org}/{project}/_apis/wit/workitems/{work_item_id}?api-version=7.1"
        headers = {"Content-Type": "application/json-patch+json", **self._auth_headers()}
        try:
            response = self._request_with_retry(
                lambda: requests.patch(url, json=patch_document, headers=headers, timeout=30)
            )
        except requests.RequestException as exc:
            resp = getattr(exc, "response", None)
            user_msg = _log_ado_patch_failure(resp, patch_document, url)
            exc.ado_user_message = user_msg  # type: ignore[attr-defined]
            console.print(f"[bold red]✗[/bold red] {user_msg}")
            raise
        return response.json()

    @beartype
    @require(require_repo_path_exists, "Repository path must exist")
    @require(require_repo_path_is_dir, "Repository path must be a directory")
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
    @require(require_bundle_dir_exists, "Bundle directory must exist")
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
    @require(require_bundle_dir_exists, "Bundle directory must exist")
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
    @require(require_bundle_dir_exists, "Bundle directory must exist")
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
    @require(require_bundle_dir_exists, "Bundle directory must exist")
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
            response = self._ado_get(url, headers=headers, timeout=30)
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
            token = _get_access_token(credential, azure_devops_scopes)

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

    @beartype
    @ensure(lambda result: hasattr(result, "raise_for_status"), "Result must support raise_for_status")
    def _ado_get(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        timeout: int = 30,
        retry_on_ambiguous_transport: bool = True,
    ) -> Any:
        """Execute an idempotent ADO GET with retry policy for transient failures."""
        return cast(
            Any,
            self._request_with_retry(
                lambda: requests.get(url, headers=headers, params=params, timeout=timeout),
                retry_on_ambiguous_transport=retry_on_ambiguous_transport,
            ),
        )

    @beartype
    @ensure(lambda result: hasattr(result, "raise_for_status"), "Result must support raise_for_status")
    def _ado_post(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        timeout: int = 30,
        retry_on_ambiguous_transport: bool = True,
    ) -> Any:
        """Execute ADO POST with retry policy. Safe for read-only WIQL endpoints."""
        request_kwargs: dict[str, Any] = {"headers": headers, "json": json, "timeout": timeout}
        if params:
            request_kwargs["params"] = params
        return cast(
            Any,
            self._request_with_retry(
                lambda: requests.post(url, **request_kwargs),
                retry_on_ambiguous_transport=retry_on_ambiguous_transport,
            ),
        )

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
            response = self._ado_get(url, headers=headers, timeout=10)
            # Check if work item is deleted (System.State == "Removed")
            work_item_data = response.json()
            fields = work_item_data.get("fields", {})
            state = fields.get("System.State", "")
            # Consider "Removed" as non-existent for our purposes
            return state != "Removed"
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return False
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
            response = self._ado_get(url, headers=headers, timeout=10)
            return _normalize_work_item_data(response.json())
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return None
            return None
        except requests.RequestException:
            return None

    @beartype
    @require(
        lambda self, issue_id: isinstance(issue_id, str) and len(issue_id.strip()) > 0, "issue_id must be non-empty"
    )
    @ensure(lambda result: result is None or isinstance(result, BacklogItem), "Must return BacklogItem or None")
    def _fetch_backlog_item_by_id(self, issue_id: str) -> BacklogItem | None:
        """Fetch a single ADO work item directly by ID (bypasses WIQL list queries)."""
        normalized_id = issue_id.strip()
        if not normalized_id.isdigit():
            return None
        if not self.org or not self.project:
            return None

        url = self._build_ado_url(f"_apis/wit/workitems/{int(normalized_id)}", api_version="7.1")
        headers = {
            **self._auth_headers(),
            "Accept": "application/json",
        }

        try:
            response = self._ado_get(url, headers=headers, params={"$expand": "all"}, timeout=30)
            work_item = response.json()
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return None
            raise

        from specfact_cli.backlog.converter import convert_ado_work_item_to_backlog_item

        return convert_ado_work_item_to_backlog_item(
            work_item,
            provider="ado",
            base_url=self.base_url,
            org=self.org,
            project_name=self.project,
        )

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
            response = self._ado_post(url, json=wiql, headers=headers, timeout=10)
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
        title = proposal_data.get("title", "Untitled Change Proposal")
        description = proposal_data.get("description", "")
        rationale = proposal_data.get("rationale", "")
        impact = proposal_data.get("impact", "")
        change_id = proposal_data.get("change_id", "unknown")
        raw_title, raw_body = self._extract_raw_fields(proposal_data)
        if raw_title:
            title = raw_title

        body = raw_body or self._build_change_proposal_body(title, rationale, description, impact, change_id)

        # Get work item type
        work_item_type = self._get_work_item_type(org, project)

        ado_state = self._resolve_proposal_ado_state(proposal_data)
        self._require_api_token()

        # Create work item via Azure DevOps API
        url = f"{self.base_url}/{org}/{project}/_apis/wit/workitems/${work_item_type}?api-version=7.1"
        headers = {
            "Content-Type": "application/json-patch+json",
            **self._auth_headers(),
        }

        patch_document = self._ado_create_patch_document(title, body, ado_state)

        try:
            response = self._request_with_retry(
                lambda: requests.post(url, json=patch_document, headers=headers, timeout=30),
                retry_on_ambiguous_transport=False,
            )
            if is_debug_mode():
                debug_log_operation(
                    "ado_create",
                    url,
                    str(response.status_code),
                    error=None if response.ok else (response.text[:200] if response.text else None),
                )
            response.raise_for_status()
            work_item_data = cast(dict[str, Any], response.json())
            work_item_id, work_item_url = self._parse_ado_create_work_item_response(work_item_data)

            self._merge_created_work_item_source_tracking(
                proposal_data,
                _AdoCreatedWorkItemRef(
                    work_item_id=work_item_id,
                    work_item_url=work_item_url,
                    org=org,
                    project=project,
                    work_item_type=work_item_type,
                    ado_state=ado_state,
                ),
            )

            return {
                "work_item_id": work_item_id,
                "work_item_url": work_item_url,
                "state": ado_state,
            }
        except requests.RequestException as e:
            resp = getattr(e, "response", None)
            user_msg = _log_ado_patch_failure(resp, patch_document, url)
            e.ado_user_message = user_msg  # type: ignore[attr-defined]
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
        work_item_id = self._get_source_tracking_work_item_id(
            proposal_data.get("source_tracking", {}),
            f"{org}/{project}",
        )
        ado_state = self._resolve_proposal_ado_state(proposal_data)
        work_item_data = self._patch_work_item(
            org,
            project,
            work_item_id,
            [{"op": "replace", "path": "/fields/System.State", "value": ado_state}],
        )
        work_item_url = work_item_data.get("_links", {}).get("html", {}).get("href", "")
        return {"work_item_id": work_item_id, "work_item_url": work_item_url, "state": ado_state}

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
        title = proposal_data.get("title", "Untitled Change Proposal")
        description = proposal_data.get("description", "")
        rationale = proposal_data.get("rationale", "")
        impact = proposal_data.get("impact", "")
        change_id = proposal_data.get("change_id", "unknown")
        raw_title, raw_body = self._extract_raw_fields(proposal_data)
        if raw_title:
            title = raw_title

        body = raw_body or self._build_change_proposal_body(title, rationale, description, impact, change_id)

        ado_state = self._resolve_proposal_ado_state(proposal_data)
        self._require_api_token()

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
            response = self._request_with_retry(
                lambda: requests.patch(url, json=patch_document, headers=headers, timeout=30)
            )
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
        source_tracking = (
            proposal.source_tracking if isinstance(proposal, ChangeProposal) else proposal.get("source_tracking")
        )
        if not source_tracking:
            raise ValueError("Source tracking required for status sync (work item must be created first)")

        target_repo = f"{org}/{project}"
        work_item_id = self._get_source_tracking_work_item_id(source_tracking, target_repo)
        ado_state = self.map_openspec_status_to_backlog(
            proposal.status if isinstance(proposal, ChangeProposal) else proposal.get("status", "proposed")
        )
        work_item_data = self._patch_work_item(
            org,
            project,
            work_item_id,
            [{"op": "replace", "path": "/fields/System.State", "value": ado_state}],
        )
        work_item_url = work_item_data.get("_links", {}).get("html", {}).get("href", "")
        return {
            "work_item_id": work_item_id,
            "work_item_url": work_item_url,
            "state_updated": True,
            "new_state": ado_state,
        }

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
        fields = work_item_data.get("fields", {})
        ado_state = fields.get("System.State", "New")
        openspec_status_from_ado = self.map_backlog_status_to_openspec(ado_state)
        openspec_status = (
            proposal.status if isinstance(proposal, ChangeProposal) else proposal.get("status", "proposed")
        )
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
            return _git_branch_exists_via_local_commands(repo_path, branch_name)
        except Exception as e:
            # If we can't check (git not available, etc.), return False to be safe
            self.console.log(f"[bold yellow]Warning:[/bold yellow] Error checking branch existence: {e}")  # type: ignore[attr-defined]
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

        url = f"{self.base_url}/{org}/{project}/_apis/wit/workItems/{work_item_id}/comments"
        headers = {
            "Accept": "application/json",
            **self._auth_headers(),
        }

        try:
            comments: list[dict[str, Any]] = []
            continuation_token: str | None = None
            seen_tokens: set[str] = set()

            while True:
                params: dict[str, Any] = {"api-version": _ADO_COMMENTS_API_VERSION, "$top": 200, "order": "asc"}
                if continuation_token:
                    params["continuationToken"] = continuation_token

                response = self._ado_get(url, headers=headers, params=params, timeout=30)
                response_data = response.json()

                raw_comments = response_data.get("comments", [])
                if isinstance(raw_comments, list):
                    comments.extend([c for c in raw_comments if isinstance(c, dict)])

                next_token = response.headers.get("x-ms-continuationtoken") or response_data.get("continuationToken")
                if not next_token or not isinstance(next_token, str):
                    break
                if next_token in seen_tokens:
                    break
                seen_tokens.add(next_token)
                continuation_token = next_token

            return comments
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
        url = (
            f"{self.base_url}/{org}/{project}/_apis/wit/workitems/{work_item_id}/comments"
            f"?api-version={_ADO_COMMENTS_API_VERSION}"
        )
        headers = {
            "Content-Type": "application/json",
            **self._auth_headers(),
        }

        # Build request body for comment
        comment_body = {"text": comment_text}

        try:
            response = self._request_with_retry(
                lambda: requests.post(url, json=comment_body, headers=headers, timeout=30),
                retry_on_ambiguous_transport=False,
            )
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
            e.ado_user_message = user_msg  # type: ignore[attr-defined]
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

    def _resolve_default_team_from_project_api(self) -> str | None:
        """Fetch first team for the project and cache as _auto_resolved_team."""
        from urllib.parse import quote

        try:
            project_encoded = quote(self.project or "", safe="")
            project_url = f"{self.base_url}/{self.org}/_apis/projects/{project_encoded}"
            project_params = {"api-version": "7.1"}
            project_headers = {
                **self._auth_headers(),
                "Accept": "application/json",
            }
            project_response = self._ado_get(project_url, headers=project_headers, params=project_params, timeout=30)
            project_data = project_response.json()
            project_id = project_data.get("id")
            if not project_id:
                return None
            teams_url = f"{self.base_url}/{self.org}/_apis/projects/{project_id}/teams"
            teams_response = self._ado_get(teams_url, headers=project_headers, params=project_params, timeout=30)
            teams_data = teams_response.json()
            teams = teams_data.get("value", [])
            if not teams:
                return None
            team_to_use = teams[0].get("name")
            self._auto_resolved_team = team_to_use
            return team_to_use
        except requests.RequestException:
            return None

    def _get_current_iteration_path_for_team(self, team_to_use: str) -> str | None:
        """Query team current iteration; on 404 retry with project name as team."""
        from urllib.parse import quote

        team_encoded = quote(team_to_use, safe="")
        url = f"{self.base_url}/{self.org}/{self.project}/{team_encoded}/_apis/work/teamsettings/iterations"
        params = {"$timeframe": "current", "api-version": "7.1"}
        headers = {
            **self._auth_headers(),
            "Accept": "application/json",
        }

        try:
            response = self._ado_get(url, headers=headers, params=params, timeout=30)
            data = response.json()
            iterations = data.get("value", [])
            if iterations:
                return iterations[0].get("path")
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404 and team_to_use != self.project:
                project_encoded = quote(self.project or "", safe="")
                fallback_url = (
                    f"{self.base_url}/{self.org}/{self.project}/{project_encoded}/_apis/work/teamsettings/iterations"
                )
                try:
                    fallback_response = self._ado_get(fallback_url, headers=headers, params=params, timeout=30)
                    fallback_data = fallback_response.json()
                    fallback_iterations = fallback_data.get("value", [])
                    if fallback_iterations:
                        return fallback_iterations[0].get("path")
                except requests.RequestException:
                    pass
        except requests.RequestException:
            pass
        return None

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

        team_to_use = self.team or getattr(self, "_auto_resolved_team", None)
        if not team_to_use:
            team_to_use = self._resolve_default_team_from_project_api()
        if not team_to_use:
            return None
        return self._get_current_iteration_path_for_team(team_to_use)

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
        team_to_use = self.team or getattr(self, "_auto_resolved_team", None)
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
                project_response = self._ado_get(
                    project_url, headers=project_headers, params=project_params, timeout=30
                )
                project_data = project_response.json()
                project_id = project_data.get("id")

                if project_id:
                    teams_url = f"{self.base_url}/{self.org}/_apis/projects/{project_id}/teams"
                    teams_response = self._ado_get(
                        teams_url, headers=project_headers, params=project_params, timeout=30
                    )
                    teams_data = teams_response.json()
                    teams = teams_data.get("value", [])
                    if teams:
                        team_to_use = teams[0].get("name")
                        self._auto_resolved_team = team_to_use
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
            response = self._ado_get(url, headers=headers, params=params, timeout=30)
            data = response.json()
            iterations = data.get("value", [])
            return [it.get("path", "") for it in iterations if it.get("path")]
        except requests.RequestException:
            # Fail silently - will be handled by caller
            pass
        return []

    def _resolve_sprint_filter_when_empty(
        self, items: list[BacklogItem], apply_current_when_missing: bool
    ) -> tuple[str | None, list[BacklogItem]]:
        if not apply_current_when_missing:
            return None, items
        current_iteration = self._get_current_iteration()
        if current_iteration:
            filtered = [item for item in items if item.iteration and item.iteration == current_iteration]
            return current_iteration, filtered
        console.print("[yellow]⚠ No current iteration found; returning all items[/yellow]")
        return None, items

    def _resolve_sprint_filter_by_name(
        self, sprint_filter: str, items: list[BacklogItem]
    ) -> tuple[str | None, list[BacklogItem]]:
        matching_items = [
            item
            for item in items
            if item.sprint
            and BacklogFilters.normalize_filter_value(item.sprint)
            == BacklogFilters.normalize_filter_value(sprint_filter)
        ]
        if not matching_items:
            return sprint_filter, []

        unique_iterations = {item.iteration for item in matching_items if item.iteration}
        if len(unique_iterations) > 1:
            raise ValueError(_ambiguous_sprint_error_message(sprint_filter, unique_iterations))

        iteration_path = unique_iterations.pop() if unique_iterations else None
        return iteration_path, matching_items

    def _resolve_sprint_filter(
        self,
        sprint_filter: str | None,
        items: list[BacklogItem],
        apply_current_when_missing: bool = True,
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
            return self._resolve_sprint_filter_when_empty(items, apply_current_when_missing)

        if "\\" in sprint_filter or "/" in sprint_filter:
            filtered = [item for item in items if item.iteration and item.iteration == sprint_filter]
            return sprint_filter, filtered

        return self._resolve_sprint_filter_by_name(sprint_filter, items)

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

    def _apply_iteration_filter_post_fetch(
        self, filtered_items: list[BacklogItem], filters: BacklogFilters
    ) -> list[BacklogItem]:
        """Restrict items by iteration when WIQL did not already scope by path."""
        if not filters.iteration:
            return filtered_items
        normalized_iteration = BacklogFilters.normalize_filter_value(filters.iteration)
        if normalized_iteration in (None, "any"):
            return filtered_items
        target_iteration = filters.iteration
        if normalized_iteration == "current":
            current_iteration = self._get_current_iteration()
            if not current_iteration:
                return []
            target_iteration = current_iteration
        return [
            item
            for item in filtered_items
            if BacklogFilters.normalize_filter_value(item.iteration)
            == BacklogFilters.normalize_filter_value(target_iteration)
        ]

    def _filter_backlog_items_state_assignee_labels(
        self, filtered_items: list[BacklogItem], filters: BacklogFilters
    ) -> list[BacklogItem]:
        if filters.state:
            normalized_state = BacklogFilters.normalize_filter_value(filters.state)
            filtered_items = [
                item for item in filtered_items if BacklogFilters.normalize_filter_value(item.state) == normalized_state
            ]

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

        return filtered_items

    def _apply_sprint_filter_post_fetch(
        self,
        filtered_items: list[BacklogItem],
        filters: BacklogFilters,
        *,
        sprint_apply_current: bool | None,
        echo_sprint_value_error: bool,
    ) -> list[BacklogItem]:
        if not filters.sprint:
            return filtered_items
        apply_current = (
            sprint_apply_current
            if sprint_apply_current is not None
            else getattr(filters, "use_current_iteration_default", True)
        )
        try:
            _, out = self._resolve_sprint_filter(
                filters.sprint,
                filtered_items,
                apply_current_when_missing=apply_current,
            )
        except ValueError as err:
            if echo_sprint_value_error:
                console.print(f"[red]Error:[/red] {err}")
            raise
        return out

    def _filter_backlog_items_by_release_post_fetch(
        self, filtered_items: list[BacklogItem], filters: BacklogFilters
    ) -> list[BacklogItem]:
        if not filters.release:
            return filtered_items
        normalized_release = BacklogFilters.normalize_filter_value(filters.release)
        return [
            item
            for item in filtered_items
            if item.release and BacklogFilters.normalize_filter_value(item.release) == normalized_release
        ]

    def _apply_backlog_limit_post_fetch(
        self, filtered_items: list[BacklogItem], filters: BacklogFilters
    ) -> list[BacklogItem]:
        if filters.limit is None or len(filtered_items) <= filters.limit:
            return filtered_items
        return filtered_items[: filters.limit]

    def _try_fetch_backlog_by_direct_issue(self, filters: BacklogFilters) -> list[BacklogItem] | None:
        """When issue_id is set, fetch that item and apply filters; otherwise return None."""
        requested_issue_id = str(getattr(filters, "issue_id", "") or "").strip()
        if not requested_issue_id:
            return None

        direct_item = self._fetch_backlog_item_by_id(requested_issue_id)
        if direct_item is None:
            return []

        return self._apply_post_fetch_filters_after_wiql(
            [direct_item],
            filters,
            include_iteration=True,
            sprint_apply_current=False,
            echo_sprint_value_error=False,
        )

    def _wiql_append_iteration_conditions(self, filters: BacklogFilters, conditions: list[str]) -> str | None:
        """Add iteration-related WIQL conditions; return resolved iteration path for error messages."""
        resolved_iteration: str | None = None
        if filters.iteration:
            if filters.iteration.lower() == "current":
                current_iteration = self._get_current_iteration()
                if current_iteration:
                    resolved_iteration = current_iteration
                    conditions.append(f"[System.IterationPath] = '{resolved_iteration}'")
                else:
                    suggestions = _rich_iteration_suggestions_block(self._list_available_iterations())
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
                resolved_iteration = filters.iteration
                conditions.append(f"[System.IterationPath] = '{resolved_iteration}'")
        elif filters.sprint:
            pass
        elif getattr(filters, "use_current_iteration_default", True):
            current_iteration = self._get_current_iteration()
            if current_iteration:
                resolved_iteration = current_iteration
                conditions.append(f"[System.IterationPath] = '{resolved_iteration}'")
            else:
                console.print("[yellow]⚠ No current iteration found and no sprint/iteration filter provided[/yellow]")

        return resolved_iteration

    def _post_wiql_handle_http_error(
        self,
        e: requests.HTTPError,
        url: str,
        resolved_iteration: str | None,
    ) -> NoReturn:
        user_friendly_msg = None
        if e.response is not None:
            try:
                error_json = e.response.json()
                error_message = error_json.get("message", "")

                if "TF51011" in error_message or "iteration path does not exist" in error_message.lower():
                    match = re.search(r"«'([^']+)'»", error_message)
                    bad_path = match.group(1) if match else (resolved_iteration if resolved_iteration else None)

                    available_iterations = self._list_available_iterations()
                    suggestions = _rich_iteration_suggestions_block(available_iterations)

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

        if user_friendly_msg:
            console.print(user_friendly_msg)
            raise ValueError(f"Iteration path error: {resolved_iteration}") from e

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
        new_exception = requests.HTTPError(error_msg)
        new_exception.response = e.response
        raise new_exception from e

    def _ado_workitems_batch_base_url(self) -> str:
        base_url_normalized = self.base_url.rstrip("/")
        if self._is_on_premise():
            parts = [p for p in base_url_normalized.split("/") if p and p not in ["http:", "https:"]]
            has_collection_in_base = "/tfs/" in base_url_normalized.lower() or len(parts) > 1

            if has_collection_in_base:
                return base_url_normalized
            if self.org:
                if "/tfs" in base_url_normalized.lower():
                    return f"{base_url_normalized}/tfs/{self.org}"
                return f"{base_url_normalized}/{self.org}"
            return base_url_normalized

        if not self.org:
            raise ValueError(f"org required for Azure DevOps Services (cloud) (org={self.org!r})")
        return f"{base_url_normalized}/{self.org}"

    def _batch_fetch_work_items_as_backlog_items(self, work_item_ids: list[int]) -> list[BacklogItem]:
        from specfact_cli.backlog.converter import convert_ado_work_item_to_backlog_item

        items: list[BacklogItem] = []
        batch_size = 200
        workitems_base_url = self._ado_workitems_batch_base_url()

        for i in range(0, len(work_item_ids), batch_size):
            batch = work_item_ids[i : i + batch_size]
            ids_str = ",".join(str(wi_id) for wi_id in batch)

            url = f"{workitems_base_url}/_apis/wit/workitems?api-version=7.1"
            params = {"ids": ids_str, "$expand": "all"}

            workitems_headers = {
                **self._auth_headers(),
                "Accept": "application/json",
            }

            debug_print(f"[dim]ADO WorkItems URL: {url}&ids={ids_str}[/dim]")

            try:
                response = self._ado_get(url, headers=workitems_headers, params=params, timeout=30)
                if is_debug_mode():
                    debug_log_operation(
                        "ado_workitems_get",
                        url,
                        str(response.status_code),
                        error=None if response.ok else (response.text[:200] if response.text else None),
                    )
            except requests.HTTPError as e:
                if is_debug_mode():
                    debug_log_operation(
                        "ado_workitems_get",
                        url,
                        "error",
                        error=str(e.response.status_code) if e.response is not None else str(e),
                    )
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
                new_exception = requests.HTTPError(error_msg)
                new_exception.response = e.response
                raise new_exception from e
            work_items_data = response.json()

            for work_item in work_items_data.get("value", []):
                backlog_item = convert_ado_work_item_to_backlog_item(
                    work_item,
                    provider="ado",
                    base_url=self.base_url,
                    org=self.org,
                    project_name=self.project,
                )
                items.append(backlog_item)

        return items

    def _apply_post_fetch_filters_after_wiql(
        self,
        filtered_items: list[BacklogItem],
        filters: BacklogFilters,
        *,
        include_iteration: bool = False,
        sprint_apply_current: bool | None = None,
        echo_sprint_value_error: bool = True,
    ) -> list[BacklogItem]:
        filtered_items = self._filter_backlog_items_state_assignee_labels(filtered_items, filters)
        if include_iteration:
            filtered_items = self._apply_iteration_filter_post_fetch(filtered_items, filters)
        filtered_items = self._apply_sprint_filter_post_fetch(
            filtered_items,
            filters,
            sprint_apply_current=sprint_apply_current,
            echo_sprint_value_error=echo_sprint_value_error,
        )
        filtered_items = self._filter_backlog_items_by_release_post_fetch(filtered_items, filters)
        if filters.search:
            pass
        return self._apply_backlog_limit_post_fetch(filtered_items, filters)

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
                "  3. Store token via specfact backlog auth azure-devops"
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

        direct_result = self._try_fetch_backlog_by_direct_issue(filters)
        if direct_result is not None:
            return direct_result

        wiql_parts = ["SELECT [System.Id], [System.Title], [System.State], [System.WorkItemType]"]
        wiql_parts.append("FROM WorkItems")
        wiql_parts.append("WHERE [System.TeamProject] = @project")

        conditions: list[str] = []
        if filters.area:
            conditions.append(f"[System.AreaPath] = '{filters.area}'")

        resolved_iteration = self._wiql_append_iteration_conditions(filters, conditions)

        if conditions:
            wiql_parts.append("AND " + " AND ".join(conditions))

        wiql = " ".join(wiql_parts)

        url = self._build_ado_url("_apis/wit/wiql", api_version="7.1")
        headers = {
            **self._auth_headers(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {"query": wiql}

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
            response = self._ado_post(url, headers=headers, json=payload, timeout=30)
        except requests.HTTPError as e:
            self._post_wiql_handle_http_error(e, url, resolved_iteration)

        query_result = response.json()

        work_item_ids = [item["id"] for item in query_result.get("workItems", [])]

        if not work_item_ids:
            return []

        items = self._batch_fetch_work_items_as_backlog_items(work_item_ids)
        return self._apply_post_fetch_filters_after_wiql(items, filters)

    def _build_create_issue_patch_document(
        self,
        org: str,
        project: str,
        payload: dict[str, Any],
        *,
        title: str,
    ) -> list[dict[str, Any]]:
        description = str(payload.get("description") or payload.get("body") or "").strip()
        description = self._strip_leading_description_heading(description)
        description_format = str(payload.get("description_format") or "markdown").strip().lower()
        field_rendering_format = "Markdown" if description_format != "classic" else "Html"

        custom_mapping_file = os.environ.get("SPECFACT_ADO_CUSTOM_MAPPING")
        ado_mapper = AdoFieldMapper(custom_mapping_file=custom_mapping_file)
        description_field = ado_mapper.resolve_write_target_field("description") or "System.Description"
        acceptance_criteria_field = (
            ado_mapper.resolve_write_target_field("acceptance_criteria") or "Microsoft.VSTS.Common.AcceptanceCriteria"
        )
        priority_field = ado_mapper.resolve_write_target_field("priority") or "Microsoft.VSTS.Common.Priority"
        story_points_field = (
            ado_mapper.resolve_write_target_field("story_points") or "Microsoft.VSTS.Scheduling.StoryPoints"
        )

        patch_document: list[dict[str, Any]] = [
            {"op": "add", "path": "/fields/System.Title", "value": title},
            {"op": "add", "path": f"/fields/{description_field}", "value": description},
            {"op": "add", "path": f"/multilineFieldsFormat/{description_field}", "value": field_rendering_format},
        ]

        acceptance_criteria = str(payload.get("acceptance_criteria") or "").strip()
        _ado_patch_doc_append_acceptance_criteria_create_issue(
            patch_document,
            acceptance_criteria=acceptance_criteria,
            acceptance_criteria_field=acceptance_criteria_field,
            field_rendering_format=field_rendering_format,
        )
        _ado_patch_doc_append_priority_story_points_create_issue(
            patch_document,
            payload=payload,
            priority_field=priority_field,
            story_points_field=story_points_field,
        )
        _ado_patch_doc_append_provider_fields_create_issue(patch_document, payload)
        _ado_patch_doc_append_sprint_parent_create_issue(
            patch_document,
            base_url=self.base_url,
            org=org,
            project=project,
            payload=payload,
        )
        return patch_document

    @beartype
    @require(
        lambda project_id: isinstance(project_id, str) and len(project_id.strip()) > 0, "project_id must be non-empty"
    )
    @require(lambda payload: isinstance(payload, dict), "payload must be dict")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def create_issue(self, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Create an Azure DevOps work item from provider-agnostic backlog payload."""
        org, project = self._resolve_graph_project_context(project_id)
        if not self.api_token:
            raise ValueError("Azure DevOps API token is required")

        title = str(payload.get("title") or "").strip()
        if not title:
            raise ValueError("payload.title is required")

        raw_type = str(payload.get("type") or "task").strip().lower()
        type_mapping = {
            "epic": "Epic",
            "feature": "Feature",
            "story": "User Story",
            "user story": "User Story",
            "task": "Task",
            "bug": "Bug",
            "spike": "Task",
        }
        work_item_type = type_mapping.get(raw_type, "Task")

        patch_document = self._build_create_issue_patch_document(org, project, payload, title=title)

        url = f"{self.base_url}/{org}/{project}/_apis/wit/workitems/${work_item_type}?api-version=7.1"
        headers = {
            "Content-Type": "application/json-patch+json",
            **self._auth_headers(),
        }
        response = self._request_with_retry(
            lambda: requests.post(url, json=patch_document, headers=headers, timeout=30),
            retry_on_ambiguous_transport=False,
        )
        created = response.json()

        created_id = str(created.get("id") or "")
        html_url = str(created.get("_links", {}).get("html", {}).get("href") or "")
        fallback_url = str(created.get("url") or "")

        return {
            "id": created_id,
            "key": created_id,
            "url": html_url or fallback_url,
        }

    def _get_org_project(self) -> tuple[str | None, str | None]:
        """Query: return current org and project without mutation."""
        return self.org, self.project

    def _set_org_project(self, org: str | None, project: str | None) -> None:
        """Command: set org and project without reading current state."""
        self.org = org
        self.project = project

    @beartype
    @require(lambda project_id: isinstance(project_id, str) and len(project_id) > 0, "project_id must be non-empty")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def fetch_all_issues(self, project_id: str, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Fetch all ADO work items as provider-agnostic dictionaries for graph building."""
        resolved_org, resolved_project = self._resolve_graph_project_context(project_id)
        saved_org, saved_project = self._get_org_project()
        self._set_org_project(resolved_org, resolved_project)
        try:
            backlog_filters = BacklogFilters(**(filters or {}))
            return [item.model_dump() for item in self.fetch_backlog_items(backlog_filters)]
        finally:
            self._set_org_project(saved_org, saved_project)

    def _edges_from_ado_work_item_relations(self, item: dict[str, Any], item_id: str) -> list[tuple[str, str, str]]:
        """Collect normalized graph edges from an ADO work item's relation list."""
        edges: list[tuple[str, str, str]] = []
        for relation in _flatten_issue_relation_dicts(cast(dict[str, Any], item)):
            if not isinstance(relation, dict):
                continue
            rel_name = str(relation.get("rel") or relation.get("relation") or relation.get("type") or "").lower()
            target_ref = str(relation.get("url") or relation.get("target") or "")
            target_wi = self._extract_work_item_id_from_reference(target_ref)
            if not target_wi:
                continue
            edge = _ado_graph_edge_from_relation(rel_name, item_id, target_wi)
            if edge:
                edges.append(edge)
        return edges

    @beartype
    @require(lambda project_id: isinstance(project_id, str) and len(project_id) > 0, "project_id must be non-empty")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def fetch_relationships(self, project_id: str) -> list[dict[str, Any]]:
        """Fetch ADO relationship edges for graph building."""
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

        for item in self.fetch_all_issues(project_id):
            item_id = str(item.get("id") or item.get("key") or "").strip()
            if not item_id:
                continue
            for src, tgt, et in self._edges_from_ado_work_item_relations(item, item_id):
                _add_edge(src, tgt, et)

        return relationships

    @beartype
    @require(
        lambda project_id: isinstance(project_id, str) and len(project_id.strip()) > 0, "project_id must be non-empty"
    )
    @ensure(lambda result: isinstance(result, tuple) and len(result) == 2, "Must return (org, project) tuple")
    def _resolve_graph_project_context(self, project_id: str) -> tuple[str, str]:
        """Resolve org/project context for graph APIs from linked project_id and adapter defaults."""
        normalized = project_id.strip()
        if "/" in normalized:
            org, project = normalized.split("/", 1)
            resolved_org = org.strip()
            resolved_project = project.strip()
            if resolved_org and resolved_project:
                return resolved_org, resolved_project
            raise ValueError(f"Invalid ADO project_id format: {project_id!r}. Expected '<org>/<project>'.")

        # Backward compatibility: allow project-only identifiers when adapter org already exists.
        if self.org:
            return self.org, normalized
        raise ValueError(
            f"ADO project_id '{project_id}' missing organization. Use '<org>/<project>' or configure adapter org."
        )

    @beartype
    @ensure(lambda result: isinstance(result, str), "Work item id extraction must return str")
    def _extract_work_item_id_from_reference(self, reference: str) -> str:
        """Extract ADO work item id from relation reference URL/string."""
        if not reference:
            return ""
        match = re.search(r"/workitems/(\d+)", reference, flags=re.IGNORECASE)
        return match.group(1) if match else ""

    @beartype
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def supports_add_comment(self) -> bool:
        """Whether this adapter can add comments (requires token, org, project)."""
        return bool(self.api_token and self.org and self.project)

    @beartype
    @require(lambda item: isinstance(item, BacklogItem), "item must be BacklogItem")
    @require(lambda comment: isinstance(comment, str) and bool(comment.strip()), "comment must be non-empty string")
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
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
    @require(lambda item: isinstance(item, BacklogItem), "item must be BacklogItem")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def get_comments(self, item: BacklogItem) -> list[str]:
        """
        Fetch comments for an Azure DevOps work item.

        Args:
            item: BacklogItem to fetch comments for

        Returns:
            List of comment body strings, or empty list on error
        """
        if not self.org or not self.project:
            return []

        if not item.id.isdigit():
            return []

        raw = self._get_work_item_comments(self.org, self.project, int(item.id))
        comment_texts: list[str] = []
        for comment in raw:
            if not isinstance(comment, dict):
                continue
            text = comment.get("text") or comment.get("body")
            if isinstance(text, str):
                stripped = text.strip()
                if stripped:
                    comment_texts.append(stripped)
        return comment_texts

    def _patch_ops_backlog_title_and_body(
        self,
        item: BacklogItem,
        update_fields: list[str] | None,
        ado_mapper: AdoFieldMapper,
        provider_field_names: set[str],
    ) -> list[dict[str, Any]]:
        operations: list[dict[str, Any]] = []
        if update_fields is None or "title" in update_fields:
            operations.append({"op": "replace", "path": "/fields/System.Title", "value": item.title})

        if update_fields is None or "body" in update_fields or "body_markdown" in update_fields:
            raw_body = item.body_markdown
            markdown_content = raw_body if raw_body is not None else ""
            markdown_content = self._strip_leading_description_heading(markdown_content)
            todo_pattern = r"^(\s*)[-*]\s*\[TODO[:\s]+([^\]]+)\](.*)$"
            markdown_content = re.sub(
                todo_pattern,
                r"\1- [ ] \2",
                markdown_content,
                flags=re.MULTILINE | re.IGNORECASE,
            )

            description_field = (
                ado_mapper.resolve_write_target_field("description", provider_field_names) or "System.Description"
            )
            operations.append({"op": "add", "path": f"/multilineFieldsFormat/{description_field}", "value": "Markdown"})
            operations.append({"op": "replace", "path": f"/fields/{description_field}", "value": markdown_content})

        return operations

    def _patch_ops_backlog_mapped_optional_fields(
        self,
        item: BacklogItem,
        update_fields: list[str] | None,
        ado_mapper: AdoFieldMapper,
        provider_field_names: set[str],
    ) -> list[dict[str, Any]]:
        operations: list[dict[str, Any]] = []
        operations.extend(
            _ado_patch_ops_optional_acceptance_criteria(item, update_fields, ado_mapper, provider_field_names)
        )
        operations.extend(_ado_patch_ops_optional_story_points(item, update_fields, ado_mapper, provider_field_names))
        operations.extend(_ado_patch_ops_optional_business_value(item, update_fields, ado_mapper, provider_field_names))
        operations.extend(_ado_patch_ops_optional_priority(item, update_fields, ado_mapper, provider_field_names))
        return operations

    def _build_update_backlog_patch_operations(
        self, item: BacklogItem, update_fields: list[str] | None
    ) -> list[dict[str, Any]]:
        custom_mapping_file = os.environ.get("SPECFACT_ADO_CUSTOM_MAPPING")
        ado_mapper = AdoFieldMapper(custom_mapping_file=custom_mapping_file)
        provider_field_names: set[str] = set()
        provider_fields_payload = item.provider_fields.get("fields")
        if isinstance(provider_fields_payload, dict):
            provider_field_names = {str(field_name) for field_name in provider_fields_payload}

        operations: list[dict[str, Any]] = []
        operations.extend(self._patch_ops_backlog_title_and_body(item, update_fields, ado_mapper, provider_field_names))
        operations.extend(
            self._patch_ops_backlog_mapped_optional_fields(item, update_fields, ado_mapper, provider_field_names)
        )

        if update_fields is None or "state" in update_fields:
            operations.append({"op": "replace", "path": "/fields/System.State", "value": item.state})

        return operations

    @staticmethod
    def _backlog_ops_without_multiline_format(operations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [op for op in operations if not (op.get("path") or "").startswith("/multilineFieldsFormat/")]

    @staticmethod
    def _backlog_ops_replace_multiline_add_with_replace(operations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for op in operations:
            path = op.get("path") or ""
            if path.startswith("/multilineFieldsFormat/"):
                out.append({"op": "replace", "path": path, "value": op["value"]})
            else:
                out.append(op)
        return out

    @staticmethod
    def _backlog_ops_convert_markdown_fields_to_html(operations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        markdown_formatted_fields = {
            str(op.get("path", "")).replace("/multilineFieldsFormat/", "", 1)
            for op in operations
            if str(op.get("path", "")).startswith("/multilineFieldsFormat/")
            and str(op.get("value", "")).lower() == "markdown"
        }

        operations_html = [
            dict(op) for op in operations if not (op.get("path") or "").startswith("/multilineFieldsFormat/")
        ]
        for op in operations_html:
            field_path = str(op.get("path", ""))
            if not field_path.startswith("/fields/"):
                continue
            field_name = field_path.replace("/fields/", "", 1)
            if field_name in markdown_formatted_fields:
                op["value"] = _markdown_to_html_ado_fallback(str(op.get("value") or ""))
        return operations_html

    @staticmethod
    def _ado_http_error_message(response: requests.Response | None) -> str:
        if not response:
            return ""
        try:
            err = response.json()
            return str(err.get("message", "") or "")
        except Exception:
            return ""

    def _backlog_patch_try_without_multiline_format(
        self,
        url: str,
        headers: dict[str, Any],
        operations: list[dict[str, Any]],
    ) -> requests.Response | None:
        operations_no_format = self._backlog_ops_without_multiline_format(operations)
        if operations_no_format == operations:
            return None
        try:
            resp = requests.patch(url, headers=headers, json=operations_no_format, timeout=30)
            resp.raise_for_status()
            return resp
        except requests.HTTPError as retry_error:
            _log_ado_patch_failure(
                retry_error.response,
                operations_no_format,
                url,
                context=str(retry_error),
            )
            return None

    def _backlog_patch_try_replace_multiline_add(
        self,
        url: str,
        headers: dict[str, Any],
        operations: list[dict[str, Any]],
    ) -> requests.Response | None:
        operations_replace = self._backlog_ops_replace_multiline_add_with_replace(operations)
        try:
            resp = requests.patch(url, headers=headers, json=operations_replace, timeout=30)
            resp.raise_for_status()
            return resp
        except requests.HTTPError:
            return None

    def _backlog_patch_try_html_conversion(
        self,
        url: str,
        headers: dict[str, Any],
        operations: list[dict[str, Any]],
        user_msg: str,
    ) -> requests.Response | None:
        console.print(
            "[yellow]⚠ Markdown format metadata not supported, converting multiline markdown fields to HTML[/yellow]"
        )
        operations_html = self._backlog_ops_convert_markdown_fields_to_html(operations)
        try:
            resp = requests.patch(url, headers=headers, json=operations_html, timeout=30)
            resp.raise_for_status()
            return resp
        except requests.HTTPError:
            console.print(f"[bold red]✗[/bold red] {user_msg}")
            raise

    def _execute_backlog_patch_with_fallbacks(
        self,
        url: str,
        headers: dict[str, Any],
        operations: list[dict[str, Any]],
    ) -> requests.Response:
        try:
            return self._request_with_retry(lambda: requests.patch(url, headers=headers, json=operations, timeout=30))
        except requests.HTTPError as e:
            user_msg = _log_ado_patch_failure(e.response, operations, url)
            e.ado_user_message = user_msg  # type: ignore[attr-defined]
            response: requests.Response | None = None
            if e.response and e.response.status_code in (400, 422):
                error_message = self._ado_http_error_message(e.response)
                response = self._backlog_patch_try_without_multiline_format(url, headers, operations)
                if response is None and (
                    "already exists" in error_message.lower() or "cannot add" in error_message.lower()
                ):
                    response = self._backlog_patch_try_replace_multiline_add(url, headers, operations)
                if response is None:
                    response = self._backlog_patch_try_html_conversion(url, headers, operations, user_msg)

            if response is None:
                console.print(f"[bold red]✗[/bold red] {user_msg}")
                raise
            return response

    @beartype
    @require(lambda item: isinstance(item, BacklogItem), "Item must be BacklogItem")
    @require(
        lambda update_fields: update_fields is None or isinstance(update_fields, list),
        "Update fields must be None or list",
    )
    @ensure(lambda result: isinstance(result, BacklogItem), "Must return BacklogItem")
    @ensure(
        lambda result, item: ensure_backlog_update_preserves_identity(result, item),
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

        operations = self._build_update_backlog_patch_operations(item, update_fields)
        response = self._execute_backlog_patch_with_fallbacks(url, headers, operations)

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


BRIDGE_PROTOCOL_REGISTRY.register_implementation("backlog_graph", "ado", AdoAdapter)
