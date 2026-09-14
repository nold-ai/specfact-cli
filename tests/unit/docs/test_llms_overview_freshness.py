"""Guard against stale generated command artifacts (llms.txt and command reference).

The pre-commit command-overview gate only fires when specific paths are staged, so a
commit that bypasses it (merge commits, --no-verify, bot commits) can land a stale
llms.txt. A stale llms.txt misleads agents worse than a missing one, so documentation jobs
re-run the generator in --check mode against their separately reviewed fixture.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR = REPO_ROOT / "scripts" / "generate-command-overview.py"
GENERATED_ARTIFACTS = (
    "llms.txt",
    "docs/reference/commands.generated.json",
    "docs/reference/commands.generated.md",
)


def _modules_repo_root() -> Path | None:
    """Only the dedicated documentation context selects source for freshness."""
    configured = os.environ.get("SPECFACT_DOCS_MODULES_REPO", "").strip()
    if not configured:
        return None
    root = Path(configured).expanduser()
    assert (root / "packages").is_dir(), "Configured documentation module fixture is unavailable"
    return root


def test_generated_command_artifacts_exist() -> None:
    for relative in GENERATED_ARTIFACTS:
        assert (REPO_ROOT / relative).is_file(), f"Missing generated artifact: {relative}"


def test_generated_command_contract_covers_requirements_module() -> None:
    """The official requirements package must be represented in generated docs."""
    records = json.loads((REPO_ROOT / "docs" / "reference" / "commands.generated.json").read_text(encoding="utf-8"))

    assert any(
        record.get("command") == "specfact requirements"
        and record.get("owner_package") == "nold-ai/specfact-requirements"
        and record.get("owner_repo") == "nold-ai/specfact-cli-modules"
        for record in records
    )


def test_llms_and_command_overview_are_current() -> None:
    """llms.txt and the generated command reference must match the current CLI surface."""
    modules_root = _modules_repo_root()
    if modules_root is None:
        pytest.skip("Dedicated documentation module fixture is not configured in this job")

    env = os.environ.copy()
    env["SPECFACT_MODULES_REPO"] = str(modules_root)

    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
        timeout=300,
    )
    assert result.returncode == 0, (
        "Generated command artifacts (llms.txt, docs/reference/commands.generated.*) are stale. "
        "Regenerate with 'hatch run generate-command-overview' and commit the result.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_requirements_source_does_not_select_documentation_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "packages").mkdir()
    monkeypatch.setenv("SPECFACT_MODULES_REPO", str(tmp_path))
    monkeypatch.delenv("SPECFACT_DOCS_MODULES_REPO", raising=False)
    assert _modules_repo_root() is None
