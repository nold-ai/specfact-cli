"""Guard against stale generated command artifacts (llms.txt and command reference).

The pre-commit command-overview gate only fires when specific paths are staged, so a
commit that bypasses it (merge commits, --no-verify, bot commits) can land a stale
llms.txt. A stale llms.txt misleads agents worse than a missing one, so this test
re-runs the generator in --check mode on every test run.
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
    configured = os.environ.get("SPECFACT_MODULES_REPO", "").strip()
    candidates = [Path(configured).expanduser()] if configured else []
    candidates.append(REPO_ROOT.parent / "specfact-cli-modules")
    if "specfact-cli-worktrees" in REPO_ROOT.parts:
        marker = REPO_ROOT.parts.index("specfact-cli-worktrees")
        candidates.append(Path(*REPO_ROOT.parts[:marker]) / "specfact-cli-modules")
    return next((candidate for candidate in candidates if (candidate / "packages").is_dir()), None)


def _paired_worktree_modules_repo() -> Path | None:
    """Mirror the generator's paired-worktree candidate (specfact-cli-worktrees layout)."""
    parts = REPO_ROOT.parts
    if "specfact-cli-worktrees" not in parts:
        return None
    marker_index = parts.index("specfact-cli-worktrees")
    base = Path(*parts[:marker_index])
    suffix = Path(*parts[marker_index + 1 :])
    return base / "specfact-cli-modules-worktrees" / suffix


def _modules_repo_available() -> bool:
    if _modules_repo_root() is not None:
        return True
    paired = _paired_worktree_modules_repo()
    return paired is not None and (paired / "packages").is_dir()


def test_generated_command_artifacts_exist() -> None:
    for relative in GENERATED_ARTIFACTS:
        assert (REPO_ROOT / relative).is_file(), f"Missing generated artifact: {relative}"


def test_generated_command_contract_covers_requirements_module() -> None:
    """The official requirements package must be represented in generated docs."""
    records = json.loads((REPO_ROOT / "docs" / "reference" / "commands.generated.json").read_text(encoding="utf-8"))

    assert any(
        record.get("command") == "specfact requirements"
        and record.get("owner_package") == "nold-ai/specfact-requirements"
        for record in records
    )


def test_llms_and_command_overview_are_current() -> None:
    """llms.txt and the generated command reference must match the current CLI surface."""
    if not _modules_repo_available():
        pytest.skip("specfact-cli-modules packages checkout not available")

    modules_root = _modules_repo_root()
    if modules_root is not None:
        os.environ.setdefault("SPECFACT_MODULES_REPO", str(modules_root))

    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    assert result.returncode == 0, (
        "Generated command artifacts (llms.txt, docs/reference/commands.generated.*) are stale. "
        "Regenerate with 'hatch run generate-command-overview' and commit the result.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
