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


@pytest.mark.parametrize("configuration_path", ["pyproject.toml", "pytest.ini", "tox.ini", "setup.cfg"])
def test_git_bound_red_proof_rejects_changed_pytest_configuration(tmp_path: Path, configuration_path: str) -> None:
    """Pytest ini options decide collection and outcome, so they must stay bound to the red failure."""
    module = _load_provenance_module()
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "requirements@example.test")
    _git(tmp_path, "config", "user.name", "Requirements proof")
    configuration = tmp_path / configuration_path
    configuration.write_text("[pytest]\nfilterwarnings =\n    error\n", encoding="utf-8")
    base_ref = _commit(tmp_path, "chore: add pytest configuration")
    test_path = tmp_path / "tests" / "test_proof.py"
    test_path.parent.mkdir()
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(tmp_path, "test: add red proof")
    red_proof_path = tmp_path / ".git" / "red.json"
    _write_red_proof(red_proof_path, tmp_path, red_ref, base_ref)

    configuration.write_text("[pytest]\nfilterwarnings =\n    ignore\n", encoding="utf-8")
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
