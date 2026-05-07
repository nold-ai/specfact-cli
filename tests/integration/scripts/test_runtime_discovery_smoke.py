from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]


def _resolve_modules_repo() -> Path | None:
    configured = os.environ.get("SPECFACT_MODULES_REPO", "").strip()
    candidates: list[Path] = []
    if configured:
        candidates.append(Path(configured).expanduser())
    candidates.extend(
        [
            REPO_ROOT.parent / "specfact-cli-modules",
            REPO_ROOT.parents[2] / "specfact-cli-modules",
        ]
    )
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


def test_runtime_discovery_smoke_keep_workspace_preserves_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.runtime_discovery_smoke as smoke

    captured: dict[str, Path] = {}

    def create_demo(workspace: Path, _template: Path | None) -> Path:
        demo = workspace / "demo"
        demo.mkdir()
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
