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
        context = module.CycleBaseContext(base_ref, final_ref, "nold-ai/specfact-cli", 698, "review")

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
    final_ref = _commit(tmp_path, "review fix")
    paths = module.CycleBasePaths(Path(), Path(), Path(), tmp_path)
    context = module.CycleBaseContext(base_ref, final_ref, "nold-ai/specfact-cli", 698, "review")

    assert module._common_history_matches(paths, context, cycle_ref, red_ref)
    assert not module._history_matches(paths, context, cycle_ref, red_ref)

    source_path.write_text("VALUE = 2\n", encoding="utf-8")
    production_red = _commit(tmp_path, "production before red")
    production_context = module.CycleBaseContext(base_ref, production_red, "nold-ai/specfact-cli", 698, "review")
    assert not module._common_history_matches(paths, production_context, cycle_ref, production_red)
