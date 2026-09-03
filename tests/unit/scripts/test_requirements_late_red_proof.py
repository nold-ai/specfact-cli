"""Focused security regressions for the bounded PR #703 late-RED loader."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "scripts" / "requirements_late_red_proof.py"
PROVENANCE_PATH = "scripts/requirements_proof_provenance.py"


def _load_script_module(script_path: Path = SCRIPT_PATH) -> Any:
    specification = importlib.util.spec_from_file_location("requirements_late_red_proof_test", script_path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _git(repo_root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _create_provenance_history(tmp_path: Path) -> tuple[Path, str, bytes]:
    repo_root = tmp_path / "repo"
    provenance = repo_root / PROVENANCE_PATH
    provenance.parent.mkdir(parents=True)
    payload = (
        b"def bind_red_proof(*args, **kwargs):\n"
        b"    return None\n\n"
        b"def validate_prior_red_proof(*args, **kwargs):\n"
        b"    return []\n"
    )
    provenance.write_bytes(payload)
    _git(repo_root, "init")
    _git(repo_root, "config", "user.email", "requirements@example.test")
    _git(repo_root, "config", "user.name", "Requirements proof")
    _git(repo_root, "add", PROVENANCE_PATH)
    _git(repo_root, "commit", "-m", "test: add trusted provenance")
    return repo_root, _git(repo_root, "rev-parse", "HEAD"), payload


def _create_validator_checkout(tmp_path: Path) -> tuple[Any, Path]:
    validator_root = tmp_path / "validator"
    validator_script = validator_root / "scripts" / SCRIPT_PATH.name
    validator_provenance = validator_root / PROVENANCE_PATH
    validator_script.parent.mkdir(parents=True)
    shutil.copyfile(SCRIPT_PATH, validator_script)
    shutil.copyfile(REPO_ROOT / PROVENANCE_PATH, validator_provenance)
    _git(validator_root, "init")
    _git(validator_root, "config", "user.email", "requirements@example.test")
    _git(validator_root, "config", "user.name", "Requirements proof")
    _git(validator_root, "add", "scripts")
    _git(validator_root, "commit", "-m", "test: add validator checkout")
    return _load_script_module(validator_script), validator_provenance


def _write_json(path: Path, value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    path.write_bytes(payload)
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _junit_with_failed_selectors(selectors: list[str]) -> bytes:
    cases = "".join(
        f'<testcase><properties><property name="specfact.selector" value="{selector}"/></properties><failure/></testcase>'
        for selector in selectors
    )
    return f"<testsuite>{cases}</testsuite>".encode()


def _write_selector_artifact(
    artifact_root: Path,
    selectors: list[str],
    junit_payload: bytes,
    mapping_digest: str,
    plan_digest: str,
) -> tuple[str, str]:
    plan_report_digest = _write_json(
        artifact_root / "requirements-evidence-plan.json",
        {
            "gate_decision": "pass",
            "plan": {
                "cases": [{"node_id": selector, "runner": "pytest"} for selector in selectors],
                "mapping_digest": mapping_digest,
                "plan_digest": plan_digest,
            },
        },
    )
    report_digest = _write_json(
        artifact_root / "requirements-evidence.json",
        {
            "delivery_status": "incomplete",
            "gate_decision": "fail",
            "observed_maturity": "incomplete",
            "required_maturity": "verified",
            "verdict": "failed",
            "mapping_digest": mapping_digest,
            "plan_digest": plan_digest,
            "execution_proof": {
                "junit_digest": f"sha256:{hashlib.sha256(junit_payload).hexdigest()}",
                "run_stage": "final",
                "selectors": selectors,
                "source_ref": "c" * 40,
            },
        },
    )
    return plan_report_digest, report_digest


def test_provenance_loader_authenticates_cycle_base_bytes_before_execution(tmp_path: Path) -> None:
    """A same-named arbitrary module must not execute inside the proof validator."""
    module = _load_script_module()
    repo_root, cycle_commit, trusted_payload = _create_provenance_history(tmp_path)
    extracted = tmp_path / "trusted" / "requirements_proof_provenance.py"
    extracted.parent.mkdir()
    extracted.write_bytes(trusted_payload)

    bind, validate = module._load_provenance(extracted, repo_root, cycle_commit)
    assert callable(bind)
    assert callable(validate)

    marker = tmp_path / "untrusted-executed"
    untrusted = tmp_path / "untrusted" / "requirements_proof_provenance.py"
    untrusted.parent.mkdir()
    untrusted.write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).touch()\n"
        "def bind_red_proof(*args, **kwargs): return None\n"
        "def validate_prior_red_proof(*args, **kwargs): return []\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        module._load_provenance(untrusted, repo_root, cycle_commit)
    assert not marker.exists()


def test_provenance_loader_accepts_exact_committed_sibling_for_synthetic_fixture(tmp_path: Path) -> None:
    """A fixture history may omit the helper while the validator checkout pins it."""
    module, validator_provenance = _create_validator_checkout(tmp_path)
    fixture_root = tmp_path / "fixture"
    fixture_root.mkdir()
    (fixture_root / "README.md").write_text("# fixture\n", encoding="utf-8")
    _git(fixture_root, "init")
    _git(fixture_root, "config", "user.email", "requirements@example.test")
    _git(fixture_root, "config", "user.name", "Requirements proof")
    _git(fixture_root, "add", "README.md")
    _git(fixture_root, "commit", "-m", "test: add synthetic fixture")
    fixture_commit = _git(fixture_root, "rev-parse", "HEAD")

    bind, validate = module._load_provenance(validator_provenance, fixture_root, fixture_commit)
    assert callable(bind)
    assert callable(validate)


def test_failed_selector_identity_is_order_independent_but_exact(tmp_path: Path) -> None:
    """Authentic unique failures may appear in a different JUnit document order."""
    module = _load_script_module()
    artifact_root = tmp_path / "artifact"
    artifact_root.mkdir()
    first_selector = "tests/test_proof.py::test_first"
    second_selector = "tests/test_proof.py::test_second"
    selectors = [first_selector, second_selector]
    junit_payload = _junit_with_failed_selectors(selectors)
    (artifact_root / "requirements-proof.xml").write_bytes(junit_payload)
    mapping_digest = f"sha256:{'a' * 64}"
    plan_digest = f"sha256:{'b' * 64}"
    plan_report_digest, report_digest = _write_selector_artifact(
        artifact_root,
        selectors,
        junit_payload,
        mapping_digest,
        plan_digest,
    )
    manifest = {
        "report_digest": report_digest,
        "plan_report_digest": plan_report_digest,
        "junit_digest": f"sha256:{hashlib.sha256(junit_payload).hexdigest()}",
        "mapping_digest": mapping_digest,
        "plan_digest": plan_digest,
        "red_commit": "c" * 40,
        "failed_selectors": [second_selector, first_selector],
    }

    _, reported = module._validate_raw_artifact(artifact_root, manifest)
    assert reported == selectors

    manifest["failed_selectors"] = [first_selector, "tests/test_proof.py::test_other"]
    with pytest.raises(ValueError):
        module._validate_raw_artifact(artifact_root, manifest)
