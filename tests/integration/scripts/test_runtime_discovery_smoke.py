from __future__ import annotations

import os
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
