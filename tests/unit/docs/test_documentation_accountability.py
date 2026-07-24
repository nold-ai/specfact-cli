"""Regression coverage for the fail-closed module documentation contract."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import sys
from functools import lru_cache
from pathlib import Path
from typing import Protocol, cast

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]


class OfficialModuleRecord(Protocol):
    """Read surface used by the checker regression tests."""

    command_roots: tuple[str, ...]


class AccountabilityChecker(Protocol):
    """Typed public surface loaded from the standalone checker script."""

    CATALOGUE_PATHS: tuple[str, ...]
    OWNERSHIP_PATHS: tuple[str, ...]

    def discover_official_modules(self, modules_root: Path) -> dict[str, OfficialModuleRecord]:
        raise NotImplementedError

    def validate_documentation_accountability(self, core_root: Path, modules_root: Path) -> list[str]:
        raise NotImplementedError

    def _resolve_modules_root(self, raw_path: str | None) -> Path:
        raise NotImplementedError


def _modules_root() -> Path | None:
    configured = os.environ.get("SPECFACT_MODULES_REPO", "").strip()
    candidates = [Path(configured).expanduser()] if configured else []
    candidates.append(REPO_ROOT.parent / "specfact-cli-modules")
    if "specfact-cli-worktrees" in REPO_ROOT.parts:
        marker = REPO_ROOT.parts.index("specfact-cli-worktrees")
        candidates.append(Path(*REPO_ROOT.parts[:marker]) / "specfact-cli-modules")
        suffix = Path(*REPO_ROOT.parts[marker + 1 :])
        candidates.append(Path(*REPO_ROOT.parts[:marker]) / "specfact-cli-modules-worktrees" / suffix)
    return next((candidate for candidate in candidates if (candidate / "packages").is_dir()), None)


def test_modules_root_is_optional_without_a_paired_checkout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Plain core checkouts skip external-fixture tests instead of raising StopIteration."""
    monkeypatch.delenv("SPECFACT_MODULES_REPO", raising=False)
    monkeypatch.setattr(sys.modules[__name__], "REPO_ROOT", tmp_path)

    assert _modules_root() is None


@pytest.fixture(scope="module")
def modules_root() -> Path:
    """Require the external modules fixture only for tests that exercise it."""
    resolved = _modules_root()
    if resolved is None:
        pytest.skip("specfact-cli-modules checkout is required for accountability contract tests")
    return resolved


@lru_cache(maxsize=1)
def _load_accountability_checker() -> AccountabilityChecker:
    path = REPO_ROOT / "scripts" / "check-documentation-accountability.py"
    spec = importlib.util.spec_from_file_location("check_documentation_accountability", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast(AccountabilityChecker, module)


def _copy_accountability_inputs(tmp_path: Path, checker: AccountabilityChecker) -> Path:
    """Create a core-document fixture that starts from the checked-in contract."""
    for relative_path in (*checker.CATALOGUE_PATHS, *checker.OWNERSHIP_PATHS, "docs/reference/commands.generated.json"):
        source = REPO_ROOT / relative_path
        target = tmp_path / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return tmp_path


def test_accountability_uses_modules_source_for_official_requirements(modules_root: Path) -> None:
    checker = _load_accountability_checker()

    inventory = checker.discover_official_modules(modules_root)

    assert inventory["nold-ai/specfact-requirements"].command_roots == ("requirements",)


def test_accountability_contract_accepts_current_catalogues(modules_root: Path) -> None:
    checker = _load_accountability_checker()

    findings = checker.validate_documentation_accountability(REPO_ROOT, modules_root)

    assert findings == []


def test_accountability_contract_reports_an_omitted_official_catalogue_package(
    tmp_path: Path, modules_root: Path
) -> None:
    checker = _load_accountability_checker()
    core_root = _copy_accountability_inputs(tmp_path, checker)
    readme = core_root / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace("specfact-requirements", "removed-module"), encoding="utf-8"
    )

    findings = checker.validate_documentation_accountability(core_root, modules_root)

    assert "README.md: missing official package nold-ai/specfact-requirements" in findings


def test_accountability_contract_reports_an_incomplete_generated_command_inventory(
    tmp_path: Path, modules_root: Path
) -> None:
    checker = _load_accountability_checker()
    core_root = _copy_accountability_inputs(tmp_path, checker)
    generated_path = core_root / "docs/reference/commands.generated.json"
    records = json.loads(generated_path.read_text(encoding="utf-8"))
    generated_path.write_text(
        json.dumps(
            [record for record in records if record.get("owner_package") != "nold-ai/specfact-requirements"],
            indent=2,
        ),
        encoding="utf-8",
    )

    findings = checker.validate_documentation_accountability(core_root, modules_root)

    assert (
        "docs/reference/commands.generated.json: missing nold-ai/specfact-requirements command root requirements"
        in findings
    )


def test_accountability_contract_reports_an_official_command_ownership_conflict(
    tmp_path: Path, modules_root: Path
) -> None:
    checker = _load_accountability_checker()
    core_root = _copy_accountability_inputs(tmp_path, checker)
    overview = core_root / "docs/architecture/overview.md"
    overview.write_text(
        f"{overview.read_text(encoding='utf-8')}\n\nspecfact code ... is not canonical\n",
        encoding="utf-8",
    )

    findings = checker.validate_documentation_accountability(core_root, modules_root)

    assert (
        "docs/architecture/overview.md: incorrectly rejects installed nold-ai/specfact-code-review command ownership"
        in findings
    )


def test_accountability_contract_detects_qualified_ownership_rejection(tmp_path: Path, modules_root: Path) -> None:
    """Ownership rejections remain invalid when they include trailing qualifiers."""
    checker = _load_accountability_checker()
    core_root = _copy_accountability_inputs(tmp_path, checker)
    overview = core_root / "docs/architecture/overview.md"
    overview.write_text(
        f"{overview.read_text(encoding='utf-8')}\n\nspecfact code is not canonical delivery targets\n",
        encoding="utf-8",
    )

    findings = checker.validate_documentation_accountability(core_root, modules_root)

    assert (
        "docs/architecture/overview.md: incorrectly rejects installed nold-ai/specfact-code-review command ownership"
        in findings
    )


def test_accountability_contract_rejects_an_unavailable_modules_source(tmp_path: Path) -> None:
    checker = _load_accountability_checker()

    with pytest.raises(ValueError, match="must contain packages"):
        checker.discover_official_modules(tmp_path)


def test_explicit_invalid_modules_root_does_not_fall_back(tmp_path: Path, modules_root: Path) -> None:
    """An explicit bad override must not silently use a different checkout."""
    checker = _load_accountability_checker()

    with pytest.raises(ValueError, match=re.escape(f"--modules-repo is not a valid modules checkout: {tmp_path}")):
        checker._resolve_modules_root(str(tmp_path))

    assert checker._resolve_modules_root(str(modules_root)) == modules_root.resolve()


def test_accountability_gate_is_mandatory_locally_and_in_pr_ci() -> None:
    pre_commit = (REPO_ROOT / "scripts" / "pre-commit-quality-checks.sh").read_text(encoding="utf-8")
    docs_workflow = yaml.safe_load(
        (REPO_ROOT / ".github" / "workflows" / "docs-review.yml").read_text(encoding="utf-8")
    )

    gate_function = re.search(
        r"run_command_overview_validation_gate\(\) \{(?P<body>.*?)^\}",
        pre_commit,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert gate_function is not None
    assert "if hatch run check-documentation-accountability; then" in gate_function.group("body")
    assert "check-documentation-accountability ||" not in gate_function.group("body")

    steps = docs_workflow["jobs"]["docs-review"]["steps"]
    accountability_step = next(step for step in steps if step.get("name") == "Validate documentation accountability")
    assert accountability_step["run"] == "python scripts/check-documentation-accountability.py"
    frozen_setup_index = next(
        index for index, step in enumerate(steps) if step.get("uses") == "./.github/actions/setup-frozen-python"
    )
    accountability_index = steps.index(accountability_step)
    assert frozen_setup_index < accountability_index
    assert accountability_step.get("continue-on-error", False) is False
