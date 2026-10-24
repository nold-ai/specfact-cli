"""Actions configuration contract for the isolated PR785 prerequisite diagnostic."""

from pathlib import Path
from typing import Any, cast

import yaml


WORKFLOW = Path(__file__).resolve().parents[3] / ".github" / "workflows" / "specfact.yml"


def test_prerequisite_workflow_is_manual_read_only_and_bounded() -> None:
    workflow = cast(dict[str, Any], yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader))

    assert set(workflow["on"]) == {"workflow_dispatch"}, "The diagnostic must have only a manual entry point"
    assert workflow["on"]["workflow_dispatch"] in ("", {}), "Manual dispatch must accept no inputs"
    assert set(workflow) == {"name", "on", "permissions", "jobs"}
    assert workflow["permissions"] == {}
    assert set(workflow["jobs"]) == {"platform-prerequisites"}
    job = workflow["jobs"]["platform-prerequisites"]
    assert set(job) == {"name", "runs-on", "timeout-minutes", "permissions", "steps"}
    assert job["name"] == "PR785 runtime platform prerequisites"
    assert job["runs-on"] == "ubuntu-24.04"
    assert job["timeout-minutes"] == "5"
    assert job["permissions"] == {"contents": "read", "actions": "read"}


def test_prerequisite_workflow_runs_isolated_observer_and_preserves_output() -> None:
    workflow = cast(dict[str, Any], yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader))
    jobs = list(workflow["jobs"].values())
    assert len(jobs) == 1, "The observer must execute in its sole diagnostic job"
    steps = jobs[0]["steps"]
    assert steps == [
        {
            "name": "Checkout immutable observer",
            "uses": "actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10",
            "with": {
                "ref": "${{ github.sha }}",
                "persist-credentials": "false",
                "submodules": "false",
                "lfs": "false",
            },
        },
        {
            "name": "Observe current job boundary",
            "shell": "bash --noprofile --norc -e -o pipefail {0}",
            "env": {"GH_TOKEN": "${{ github.token }}"},
            "run": "/usr/bin/python3 -I -S -B scripts/pr785_runtime_prerequisite.py",
        },
        {
            "name": "Future step marker",
            "shell": "bash --noprofile --norc -e -o pipefail {0}",
            "run": "/usr/bin/printf '%s\\n' 'observation-only; no policy or authority'",
        },
        {
            "name": "Upload prerequisite observations",
            "if": "always()",
            "uses": "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
            "with": {
                "name": "pr785-runtime-prerequisite-${{ github.run_id }}-${{ github.run_attempt }}-${{ github.sha }}",
                "path": "platform-prerequisite-observations/",
                "if-no-files-found": "error",
            },
        },
    ], "The workflow must preserve the exact bounded diagnostic operations"
