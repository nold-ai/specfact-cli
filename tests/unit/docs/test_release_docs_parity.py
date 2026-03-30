from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import ParseResult, unquote, urlparse

import yaml


MODULES_DOCS_HOST = "modules.specfact.io"
DOCS_HOST = "docs.specfact.io"
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
HTML_HREF_RE = re.compile(r'href="([^"]+)"')
JEKYLL_RELATIVE_URL_RE = re.compile(r'\{\{\s*[\'"]([^\'"]+)[\'"]\s*\|\s*relative_url\s*\}\}')
REQUIRED_NAV_FRONT_MATTER_KEYS = ("layout", "title", "permalink")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _repo_file(path: str) -> Path:
    return _repo_root() / path


def _docs_root() -> Path:
    return _repo_root() / "docs"


def _assert_mentions_modules_docs_site(content: str) -> None:
    host_index = content.find(MODULES_DOCS_HOST)
    assert host_index != -1
    assert content[max(0, host_index - 8) : host_index] == "https://"
    assert content[host_index + len(MODULES_DOCS_HOST)] == "/"


def _is_docs_markdown(path: Path) -> bool:
    return path.suffix == ".md" and "_site" not in path.parts and "vendor" not in path.parts


def _iter_docs_markdown_paths() -> list[Path]:
    return sorted(path.resolve() for path in _docs_root().rglob("*.md") if _is_docs_markdown(path))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _split_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text

    lines = text.splitlines()
    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break
    if end_index is None:
        return {}, text

    metadata: dict[str, str] = {}
    for raw_line in lines[1:end_index]:
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")

    body = "\n".join(lines[end_index + 1 :])
    return metadata, body


def _normalize_route(route: str) -> str:
    cleaned = unquote(route.strip())
    if not cleaned:
        return "/"
    if not cleaned.startswith("/"):
        cleaned = "/" + cleaned
    cleaned = re.sub(r"/{2,}", "/", cleaned)
    if cleaned != "/" and not cleaned.endswith("/"):
        cleaned += "/"
    return cleaned


def _published_route_for_path(path: Path, metadata: dict[str, str]) -> str:
    permalink = metadata.get("permalink")
    if permalink:
        return _normalize_route(permalink)
    rel = path.relative_to(_docs_root())
    return _normalize_route("/" + str(rel.with_suffix("")).replace("\\", "/").lstrip("/"))


def _build_published_docs_index() -> tuple[dict[str, Path], dict[Path, dict[str, str]], dict[Path, str]]:
    route_to_path: dict[str, Path] = {}
    path_to_metadata: dict[Path, dict[str, str]] = {}
    path_to_route: dict[Path, str] = {}

    for path in _iter_docs_markdown_paths():
        metadata, _ = _split_front_matter(_read_text(path))
        route = _published_route_for_path(path, metadata)
        route_to_path[route] = path
        path_to_metadata[path] = metadata
        path_to_route[path] = route

    return route_to_path, path_to_metadata, path_to_route


def _docs_config() -> dict[str, object]:
    config_path = _repo_file("docs/_config.yml")
    return yaml.safe_load(_read_text(config_path)) or {}


def _extract_links(source: Path, content: str) -> list[str]:
    if source.suffix == ".html":
        return HTML_HREF_RE.findall(content)
    return MARKDOWN_LINK_RE.findall(content)


def _normalize_jekyll_relative_url(link: str) -> str:
    match = JEKYLL_RELATIVE_URL_RE.fullmatch(link.strip())
    if match:
        return match.group(1)
    return link


def _is_published_docs_route_candidate(route: str) -> bool:
    return route not in {"/assets/main.css/", "/feed.xml/"}


def _missing_route_failure(source: Path, route: str) -> tuple[str, None, str]:
    return route, None, f"{source.relative_to(_repo_root())} -> {route}"


def _resolve_site_token_link(source: Path, stripped: str) -> tuple[str | None, str | None]:
    if "{{" not in stripped or "site." not in stripped:
        return stripped, None

    match = re.search(r"\{\{\s*site\.([A-Za-z0-9_]+)(?:\s*\|.*?)*\s*\}\}", stripped)
    if not match:
        return None, f"{source.relative_to(_repo_root())} -> unresolved site token {stripped}"

    key = match.group(1)
    config = _docs_config()
    value = config.get(key)
    if not isinstance(value, str) or not value.strip():
        return None, f"{source.relative_to(_repo_root())} -> docs/_config.yml missing non-empty site.{key}"
    if key.endswith("_url") and not value.startswith("http"):
        return None, f"{source.relative_to(_repo_root())} -> docs/_config.yml site.{key} must start with http"

    suffix = stripped[match.end() :]
    return value.strip() + suffix, None


def _resolve_published_route(
    source: Path,
    route: str,
    route_to_path: dict[str, Path],
) -> tuple[str | None, Path | None, str | None]:
    if not _is_published_docs_route_candidate(route):
        return None, None, None

    target = route_to_path.get(route)
    if target is None:
        return _missing_route_failure(source, route)
    return route, target, None


def _resolve_http_docs_link(
    source: Path,
    parsed: ParseResult,
    route_to_path: dict[str, Path],
) -> tuple[str | None, Path | None, str | None]:
    if parsed.netloc != DOCS_HOST:
        return None, None, None
    return _resolve_published_route(source, _normalize_route(parsed.path or "/"), route_to_path)


def _resolve_absolute_docs_link(
    source: Path,
    target_value: str,
    route_to_path: dict[str, Path],
) -> tuple[str | None, Path | None, str | None]:
    return _resolve_published_route(source, _normalize_route(target_value), route_to_path)


def _resolve_existing_candidate(
    source: Path,
    target_value: str,
    candidate: Path,
    path_to_route: dict[Path, str],
) -> tuple[str | None, Path | None, str | None]:
    route = path_to_route.get(candidate)
    if route is None:
        return None, None, f"{source.relative_to(_repo_root())} -> {target_value}"
    return route, candidate, None


def _resolve_relative_docs_link(
    source: Path,
    target_value: str,
    route_to_path: dict[str, Path],
    path_to_route: dict[Path, str],
) -> tuple[str | None, Path | None, str | None]:
    candidate = (source.parent / target_value).resolve()

    if candidate.is_dir():
        readme_candidate = (candidate / "README.md").resolve()
        if readme_candidate.is_file() and _is_docs_markdown(readme_candidate):
            return _resolve_existing_candidate(source, target_value, readme_candidate, path_to_route)
        return None, None, None

    if candidate.is_file() and _is_docs_markdown(candidate):
        return _resolve_existing_candidate(source, target_value, candidate, path_to_route)

    if not candidate.suffix:
        markdown_candidate = candidate.with_suffix(".md")
        if markdown_candidate.is_file() and _is_docs_markdown(markdown_candidate):
            return _resolve_existing_candidate(source, target_value, markdown_candidate.resolve(), path_to_route)

    route = _normalize_route(target_value)
    if not _is_published_docs_route_candidate(route):
        return None, None, None

    target = route_to_path.get(route)
    if target is None:
        return route, None, f"{source.relative_to(_repo_root())} -> {target_value} (normalized: {route})"
    return route, target, None


def _resolve_internal_docs_target(
    source: Path,
    raw_link: str,
    route_to_path: dict[str, Path],
    path_to_route: dict[Path, str],
) -> tuple[str | None, Path | None, str | None]:
    stripped = _normalize_jekyll_relative_url(raw_link.strip())
    if not stripped or stripped.startswith("#"):
        return None, None, None

    stripped, site_token_failure = _resolve_site_token_link(source, stripped)
    if site_token_failure is not None or stripped is None:
        return None, None, site_token_failure

    parsed = urlparse(stripped)
    if parsed.scheme in {"mailto", "javascript", "tel"}:
        return None, None, None
    if parsed.scheme in {"http", "https"}:
        return _resolve_http_docs_link(source, parsed, route_to_path)
    if parsed.scheme:
        return None, None, None

    target_value = unquote(parsed.path)
    if not target_value:
        return None, None, None

    if target_value.startswith("/"):
        return _resolve_absolute_docs_link(source, target_value, route_to_path)

    return _resolve_relative_docs_link(source, target_value, route_to_path, path_to_route)


def _navigation_sources() -> list[Path]:
    return [
        _repo_file("docs/index.md").resolve(),
        _repo_file("docs/_layouts/default.html").resolve(),
    ]


def _scan_navigation_targets() -> tuple[list[str], set[Path]]:
    route_to_path, _, path_to_route = _build_published_docs_index()
    failures: list[str] = []
    targets: set[Path] = set()

    for source in _navigation_sources():
        for link in _extract_links(source, _read_text(source)):
            _, target, failure = _resolve_internal_docs_target(source, link, route_to_path, path_to_route)
            if failure:
                failures.append(failure)
            if target is not None:
                targets.add(target)

    return failures, targets


def _scan_authored_doc_link_failures() -> tuple[list[str], set[Path]]:
    route_to_path, _, path_to_route = _build_published_docs_index()
    failures: list[str] = []
    targets: set[Path] = set()

    for source in _iter_docs_markdown_paths():
        metadata, body = _split_front_matter(_read_text(source))
        if not metadata:
            continue
        for link in _extract_links(source, body):
            _, target, failure = _resolve_internal_docs_target(source, link, route_to_path, path_to_route)
            if failure:
                failures.append(failure)
            if target is not None:
                targets.add(target)

    return failures, targets


def test_changelog_has_single_0340_release_header() -> None:
    changelog = _repo_file("CHANGELOG.md").read_text(encoding="utf-8")
    assert changelog.count("## [0.34.0] - 2026-02-18") == 1


def test_patch_mode_is_not_left_under_unreleased() -> None:
    changelog = _repo_file("CHANGELOG.md").read_text(encoding="utf-8")
    unreleased_start = changelog.find("## [Unreleased]")
    next_release_start = changelog.find("\n## [", unreleased_start + 1)
    unreleased_block = changelog[unreleased_start:next_release_start]
    assert "Patch mode module" not in unreleased_block


def test_command_reference_documents_patch_apply() -> None:
    commands_doc = _repo_file("docs/reference/commands.md").read_text(encoding="utf-8")
    assert "specfact govern patch" in commands_doc


def test_module_bootstrap_checklist_uses_current_bundle_ids() -> None:
    checklist = _repo_file("docs/module-system/bootstrap-checklist.md").read_text(encoding="utf-8")
    assert "specfact module install backlog --source bundled" in checklist
    assert "backlog-core" not in checklist


def test_module_publishing_docs_describe_modules_repo_flow() -> None:
    publishing = _repo_file("docs/guides/publishing-modules.md").read_text(encoding="utf-8")
    assert "specfact-cli-modules" in publishing
    assert "Push to `dev` and `main`" in publishing
    assert "tags matching `*-v*`" not in publishing


def test_module_contracts_reference_external_bundle_boundary() -> None:
    contracts_doc = _repo_file("docs/reference/module-contracts.md").read_text(encoding="utf-8")
    assert "specfact-cli-modules" in contracts_doc
    assert "Core runtime must not import external bundle package namespaces" in contracts_doc


def test_readme_and_docs_index_define_core_and_modules_split() -> None:
    readme = _repo_file("README.md").read_text(encoding="utf-8")
    docs_index = _repo_file("docs/index.md").read_text(encoding="utf-8")
    assert "validation and alignment layer for software delivery" in readme
    assert "docs.specfact.io` is the canonical starting point for SpecFact" in readme
    assert "Module-specific deep docs are canonically owned by `specfact-cli-modules`" in readme
    _assert_mentions_modules_docs_site(readme)
    assert "canonical starting point for the core CLI story" in docs_index
    assert "docs.specfact.io` is the default starting point" in docs_index
    assert "modules.specfact.io" in docs_index


def test_top_navigation_exposes_docs_home_core_cli_and_modules() -> None:
    layout = _repo_file("docs/_layouts/default.html").read_text(encoding="utf-8")
    assert ">Docs Home<" in layout
    assert ">Core CLI<" in layout
    assert ">Modules<" in layout
    assert "{{ site.docs_home_url }}" in layout
    assert "{{ site.core_cli_docs_url }}" in layout
    assert "{{ site.modules_docs_url }}" in layout


def test_command_reference_and_docs_readme_link_to_modules_canonical_site() -> None:
    docs_readme = _repo_file("docs/README.md").read_text(encoding="utf-8")
    commands_doc = _repo_file("docs/reference/commands.md").read_text(encoding="utf-8")
    assert "canonical modules docs site" in docs_readme
    _assert_mentions_modules_docs_site(docs_readme)
    assert "canonical modules docs site" in commands_doc
    _assert_mentions_modules_docs_site(commands_doc)


def test_bundle_focused_pages_use_handoff_note_instead_of_future_migration_language() -> None:
    backlog_refinement = _repo_file("docs/guides/backlog-refinement.md").read_text(encoding="utf-8")
    github_adapter = _repo_file("docs/adapters/github.md").read_text(encoding="utf-8")
    assert "canonical modules docs site" in backlog_refinement
    assert "canonical modules docs site" in github_adapter
    assert "planned to migrate to `specfact-cli-modules`" not in backlog_refinement
    assert "planned to migrate to `specfact-cli-modules`" not in github_adapter


# ---------------------------------------------------------------------------
# docs-03-command-syntax-parity: removed syntax families must be absent
# ---------------------------------------------------------------------------


def _scan_authored_docs(pattern: str) -> list[tuple[str, int, str]]:
    """Return list of (relative_path, line_number, line_text) for pattern hits.

    Lines that are clearly labeled as historical/removed context are excluded:
    - Code-block comment lines (stripped line starts with ``#``)
    - Blockquote lines that reference a removed command (stripped starts with ``>``)
    - Any line where the pattern co-occurs with the word "removed" or "(removed)"
    """
    hits: list[tuple[str, int, str]] = []
    repo_root = _repo_root()
    for src in _authored_doc_sources(repo_root):
        if not src.exists():
            continue
        for lineno, line in enumerate(src.read_text(encoding="utf-8").splitlines(), 1):
            if pattern not in line:
                continue
            stripped = line.strip()
            if _skip_historical_pattern_hit(stripped):
                continue
            hits.append((str(src.relative_to(repo_root)), lineno, stripped))
    return hits


def _authored_doc_sources(repo_root: Path) -> list[Path]:
    sources: list[Path] = [repo_root / "README.md"]
    docs_dir = repo_root / "docs"
    sources.extend(path for path in docs_dir.rglob("*.md") if "_site" not in path.parts and "vendor" not in path.parts)
    return sources


def _skip_historical_pattern_hit(stripped: str) -> bool:
    if stripped.startswith("#") and not stripped.startswith(("# ", "## ", "### ", "#### ", "##### ", "###### ")):
        return True
    if stripped.startswith(">"):
        return True

    lower = stripped.lower()
    return "removed" in lower or "(removed)" in lower or "is removed" in lower


def _fmt_hits(hits: list[tuple[str, int, str]]) -> str:
    return "\n".join(f"  {path}:{lineno}  {line}" for path, lineno, line in hits)


def test_removed_project_plan_syntax_absent_from_authored_docs() -> None:
    hits = _scan_authored_docs("specfact project plan")
    assert not hits, f"Removed syntax 'specfact project plan' still present:\n{_fmt_hits(hits)}"


def test_removed_project_import_from_bridge_syntax_absent_from_authored_docs() -> None:
    hits = _scan_authored_docs("project import from-bridge")
    assert not hits, f"Removed syntax 'project import from-bridge' still present:\n{_fmt_hits(hits)}"


def test_removed_backlog_policy_syntax_absent_from_authored_docs() -> None:
    hits = _scan_authored_docs("backlog policy")
    assert not hits, f"Removed syntax 'backlog policy' still present:\n{_fmt_hits(hits)}"


def test_removed_spec_contract_syntax_absent_from_authored_docs() -> None:
    hits = _scan_authored_docs("spec contract")
    assert not hits, f"Removed syntax 'spec contract' still present:\n{_fmt_hits(hits)}"


def test_removed_spec_api_syntax_absent_from_authored_docs() -> None:
    hits = _scan_authored_docs("specfact spec api")
    assert not hits, f"Removed syntax 'specfact spec api' still present:\n{_fmt_hits(hits)}"


def test_removed_spec_sdd_syntax_absent_from_authored_docs() -> None:
    hits = _scan_authored_docs("spec sdd")
    assert not hits, f"Removed syntax 'spec sdd' still present:\n{_fmt_hits(hits)}"


def test_removed_spec_generate_syntax_absent_from_authored_docs() -> None:
    hits = _scan_authored_docs("spec generate ")
    assert not hits, f"Removed syntax 'spec generate <subcommand>' still present:\n{_fmt_hits(hits)}"


# ---------------------------------------------------------------------------
# docs-03-command-syntax-parity: current command families must be present
# ---------------------------------------------------------------------------


def test_current_code_import_from_bridge_documented() -> None:
    hits = _scan_authored_docs("code import")
    assert hits, "Current syntax 'code import' must appear in at least one authored doc"


def test_current_spec_commands_documented_in_commands_reference() -> None:
    commands_doc = _repo_file("docs/reference/commands.md").read_text(encoding="utf-8")
    for cmd in ("spec validate", "spec backward-compat", "spec generate-tests", "spec mock"):
        assert cmd in commands_doc, f"Current command '{cmd}' missing from docs/reference/commands.md"


def test_current_govern_enforce_sdd_documented() -> None:
    commands_doc = _repo_file("docs/reference/commands.md").read_text(encoding="utf-8")
    assert "govern enforce" in commands_doc, "'govern enforce' must appear in commands reference"


def test_current_backlog_subcommands_documented_in_commands_reference() -> None:
    commands_doc = _repo_file("docs/reference/commands.md").read_text(encoding="utf-8")
    for sub in ("backlog ceremony", "backlog refine", "backlog daily", "backlog sync"):
        assert sub in commands_doc, f"Current subcommand '{sub}' missing from commands reference"


def test_all_published_docs_markdown_files_have_jekyll_front_matter() -> None:
    missing: list[str] = []
    for path in _iter_docs_markdown_paths():
        first_line = _read_text(path).splitlines()[0] if _read_text(path) else ""
        if first_line != "---":
            missing.append(str(path.relative_to(_repo_root())))
    assert not missing, "Docs files missing front matter:\n" + "\n".join(missing)


# ---------------------------------------------------------------------------
# docs-04-docs-review-gate-and-link-integrity
# ---------------------------------------------------------------------------


def test_navigation_links_resolve_to_published_docs_routes() -> None:
    failures, _ = _scan_navigation_targets()
    assert not failures, "Broken navigation docs links:\n" + "\n".join(sorted(failures))


def test_authored_internal_docs_links_resolve_to_published_docs_targets() -> None:
    failures, _ = _scan_authored_doc_link_failures()
    assert not failures, "Broken authored docs links:\n" + "\n".join(sorted(failures))


def test_navigation_link_targets_have_required_front_matter_keys() -> None:
    _, targets = _scan_navigation_targets()
    _, path_to_metadata, _ = _build_published_docs_index()
    missing: list[str] = []

    for target in sorted(targets):
        metadata = path_to_metadata[target]
        missing_keys = [key for key in REQUIRED_NAV_FRONT_MATTER_KEYS if not metadata.get(key)]
        if missing_keys:
            missing.append(f"{target.relative_to(_repo_root())}: missing {', '.join(missing_keys)}")

    assert not missing, "Navigation-linked docs missing required front matter keys:\n" + "\n".join(missing)
