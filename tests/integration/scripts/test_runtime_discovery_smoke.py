from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]


def _write_module_manifest(modules_repo: Path, bundle_name: str, dependencies: list[str] | None = None) -> None:
    package_dir = modules_repo / "packages" / bundle_name
    package_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, object] = {
        "name": bundle_name,
        "version": "0.1.0",
        "commands": [],
        "core_compatibility": ">=0.1.0,<1.0.0",
    }
    if dependencies:
        manifest["bundle_dependencies"] = dependencies
    (package_dir / "module-package.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False),
        encoding="utf-8",
    )


def _resolve_modules_repo() -> Path | None:
    configured = os.environ.get("SPECFACT_MODULES_REPO", "").strip()
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


def test_local_runtime_registry_includes_transitive_bundle_dependencies(tmp_path: Path) -> None:
    import scripts.runtime_discovery_smoke as smoke

    modules_repo = tmp_path / "modules"
    for module_id in smoke.MODULE_IDS:
        _write_module_manifest(modules_repo, module_id.split("/", 1)[1])
    _write_module_manifest(
        modules_repo,
        "specfact-code-review",
        dependencies=["nold-ai/specfact-requirements"],
    )
    _write_module_manifest(modules_repo, "specfact-requirements")

    index_path = smoke._build_local_registry(tmp_path / "workspace", modules_repo)
    module_ids = {entry["id"] for entry in yaml.safe_load(index_path.read_text(encoding="utf-8"))["modules"]}

    assert module_ids == {*smoke.MODULE_IDS, "nold-ai/specfact-requirements"}


def test_local_runtime_registry_rejects_traversal_in_manifest_version(tmp_path: Path) -> None:
    import scripts.runtime_discovery_smoke as smoke

    modules_repo = tmp_path / "modules"
    for module_id in smoke.MODULE_IDS:
        _write_module_manifest(modules_repo, module_id.split("/", 1)[1])
    manifest_path = modules_repo / "packages" / smoke.MODULE_IDS[0].split("/", 1)[1] / "module-package.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["version"] = "0.1.0/../../outside"
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")

    with pytest.raises(RuntimeError, match="Invalid module version"):
        smoke._build_local_registry(tmp_path / "workspace", modules_repo)


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
