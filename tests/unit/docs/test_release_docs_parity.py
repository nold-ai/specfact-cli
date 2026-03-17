from __future__ import annotations

from pathlib import Path


MODULES_DOCS_HOST = "modules.specfact.io"


def _repo_file(path: str) -> Path:
    return Path(__file__).resolve().parents[3] / path


def _assert_mentions_modules_docs_site(content: str) -> None:
    host_index = content.find(MODULES_DOCS_HOST)
    assert host_index != -1
    assert content[max(0, host_index - 8) : host_index] == "https://"
    assert content[host_index + len(MODULES_DOCS_HOST)] == "/"


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
    checklist = _repo_file("docs/getting-started/module-bootstrap-checklist.md").read_text(encoding="utf-8")
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
    assert "canonical docs entry point" in readme
    assert "module-specific deep docs are canonically owned by `specfact-cli-modules`" in readme
    _assert_mentions_modules_docs_site(readme)
    assert "Docs Home" in docs_index
    assert "Core CLI" in docs_index
    assert "Modules" in docs_index


def test_top_navigation_exposes_docs_home_core_cli_and_modules() -> None:
    layout = _repo_file("docs/_layouts/default.html").read_text(encoding="utf-8")
    assert ">Docs Home<" in layout
    assert ">Core CLI<" in layout
    assert ">Modules<" in layout
    _assert_mentions_modules_docs_site(layout)


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
    repo_root = Path(__file__).resolve().parents[3]
    sources: list[Path] = [repo_root / "README.md"]
    docs_dir = repo_root / "docs"
    for p in docs_dir.rglob("*.md"):
        if "_site" not in p.parts and "vendor" not in p.parts:
            sources.append(p)
    for src in sources:
        if not src.exists():
            continue
        for lineno, line in enumerate(src.read_text(encoding="utf-8").splitlines(), 1):
            if pattern not in line:
                continue
            stripped = line.strip()
            # Skip comment lines in code blocks
            if stripped.startswith("#"):
                continue
            # Skip blockquote lines (historical/migration notes)
            if stripped.startswith(">"):
                continue
            # Skip lines that explicitly label the pattern as removed
            lower = stripped.lower()
            if "removed" in lower or "(removed)" in lower or "is removed" in lower:
                continue
            hits.append((str(src.relative_to(repo_root)), lineno, stripped))
    return hits


def _fmt_hits(hits: list[tuple[str, int, str]]) -> str:
    return "\n".join(f"  {p}:{n}  {line}" for p, n, line in hits)


def test_removed_project_plan_syntax_absent_from_authored_docs() -> None:
    """specfact project plan is not a shipped command; must not appear as current syntax."""
    hits = _scan_authored_docs("specfact project plan")
    assert not hits, f"Removed syntax 'specfact project plan' still present:\n{_fmt_hits(hits)}"


def test_removed_project_import_from_bridge_syntax_absent_from_authored_docs() -> None:
    """project import from-bridge moved to code import from-bridge; old path must not appear."""
    hits = _scan_authored_docs("project import from-bridge")
    assert not hits, f"Removed syntax 'project import from-bridge' still present:\n{_fmt_hits(hits)}"


def test_removed_backlog_policy_syntax_absent_from_authored_docs() -> None:
    """backlog policy is not a shipped subcommand; must not appear as current syntax."""
    hits = _scan_authored_docs("backlog policy")
    assert not hits, f"Removed syntax 'backlog policy' still present:\n{_fmt_hits(hits)}"


def test_removed_spec_contract_syntax_absent_from_authored_docs() -> None:
    hits = _scan_authored_docs("spec contract")
    assert not hits, f"Removed syntax 'spec contract' still present:\n{_fmt_hits(hits)}"


def test_removed_spec_api_syntax_absent_from_authored_docs() -> None:
    # Search for "specfact spec api" to avoid false positives from --spec api/openapi.yaml paths
    hits = _scan_authored_docs("specfact spec api")
    assert not hits, f"Removed syntax 'specfact spec api' still present:\n{_fmt_hits(hits)}"


def test_removed_spec_sdd_syntax_absent_from_authored_docs() -> None:
    hits = _scan_authored_docs("spec sdd")
    assert not hits, f"Removed syntax 'spec sdd' still present:\n{_fmt_hits(hits)}"


def test_removed_spec_generate_syntax_absent_from_authored_docs() -> None:
    # "spec generate " (space) catches stale subcommands like fix-prompt, test-prompt,
    # contracts-prompt etc. without matching the valid "spec generate-tests" (hyphen).
    hits = _scan_authored_docs("spec generate ")
    assert not hits, f"Removed syntax 'spec generate <subcommand>' still present:\n{_fmt_hits(hits)}"


# ---------------------------------------------------------------------------
# docs-03-command-syntax-parity: current command families must be present
# ---------------------------------------------------------------------------


def test_current_code_import_from_bridge_documented() -> None:
    """Bridge import moved to code import from-bridge; at least one authored doc must show this."""
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
