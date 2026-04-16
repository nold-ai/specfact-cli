"""scripts/module-verify-policy.sh must stay aligned with pre-commit and CI workflows."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
POLICY = REPO_ROOT / "scripts" / "module-verify-policy.sh"


def _sourced_args(var: str) -> list[str]:
    result = subprocess.run(
        ["bash", "-c", f'source "{POLICY}" && printf "%s\\0" "${{{var}[@]}}"'],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    out = result.stdout
    if not out:
        return []
    return [part for part in out.split("\0") if part]


def test_module_verify_policy_script_exists() -> None:
    assert POLICY.is_file(), "module-verify-policy.sh must exist for CI/pre-commit parity"


@pytest.mark.parametrize(
    ("var", "expected"),
    (
        (
            "VERIFY_MODULES_STRICT",
            ["--require-signature", "--enforce-version-bump", "--payload-from-filesystem"],
        ),
        ("VERIFY_MODULES_PR", ["--enforce-version-bump", "--skip-checksum-verification"]),
        (
            "VERIFY_MODULES_PUSH_ORCHESTRATOR",
            ["--enforce-version-bump", "--payload-from-filesystem"],
        ),
    ),
)
def test_module_verify_policy_arrays(var: str, expected: list[str]) -> None:
    assert _sourced_args(var) == expected


def test_pre_commit_verify_modules_sources_policy() -> None:
    body = (REPO_ROOT / "scripts" / "pre-commit-verify-modules.sh").read_text(encoding="utf-8")
    assert "module-verify-policy.sh" in body
    assert "exec hatch run verify-modules-signature" in body
    assert "exec hatch run verify-modules-signature-pr" in body


def test_pr_orchestrator_verify_job_sources_policy() -> None:
    orchestrator = REPO_ROOT / ".github" / "workflows" / "pr-orchestrator.yml"
    if not orchestrator.is_file():
        pytest.skip("pr-orchestrator not present")
    text = orchestrator.read_text(encoding="utf-8")
    assert "source scripts/module-verify-policy.sh" in text
    assert '"${VERIFY_MODULES_PR[@]}"' in text
    assert '"${VERIFY_MODULES_PUSH_ORCHESTRATOR[@]}"' in text


def test_sign_modules_verify_job_sources_policy() -> None:
    workflow = REPO_ROOT / ".github" / "workflows" / "sign-modules.yml"
    if not workflow.is_file():
        pytest.skip("sign-modules workflow not present")
    text = workflow.read_text(encoding="utf-8")
    assert "source scripts/module-verify-policy.sh" in text
    assert '"${VERIFY_MODULES_STRICT[@]}"' in text
    assert '"${VERIFY_MODULES_PR[@]}"' in text
