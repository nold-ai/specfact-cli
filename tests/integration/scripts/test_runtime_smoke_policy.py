"""Reject executable-wheel smoke inputs and authenticate the portable fixture."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import scripts.runtime_discovery_smoke as smoke


def test_smoke_seed_excludes_unofficial_node_and_python_type_runner() -> None:
    lock = (smoke.REPO_ROOT / "requirements/runtime-smoke/locked.txt").read_text()
    assert "nodejs-wheel-binaries==" not in lock
    assert "basedpyright==" not in lock


def test_portable_smoke_fixture_precedes_legacy_requirements_fixture(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    portable, legacy = tmp_path / "portable", tmp_path / "legacy"
    for repo in (portable, legacy):
        for module_id in smoke.MODULE_IDS:
            manifest = repo / "packages" / module_id.split("/", 1)[1] / "module-package.yaml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text("name: fixture\n")
    monkeypatch.setenv("SPECFACT_SMOKE_MODULES_REPO", str(portable))
    monkeypatch.setenv("SPECFACT_MODULES_REPO", str(legacy))
    assert smoke._resolve_modules_repo(None) == portable.resolve()


@pytest.mark.parametrize("mismatch", [None, "commit", "tree", "dirty"])
def test_smoke_fixture_rejects_unreviewed_git_bytes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mismatch: str | None
) -> None:
    repo = tmp_path / "modules"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.test",
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "fixture",
        ],
        check=True,
    )
    identity = {"repository": "nold-ai/specfact-cli-modules"}
    for key, revision in (("commit", "HEAD"), ("tree", "HEAD^{tree}")):
        identity[key] = subprocess.check_output(["git", "-C", str(repo), "rev-parse", revision], text=True).strip()
    if mismatch in {"commit", "tree"}:
        identity[mismatch] = "a" * 40
    if mismatch == "dirty":
        (repo / "unreviewed.py").write_text("raise RuntimeError('unreviewed')\n")
    (tmp_path / "ci").mkdir()
    (tmp_path / "ci/runtime-smoke-fixture.lock.json").write_text(json.dumps(identity))
    monkeypatch.setattr(smoke, "REPO_ROOT", tmp_path)
    if mismatch is None:
        smoke._verify_smoke_fixture(repo)
    else:
        with pytest.raises(RuntimeError, match="Smoke fixture identity"):
            smoke._verify_smoke_fixture(repo)
