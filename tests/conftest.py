"""Pytest configuration for tools tests."""

import os
import sys
import tempfile
from fnmatch import fnmatch
from pathlib import Path


# Use the repo that contains this conftest (worktree when tests run from worktree).
# __file__ is always the conftest in the repo we're testing; avoid cwd so we're not affected by run dir.
project_root = Path(__file__).resolve().parent.parent
if not (project_root / "src" / "specfact_cli").exists():
    _invoke_dir = Path.cwd().resolve()
    if (_invoke_dir / "src" / "specfact_cli").exists():
        project_root = _invoke_dir

# Force module discovery to use this repo so we run worktree code, not site-packages.
os.environ["SPECFACT_REPO_ROOT"] = str(project_root.resolve())

# Add project root and src to path so specfact_cli and tests use repo code (not only site-packages).
# Insert project_root first, then src_root, so src_root ends up at index 0 and specfact_cli loads from worktree.
src_root = project_root / "src"
for path in (project_root, src_root):
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))


def _resolve_modules_repo_root() -> Path:
    configured = os.environ.get("SPECFACT_MODULES_REPO")
    if configured:
        return Path(configured).expanduser().resolve()
    for candidate_base in (project_root, *project_root.parents):
        sibling_repo = candidate_base / "specfact-cli-modules"
        if sibling_repo.exists():
            return sibling_repo
        sibling_repo = candidate_base.parent / "specfact-cli-modules"
        if sibling_repo.exists():
            return sibling_repo
    return project_root / "specfact-cli-modules"


# Add bundle package src roots for module-migration-02 test runs.
bundle_packages_root = _resolve_modules_repo_root() / "packages"
if bundle_packages_root.exists():
    for bundle_src in bundle_packages_root.glob("*/src"):
        bundle_src_str = str(bundle_src)
        if bundle_src_str not in sys.path:
            sys.path.insert(0, bundle_src_str)

# Set TEST_MODE globally for all tests to avoid interactive prompts
os.environ["TEST_MODE"] = "true"
# Allow loading bundled modules without signature in tests
os.environ.setdefault("SPECFACT_ALLOW_UNSIGNED", "1")
# Point policy init at repo resources so template resolution works in tests/CI.
policy_templates = project_root / "resources" / "templates" / "policies"
if policy_templates.exists():
    os.environ["SPECFACT_POLICY_TEMPLATES_DIR"] = str(policy_templates.resolve())
else:
    _cwd_templates = Path.cwd().resolve() / "resources" / "templates" / "policies"
    if _cwd_templates.exists():
        os.environ["SPECFACT_POLICY_TEMPLATES_DIR"] = str(_cwd_templates)

# Isolate registry state for test runs to avoid coupling with ~/.specfact/registry.
# This prevents local module enable/disable settings from affecting command discovery in tests.
os.environ.setdefault("SPECFACT_REGISTRY_DIR", tempfile.mkdtemp(prefix="specfact-test-registry-"))


_MIGRATED_TEST_PATTERNS: tuple[str, ...] = (
    # Module-owned E2E/integration suites moved under specfact-cli-modules.
    "tests/e2e/backlog/*",
    "tests/e2e/test_auth_flow_e2e.py",
    "tests/e2e/test_brownfield_speckit_compliance.py",
    "tests/e2e/test_bundle_extraction_e2e.py",
    "tests/e2e/test_complete_workflow.py",
    "tests/e2e/test_constitution_commands.py",
    "tests/e2e/test_directory_structure_workflow.py",
    "tests/e2e/test_enforcement_workflow.py",
    "tests/e2e/test_enrichment_workflow.py",
    "tests/e2e/test_natural_ux_flow_e2e.py",
    "tests/e2e/test_phase1_features_e2e.py",
    "tests/e2e/test_phase2_contracts_e2e.py",
    "tests/e2e/test_plan_review_batch_updates.py",
    "tests/e2e/test_plan_review_non_interactive.py",
    "tests/e2e/test_openspec_bridge_workflow.py",
    "tests/e2e/test_quick_start_performance_e2e.py",
    "tests/e2e/test_semgrep_integration_e2e.py",
    "tests/e2e/test_specmatic_integration_e2e.py",
    "tests/e2e/test_telemetry_e2e.py",
    "tests/e2e/test_validate_sidecar_workflow.py",
    "tests/e2e/test_watch_mode_e2e.py",
    "tests/integration/backlog/*",
    "tests/integration/commands/*",
    "tests/integration/importers/*",
    "tests/integration/sync/*",
    "tests/integration/analyzers/test_analyze_command.py",
    "tests/integration/test_specmatic_integration.py",
    # Obsolete flat-plan command topology assertions retired from core.
    "tests/unit/commands/test_plan_add_commands.py",
    "tests/unit/commands/test_plan_telemetry.py",
    "tests/unit/commands/test_plan_update_commands.py",
    # Backlog command behavior is module-owned after extraction.
    "tests/unit/commands/test_backlog_commands.py",
    "tests/unit/commands/test_backlog_daily.py",
    "tests/unit/commands/test_project_cmd.py",
    # Legacy topology and extracted-module path assumptions retired from core.
    "tests/unit/specfact_cli/test_module_migration_compatibility.py",
)


def _should_skip_migrated_test(rel_path: str) -> bool:
    return any(fnmatch(rel_path, pattern) for pattern in _MIGRATED_TEST_PATTERNS)


def pytest_ignore_collect(collection_path: object, config: object) -> bool:
    """Skip module-owned suites in core repo unless explicitly re-enabled."""
    if os.environ.get("SPECFACT_INCLUDE_MIGRATED_TESTS") == "1":
        return False
    path = Path(str(collection_path)).resolve()
    try:
        rel = path.relative_to(project_root).as_posix()
    except ValueError:
        return False
    return _should_skip_migrated_test(rel)


def pytest_collection_modifyitems(config: object, items: list[object]) -> None:
    """Skip migrated suites even when runners select them explicitly by path."""
    if os.environ.get("SPECFACT_INCLUDE_MIGRATED_TESTS") == "1":
        return
    import pytest

    skip_marker = pytest.mark.skip(reason="Module-owned suite moved to specfact-cli-modules")
    for item in items:
        item_path = Path(str(getattr(item, "fspath", ""))).resolve()
        try:
            rel = item_path.relative_to(project_root).as_posix()
        except ValueError:
            continue
        if _should_skip_migrated_test(rel):
            item.add_marker(skip_marker)


# Pytest 8+ / 9+: ``pytest_plugins`` is only allowed in the rootdir conftest (not in nested
# packages). Doc frontmatter fixtures live in ``tests.helpers.doc_frontmatter_fixtures``.
pytest_plugins = ("tests.helpers.doc_frontmatter_fixtures",)
