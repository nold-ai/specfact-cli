"""Documentation jobs authenticate signed source before exposing module imports."""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import yaml
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


REPO_ROOT = Path(__file__).resolve().parents[3]
BUNDLES = ("backlog", "codebase", "code-review", "govern", "project", "requirements", "spec")
JOBS = [("docs-review.yml", "docs-review"), ("pr-orchestrator.yml", "cli-validation")]


def _canonical_verifier() -> ModuleType:
    path = REPO_ROOT / "scripts/verify-modules-signature.py"
    spec = importlib.util.spec_from_file_location("docs_test_canonical_verifier", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_public_key(root: Path, key: Ed25519PrivateKey) -> None:
    destination = root / "resources/keys/module-signing-public.pem"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(
        key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    )


def _signed_sources(root: Path) -> tuple[Path, Path]:
    modules = root / "specfact-cli-modules"
    trusted = root / "trusted-core-docs"
    (trusted / "scripts").mkdir(parents=True)
    shutil.copyfile(REPO_ROOT / "scripts/verify-modules-signature.py", trusted / "scripts/verify-modules-signature.py")
    key = Ed25519PrivateKey.generate()
    _write_public_key(trusted, key)
    verifier = _canonical_verifier()
    for name in BUNDLES:
        bundle = modules / "packages" / f"specfact-{name}"
        (bundle / "src").mkdir(parents=True)
        (bundle / "src/commands.py").write_text("raise RuntimeError('verification must not import source')\n")
        manifest = bundle / "module-package.yaml"
        document: dict[str, Any] = {"name": f"nold-ai/specfact-{name}", "version": "1.0.0"}
        manifest.write_text(yaml.safe_dump(document))
        payload = verifier._module_payload(bundle, payload_from_filesystem=True)
        document["integrity"] = {
            "checksum": f"sha256:{hashlib.sha256(payload).hexdigest()}",
            "signature": base64.b64encode(key.sign(payload)).decode(),
        }
        manifest.write_text(yaml.safe_dump(document))
    (modules / "scripts").mkdir()
    (modules / "scripts/verify-modules-signature.py").write_text("raise RuntimeError('external verifier executed')\n")
    _write_public_key(modules, Ed25519PrivateKey.generate())
    return modules, trusted


def _mutate_source(modules: Path, trusted: Path, mutation: str) -> None:
    bundle = modules / "packages/specfact-code-review"
    manifest = bundle / "module-package.yaml"
    if mutation in {"missing-signature", "invalid-signature"}:
        document = yaml.safe_load(manifest.read_text())
        document["integrity"]["signature"] = (
            "" if mutation == "missing-signature" else base64.b64encode(b"x" * 64).decode()
        )
        manifest.write_text(yaml.safe_dump(document))
    if mutation == "payload-mismatch":
        (bundle / "src/commands.py").write_text("raise RuntimeError('changed source')\n")
    if mutation == "wrong-key":
        _write_public_key(trusted, Ed25519PrivateKey.generate())
    if mutation == "missing-manifest":
        manifest.unlink()
    if mutation == "empty-fixture":
        shutil.rmtree(modules / "packages")
        (modules / "packages").mkdir()
    if mutation == "extra-unsigned-source":
        (modules / "packages/unreviewed/src").mkdir(parents=True)


def _commit_source(modules: Path) -> dict[str, str]:
    subprocess.run(["git", "init", "-q", str(modules)], check=True)
    subprocess.run(["git", "-C", str(modules), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(modules),
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.test",
            "commit",
            "-qm",
            "fixture",
        ],
        check=True,
    )
    return {
        "repository": "nold-ai/specfact-cli-modules",
        **{
            name: subprocess.check_output(["git", "-C", str(modules), "rev-parse", ref], text=True).strip()
            for name, ref in (("commit", "HEAD"), ("tree", "HEAD^{tree}"))
        },
    }


def _workflow_steps(filename: str, job: str) -> list[dict[str, Any]]:
    return yaml.safe_load((REPO_ROOT / ".github/workflows" / filename).read_text())["jobs"][job]["steps"]


@pytest.mark.parametrize(("filename", "job"), JOBS)
@pytest.mark.parametrize(
    "mutation",
    [
        "valid",
        "missing-signature",
        "invalid-signature",
        "payload-mismatch",
        "wrong-key",
        "missing-manifest",
        "empty-fixture",
        "extra-unsigned-source",
    ],
)
def test_docs_jobs_authenticate_actual_signed_payloads(tmp_path: Path, filename: str, job: str, mutation: str) -> None:
    modules, trusted = _signed_sources(tmp_path)
    _mutate_source(modules, trusted, mutation)
    identity = _commit_source(modules)
    (tmp_path / "ci").mkdir()
    for name in ("module-fixture.lock.json", "docs-module-fixture.lock.json"):
        (tmp_path / "ci" / name).write_text(json.dumps(identity))
    wrapper = REPO_ROOT / "scripts/verify_docs_module_source.py"
    if wrapper.exists():
        (tmp_path / "scripts").mkdir()
        shutil.copyfile(wrapper, tmp_path / "scripts" / wrapper.name)
    names = {
        "Read immutable module fixture",
        "Verify immutable module fixture",
        "Authenticate module command sources",
        "Export module command source path",
    }
    script = "\n".join(step["run"] for step in _workflow_steps(filename, job) if step.get("name") in names)
    script = script.replace("${{ steps.modules-fixture.outputs.repository }}", "nold-ai/specfact-cli-modules")
    environment = {
        **os.environ,
        "PATH": str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"],
        "GITHUB_OUTPUT": str(tmp_path / "outputs"),
        "GITHUB_ENV": str(tmp_path / "environment"),
        "GITHUB_WORKSPACE": str(tmp_path),
        "VERIFY_MODULES_PR": "--skip-checksum-verification",
    }
    result = subprocess.run(["bash", "-c", script], cwd=tmp_path, env=environment, capture_output=True, text=True)
    assert (result.returncode == 0) is (mutation == "valid"), result.stdout + result.stderr
    assert (tmp_path / "environment").exists() is (mutation == "valid")


@pytest.mark.parametrize(("filename", "job"), JOBS)
def test_docs_authentication_precedes_exports_and_uses_core_base(filename: str, job: str) -> None:
    steps = _workflow_steps(filename, job)
    names = [step.get("name", "") for step in steps]
    assert "Authenticate module command sources" in names
    assert names.index("Authenticate module command sources") < names.index("Export module command source path")
    trusted = next(step for step in steps if step.get("name") == "Checkout trusted module verifier")
    assert trusted["with"]["ref"] == "${{ github.event.pull_request.base.sha || github.sha }}"
    assert trusted["with"]["path"] == "trusted-core-docs"
    assert trusted["with"]["persist-credentials"] is False
