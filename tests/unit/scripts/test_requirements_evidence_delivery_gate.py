"""Contract tests for the immutable Requirements evidence delivery adapter."""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Protocol, cast

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
GATE_SCRIPT = REPO_ROOT / "scripts" / "requirements_evidence_delivery_gate.py"


class GateModule(Protocol):
    """Typed public surface supplied by the file-loaded delivery adapter."""

    EvidenceRequest: Callable[..., object]

    def verify_fixture(
        self, fixture: dict[str, object], fixture_root: Path, *, git_runner: Callable[..., str]
    ) -> None: ...

    def run_evidence_command(
        self, request: object, fixture_root: Path, *, command_runner: Callable[..., int]
    ) -> int: ...


def _load_gate_module() -> GateModule:
    spec = importlib.util.spec_from_file_location("requirements_evidence_delivery_gate", GATE_SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("Requirements evidence delivery adapter must be importable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast(GateModule, module)


def test_verified_fixture_requires_exact_released_identity(tmp_path: Path) -> None:
    """Mutable, missing, or wrong-SHA fixture sources must be rejected before execution."""
    module = _load_gate_module()

    with pytest.raises(ValueError, match="full immutable SHA"):  # type: ignore[reportUnknownMemberType]
        module.verify_fixture(
            {"repository": "nold-ai/specfact-cli-modules", "commit": "dev"},
            tmp_path,
            git_runner=lambda *_: "",
        )

    with pytest.raises(  # type: ignore[reportUnknownMemberType]
        ValueError, match="must target nold-ai/specfact-cli-modules"
    ):
        module.verify_fixture(
            {"repository": "example/other", "commit": "2438372f8e34c96d4e474afa4c66c92a9cee7979"},
            tmp_path,
            git_runner=lambda *_: "",
        )

    with pytest.raises(ValueError, match="does not match"):  # type: ignore[reportUnknownMemberType]
        module.verify_fixture(
            {
                "repository": "nold-ai/specfact-cli-modules",
                "commit": "2438372f8e34c96d4e474afa4c66c92a9cee7979",
            },
            tmp_path,
            git_runner=lambda *_: "0000000000000000000000000000000000000000",
        )


def test_staged_red_verdict_keeps_both_report_destinations(tmp_path: Path) -> None:
    """The adapter must propagate a red verdict without deleting module output paths."""
    module = _load_gate_module()
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    json_report = tmp_path / "reports" / "evidence.json"
    markdown_report = tmp_path / "reports" / "evidence.md"

    observed = module.run_evidence_command(
        module.EvidenceRequest(
            repo_root=tmp_path,
            selection=("--staged", None),
            output_path=json_report,
            summary_path=markdown_report,
        ),
        fixture,
        command_runner=lambda arguments, environment: (
            json_report.parent.mkdir(parents=True, exist_ok=True),
            json_report.write_text('{"verdict":"failed"}\n', encoding="utf-8"),
            markdown_report.write_text("## Requirements evidence\n", encoding="utf-8"),
            1,
        )[-1],
    )

    assert observed == 1
    assert json_report.read_text(encoding="utf-8") == '{"verdict":"failed"}\n'
    assert markdown_report.read_text(encoding="utf-8") == "## Requirements evidence\n"


def test_pre_commit_places_evidence_before_review_and_contracts() -> None:
    """A red evidence verdict must stop later Block 2 gates."""
    pre_commit = (REPO_ROOT / "scripts" / "pre-commit-quality-checks.sh").read_text(encoding="utf-8")

    assert "run_requirements_evidence_gate" in pre_commit
    block2 = pre_commit[pre_commit.index("run_block2() {") : pre_commit.index("run_all() {")]
    assert block2.index("run_requirements_evidence_gate") < block2.index("run_code_review_gate")
    assert block2.index("run_requirements_evidence_gate") < block2.index("run_contract_tests_visible")
    assert ".specfact/reports/requirements-evidence" in pre_commit
