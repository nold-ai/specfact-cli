"""
Backlog item converter utilities.

This module provides utilities to convert adapter items (GitHub issues, ADO work items, etc.)
to BacklogItem domain models, handling arbitrary DevOps backlog input.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

from beartype import beartype
from icontract import ensure, require

from specfact_cli.backlog.mappers.ado_mapper import AdoFieldMapper
from specfact_cli.backlog.mappers.github_mapper import GitHubFieldMapper
from specfact_cli.models.backlog_item import BacklogItem
from specfact_cli.models.source_tracking import SourceTracking


def _github_issue_has_number_or_id(item_data: dict[str, Any]) -> bool:
    return bool(item_data.get("number") or item_data.get("id"))


def _github_issue_has_url(item_data: dict[str, Any]) -> bool:
    return bool(item_data.get("html_url") or item_data.get("url"))


def _ado_item_has_id(item_data: dict[str, Any]) -> bool:
    return bool(item_data.get("id"))


def _require_ado_work_item_core(item_data: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    work_item_id = str(item_data.get("id") or "")
    if not work_item_id:
        msg = "ADO work item must have 'id' field"
        raise ValueError(msg)
    links_raw = item_data.get("_links", {})
    links: dict[str, Any] = links_raw if isinstance(links_raw, dict) else {}
    html_raw = links.get("html", {})
    html: dict[str, Any] = html_raw if isinstance(html_raw, dict) else {}
    href = str(html.get("href", ""))
    url = item_data.get("url") or href or ""
    if not url:
        msg = "ADO work item must have 'url' or '_links.html.href' field"
        raise ValueError(msg)
    fields = item_data.get("fields", {})
    if not fields:
        msg = "ADO work item must have 'fields' dict"
        raise ValueError(msg)
    title = fields.get("System.Title", "").strip()
    if not title:
        msg = "ADO work item must have 'System.Title' field"
        raise ValueError(msg)
    return work_item_id, url, fields


def _ado_item_has_url(item_data: dict[str, Any]) -> bool:
    links_raw = item_data.get("_links", {})
    links: dict[str, Any] = links_raw if isinstance(links_raw, dict) else {}
    html_raw = links.get("html", {})
    html: dict[str, Any] = html_raw if isinstance(html_raw, dict) else {}
    href = str(html.get("href", ""))
    return bool(item_data.get("url") or href)


def _github_assignees_from_item(item_data: dict[str, Any]) -> list[str]:
    assignees: list[str] = []
    raw_assignees = item_data.get("assignees")
    if raw_assignees:
        if not isinstance(raw_assignees, list):
            return assignees
        for a in raw_assignees:
            if not a:
                continue
            if isinstance(a, dict):
                ad: dict[str, Any] = a
                assignees.append(str(ad.get("login", "")))
            else:
                assignees.append(str(a))
    elif item_data.get("assignee"):
        assignee = item_data["assignee"]
        if isinstance(assignee, dict):
            ag: dict[str, Any] = assignee
            assignees = [str(ag.get("login", ""))]
        else:
            assignees = [str(assignee)]
    return assignees


def _github_issue_labels_as_tags(item_data: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    raw_labels = item_data.get("labels")
    if not raw_labels or not isinstance(raw_labels, list):
        return tags
    for label in raw_labels:
        if not label:
            continue
        if isinstance(label, dict):
            ld: dict[str, Any] = label
            tags.append(str(ld.get("name", "")))
        else:
            tags.append(str(label))
    return tags


def _require_github_issue_core(item_data: dict[str, Any]) -> tuple[str, str, str]:
    issue_id = str(item_data.get("number") or item_data.get("id") or "")
    if not issue_id:
        msg = "GitHub issue must have 'number' or 'id' field"
        raise ValueError(msg)
    url = item_data.get("html_url") or item_data.get("url") or ""
    if not url:
        msg = "GitHub issue must have 'html_url' or 'url' field"
        raise ValueError(msg)
    title = item_data.get("title", "").strip()
    if not title:
        msg = "GitHub issue must have 'title' field"
        raise ValueError(msg)
    return issue_id, url, title


def _milestone_sprint_release_github(milestone: Any) -> tuple[str | None, str | None]:
    if not milestone:
        return None, None
    if isinstance(milestone, dict):
        md: dict[str, Any] = milestone
        milestone_title = str(md.get("title", ""))
    else:
        milestone_title = str(milestone)
    milestone_title_lower = milestone_title.lower()
    if "sprint" in milestone_title_lower:
        return milestone_title, None
    if "release" in milestone_title_lower or milestone_title_lower.startswith(("v", "r")):
        return None, milestone_title
    return None, None


@beartype
@require(lambda item_data: isinstance(item_data, dict), "Item data must be dict")
@require(lambda provider: isinstance(provider, str) and len(provider) > 0, "Provider must be non-empty string")
@require(
    _github_issue_has_number_or_id,
    "GitHub issue must include 'number' or 'id'",
)
@require(
    _github_issue_has_url,
    "GitHub issue must include 'html_url' or 'url'",
)
@ensure(lambda result: isinstance(result, BacklogItem), "Must return BacklogItem")
def convert_github_issue_to_backlog_item(item_data: dict[str, Any], provider: str = "github") -> BacklogItem:
    """
    Convert GitHub issue data to BacklogItem.

    Handles arbitrary GitHub issue input and normalizes it to BacklogItem format.

    Args:
        item_data: GitHub issue data from API (dict)
        provider: Provider name (default: "github")

    Returns:
        BacklogItem instance with normalized fields

    Raises:
        ValueError: If required fields are missing
    """
    issue_id, url, title = _require_github_issue_core(item_data)

    body_markdown = item_data.get("body", "") or ""
    state = item_data.get("state", "open").lower()

    # Extract fields using GitHubFieldMapper
    github_mapper = GitHubFieldMapper()
    extracted_fields: dict[str, Any] = github_mapper.extract_fields(item_data)
    acceptance_criteria = extracted_fields.get("acceptance_criteria")
    story_points = extracted_fields.get("story_points")
    business_value = extracted_fields.get("business_value")
    priority = extracted_fields.get("priority")
    value_points = extracted_fields.get("value_points")
    work_item_type = extracted_fields.get("work_item_type")

    assignees = _github_assignees_from_item(item_data)

    tags = _github_issue_labels_as_tags(item_data)

    # Extract timestamps
    created_at = _parse_github_timestamp(item_data.get("created_at"))
    updated_at = _parse_github_timestamp(item_data.get("updated_at"))

    # Create source tracking
    source_tracking = SourceTracking(
        tool=provider,
        source_metadata={
            "source_id": issue_id,
            "source_url": url,
            "source_state": state,
            "assignees": assignees,
            "labels": tags,
        },
    )

    milestone = item_data.get("milestone")
    sprint, release = _milestone_sprint_release_github(milestone)

    # Preserve provider-specific fields
    provider_fields = {
        "number": issue_id,
        "html_url": url,
        "api_url": item_data.get("url", ""),
        "user": item_data.get("user", {}),
        "milestone": item_data.get("milestone"),
        "comments": item_data.get("comments", 0),
        "comments_url": item_data.get("comments_url", ""),
        "events_url": item_data.get("events_url", ""),
        "labels_url": item_data.get("labels_url", ""),
    }

    return BacklogItem(
        id=issue_id,
        provider=provider,
        url=url,
        title=title,
        body_markdown=body_markdown,
        state=state,
        assignees=assignees,
        tags=tags,
        iteration=None,  # GitHub doesn't have iteration path, use milestone instead
        sprint=sprint,
        release=release,
        created_at=created_at,
        updated_at=updated_at,
        source_tracking=source_tracking,
        provider_fields=provider_fields,
        acceptance_criteria=acceptance_criteria,
        story_points=story_points,
        business_value=business_value,
        priority=priority,
        value_points=value_points,
        work_item_type=work_item_type,
    )


@beartype
@require(lambda item_data: isinstance(item_data, dict), "Item data must be dict")
@require(lambda provider: isinstance(provider, str) and len(provider) > 0, "Provider must be non-empty string")
@require(_ado_item_has_id, "ADO work item must include 'id'")
@require(
    _ado_item_has_url,
    "ADO work item must include 'url' or '_links.html.href'",
)
@ensure(lambda result: isinstance(result, BacklogItem), "Must return BacklogItem")
def convert_ado_work_item_to_backlog_item(
    item_data: dict[str, Any],
    provider: str = "ado",
    custom_mapping_file: str | Path | None = None,
    base_url: str | None = None,
    org: str | None = None,
    project_name: str | None = None,
) -> BacklogItem:
    """
    Convert Azure DevOps work item data to BacklogItem.

    Handles arbitrary ADO work item input and normalizes it to BacklogItem format.

    Args:
        item_data: ADO work item data from API (dict)
        provider: Provider name (default: "ado")
        custom_mapping_file: Optional path to custom ADO field mapping file.
        base_url: ADO base URL (e.g. https://dev.azure.com) for canonical URL.
        org: ADO organization name for canonical URL.
        project_name: ADO project name (URL-encoded in canonical URL) for opening in browser.

    Returns:
        BacklogItem instance with normalized fields

    Raises:
        ValueError: If required fields are missing
    """
    work_item_id, url, fields = _require_ado_work_item_core(item_data)

    title = fields.get("System.Title", "").strip()

    state = fields.get("System.State", "New").lower()

    ext = _ado_mapper_extractions(item_data, fields, custom_mapping_file)
    body_markdown = ext["body_markdown"]
    acceptance_criteria = ext["acceptance_criteria"]
    story_points = ext["story_points"]
    business_value = ext["business_value"]
    priority = ext["priority"]
    value_points = ext["value_points"]
    work_item_type = ext["work_item_type"]

    assignees = _ado_assignees_from_fields(fields)

    tags = []
    ado_tags = fields.get("System.Tags", "")
    if ado_tags:
        tags = [t.strip() for t in ado_tags.split(";") if t.strip()]

    iteration = fields.get("System.IterationPath", "")
    area = fields.get("System.AreaPath", "")

    sprint, release = _ado_sprint_release_from_iteration(iteration)

    # Extract timestamps
    created_at = _parse_ado_timestamp(fields.get("System.CreatedDate"))
    updated_at = _parse_ado_timestamp(fields.get("System.ChangedDate"))

    # Create source tracking
    source_tracking = SourceTracking(
        tool=provider,
        source_metadata={
            "source_id": work_item_id,
            "source_url": url,
            "source_state": state,
            "assignees": assignees,
            "tags": tags,
            "work_item_type": fields.get("System.WorkItemType", ""),
        },
    )

    # Preserve provider-specific fields
    provider_fields = {
        "id": work_item_id,
        "rev": item_data.get("rev", 0),
        "fields": fields,
        "relations": item_data.get("relations", []),
        "_links": item_data.get("_links", {}),
    }

    canonical_url = None
    if base_url and org and project_name:
        base = base_url.rstrip("/")
        encoded_project = quote(project_name, safe="")
        canonical_url = f"{base}/{org}/{encoded_project}/_workitems/edit/{work_item_id}"

    return BacklogItem(
        id=work_item_id,
        provider=provider,
        url=url,
        canonical_url=canonical_url,
        title=title,
        body_markdown=body_markdown,
        state=state,
        assignees=assignees,
        tags=tags,
        iteration=iteration,
        sprint=sprint,
        release=release,
        area=area,
        created_at=created_at,
        updated_at=updated_at,
        source_tracking=source_tracking,
        provider_fields=provider_fields,
        acceptance_criteria=acceptance_criteria,
        story_points=story_points,
        business_value=business_value,
        priority=priority,
        value_points=value_points,
        work_item_type=work_item_type,
    )


@beartype
@ensure(lambda result: isinstance(result, dict), "Must return dict")
def _ado_mapper_extractions(
    item_data: dict[str, Any],
    fields: dict[str, Any],
    custom_mapping_file: str | Path | None,
) -> dict[str, Any]:
    """Run AdoFieldMapper and compute body plus extracted optional fields."""
    import os

    if custom_mapping_file is None and os.environ.get("SPECFACT_ADO_CUSTOM_MAPPING"):
        custom_mapping_file = os.environ.get("SPECFACT_ADO_CUSTOM_MAPPING")
    ado_mapper = AdoFieldMapper(custom_mapping_file=custom_mapping_file)
    extracted_fields = ado_mapper.extract_fields(item_data)
    extracted_description = extracted_fields.get("description")
    body_markdown = (
        extracted_description
        if isinstance(extracted_description, str) and extracted_description
        else (fields.get("System.Description", "") or "")
    )
    return {
        "body_markdown": body_markdown,
        "acceptance_criteria": extracted_fields.get("acceptance_criteria"),
        "story_points": extracted_fields.get("story_points"),
        "business_value": extracted_fields.get("business_value"),
        "priority": extracted_fields.get("priority"),
        "value_points": extracted_fields.get("value_points"),
        "work_item_type": extracted_fields.get("work_item_type"),
    }


def _ado_assignees_from_fields(fields: dict[str, Any]) -> list[str]:
    assignees: list[str] = []
    assigned_to = fields.get("System.AssignedTo", {})
    if not assigned_to:
        return assignees
    if isinstance(assigned_to, dict):
        assignee_candidates: list[str] = []
        at: dict[str, Any] = assigned_to
        if at.get("displayName"):
            assignee_candidates.append(str(at["displayName"]).strip())
        if at.get("uniqueName"):
            assignee_candidates.append(str(at["uniqueName"]).strip())
        if at.get("mail"):
            assignee_candidates.append(str(at["mail"]).strip())
        seen: set[str] = set()
        for candidate in assignee_candidates:
            if candidate and candidate not in seen:
                assignees.append(candidate)
                seen.add(candidate)
    else:
        assignee_str = str(assigned_to).strip()
        if assignee_str:
            assignees = [assignee_str]
    return assignees


def _ado_sprint_release_from_iteration(iteration: str) -> tuple[str | None, str | None]:
    if not iteration:
        return None, None
    parts = [p.strip() for p in iteration.split("\\") if p.strip()]
    sprint: str | None = None
    release: str | None = None
    for i, part in enumerate(parts):
        part_lower = part.lower()
        if "sprint" in part_lower:
            sprint = part
            if i > 0 and ("release" in parts[i - 1].lower() or parts[i - 1].lower().startswith("r")):
                release = parts[i - 1]
        elif "release" in part_lower or part_lower.startswith("r"):
            release = part
    return sprint, release


def _parse_github_timestamp(timestamp: str | None) -> datetime:
    """
    Parse GitHub timestamp string to datetime.

    Args:
        timestamp: GitHub timestamp string (ISO 8601 format) or None

    Returns:
        datetime instance (UTC)
    """
    if not timestamp:
        return datetime.now(UTC)

    try:
        # GitHub uses ISO 8601 format: "2024-01-18T10:30:00Z"
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except (TypeError, ValueError, AttributeError):
        return datetime.now(UTC)


@beartype
@require(lambda timestamp: timestamp is None or isinstance(timestamp, str), "Timestamp must be str or None")
@ensure(lambda result: isinstance(result, datetime), "Must return datetime")
def _parse_ado_timestamp(timestamp: str | None) -> datetime:
    """
    Parse ADO timestamp string to datetime.

    Args:
        timestamp: ADO timestamp string (ISO 8601 format) or None

    Returns:
        datetime instance (UTC)
    """
    if not timestamp:
        return datetime.now(UTC)

    try:
        # ADO uses ISO 8601 format: "2024-01-18T10:30:00Z"
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except (TypeError, ValueError, AttributeError):
        return datetime.now(UTC)
