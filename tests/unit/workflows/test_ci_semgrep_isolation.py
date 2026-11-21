"""Verify the scanner boundary and fail-closed scan ordering."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
SCANNER_PACKAGES = {"semgrep", "mcp", "wcmatch"}


def test_shared_dependency_profiles_exclude_scanner() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert "scanning" not in project["project"]["optional-dependencies"]
    hatch = project["tool"]["hatch"]["envs"]["default"]["dependencies"]
    assert not any(requirement.lower().startswith("semgrep") for requirement in hatch)
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    assert SCANNER_PACKAGES.isdisjoint(package["name"] for package in lock["package"])
    for scope in ("ci", "code-review", "runtime-smoke"):
        export = (ROOT / f"requirements/{scope}/locked.txt").read_text(encoding="utf-8")
        assert SCANNER_PACKAGES.isdisjoint(re.findall(r"^([\w.-]+)==", export, re.MULTILINE)), scope


def test_semgrep_is_audited_before_its_isolated_install_and_scan() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/pr-orchestrator.yml").read_text(encoding="utf-8"))
    job = workflow["jobs"]["independent-static-analysis"]
    assert job.get("continue-on-error") is not True
    steps = [step for step in job["steps"] if "run" in step]
    scan = next(step for step in steps if "semgrep_sast_gate.py" in step["run"])
    script = scan["run"]
    assert "set -euo pipefail" in script
    audit = script.index("python scripts/security_audit_gate.py --requirement requirements/semgrep/locked.txt")
    install = script.index("uv pip install")
    invoke = script.index('/bin/semgrep" scan --config tools/semgrep/sast.yml')
    assert audit < install < invoke < script.index("python scripts/semgrep_sast_gate.py")
    assert "--require-hashes --only-binary :all:" in script
    assert "--baseline tools/semgrep/sast-baseline.json" in script
    assert any("bandit -r src/" in step["run"] for step in steps)
    assert scan.get("continue-on-error") is not True
