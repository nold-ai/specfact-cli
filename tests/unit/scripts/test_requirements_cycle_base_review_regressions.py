"""Review regressions for trusted Requirements amendment-cycle bases."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[3]
CYCLE_BASE_SCRIPT = REPO_ROOT / "scripts" / "requirements_cycle_base.py"


def _load_cycle_base_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("requirements_cycle_base_review", CYCLE_BASE_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _git(repo_root: Path, *arguments: str) -> str:
    result = subprocess.run(["git", *arguments], cwd=repo_root, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _commit(repo_root: Path, message: str) -> str:
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "--no-gpg-sign", "-m", message)
    return _git(repo_root, "rev-parse", "HEAD")


def test_cycle_base_rejects_self_authored_evidence_authority(tmp_path: Path) -> None:
    """A PR-authored workflow cannot bless its own successful artifact as trusted green."""
    authority_paths = (
        ".github/workflows/requirements-evidence.yml",
        "src/specfact_cli/commands/requirements.py",
        "pyproject.toml",
    )
    for index, authority_path in enumerate(authority_paths):
        module = _load_cycle_base_module()
        repository = tmp_path / f"repository-{index}"
        repository.mkdir()
        _git(repository, "init")
        _git(repository, "config", "user.email", "requirements@example.test")
        _git(repository, "config", "user.name", "Requirements proof")
        (repository / "README.md").write_text("# base\n", encoding="utf-8")
        base_ref = _commit(repository, "base")
        authority = repository / authority_path
        authority.parent.mkdir(parents=True, exist_ok=True)
        authority.write_text("forged evidence\n", encoding="utf-8")
        cycle_ref = _commit(repository, "self-authored green authority")
        tests = repository / "tests"
        tests.mkdir()
        (tests / "test_review.py").write_text("def test_review(): assert False\n", encoding="utf-8")
        final_ref = _commit(repository, "review red test")
        paths = module.CycleBasePaths(Path(), Path(), Path(), repository)
        context = module.CycleBaseContext(
            base_ref, final_ref, "nold-ai/specfact-cli", 698, "review", "fix-release-promotion-security-gates"
        )

        assert not module._history_matches(paths, context, cycle_ref, final_ref)


def test_external_authority_can_skip_only_the_self_authored_predicate(tmp_path: Path) -> None:
    """The shared history boundary retains ancestry, linearity, and test-only checks."""
    module = _load_cycle_base_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "README.md").write_text("# base\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "base")
    workflow = tmp_path / ".github" / "workflows" / "requirements-evidence.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("approved producer\n", encoding="utf-8")
    cycle_ref = _commit(tmp_path, "self-authored green authority")
    test_path = tmp_path / "tests" / "test_review.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_review(): assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "review red test")
    source_path = tmp_path / "src" / "delivery.py"
    source_path.parent.mkdir()
    source_path.write_text("VALUE = 1\n", encoding="utf-8")
    workflow.write_text("approved producer implementation\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "review fix")
    paths = module.CycleBasePaths(Path(), Path(), Path(), tmp_path)
    context = module.CycleBaseContext(
        base_ref, final_ref, "nold-ai/specfact-cli", 698, "review", "fix-release-promotion-security-gates"
    )

    assert module._common_history_matches(paths, context, cycle_ref, red_ref)
    assert not module._history_matches(paths, context, cycle_ref, red_ref)
    receipt = {
        "cycle_base": cycle_ref,
        "red_ref": red_ref,
        "cycle_base_commit": cycle_ref,
        "red_commit": red_ref,
        "cycle_base_tree": _git(tmp_path, "rev-parse", f"{cycle_ref}^{{tree}}"),
        "red_tree": _git(tmp_path, "rev-parse", f"{red_ref}^{{tree}}"),
    }
    assert not module._external_receipt_history_matches(paths, context, final_ref, receipt)

    source_path.write_text("VALUE = 2\n", encoding="utf-8")
    production_red = _commit(tmp_path, "production before red")
    production_context = module.CycleBaseContext(
        base_ref, production_red, "nold-ai/specfact-cli", 698, "review", "fix-release-promotion-security-gates"
    )
    assert not module._common_history_matches(paths, production_context, cycle_ref, production_red)


def test_red_history_uses_a_positive_test_and_change_artifact_allowlist(tmp_path: Path) -> None:
    """Unknown production roots cannot be smuggled into a nominally test-only red commit."""
    module = _load_cycle_base_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "README.md").write_text("# base\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "base")
    red_ref = base_ref

    for index, relative in enumerate(
        ("implementation.py", "lib/implementation.py", "modules/new/module.py", "docs/_ext/implementation.py")
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("VALUE = 1\n", encoding="utf-8")
        red_ref = _commit(tmp_path, f"unknown production root {index}")
        assert module._has_governed_cycle_change(tmp_path, base_ref, red_ref, "fix-release-promotion-security-gates")

    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_review.py").write_text("def test_review(): assert False\n", encoding="utf-8")
    test_ref = _commit(tmp_path, "test-only red")
    assert not module._has_governed_cycle_change(tmp_path, red_ref, test_ref, "fix-release-promotion-security-gates")

    rename_source = tmp_path / "lib" / "implementation.py"
    rename_target = tmp_path / "tests" / "implementation_fixture.py"
    rename_source.rename(rename_target)
    renamed_ref = _commit(tmp_path, "rename production into tests")
    assert module._has_governed_cycle_change(tmp_path, test_ref, renamed_ref, "fix-release-promotion-security-gates")


def test_red_history_rejects_production_changes_reverted_before_red(tmp_path: Path) -> None:
    """Every commit in the red segment must be test-only, not just its final tree delta."""
    module = _load_cycle_base_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    production = tmp_path / "src" / "delivery.py"
    production.parent.mkdir()
    production.write_text("VALUE = 1\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "base")

    production.write_text("VALUE = 2\n", encoding="utf-8")
    _commit(tmp_path, "production change")
    production.write_text("VALUE = 1\n", encoding="utf-8")
    _commit(tmp_path, "revert production change")
    test_path = tmp_path / "tests" / "test_review.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_review(): assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test-only final delta")

    assert module._has_governed_cycle_change(tmp_path, base_ref, red_ref, "fix-release-promotion-security-gates")
