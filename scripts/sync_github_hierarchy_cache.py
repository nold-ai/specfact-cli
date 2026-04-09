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
DEFAULT_REPO_NAME = Path(__file__).resolve().parents[1].name
DEFAULT_OUTPUT_PATH = Path(".specfact") / "backlog" / "github_hierarchy_cache.md"
DEFAULT_STATE_PATH = Path(".specfact") / "backlog" / "github_hierarchy_cache_state.json"
SUPPORTED_ISSUE_TYPES = frozenset({"Epic", "Feature"})
_SUMMARY_SKIP_LINES = {"why", "scope", "summary", "changes", "capabilities", "impact"}

_FINGERPRINT_QUERY = """
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    issues(first: 100, after: $after, states: [OPEN, CLOSED], orderBy: {field: CREATED_AT, direction: ASC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number
        title
        url
        updatedAt
        issueType { name }
        labels(first: 100) { nodes { name } }
        parent { number title url }
        subIssues(first: 100) { nodes { number title url } }
      }
    }
  }
}
"""

_DETAIL_QUERY = """
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    issues(first: 100, after: $after, states: [OPEN, CLOSED], orderBy: {field: CREATED_AT, direction: ASC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number
        title
        url
        updatedAt
        bodyText
        issueType { name }
        labels(first: 100) { nodes { name } }
        parent { number title url }
        subIssues(first: 100) { nodes { number title url } }
      }
    }
  }
}
"""


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
def _parse_issue_node(node: Mapping[str, Any], *, include_body: bool) -> HierarchyIssue | None:
    """Convert a GraphQL issue node to HierarchyIssue when supported."""
    issue_type_node = node.get("issueType")
    issue_type_name = issue_type_node.get("name") if isinstance(issue_type_node, Mapping) else None
    if issue_type_name not in SUPPORTED_ISSUE_TYPES:
        return None

    labels_container = node.get("labels") if isinstance(node.get("labels"), Mapping) else {}
    label_nodes = labels_container.get("nodes") if isinstance(labels_container, Mapping) else []
    labels = sorted(
        (str(item["name"]) for item in label_nodes if isinstance(item, Mapping) and item.get("name")),
        key=str.lower,
    )

    subissues_container = node.get("subIssues") if isinstance(node.get("subIssues"), Mapping) else {}
    subissue_nodes = subissues_container.get("nodes") if isinstance(subissues_container, Mapping) else []
    children = [
        IssueLink(number=int(item["number"]), title=str(item["title"]), url=str(item["url"]))
        for item in subissue_nodes
        if isinstance(item, Mapping) and item.get("number") is not None
    ]
    children.sort(key=lambda item: item.number)

    summary = _extract_summary(str(node.get("bodyText", ""))) if include_body else ""
    return HierarchyIssue(
        number=int(node["number"]),
        title=str(node["title"]),
        url=str(node["url"]),
        issue_type=str(issue_type_name),
        labels=labels,
        summary=summary,
        updated_at=str(node["updatedAt"]),
        parent=_parse_issue_link(node.get("parent") if isinstance(node.get("parent"), Mapping) else None),
        children=children,
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

    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "GitHub GraphQL query failed")

    payload = json.loads(completed.stdout)
    if "errors" in payload:
        raise RuntimeError(json.dumps(payload["errors"], indent=2))
    return payload


@beartype
def fetch_hierarchy_issues(*, repo_owner: str, repo_name: str, fingerprint_only: bool) -> list[HierarchyIssue]:
    """Fetch Epic and Feature issues from GitHub for the given repository."""
    query = _FINGERPRINT_QUERY if fingerprint_only else _DETAIL_QUERY
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


def render_cache_markdown(
    *,
    repo_full_name: str,
    issues: list[HierarchyIssue],
    generated_at: str,
    fingerprint: str,
) -> str:
    """Render deterministic markdown for the hierarchy cache."""
    grouped = {
        "Epic": sorted((item for item in issues if item.issue_type == "Epic"), key=lambda item: item.number),
        "Feature": sorted((item for item in issues if item.issue_type == "Feature"), key=lambda item: item.number),
    }

    lines = [
        "# GitHub Hierarchy Cache",
        "",
        f"- Repository: `{repo_full_name}`",
        f"- Generated At: `{generated_at}`",
        f"- Fingerprint: `{fingerprint}`",
        f"- Included Issue Types: `{', '.join(sorted(SUPPORTED_ISSUE_TYPES))}`",
        "",
        "Use this file as the first lookup source for parent Epic or Feature relationships during OpenSpec and GitHub issue setup.",
        "",
    ]

    for section_name, issue_type in (("Epics", "Epic"), ("Features", "Feature")):
        lines.append(f"## {section_name}")
        lines.append("")
        if not grouped[issue_type]:
            lines.append("_None_")
            lines.append("")
            continue

        for issue in grouped[issue_type]:
            lines.append(f"### #{issue.number} {issue.title}")
            lines.append(f"- URL: {issue.url}")
            parent_text = "none"
            if issue.parent is not None:
                parent_text = f"#{issue.parent.number} {issue.parent.title}"
            lines.append(f"- Parent: {parent_text}")

            if issue.children:
                child_text = ", ".join(f"#{child.number} {child.title}" for child in issue.children)
            else:
                child_text = "none"
            lines.append(f"- Children: {child_text}")

            label_text = ", ".join(sorted(issue.labels, key=str.lower)) if issue.labels else "none"
            lines.append(f"- Labels: {label_text}")
            lines.append(f"- Summary: {issue.summary or 'No summary provided.'}")
            lines.append("")

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
@require(lambda repo_owner: bool(repo_owner.strip()), "repo_owner must not be blank")
@require(lambda repo_name: bool(repo_name.strip()), "repo_name must not be blank")
def sync_cache(
    *,
    repo_owner: str,
    repo_name: str,
    output_path: Path,
    state_path: Path,
    force: bool = False,
) -> SyncResult:
    """Sync the local hierarchy cache from GitHub."""
    fingerprint_issues = fetch_hierarchy_issues(
        repo_owner=repo_owner,
        repo_name=repo_name,
        fingerprint_only=True,
    )
    fingerprint = compute_hierarchy_fingerprint(fingerprint_issues)
    state = _load_state(state_path)

    if not force and state.get("fingerprint") == fingerprint and output_path.exists():
        return SyncResult(
            changed=False,
            issue_count=len(fingerprint_issues),
            fingerprint=fingerprint,
            output_path=output_path,
        )

    detailed_issues = fetch_hierarchy_issues(
        repo_owner=repo_owner,
        repo_name=repo_name,
        fingerprint_only=False,
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
        print(
            f"Updated GitHub hierarchy cache with {result.issue_count} issues at {result.output_path}",
            file=sys.stdout,
        )
    else:
        print(
            f"GitHub hierarchy cache unchanged ({result.issue_count} issues).",
            file=sys.stdout,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
