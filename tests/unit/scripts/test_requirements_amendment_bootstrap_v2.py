"""Amendment bootstrap regressions for raw run outcome integrity."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from types import ModuleType
from typing import cast


REPO_ROOT = Path(__file__).resolve().parents[3]
BOOTSTRAP_SCRIPT = REPO_ROOT / "scripts" / "requirements_amendment_bootstrap.py"


def _load_bootstrap_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("requirements_amendment_bootstrap_v2", BOOTSTRAP_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _plan_report() -> dict[str, object]:
    mapping_digest = f"sha256:{'a' * 64}"
    plan_digest = f"sha256:{'b' * 64}"
    cases = [
        {"method": "test", "node_id": "tests/test_proof.py::test_pass"},
        {"method": "test", "node_id": "tests/test_proof.py::test_fail"},
    ]
    return {
        "gate_decision": "pass",
        "observed_maturity": "test-authored",
        "mapping_digest": mapping_digest,
        "plan": {"cases": cases, "mapping_digest": mapping_digest, "plan_digest": plan_digest},
    }


def _raw_junit(path: Path) -> None:
    path.write_text(
        """<testsuite tests="2" failures="1">
<testcase><properties>
<property name="specfact.selector" value="tests/test_proof.py::test_pass"/>
<property name="specfact.runner" value="pytest"/>
<property name="specfact.python" value="3.12"/>
<property name="specfact.pytest" value="9.1"/>
</properties></testcase>
<testcase><properties>
<property name="specfact.selector" value="tests/test_proof.py::test_fail"/>
<property name="specfact.runner" value="pytest"/>
<property name="specfact.python" value="3.12"/>
<property name="specfact.pytest" value="9.1"/>
</properties><failure/></testcase>
</testsuite>""",
        encoding="utf-8",
    )


def test_v2_bootstrap_derives_red_subset_from_raw_case_outcomes(tmp_path: Path) -> None:
    """A diagnostic report cannot relabel a passing raw testcase as failed."""
    module = _load_bootstrap_module()
    red_root = tmp_path / "red"
    green_root = tmp_path / "green"
    red_root.mkdir()
    green_root.mkdir()
    (red_root / "requirements-evidence.json").write_text(
        json.dumps({"schema_version": 1, "verdict": "failed", "diagnostic": "stale-red-proof"}),
        encoding="utf-8",
    )
    plan = _plan_report()
    (red_root / "requirements-evidence-plan.json").write_text(json.dumps(plan), encoding="utf-8")
    _raw_junit(red_root / "requirements-proof.xml")
    for root in (green_root,):
        for name in ("requirements-evidence.json", "requirements-evidence-plan.json"):
            (root / name).write_text("{}", encoding="utf-8")
        (root / "requirements-proof.xml").write_text("<testsuite/>", encoding="utf-8")
    for name in ("red-run.json", "red-artifacts.json", "green-run.json", "green-artifacts.json"):
        (tmp_path / name).write_text("{}", encoding="utf-8")
    authority = {
        "mapping_digest": plan["mapping_digest"],
        "plan_digest": cast(dict[str, object], plan["plan"])["plan_digest"],
        "red_commit": "c" * 40,
        "expected_failed_cases": 1,
        "expected_passing_cases": 1,
        "cycle_selector_digest": (
            "sha256:"
            + hashlib.sha256(
                json.dumps(["tests/test_proof.py::test_fail"], sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
        ),
        "report_digest": f"sha256:{'c' * 64}",
        "junit_digest": f"sha256:{'d' * 64}",
    }
    module.__dict__["_authority"] = lambda *_arguments, **_keywords: authority
    module.__dict__["_metadata_matches"] = lambda *_arguments: True
    output = tmp_path / "output" / "red.json"
    arguments = argparse.Namespace(
        comment=tmp_path / "comment.json",
        comment_id=5464938148,
        red_run=tmp_path / "red-run.json",
        red_artifacts=tmp_path / "red-artifacts.json",
        red_artifact_root=red_root,
        green_run=tmp_path / "green-run.json",
        green_artifacts=tmp_path / "green-artifacts.json",
        green_artifact_root=green_root,
        repo_root=tmp_path,
        repository="nold-ai/specfact-cli",
        issue=692,
        change_id="fix-release-promotion-security-gates",
        pull_request=698,
        head_branch="codex/692-computed-owner-red-proof-v2",
        base_ref="origin/dev",
        final_ref="d" * 40,
        output=output,
        authority_output=None,
    )

    module.normalize(arguments)

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["execution_proof"]["selectors"] == ["tests/test_proof.py::test_fail"]
    normalized = ET.parse(output.with_suffix(".xml")).getroot().findall(".//testcase")
    assert len(normalized) == 1
    selector = normalized[0].find("./properties/property[@name='specfact.selector']")
    assert selector is not None and selector.get("value") == "tests/test_proof.py::test_fail"
    assert normalized[0].find("failure") is not None


def test_v3_bootstrap_accepts_only_the_exact_stale_producer_boundary(tmp_path: Path) -> None:
    """V3 bypasses only the stale producer verdict while retaining raw outcome proof."""
    module = _load_bootstrap_module()
    plan = _plan_report()
    green_junit = tmp_path / "green.xml"
    green_junit.write_text(
        """<testsuite tests="2" failures="0">
<testcase><properties><property name="specfact.selector" value="tests/test_proof.py::test_pass"/></properties></testcase>
<testcase><properties><property name="specfact.selector" value="tests/test_proof.py::test_fail"/></properties></testcase>
</testsuite>""",
        encoding="utf-8",
    )
    red_junit = tmp_path / "red.xml"
    _raw_junit(red_junit)
    stale_report = {
        "schema_version": 1,
        "verdict": "failed",
        "diagnostic": "Red proof provenance rejected: stale-red-proof",
    }
    authority = {
        "authority_version": 3,
        "producer_bypass": "stale-red-proof-only",
        "prior_green_report_diagnostic": stale_report["diagnostic"],
        "red_report_diagnostic": stale_report["diagnostic"],
        "expected_failed_cases": 1,
        "expected_passing_cases": 1,
        "prior_green_expected_passing_cases": 2,
    }
    green_report = tmp_path / "green.json"
    green_plan = tmp_path / "green-plan.json"
    red_report = tmp_path / "red.json"
    red_plan = tmp_path / "red-plan.json"
    for path, payload in (
        (green_report, stale_report),
        (green_plan, plan),
        (red_report, stale_report),
        (red_plan, plan),
    ):
        path.write_text(json.dumps(payload), encoding="utf-8")
    files = module._ArtifactFiles(red_report, red_junit, red_plan, green_report, green_junit, green_plan)

    assert module._stale_producer_evidence_matches(authority, files)

    tampered = {**stale_report, "diagnostic": "Red proof provenance rejected: another-reason"}
    green_report.write_text(json.dumps(tampered), encoding="utf-8")
    assert not module._stale_producer_evidence_matches(authority, files)
    green_report.write_text(json.dumps(stale_report), encoding="utf-8")

    skipped = green_junit.read_text(encoding="utf-8").replace(
        "</properties></testcase>", "</properties><skipped/></testcase>", 1
    )
    green_junit.write_text(skipped, encoding="utf-8")
    assert not module._stale_producer_evidence_matches(authority, files)
    green_junit.write_text(skipped.replace("<skipped/>", "", 1), encoding="utf-8")
    red_junit.write_text(
        red_junit.read_text(encoding="utf-8").replace("<failure/>", "<skipped/>", 1),
        encoding="utf-8",
    )
    assert not module._stale_producer_evidence_matches(authority, files)

    wrong_version = {**authority, "authority_version": 2}
    assert not module._stale_producer_evidence_matches(wrong_version, files)
    wrong_bypass = {**authority, "producer_bypass": "anything-else"}
    assert not module._stale_producer_evidence_matches(wrong_bypass, files)

    old_comment = {
        "id": module.APPROVED_BOOTSTRAP_LOCATOR["comment_id"],
        "issue_url": "https://api.github.com/repos/nold-ai/specfact-cli/issues/692",
        "author_association": "MEMBER",
        "created_at": "2026-08-30T10:14:02Z",
        "updated_at": "2026-08-30T10:14:02Z",
        "user": {"login": "djm81"},
        "body": "SPECFACT_REQUIREMENTS_AMENDMENT_BOOTSTRAP_V2\n" + json.dumps({"signer_login": "djm81"}),
    }
    comment_path = tmp_path / "comment.json"
    comment_path.write_text(json.dumps(old_comment), encoding="utf-8")
    try:
        module._authority(
            comment_path,
            comment_id=module.APPROVED_BOOTSTRAP_LOCATOR["comment_id"],
            repository="nold-ai/specfact-cli",
            issue=692,
        )
    except ValueError as error:
        assert str(error) == "amendment-bootstrap-invalid"
    else:
        raise AssertionError("superseded V2 authority was accepted")
