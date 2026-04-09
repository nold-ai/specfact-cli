#!/usr/bin/env python3
"""Sync GitHub Epic/Feature hierarchy into a local OpenSpec cache."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require


DEFAULT_REPO_OWNER = "nold-ai"
_SCRIPT_DIR = Path(__file__).resolve().parent


@beartype
@ensure(
    lambda result: result is None or bool(str(result).strip()),
    "parsed repository name must be non-blank when present",
)
def parse_repo_name_from_remote_url(url: str) -> str | None:
    """Return the repository name segment from a Git remote URL, if parseable."""
    stripped = url.strip()
    if not stripped:
        return None
    if stripped.startswith("git@"):
        _, _, rest = stripped.partition(":")
        path = rest
    elif "://" in stripped:
        host_and_path = stripped.split("://", 1)[1]
        if "/" not in host_and_path:
            return None
        path = host_and_path.split("/", 1)[1]
    else:
        path = stripped
    path = path.rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    segments = [segment for segment in path.split("/") if segment]
    if not segments:
        return None
    return segments[-1]


@beartype
def _default_repo_name_from_git(script_dir: Path) -> str | None:
    """Resolve the GitHub repository name from ``origin`` (works in worktrees)."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(script_dir), "config", "--get", "remote.origin.url"],
            check=False,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, OSError):
        return None
    if completed.returncode != 0:
        return None
    return parse_repo_name_from_remote_url(completed.stdout)


_DEFAULT_REPO_NAME_FALLBACK = Path(__file__).resolve().parents[1].name
DEFAULT_REPO_NAME = _default_repo_name_from_git(_SCRIPT_DIR) or _DEFAULT_REPO_NAME_FALLBACK
DEFAULT_OUTPUT_PATH = Path(".specfact") / "backlog" / "github_hierarchy_cache.md"
DEFAULT_STATE_PATH = Path(".specfact") / "backlog" / "github_hierarchy_cache_state.json"
SUPPORTED_ISSUE_TYPES = frozenset({"Epic", "Feature"})
SUPPORTED_ISSUE_TYPES_ORDER: tuple[str, ...] = ("Epic", "Feature")
_SUMMARY_SKIP_LINES = {"why", "scope", "summary", "changes", "capabilities", "impact"}
_GH_GRAPHQL_TIMEOUT_SEC = 120


@beartype
def _build_hierarchy_issues_query(*, include_body: bool) -> str:
    """Return the shared GitHub GraphQL query, optionally including issue body text."""
    body_field = "        bodyText\n" if include_body else ""
    return f"""
query($owner: String!, $name: String!, $after: String) {{
  repository(owner: $owner, name: $name) {{
    issues(first: 100, after: $after, states: [OPEN, CLOSED], orderBy: {{field: CREATED_AT, direction: ASC}}) {{
      pageInfo {{ hasNextPage endCursor }}
      nodes {{
        number
        title
        url
        updatedAt
{body_field}        issueType {{ name }}
        labels(first: 100) {{ nodes {{ name }} }}
        parent {{ number title url }}
        subIssues(first: 100) {{ nodes {{ number title url issueType {{ name }} }} }}
      }}
    }}
  }}
}}
""".strip()


@dataclass(frozen=True)
class IssueLink:
    """Compact link to a related issue."""

    number: int
    title: str
    url: str


@dataclass(frozen=True)
class HierarchyIssue:
    """Normalized hierarchy issue used for cache rendering."""

    number: int
    title: str
    url: str
    issue_type: str
    labels: list[str]
    summary: str
    updated_at: str
    parent: IssueLink | None
    children: list[IssueLink]


@dataclass(frozen=True)
class SyncResult:
    """Outcome of a cache sync attempt."""

    changed: bool
    issue_count: int
    fingerprint: str
    output_path: Path


@beartype
def _extract_summary(body_text: str) -> str:
    """Return a compact summary line for markdown output."""
    normalized = body_text.replace("\\n", "\n")
    for line in normalized.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        if cleaned.startswith("#"):
            cleaned = cleaned.lstrip("#").strip()
        if cleaned.lower().rstrip(":") in _SUMMARY_SKIP_LINES:
            continue
        if cleaned:
            return cleaned[:200]
    return "No summary provided."


@beartype
def _parse_issue_link(node: Mapping[str, Any] | None) -> IssueLink | None:
    """Convert a GraphQL link node to IssueLink."""
    if not node:
        return None
    return IssueLink(
        number=int(node["number"]),
        title=str(node["title"]),
        url=str(node["url"]),
    )


@beartype
def _mapping_value(node: Mapping[str, Any], key: str) -> Mapping[str, Any] | None:
    """Return a nested mapping value when present."""
    value = node.get(key)
    return value if isinstance(value, Mapping) else None


@beartype
def _mapping_nodes(container: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    """Return a filtered list of mapping nodes from a GraphQL connection."""
    if container is None:
        return []

    raw_nodes = container.get("nodes")
    if not isinstance(raw_nodes, list):
        return []

    return [item for item in raw_nodes if isinstance(item, Mapping)]


@beartype
def _label_names(label_nodes: list[Mapping[str, Any]]) -> list[str]:
    """Extract sorted label names from GraphQL label nodes."""
    names: list[str] = []
    for item in label_nodes:
        name = item.get("name")
        if name:
            names.append(str(name))
    return sorted(names, key=str.lower)


@beartype
def _subissue_type_name(item: Mapping[str, Any]) -> str | None:
    """Return sub-issue type name when present."""
    issue_type_node = _mapping_value(item, "issueType")
    if issue_type_node and issue_type_node.get("name"):
        return str(issue_type_node["name"])
    return None


@beartype
def _child_links(subissue_nodes: list[Mapping[str, Any]]) -> list[IssueLink]:
    """Extract sorted child issue links from GraphQL subissue nodes (Epic/Feature only)."""
    children = [
        IssueLink(number=int(item["number"]), title=str(item["title"]), url=str(item["url"]))
        for item in subissue_nodes
        if item.get("number") is not None and _subissue_type_name(item) in SUPPORTED_ISSUE_TYPES
    ]
    children.sort(key=lambda item: item.number)
    return children


@beartype
def _parse_issue_node(node: Mapping[str, Any], *, include_body: bool) -> HierarchyIssue | None:
    """Convert a GraphQL issue node to HierarchyIssue when supported."""
    issue_type_node = _mapping_value(node, "issueType")
    issue_type_name = str(issue_type_node["name"]) if issue_type_node and issue_type_node.get("name") else None
    if issue_type_name not in SUPPORTED_ISSUE_TYPES:
        return None

    summary = _extract_summary(str(node.get("bodyText", ""))) if include_body else ""
    return HierarchyIssue(
        number=int(node["number"]),
        title=str(node["title"]),
        url=str(node["url"]),
        issue_type=str(issue_type_name),
        labels=_label_names(_mapping_nodes(_mapping_value(node, "labels"))),
        summary=summary,
        updated_at=str(node["updatedAt"]),
        parent=_parse_issue_link(_mapping_value(node, "parent")),
        children=_child_links(_mapping_nodes(_mapping_value(node, "subIssues"))),
    )


@beartype
def _run_graphql_query(query: str, *, repo_owner: str, repo_name: str, after: str | None) -> Mapping[str, Any]:
    """Run a GitHub GraphQL query through `gh`."""
    command = [
        "gh",
        "api",
        "graphql",
        "-f",
        f"query={query}",
        "-F",
        f"owner={repo_owner}",
        "-F",
        f"name={repo_name}",
    ]
    if after is not None:
        command.extend(["-F", f"after={after}"])

    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=_GH_GRAPHQL_TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired as exc:
        detail = f"GitHub GraphQL subprocess timed out after {_GH_GRAPHQL_TIMEOUT_SEC}s"
        out = (exc.stdout or "").strip()
        err = (exc.stderr or "").strip()
        if out or err:
            detail = f"{detail}; stdout={out!r}; stderr={err!r}"
        raise RuntimeError(detail) from exc

    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "GitHub GraphQL query failed")

    payload = json.loads(completed.stdout)
    if "errors" in payload:
        raise RuntimeError(json.dumps(payload["errors"], indent=2))
    return payload


@beartype
def _is_not_blank(value: str) -> bool:
    """Return whether a required CLI string value is non-blank."""
    return bool(value.strip())


@beartype
def _all_supported_issue_types(result: list[HierarchyIssue]) -> bool:
    """Return whether every issue has a supported issue type."""
    return all(issue.issue_type in SUPPORTED_ISSUE_TYPES for issue in result)


@beartype
def _require_repo_owner_for_fetch(*, repo_owner: str, repo_name: str, fingerprint_only: bool) -> bool:
    _ = (repo_name, fingerprint_only)
    return _is_not_blank(repo_owner)


@beartype
def _require_repo_name_for_fetch(*, repo_owner: str, repo_name: str, fingerprint_only: bool) -> bool:
    _ = (repo_owner, fingerprint_only)
    return _is_not_blank(repo_name)


@beartype
@require(_require_repo_owner_for_fetch, "repo_owner must not be blank")
@require(_require_repo_name_for_fetch, "repo_name must not be blank")
@ensure(_all_supported_issue_types, "Only Epic and Feature issues should be returned")
def fetch_hierarchy_issues(*, repo_owner: str, repo_name: str, fingerprint_only: bool) -> list[HierarchyIssue]:
    """Fetch Epic and Feature issues from GitHub for the given repository."""
    query = _build_hierarchy_issues_query(include_body=not fingerprint_only)
    issues: list[HierarchyIssue] = []
    after: str | None = None

    while True:
        payload = _run_graphql_query(query, repo_owner=repo_owner, repo_name=repo_name, after=after)
        repository = payload.get("data", {}).get("repository", {})
        issue_connection = repository.get("issues", {})
        nodes = issue_connection.get("nodes", [])
        for node in nodes:
            if not isinstance(node, Mapping):
                continue
            parsed = _parse_issue_node(node, include_body=not fingerprint_only)
            if parsed is not None:
                issues.append(parsed)
        page_info = issue_connection.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        after = page_info.get("endCursor")

    return issues


@beartype
@ensure(lambda result: len(result) == 64, "Fingerprint must be a SHA-256 hex digest")
def compute_hierarchy_fingerprint(issues: list[HierarchyIssue]) -> str:
    """Compute a deterministic fingerprint for hierarchy state."""
    canonical_rows: list[dict[str, Any]] = []
    for issue in sorted(issues, key=lambda item: (item.issue_type, item.number)):
        canonical_rows.append(
            {
                "number": issue.number,
                "title": issue.title,
                "issue_type": issue.issue_type,
                "updated_at": issue.updated_at,
                "labels": sorted(issue.labels, key=str.lower),
                "parent_number": issue.parent.number if issue.parent else None,
                "child_numbers": [child.number for child in sorted(issue.children, key=lambda item: item.number)],
            }
        )

    canonical_json = json.dumps(canonical_rows, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


@beartype
def _group_issues_by_type(issues: list[HierarchyIssue]) -> dict[str, list[HierarchyIssue]]:
    """Return issues grouped by supported type in deterministic order."""
    return {
        issue_type: sorted((item for item in issues if item.issue_type == issue_type), key=lambda item: item.number)
        for issue_type in SUPPORTED_ISSUE_TYPES_ORDER
    }


@beartype
def _render_issue_block(issue: HierarchyIssue) -> list[str]:
    """Render one issue block for the hierarchy cache."""
    parent_text = "none"
    if issue.parent is not None:
        parent_text = f"#{issue.parent.number} {issue.parent.title}"

    child_text = "none"
    if issue.children:
        child_text = ", ".join(f"#{child.number} {child.title}" for child in issue.children)

    label_text = ", ".join(sorted(issue.labels, key=str.lower)) if issue.labels else "none"
    return [
        f"### #{issue.number} {issue.title}",
        f"- URL: {issue.url}",
        f"- Parent: {parent_text}",
        f"- Children: {child_text}",
        f"- Labels: {label_text}",
        f"- Summary: {issue.summary or 'No summary provided.'}",
        "",
    ]


@beartype
def _render_issue_section(*, title: str, issues: list[HierarchyIssue]) -> list[str]:
    """Render one section of grouped issues."""
    lines = [f"## {title}", ""]
    if not issues:
        lines.extend(["_None_", ""])
        return lines

    for issue in issues:
        lines.extend(_render_issue_block(issue))
    return lines


@beartype
def _require_repo_full_name_for_render(
    *, repo_full_name: str, issues: list[HierarchyIssue], generated_at: str, fingerprint: str
) -> bool:
    _ = (issues, generated_at, fingerprint)
    return _is_not_blank(repo_full_name)


@beartype
def _require_generated_at_for_render(
    *, repo_full_name: str, issues: list[HierarchyIssue], generated_at: str, fingerprint: str
) -> bool:
    _ = (repo_full_name, issues, fingerprint)
    return _is_not_blank(generated_at)


@beartype
def _require_fingerprint_for_render(
    *, repo_full_name: str, issues: list[HierarchyIssue], generated_at: str, fingerprint: str
) -> bool:
    _ = (repo_full_name, issues, generated_at)
    return _is_not_blank(fingerprint)


@beartype
@require(_require_repo_full_name_for_render, "repo_full_name must not be blank")
@require(_require_generated_at_for_render, "generated_at must not be blank")
@require(_require_fingerprint_for_render, "fingerprint must not be blank")
def render_cache_markdown(
    *,
    repo_full_name: str,
    issues: list[HierarchyIssue],
    generated_at: str,
    fingerprint: str,
) -> str:
    """Render deterministic markdown for the hierarchy cache."""
    grouped = _group_issues_by_type(issues)

    lines = [
        "# GitHub Hierarchy Cache",
        "",
        f"- Repository: `{repo_full_name}`",
        f"- Generated At: `{generated_at}`",
        f"- Fingerprint: `{fingerprint}`",
        f"- Included Issue Types: `{', '.join(sorted(SUPPORTED_ISSUE_TYPES))}`",
        "",
        (
            "Use this file as the first lookup source for parent Epic or Feature relationships "
            "during OpenSpec and GitHub issue setup."
        ),
        "",
    ]

    for section_name, issue_type in (("Epics", "Epic"), ("Features", "Feature")):
        lines.extend(_render_issue_section(title=section_name, issues=grouped[issue_type]))

    return "\n".join(lines).rstrip() + "\n"


@beartype
def _load_state(state_path: Path) -> Mapping[str, Any]:
    """Load state JSON if it exists; otherwise return empty mapping."""
    if not state_path.exists():
        return {}
    try:
        loaded = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, Mapping) else {}


@beartype
def _write_state(
    *, state_path: Path, repo_full_name: str, fingerprint: str, issue_count: int, generated_at: str
) -> None:
    """Persist machine-readable sync state."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "repo": repo_full_name,
        "fingerprint": fingerprint,
        "issue_count": issue_count,
        "generated_at": generated_at,
    }
    state_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@beartype
def _require_repo_owner_for_sync(
    *, repo_owner: str, repo_name: str, output_path: Path, state_path: Path, force: bool = False
) -> bool:
    _ = (repo_name, output_path, state_path, force)
    return _is_not_blank(repo_owner)


@beartype
def _require_repo_name_for_sync(
    *, repo_owner: str, repo_name: str, output_path: Path, state_path: Path, force: bool = False
) -> bool:
    _ = (repo_owner, output_path, state_path, force)
    return _is_not_blank(repo_name)


@beartype
@require(_require_repo_owner_for_sync, "repo_owner must not be blank")
@require(_require_repo_name_for_sync, "repo_name must not be blank")
def sync_cache(
    *,
    repo_owner: str,
    repo_name: str,
    output_path: Path,
    state_path: Path,
    force: bool = False,
) -> SyncResult:
    """Sync the local hierarchy cache from GitHub."""
    state = _load_state(state_path)
    detailed_issues = fetch_hierarchy_issues(
        repo_owner=repo_owner,
        repo_name=repo_name,
        fingerprint_only=False,
    )
    fingerprint = compute_hierarchy_fingerprint(detailed_issues)

    if not force and state.get("fingerprint") == fingerprint and output_path.exists():
        return SyncResult(
            changed=False,
            issue_count=len(detailed_issues),
            fingerprint=fingerprint,
            output_path=output_path,
        )

    generated_at = datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_cache_markdown(
            repo_full_name=f"{repo_owner}/{repo_name}",
            issues=detailed_issues,
            generated_at=generated_at,
            fingerprint=fingerprint,
        ),
        encoding="utf-8",
    )
    _write_state(
        state_path=state_path,
        repo_full_name=f"{repo_owner}/{repo_name}",
        fingerprint=fingerprint,
        issue_count=len(detailed_issues),
        generated_at=generated_at,
    )
    return SyncResult(
        changed=True,
        issue_count=len(detailed_issues),
        fingerprint=fingerprint,
        output_path=output_path,
    )


@beartype
def _build_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-owner", default=DEFAULT_REPO_OWNER, help="GitHub repo owner")
    parser.add_argument("--repo-name", default=DEFAULT_REPO_NAME, help="GitHub repo name")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help="Markdown cache output path")
    parser.add_argument("--state-file", default=str(DEFAULT_STATE_PATH), help="Fingerprint state file path")
    parser.add_argument("--force", action="store_true", help="Rewrite cache even when fingerprint is unchanged")
    return parser


@beartype
@ensure(lambda result: result >= 0, "exit code must be non-negative")
def main(argv: list[str] | None = None) -> int:
    """Run the hierarchy cache sync."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    result = sync_cache(
        repo_owner=args.repo_owner,
        repo_name=args.repo_name,
        output_path=Path(args.output),
        state_path=Path(args.state_file),
        force=bool(args.force),
    )
    if result.changed:
        sys.stdout.write(f"Updated GitHub hierarchy cache with {result.issue_count} issues at {result.output_path}\n")
    else:
        sys.stdout.write(f"GitHub hierarchy cache unchanged ({result.issue_count} issues).\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
