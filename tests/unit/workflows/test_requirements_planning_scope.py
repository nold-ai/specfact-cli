"""Execute workflow selection boundaries for planning and implementation evidence."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml


WORKFLOW = Path(__file__).resolve().parents[3] / ".github/workflows/requirements-evidence.yml"
STAGES = (
    ("Reconcile Requirements evidence on fresh runner", "consumer"),
    ("Reconcile final Requirements verdict on fresh runner", "final"),
)


def _command(step_name: str) -> str:
    """Read the actual shell command for one named workflow step."""
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    return next(
        step["run"] for job in workflow["jobs"].values() for step in job["steps"] if step.get("name") == step_name
    )


def _select_review(
    root: Path, step_name: str, prefix: str, maturity: str, changes: tuple[str, ...]
) -> subprocess.CompletedProcess[str]:
    """Execute the workflow's selection block with a controlled changed scope."""
    command = _command(step_name)
    start = command.index("review_evidence_paths=()")
    end = command.index('selected_change=""', start)
    entries = " ".join(f"[{change}]=1" for change in changes)
    script = (
        "set -euo pipefail\n"
        f"declare -A {prefix}_changed_change_ids=({entries})\n"
        + command[start:end]
        + '\nprintf "%s\\n" "${review_evidence_paths[@]}"\n'
    )
    return subprocess.run(
        ["bash", "-c", script],
        cwd=root,
        env={**os.environ, "planning_maturity": maturity, "EVIDENCE_PROMOTION_REUSE": "false"},
        check=False,
        capture_output=True,
        text=True,
    )


def test_planned_changes_do_not_select_implementation_reviews(tmp_path: Path) -> None:
    """One or several plans need no approval; an unrelated record cannot enter them."""
    unrelated = tmp_path / "openspec/changes/unrelated/requirements-proof/review-evidence.json"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_text("{}", encoding="utf-8")
    for step_name, prefix in STAGES:
        for changes in (("first",), ("first", "second"), ()):
            result = _select_review(tmp_path, step_name, prefix, "planned", changes)
            assert result.returncode == 0, result.stderr
            assert not result.stdout.strip(), result.stdout


def test_implementation_review_scope_remains_enforced(tmp_path: Path) -> None:
    """Existing implementation selection and ambiguous-scope rejection remain intact."""
    for step_name, prefix in STAGES:
        selected = _select_review(tmp_path, step_name, prefix, "test-authored", ("first",))
        assert selected.returncode == 0, selected.stderr
        assert selected.stdout.strip() == "openspec/changes/first/requirements-proof/review-evidence.json"
        rejected = _select_review(tmp_path, step_name, prefix, "test-authored", ("first", "second"))
        assert rejected.returncode != 0
        assert "multiple changed active OpenSpec changes" in rejected.stderr


def test_producer_keeps_implementation_approval_out_of_planning(tmp_path: Path) -> None:
    """Producer and verifiers use the same approval-free planning context."""
    record = tmp_path / "openspec/changes/first/requirements-proof/review-evidence.json"
    record.parent.mkdir(parents=True)
    record.write_text("{}", encoding="utf-8")
    command = _command("Run Requirements evidence gate")
    start = command.index('prior_red_proof=""')
    end = command.index("bootstrap_root=", start)
    script = (
        'set -euo pipefail\nevidence_arguments=()\nselected_change="first"\n'
        + command[start:end]
        + '\nprintf "%s\\n" "${evidence_arguments[@]}"\n'
    )
    for maturity in ("planned", "test-authored"):
        result = subprocess.run(
            ["bash", "-c", script],
            cwd=tmp_path,
            env={
                **os.environ,
                "planning_maturity": maturity,
                "RUNNER_TEMP": str(tmp_path),
                "evidence_base_commit": "0" * 40,
                "LATE_RED_ACTIVE": "false",
            },
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert ("--review-evidence" in result.stdout) == (maturity != "planned")
