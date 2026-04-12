#!/usr/bin/env python3
"""Validate YAML doc ownership frontmatter for Markdown documentation."""

from __future__ import annotations

import datetime
import fnmatch
import functools
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import typer
import yaml
from beartype import beartype
from icontract import ensure, require
from pydantic import BaseModel, ConfigDict, Field, ValidationError, ValidationInfo, field_validator, model_validator
from rich.console import Console
from typer.main import get_command

from specfact_cli.common import get_bridge_logger


_ERR = Console(stderr=True)
_LOG = get_bridge_logger(__name__)

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
DOC_OWNER_RE = re.compile(r"^\s*doc_owner\s*:\s*['\"]?(.+?)['\"]?\s*$", re.MULTILINE)
LAST_REVIEWED_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

TRACKED_DOC_DIRS = ("docs",)
REQUIRED_ROOT_DOCS: tuple[str, ...] = ("USAGE-FAQ.md",)
AGENT_RULES_DIR = "docs/agent-rules/"
EXEMPT_FILES = frozenset(
    {
        "docs/LICENSE.md",
        "docs/TRADEMARKS.md",
        "CHANGELOG.md",
        "CLA.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        "TRADEMARKS.md",
    }
)
VALID_OWNER_TOKENS = frozenset({"specfact-cli", "nold-ai", "openspec"})
SOURCE_ROOTS = (Path("src"), Path("openspec"), Path("modules"), Path("tools"))

_OWNER_GLOB_METACHARS = frozenset("*?[]{}")
REQUIRED_KEYS = ("title", "doc_owner", "tracks", "last_reviewed", "exempt", "exempt_reason")
AGENT_RULE_REQUIRED_KEYS = (
    *REQUIRED_KEYS,
    "id",
    "always_load",
    "applies_when",
    "priority",
    "blocking",
    "user_interaction_required",
    "stop_conditions",
    "depends_on",
)
RULE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class DocFrontmatter(BaseModel):
    """Validated doc-sync ownership record (YAML frontmatter subset)."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=False)

    title: str = Field(..., description="Document title")
    doc_owner: str = Field(..., description="Owner path or known token")
    tracks: list[str] = Field(..., min_length=1, description="Glob patterns for tracked sources")
    last_reviewed: datetime.date = Field(..., description="Last review date (YYYY-MM-DD)")
    exempt: bool = Field(..., description="Whether the page is exempt from sync rules")
    exempt_reason: str = Field(..., description="Reason when exempt; empty string when not exempt")

    @field_validator("tracks", mode="before")
    @classmethod
    def _tracks_must_be_string_list(cls, value: object) -> list[str]:
        if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
            raise ValueError("`tracks` must be a list of strings")
        return list(value)

    @field_validator("last_reviewed", mode="before")
    @classmethod
    def _normalize_last_reviewed_field(cls, value: object) -> datetime.date:
        if isinstance(value, datetime.datetime):
            return value.date()
        if isinstance(value, datetime.date):
            return value
        if isinstance(value, str):
            s = value.strip()
            if LAST_REVIEWED_RE.match(s):
                y, m, d = (int(x) for x in s.split("-"))
                return datetime.date(y, m, d)
        raise ValueError("`last_reviewed` must be YYYY-MM-DD")

    @field_validator("exempt", mode="before")
    @classmethod
    def _exempt_must_be_bool(cls, value: object) -> bool:
        if not isinstance(value, bool):
            raise ValueError("`exempt` must be a boolean")
        return value

    @field_validator("doc_owner", "title", "exempt_reason", mode="before")
    @classmethod
    def _required_strings(cls, value: object, info: ValidationInfo) -> str:
        if not isinstance(value, str):
            raise ValueError(f"`{info.field_name}` must be a string")
        return value

    @model_validator(mode="after")
    def _tracks_globs_valid(self) -> DocFrontmatter:
        if not validate_glob_patterns(list(self.tracks)):
            raise ValueError("invalid glob pattern in `tracks`")
        return self

    @model_validator(mode="after")
    def _owner_and_exempt_rules(self) -> DocFrontmatter:
        if not resolve_owner(self.doc_owner):
            raise ValueError(
                "doc_owner `"
                + self.doc_owner
                + "` does not resolve (tokens: "
                + ", ".join(sorted(VALID_OWNER_TOKENS))
                + " or repo path)",
            )
        if self.exempt and not self.exempt_reason.strip():
            raise ValueError("`exempt_reason` required when exempt is true")
        return self


DocFrontmatter.model_rebuild(_types_namespace={"datetime": datetime})


class AgentRuleFrontmatter(DocFrontmatter):
    """Validated frontmatter for deterministic governance rule documents."""

    id: str = Field(..., description="Stable rule identifier")
    always_load: bool = Field(..., description="Whether the rule must load for every applicable bootstrap")
    applies_when: list[str] = Field(..., min_length=1, description="Task signals that require this rule")
    priority: int = Field(..., ge=0, description="Deterministic loading order")
    blocking: bool = Field(..., description="Whether the rule can block progress")
    user_interaction_required: bool = Field(..., description="Whether the rule requires user clarification")
    stop_conditions: list[str] = Field(..., min_length=1, description="Blocking conditions for the rule")
    depends_on: list[str] = Field(..., description="Other rule ids that must load first")

    @field_validator("id", mode="before")
    @classmethod
    def _normalize_rule_id(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("`id` must be a string")
        rule_id = value.strip()
        if not RULE_ID_RE.match(rule_id):
            raise ValueError("`id` must be kebab-case")
        return rule_id

    @field_validator("applies_when", "stop_conditions", "depends_on", mode="before")
    @classmethod
    def _string_list_fields(cls, value: object, info: ValidationInfo) -> list[str]:
        if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
            raise ValueError(f"`{info.field_name}` must be a list of strings")
        string_values = cast(list[str], value)
        normalized = [x.strip() for x in string_values]
        if info.field_name != "depends_on" and any(not x for x in normalized):
            raise ValueError(f"`{info.field_name}` entries must be non-empty")
        if info.field_name == "depends_on":
            return [x for x in normalized if x]
        return normalized

    @model_validator(mode="after")
    def _always_load_requires_bootstrap_signal(self) -> AgentRuleFrontmatter:
        if self.always_load and not {"session-bootstrap", "implementation", "all"} & set(self.applies_when):
            raise ValueError("always-load rules must apply to bootstrap, implementation, or all tasks")
        return self


AgentRuleFrontmatter.model_rebuild(_types_namespace={"datetime": datetime})


def _format_doc_frontmatter_errors(exc: ValidationError) -> list[str]:
    """Turn Pydantic errors into the same style as legacy manual validation."""
    out: list[str] = []
    for err in exc.errors():
        loc = err.get("loc") or ()
        key = str(loc[0]) if loc else "record"
        typ = err.get("type", "")
        if typ == "missing":
            out.append(f"missing `{key}`")
            continue
        msg = str(err.get("msg", "validation error"))
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, ") :]
        out.append(msg)
    return out


def _root() -> Path:
    """Repository root for validation (override with DOC_FRONTMATTER_ROOT in tests)."""
    env = os.environ.get("DOC_FRONTMATTER_ROOT")
    return Path(env).resolve() if env else Path(__file__).resolve().parents[1]


def _enforced_path() -> Path:
    return _root() / "docs" / ".doc-frontmatter-enforced"


def _rel_posix(path: Path) -> str:
    try:
        return path.resolve().relative_to(_root().resolve()).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _agent_rules_path_slug(rel_under_rules: str) -> str:
    """Build URL-style slug from path under ``docs/agent-rules/`` (matches existing rule ids)."""
    tail = rel_under_rules[:-3] if rel_under_rules.endswith(".md") else rel_under_rules
    parts = tail.split("/")
    cleaned = [re.sub(r"^\d+-", "", segment) for segment in parts]
    return "-".join(cleaned).lower().replace("_", "-")


def _agent_rules_canonical_id(rel_under_rules: str) -> str:
    return f"agent-rules-{_agent_rules_path_slug(rel_under_rules)}"


def _agent_rules_default_permalink(slug: str) -> str:
    if slug == "index":
        return "/contributing/agent-rules/"
    return f"/contributing/agent-rules/{slug}/"


def _path_is_existing_file(path: Path) -> bool:
    return path.is_file()


@beartype
@require(_path_is_existing_file, "Path must be an existing file")
@ensure(lambda result: isinstance(result, dict), "Must return dict")
def parse_frontmatter(path: Path) -> dict[str, Any]:
    """Parse YAML frontmatter from a Markdown file."""
    content = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}
    loaded = yaml.safe_load(match.group(1))
    return loaded if isinstance(loaded, dict) else {}


@beartype
@require(lambda content: isinstance(content, str), "Content must be string")
@ensure(lambda result: result is None or isinstance(result, str), "Must return string or None")
def extract_doc_owner(content: str) -> str | None:
    """Extract doc_owner value from raw Markdown content."""
    match = DOC_OWNER_RE.search(content)
    return match.group(1).strip() if match else None


def _owner_literal_is_safe(owner: str) -> bool:
    """Reject empty owners, traversal segments, and glob metacharacters."""
    if not isinstance(owner, str):
        return False
    s = owner.strip()
    if not s:
        return False
    if any(ch in _OWNER_GLOB_METACHARS for ch in s):
        return False
    parts = Path(s).as_posix().split("/")
    return all(part not in ("", ".", "..") for part in parts)


def _is_resolved_under(child: Path, root: Path) -> bool:
    """True if ``child`` resolves to a path under ``root`` (same device)."""
    try:
        child.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _resolve_owner_absolute_path(owner: str, base_root: Path) -> bool:
    """Return True if ``owner`` is an absolute path inside ``base_root`` that exists."""
    candidate = Path(owner)
    if not candidate.is_absolute():
        return False
    try:
        resolved = candidate.resolve()
    except OSError:
        return False
    if not _is_resolved_under(resolved, base_root):
        return False
    return resolved.exists()


def _resolve_owner_repo_relative(owner: str, base_root: Path) -> bool:
    """Return True if ``base_root/owner`` resolves under ``base_root`` and exists."""
    rel = (base_root / owner).resolve()
    if not _is_resolved_under(rel, base_root):
        return False
    return rel.exists()


def _glob_owner_dir_under_root(owner: str, root: Path) -> bool:
    """Return True if a directory named ``owner`` exists anywhere under ``root`` (single-segment owners)."""
    try:
        for match in root.glob(f"**/{owner}"):
            if match.is_dir():
                return True
    except OSError:
        return False
    return False


def _find_owner_under_source_roots(owner: str, base_root: Path, owner_single_segment: bool) -> bool:
    """Search ``SOURCE_ROOTS`` for a path or directory name matching ``owner``."""
    for rel_root in SOURCE_ROOTS:
        root = (base_root / rel_root).resolve()
        if not root.exists():
            continue
        joined = (root / owner).resolve()
        if _is_resolved_under(joined, root) and joined.exists():
            return True
        if owner_single_segment and _glob_owner_dir_under_root(owner, root):
            return True
    return False


@beartype
@require(lambda owner: isinstance(owner, str), "Owner must be string")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def resolve_owner(owner: str) -> bool:
    """Return True if owner is a known token or an existing path under the repo."""
    return _resolve_owner_impl(owner, str(_root().resolve()))


@functools.lru_cache(maxsize=256)
def _resolve_owner_impl(owner: str, root_key: str) -> bool:
    """Memoized owner resolution keyed by owner and repository root (see ``resolve_owner``)."""
    if owner in VALID_OWNER_TOKENS:
        return True
    if not _owner_literal_is_safe(owner):
        return False
    base_root = Path(root_key).resolve()
    candidate = Path(owner)
    if candidate.is_absolute():
        return _resolve_owner_absolute_path(owner, base_root)
    if _resolve_owner_repo_relative(owner, base_root):
        return True
    owner_single_segment = "/" not in owner.strip().rstrip("/")
    return _find_owner_under_source_roots(owner, base_root, owner_single_segment)


_PLAIN_YAML_SCALAR = re.compile(r"^[A-Za-z0-9_.\-/]+$")


@beartype
def _yaml_plain_or_quoted_scalar(value: str) -> str:
    """Format a string as a YAML scalar (plain when unambiguous, else double-quoted)."""
    if _PLAIN_YAML_SCALAR.fullmatch(value) and not value.startswith(("-", ":", "?", "[")):
        return value
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


@beartype
def _yaml_flow_inline(value: object) -> str:
    """Serialize a Python value as an inline (flow-style) YAML fragment."""
    return yaml.dump(value, default_flow_style=True, allow_unicode=True, width=1000).strip()


@beartype
@require(lambda patterns: isinstance(patterns, list), "Patterns must be list")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def validate_glob_patterns(patterns: list[str]) -> bool:
    """Return True if patterns are non-empty, balanced for `[]`/`{}`, and compile as fnmatch regex.

    Full glob semantics follow Python :func:`fnmatch.fnmatch`; this adds bracket/brace balance
    checks and a best-effort :func:`fnmatch.translate` + :func:`re.compile` pass for invalid
    metacharacter sequences. See ``docs/contributing/frontmatter-schema.md``.
    """
    if not patterns:
        return False
    for pattern in patterns:
        p = str(pattern).strip()
        if not p:
            return False
        if p.count("[") != p.count("]"):
            return False
        if p.count("{") != p.count("}"):
            return False
        try:
            re.compile(fnmatch.translate(p))
        except re.error:
            return False
    return True


@dataclass
class _AgentRuleFrontmatterDraft:
    layout_val: str = "default"
    permalink_val: str = ""
    description_val: str | None = None
    keywords_val: list[str] | None = None
    audience_val: list[str] | None = None
    expertise_val: list[str] | None = None


def _parse_str_field(existing: dict[str, Any], key: str, current: str) -> str:
    val = existing.get(key)
    if isinstance(val, str) and val.strip():
        return val.strip()
    return current


def _parse_optional_str_field(existing: dict[str, Any], key: str) -> str | None:
    val = existing.get(key)
    if isinstance(val, str) and val.strip():
        return val.strip()
    return None


def _parse_str_list_field(existing: dict[str, Any], key: str) -> list[str] | None:
    val = existing.get(key)
    if isinstance(val, list) and all(isinstance(x, str) for x in val):
        return list(val)
    return None


def _load_existing_agent_rule_frontmatter_overrides(path: Path, default_permalink: str) -> _AgentRuleFrontmatterDraft:
    draft = _AgentRuleFrontmatterDraft(permalink_val=default_permalink)
    if not path.is_file():
        return draft
    try:
        existing = parse_frontmatter(path)
    except OSError:
        return draft
    draft.layout_val = _parse_str_field(existing, "layout", draft.layout_val)
    draft.permalink_val = _parse_str_field(existing, "permalink", draft.permalink_val)
    draft.description_val = _parse_optional_str_field(existing, "description")
    draft.keywords_val = _parse_str_list_field(existing, "keywords")
    draft.audience_val = _parse_str_list_field(existing, "audience")
    draft.expertise_val = _parse_str_list_field(existing, "expertise_level")
    return draft


def _agent_rule_optional_frontmatter_lines(draft: _AgentRuleFrontmatterDraft) -> str:
    parts: list[str] = []
    if draft.description_val is not None:
        parts.append(f"description: {_yaml_flow_inline(draft.description_val)}\n")
    if draft.keywords_val is not None:
        parts.append(f"keywords: {_yaml_flow_inline(draft.keywords_val)}\n")
    if draft.audience_val is not None:
        parts.append(f"audience: {_yaml_flow_inline(draft.audience_val)}\n")
    if draft.expertise_val is not None:
        parts.append(f"expertise_level: {_yaml_flow_inline(draft.expertise_val)}\n")
    return "".join(parts)


@beartype
@require(lambda path: isinstance(path, Path), "Path must be Path object")
@ensure(lambda result: isinstance(result, str), "Must return string")
def _format_agent_rules_suggested_frontmatter(path: Path, canonical_id: str, draft: _AgentRuleFrontmatterDraft) -> str:
    title_guess = path.stem.replace("-", " ").title().replace('"', '\\"')
    optional_lines = _agent_rule_optional_frontmatter_lines(draft)
    return f"""---
layout: {_yaml_plain_or_quoted_scalar(draft.layout_val)}
title: "{title_guess}"
permalink: {_yaml_plain_or_quoted_scalar(draft.permalink_val)}
{optional_lines}id: {canonical_id}
doc_owner: specfact-cli
tracks:
  - AGENTS.md
  - docs/agent-rules/**
last_reviewed: {datetime.date.today().isoformat()}
exempt: false
exempt_reason: ""
always_load: false
applies_when:
  - detailed-reference
priority: 50
blocking: false
user_interaction_required: false
stop_conditions:
  - none
depends_on: []
---
"""


@beartype
@require(lambda path: isinstance(path, Path), "Path must be Path object")
@ensure(lambda result: isinstance(result, str), "Must return string")
def suggest_frontmatter(path: Path) -> str:
    """Return a suggested frontmatter block for a document."""
    rel = _rel_posix(path)
    if rel.startswith(AGENT_RULES_DIR):
        rel_under = rel[len(AGENT_RULES_DIR) :]
        rule_slug = _agent_rules_path_slug(rel_under)
        canonical_id = _agent_rules_canonical_id(rel_under)
        default_permalink = _agent_rules_default_permalink(rule_slug)
        draft = _load_existing_agent_rule_frontmatter_overrides(path, default_permalink)
        return _format_agent_rules_suggested_frontmatter(path, canonical_id, draft)
    return f"""---
title: "{path.stem}"
doc_owner: specfact-cli
tracks:
  - src/specfact_cli/**
  - openspec/**
last_reviewed: {datetime.date.today().isoformat()}
exempt: false
exempt_reason: ""
---
"""


def _load_enforced_patterns() -> list[str] | None:
    """Return path patterns from docs/.doc-frontmatter-enforced, or None if file missing."""
    path = _enforced_path()
    if not path.exists():
        return None
    lines: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def _matches_enforced(rel: str, patterns: list[str]) -> bool:
    return any(rel == p or fnmatch.fnmatch(rel, p) for p in patterns)


@beartype
@ensure(lambda result: isinstance(result, list), "Must return list")
def get_all_md_files() -> list[Path]:
    """Discover Markdown files that are candidates for validation."""
    root = _root()
    files: list[Path] = []
    for doc_dir in TRACKED_DOC_DIRS:
        target = root / doc_dir
        if target.exists():
            files.extend(target.rglob("*.md"))
    for name in REQUIRED_ROOT_DOCS:
        p = root / name
        if p.exists():
            files.append(p)

    filtered: list[Path] = []
    for file_path in files:
        rel = _rel_posix(file_path)
        if rel in EXEMPT_FILES:
            continue
        try:
            fm = parse_frontmatter(file_path)
        except (OSError, yaml.YAMLError) as exc:
            _LOG.debug("parse_frontmatter failed for %s during discovery: %r", file_path, exc, exc_info=exc)
            filtered.append(file_path)
            continue
        exempt_val = fm.get("exempt")
        if exempt_val is True and str(fm.get("exempt_reason", "")).strip():
            continue
        filtered.append(file_path)
    return filtered


def _missing_owner_by_scan(files: list[Path]) -> list[Path]:
    out: list[Path] = []
    for file_path in files:
        try:
            content = file_path.read_text(encoding="utf-8")
            if not DOC_OWNER_RE.search(content):
                out.append(file_path)
        except OSError:
            out.append(file_path)
    return out


def _missing_owner_via_rg(files: list[Path]) -> list[Path] | None:
    """Return missing list, or None to fall back to line-by-line scan."""
    file_args = [str(f) for f in files]
    try:
        result = subprocess.run(
            ["rg", "--files-without-match", r"^\s*doc_owner\s*:", *file_args],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return None
    # rg: 0 = listed files exist, 1 = no listings (e.g. all files match pattern), 2+ = error
    if result.returncode >= 2:
        return None
    if result.returncode == 1:
        return []
    missing: list[Path] = []
    for line in result.stdout.strip().splitlines():
        if line.strip():
            missing.append(Path(line))
    return missing


@beartype
@require(lambda files: isinstance(files, list), "Files must be list")
@ensure(lambda result: isinstance(result, list), "Must return list")
def rg_missing_doc_owner(files: list[Path]) -> list[Path]:
    """Return paths whose raw content lacks a doc_owner field."""
    if not files:
        return []
    try:
        via_rg = _missing_owner_via_rg(files)
        if via_rg is not None:
            return via_rg
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        _ERR.print(
            f"doc-frontmatter: rg-based doc_owner scan failed ({exc!r}); falling back to per-file scan.",
        )
    return _missing_owner_by_scan(files)


def _validate_record(fm: dict[str, Any]) -> list[str]:
    """Return human-readable errors for a frontmatter dict (non-exempt docs)."""
    missing = [f"missing `{key}`" for key in REQUIRED_KEYS if key not in fm]
    if missing:
        return missing
    try:
        DocFrontmatter.model_validate(fm)
    except ValidationError as exc:
        return _format_doc_frontmatter_errors(exc)
    return []


def _is_agent_rule_doc(path: Path) -> bool:
    return _rel_posix(path).startswith(AGENT_RULES_DIR)


def _validate_record_for_path(path: Path, fm: dict[str, Any]) -> list[str]:
    required_keys = AGENT_RULE_REQUIRED_KEYS if _is_agent_rule_doc(path) else REQUIRED_KEYS
    missing = [f"missing `{key}`" for key in required_keys if key not in fm]
    if missing:
        return missing
    model = AgentRuleFrontmatter if _is_agent_rule_doc(path) else DocFrontmatter
    try:
        model.model_validate(fm)
    except ValidationError as exc:
        return _format_doc_frontmatter_errors(exc)
    return []


def _discover_paths_to_check(all_docs: bool) -> list[Path] | None:
    """Return files to validate, or None when the run should exit 0 early (skip)."""
    if all_docs:
        return get_all_md_files()
    enforced = _load_enforced_patterns()
    if enforced is None:
        _ERR.print(
            "doc-frontmatter: docs/.doc-frontmatter-enforced not found — skipping "
            "(use --all-docs to validate every doc).",
        )
        return None
    if len(enforced) == 0:
        _ERR.print("doc-frontmatter: enforced list is empty — nothing to check.")
        return None
    return [f for f in get_all_md_files() if _matches_enforced(_rel_posix(f), enforced)]


def _collect_failures(
    all_files: list[Path],
    files_without_owner: list[Path],
    fix_hint: bool,
) -> list[str]:
    failures: list[str] = []
    for file_path in all_files:
        rel = _rel_posix(file_path)
        if file_path in files_without_owner:
            if fix_hint:
                failures.append(
                    f"  ✗ MISSING doc_owner:  {rel}\n\n    Suggested frontmatter:\n{suggest_frontmatter(file_path)}"
                )
            else:
                failures.append(f"  ✗ MISSING doc_owner:  {rel}")
            continue
        try:
            fm = parse_frontmatter(file_path)
        except (OSError, yaml.YAMLError) as exc:
            failures.append(f"  ✗ YAML parse error: {rel}: {exc}")
            continue
        errs = _validate_record_for_path(file_path, fm)
        if errs:
            msg = f"  ✗ INVALID frontmatter:  {rel}\n    - " + "\n    - ".join(errs)
            if fix_hint:
                msg += f"\n\n    Suggested frontmatter:\n{suggest_frontmatter(file_path)}"
            failures.append(msg)
    return failures


def _argv_ok(argv: list[str] | None) -> bool:
    return argv is None or all(isinstance(x, str) for x in argv)


def _run_validation(fix_hint: bool, all_docs: bool) -> int:
    all_files = _discover_paths_to_check(all_docs)
    if all_files is None:
        return 0
    if not all_files:
        _ERR.print("✅ No documentation paths matched — nothing to check.")
        return 0

    files_without_owner = rg_missing_doc_owner(all_files)
    failures = _collect_failures(all_files, files_without_owner, fix_hint)

    if failures:
        _ERR.print(f"\n❌ Doc frontmatter validation failed ({len(failures)} issue(s)):\n")
        for block in failures:
            _ERR.print(block)
        if not fix_hint:
            _ERR.print("\n💡 Tip: run with --fix-hint for suggested frontmatter blocks.")
        return 1

    scope = "all docs" if all_docs else "enforced list"
    _ERR.print(f"✅ Doc frontmatter OK — {len(all_files)} doc(s) checked (scope: {scope}).")
    return 0


app = typer.Typer(
    add_completion=False,
    no_args_is_help=False,
    help="Validate documentation ownership frontmatter for Markdown files.",
)


@app.callback(invoke_without_command=True)
def _cli_root(
    fix_hint: bool = typer.Option(
        False,
        "--fix-hint",
        help="Print suggested YAML blocks for common failures.",
    ),
    all_docs: bool = typer.Option(
        False,
        "--all-docs",
        help="Validate every discovered Markdown file (ignore docs/.doc-frontmatter-enforced).",
    ),
) -> None:
    """Validate doc frontmatter and terminate with the validator exit code."""
    raise typer.Exit(code=_run_validation(fix_hint, all_docs))


@beartype
@require(_argv_ok, "argv must be None or a list of strings")
@ensure(lambda result: result in (0, 1), "exit code must be 0 or 1")
def main(argv: list[str] | None = None) -> int:
    """CLI entry: validate doc frontmatter; exit 0 on success, 1 on failure."""
    args = list(sys.argv[1:]) if argv is None else list(argv)
    cli = get_command(app)
    try:
        exit_code = cli.main(args=args, prog_name="doc-frontmatter-check", standalone_mode=False)
    except SystemExit as exc:
        code = exc.code
        if isinstance(code, int):
            return code
        return 1
    if exit_code is None:
        return 0
    return int(exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
