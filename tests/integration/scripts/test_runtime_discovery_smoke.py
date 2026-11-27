from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
from collections.abc import Callable
from pathlib import Path

import pytest
import yaml

from scripts import runtime_discovery_smoke as smoke
from specfact_cli.registry import official_module_cutoff
from specfact_cli.registry.official_module_cutoff import FrozenArchive


REPO_ROOT = Path(__file__).resolve().parents[3]


def _resolve_modules_repo() -> Path | None:
    configured = (
        os.environ.get("SPECFACT_SMOKE_MODULES_REPO", "").strip() or os.environ.get("SPECFACT_MODULES_REPO", "").strip()
    )
    candidates: list[Path] = []
    if configured:
        candidates.append(Path(configured).expanduser())
    candidates.append(REPO_ROOT.parent / "specfact-cli-modules")
    parts = REPO_ROOT.parts
    if "specfact-cli-worktrees" in parts:
        marker_index = parts.index("specfact-cli-worktrees")
        candidates.append(
            Path(*parts[:marker_index]) / "specfact-cli-modules-worktrees" / Path(*parts[marker_index + 1 :])
        )
    if len(REPO_ROOT.parents) > 2:
        candidates.append(REPO_ROOT.parents[2] / "specfact-cli-modules")
    for candidate in candidates:
        packages = candidate / "packages"
        required = ("specfact-project", "specfact-codebase", "specfact-code-review")
        if all((packages / module / "module-package.yaml").exists() for module in required):
            return candidate.resolve()
    return None


@pytest.mark.integration
@pytest.mark.timeout(180)
def test_runtime_discovery_smoke_direct_launcher() -> None:
    modules_repo = _resolve_modules_repo()
    if modules_repo is None:
        pytest.skip("specfact-cli-modules checkout not available")

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "runtime_discovery_smoke.py"),
            "--modules-repo",
            str(modules_repo),
            "--launcher",
            "direct",
        ],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=180,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert "runtime-discovery smoke passed for launcher=direct" in result.stdout


@pytest.mark.parametrize("system_python", [False, True])
def test_isolated_launcher_retains_system_tools(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, system_python: bool
) -> None:
    if os.name != "posix":
        pytest.skip("The /usr system layout is POSIX-specific")
    parent = Path("/usr") if system_python else tmp_path / "parent-venv"
    inherited = [str(parent / "lib" / "parent-tools"), "/usr/bin", "/usr/sbin", "/bin", "/sbin"]
    monkeypatch.setattr(sys, "prefix", str(parent))
    monkeypatch.setenv("PATH", os.pathsep.join(inherited))

    env = smoke._build_launcher_env("direct", tmp_path / "home", tmp_path / "index.json", tmp_path)

    assert env["PATH"].split(os.pathsep) == [str(tmp_path / "launcher-direct" / "runtime-venv" / "bin"), *inherited[1:]]


@pytest.fixture
def add_frozen_smoke_archive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Callable[[str, str, tuple[str, ...]], Path]:
    latest: dict[str, str] = {}
    archives: dict[str, dict[str, FrozenArchive]] = {}
    original = official_module_cutoff._inventory()
    monkeypatch.setattr(
        official_module_cutoff,
        "_inventory",
        lambda: {**original, "latest": latest, "archives": archives},
    )

    def add(name: str, version: str, dependencies: tuple[str, ...]) -> Path:
        module_id = f"nold-ai/{name}"
        registry = tmp_path / "modules-repo" / "registry" / "modules"
        registry.mkdir(parents=True, exist_ok=True)
        archive = registry / f"{name}-{version}.tar.gz"
        manifest = tmp_path / f"{name}.yaml"
        manifest.write_text(
            yaml.safe_dump({"name": module_id, "version": version, "bundle_dependencies": list(dependencies)}),
            encoding="utf-8",
        )
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(manifest, arcname=f"{name}/module-package.yaml")
        latest[module_id] = version
        archives[module_id] = {version: {"archive": hashlib.sha256(archive.read_bytes()).hexdigest(), "tree": "unused"}}
        return archive

    return add


@pytest.fixture
def frozen_smoke_archive(add_frozen_smoke_archive: Callable[[str, str, tuple[str, ...]], Path]) -> Path:
    return add_frozen_smoke_archive("specfact-project", "0.41.27", ())


def test_local_runtime_registry_includes_transitive_bundle_dependencies(
    tmp_path: Path, add_frozen_smoke_archive: Callable[[str, str, tuple[str, ...]], Path]
) -> None:
    from scripts.runtime_discovery_smoke import _build_local_registry

    add_frozen_smoke_archive("specfact-project", "0.41.27", ())
    add_frozen_smoke_archive("specfact-spec", "0.40.25", ("nold-ai/specfact-project",))
    add_frozen_smoke_archive("specfact-govern", "0.40.27", ("nold-ai/specfact-spec", "nold-ai/specfact-project"))
    index = _build_local_registry(tmp_path / "workspace", tmp_path / "modules-repo")
    entries = json.loads(index.read_text(encoding="utf-8"))["modules"]
    assert [entry["id"] for entry in entries] == [
        "nold-ai/specfact-govern",
        "nold-ai/specfact-project",
        "nold-ai/specfact-spec",
    ]
    assert entries[0]["bundle_dependencies"] == ["nold-ai/specfact-spec", "nold-ai/specfact-project"]
    assert entries[2]["bundle_dependencies"] == ["nold-ai/specfact-project"]


def test_semver_prerelease_and_suffix_are_valid_for_runtime_registry(
    tmp_path: Path, add_frozen_smoke_archive: Callable[[str, str, tuple[str, ...]], Path]
) -> None:
    from scripts.runtime_discovery_smoke import _build_local_registry

    version = "0.5.1-rc.1+build.7"
    archive = add_frozen_smoke_archive("specfact-project", version, ())
    index = _build_local_registry(tmp_path / "workspace", tmp_path / "modules-repo")
    entry = json.loads(index.read_text(encoding="utf-8"))["modules"][0]
    assert entry["latest_version"] == version
    assert (index.parent / entry["download_url"]).read_bytes() == archive.read_bytes()


@pytest.mark.parametrize("version", ["01.2.3", "1.2.3-01", "1.2.3-alpha..1"])
def test_local_runtime_registry_rejects_malformed_semver(
    tmp_path: Path, version: str, add_frozen_smoke_archive: Callable[[str, str, tuple[str, ...]], Path]
) -> None:
    from scripts.runtime_discovery_smoke import _build_local_registry

    add_frozen_smoke_archive("specfact-project", version, ())
    workspace = tmp_path / "workspace"
    with pytest.raises(RuntimeError, match="Invalid module version"):
        _build_local_registry(workspace, tmp_path / "modules-repo")
    assert not list(workspace.rglob("*.tar.gz"))


def test_local_runtime_registry_preserves_exact_published_archive(
    tmp_path: Path, frozen_smoke_archive: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.runtime_discovery_smoke import _build_local_registry
    from specfact_cli.registry.marketplace_client import download_module

    modules_repo = tmp_path / "modules-repo"
    ignored = modules_repo / "packages/specfact-project/ignored.py"
    ignored.parent.mkdir(parents=True)
    ignored.write_text("# Local scratch file\n", encoding="utf-8")
    index_path = _build_local_registry(tmp_path / "workspace", modules_repo)
    entry = json.loads(index_path.read_text())["modules"][0]
    assert (index_path.parent / entry["download_url"]).read_bytes() == frozen_smoke_archive.read_bytes()
    monkeypatch.setenv("SPECFACT_REGISTRY_INDEX_URL", str(index_path))
    downloaded = download_module(entry["id"], download_dir=tmp_path / "downloads")
    assert downloaded.read_bytes() == frozen_smoke_archive.read_bytes()


def test_local_runtime_registry_refuses_changed_archive(tmp_path: Path, frozen_smoke_archive: Path) -> None:
    from scripts.runtime_discovery_smoke import _build_local_registry

    frozen_smoke_archive.write_bytes(b"changed archive")
    with pytest.raises(RuntimeError, match="does not match the release cutoff"):
        _build_local_registry(tmp_path / "workspace", tmp_path / "modules-repo")


def test_runtime_discovery_smoke_keep_workspace_preserves_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.runtime_discovery_smoke as smoke

    captured: dict[str, Path] = {}

    def create_demo(workspace: Path, _template: Path | None) -> Path:
        demo = workspace / "demo"
        demo.mkdir(parents=True)
        return demo

    def smoke_launcher(_name: str, workspace: Path, _demo: Path, _index_path: Path, _modules_repo: Path) -> None:
        captured["workspace"] = workspace

    monkeypatch.setattr(smoke, "_resolve_modules_repo", lambda _configured: tmp_path)
    monkeypatch.setattr(smoke, "_verify_smoke_fixture", lambda _modules_repo: None)
    monkeypatch.setattr(smoke, "_create_rootless_monorepo_demo", create_demo)
    monkeypatch.setattr(smoke, "_build_local_registry", lambda workspace, _modules_repo: workspace / "index.json")
    monkeypatch.setattr(smoke, "_smoke_launcher", smoke_launcher)
    monkeypatch.setattr(sys, "argv", ["runtime_discovery_smoke.py", "--keep-workspace"])

    try:
        assert smoke.main() == 0
        assert captured["workspace"].exists()
    finally:
        if "workspace" in captured:
            shutil.rmtree(captured["workspace"], ignore_errors=True)


def test_runtime_discovery_smoke_uses_fresh_demo_per_launcher(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.runtime_discovery_smoke as smoke

    demos: list[Path] = []
    registry_builds: list[Path] = []

    def create_demo(workspace: Path, _template: Path | None) -> Path:
        demo = workspace / "demo"
        demo.mkdir(parents=True)
        demos.append(demo)
        return demo

    def build_registry(workspace: Path, _modules_repo: Path) -> Path:
        registry_builds.append(workspace)
        return workspace / "index.json"

    monkeypatch.setattr(smoke, "_resolve_modules_repo", lambda _configured: tmp_path)
    monkeypatch.setattr(smoke, "_verify_smoke_fixture", lambda _modules_repo: None)
    monkeypatch.setattr(smoke, "_create_rootless_monorepo_demo", create_demo)
    monkeypatch.setattr(smoke, "_build_local_registry", build_registry)
    monkeypatch.setattr(smoke, "_smoke_launcher", lambda _name, _workspace, _demo, _index_path, _modules_repo: None)
    monkeypatch.setattr(
        sys,
        "argv",
        ["runtime_discovery_smoke.py", "--launcher", "direct", "--launcher", "console"],
    )

    assert smoke.main() == 0

    assert len(registry_builds) == 1
    assert len(demos) == 2
    assert len({demo.resolve() for demo in demos}) == 2
    assert str(REPO_ROOT / "src") in smoke.sys.path
