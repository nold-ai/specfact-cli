"""Contract coverage for Git-bound Requirements red-proof provenance."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Protocol, cast

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
PROVENANCE_SCRIPT = REPO_ROOT / "scripts" / "requirements_proof_provenance.py"


class ProvenanceModule(Protocol):
    """Minimal public surface for validating a committed red-proof report."""

    def bind_red_proof(self, red_proof_path: Path, repo_root: Path, *, base_ref: str) -> None:
        raise NotImplementedError

    def validate_prior_red_proof(
        self, red_proof_path: Path, repo_root: Path, *, base_ref: str, final_ref: str
    ) -> list[str]:
        raise NotImplementedError

    def _validate_red_history_freshness(
        self,
        report: dict[str, object],
        repo_root: Path,
        *boundary_values: object,
    ) -> list[str]:
        raise NotImplementedError


def _load_provenance_module() -> ProvenanceModule:
    spec = importlib.util.spec_from_file_location("requirements_proof_provenance", PROVENANCE_SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("Requirements proof provenance validator must be importable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast(ProvenanceModule, module)


def _git(repo_root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _commit(repo_root: Path, message: str) -> str:
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "--no-gpg-sign", "-m", message)
    return _git(repo_root, "rev-parse", "HEAD")


def _empty_commit(repo_root: Path, message: str) -> str:
    _git(repo_root, "commit", "--allow-empty", "--no-gpg-sign", "-m", message)
    return _git(repo_root, "rev-parse", "HEAD")


def _red_proof(
    source_ref: str,
    junit_digest: str,
    *,
    source_tree: str,
    merge_base: str,
    test_file_digest: str,
) -> dict[str, object]:
    mapping_digest = f"sha256:{'a' * 64}"
    plan_digest = f"sha256:{'b' * 64}"
    touchpoints = [{"id": "selected-test", "kind": "test_file", "locator": "tests/test_proof.py"}]
    return {
        "gate_decision": "pass",
        "observed_maturity": "red",
        "mapping_digest": mapping_digest,
        "plan_digest": plan_digest,
        "plan": {
            "mapping_digest": mapping_digest,
            "plan_digest": plan_digest,
            "cases": [
                {
                    "requirement_id": "openspec:test:capability:requirement",
                    "case_id": "CASE-S01",
                    "touchpoints": touchpoints,
                }
            ],
        },
        "execution_proof": {
            "run_stage": "red",
            "source_ref": source_ref,
            "source_tree": source_tree,
            "merge_base": merge_base,
            "selectors": ["tests/test_proof.py::test_selected"],
            "test_file_digests": {"tests/test_proof.py": test_file_digest},
            "mutable_sut_paths": [],
            "junit_digest": junit_digest,
            "toolchain_identity": {"runner": "pytest", "python": "3.12", "pytest": "9.1"},
        },
    }


def _write_red_proof(
    path: Path,
    repo_root: Path,
    source_ref: str,
    merge_base: str,
) -> None:
    junit = (
        b'<testsuite><testcase><properties><property name="specfact.selector" '
        b'value="tests/test_proof.py::test_selected"/>'
        b'<property name="specfact.runner" value="pytest"/>'
        b'<property name="specfact.python" value="3.12"/>'
        b'<property name="specfact.pytest" value="9.1"/>'
        b"</properties><failure/></testcase></testsuite>"
    )
    path.with_suffix(".xml").write_bytes(junit)
    digest = f"sha256:{hashlib.sha256(junit).hexdigest()}"
    source_tree = _git(repo_root, "rev-parse", f"{source_ref}^{{tree}}")
    test_payload = subprocess.run(
        ["git", "show", f"{source_ref}:tests/test_proof.py"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    ).stdout
    test_file_digest = f"sha256:{hashlib.sha256(test_payload).hexdigest()}"
    report = _red_proof(
        source_ref,
        digest,
        source_tree=source_tree,
        merge_base=merge_base,
        test_file_digest=test_file_digest,
    )
    path.write_text(json.dumps(report), encoding="utf-8")


def _write_unbound_red_proof(path: Path, source_ref: str) -> None:
    """Write the exact incomplete report shape produced by released reconciliation."""
    selector = "tests/test_proof.py::test_selected"
    junit = (
        "<testsuite><testcase><properties>"
        f'<property name="specfact.selector" value="{selector}"/>'
        '<property name="specfact.runner" value="pytest"/>'
        '<property name="specfact.python" value="3.13.7"/>'
        '<property name="specfact.pytest" value="8.4.1"/>'
        "</properties><failure/></testcase></testsuite>"
    ).encode()
    path.with_suffix(".xml").write_bytes(junit)
    mapping_digest = f"sha256:{'a' * 64}"
    plan_digest = f"sha256:{'b' * 64}"
    touchpoints = [{"id": "selected-test", "kind": "test_file", "locator": "tests/test_proof.py"}]
    path.write_text(
        json.dumps(
            {
                "gate_decision": "pass",
                "observed_maturity": "red",
                "mapping_digest": mapping_digest,
                "plan_digest": plan_digest,
                "plan": {
                    "mapping_digest": mapping_digest,
                    "plan_digest": plan_digest,
                    "cases": [
                        {
                            "requirement_id": "openspec:test:capability:requirement",
                            "case_id": "CASE-S01",
                            "touchpoints": touchpoints,
                        }
                    ],
                },
                "execution_proof": {
                    "run_stage": "red",
                    "source_ref": source_ref,
                    "selectors": [selector],
                    "junit_digest": f"sha256:{hashlib.sha256(junit).hexdigest()}",
                },
            }
        ),
        encoding="utf-8",
    )


def test_bind_red_proof_records_validator_complete_immutable_provenance(tmp_path: Path) -> None:
    """The producer must fill every validator-required fact from the red execution boundary."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "README.md").write_text("# proof\n", encoding="utf-8")
    delivery_path = tmp_path / "src" / "delivery.py"
    delivery_path.parent.mkdir()
    delivery_path.write_text("VALUE = 0\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "chore: base")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_unbound_red_proof(red_proof_path, red_ref)

    module.bind_red_proof(red_proof_path, tmp_path, base_ref=base_ref)

    report = json.loads(red_proof_path.read_text(encoding="utf-8"))
    execution_proof = report["execution_proof"]
    assert execution_proof["source_tree"] == _git(tmp_path, "rev-parse", f"{red_ref}^{{tree}}")
    assert execution_proof["merge_base"] == base_ref
    assert execution_proof["test_file_digests"] == {
        "tests/test_proof.py": f"sha256:{hashlib.sha256(test_path.read_bytes()).hexdigest()}"
    }
    assert execution_proof["toolchain_identity"] == {
        "runner": "pytest",
        "python": "3.13.7",
        "pytest": "8.4.1",
    }
    assert execution_proof["mutable_sut_paths"] == []

    final_ref = _empty_commit(tmp_path, "chore: retain immutable proof")
    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


def test_git_bound_red_proof_requires_test_only_ancestor_and_unchanged_selector_files(tmp_path: Path) -> None:
    """Only an ancestor red report with unchanged selected tests may reach reconciliation."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "README.md").write_text("# proof\n", encoding="utf-8")
    delivery_path = tmp_path / "src" / "delivery.py"
    delivery_path.parent.mkdir()
    delivery_path.write_text("VALUE = 0\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "chore: base")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    final_ref = _empty_commit(tmp_path, "chore: retain immutable proof")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []

    test_path.write_text("def test_selected() -> None: assert True\n", encoding="utf-8")
    stale_ref = _commit(tmp_path, "test: change selector")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=stale_ref) == [
        "stale-red-proof"
    ]


def test_exact_producer_authority_is_separate_from_mutable_sut_policy(tmp_path: Path) -> None:
    """Only the exact externally authenticated producer path may cross red."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "README.md").write_text("# proof\n", encoding="utf-8")
    producer_path = tmp_path / "scripts" / "requirements_proof_provenance.py"
    producer_path.parent.mkdir()
    producer_path.write_text("VALUE = 'red'\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "chore: base")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    report = json.loads(red_proof_path.read_text(encoding="utf-8"))

    producer_path.write_text("VALUE = 'green'\n", encoding="utf-8")
    producer_ref = _commit(tmp_path, "fix: update exact producer")
    producer_paths = frozenset({"scripts/requirements_proof_provenance.py"})

    assert (
        module._validate_red_history_freshness(
            report,
            tmp_path,
            base_ref,
            red_ref,
            producer_ref,
            None,
            producer_paths,
        )
        == []
    )

    selected_producer_report = json.loads(json.dumps(report))
    selected_producer_report["execution_proof"]["selectors"] = [
        "scripts/requirements_proof_provenance.py::test_selected"
    ]
    assert module._validate_red_history_freshness(
        selected_producer_report,
        tmp_path,
        base_ref,
        red_ref,
        producer_ref,
        None,
        producer_paths,
    ) == ["prior-red-proof-invalid"]

    alias_selector_report = json.loads(json.dumps(report))
    alias_selector_report["execution_proof"]["selectors"] = [
        "./scripts/requirements_proof_provenance.py::test_selected"
    ]
    with pytest.raises(ValueError, match="prior-red-proof-invalid"):
        module._validate_red_history_freshness(
            alias_selector_report,
            tmp_path,
            base_ref,
            red_ref,
            producer_ref,
            None,
            producer_paths,
        )

    for test_touchpoint in (
        "scripts/requirements_proof_provenance.py",
        "./scripts/requirements_proof_provenance.py",
    ):
        test_touchpoint_report = json.loads(json.dumps(report))
        test_touchpoint_report["plan"]["cases"][0]["touchpoints"].append(
            {
                "id": "producer-as-test-input",
                "kind": "test_file",
                "locator": test_touchpoint,
            }
        )
        assert module._validate_red_history_freshness(
            test_touchpoint_report,
            tmp_path,
            base_ref,
            red_ref,
            producer_ref,
            None,
            producer_paths,
        ) == ["prior-red-proof-invalid"]

    adjacent_path = tmp_path / "docs" / "adjacent.md"
    adjacent_path.parent.mkdir()
    adjacent_path.write_text("not authorized\n", encoding="utf-8")
    adjacent_ref = _commit(tmp_path, "docs: add adjacent path")

    assert module._validate_red_history_freshness(
        report,
        tmp_path,
        base_ref,
        red_ref,
        adjacent_ref,
        None,
        producer_paths,
    ) == ["stale-red-proof"]

    for unauthorized_producer in (
        "src/specfact_cli/delivery.py",
        "scripts/requirements_unlisted_plugin.py",
    ):
        assert module._validate_red_history_freshness(
            report,
            tmp_path,
            base_ref,
            red_ref,
            adjacent_ref,
            None,
            frozenset({unauthorized_producer}),
        ) == ["prior-red-proof-invalid"]


@pytest.mark.parametrize("support_path", ["conftest.py", "tests/conftest.py"])
def test_git_bound_red_proof_rejects_changed_applicable_conftest(tmp_path: Path, support_path: str) -> None:
    """A fixture or hook change must invalidate an earlier selected-test failure."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    conftest_path = tmp_path / support_path
    conftest_path.parent.mkdir(parents=True, exist_ok=True)
    conftest_path.write_text("VALUE = 'red'\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add pytest support")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir(exist_ok=True)
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    conftest_path.write_text("VALUE = 'green'\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change pytest support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_rejects_changed_imported_test_support(tmp_path: Path) -> None:
    """A changed imported helper must invalidate an earlier selected-test failure."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    helper_path = tmp_path / "tests" / "support.py"
    helper_path.parent.mkdir(parents=True)
    helper_path.write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add pytest support")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.write_text(
        "from tests.support import VALUE\n\ndef test_selected() -> None: assert VALUE\n",
        encoding="utf-8",
    )
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    helper_path.write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change imported pytest support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


@pytest.mark.parametrize(
    ("support_path", "expected"),
    (
        ("tests/fixtures/expected.txt", ["stale-red-proof"]),
        ("docs/unrelated.md", ["stale-red-proof"]),
    ),
)
def test_git_bound_red_proof_tracks_non_python_test_support(
    tmp_path: Path, support_path: str, expected: list[str]
) -> None:
    """Every unapproved repository path remains frozen after red."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    support = tmp_path / support_path
    support.parent.mkdir(parents=True)
    support.write_text("red\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add support input")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir(exist_ok=True)
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    support.write_text("green\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: update support input")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == expected


def test_git_bound_red_proof_rejects_changed_support_imported_by_conftest(tmp_path: Path) -> None:
    """A helper reached through conftest must remain bound to the red failure."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    helper_path = tests_path / "support.py"
    helper_path.write_text("VALUE = False\n", encoding="utf-8")
    (tests_path / "conftest.py").write_text("from tests.support import VALUE\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add pytest support")
    test_path = tests_path / "test_proof.py"
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    helper_path.write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change conftest helper")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_rejects_changed_pytest_plugin(tmp_path: Path) -> None:
    """A repository-local pytest plugin must remain bound to the red failure."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    helpers_path = tests_path / "helpers"
    helpers_path.mkdir(parents=True)
    plugin_path = helpers_path / "fixtures.py"
    plugin_path.write_text("VALUE = False\n", encoding="utf-8")
    (tests_path / "conftest.py").write_text('pytest_plugins = ("tests.helpers.fixtures",)\n', encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add pytest plugin")
    test_path = tests_path / "test_proof.py"
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    plugin_path.write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change pytest plugin")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


@pytest.mark.parametrize(
    "declaration",
    [
        'plugin_key = "pytest_plugins"\nglobals()[plugin_key] = ("tests.helpers.fixtures",)\n',
        'class Plugins:\n    globals().update(pytest_plugins=("tests.helpers.fixtures",))\n',
        'class Plugins:\n    eval("globals().update(pytest_plugins=(\\"tests.helpers.fixtures\\",))")\n',
        'import builtins\nbuiltins.exec("pytest_plugins = (\\"tests.helpers.fixtures\\",)")\n',
        'for namespace in [globals()]:\n    namespace["pytest_plugins"] = ("tests.helpers.fixtures",)\n',
        'from contextlib import nullcontext\nwith nullcontext(globals()) as namespace:\n    namespace["pytest_plugins"] = ("tests.helpers.fixtures",)\n',
        'import builtins\nclass Plugins:\n    builtins.exec("global pytest_plugins; pytest_plugins = (\\"tests.helpers.fixtures\\",)")\n',
    ],
    ids=(
        "computed-module-key",
        "class-body-module-mutation",
        "class-body-indirect-execution",
        "qualified-builtins-execution",
        "compound-namespace-alias",
        "with-namespace-alias",
        "class-enclosing-executor-alias",
    ),
)
def test_git_bound_red_proof_rejects_dynamic_pytest_plugin_binding(tmp_path: Path, declaration: str) -> None:
    """Changed pytest support remains stale without interpreting its runtime behavior."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    helpers_path = tmp_path / "tests" / "helpers"
    helpers_path.mkdir(parents=True)
    plugin_path = helpers_path / "fixtures.py"
    plugin_path.write_text("VALUE = False\n", encoding="utf-8")
    (tmp_path / "tests" / "conftest.py").write_text(declaration, encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add dynamic pytest plugin")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    plugin_path.write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change dynamically bound pytest plugin")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_rejects_import_target_added_after_red(tmp_path: Path) -> None:
    """A missing local import added after red must invalidate collection-error proof."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "conftest.py").write_text("from tests.missing_support import VALUE\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add missing pytest support import")
    test_path = tests_path / "test_proof.py"
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "missing_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: add missing pytest support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_rejects_wholly_absent_import_target_added_after_red(tmp_path: Path) -> None:
    """A missing import remains bound even when its root package did not exist at red."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "conftest.py").write_text("from support.fixtures import VALUE\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add wholly missing pytest support import")
    test_path = tests_path / "test_proof.py"
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    support_path = tmp_path / "support"
    support_path.mkdir()
    (support_path / "fixtures.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: add missing root support package")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_rejects_changed_parent_package_initializer(tmp_path: Path) -> None:
    """Parent package initializers executed during import must remain bound to red."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    helpers_path = tmp_path / "tests" / "helpers"
    helpers_path.mkdir(parents=True)
    (tmp_path / "tests" / "__init__.py").write_text("VALUE = False\n", encoding="utf-8")
    (helpers_path / "__init__.py").write_text("", encoding="utf-8")
    (helpers_path / "fixtures.py").write_text("VALUE = False\n", encoding="utf-8")
    (tmp_path / "tests" / "conftest.py").write_text("from tests.helpers.fixtures import VALUE\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add packaged pytest support")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tmp_path / "tests" / "__init__.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change parent package initializer")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_rejects_added_parent_package_initializer(tmp_path: Path) -> None:
    """A namespace package cannot gain executable initialization after the red run."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    support_path = tmp_path / "support"
    support_path.mkdir()
    (support_path / "fixtures.py").write_text("VALUE = False\n", encoding="utf-8")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "conftest.py").write_text("from support.fixtures import VALUE\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add namespace-package support")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (support_path / "__init__.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: initialize support package")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_accepts_executable_regular_selector(tmp_path: Path) -> None:
    """An executable Git blob remains a regular pytest selector rather than a symlink."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "README.md").write_text("# proof\n", encoding="utf-8")
    feature_path = tmp_path / "src" / "feature.py"
    feature_path.parent.mkdir()
    feature_path.write_text("VALUE = 1\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "chore: base")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    _git(tmp_path, "add", "tests/test_proof.py")
    _git(tmp_path, "update-index", "--chmod=+x", "tests/test_proof.py")
    executable_ref = _commit(tmp_path, "test: add executable red selector")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, executable_ref, base_ref)
    final_ref = _empty_commit(tmp_path, "chore: retain executable red selector")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


def test_git_bound_red_proof_rejects_symlink_selector(tmp_path: Path) -> None:
    """A selector symlink must not hide mutable target bytes from provenance."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "README.md").write_text("# proof\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "chore: base")
    target = tmp_path / "tests" / "target.py"
    target.parent.mkdir()
    target.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    (tmp_path / "tests" / "test_proof.py").symlink_to("target.py")
    red_ref = _commit(tmp_path, "test: add symlink selector")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "delivery.md").write_text("final\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: final")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "prior-red-proof-invalid"
    ]


def test_git_bound_red_proof_rejects_unapproved_base_merge_after_red(tmp_path: Path) -> None:
    """A merge cannot introduce an unapproved path after the retained red source."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "README.md").write_text("# proof\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "chore: base")
    _git(tmp_path, "branch", "base-update")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    _git(tmp_path, "checkout", "base-update")
    (tmp_path / "base.md").write_text("updated\n", encoding="utf-8")
    _commit(tmp_path, "docs: update base")
    _git(tmp_path, "checkout", "master")
    _git(tmp_path, "merge", "--no-ff", "base-update", "-m", "merge: update base")
    final_ref = _git(tmp_path, "rev-parse", "HEAD")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_rejects_base_commit_as_red_source(tmp_path: Path) -> None:
    """The red source must be a new test-only commit after the pull-request base."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: base already contains failure")
    _git(tmp_path, "branch", "current-base", base_ref)
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, base_ref, base_ref)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(
        red_proof_path, tmp_path, base_ref="refs/heads/current-base", final_ref=final_ref
    ) == ["tdd-order-unproven"]


def _assert_renamed_governed_path_is_rejected(rename_root: Path, module: ProvenanceModule) -> None:
    """Exercise the rename-source half of the governed-history boundary."""
    rename_root.mkdir()
    _git(rename_root, "init")
    _git(rename_root, "config", "user.email", "requirements@example.test")
    _git(rename_root, "config", "user.name", "Requirements proof")
    (rename_root / "src").mkdir()
    (rename_root / "src" / "delivery.py").write_text("VALUE = 0\n", encoding="utf-8")
    rename_base_ref = _commit(rename_root, "chore: base")
    (rename_root / "docs").mkdir()
    _git(rename_root, "mv", "src/delivery.py", "docs/delivery.py")
    _commit(rename_root, "docs: relocate delivery notes")
    rename_test_path = rename_root / "tests" / "test_proof.py"
    rename_test_path.parent.mkdir()
    rename_test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    rename_red_ref = _commit(rename_root, "test: add red proof")
    rename_proof_path = rename_root / ".git" / "red.json"
    _write_red_proof(rename_proof_path, rename_root, rename_red_ref, rename_base_ref)
    (rename_root / "src").mkdir(exist_ok=True)
    (rename_root / "src" / "replacement.py").write_text("VALUE = 1\n", encoding="utf-8")
    rename_final_ref = _commit(rename_root, "feat: replace delivery")

    assert module.validate_prior_red_proof(
        rename_proof_path, rename_root, base_ref=rename_base_ref, final_ref=rename_final_ref
    ) == ["tdd-order-unproven"]


def test_git_bound_red_proof_rejects_replayed_or_renamed_production_history(tmp_path: Path) -> None:
    """Red evidence must follow the current base and retain governed rename sources."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 0\n", encoding="utf-8")
    original_base_ref = _commit(tmp_path, "chore: base")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, original_base_ref)
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    current_base_ref = _commit(tmp_path, "fix: apply delivery")
    (tmp_path / "src" / "other.py").write_text("VALUE = 2\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: unrelated delivery")

    assert module.validate_prior_red_proof(
        red_proof_path, tmp_path, base_ref=current_base_ref, final_ref=final_ref
    ) == ["tdd-order-unproven"]

    _assert_renamed_governed_path_is_rejected(tmp_path / "rename", module)


def test_git_bound_red_proof_rejects_governed_path_with_tab(tmp_path: Path) -> None:
    """A control character in a governed Git path must not hide its prefix."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "README.md").write_text("# proof\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "chore: base")
    unusual_path = tmp_path / "src" / "a\tb.py"
    unusual_path.parent.mkdir()
    unusual_path.write_text("VALUE = 1\n", encoding="utf-8")
    _commit(tmp_path, "feat: add governed path with tab")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "docs.md").write_text("# final\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "docs: retain final source")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "tdd-order-unproven"
    ]


def test_git_bound_red_proof_rejects_governed_path_changed_and_restored_before_red(tmp_path: Path) -> None:
    """Intermediate production edits remain production history after a later revert."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    source_path = tmp_path / "src" / "delivery.py"
    source_path.parent.mkdir()
    source_path.write_text("VALUE = 0\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "chore: base")
    source_path.write_text("VALUE = 1\n", encoding="utf-8")
    _commit(tmp_path, "feat: premature delivery")
    source_path.write_text("VALUE = 0\n", encoding="utf-8")
    _commit(tmp_path, "revert: restore delivery")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "docs.md").write_text("# final\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "docs: retain final source")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "tdd-order-unproven"
    ]


def test_git_bound_red_proof_rejects_test_changed_and_restored_after_red(tmp_path: Path) -> None:
    """Intermediate selected-test edits make a retained red proof stale after a revert."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "README.md").write_text("# proof\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "chore: base")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    original_test = "def test_selected() -> None: assert False\n"
    test_path.write_text(original_test, encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    test_path.write_text("def test_selected() -> None: assert True\n", encoding="utf-8")
    _commit(tmp_path, "test: alter selected proof")
    test_path.write_text(original_test, encoding="utf-8")
    _commit(tmp_path, "revert: restore selected proof")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


@pytest.mark.parametrize(
    "delivery_path",
    [
        "pyproject.toml",
        "resources/templates/proof.j2",
        "resources/schemas/proof.json",
        "resources/mappings/proof.yaml",
        "resources/keys/proof.pub",
        "modules/bundle-mapper/module-package.yaml",
        "tools/proof_runner.py",
    ],
)
def test_git_bound_red_proof_rejects_delivery_input_before_red(tmp_path: Path, delivery_path: str) -> None:
    """Frozen dependency input changes are production work, even at repository root."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "README.md").write_text("# proof\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "chore: base")
    packaged_path = tmp_path / delivery_path
    packaged_path.parent.mkdir(parents=True, exist_ok=True)
    packaged_path.write_text("packaged proof\n", encoding="utf-8")
    _commit(tmp_path, "build: change delivery input")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "docs.md").write_text("# final\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "docs: retain final source")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "tdd-order-unproven"
    ]


@pytest.mark.parametrize("missing_field", ["source_tree", "merge_base", "test_file_digests", "toolchain_identity"])
def test_git_bound_red_proof_requires_every_execution_binding(tmp_path: Path, missing_field: str) -> None:
    """A retained red report without every source and toolchain binding is invalid."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "README.md").write_text("# proof\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "chore: base")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    report = json.loads(red_proof_path.read_text(encoding="utf-8"))
    del report["execution_proof"][missing_field]
    red_proof_path.write_text(json.dumps(report), encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "prior-red-proof-invalid"
    ]


def test_git_bound_red_proof_rejects_pull_request_tracked_artifacts(tmp_path: Path) -> None:
    """A report and digest controlled by the pull request are not a trusted run artifact."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "README.md").write_text("# proof\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "chore: base")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    _commit(tmp_path, "test: commit self-reported red artifacts")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "prior-red-proof-invalid"
    ]


def test_git_bound_red_proof_rejects_test_digest_not_present_at_source(tmp_path: Path) -> None:
    """The selected test digest must match the committed bytes at the red source."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "README.md").write_text("# proof\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "chore: base")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    report = json.loads(red_proof_path.read_text(encoding="utf-8"))
    report["execution_proof"]["test_file_digests"]["tests/test_proof.py"] = f"sha256:{'0' * 64}"
    red_proof_path.write_text(json.dumps(report), encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "prior-red-proof-invalid"
    ]
