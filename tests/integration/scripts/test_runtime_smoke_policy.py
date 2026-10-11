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


def test_child_environment_cannot_import_parent_or_inherited_packages(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    unrelated = tmp_path / "unreviewed-python-path"
    monkeypatch.setenv("PYTHONPATH", str(unrelated))
    env = smoke._frozen_runtime_env(dict(smoke.os.environ), tmp_path / "constraints.txt")
    assert env["PYTHONPATH"] == str(smoke.SRC_ROOT)
    assert env["SPECFACT_CHILD_PYTHONPATH"] == str(smoke.SRC_ROOT)


def test_child_seed_installs_the_entire_hash_locked_graph(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    commands: list[list[str]] = []
    environments: list[dict[str, str]] = []
    cache = tmp_path / "reviewed-artifact-cache"
    monkeypatch.setattr(smoke.subprocess, "check_output", lambda *_args, **_kwargs: str(cache))

    def capture(
        command: list[str], *, cwd: Path, env: dict[str, str], timeout: int
    ) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        environments.append(env)
        return subprocess.CompletedProcess(command, 0, "")

    monkeypatch.setattr(smoke, "_run", capture)
    monkeypatch.setattr(smoke, "_resolve_modules_repo", lambda _configured: tmp_path)
    monkeypatch.setattr(smoke, "_verify_smoke_fixture", lambda _repo: None)
    monkeypatch.setattr(smoke, "_frozen_marketplace_requirements", lambda _repo: "reviewed==1.0\n")
    smoke._seed_frozen_module_dependencies(tmp_path, {"PIP_NO_INDEX": "1"})
    assert len(commands) == 3
    assert all(
        flag in commands[0] for flag in ("sync", "--frozen", "--all-extras", "--offline", "--no-install-project")
    )
    assert str(smoke.REPO_ROOT / "requirements/runtime-smoke/locked.txt") in commands[1]
    assert "--require-hashes" in commands[1]
    assert "download" in commands[2] and "--require-hashes" in commands[2] and "--no-deps" in commands[2]
    assert all(env["UV_CACHE_DIR"] == str(cache) for env in environments)


def test_marketplace_wheelhouse_uses_frozen_transitive_hashes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    modules = tmp_path / "modules"
    for module_id in smoke.MODULE_IDS:
        manifest = modules / "packages" / module_id.split("/", 1)[1] / "module-package.yaml"
        manifest.parent.mkdir(parents=True)
        manifest.write_text("pip_dependencies: [reviewed-root]\nbundle_dependencies: []\n")
    (tmp_path / "uv.lock").write_text(
        '[[package]]\nname = "reviewed-root"\nversion = "1.0"\ndependencies = [{name = "reviewed-leaf"}]\n'
        '[[package]]\nname = "reviewed-leaf"\nversion = "2.0"\n'
    )
    for directory in ("ci", "runtime-smoke"):
        (tmp_path / "requirements" / directory).mkdir(parents=True)
    root = "reviewed-root==1.0 \\" + "\n    --hash=sha256:" + "a" * 64 + "\n"
    leaf = "reviewed-leaf==2.0 \\" + "\n    --hash=sha256:" + "b" * 64 + "\n"
    (tmp_path / "requirements/ci/locked.txt").write_text(root + leaf + "unrelated==3.0\n")
    (tmp_path / "requirements/runtime-smoke/locked.txt").write_text("lz4==4.4.5\n")
    monkeypatch.setattr(smoke, "REPO_ROOT", tmp_path)
    assert smoke._frozen_marketplace_requirements(modules) == leaf + root
    (tmp_path / "requirements/ci/locked.txt").write_text(root)
    with pytest.raises(RuntimeError, match="frozen hash"):
        smoke._frozen_marketplace_requirements(modules)


def test_marketplace_resolver_only_uses_child_wheelhouse(tmp_path: Path) -> None:
    home = tmp_path / "home-direct"
    env = smoke._build_launcher_env("direct", home, tmp_path / "index.json", tmp_path / "modules")
    assert env["PIP_FIND_LINKS"] == str(tmp_path / "launcher-direct" / "frozen-wheels")
    assert env["PIP_NO_INDEX"] == "1"
