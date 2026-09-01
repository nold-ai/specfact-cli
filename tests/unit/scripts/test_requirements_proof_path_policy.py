"""Focused regressions for retained Requirements proof path authority."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
PROVENANCE_SCRIPT = REPO_ROOT / "scripts" / "requirements_proof_provenance.py"
FROZEN_TRUST_ANCHORS = {
    "scripts/requirements_amendment_bootstrap.py",
    "scripts/requirements_bootstrap_authority.py",
    "scripts/requirements_cycle_base.py",
    "scripts/requirements_proof_provenance.py",
}


def _load_provenance_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("requirements_proof_path_policy", PROVENANCE_SCRIPT)
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


def _touchpoint(locator: str, *, kind: str = "source_file", mutable: object = True) -> dict[str, object]:
    return {
        "id": f"path-{locator}",
        "kind": kind,
        "locator": locator,
        "mutable_after_red": mutable,
    }


def _report(*touchpoints: dict[str, object]) -> dict[str, object]:
    mapping_digest = f"sha256:{'a' * 64}"
    plan_digest = f"sha256:{'b' * 64}"
    return {
        "gate_decision": "pass",
        "observed_maturity": "red",
        "mapping_digest": mapping_digest,
        "plan_digest": plan_digest,
        "plan": {
            "mapping_digest": mapping_digest,
            "plan_digest": plan_digest,
            "cases": [
                {
                    "requirement_id": "openspec:change:capability:requirement",
                    "case_id": "CASE-S01",
                    "touchpoints": list(touchpoints),
                }
            ],
        },
        "execution_proof": {
            "run_stage": "red",
            "source_ref": "a" * 40,
            "selectors": ["tests/unit/test_delivery.py::test_delivery"],
        },
    }


def _mutable_paths(module: ModuleType, report: dict[str, object]) -> set[str]:
    with patch.object(module, "_test_path_is_regular_at_ref", return_value=True):
        return module._mutable_sut_paths(
            report,
            Path(),
            "a" * 40,
            ["tests/unit/test_delivery.py"],
        )


def _freshness(module: ModuleType, report: dict[str, object], changed_paths: list[str]) -> list[str]:
    history = [[], changed_paths]
    with (
        patch.object(module, "_changed_paths_in_history", side_effect=history),
        patch.object(module, "_has_governed_production_path", return_value=False),
        patch.object(module, "_test_path_is_regular_at_ref", return_value=True),
    ):
        return module._validate_red_history_freshness(
            report,
            Path(),
            "base",
            "a" * 40,
            "b" * 40,
            "change",
        )


def test_exact_mutable_sut_path_is_allowed_after_red() -> None:
    """Only an exact owner-approved regular-file SUT locator is mutable."""
    module = _load_provenance_module()
    report = _report(_touchpoint("src/specfact_cli/delivery.py"))

    assert _mutable_paths(module, report) == {"src/specfact_cli/delivery.py"}
    assert _freshness(module, report, ["src/specfact_cli/delivery.py"]) == []


@pytest.mark.parametrize(
    "changed_paths",
    [
        ["src/specfact_cli/delivery.py", "src/specfact_cli/restored.py"],
        ["src/specfact_cli/delivery.py", "src/specfact_cli/renamed.py"],
        ["src/specfact_cli/delivery.py", "src/specfact_cli/copied.py"],
    ],
)
def test_complete_history_retains_restored_rename_and_copy_paths(changed_paths: list[str]) -> None:
    """Every path reported anywhere in the commit walk needs exact authority."""
    module = _load_provenance_module()
    report = _report(_touchpoint("src/specfact_cli/delivery.py"))

    assert _freshness(module, report, changed_paths) == ["stale-red-proof"]


@pytest.mark.parametrize(
    ("locator", "kind"),
    [
        ("tests/unit/test_delivery.py", "test_file"),
        ("tests/helpers/delivery.py", "source_file"),
        ("pyproject.toml", "config"),
        ("scripts/requirements_proof_executor.py", "source_file"),
        ("scripts/requirements_proof_pytest_plugin.py", "source_file"),
        ("uv.lock", "lockfile"),
        ("tests/__init__.py", "source_file"),
        *((anchor, "source_file") for anchor in sorted(FROZEN_TRUST_ANCHORS)),
    ],
)
def test_frozen_proof_inputs_cannot_be_authorized_as_mutable(locator: str, kind: str) -> None:
    """Mapping content cannot override an explicitly frozen proof class."""
    module = _load_provenance_module()
    assert module.NON_TRANSITIVE_PROOF_INPUTS == FROZEN_TRUST_ANCHORS

    with pytest.raises(ValueError, match="prior-red-proof-invalid"):
        _mutable_paths(module, _report(_touchpoint(locator, kind=kind)))


@pytest.mark.parametrize(
    "touchpoints",
    [
        (_touchpoint("src/**/*.py"),),
        (_touchpoint("src/specfact_cli/"),),
        (_touchpoint("./src/specfact_cli/delivery.py"),),
        (_touchpoint("src/specfact_cli/../delivery.py"),),
        (_touchpoint("/src/specfact_cli/delivery.py"),),
        (_touchpoint("src/specfact_cli/delivery.py", mutable="true"),),
        (_touchpoint("src/specfact_cli/delivery.py", kind="test_file"),),
        (
            _touchpoint("src/specfact_cli/delivery.py"),
            _touchpoint("src/specfact_cli/delivery.py"),
        ),
    ],
)
def test_ambiguous_mutable_sut_mapping_fails_closed(touchpoints: tuple[dict[str, object], ...]) -> None:
    """Over-broad, aliased, mistyped, or duplicate authority is invalid."""
    module = _load_provenance_module()

    with pytest.raises(ValueError, match="prior-red-proof-invalid"):
        _mutable_paths(module, _report(*touchpoints))


def test_unmapped_changed_path_remains_stale() -> None:
    """Every post-red path is denied unless the approved plan names it exactly."""
    module = _load_provenance_module()
    report = _report(_touchpoint("src/specfact_cli/delivery.py", mutable=False))

    assert _freshness(module, report, ["src/specfact_cli/delivery.py"]) == ["stale-red-proof"]


@pytest.mark.parametrize(
    ("selector", "locator"),
    [
        ("tests/unit/test_delivery.py", "conftest.py"),
        ("tests/unit/test_delivery.py", "tests/conftest.py"),
        ("test_delivery.py", "conftest.py"),
    ],
)
def test_applicable_conftests_cannot_be_authorized_as_mutable(selector: str, locator: str) -> None:
    """Pytest ancestor hooks remain frozen even when mislabeled as SUT source."""
    module = _load_provenance_module()
    with (
        patch.object(module, "_test_path_is_regular_at_ref", return_value=True),
        pytest.raises(ValueError, match="prior-red-proof-invalid"),
    ):
        module._mutable_sut_paths(_report(_touchpoint(locator)), Path(), "a" * 40, [selector])


def test_copy_from_unchanged_frozen_source_is_retained(tmp_path: Path) -> None:
    """Complete history reports the unchanged source of a copied test blob."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    test_path = tmp_path / "tests" / "test_selected.py"
    mutable_path = tmp_path / "src" / "delivery.py"
    test_path.parent.mkdir()
    mutable_path.parent.mkdir()
    test_path.write_text("VALUE = 'frozen'\n", encoding="utf-8")
    mutable_path.write_text("VALUE = 'mutable'\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "red source")
    mutable_path.unlink()
    _commit(tmp_path, "delete mutable destination")
    mutable_path.write_bytes(test_path.read_bytes())
    final_ref = _commit(tmp_path, "copy frozen bytes to mutable destination")

    changed = module._changed_paths_in_history(tmp_path, red_ref, final_ref, merge_parent=1)

    assert changed is not None
    assert "tests/test_selected.py" in changed
    assert "src/delivery.py" in changed


def test_missing_or_non_regular_mutable_path_fails_closed() -> None:
    """Owner intent cannot authorize a path absent from the authenticated red tree."""
    module = _load_provenance_module()
    with (
        patch.object(module, "_test_path_is_regular_at_ref", return_value=False),
        pytest.raises(ValueError, match="prior-red-proof-invalid"),
    ):
        module._mutable_sut_paths(
            _report(_touchpoint("src/specfact_cli/delivery.py")),
            Path(),
            "a" * 40,
            ["tests/unit/test_delivery.py"],
        )
