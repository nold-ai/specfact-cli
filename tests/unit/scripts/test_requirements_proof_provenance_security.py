"""Security regressions for retained Requirements proof parsing."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from tests.unit.scripts.test_requirements_proof_provenance import (
    _commit,
    _git,
    _load_provenance_module,
    _write_unbound_red_proof,
)


def _red_source(repo_root: Path) -> tuple[str, str]:
    """Create a test-only red source with a committed selector."""
    _git(repo_root, "init")
    _git(repo_root, "config", "user.email", "requirements@example.test")
    _git(repo_root, "config", "user.name", "Requirements proof")
    (repo_root / "README.md").write_text("# proof\n", encoding="utf-8")
    base_ref = _commit(repo_root, "chore: base")
    test_path = repo_root / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    return base_ref, _commit(repo_root, "test: add red proof")


def test_retained_red_junit_rejects_entity_declarations(tmp_path: Path) -> None:
    """Runner artifacts must not expand attacker-controlled XML entities."""
    module = cast(Any, _load_provenance_module())
    selector = "tests/test_proof.py::test_selected"
    junit = (
        f'<!DOCTYPE proof [<!ENTITY selector "{selector}">]>'
        '<testsuite><testcase><properties><property name="specfact.selector" value="&selector;"/>'
        "</properties><failure/></testcase></testsuite>"
    ).encode()
    red_proof_path = tmp_path / "red.json"
    red_proof_path.with_suffix(".xml").write_bytes(junit)
    report: dict[str, object] = {
        "execution_proof": {
            "junit_digest": f"sha256:{hashlib.sha256(junit).hexdigest()}",
            "selectors": [selector],
            "source_ref": "a" * 40,
        }
    }

    with pytest.raises(ValueError, match="prior-red-proof-invalid"):
        module._validate_retained_red_junit(red_proof_path, report)


def test_retained_red_junit_rejects_oversized_file_before_read(tmp_path: Path) -> None:
    """The validator must bound hostile runner output before loading it into memory."""
    module = cast(Any, _load_provenance_module())
    red_proof_path = tmp_path / "red.json"
    report: dict[str, object] = {
        "execution_proof": {
            "junit_digest": f"sha256:{'a' * 64}",
            "selectors": ["tests/test_proof.py::test_selected"],
            "source_ref": "a" * 40,
        }
    }

    class OversizedJunit:
        def stat(self) -> Any:
            return type("Stat", (), {"st_size": module.MAX_JUNIT_BYTES + 1})()

        def read_bytes(self) -> bytes:
            raise AssertionError("oversized JUnit was read")

    with pytest.raises(ValueError, match="prior-red-proof-invalid"):
        module._validate_retained_red_junit(red_proof_path, report, junit_path=cast(Path, OversizedJunit()))


def test_bind_red_proof_uses_explicit_workflow_junit_path(tmp_path: Path) -> None:
    """The binder must consume the executor's real report and JUnit filenames."""
    module = cast(Any, _load_provenance_module())
    base_ref, red_ref = _red_source(tmp_path)
    artifact_dir = tmp_path / ".git" / "artifacts" / "requirements-evidence"
    artifact_dir.mkdir(parents=True)
    report_path = artifact_dir / "requirements-evidence.json"
    _write_unbound_red_proof(report_path, red_ref)
    junit_path = artifact_dir / "requirements-proof.xml"
    report_path.with_suffix(".xml").rename(junit_path)

    module.bind_red_proof(report_path, tmp_path, base_ref=base_ref, junit_path=junit_path)

    execution_proof = json.loads(report_path.read_text(encoding="utf-8"))["execution_proof"]
    assert execution_proof["source_ref"] == red_ref
    assert execution_proof["toolchain_identity"]["runner"] == "pytest"


def test_retained_red_proof_rejects_json_toolchain_tampering(tmp_path: Path) -> None:
    """Digest-bound JUnit identity must agree with the retained JSON binding."""
    module = cast(Any, _load_provenance_module())
    base_ref, red_ref = _red_source(tmp_path)
    report_path = tmp_path / ".git" / "red.json"
    _write_unbound_red_proof(report_path, red_ref)
    module.bind_red_proof(report_path, tmp_path, base_ref=base_ref)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["execution_proof"]["toolchain_identity"]["python"] = "attacker-controlled"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: deliver behavior")

    assert module.validate_prior_red_proof(report_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "prior-red-proof-invalid"
    ]
