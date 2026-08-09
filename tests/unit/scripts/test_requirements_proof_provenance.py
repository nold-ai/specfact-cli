"""Contract coverage for Git-bound Requirements red-proof provenance."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Protocol, cast

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
PROVENANCE_SCRIPT = REPO_ROOT / "scripts" / "requirements_proof_provenance.py"


class ProvenanceModule(Protocol):
    """Minimal public surface for validating a committed red-proof report."""

    def validate_prior_red_proof(
        self, red_proof_path: Path, repo_root: Path, *, base_ref: str, final_ref: str
    ) -> list[str]: ...


def _load_provenance_module() -> ProvenanceModule:
    spec = importlib.util.spec_from_file_location("requirements_proof_provenance", PROVENANCE_SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("Requirements proof provenance validator must be importable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast(ProvenanceModule, module)


def _git(repo_root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _commit(repo_root: Path, message: str) -> str:
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "--no-gpg-sign", "-m", message)
    return _git(repo_root, "rev-parse", "HEAD")


def _red_proof(source_ref: str) -> dict[str, object]:
    return {
        "gate_decision": "pass",
        "observed_maturity": "red",
        "mapping_digest": f"sha256:{'a' * 64}",
        "plan_digest": f"sha256:{'b' * 64}",
        "execution_proof": {
            "run_stage": "red",
            "source_ref": source_ref,
            "selectors": ["tests/test_proof.py::test_selected"],
            "junit_digest": f"sha256:{'c' * 64}",
        },
    }


def test_git_bound_red_proof_requires_test_only_ancestor_and_unchanged_selector_files(tmp_path: Path) -> None:
    """Only an ancestor red report with unchanged selected tests may reach reconciliation."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "README.md").write_text("# proof\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "chore: base")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / "red.json"
    red_proof_path.write_text(json.dumps(_red_proof(red_ref)), encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []

    test_path.write_text("def test_selected() -> None: assert True\n", encoding="utf-8")
    stale_ref = _commit(tmp_path, "test: change selector")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=stale_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_rejects_replayed_or_renamed_production_history(tmp_path: Path) -> None:
    """Red evidence must follow the current base and retain governed rename sources."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 0\n", encoding="utf-8")
    _commit(tmp_path, "chore: base")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / "red.json"
    red_proof_path.write_text(json.dumps(_red_proof(red_ref)), encoding="utf-8")
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    current_base_ref = _commit(tmp_path, "fix: apply delivery")
    (tmp_path / "src" / "other.py").write_text("VALUE = 2\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: unrelated delivery")

    assert module.validate_prior_red_proof(
        red_proof_path, tmp_path, base_ref=current_base_ref, final_ref=final_ref
    ) == ["tdd-order-unproven"]

    rename_root = tmp_path / "rename"
    rename_root.mkdir()
    _git(rename_root, "init")
    _git(rename_root, "config", "user.email", "requirements@example.test")
    _git(rename_root, "config", "user.name", "Requirements proof")
    (rename_root / "src").mkdir()
    (rename_root / "src" / "delivery.py").write_text("VALUE = 0\n", encoding="utf-8")
    rename_base_ref = _commit(rename_root, "chore: base")
    (rename_root / "docs").mkdir()
    _git(rename_root, "mv", "src/delivery.py", "docs/delivery.py")
    _commit(rename_root, "docs: relocate delivery notes")
    rename_test_path = rename_root / "tests" / "test_proof.py"
    rename_test_path.parent.mkdir()
    rename_test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    rename_red_ref = _commit(rename_root, "test: add red proof")
    rename_proof_path = rename_root / "red.json"
    rename_proof_path.write_text(json.dumps(_red_proof(rename_red_ref)), encoding="utf-8")
    (rename_root / "src").mkdir(exist_ok=True)
    (rename_root / "src" / "replacement.py").write_text("VALUE = 1\n", encoding="utf-8")
    rename_final_ref = _commit(rename_root, "feat: replace delivery")

    assert module.validate_prior_red_proof(
        rename_proof_path, rename_root, base_ref=rename_base_ref, final_ref=rename_final_ref
    ) == ["tdd-order-unproven"]


def test_git_bound_red_proof_rejects_governed_path_with_tab(tmp_path: Path) -> None:
    """A control character in a governed Git path must not hide its prefix."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "README.md").write_text("# proof\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "chore: base")
    unusual_path = tmp_path / "src" / "a\tb.py"
    unusual_path.parent.mkdir()
    unusual_path.write_text("VALUE = 1\n", encoding="utf-8")
    _commit(tmp_path, "feat: add governed path with tab")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / "red.json"
    red_proof_path.write_text(json.dumps(_red_proof(red_ref)), encoding="utf-8")
    (tmp_path / "docs.md").write_text("# final\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "docs: retain final source")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "tdd-order-unproven"
    ]


@pytest.mark.parametrize(
    "delivery_path",
    [
        "pyproject.toml",
        "resources/templates/proof.j2",
        "resources/schemas/proof.json",
        "resources/mappings/proof.yaml",
        "resources/keys/proof.pub",
        "modules/bundle-mapper/module-package.yaml",
    ],
)
def test_git_bound_red_proof_rejects_delivery_input_before_red(tmp_path: Path, delivery_path: str) -> None:
    """Frozen dependency input changes are production work, even at repository root."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "README.md").write_text("# proof\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "chore: base")
    packaged_path = tmp_path / delivery_path
    packaged_path.parent.mkdir(parents=True, exist_ok=True)
    packaged_path.write_text("packaged proof\n", encoding="utf-8")
    _commit(tmp_path, "build: change delivery input")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / "red.json"
    red_proof_path.write_text(json.dumps(_red_proof(red_ref)), encoding="utf-8")
    (tmp_path / "docs.md").write_text("# final\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "docs: retain final source")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "tdd-order-unproven"
    ]
