"""Import-gate tests for cross-bundle private imports (module-migration-02 phase 0)."""

from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def _collect_import_targets(py_file: Path) -> set[str]:
    source = py_file.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(py_file))
    targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                targets.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            targets.add(node.module)
    return targets


def test_analyze_module_has_no_cross_bundle_import_to_plan_module() -> None:
    """analyze (codebase) must not import project module internals."""
    imports = _collect_import_targets(REPO_ROOT / "src/specfact_cli/modules/analyze/src/commands.py")
    assert not any(target.startswith("specfact_cli.modules.plan") for target in imports)


def test_generate_plan_access_uses_common_or_intra_bundle_only() -> None:
    """generate (spec bundle) must not access project plan via core private paths."""
    imports = _collect_import_targets(REPO_ROOT / "src/specfact_cli/modules/generate/src/commands.py")
    banned_prefixes = ("specfact_cli.modules.plan", "specfact_cli.models.plan")
    assert not any(target.startswith(banned_prefixes) for target in imports)


def test_enforce_plan_access_uses_common_or_intra_bundle_only() -> None:
    """enforce (govern bundle) must not access project plan via core private paths."""
    imports = _collect_import_targets(REPO_ROOT / "src/specfact_cli/modules/enforce/src/commands.py")
    banned_prefixes = ("specfact_cli.modules.plan", "specfact_cli.models.plan")
    assert not any(target.startswith(banned_prefixes) for target in imports)
