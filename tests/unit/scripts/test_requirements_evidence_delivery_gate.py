"""Contract tests for the immutable Requirements evidence delivery adapter."""

from __future__ import annotations

import importlib.util
import json
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

    def verify_fixture(self, fixture: dict[str, object], fixture_root: Path, *, git_runner: Callable[..., str]) -> None:
        pass

    def run_evidence_command(self, request: object, fixture_root: Path, *, command_runner: Callable[..., int]) -> int:
        raise NotImplementedError

    def main(self, argv: list[str] | None = None) -> int:
        raise NotImplementedError


class CapturedRequest(Protocol):
    """Minimal assertion surface retained from a delegated evidence request."""

    selection: tuple[str, str | None]
    required_maturity: str


def _load_gate_module() -> GateModule:
    spec = importlib.util.spec_from_file_location("requirements_evidence_delivery_gate", GATE_SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("Requirements evidence delivery adapter must be importable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast(GateModule, module)


def test_verified_fixture_requires_exact_released_identity_and_clean_tree(tmp_path: Path) -> None:
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

    with pytest.raises(ValueError, match="must use approved release commit"):  # type: ignore[reportUnknownMemberType]
        module.verify_fixture(
            {
                "repository": "nold-ai/specfact-cli-modules",
                "commit": "0000000000000000000000000000000000000000",
            },
            tmp_path,
            git_runner=lambda *_: "0000000000000000000000000000000000000000",
        )

    with pytest.raises(ValueError, match="must be clean"):  # type: ignore[reportUnknownMemberType]
        module.verify_fixture(
            {
                "repository": "nold-ai/specfact-cli-modules",
                "commit": "2438372f8e34c96d4e474afa4c66c92a9cee7979",
            },
            tmp_path,
            git_runner=lambda arguments: (
                "2438372f8e34c96d4e474afa4c66c92a9cee7979"
                if arguments[-2:] == ["rev-parse", "HEAD"]
                else " M package.py\n"
            ),
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


def test_delegated_command_requests_planned_maturity(tmp_path: Path) -> None:
    """Proposal-only core changes must never be evaluated as implemented delivery."""
    module = _load_gate_module()
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    captured_arguments: list[str] = []
    request = module.EvidenceRequest(
        repo_root=tmp_path,
        selection=("--staged", None),
        output_path=tmp_path / "evidence.json",
        summary_path=tmp_path / "evidence.md",
    )

    assert (
        module.run_evidence_command(
            request,
            fixture,
            command_runner=lambda arguments, _environment: captured_arguments.extend(arguments) or 0,
        )
        == 0
    )
    assert request.required_maturity == "planned"
    maturity_index = captured_arguments.index("--required-maturity")
    assert captured_arguments[maturity_index : maturity_index + 2] == ["--required-maturity", "planned"]


def test_failed_command_writes_missing_diagnostic_reports_and_exports_fixture_roots(tmp_path: Path) -> None:
    """A startup failure must retain diagnostics and discover only the verified fixture."""
    module = _load_gate_module()
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    json_report = tmp_path / "reports" / "evidence.json"
    markdown_report = tmp_path / "reports" / "evidence.md"
    observed_environment: dict[str, str] = {}

    observed = module.run_evidence_command(
        module.EvidenceRequest(
            repo_root=tmp_path,
            selection=("--base-ref", "origin/dev"),
            output_path=json_report,
            summary_path=markdown_report,
        ),
        fixture,
        command_runner=lambda _arguments, environment: (observed_environment.update(environment), 1)[1],
    )

    assert observed == 1
    assert observed_environment["SPECFACT_MODULES_REPO"] == str(fixture.resolve())
    assert observed_environment["SPECFACT_MODULES_ROOTS"] == str((fixture / "packages").resolve())
    assert json.loads(json_report.read_text(encoding="utf-8"))["verdict"] == "failed"
    assert "Requirements evidence unavailable" in markdown_report.read_text(encoding="utf-8")


def test_main_rejects_invalid_fixture_before_command_execution_and_writes_diagnostics(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """CLI execution must fail closed before delegating an invalid fixture."""
    module = _load_gate_module()
    (tmp_path / "ci").mkdir()
    (tmp_path / "ci" / "module-fixture.lock.json").write_text(
        json.dumps({"repository": "example/other", "commit": "2438372f8e34c96d4e474afa4c66c92a9cee7979"}),
        encoding="utf-8",
    )
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    json_report = tmp_path / "evidence.json"
    markdown_report = tmp_path / "evidence.md"
    json_report.write_text('{"verdict":"passed"}\n', encoding="utf-8")
    markdown_report.write_text("## Previous passing evidence\n", encoding="utf-8")
    invoked = False

    def _unexpected_command(*_args: object, **_kwargs: object) -> int:
        nonlocal invoked
        invoked = True
        return 0

    monkeypatch.setenv("SPECFACT_MODULES_REPO", str(fixture))
    monkeypatch.setattr(module, "run_evidence_command", _unexpected_command)

    with pytest.raises(SystemExit):
        module.main(
            [
                "--repo-root",
                str(tmp_path),
                "--staged",
                "--output",
                str(json_report),
                "--summary",
                str(markdown_report),
            ]
        )

    assert not invoked
    assert json.loads(json_report.read_text(encoding="utf-8"))["verdict"] == "failed"
    assert "must target nold-ai/specfact-cli-modules" in markdown_report.read_text(encoding="utf-8")
    assert "Previous passing evidence" not in markdown_report.read_text(encoding="utf-8")


@pytest.mark.parametrize("selection", [("--staged",), ("--base-ref", "origin/dev")])
def test_main_forwards_selection_and_verified_fixture(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, selection: tuple[str, ...]
) -> None:
    """CLI boundary must delegate the caller selection only after fixture verification."""
    module = _load_gate_module()
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        module,
        "_read_fixture_lock",
        lambda _repo_root: {
            "repository": "nold-ai/specfact-cli-modules",
            "commit": "2438372f8e34c96d4e474afa4c66c92a9cee7979",
        },
    )
    monkeypatch.setattr(module, "verify_fixture", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        module,
        "run_evidence_command",
        lambda request, fixture_root: captured.update({"request": request, "fixture_root": fixture_root}) or 0,
    )

    result = module.main(
        [
            "--repo-root",
            str(tmp_path),
            "--fixture-root",
            str(fixture),
            *selection,
            "--output",
            str(tmp_path / "evidence.json"),
            "--summary",
            str(tmp_path / "evidence.md"),
        ]
    )

    request = cast(CapturedRequest, captured["request"])
    assert result == 0
    assert captured["fixture_root"] == fixture.resolve()
    assert request.selection == (("--staged", None) if selection == ("--staged",) else ("--base-ref", "origin/dev"))
    assert request.required_maturity == "planned"


def test_pre_commit_places_evidence_before_review_and_contracts() -> None:
    """A red evidence verdict must stop later Block 2 gates."""
    pre_commit = (REPO_ROOT / "scripts" / "pre-commit-quality-checks.sh").read_text(encoding="utf-8")

    assert "run_requirements_evidence_gate" in pre_commit
    block2 = pre_commit[pre_commit.index("run_block2() {") : pre_commit.index("run_all() {")]
    assert block2.index("run_requirements_evidence_gate") < block2.index("run_code_review_gate")
    assert block2.index("run_requirements_evidence_gate") < block2.index("run_contract_tests_visible")
    assert ".specfact/reports/requirements-evidence" in pre_commit
