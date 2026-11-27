"""Check that CI binds module checkout inputs before checkout."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(
    ("filename", "jobs"),
    [
        (
            "pr-orchestrator.yml",
            {
                "tests": "module-fixture",
                "compat-py311": "module-fixture",
                "contract-first-ci": "module-fixture",
                "cli-validation": "docs-module-fixture",
                "runtime-smoke-macos": "module-fixture",
                "runtime-smoke-windows": "module-fixture",
                "dependency-compatibility": "module-fixture",
            },
        ),
        ("specfact.yml", {"specfact-validation": "module-fixture"}),
        ("docs-review.yml", {"docs-review": "docs-module-fixture"}),
    ],
    ids=["orchestrator", "contract", "docs"],
)
def test_default_branch_jobs_pin_module_checkouts(filename: str, jobs: dict[str, str]) -> None:
    workflow = cast(dict[str, Any], yaml.safe_load((ROOT / ".github/workflows" / filename).read_text()))
    for job, lock_name in jobs.items():
        identity = json.loads((ROOT / "ci" / f"{lock_name}.lock.json").read_text())
        steps = workflow["jobs"][job]["steps"]
        checkout = next(step["with"] for step in steps if step.get("with", {}).get("path") == "specfact-cli-modules")
        assert checkout["repository"] == identity["repository"], job
        assert checkout["ref"] == identity["commit"], job
        assert checkout["persist-credentials"] is False, job
