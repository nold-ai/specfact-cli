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
    "tests/e2e/*",
    "tests/integration/*",
    # Obsolete flat-plan command topology assertions retired from core.
    "tests/unit/commands/test_plan_add_commands.py",
    "tests/unit/commands/test_plan_telemetry.py",
    "tests/unit/commands/test_plan_update_commands.py",
    # Backlog command behavior is module-owned after extraction.
    "tests/unit/commands/test_backlog_commands.py",
    "tests/unit/commands/test_backlog_daily.py",
    "tests/unit/commands/test_project_cmd.py",
    # Legacy topology and extracted-module path assumptions retired from core.
    "tests/unit/groups/test_codebase_group.py",
    "tests/unit/modules/init/test_first_run_selection.py",
    "tests/unit/modules/test_reexport_shims.py",
    "tests/unit/prompts/test_prompt_validation.py",
    "tests/unit/registry/test_category_groups.py",
    "tests/unit/registry/test_core_only_bootstrap.py",
    "tests/unit/registry/test_cross_bundle_imports.py",
    "tests/unit/specfact_cli/test_module_migration_compatibility.py",
    "tests/unit/test_core_module_isolation.py",
    "tests/unit/utils/test_suggestions.py",
)


def pytest_ignore_collect(collection_path: object, config: object) -> bool:
    """Skip module-owned suites in core repo unless explicitly re-enabled."""
    if os.environ.get("SPECFACT_INCLUDE_MIGRATED_TESTS") == "1":
        return False
    path = Path(str(collection_path)).resolve()
    try:
        rel = path.relative_to(project_root).as_posix()
    except ValueError:
        return False
    return any(fnmatch(rel, pattern) for pattern in _MIGRATED_TEST_PATTERNS)
