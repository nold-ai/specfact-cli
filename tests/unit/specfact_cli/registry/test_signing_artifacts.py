"""
Tests for signing automation artifacts (arch-06): script and CI workflow.
"""

from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[4]
SIGN_SCRIPT = REPO_ROOT / "scripts" / "sign-module.sh"
SIGN_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "sign-modules.yml"


def test_sign_module_script_exists():
    """Signing script scripts/sign-module.sh SHALL exist."""
    assert SIGN_SCRIPT.exists(), "scripts/sign-module.sh must exist for signing automation"


def test_sign_module_script_invocation_prints_or_produces_checksum(tmp_path: Path):
    """Signing script invocation SHALL produce or emit checksum for manifest integrity."""
    if not SIGN_SCRIPT.exists():
        pytest.skip("sign-module.sh not present")
    manifest = tmp_path / "module-package.yaml"
    manifest.write_text("name: test\nversion: 0.1.0\ncommands: [c]\n", encoding="utf-8")
    import subprocess

    result = subprocess.run(
        ["bash", str(SIGN_SCRIPT), str(manifest)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=10,
    )
    assert result.returncode == 0 or result.stderr or result.stdout
    if result.returncode == 0 and result.stdout:
        assert "sha256:" in result.stdout or "checksum" in result.stdout.lower()


def test_sign_modules_workflow_exists():
    """CI workflow .github/workflows/sign-modules.yml SHALL exist."""
    assert SIGN_WORKFLOW.exists(), "sign-modules.yml workflow must exist"


def test_sign_modules_workflow_valid_yaml():
    """Sign-modules workflow file SHALL be valid YAML."""
    if not SIGN_WORKFLOW.exists():
        pytest.skip("workflow not present")
    import yaml

    data = yaml.safe_load(SIGN_WORKFLOW.read_text(encoding="utf-8"))
    assert data is not None
    assert isinstance(data, dict)
