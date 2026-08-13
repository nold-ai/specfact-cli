"""Contract coverage for Git-bound Requirements red-proof provenance."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import itertools
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Protocol, cast

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
PROVENANCE_SCRIPT = REPO_ROOT / "scripts" / "requirements_proof_provenance.py"


class ProvenanceModule(Protocol):
    """Minimal public surface for validating a committed red-proof report."""

    def validate_prior_red_proof(
        self, red_proof_path: Path, repo_root: Path, *, base_ref: str, final_ref: str
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


def _red_proof(
    source_ref: str,
    junit_digest: str,
    *,
    source_tree: str,
    merge_base: str,
    test_file_digest: str,
) -> dict[str, object]:
    return {
        "gate_decision": "pass",
        "observed_maturity": "red",
        "mapping_digest": f"sha256:{'a' * 64}",
        "plan_digest": f"sha256:{'b' * 64}",
        "execution_proof": {
            "run_stage": "red",
            "source_ref": source_ref,
            "source_tree": source_tree,
            "merge_base": merge_base,
            "selectors": ["tests/test_proof.py::test_selected"],
            "test_file_digests": {"tests/test_proof.py": test_file_digest},
            "junit_digest": junit_digest,
            "toolchain_identity": {"runner": "pytest", "python": "3.12", "pytest": "9.1"},
        },
    }


def _write_red_proof(path: Path, repo_root: Path, source_ref: str, merge_base: str) -> None:
    junit = (
        b'<testsuite><testcase><properties><property name="specfact.selector" '
        b'value="tests/test_proof.py::test_selected"/></properties><failure/></testcase></testsuite>'
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


def test_git_bound_red_proof_requires_test_only_ancestor_and_unchanged_selector_files(tmp_path: Path) -> None:
    """Only an ancestor red report with unchanged selected tests may reach reconciliation."""
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
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []

    test_path.write_text("def test_selected() -> None: assert True\n", encoding="utf-8")
    stale_ref = _commit(tmp_path, "test: change selector")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=stale_ref) == [
        "stale-red-proof"
    ]


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


@pytest.mark.parametrize(
    "plugin_declaration",
    [
        'pytest_plugins = ("tests.helpers.fixtures",)\n',
        'pytest_plugins: tuple[str, ...] = ("tests.helpers.fixtures",)\n',
        'pytest_plugins: str = "tests.helpers.fixtures,tests.helpers.other"\n',
        'PLUGINS = ("tests.helpers.fixtures",)\npytest_plugins: tuple[str, ...] = PLUGINS\n',
        'PLUGINS = ("tests.helpers.other",)\nPLUGINS = ("tests.helpers.fixtures",)\npytest_plugins = PLUGINS\n',
        'FLAG = True\nif FLAG:\n    PLUGINS = ("tests.helpers.fixtures",)\nelse:\n    PLUGINS = ("tests.helpers.other",)\npytest_plugins = PLUGINS\n',
        'PLUGINS = ("tests.helpers.fixtures",)\nfor _ in ():\n    PLUGINS = ("tests.helpers.other",)\npytest_plugins = PLUGINS\n',
        'FLAG = False\nPLUGINS = ("tests.helpers.fixtures",)\nif FLAG:\n    PLUGINS = load_plugins()\npytest_plugins = PLUGINS\n',
        'pytest_plugins = ()\npytest_plugins += ("tests.helpers.fixtures",)\n',
        'pytest_plugins, _unused = ("tests.helpers.fixtures",), 1\n',
        'PLUGINS = ()\nPLUGINS += ("tests.helpers.fixtures",)\npytest_plugins = PLUGINS\n',
    ],
)
def test_git_bound_red_proof_rejects_changed_pytest_plugin(tmp_path: Path, plugin_declaration: str) -> None:
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
    (tests_path / "conftest.py").write_text(plugin_declaration, encoding="utf-8")
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
    "plugin_declaration",
    [
        'def helper() -> None:\n    pytest_plugins: tuple[str, ...] = ("tests.helpers.fixtures",)\n',
        'class Helper:\n    pytest_plugins: tuple[str, ...] = ("tests.helpers.fixtures",)\n',
    ],
)
def test_git_bound_red_proof_ignores_nested_pytest_plugin(tmp_path: Path, plugin_declaration: str) -> None:
    """A local or class annotation does not declare a pytest plugin."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    helpers_path = tests_path / "helpers"
    helpers_path.mkdir(parents=True)
    plugin_path = helpers_path / "fixtures.py"
    plugin_path.write_text("VALUE = False\n", encoding="utf-8")
    (tests_path / "conftest.py").write_text(plugin_declaration, encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add nested plugin-like annotation")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    plugin_path.write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change unrelated plugin-like target")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


def test_git_bound_red_proof_ignores_plugin_declaration_in_imported_helper(tmp_path: Path) -> None:
    """An ordinary imported helper cannot register a pytest plugin."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "fake.py").write_text("VALUE = False\n", encoding="utf-8")
    (tests_path / "helper.py").write_text('pytest_plugins: tuple[str, ...] = ("tests.fake",)\n', encoding="utf-8")
    (tests_path / "conftest.py").write_text("import tests.helper\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add plugin-like helper annotation")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "fake.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change unrelated plugin-like target")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


def test_git_bound_red_proof_ignores_plugin_declaration_in_plugin_parent(tmp_path: Path) -> None:
    """A registered plugin's parent initializer cannot register another plugin."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    plugins_path = tmp_path / "plugins"
    plugins_path.mkdir()
    (plugins_path / "__init__.py").write_text('pytest_plugins = ("tests.fake",)\n', encoding="utf-8")
    (plugins_path / "foo.py").write_text("VALUE = False\n", encoding="utf-8")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "fake.py").write_text("VALUE = False\n", encoding="utf-8")
    (tests_path / "conftest.py").write_text('pytest_plugins = ("plugins.foo",)\n', encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add packaged pytest plugin")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "fake.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change inactive parent plugin target")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


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


def test_git_bound_red_proof_rejects_changed_initializer_import(tmp_path: Path) -> None:
    """Repository-local imports from package initializers remain bound to red."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "__init__.py").write_text("from tests.support import VALUE\n", encoding="utf-8")
    (tests_path / "support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add packaged pytest support")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change initializer support import")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_ignores_lazy_initializer_import(tmp_path: Path) -> None:
    """An import inside an uncalled initializer function is not a proof input."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "__init__.py").write_text(
        "def load_support() -> None:\n    import tests.lazy_support\n", encoding="utf-8"
    )
    (tests_path / "lazy_support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add lazy initializer support")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "lazy_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change lazy initializer support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


def test_git_bound_red_proof_ignores_unreachable_initializer_imports(tmp_path: Path) -> None:
    """Statically false initializer branches do not execute their imports."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "__init__.py").write_text(
        "from typing import TYPE_CHECKING\n"
        "if False:\n    import tests.false_support\n"
        "if TYPE_CHECKING:\n    import tests.typed_support\n",
        encoding="utf-8",
    )
    (tests_path / "false_support.py").write_text("VALUE = False\n", encoding="utf-8")
    (tests_path / "typed_support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add unreachable initializer imports")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "false_support.py").write_text("VALUE = True\n", encoding="utf-8")
    (tests_path / "typed_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change unreachable initializer support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


def _validate_rebound_type_checking_branch(tmp_path: Path) -> list[str]:
    """Build and validate a proof whose typing guard is rebound at runtime."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "__init__.py").write_text(
        "from typing import TYPE_CHECKING\n"
        "if True:\n    TYPE_CHECKING = True\n"
        "if TYPE_CHECKING:\n    import tests.runtime_support\n",
        encoding="utf-8",
    )
    (tests_path / "runtime_support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add rebound type-checking import")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "runtime_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change runtime type-checking support")

    return module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref)


def test_git_bound_red_proof_tracks_rebound_type_checking_branch(tmp_path: Path) -> None:
    """A rebound TYPE_CHECKING name cannot make a runtime branch unreachable."""
    assert _validate_rebound_type_checking_branch(tmp_path) == ["stale-red-proof"]


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


def test_git_bound_red_proof_rejects_added_selector_package_initializer(tmp_path: Path) -> None:
    """A selected test directory cannot become an executable package after red."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "README.md").write_text("# proof\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "chore: base")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "__init__.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: initialize selector package")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_rejects_added_repository_root_initializer(tmp_path: Path) -> None:
    """The repository-root package initializer remains bound to red."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "README.md").write_text("# proof\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "chore: base")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add root red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tmp_path / "__init__.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: initialize repository package")

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
    base_ref = _commit(tmp_path, "chore: base")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    _git(tmp_path, "add", "tests/test_proof.py")
    _git(tmp_path, "update-index", "--chmod=+x", "tests/test_proof.py")
    executable_ref = _commit(tmp_path, "test: add executable red selector")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, executable_ref, base_ref)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "feature.py").write_text("VALUE = 2\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: implement after executable red selector")

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


def test_git_bound_red_proof_accepts_base_merge_after_red(tmp_path: Path) -> None:
    """Imported base changes must not make an unchanged red selector stale."""
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

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


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

    rename_root = tmp_path / "rename"
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


@pytest.mark.parametrize(
    "initializer_source",
    [
        "from typing import TYPE_CHECKING\n"
        "if True:\n    from tests.guard import TYPE_CHECKING\n"
        "if TYPE_CHECKING:\n    import tests.runtime_support\n",
        "import typing\n"
        "if True:\n    import tests.guard as typing\n"
        "if typing.TYPE_CHECKING:\n    import tests.runtime_support\n",
    ],
)
def test_git_bound_red_proof_tracks_rebound_type_checking_import(tmp_path: Path, initializer_source: str) -> None:
    """A nested import rebinding the guard name or the typing module cannot prune a runtime branch."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "guard.py").write_text("TYPE_CHECKING = True\n", encoding="utf-8")
    (tests_path / "__init__.py").write_text(initializer_source, encoding="utf-8")
    (tests_path / "runtime_support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add rebound type-checking import")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "runtime_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change runtime type-checking support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


@pytest.mark.parametrize(
    ("configuration_path", "red_body", "final_body"),
    [
        ("pytest.toml", '[pytest]\nfilterwarnings = ["error"]\n', '[pytest]\nfilterwarnings = ["ignore"]\n'),
        (".pytest.toml", '[pytest]\nfilterwarnings = ["error"]\n', '[pytest]\nfilterwarnings = ["ignore"]\n'),
        ("pytest.ini", "[pytest]\nfilterwarnings =\n    error\n", "[pytest]\nfilterwarnings =\n    ignore\n"),
        (".pytest.ini", "[pytest]\nfilterwarnings =\n    error\n", "[pytest]\nfilterwarnings =\n    ignore\n"),
        (
            "pyproject.toml",
            '[tool.pytest.ini_options]\nfilterwarnings = ["error"]\n',
            '[tool.pytest.ini_options]\nfilterwarnings = ["ignore"]\n',
        ),
        ("tox.ini", "[pytest]\nfilterwarnings =\n    error\n", "[pytest]\nfilterwarnings =\n    ignore\n"),
        ("setup.cfg", "[tool:pytest]\nfilterwarnings =\n    error\n", "[tool:pytest]\nfilterwarnings =\n    ignore\n"),
    ],
)
def test_git_bound_red_proof_rejects_changed_pytest_configuration(
    tmp_path: Path, configuration_path: str, red_body: str, final_body: str
) -> None:
    """Pytest configuration decides collection and outcome, so it must stay bound to the red failure."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    configuration = tmp_path / configuration_path
    configuration.write_text(red_body, encoding="utf-8")
    base_ref = _commit(tmp_path, "chore: add pytest configuration")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    configuration.write_text(final_body, encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: relax pytest configuration")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


@pytest.mark.parametrize(
    "plugin_declaration",
    [
        'BASE = ("tests.helpers.fixtures",)\npytest_plugins = list(BASE)\n',
        'BASE = ("tests.helpers.fixtures",)\nEXTRA = ("tests.helpers.other",)\npytest_plugins = BASE + EXTRA\n',
        'BASE = ("tests.helpers.fixtures",)\npytest_plugins = [*BASE, "tests.helpers.other"]\n',
        "pytest_plugins = _discover_plugins()\n",
        'FLAG = True\nPLUGINS = ("tests.helpers.fixtures",)\nif FLAG:\n    PLUGINS = _load()\npytest_plugins = PLUGINS\n',
    ],
)
def test_git_bound_red_proof_rejects_unresolvable_pytest_plugins(tmp_path: Path, plugin_declaration: str) -> None:
    """An active plugin declaration that cannot be resolved statically must fail closed."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "conftest.py").write_text(plugin_declaration, encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add unresolvable plugin declaration")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


@pytest.mark.parametrize("selectors", [[{"path": "tests/test_proof.py"}], [["tests/test_proof.py::test_selected"]]])
def test_git_bound_red_proof_rejects_unhashable_selector_entry(tmp_path: Path, selectors: list[object]) -> None:
    """A malformed selector entry yields a deterministic finding instead of an unhandled error."""
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
    report["execution_proof"]["selectors"] = selectors
    red_proof_path.write_text(json.dumps(report), encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "prior-red-proof-invalid"
    ]


def test_git_bound_red_proof_binds_non_utf8_support_module(tmp_path: Path) -> None:
    """A legally encoded non-UTF-8 support module must be parsed, not crash the gate."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "support.py").write_bytes(b"# -*- coding: latin-1 -*-\nLABEL = 'caf\xe9'\nVALUE = False\n")
    (tests_path / "conftest.py").write_bytes(b"# -*- coding: latin-1 -*-\n# caf\xe9\nimport tests.support\n")
    (tests_path / "__init__.py").write_text("", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add latin-1 support module")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "support.py").write_bytes(b"# -*- coding: latin-1 -*-\nLABEL = 'caf\xe9'\nVALUE = True\n")
    final_ref = _commit(tmp_path, "fix: change latin-1 support module")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


@pytest.mark.parametrize(
    ("configuration_path", "configuration_body"),
    [
        ("pyproject.toml", '[tool.pytest.ini_options]\npythonpath = ["source"]\n'),
        ("pytest.ini", "[pytest]\npythonpath = source\n"),
        ("tox.ini", "[pytest]\npythonpath = source\n"),
        ("setup.cfg", "[tool:pytest]\npythonpath = source\n"),
        ("pytest.toml", '[pytest]\npythonpath = ["source"]\n'),
        ("pyproject.toml", '[tool.pytest]\npythonpath = ["source"]\n'),
    ],
)
def test_git_bound_red_proof_rejects_changed_plugin_under_pythonpath_root(
    tmp_path: Path, configuration_path: str, configuration_body: str
) -> None:
    """A plugin resolvable only through a configured pythonpath root stays bound to the red failure."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / configuration_path).write_text(configuration_body, encoding="utf-8")
    plugin_path = tmp_path / "source" / "rooted_plugin"
    plugin_path.mkdir(parents=True)
    (plugin_path / "__init__.py").write_text("", encoding="utf-8")
    (plugin_path / "fixtures.py").write_text("VALUE = False\n", encoding="utf-8")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "conftest.py").write_text('pytest_plugins = ("rooted_plugin.fixtures",)\n', encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add plugin under a pythonpath root")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (plugin_path / "fixtures.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change plugin under a pythonpath root")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_allows_production_change_under_pythonpath_root(tmp_path: Path) -> None:
    """A pythonpath root must not bind ordinary production imports, which red-to-green work edits."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "pyproject.toml").write_text('[tool.pytest.ini_options]\npythonpath = ["src"]\n', encoding="utf-8")
    delivery_path = tmp_path / "src" / "delivery"
    delivery_path.mkdir(parents=True)
    (delivery_path / "__init__.py").write_text("", encoding="utf-8")
    (delivery_path / "feature.py").write_text("VALUE = False\n", encoding="utf-8")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    base_ref = _commit(tmp_path, "chore: add production module under a pythonpath root")
    (tests_path / "test_proof.py").write_text(
        "from delivery.feature import VALUE\n\ndef test_selected() -> None: assert VALUE\n",
        encoding="utf-8",
    )
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (delivery_path / "feature.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: implement delivery behavior")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


@pytest.mark.parametrize(
    "plugin_declaration",
    [
        'PLUGINS = ("tests.helpers.other",)\nfor PLUGINS in [("tests.helpers.fixtures",)]:\n    pass\npytest_plugins = PLUGINS\n',
        'PLUGINS = ("tests.helpers.other",)\nwith open("x") as PLUGINS:\n    pass\npytest_plugins = PLUGINS\n',
        'PLUGINS = ("tests.helpers.other",)\ntry:\n    pass\nexcept ValueError as PLUGINS:\n    pass\npytest_plugins = PLUGINS\n',
        'PLUGINS = ("tests.helpers.other",)\nmatch object():\n    case PLUGINS:\n        pass\npytest_plugins = PLUGINS\n',
        'PLUGINS = ("tests.helpers.other",)\nif (PLUGINS := load()):\n    pass\npytest_plugins = PLUGINS\n',
    ],
)
def test_git_bound_red_proof_rejects_compound_target_plugin_rebinding(tmp_path: Path, plugin_declaration: str) -> None:
    """A plugin constant rebound by a compound statement target cannot be treated as still known."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "conftest.py").write_text(plugin_declaration, encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add compound-target plugin rebinding")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_rejects_unparsable_proof_input(tmp_path: Path) -> None:
    """An existing proof input that cannot be parsed must fail closed, not be skipped as absent."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "conftest.py").write_text("def broken(:\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add unparsable conftest")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_rejects_oversized_proof_input(tmp_path: Path) -> None:
    """An existing proof input beyond the parse bound must fail closed rather than be skipped."""
    module = _load_provenance_module()
    # Kept above the selected test blob so only the conftest exceeds the parse bound.
    cast(Any, module).MAX_TEST_BLOB_BYTES = 256
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "conftest.py").write_text(f"VALUE = '{'x' * 512}'\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add oversized conftest")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


@pytest.mark.parametrize(
    ("configuration_path", "configuration_body"),
    [
        ("pyproject.toml", '[tool.pytest.ini_options]\naddopts = "-ra -p tests.localplugin"\n'),
        ("pyproject.toml", '[tool.pytest.ini_options]\naddopts = ["-ra", "-ptests.localplugin"]\n'),
        ("pytest.ini", "[pytest]\naddopts = -ra -p tests.localplugin\n"),
        ("tox.ini", "[pytest]\naddopts = -ra -p tests.localplugin\n"),
        ("setup.cfg", "[tool:pytest]\naddopts = -ra -p tests.localplugin\n"),
        ("pytest.toml", '[pytest]\naddopts = "-ra -p tests.localplugin"\n'),
        (".pytest.toml", '[pytest]\naddopts = ["-ra", "-p", "tests.localplugin"]\n'),
        ("pyproject.toml", '[tool.pytest]\naddopts = "-ra -p tests.localplugin"\n'),
        (".pytest.ini", "[pytest]\naddopts = -ra -p tests.localplugin\n"),
    ],
)
def test_git_bound_red_proof_rejects_changed_addopts_plugin(
    tmp_path: Path, configuration_path: str, configuration_body: str
) -> None:
    """A plugin early-loaded through configured addopts decides collection and must stay bound."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / configuration_path).write_text(configuration_body, encoding="utf-8")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "localplugin.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add addopts plugin")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "localplugin.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change addopts plugin")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_ignores_disabled_addopts_plugin(tmp_path: Path) -> None:
    """A `-p no:` entry disables a plugin rather than naming a repository module to bind."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\naddopts = "-p no:cacheprovider"\n', encoding="utf-8"
    )
    no_path = tmp_path / "no:cacheprovider.py"
    no_path.write_text("VALUE = False\n", encoding="utf-8")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    base_ref = _commit(tmp_path, "test: add disabled plugin option")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    no_path.write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "chore: change unrelated module")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


def test_git_bound_red_proof_ignores_overwritten_plugin_declaration(tmp_path: Path) -> None:
    """Only the final pytest_plugins binding loads, so an overwritten declaration must not bind."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    helpers_path = tests_path / "helpers"
    helpers_path.mkdir(parents=True)
    (helpers_path / "obsolete.py").write_text("VALUE = False\n", encoding="utf-8")
    (helpers_path / "active.py").write_text("VALUE = False\n", encoding="utf-8")
    (tests_path / "conftest.py").write_text(
        'pytest_plugins = ("tests.helpers.obsolete",)\npytest_plugins = ("tests.helpers.active",)\n',
        encoding="utf-8",
    )
    base_ref = _commit(tmp_path, "test: overwrite plugin declaration")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (helpers_path / "obsolete.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "chore: change never-loaded plugin")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


def test_git_bound_red_proof_ignores_function_local_type_checking_rebinding(tmp_path: Path) -> None:
    """A function-local name cannot rebind the module typing guard, so its branch stays pruned."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "__init__.py").write_text(
        "from typing import TYPE_CHECKING\n"
        "def helper() -> None:\n    TYPE_CHECKING = True\n    return None\n"
        "if TYPE_CHECKING:\n    import tests.typing_only\n",
        encoding="utf-8",
    )
    (tests_path / "typing_only.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add function-local guard name")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "typing_only.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "chore: change type-only helper")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


def test_git_bound_red_proof_tracks_compound_target_type_checking_rebinding(tmp_path: Path) -> None:
    """A module-scope compound target can rebind the typing alias, so its guard is not static."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "__init__.py").write_text(
        "import typing\nfor typing in []:\n    pass\nif typing.TYPE_CHECKING:\n    import tests.runtime_support\n",
        encoding="utf-8",
    )
    (tests_path / "runtime_support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add compound-target typing rebinding")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "runtime_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change runtime support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


@pytest.mark.parametrize(
    "initializer_source",
    [
        "from typing import TYPE_CHECKING\n"
        "def helper(x: object = (TYPE_CHECKING := True)) -> None:\n    return None\n"
        "if TYPE_CHECKING:\n    import tests.runtime_support\n",
        "from typing import TYPE_CHECKING\n"
        "handler = lambda x=(TYPE_CHECKING := True): x\n"
        "if TYPE_CHECKING:\n    import tests.runtime_support\n",
        "from typing import TYPE_CHECKING\n"
        "class Holder(list[(TYPE_CHECKING := True) and int]):\n    pass\n"
        "if TYPE_CHECKING:\n    import tests.runtime_support\n",
    ],
)
def test_git_bound_red_proof_tracks_scope_header_type_checking_rebinding(
    tmp_path: Path, initializer_source: str
) -> None:
    """A scope header executes where it appears, so a rebinding there is not deferred."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "__init__.py").write_text(initializer_source, encoding="utf-8")
    (tests_path / "runtime_support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add scope-header guard rebinding")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "runtime_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change runtime support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


@pytest.mark.parametrize("configuration_path", ["pytest.ini", ".pytest.ini", "tox.ini", "setup.cfg"])
def test_git_bound_red_proof_reads_percent_literal_configuration(tmp_path: Path, configuration_path: str) -> None:
    """A literal percent sign is valid in a pytest option and must not abort the gate."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    section = "tool:pytest" if configuration_path == "setup.cfg" else "pytest"
    (tmp_path / configuration_path).write_text(
        f"[{section}]\naddopts = --junit-prefix=foo%bar -p tests.localplugin\n", encoding="utf-8"
    )
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "localplugin.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add percent-literal configuration")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "localplugin.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change addopts plugin")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


@pytest.mark.parametrize(
    "initializer_source",
    [
        "import typing\ntyping.TYPE_CHECKING = True\nif typing.TYPE_CHECKING:\n    import tests.runtime_support\n",
        "import typing\ntyping.TYPE_CHECKING |= True\nif typing.TYPE_CHECKING:\n    import tests.runtime_support\n",
        "from typing import TYPE_CHECKING\n"
        "class Holder:\n    global TYPE_CHECKING\n    TYPE_CHECKING = True\n"
        "if TYPE_CHECKING:\n    import tests.runtime_support\n",
    ],
)
def test_git_bound_red_proof_tracks_mutated_type_checking_guard(tmp_path: Path, initializer_source: str) -> None:
    """An attribute write or a global declaration mutates the module guard, so it is not static."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "__init__.py").write_text(initializer_source, encoding="utf-8")
    (tests_path / "runtime_support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add mutated type-checking guard")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "runtime_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change runtime support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_rejects_oversized_pytest_configuration(tmp_path: Path) -> None:
    """An unreadable configuration could declare plugins or roots, so it must fail closed."""
    module = _load_provenance_module()
    # Kept above the selected test blob so only the configuration exceeds the read bound.
    cast(Any, module).MAX_TEST_BLOB_BYTES = 256
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "pyproject.toml").write_text(
        f'[tool.pytest.ini_options]\nfilterwarnings = ["{"x" * 512}"]\n', encoding="utf-8"
    )
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    base_ref = _commit(tmp_path, "chore: add oversized pytest configuration")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


@pytest.mark.parametrize("guard_literal", ["0", "None", '""', "()"])
def test_git_bound_red_proof_ignores_falsy_literal_guard_imports(tmp_path: Path, guard_literal: str) -> None:
    """Any falsy literal guard is as unreachable as `if False`, so its import is not executed."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "__init__.py").write_text(f"if {guard_literal}:\n    import tests.typing_only\n", encoding="utf-8")
    (tests_path / "typing_only.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add falsy literal guard")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "typing_only.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "chore: change unexecuted helper")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


@pytest.mark.parametrize(
    "plugin_declaration",
    [
        "from tests.names import pytest_plugins\n",
        "from tests.names import pytest_plugins as pytest_plugins\n",
        "from tests.names import *\n",
    ],
)
def test_git_bound_red_proof_rejects_imported_pytest_plugins(tmp_path: Path, plugin_declaration: str) -> None:
    """A pytest_plugins value that lives in another module cannot be resolved, so it fails closed."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    helpers_path = tests_path / "helpers"
    helpers_path.mkdir(parents=True)
    (helpers_path / "fixtures.py").write_text("VALUE = False\n", encoding="utf-8")
    (tests_path / "names.py").write_text('pytest_plugins = ("tests.helpers.fixtures",)\n', encoding="utf-8")
    (tests_path / "conftest.py").write_text(plugin_declaration, encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add imported plugin declaration")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_binds_plugins_declared_after_an_import(tmp_path: Path) -> None:
    """An unrelated import must not stale a conftest whose own plugin declaration is literal."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    helpers_path = tests_path / "helpers"
    helpers_path.mkdir(parents=True)
    (helpers_path / "fixtures.py").write_text("VALUE = False\n", encoding="utf-8")
    (tests_path / "conftest.py").write_text(
        'import os\nfrom tests.helpers import fixtures\npytest_plugins = ("tests.helpers.fixtures",)\n',
        encoding="utf-8",
    )
    base_ref = _commit(tmp_path, "test: add literal declaration beside imports")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (helpers_path / "fixtures.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change declared plugin")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_rejects_changed_plugin_import_under_pythonpath_root(tmp_path: Path) -> None:
    """A plugin loaded from a pythonpath root resolves its own imports against that root."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "pytest.ini").write_text("[pytest]\npythonpath = source\naddopts = -p plugin\n", encoding="utf-8")
    source_path = tmp_path / "source"
    source_path.mkdir()
    (source_path / "plugin.py").write_text("import helper\n", encoding="utf-8")
    (source_path / "helper.py").write_text("VALUE = False\n", encoding="utf-8")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    base_ref = _commit(tmp_path, "test: add rooted plugin and its helper")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (source_path / "helper.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change helper imported by the rooted plugin")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_rejects_changed_plugin_under_quoted_pythonpath_root(tmp_path: Path) -> None:
    """Pytest splits an ini path list with shlex, so a quoted root containing a space is one path."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "pytest.ini").write_text(
        '[pytest]\npythonpath = "test support"\naddopts = -p rooted_plugin\n', encoding="utf-8"
    )
    support_path = tmp_path / "test support"
    support_path.mkdir()
    (support_path / "rooted_plugin.py").write_text("VALUE = False\n", encoding="utf-8")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    base_ref = _commit(tmp_path, "test: add plugin under a quoted pythonpath root")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (support_path / "rooted_plugin.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change plugin under a quoted root")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


@pytest.mark.parametrize(
    "plugin_declaration",
    [
        'pytest_plugins = []\npytest_plugins.append("tests.helpers.fixtures")\n',
        'PLUGINS = []\nPLUGINS.extend(["tests.helpers.fixtures"])\npytest_plugins = PLUGINS\n',
    ],
)
def test_git_bound_red_proof_rejects_mutated_pytest_plugins(tmp_path: Path, plugin_declaration: str) -> None:
    """An in-place mutation leaves the declaration unknowable statically, so it fails closed."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    helpers_path = tests_path / "helpers"
    helpers_path.mkdir(parents=True)
    (helpers_path / "fixtures.py").write_text("VALUE = False\n", encoding="utf-8")
    (tests_path / "conftest.py").write_text(plugin_declaration, encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add mutated plugin declaration")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_tracks_class_body_guard_mutation(tmp_path: Path) -> None:
    """A class body executes during import, so a guard attribute written there is not static."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "__init__.py").write_text(
        "import typing\n"
        "class Holder:\n    typing.TYPE_CHECKING = True\n"
        "if typing.TYPE_CHECKING:\n    import tests.runtime_support\n",
        encoding="utf-8",
    )
    (tests_path / "runtime_support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add class-body guard mutation")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "runtime_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change runtime support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_rejects_symlinked_support_input(tmp_path: Path) -> None:
    """A symlinked pytest input executes bytes this gate never inspected, so it fails closed."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    support_path = tmp_path / "support"
    support_path.mkdir()
    (support_path / "real_conftest.py").write_text("VALUE = False\n", encoding="utf-8")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "conftest.py").symlink_to(Path("..") / "support" / "real_conftest.py")
    base_ref = _commit(tmp_path, "test: add symlinked conftest")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_rejects_scope_header_plugin_binding(tmp_path: Path) -> None:
    """A function default executes at import, so a plugin bound there is loaded by pytest."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    helpers_path = tests_path / "helpers"
    helpers_path.mkdir(parents=True)
    (helpers_path / "fixtures.py").write_text("VALUE = False\n", encoding="utf-8")
    (tests_path / "conftest.py").write_text(
        'def helper(arg: object = (pytest_plugins := ("tests.helpers.fixtures",))) -> object:\n    return arg\n',
        encoding="utf-8",
    )
    base_ref = _commit(tmp_path, "test: bind plugins in a function default")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (helpers_path / "fixtures.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change plugin bound in a default")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_ignores_uncalled_global_guard_rebinding(tmp_path: Path) -> None:
    """An uncalled function never runs, so its global rebinding must not drop the guard."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "__init__.py").write_text(
        "from typing import TYPE_CHECKING\n"
        "def enable() -> None:\n    global TYPE_CHECKING\n    TYPE_CHECKING = True\n"
        "if TYPE_CHECKING:\n    import tests.typing_only\n",
        encoding="utf-8",
    )
    (tests_path / "typing_only.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add uncalled global rebinding")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "typing_only.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "chore: change type-only helper")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


def test_git_bound_red_proof_tracks_called_global_guard_rebinding(tmp_path: Path) -> None:
    """A function invoked while the module loads does rebind the guard, so it must be tracked."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "__init__.py").write_text(
        "from typing import TYPE_CHECKING\n"
        "def enable() -> None:\n    global TYPE_CHECKING\n    TYPE_CHECKING = True\n"
        "enable()\n"
        "if TYPE_CHECKING:\n    import tests.runtime_support\n",
        encoding="utf-8",
    )
    (tests_path / "runtime_support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add called global rebinding")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "runtime_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change runtime support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


@pytest.mark.parametrize(
    "initializer_source",
    [
        # An invoked setter assigns the declaration through `global`.
        'def configure() -> None:\n    global pytest_plugins\n    pytest_plugins = ("tests.helpers.fixtures",)\nconfigure()\n',
        # An invoked function mutates the typing guard by attribute.
        "import typing\ndef enable() -> None:\n    typing.TYPE_CHECKING = True\nenable()\n",
        # The invoked function is reached through an alias rather than its own name.
        "from typing import TYPE_CHECKING\n"
        "def enable() -> None:\n    global TYPE_CHECKING\n    TYPE_CHECKING = True\n"
        "activate = enable\nactivate()\n",
    ],
)
def test_git_bound_red_proof_rejects_invoked_module_state_mutation(tmp_path: Path, initializer_source: str) -> None:
    """An invoked function that can change module state leaves it unverifiable, so it fails closed."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    helpers_path = tests_path / "helpers"
    helpers_path.mkdir(parents=True)
    (helpers_path / "fixtures.py").write_text("VALUE = False\n", encoding="utf-8")
    (tests_path / "conftest.py").write_text(initializer_source, encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add invoked module-state mutation")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_ignores_guard_rebound_after_its_branch(tmp_path: Path) -> None:
    """A rebinding cannot invalidate a branch that already ran before it."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "__init__.py").write_text(
        "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    import tests.type_support\nTYPE_CHECKING = True\n",
        encoding="utf-8",
    )
    (tests_path / "type_support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: rebind the guard after its branch")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "type_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "chore: change type-only helper")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


def test_git_bound_red_proof_tracks_guard_rebound_before_its_branch(tmp_path: Path) -> None:
    """A rebinding that precedes the branch still invalidates the guard."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "__init__.py").write_text(
        "from typing import TYPE_CHECKING\nTYPE_CHECKING = True\nif TYPE_CHECKING:\n    import tests.runtime_support\n",
        encoding="utf-8",
    )
    (tests_path / "runtime_support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: rebind the guard before its branch")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "runtime_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change runtime support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_normalizes_traversing_pythonpath_root(tmp_path: Path) -> None:
    """Pytest resolves a `pythonpath` entry, so a root spelled with `..` still binds its plugin."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\npythonpath = tests/helpers/../plugins\naddopts = -p localplugin\n", encoding="utf-8"
    )
    plugins_path = tmp_path / "tests" / "plugins"
    plugins_path.mkdir(parents=True)
    (plugins_path / "localplugin.py").write_text("VALUE = False\n", encoding="utf-8")
    (tmp_path / "tests" / "helpers").mkdir()
    (tmp_path / "tests" / "helpers" / "keep.py").write_text("VALUE = True\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add plugin under a traversing pythonpath root")
    (tmp_path / "tests" / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (plugins_path / "localplugin.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change plugin under a traversing root")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_rejects_symlinked_pytest_configuration(tmp_path: Path) -> None:
    """Pytest reads a symlinked configuration target whose bytes this gate never inspected."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    config_path = tmp_path / "config"
    config_path.mkdir()
    (config_path / "real-pytest.ini").write_text("[pytest]\naddopts = -p tests.localplugin\n", encoding="utf-8")
    (tmp_path / "pytest.ini").symlink_to(Path("config") / "real-pytest.ini")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "localplugin.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add symlinked pytest configuration")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_tracks_mutation_through_an_earlier_alias(tmp_path: Path) -> None:
    """Aliasing a list binds the same object, so a later mutation changes the declared plugins."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "conftest.py").write_text(
        'PLUGINS = []\npytest_plugins = PLUGINS\nPLUGINS.append("tests.localplugin")\n', encoding="utf-8"
    )
    (tests_path / "localplugin.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: alias the plugin list before mutating it")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_tracks_setattr_written_typing_guard(tmp_path: Path) -> None:
    """A guard handed to a call can be rewritten, so its branch is no longer type-only."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "__init__.py").write_text(
        'import typing\nsetattr(typing, "TYPE_CHECKING", True)\n'
        "if typing.TYPE_CHECKING:\n    import tests.runtime_support\n",
        encoding="utf-8",
    )
    (tests_path / "runtime_support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: rewrite the typing guard through setattr")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "runtime_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change runtime support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_tracks_setattr_guard_write_from_a_function(tmp_path: Path) -> None:
    """A function that rewrites an attribute makes module state unverifiable once it is called."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "__init__.py").write_text(
        "import typing\n\n\ndef _enable() -> None:\n"
        '    setattr(typing, "TYPE_CHECKING", True)\n\n\n_enable()\n'
        "if typing.TYPE_CHECKING:\n    import tests.runtime_support\n",
        encoding="utf-8",
    )
    (tests_path / "runtime_support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: rewrite the typing guard from a called function")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "runtime_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change runtime support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_tracks_guard_handed_to_a_call_inside_a_function(tmp_path: Path) -> None:
    """A callee that receives the guard module can rewrite it however it is named."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "__init__.py").write_text(
        "from builtins import setattr as _set\nimport typing\n\n\ndef _enable() -> None:\n"
        '    _set(typing, "TYPE_CHECKING", True)\n\n\n_enable()\n'
        "if typing.TYPE_CHECKING:\n    import tests.runtime_support\n",
        encoding="utf-8",
    )
    (tests_path / "runtime_support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: rewrite the guard through an aliased builtin")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "runtime_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change runtime support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_rejects_symlinked_support_input_that_parses(tmp_path: Path) -> None:
    """A link target that is valid Python parses, so parse failure cannot be the symlink check."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "real_conftest.py").write_text("VALUE = False\n", encoding="utf-8")
    (tests_path / "conftest.py").symlink_to(Path("real_conftest.py"))
    base_ref = _commit(tmp_path, "test: add a symlinked conftest whose link text parses")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_tracks_subscript_mutation_of_an_aliased_plugin_list(tmp_path: Path) -> None:
    """A subscript write changes the aliased list in place without rebinding either name."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "conftest.py").write_text(
        'PLUGINS = ["tests.old"]\npytest_plugins = PLUGINS\nPLUGINS[0] = "tests.active"\n', encoding="utf-8"
    )
    (tests_path / "old.py").write_text("VALUE = False\n", encoding="utf-8")
    (tests_path / "active.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: mutate an aliased plugin list through a subscript")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_tracks_guard_written_through_a_module_alias(tmp_path: Path) -> None:
    """A second reference to the guard module rewrites the guard the first name also sees."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "__init__.py").write_text(
        "import typing as t\nalias = t\nalias.TYPE_CHECKING = True\n"
        "if t.TYPE_CHECKING:\n    import tests.runtime_support\n",
        encoding="utf-8",
    )
    (tests_path / "runtime_support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: rewrite the guard through a module alias")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "runtime_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change runtime support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_tracks_mutation_through_a_chained_assignment(tmp_path: Path) -> None:
    """Chained targets share one runtime object, so a mutation reaches both names."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "conftest.py").write_text(
        'PLUGINS = pytest_plugins = []\nPLUGINS.append("tests.localplugin")\n', encoding="utf-8"
    )
    (tests_path / "localplugin.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: mutate a chained plugin assignment")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_binds_repository_contained_absolute_pythonpath_root(tmp_path: Path) -> None:
    """An absolute pythonpath entry inside the checkout still names a repository root."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    plugins_path = tmp_path / "plugins"
    plugins_path.mkdir()
    (plugins_path / "localplugin.py").write_text("VALUE = False\n", encoding="utf-8")
    (tmp_path / "pytest.ini").write_text(
        f"[pytest]\npythonpath = {plugins_path}\naddopts = -p localplugin\n", encoding="utf-8"
    )
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    base_ref = _commit(tmp_path, "test: add plugin under an absolute pythonpath root")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (plugins_path / "localplugin.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change plugin under an absolute root")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_tracks_called_lambda_guard_mutation(tmp_path: Path) -> None:
    """A lambda body runs when it is called, so it mutates module state like a function."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "__init__.py").write_text(
        'import typing\nactivate = lambda: setattr(typing, "TYPE_CHECKING", True)\nactivate()\n'
        "if typing.TYPE_CHECKING:\n    import tests.runtime_support\n",
        encoding="utf-8",
    )
    (tests_path / "runtime_support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: rewrite the guard from a called lambda")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "runtime_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change runtime support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_rejects_module_namespace_plugin_write(tmp_path: Path) -> None:
    """A write through globals() creates the attribute pytest reads without a name target."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "conftest.py").write_text('globals()["pytest_plugins"] = ["tests.localplugin"]\n', encoding="utf-8")
    (tests_path / "localplugin.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: declare plugins through the module namespace")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_rejects_class_body_global_plugin_binding(tmp_path: Path) -> None:
    """A class body executes at import, so a global plugin binding there is what pytest reads."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "conftest.py").write_text(
        'class _Configure:\n    global pytest_plugins\n    pytest_plugins = ("tests.localplugin",)\n',
        encoding="utf-8",
    )
    (tests_path / "localplugin.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: declare plugins from a class body")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_tracks_guard_nested_in_a_call_argument(tmp_path: Path) -> None:
    """A guard reached through a nested argument expression is still handed to the call."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "__init__.py").write_text(
        'import typing\nsetattr([typing][0], "TYPE_CHECKING", True)\n'
        "if typing.TYPE_CHECKING:\n    import tests.runtime_support\n",
        encoding="utf-8",
    )
    (tests_path / "runtime_support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: rewrite the guard through a nested argument")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "runtime_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change runtime support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_treats_a_bare_decorator_as_a_module_load_call(tmp_path: Path) -> None:
    """Applying a decorator invokes it during import even without a call expression."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "conftest.py").write_text(
        "def activate(function):\n    global pytest_plugins\n"
        '    pytest_plugins = ("tests.localplugin",)\n    return function\n\n\n'
        "@activate\ndef _configure() -> None:\n    return None\n",
        encoding="utf-8",
    )
    (tests_path / "localplugin.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: declare plugins from a bare decorator")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_binds_imports_inside_an_invoked_function(tmp_path: Path) -> None:
    """A function body called during module load executes its imports at import time."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "conftest.py").write_text(
        "def _load() -> None:\n    import tests.runtime_support\n\n\n_load()\n", encoding="utf-8"
    )
    (tests_path / "runtime_support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: import support from an invoked function")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "runtime_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change runtime support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_ignores_type_only_import_inside_a_function(tmp_path: Path) -> None:
    """Widening to function bodies must not bind imports a typing guard keeps unexecuted."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "conftest.py").write_text(
        "from typing import TYPE_CHECKING\n\n\ndef _load() -> None:\n"
        "    if TYPE_CHECKING:\n        import tests.type_support\n",
        encoding="utf-8",
    )
    (tests_path / "type_support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: guard a function-body import")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "type_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "chore: change type-only helper")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


def test_git_bound_red_proof_binds_imports_inside_a_selected_test_body(tmp_path: Path) -> None:
    """Pytest executes a test body, so its imports run even with no import-time call."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "runtime_support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add support imported by the selected test")
    (tests_path / "test_proof.py").write_text(
        "def test_selected() -> None:\n    import tests.runtime_support\n\n    assert False\n", encoding="utf-8"
    )
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "runtime_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change runtime support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_reads_pytest_configuration_from_selector_ancestors(tmp_path: Path) -> None:
    """Pytest searches upward from the selector, so a nested configuration decides collection."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "pytest.ini").write_text("[pytest]\naddopts = -p tests.localplugin\n", encoding="utf-8")
    (tests_path / "localplugin.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add nested pytest configuration")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "localplugin.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change nested-config plugin")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_tracks_augmented_mutation_of_an_aliased_plugin_list(tmp_path: Path) -> None:
    """List `+=` mutates the shared object rather than rebinding the name."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "conftest.py").write_text(
        'PLUGINS = []\npytest_plugins = PLUGINS\nPLUGINS += ["tests.localplugin"]\n', encoding="utf-8"
    )
    (tests_path / "localplugin.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: extend an aliased plugin list in place")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_rejects_imports_through_a_symlinked_package_directory(tmp_path: Path) -> None:
    """Python follows a directory link, so the resolved candidate is not the Git path."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    support_path = tests_path / "support"
    support_path.mkdir(parents=True)
    (support_path / "__init__.py").write_text("", encoding="utf-8")
    (support_path / "helper.py").write_text("VALUE = False\n", encoding="utf-8")
    (tmp_path / "support").symlink_to(Path("tests") / "support")
    (tests_path / "conftest.py").write_text("from support import helper\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: import through a symlinked package directory")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (support_path / "helper.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change helper behind the directory link")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_tracks_guard_written_through_a_module_dictionary(tmp_path: Path) -> None:
    """A write through `__dict__` changes the same attribute the guard reads."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "__init__.py").write_text(
        'import typing\ntyping.__dict__["TYPE_CHECKING"] = True\n'
        "if typing.TYPE_CHECKING:\n    import tests.runtime_support\n",
        encoding="utf-8",
    )
    (tests_path / "runtime_support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: rewrite the guard through a module dictionary")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "runtime_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change runtime support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_fails_closed_when_configuration_cannot_be_read(tmp_path: Path) -> None:
    """An unreadable configuration is not an absent one; a Git failure must not silently skip it."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "pytest.ini").write_text("[pytest]\naddopts = -p tests.localplugin\n", encoding="utf-8")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "localplugin.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add configuration that will be unreadable")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "feat: delivery")

    original_git_bytes = module._git_bytes

    def _failing_git_bytes(repo_root: Path, *arguments: str):  # type: ignore[no-untyped-def]
        if arguments[:1] == ("show",) and arguments[1].endswith(":pytest.ini"):
            return subprocess.CompletedProcess(["git", *arguments], returncode=1, stdout=b"", stderr=b"timeout")
        return original_git_bytes(repo_root, *arguments)

    module._git_bytes = _failing_git_bytes  # type: ignore[attr-defined]
    try:
        findings = module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref)
    finally:
        module._git_bytes = original_git_bytes  # type: ignore[attr-defined]

    assert findings == ["stale-red-proof"]


GUARD_REWRITE_SHAPES = (
    "typing.TYPE_CHECKING = True",
    'setattr(typing, "TYPE_CHECKING", True)',
    'from builtins import setattr as _s\n_s(typing, "TYPE_CHECKING", True)',
    'setattr([typing][0], "TYPE_CHECKING", True)',
    'vars(typing)["TYPE_CHECKING"] = True',
    'typing.__dict__["TYPE_CHECKING"] = True',
    'getattr(typing, "__dict__")["TYPE_CHECKING"] = True',
    "alias = typing\nalias.TYPE_CHECKING = True",
    'a = typing\nb = a\nb.__dict__["TYPE_CHECKING"] = True',
    "_rewrite(typing)",
    'def _e() -> None:\n    setattr(typing, "TYPE_CHECKING", True)\n_e()',
    "def _e() -> None:\n    typing.TYPE_CHECKING = True\nactivate = _e\nactivate()",
    '_e = lambda: setattr(typing, "TYPE_CHECKING", True)\n_e()',
    "def _d(f):\n    typing.TYPE_CHECKING = True\n    return f\n@_d\ndef _c() -> None:\n    return None",
    "class _C:\n    global typing\n    typing = _fake",
    'globals()["TYPE_CHECKING"] = True',
)


@pytest.mark.parametrize("mutation", GUARD_REWRITE_SHAPES)
def test_typing_guard_is_never_trusted_after_any_rewrite_shape(mutation: str) -> None:
    """No syntactic wrapper may leave the guard trusted.

    This battery exists because every review round found another wrapper around the same
    idea. Asserting the family rather than the instance means a newly invented shape has to
    defeat the structural rules, not merely differ from the shapes already listed.
    """
    module = cast(Any, _load_provenance_module())
    tree = ast.parse(f"import typing\n{mutation}\nif typing.TYPE_CHECKING:\n    import tests.support\n")
    _type_checking_names, typing_module_names = module._verified_type_checking_bindings(tree)
    assert "typing" not in typing_module_names, f"guard stayed trusted after: {mutation!r}"


UNRESOLVABLE_PLUGIN_SHAPES = (
    'pytest_plugins = []\npytest_plugins.append("tests.p")',
    'P = []\npytest_plugins = P\nP.append("tests.p")',
    'P = []\npytest_plugins = P\nP += ["tests.p"]',
    'P = ["tests.old"]\npytest_plugins = P\nP[0] = "tests.p"',
    'P = ["tests.old"]\npytest_plugins = P\ndel P[0]',
    'P = pytest_plugins = []\nP.append("tests.p")',
    'P = {}\npytest_plugins = P\nP.setdefault("a", "b")',
    'globals()["pytest_plugins"] = ["tests.p"]',
    'vars()["pytest_plugins"] = ["tests.p"]',
    'class _C:\n    global pytest_plugins\n    pytest_plugins = ("tests.p",)',
    'def _f() -> None:\n    global pytest_plugins\n    pytest_plugins = ("tests.p",)\n_f()',
    "from tests.other import pytest_plugins",
    'for pytest_plugins in [("tests.p",)]:\n    pass',
    'with open("f") as pytest_plugins:\n    pass',
    "try:\n    pass\nexcept OSError as pytest_plugins:\n    pass",
    "pytest_plugins = _dynamic()",
)


@pytest.mark.parametrize("declaration", UNRESOLVABLE_PLUGIN_SHAPES)
def test_unresolvable_plugin_declaration_always_fails_closed(declaration: str) -> None:
    """A plugin declaration this gate cannot resolve must never resolve to nothing.

    Reporting no plugins for an unresolvable declaration is the fail-open shape every plugin
    finding shared, so the whole family is asserted rather than each shape as it is reported.
    """
    module = cast(Any, _load_provenance_module())
    with pytest.raises(ValueError, match="stale-red-proof"):
        module._pytest_plugin_names(ast.parse(declaration))


def test_root_name_resolves_through_arbitrary_wrapper_nesting() -> None:
    """The single resolver behind every "which name does this touch" rule must not bottom out."""
    module = cast(Any, _load_provenance_module())
    resolve = module._root_name
    expressions = (
        "typing",
        "typing.a",
        "typing.a.b.c",
        "typing['a']",
        "typing.__dict__['x']['y']",
        "typing.a['b'].c['d']",
        "typing()",
        "typing().a['b']",
    )
    for source in expressions:
        assert resolve(ast.parse(source, mode="eval").body) == "typing", source
    assert resolve(ast.parse("[typing][0]", mode="eval").body) is None


def test_statically_resolvable_declarations_still_resolve() -> None:
    """The batteries must not be satisfiable by rejecting everything."""
    module = cast(Any, _load_provenance_module())
    assert module._pytest_plugin_names(ast.parse('pytest_plugins = ("tests.p",)')) == [["tests", "p"]]
    assert module._pytest_plugin_names(ast.parse('pytest_plugins = "tests.p"')) == [["tests", "p"]]
    assert module._pytest_plugin_names(ast.parse("VALUE = 1\n")) == []
    # A later explicit assignment overwrites whatever a star import may have bound, so the
    # final value is knowable even though the star import alone is not.
    star_then_assign = 'from tests.other import *\npytest_plugins = ("tests.p",)'
    assert module._pytest_plugin_names(ast.parse(star_then_assign)) == [["tests", "p"]]
    # A conditional declaration binds the union of its possible values, which is the
    # fail-closed direction: the plugin is bound whether or not the branch ran.
    conditional = 'if _flag:\n    pytest_plugins = ("tests.p",)'
    assert module._pytest_plugin_names(ast.parse(conditional)) == [["tests", "p"]]
    tree = ast.parse("from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    import tests.support\n")
    type_checking_names, _typing_module_names = module._verified_type_checking_bindings(tree)
    assert "TYPE_CHECKING" in type_checking_names


def test_ordinary_mapping_writes_do_not_make_a_module_unverifiable() -> None:
    """Fail-closed rules must not fire on code that touches nothing this gate depends on.

    Broadening guard-write detection to every subscript target once made almost every real
    conftest unverifiable, because `mapping[key] = value` inside any helper marked the module
    as state-mutating. The whole-repository measurement caught it; this pins the boundary.
    """
    module = cast(Any, _load_provenance_module())
    benign = (
        'CACHE = {}\ndef _store(key, value):\n    CACHE[key] = value\n_store("a", 1)\npytest_plugins = ("tests.p",)\n'
    )
    assert module._pytest_plugin_names(ast.parse(benign)) == [["tests", "p"]]
    assert not module._unverifiable_module_state(ast.parse(benign))


def test_guard_survives_unrelated_module_load_activity() -> None:
    """A typing guard stays trusted when nothing can reach the module it names."""
    module = cast(Any, _load_provenance_module())
    tree = ast.parse(
        "import typing\nimport json\nVALUES = {}\nVALUES['a'] = json.dumps({})\n"
        "if typing.TYPE_CHECKING:\n    import tests.support\n"
    )
    _type_checking_names, typing_module_names = module._verified_type_checking_bindings(tree)
    assert "typing" in typing_module_names


def test_git_bound_red_proof_binds_a_nested_configuration_path(tmp_path: Path) -> None:
    """A nested configuration decides collection, so changing it after red invalidates proof."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "pytest.ini").write_text("[pytest]\nfilterwarnings = error\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add nested configuration")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tests_path / "pytest.ini").write_text("[pytest]\nfilterwarnings = ignore\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change nested configuration")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_resolves_pythonpath_against_its_configuration(tmp_path: Path) -> None:
    """Pytest joins a relative `pythonpath` entry to the directory of the file declaring it."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    plugins_path = tests_path / "plugins"
    plugins_path.mkdir(parents=True)
    (plugins_path / "localplugin.py").write_text("VALUE = False\n", encoding="utf-8")
    (tests_path / "pytest.ini").write_text(
        "[pytest]\npythonpath = plugins\naddopts = -p localplugin\n", encoding="utf-8"
    )
    base_ref = _commit(tmp_path, "test: declare a nested pythonpath root")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (plugins_path / "localplugin.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change the nested-root plugin")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_git_bound_red_proof_fails_closed_when_a_call_receives_an_aliased_plugin_list() -> None:
    """An unbound-method call mutates the argument, not the receiver."""
    module = cast(Any, _load_provenance_module())
    declaration = 'P = []\npytest_plugins = P\nlist.append(P, "tests.localplugin")\n'
    with pytest.raises(ValueError, match="stale-red-proof"):
        module._pytest_plugin_names(ast.parse(declaration))


def _repository_with_nested_pytest_layout(tmp_path: Path) -> str:
    """Build a repository exercising nested configuration, roots, plugins, and imports."""
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    unit_path = tests_path / "unit"
    plugins_path = tests_path / "plugins"
    unit_path.mkdir(parents=True)
    plugins_path.mkdir(parents=True)
    (tmp_path / "pytest.ini").write_text("[pytest]\nfilterwarnings = error\n", encoding="utf-8")
    (tests_path / "pytest.ini").write_text(
        "[pytest]\npythonpath = plugins\naddopts = -p localplugin\n", encoding="utf-8"
    )
    (plugins_path / "localplugin.py").write_text("import helper\n", encoding="utf-8")
    (plugins_path / "helper.py").write_text("VALUE = False\n", encoding="utf-8")
    (tests_path / "__init__.py").write_text("", encoding="utf-8")
    (tests_path / "conftest.py").write_text("import tests.support\n", encoding="utf-8")
    (tests_path / "support.py").write_text("VALUE = False\n", encoding="utf-8")
    (unit_path / "__init__.py").write_text("", encoding="utf-8")
    (unit_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    return _commit(tmp_path, "test: nested pytest layout")


def test_every_file_whose_content_is_read_is_bound_as_a_proof_input(tmp_path: Path) -> None:
    """Anything the gate reads to decide collection must also be bound as a proof input.

    Two review rounds found the same shape: a source was *discovered and read* to derive
    plugins or roots, but never added to the returned set, so changing it after the red
    source did not intersect the changed paths. The AST batteries cannot catch that, because
    the defect lives in the path plumbing rather than in a rule. This asserts the invariant
    directly by recording every content read the gate performs.
    """
    module = cast(Any, _load_provenance_module())
    source_ref = _repository_with_nested_pytest_layout(tmp_path)

    read_paths: list[str] = []
    original_git_bytes = module._git_bytes

    def _recording_git_bytes(repo_root: Path, *arguments: str):  # type: ignore[no-untyped-def]
        if arguments[:1] == ("show",) and ":" in arguments[1]:
            read_paths.append(arguments[1].partition(":")[2])
        return original_git_bytes(repo_root, *arguments)

    module._git_bytes = _recording_git_bytes
    try:
        inputs = module._proof_inputs(tmp_path, source_ref, ("tests/unit/test_proof.py",))
    finally:
        module._git_bytes = original_git_bytes

    read_and_present = {path for path in read_paths if (tmp_path / path).is_file()}
    assert read_and_present, "the layout must exercise real content reads"
    unbound = sorted(read_and_present - inputs)
    assert not unbound, f"read to decide collection but never bound as proof input: {unbound}"


def test_every_configuration_candidate_is_bound_including_absent_ones(tmp_path: Path) -> None:
    """A configuration added after the red source must invalidate the proof, so absent candidates bind."""
    module = cast(Any, _load_provenance_module())
    source_ref = _repository_with_nested_pytest_layout(tmp_path)
    inputs = module._proof_inputs(tmp_path, source_ref, ("tests/unit/test_proof.py",))

    directories = module._configuration_directories(("tests/unit/test_proof.py",))
    assert set(directories) == {"", "tests", "tests/unit"}
    unbound = sorted(module._configuration_candidate_paths(directories) - inputs)
    assert not unbound, f"configuration candidates not bound: {unbound}"


def test_a_plugin_reached_through_a_nested_root_is_bound_with_its_imports(tmp_path: Path) -> None:
    """A root declared by a nested configuration must bind the plugin and what the plugin imports."""
    module = cast(Any, _load_provenance_module())
    source_ref = _repository_with_nested_pytest_layout(tmp_path)
    inputs = module._proof_inputs(tmp_path, source_ref, ("tests/unit/test_proof.py",))

    assert "tests/plugins/localplugin.py" in inputs
    assert "tests/plugins/helper.py" in inputs
    assert "tests/support.py" in inputs


# Every way a conftest can hand ``tests.runtime_support`` to something that loads it. The
# mechanism differs in each; what they share is that the target is named by a literal, so a rule
# that resolves the literal covers the family rather than the spellings enumerated here.
DYNAMIC_LOADER_SHAPES = (
    'importlib.import_module("tests.runtime_support")',
    '__import__("tests.runtime_support")',
    'importlib.__import__("tests.runtime_support")',
    'from importlib import import_module\nimport_module("tests.runtime_support")',
    'from importlib import import_module as _load\n_load("tests.runtime_support")',
    'importlib.import_module(name="tests.runtime_support")',
    'importlib.util.find_spec("tests.runtime_support")',
    'def _bring_in(name):\n    return importlib.import_module(name)\n\n\n_bring_in("tests.runtime_support")',
    'for _name in _collect(["tests.runtime_support"]):\n    importlib.import_module(_name)',
    'functools.partial(importlib.import_module, "tests.runtime_support")()',
    'if VERSION:\n    importlib.import_module("tests.runtime_support")',
    'try:\n    importlib.import_module("tests.runtime_support")\nexcept ImportError:\n    pass',
    'class Support:\n    module = importlib.import_module("tests.runtime_support")',
    '@pytest.fixture\ndef support():\n    return importlib.import_module("tests.runtime_support")',
    'def test_local() -> None:\n    importlib.import_module("tests.runtime_support")',
    '_preload({"support": "tests.runtime_support"})',
)

# Literals shaped like a module name that are never handed to a loader, or that name nothing
# importable. Binding these would reject valid proofs whenever an unrelated file changes.
INERT_LITERAL_SHAPES = (
    'NAMES = ("tests.runtime_support",)',
    'def helper():\n    names = ["tests.runtime_support"]\n    return names',
    'class Helper:\n    names = ("tests.runtime_support",)',
    'assert ARGUMENTS == ["-p", "tests.runtime_support"]',
    'importlib.import_module("tests.absent_support")',
    'Path("tests")\nPath("runtime_support")',
)

_DYNAMIC_LOADER_HEADER = (
    "import functools\n"
    "import importlib\n"
    "import importlib.util\n"
    "from pathlib import Path\n"
    "\n"
    "import pytest\n"
    "\n"
    "VERSION = 1\n"
    "ARGUMENTS = []\n"
    "\n"
    "\n"
    "def _collect(names):\n"
    "    return names\n"
    "\n"
    "\n"
    "def _preload(mapping):\n"
    "    return mapping\n"
)


def _repository_with_dynamic_loader(tmp_path: Path, body: str) -> tuple[str, Path]:
    """Commit a conftest carrying ``body`` beside a support module, and return the red proof."""
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    tests_path = tmp_path / "tests"
    tests_path.mkdir()
    (tests_path / "conftest.py").write_text(f"{_DYNAMIC_LOADER_HEADER}\n\n{body}\n", encoding="utf-8")
    (tests_path / "runtime_support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add support module")
    (tests_path / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    return base_ref, red_proof_path


@pytest.mark.parametrize("loader", DYNAMIC_LOADER_SHAPES)
def test_git_bound_red_proof_binds_a_literal_dynamic_import_target(tmp_path: Path, loader: str) -> None:
    """A statically known dynamic-import target is an ordinary proof input, however it is spelled."""
    module = _load_provenance_module()
    base_ref, red_proof_path = _repository_with_dynamic_loader(tmp_path, loader)

    (tmp_path / "tests" / "runtime_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change dynamically loaded support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


@pytest.mark.parametrize("inert", INERT_LITERAL_SHAPES)
def test_a_name_shaped_literal_that_loads_nothing_does_not_bind_a_file(tmp_path: Path, inert: str) -> None:
    """Reading every module-shaped string as an import would fail proofs on unrelated edits."""
    module = _load_provenance_module()
    base_ref, red_proof_path = _repository_with_dynamic_loader(tmp_path, inert)

    (tmp_path / "tests" / "runtime_support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "chore: edit a module nothing loads")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


def test_a_dynamic_import_in_an_uncalled_initializer_is_not_bound(tmp_path: Path) -> None:
    """A deferred body no one invokes never runs, so its target is not an input pytest reads."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    package_path = tmp_path / "tests" / "helpers"
    package_path.mkdir(parents=True)
    (tmp_path / "tests" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "tests" / "conftest.py").write_text("from tests import helpers\n", encoding="utf-8")
    initializer = 'import importlib\n\n\ndef load():\n    return importlib.import_module("tests.helpers.support")\n'
    (package_path / "__init__.py").write_text(initializer, encoding="utf-8")
    (package_path / "support.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add lazy loader")
    (tmp_path / "tests" / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (package_path / "support.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "chore: edit the never-loaded support")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


def _executor_early_loaded_plugin_names() -> set[str]:
    """Return the plugin names the executor early-loads, read from its own command shape."""
    tree = ast.parse((Path(__file__).resolve().parents[3] / "scripts" / "requirements_proof_executor.py").read_bytes())
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.List, ast.Tuple)):
            continue
        literals = [element.value if isinstance(element, ast.Constant) else None for element in node.elts]
        names.update(
            following
            for token, following in itertools.pairwise(literals)
            if token == "-p" and isinstance(following, str)
        )
    return names


def test_every_plugin_the_executor_early_loads_is_a_proof_input(tmp_path: Path) -> None:
    """A plugin the proof run always loads decides collection, so changing it invalidates the proof."""
    module = _load_provenance_module()
    early_loaded = _executor_early_loaded_plugin_names()
    assert early_loaded, "the executor no longer early-loads any plugin; this guard needs updating"
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    plugin_paths = [Path(*name.split(".")).with_suffix(".py") for name in sorted(early_loaded)]
    for relative in plugin_paths:
        (tmp_path / relative).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / relative).write_text(
            "def pytest_collection_modifyitems(items):\n    return None\n", encoding="utf-8"
        )
    (tmp_path / "tests").mkdir()
    base_ref = _commit(tmp_path, "test: add the early-loaded plugin")
    (tmp_path / "tests" / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tmp_path / plugin_paths[0]).write_text(
        "def pytest_collection_modifyitems(items):\n    items.clear()\n", encoding="utf-8"
    )
    final_ref = _commit(tmp_path, "fix: change the early-loaded plugin")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_the_gate_seeds_every_plugin_the_executor_early_loads() -> None:
    """The two scripts must not drift: a plugin added to the command must be bound by the gate."""
    module = _load_provenance_module()
    seeded = {".".join(parts) for parts in module.EXECUTOR_PLUGIN_NAMES}

    assert _executor_early_loaded_plugin_names() <= seeded


def _repository_with_data_read(tmp_path: Path, body: str, extra: dict[str, str] | None = None) -> tuple[str, Path]:
    """Commit a conftest whose ``body`` reads repository data, and return the red proof."""
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "tests" / "data").mkdir(parents=True)
    (tmp_path / "tests" / "data" / "case.json").write_text('{"expected": false}\n', encoding="utf-8")
    for relative, text in (extra or {}).items():
        (tmp_path / relative).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / relative).write_text(text, encoding="utf-8")
    header = "from pathlib import Path\n\nREPO_ROOT = Path(__file__).resolve().parents[1]\n"
    (tmp_path / "tests" / "conftest.py").write_text(f"{header}\n{body}\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add data the harness reads")
    (tmp_path / "tests" / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    return base_ref, red_proof_path


# Every way the harness can name ``tests/data/case.json`` as a file it reads.
DATA_READ_SHAPES = (
    'CASE = Path("tests/data/case.json").read_text()',
    'CASE = open("tests/data/case.json").read()',
    'CASE = (REPO_ROOT / "tests" / "data" / "case.json").read_text()',
    'CASE = (REPO_ROOT / "tests/data/case.json").read_text()',
    'def fixture_case():\n    return Path("tests/data/case.json").read_bytes()',
    'CASES = [Path(name) for name in ["tests/data/case.json"]]',
)


@pytest.mark.parametrize("read", DATA_READ_SHAPES)
def test_repository_data_the_harness_reads_is_a_proof_input(tmp_path: Path, read: str) -> None:
    """Data inside the test tree decides the outcome, so changing it invalidates the proof."""
    module = _load_provenance_module()
    base_ref, red_proof_path = _repository_with_data_read(tmp_path, read)

    (tmp_path / "tests" / "data" / "case.json").write_text('{"expected": true}\n', encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change the case the harness reads")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


@pytest.mark.parametrize(
    ("read", "changed"),
    [
        ('CASE = Path("src/product.py").read_text()', "src/product.py"),
        ('CASE = Path("README.md").read_text()', "README.md"),
        ('CASE = Path("docs/index.md").read_text()', "docs/index.md"),
    ],
)
def test_a_file_the_fix_is_expected_to_change_is_not_bound_by_a_read(tmp_path: Path, read: str, changed: str) -> None:
    """Production source and documentation are what a red-to-green change edits, not the harness."""
    module = _load_provenance_module()
    base_ref, red_proof_path = _repository_with_data_read(tmp_path, read, {changed: "before\n"})

    (tmp_path / changed).write_text("after\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change the file under test")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


def test_a_read_that_cannot_be_resolved_does_not_fail_the_proof(tmp_path: Path) -> None:
    """Harnesses read paths built at runtime constantly; failing closed on those rejects every proof."""
    module = _load_provenance_module()
    body = 'def fixture_case(tmp_path):\n    return (tmp_path / "case.json").read_text()'
    base_ref, red_proof_path = _repository_with_data_read(tmp_path, body)

    (tmp_path / "tests" / "data" / "case.json").write_text('{"expected": true}\n', encoding="utf-8")
    final_ref = _commit(tmp_path, "chore: change data nothing reads")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


@pytest.mark.parametrize(
    "literal",
    [
        "tests/data/case.json\x00truncated",
        "tests/data/case.json\tinjected",
        "tests/data/case.json\ninjected",
        "tests/../src/product.py",
    ],
)
def test_a_literal_that_cannot_name_a_committed_path_is_discarded(tmp_path: Path, literal: str) -> None:
    """Arbitrary strings become Git arguments, and a null byte cannot even reach a subprocess."""
    module = _load_provenance_module()
    body = f"CASE = Path({literal!r}).read_text()"
    base_ref, red_proof_path = _repository_with_data_read(tmp_path, body)

    (tmp_path / "tests" / "data" / "case.json").write_text('{"expected": true}\n', encoding="utf-8")
    final_ref = _commit(tmp_path, "chore: change data the malformed literal does not name")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


def test_a_file_relative_data_read_resolves_against_the_reading_module(tmp_path: Path) -> None:
    """``Path(__file__).parent / "data"`` names a directory beside the module, not beside the root."""
    module = _load_provenance_module()
    body = 'CASE = (Path(__file__).parent / "data" / "case.json").read_text()'
    base_ref, red_proof_path = _repository_with_data_read(tmp_path, body)

    (tmp_path / "tests" / "data" / "case.json").write_text('{"expected": true}\n', encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change the case the harness reads")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_a_data_read_through_a_symlink_binds_the_target(tmp_path: Path) -> None:
    """Pytest follows the link and consumes the target's bytes, which Git records separately."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    data_path = tmp_path / "tests" / "data"
    data_path.mkdir(parents=True)
    (data_path / "real.json").write_text('{"expected": false}\n', encoding="utf-8")
    (data_path / "case.json").symlink_to("real.json")
    (tmp_path / "tests" / "conftest.py").write_text(
        'from pathlib import Path\n\nCASE = Path("tests/data/case.json").read_text()\n', encoding="utf-8"
    )
    base_ref = _commit(tmp_path, "test: add linked data")
    (tmp_path / "tests" / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (data_path / "real.json").write_text('{"expected": true}\n', encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change the link target")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_an_undetermined_existence_check_is_stale_rather_than_absent(tmp_path: Path) -> None:
    """A Git call that could not answer is not evidence that a module is missing."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "conftest.py").write_text("import tests.support\n", encoding="utf-8")
    (tmp_path / "tests" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "tests" / "support.py").write_text("import tests.helper\n", encoding="utf-8")
    (tmp_path / "tests" / "helper.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add support")
    (tmp_path / "tests" / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    # Only the helper reached *through* the unreadable module changes, so accepting the proof
    # depends entirely on whether the unanswerable lookup was read as "absent".
    (tmp_path / "tests" / "helper.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change the transitively imported helper")

    original_git_bytes = module._git_bytes

    def timing_out_git_bytes(repo_root: Path, *arguments: str) -> Any:
        # A timeout reaches callers as an ordinary failure, whichever command was issued.
        if any("tests/support.py" in argument for argument in arguments):
            return subprocess.CompletedProcess(["git", *arguments], returncode=1, stdout=b"", stderr=b"")
        return original_git_bytes(repo_root, *arguments)

    module._git_bytes = timing_out_git_bytes
    try:
        module._tree_entry_mode_at_ref.cache_clear()
        module._python_tree_at_ref.cache_clear()
        findings = module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref)
    finally:
        module._git_bytes = original_git_bytes

    assert findings == ["stale-red-proof"]


# Every way a harness names data beside itself. The base differs in each; what they share is
# that it resolves to the reading module's own directory rather than to the repository root.
FILE_RELATIVE_BASE_SHAPES = (
    '(Path(__file__).parent / "data" / "case.json").read_text()',
    '(Path(__file__).resolve().parent / "data" / "case.json").read_text()',
    '(Path(__file__).parents[0] / "data" / "case.json").read_text()',
    '(Path(__file__).parent.parent / "tests" / "data" / "case.json").read_text()',
    '(Path(__file__).resolve().parents[1] / "tests" / "data" / "case.json").read_text()',
    'HERE = Path(__file__).parent\nCASE = (HERE / "data" / "case.json").read_text()',
    'ROOT = Path(__file__).resolve().parents[1]\nCASE = (ROOT / "tests" / "data" / "case.json").read_text()',
    '(Path(os.path.dirname(__file__)) / "data" / "case.json").read_text()',
)

# Joins whose base is decided at runtime. Reading them as root-relative would bind whatever
# committed file happens to share the remaining components, failing proofs on unrelated edits.
UNKNOWABLE_BASE_SHAPES = (
    'def fixture_case(tmp_path):\n    return (tmp_path / "tests" / "data" / "case.json").read_text()',
    'def fixture_case(request):\n    return (request.config.rootpath / "tests" / "data" / "case.json").read_text()',
    'def fixture_case(base):\n    return (base / "tests" / "data" / "case.json").read_text()',
)


@pytest.mark.parametrize("read", FILE_RELATIVE_BASE_SHAPES)
def test_a_data_read_resolves_every_knowable_path_base(tmp_path: Path, read: str) -> None:
    """The reading module's own directory is the base a harness names its data from."""
    module = _load_provenance_module()
    base_ref, red_proof_path = _repository_with_data_read(tmp_path, f"import os\n\nCASE = {read}")

    (tmp_path / "tests" / "data" / "case.json").write_text('{"expected": true}\n', encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change the case the harness reads")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


@pytest.mark.parametrize("read", UNKNOWABLE_BASE_SHAPES)
def test_a_join_from_an_unknowable_base_binds_nothing(tmp_path: Path, read: str) -> None:
    """A runtime base names no committed file, so treating it as root-relative binds the wrong one."""
    module = _load_provenance_module()
    base_ref, red_proof_path = _repository_with_data_read(tmp_path, read)

    (tmp_path / "tests" / "data" / "case.json").write_text('{"expected": true}\n', encoding="utf-8")
    final_ref = _commit(tmp_path, "chore: change a case nothing reads")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


def _repository_with_linked_data(tmp_path: Path, link_text: str) -> tuple[str, Path]:
    """Commit ``tests/data/case.json`` as a link to ``link_text`` beside a real target."""
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    data_path = tmp_path / "tests" / "data"
    data_path.mkdir(parents=True)
    (data_path / "real.json").write_text('{"expected": false}\n', encoding="utf-8")
    (data_path / "hop.json").symlink_to("real.json")
    (data_path / "case.json").symlink_to(link_text)
    (tmp_path / "tests" / "conftest.py").write_text(
        'from pathlib import Path\n\nCASE = Path("tests/data/case.json").read_text()\n', encoding="utf-8"
    )
    base_ref = _commit(tmp_path, "test: add linked data")
    (tmp_path / "tests" / "test_proof.py").write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    return base_ref, red_proof_path


def test_a_data_read_follows_a_chain_of_links_to_its_target(tmp_path: Path) -> None:
    """Each hop is bound, because editing any of them changes the bytes the read returns."""
    module = _load_provenance_module()
    base_ref, red_proof_path = _repository_with_linked_data(tmp_path, "hop.json")

    (tmp_path / "tests" / "data" / "real.json").write_text('{"expected": true}\n', encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change the far end of the chain")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


@pytest.mark.parametrize("link_text", ["../../../outside.json", "/etc/hostname", "missing.json", "case.json"])
def test_a_link_that_cannot_be_bound_is_stale(tmp_path: Path, link_text: str) -> None:
    """A link out of the checkout, at nothing, or at itself binds no bytes and is not proof."""
    module = _load_provenance_module()
    base_ref, red_proof_path = _repository_with_linked_data(tmp_path, link_text)

    (tmp_path / "tests" / "data" / "real.json").write_text('{"expected": true}\n', encoding="utf-8")
    final_ref = _commit(tmp_path, "chore: touch the repository after the red source")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def _repository_with_two_tests(
    tmp_path: Path, other_body: str, selected_body: str = "assert False"
) -> tuple[str, Path]:
    """Commit a selected test beside an unselected one, and return the red proof."""
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "tests" / "helper.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add helper")
    (tmp_path / "tests" / "test_proof.py").write_text(
        f"def test_selected() -> None:\n    {selected_body}\n\n\ndef test_other() -> None:\n    {other_body}\n",
        encoding="utf-8",
    )
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)
    return base_ref, red_proof_path


def test_an_import_only_inside_an_unselected_test_body_is_not_bound(tmp_path: Path) -> None:
    """Exact selection runs one node, so another test's body never executes its imports."""
    module = _load_provenance_module()
    base_ref, red_proof_path = _repository_with_two_tests(tmp_path, "import tests.helper")

    (tmp_path / "tests" / "helper.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "chore: change a helper only the unselected test imports")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


@pytest.mark.parametrize(
    ("other_body", "selected_body"),
    [
        # The selected body imports it, so it runs.
        ("pass", "import tests.helper"),
        # The unselected function is called by the selected one, so its body runs after all.
        ("import tests.helper", "test_other()"),
    ],
)
def test_an_import_a_selected_run_can_reach_stays_bound(tmp_path: Path, other_body: str, selected_body: str) -> None:
    """Narrowing may only drop bodies nothing invokes; anything reachable still binds."""
    module = _load_provenance_module()
    base_ref, red_proof_path = _repository_with_two_tests(tmp_path, other_body, selected_body)

    (tmp_path / "tests" / "helper.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change a helper the selected run reaches")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]


def test_a_fixture_body_stays_bound_beside_an_unselected_test(tmp_path: Path) -> None:
    """Which fixtures a run activates is not statically decidable, so fixtures are never dropped."""
    module = _load_provenance_module()
    body = (
        "import pytest\n\n\n@pytest.fixture\ndef support():\n    import tests.helper\n\n    return tests.helper\n\n\n"
        "def test_selected(support) -> None:\n    assert False\n\n\ndef test_other() -> None:\n    pass\n"
    )
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "tests" / "helper.py").write_text("VALUE = False\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "test: add helper")
    (tmp_path / "tests" / "test_proof.py").write_text(body, encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    (tmp_path / "tests" / "helper.py").write_text("VALUE = True\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: change a helper the fixture imports")

    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == [
        "stale-red-proof"
    ]
