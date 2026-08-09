"""Contract tests for the immutable Requirements evidence delivery adapter."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast

import pytest

from tests.unit.scripts.requirements_change_support import runtime_proof_change_root


REPO_ROOT = Path(__file__).resolve().parents[3]
GATE_SCRIPT = REPO_ROOT / "scripts" / "requirements_evidence_delivery_gate.py"
APPROVED_MODULE_COMMIT = "69f075819be5e1ceca1446b026b0417f19e584ca"
APPROVED_MODULE_TREE = "5d0b8e66c6cd467e6b1ad9d582e24c66b907e205"


class CapturedRequest(Protocol):
    """Minimal assertion surface retained from a delegated evidence request."""

    selection: tuple[str, str | None]
    required_maturity: str


class GateModule(Protocol):
    """Typed public surface supplied by the file-loaded delivery adapter."""

    EvidenceRequest: Callable[..., CapturedRequest]
    subprocess: ModuleType

    def _git_head(self, arguments: list[str]) -> str:
        raise NotImplementedError

    def verify_fixture(self, fixture: dict[str, object], fixture_root: Path, *, git_runner: Callable[..., str]) -> None:
        pass

    def run_evidence_command(
        self, request: CapturedRequest, fixture_root: Path, *, command_runner: Callable[..., int] = ...
    ) -> int:
        raise NotImplementedError

    def main(self, argv: list[str]) -> int:
        raise NotImplementedError


def _load_gate_module() -> GateModule:
    spec = importlib.util.spec_from_file_location("requirements_evidence_delivery_gate", GATE_SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("Requirements evidence delivery adapter must be importable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast(GateModule, module)


def _git_output(repo_root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


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
            {"repository": "example/other", "commit": APPROVED_MODULE_COMMIT},
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
                "commit": APPROVED_MODULE_COMMIT,
                "tree": APPROVED_MODULE_TREE,
            },
            tmp_path,
            git_runner=lambda arguments: (
                APPROVED_MODULE_COMMIT
                if arguments[-2:] == ["rev-parse", "HEAD"]
                else APPROVED_MODULE_TREE
                if arguments[-2:] == ["rev-parse", "HEAD^{tree}"]
                else " M package.py\n"
            ),
        )

    with pytest.raises(ValueError, match="tree attestation"):  # type: ignore[reportUnknownMemberType]
        module.verify_fixture(
            {
                "repository": "nold-ai/specfact-cli-modules",
                "commit": APPROVED_MODULE_COMMIT,
                "tree": "0" * 40,
            },
            tmp_path,
            git_runner=lambda arguments: (
                APPROVED_MODULE_COMMIT if arguments[-2:] == ["rev-parse", "HEAD"] else APPROVED_MODULE_TREE
            ),
        )


def test_fixture_git_lookup_ignores_commit_hook_worktree_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """The supplied fixture path must win over Git's commit-hook environment."""
    module = _load_gate_module()
    captured_environment: dict[str, str] = {}

    def git_run(_arguments: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        environment = kwargs["env"]
        assert isinstance(environment, dict)
        captured_environment.update(environment)
        return subprocess.CompletedProcess([], 0, stdout=f"{APPROVED_MODULE_COMMIT}\n")

    monkeypatch.setenv("GIT_DIR", "/unrelated/commit-worktree.git")
    monkeypatch.setenv("GIT_WORK_TREE", "/unrelated/commit-worktree")
    monkeypatch.setattr(module.subprocess, "run", git_run)

    assert module._git_head(["git", "-C", "/fixture", "rev-parse", "HEAD"]).startswith("69f07581")
    assert "GIT_DIR" not in captured_environment
    assert "GIT_WORK_TREE" not in captured_environment


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
    assert captured_arguments[:3] == [sys.executable, "-m", "specfact_cli"]
    maturity_index = captured_arguments.index("--required-maturity")
    assert captured_arguments[maturity_index : maturity_index + 2] == ["--required-maturity", "planned"]


def test_delegated_command_forwards_accepted_maturity_and_proof_inputs(tmp_path: Path) -> None:
    """CI can request accepted planning without the adapter inventing review evidence."""
    module = _load_gate_module()
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    review_evidence = tmp_path / "review-evidence.json"
    review_evidence.write_text('{"decision":"accepted"}\n', encoding="utf-8")
    plan_output = tmp_path / "plan.json"
    captured_arguments: list[str] = []
    request = module.EvidenceRequest(
        repo_root=tmp_path,
        selection=("--base-ref", "origin/dev"),
        output_path=tmp_path / "evidence.json",
        summary_path=tmp_path / "evidence.md",
        required_maturity="accepted",
        review_evidence=review_evidence,
        plan_output=plan_output,
    )

    assert (
        module.run_evidence_command(
            request,
            fixture,
            command_runner=lambda arguments, _environment: captured_arguments.extend(arguments) or 0,
        )
        == 0
    )
    assert captured_arguments[captured_arguments.index("--required-maturity") + 1] == "accepted"
    assert captured_arguments[captured_arguments.index("--review-evidence") + 1] == str(review_evidence)
    assert captured_arguments[captured_arguments.index("--plan-output") + 1] == str(plan_output)


def test_failed_command_writes_missing_diagnostic_reports_and_exports_fixture_roots(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A startup failure must retain diagnostics and discover only the verified fixture."""
    module = _load_gate_module()
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    json_report = tmp_path / "reports" / "evidence.json"
    markdown_report = tmp_path / "reports" / "evidence.md"
    observed_environment: dict[str, str] = {}
    monkeypatch.setenv("PATH", os.environ["PATH"])
    monkeypatch.setenv("SPECFACT_TEST_SECRET", "must-not-leak")

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
    assert observed_environment["PATH"] == os.environ["PATH"]
    assert "SPECFACT_TEST_SECRET" not in observed_environment
    assert json.loads(json_report.read_text(encoding="utf-8"))["verdict"] == "failed"
    assert "Requirements evidence unavailable" in markdown_report.read_text(encoding="utf-8")


def test_main_rejects_invalid_fixture_before_command_execution_and_writes_diagnostics(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """CLI execution must fail closed before delegating an invalid fixture."""
    module = _load_gate_module()
    (tmp_path / "ci").mkdir()
    (tmp_path / "ci" / "module-fixture.lock.json").write_text(
        json.dumps({"repository": "example/other", "commit": APPROVED_MODULE_COMMIT}),
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


def test_released_evidence_publishes_a_bounded_no_impact_pull_request_decision(tmp_path: Path) -> None:
    """A docs-only pull-request diff must retain the released module's explicit skip report."""
    fixture_root_text = os.environ.get("SPECFACT_MODULES_REPO")
    if fixture_root_text is None:
        pytest.skip("requires the pinned modules fixture")
    fixture_root = Path(fixture_root_text)
    if not fixture_root.is_dir():
        pytest.skip("requires the pinned modules fixture")
    module = _load_gate_module()
    _git_output(tmp_path, "init")
    _git_output(tmp_path, "config", "user.email", "requirements@example.test")
    _git_output(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "README.md").write_text("# proof\n", encoding="utf-8")
    _git_output(tmp_path, "add", ".")
    _git_output(tmp_path, "commit", "--no-gpg-sign", "-m", "chore: base")
    base_ref = _git_output(tmp_path, "rev-parse", "HEAD")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("# guide\n", encoding="utf-8")
    _git_output(tmp_path, "add", ".")
    _git_output(tmp_path, "commit", "--no-gpg-sign", "-m", "docs: add guide")
    output_path = tmp_path / "evidence.json"
    summary_path = tmp_path / "evidence.md"

    assert (
        module.run_evidence_command(
            module.EvidenceRequest(
                repo_root=tmp_path,
                selection=("--base-ref", base_ref),
                output_path=output_path,
                summary_path=summary_path,
            ),
            fixture_root,
        )
        == 0
    )
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["verdict"] == "skipped"
    assert report["gate_decision"] == "pass"
    assert report["observed_maturity"] == "no-impact"
    assert report["delivery_status"] == "no-impact"
    assert report["sources"] == []
    assert "no-impact" in summary_path.read_text(encoding="utf-8")


def _pinned_fixture_root() -> Path:
    """Return the released fixture required for empirical Requirements tests."""
    fixture_root_text = os.environ.get("SPECFACT_MODULES_REPO")
    if fixture_root_text is None:
        pytest.skip("requires the pinned modules fixture")
    fixture_root = Path(fixture_root_text)
    if not fixture_root.is_dir():
        pytest.skip("requires the pinned modules fixture")
    return fixture_root


def _initialize_evidence_repository(repo_root: Path) -> None:
    """Create an isolated Git repository accepted by the released selector logic."""
    _git_output(repo_root, "init")
    _git_output(repo_root, "config", "user.email", "requirements@example.test")
    _git_output(repo_root, "config", "user.name", "Requirements proof")


def test_released_evidence_rejects_stale_acceptance(tmp_path: Path) -> None:
    """Released evidence rejects an accepted record whose mapping digest is stale."""
    fixture_root = _pinned_fixture_root()
    module = _load_gate_module()
    change_root = tmp_path / "openspec" / "changes" / "requirements-07-runtime-proof-delivery"
    change_root.parent.mkdir(parents=True)
    shutil.copytree(runtime_proof_change_root(REPO_ROOT), change_root)
    _initialize_evidence_repository(tmp_path)
    _git_output(tmp_path, "add", ".")
    _git_output(tmp_path, "commit", "--no-gpg-sign", "-m", "chore: base")
    sidecar = change_root / "requirements-evidence.yaml"
    sidecar.write_text(sidecar.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    _git_output(tmp_path, "add", "--", str(sidecar.relative_to(tmp_path)))
    review_evidence = tmp_path / "review-evidence.json"
    review_evidence.write_text(
        json.dumps(
            {
                "decision": "accepted",
                "reviewer_id": "owner@example.test",
                "reviewer_role": "product-owner",
                "recorded_at": "2026-08-07T00:00:00Z",
                "reference": "review:663",
                "mapping_digest": f"sha256:{'0' * 64}",
            }
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "evidence.json"

    assert (
        module.run_evidence_command(
            module.EvidenceRequest(
                repo_root=tmp_path,
                selection=("--staged", None),
                output_path=output_path,
                summary_path=tmp_path / "evidence.md",
                required_maturity="accepted",
                review_evidence=review_evidence,
            ),
            fixture_root,
        )
        == 1
    )
    assert "acceptance-stale" in json.loads(output_path.read_text(encoding="utf-8"))["sources"][0]["findings"]


def test_released_evidence_publishes_a_bounded_staged_no_impact_decision(tmp_path: Path) -> None:
    """A staged docs-only diff receives the released no-impact report, not a silent skip."""
    fixture_root = _pinned_fixture_root()
    module = _load_gate_module()
    _initialize_evidence_repository(tmp_path)
    (tmp_path / "README.md").write_text("# proof\n", encoding="utf-8")
    _git_output(tmp_path, "add", ".")
    _git_output(tmp_path, "commit", "--no-gpg-sign", "-m", "chore: base")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("# guide\n", encoding="utf-8")
    _git_output(tmp_path, "add", "--", "docs/guide.md")
    output_path = tmp_path / "evidence.json"

    assert (
        module.run_evidence_command(
            module.EvidenceRequest(
                repo_root=tmp_path,
                selection=("--staged", None),
                output_path=output_path,
                summary_path=tmp_path / "evidence.md",
            ),
            fixture_root,
        )
        == 0
    )
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["verdict"] == "skipped"
    assert report["observed_maturity"] == "no-impact"
    assert report["sources"] == []


def test_released_reconciliation_marks_incomplete_junit_unverified(tmp_path: Path) -> None:
    """A released reconciler must reject skipped proof output as incomplete red evidence."""
    fixture_root = _pinned_fixture_root()
    requirements_source = str(fixture_root / "packages" / "specfact-requirements" / "src")
    sys.path.insert(0, requirements_source)
    try:
        from specfact_requirements.requirements.lifecycle import evaluate_mapping, reconcile_junit
    finally:
        sys.path.remove(requirements_source)

    selector = "tests/test_readiness.py::test_unavailable"
    mapping = {
        "schema_version": "2",
        "requirements": {
            "REQ-001": {
                "rationale": "Operators need a reliable readiness decision.",
                "stakeholder_refs": ["issue:663"],
                "touchpoints": [{"id": "readiness", "kind": "cli_command", "locator": "specfact readiness"}],
                "verification_cases": [
                    {
                        "case_id": "REQ-001-S01",
                        "scenario_id": "unavailable",
                        "method": "test",
                        "intent": "Report unavailable dependencies.",
                        "observable": "Structured readiness result and exit code.",
                        "selector": {"runner": "pytest", "node_id": selector},
                    }
                ],
            }
        },
    }
    planned = evaluate_mapping(mapping, required_maturity="planned")
    plan = evaluate_mapping(
        mapping,
        required_maturity="test-authored",
        review_evidence={
            "decision": "accepted",
            "reviewer_id": "owner@example.test",
            "reviewer_role": "product-owner",
            "recorded_at": "2026-08-07T00:00:00Z",
            "reference": "review:663",
            "mapping_digest": planned["mapping_digest"],
        },
    )
    junit = tmp_path / "skipped.xml"
    junit.write_text(
        f'<testsuite><testcase><properties><property name="specfact.selector" value="{selector}"/></properties><skipped/></testcase></testsuite>',
        encoding="utf-8",
    )

    report = reconcile_junit(plan, junit, run_stage="red", source_ref="a" * 40)

    assert report["gate_decision"] == "fail"
    assert report["observed_maturity"] == "incomplete"
    assert f"red-proof-skipped-not-failed:{selector}" in report["findings"]


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
            "commit": APPROVED_MODULE_COMMIT,
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


def test_pre_commit_treats_delivery_inputs_as_production() -> None:
    """Staged dependency and packaging inputs must require production maturity."""
    pre_commit = (REPO_ROOT / "scripts" / "pre-commit-quality-checks.sh").read_text(encoding="utf-8")

    assert "pyproject.toml|setup.py|uv.lock|requirements/ci/locked.txt" in pre_commit
    assert (
        "resources/templates/*|resources/schemas/*|resources/mappings/*|resources/keys/*|modules/bundle-mapper/*"
        in pre_commit
    )
    assert ".github/*|ci/*|scripts/*|src/*|tools/*" in pre_commit
