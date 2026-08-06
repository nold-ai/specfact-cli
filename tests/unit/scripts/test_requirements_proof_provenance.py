"""Contract coverage for Git-bound Requirements red-proof provenance."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Protocol, cast


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
