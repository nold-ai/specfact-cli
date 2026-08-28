"""Contract coverage for Git-bound Requirements red-proof provenance."""

from __future__ import annotations

import ast
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

    def _pytest_plugin_names(self, tree: ast.AST) -> list[list[str]]:
        raise NotImplementedError

    def bind_red_proof(self, red_proof_path: Path, repo_root: Path, *, base_ref: str) -> None:
        raise NotImplementedError

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
    path.write_text(
        json.dumps(
            {
                "gate_decision": "pass",
                "observed_maturity": "red",
                "mapping_digest": f"sha256:{'a' * 64}",
                "plan_digest": f"sha256:{'b' * 64}",
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

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "delivery.py").write_text("VALUE = 1\n", encoding="utf-8")
    final_ref = _commit(tmp_path, "fix: deliver behavior")
    assert module.validate_prior_red_proof(red_proof_path, tmp_path, base_ref=base_ref, final_ref=final_ref) == []


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
    """Dynamic import-time plugin bindings must invalidate retained proof."""
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
        "prior-red-proof-invalid"
    ]


def test_pytest_plugin_discovery_ignores_function_local_assignments() -> None:
    """Module control flow counts, while function-local plugin assignments do not."""
    module = _load_provenance_module()
    tree = ast.parse(
        'pytest_plugins = ("tests.helpers.active",)\n'
        "if True:\n"
        '    pytest_plugins = ("tests.helpers.conditional",)\n'
        "try:\n"
        '    pytest_plugins = ("tests.helpers.tried",)\n'
        "except RuntimeError:\n"
        "    pass\n"
        'pytest_plugins: tuple[str, ...] = ("tests.helpers.annotated",)\n'
        "globals().update(unrelated_binding=True)\n"
        "class PluginMetadata:\n"
        '    pytest_plugins = ("tests.helpers.class_local",)\n'
        '    locals().update(pytest_plugins=("tests.helpers.also_class_local",))\n'
        '    vars().update(pytest_plugins=("tests.helpers.still_class_local",))\n'
        "    delayed = (\n"
        '        globals().update(pytest_plugins=("tests.helpers.deferred",))\n'
        "        for _ in ()\n"
        "    )\n"
        "    def register_later(self) -> None:\n"
        '        globals().update(pytest_plugins=("tests.helpers.inactive_method",))\n'
        "def helper() -> None:\n"
        '    pytest_plugins = ("tests.helpers.inactive",)\n'
        '    exec("pytest_plugins = (\\"tests.helpers.also_inactive\\",)")\n'
    )

    assert module._pytest_plugin_names(tree) == [
        ["tests", "helpers", "active"],
        ["tests", "helpers", "conditional"],
        ["tests", "helpers", "tried"],
        ["tests", "helpers", "annotated"],
    ]


@pytest.mark.parametrize(
    "source",
    [
        "pytest_plugins = discover_plugins()\n",
        "from tests.helpers import plugins as pytest_plugins\n",
        'match ("tests.helpers.matched",):\n    case pytest_plugins:\n        pass\n',
        'globals()["pytest_plugins"] = ("tests.helpers.hidden",)\n',
        'plugin_key = "pytest_plugins"\nglobals()[plugin_key] = ("tests.helpers.hidden",)\n',
        'globals().__setitem__("pytest_plugins", ("tests.helpers.hidden",))\n',
        'globals().update(pytest_plugins=("tests.helpers.hidden",))\n',
        'globals().update({"pytest_plugins": ("tests.helpers.hidden",)})\n',
        "globals().update(dynamic_bindings)\n",
        'namespace = globals()\nnamespace["pytest_plugins"] = ("tests.helpers.hidden",)\n',
        'namespace = locals()\nnamespace.update(pytest_plugins=("tests.helpers.hidden",))\n',
        'namespace = vars()\nalias = namespace\nalias.setdefault("pytest_plugins", ("tests.helpers.hidden",))\n',
        'namespace_factory = globals\nnamespace_factory()["pytest_plugins"] = ("tests.helpers.hidden",)\n',
        'getattr(globals(), "update")(pytest_plugins=("tests.helpers.hidden",))\n',
        'exec("pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
        'run = exec\nrun("pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
        'class Plugins:\n    globals().update(pytest_plugins=("tests.helpers.hidden",))\n',
        'class Plugins:\n    namespace = globals()\n    namespace["pytest_plugins"] = ("tests.helpers.hidden",)\n',
        'class Plugins:\n    global pytest_plugins\n    pytest_plugins = ("tests.helpers.hidden",)\n',
        'class Plugins:\n    exec("global pytest_plugins; pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
        'class Plugins:\n    eval("globals().update(pytest_plugins=(\\"tests.helpers.hidden\\",))")\n',
        'class Plugins:\n    getattr(globals(), "update")(pytest_plugins=("tests.helpers.hidden",))\n',
        'class Plugins:\n    run = exec\n    run("global pytest_plugins; pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
        'import builtins\nbuiltins.exec("pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
        'import builtins as runtime\nruntime.eval("globals().update(pytest_plugins=(\\"tests.helpers.hidden\\",))")\n',
        'from builtins import exec as run\nrun("pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
        'for namespace in [globals()]:\n    namespace["pytest_plugins"] = ("tests.helpers.hidden",)\n',
        'namespace, = (globals(),)\nnamespace.update(pytest_plugins=("tests.helpers.hidden",))\n',
        '[namespace.setdefault("pytest_plugins", ("tests.helpers.hidden",)) for namespace in [globals()]]\n',
        'from contextlib import nullcontext\nwith nullcontext(globals()) as namespace:\n    namespace.update(pytest_plugins=("tests.helpers.hidden",))\n',
        'for run in [exec]:\n    run("pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
        'match globals():\n    case namespace:\n        namespace["pytest_plugins"] = ("tests.helpers.hidden",)\n',
        'namespace = globals()\nclass Plugins:\n    namespace["pytest_plugins"] = ("tests.helpers.hidden",)\n',
        'import builtins\nclass Plugins:\n    builtins.exec("global pytest_plugins; pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
        'class Plugins:\n    match globals():\n        case namespace:\n            namespace["pytest_plugins"] = ("tests.helpers.hidden",)\n',
        '__builtins__["exec"]("pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
        '__import__("builtins").eval("globals().update(pytest_plugins=(\\"tests.helpers.hidden\\",))")\n',
        'import builtins\ngetattr(builtins, "exec")("pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
    ],
)
def test_pytest_plugin_discovery_rejects_unresolved_module_bindings(source: str) -> None:
    """Computed, imported, captured, and namespace bindings must fail closed."""
    module = _load_provenance_module()

    with pytest.raises(ValueError, match=r"^prior-red-proof-invalid$"):
        module._pytest_plugin_names(ast.parse(source))


def test_pytest_plugin_discovery_rejects_function_default_module_binding() -> None:
    """Function defaults execute at module import and may bind the active global."""
    module = _load_provenance_module()
    source = 'def helper(bound=(pytest_plugins := ("tests.helpers.default_bound",))):\n    pass\n'

    with pytest.raises(ValueError, match=r"^prior-red-proof-invalid$"):
        module._pytest_plugin_names(ast.parse(source))


def test_pytest_plugin_discovery_allows_legitimate_namespace_access() -> None:
    """Read-only and ordinary-mapping namespace patterns must remain compatible."""
    module = _load_provenance_module()
    sources = (
        (
            "class Metadata:\n"
            '    module_name = globals().get("__name__")\n'
            '    module_package = globals()["__package__"]\n'
            '    lookup = getattr(globals(), "get")\n'
            'for namespace in [{}]:\n    namespace.update(pytest_plugins=("tests.helpers.local",))\n'
            'namespace, = ({},)\nnamespace["pytest_plugins"] = ("tests.helpers.local",)\n'
            '[item.setdefault("pytest_plugins", ("tests.helpers.local",)) for item in [{}]]\n'
            "from contextlib import nullcontext\n"
            'with nullcontext({}) as item:\n    item.update(pytest_plugins=("tests.helpers.local",))\n'
            'match {}:\n    case item:\n        item.update(pytest_plugins=("tests.helpers.local",))\n'
            '[item.get("__name__") for item in [globals()]]\n'
            'item = {}\nitem.update(pytest_plugins=("tests.helpers.local",))\n'
            'for safe, namespace in [({}, globals())]:\n    safe["pytest_plugins"] = ("tests.helpers.local",)\n'
        ),
        (
            'namespace = globals()\nnamespace = {}\nnamespace["pytest_plugins"] = ("tests.helpers.local",)\n'
            'import builtins\nruntime = builtins\nruntime = object()\nruntime.exec("ordinary payload")\n'
            'run = exec\nrun = print\nrun("ordinary payload")\n'
        ),
        (
            'match {"ns": {}}:\n    case {"ns": captured}:\n'
            '        captured["pytest_plugins"] = ("tests.helpers.local",)\n'
            'match {"ns": globals()}:\n    case {"ns": _, **rest}:\n'
            '        rest["pytest_plugins"] = ("tests.helpers.local",)\n'
            "match {None: {}}:\n    case {None: captured}:\n"
            '        captured["pytest_plugins"] = ("tests.helpers.local",)\n'
        ),
    )

    for source in sources:
        assert module._pytest_plugin_names(ast.parse(source)) == []


@pytest.mark.parametrize(
    "source",
    [
        'import builtins\nruntime = builtins\nruntime.exec("pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
        'import builtins\nruntime = builtins\nagain = runtime\nagain.eval("globals().update(pytest_plugins=(\\"tests.helpers.hidden\\",))")\n',
    ],
)
def test_pytest_plugin_discovery_rejects_builtins_module_aliases(source: str) -> None:
    """Aliases of the imported builtins owner must retain exec/eval authority."""
    module = _load_provenance_module()

    with pytest.raises(ValueError, match=r"^prior-red-proof-invalid$"):
        module._pytest_plugin_names(ast.parse(source))


@pytest.mark.parametrize(
    "source",
    [
        'match {"ns": globals()}:\n    case {"ns": namespace}:\n        namespace["pytest_plugins"] = ("tests.helpers.hidden",)\n',
        'match {"safe": {}, "ns": globals()}:\n    case {"ns": namespace, "safe": _}:\n        namespace.update(pytest_plugins=("tests.helpers.hidden",))\n',
        'match {"outer": {"ns": globals()}}:\n    case {"outer": {"ns": namespace}}:\n        namespace.setdefault("pytest_plugins", ("tests.helpers.hidden",))\n',
        'match {None: globals()}:\n    case {None: namespace}:\n        namespace["pytest_plugins"] = ("tests.helpers.hidden",)\n',
        'match {**{"ns": globals()}}:\n    case {"ns": namespace}:\n        namespace["pytest_plugins"] = ("tests.helpers.hidden",)\n',
    ],
)
def test_pytest_plugin_discovery_rejects_mapping_pattern_namespace_captures(source: str) -> None:
    """Mapping captures must retain their corresponding namespace subject value."""
    module = _load_provenance_module()

    with pytest.raises(ValueError, match=r"^prior-red-proof-invalid$"):
        module._pytest_plugin_names(ast.parse(source))


@pytest.mark.parametrize(
    "source",
    [
        'namespace = globals()\nnamespace["pytest_plugins"] = ("tests.helpers.hidden",)\nnamespace = {}\n',
        'namespace = globals()\nnamespace = {}\nnamespace = globals()\nnamespace["pytest_plugins"] = ("tests.helpers.hidden",)\n',
        'namespace = globals()\nif enabled:\n    namespace = {}\nnamespace["pytest_plugins"] = ("tests.helpers.hidden",)\n',
        'namespace = {}\nif enabled:\n    namespace = globals()\nnamespace["pytest_plugins"] = ("tests.helpers.hidden",)\n',
        'for namespace in [globals()]:\n    pass\nnamespace["pytest_plugins"] = ("tests.helpers.hidden",)\n',
        'from contextlib import nullcontext\nwith nullcontext(globals()) as namespace:\n    pass\nnamespace["pytest_plugins"] = ("tests.helpers.hidden",)\n',
        'match globals():\n    case namespace:\n        pass\nnamespace["pytest_plugins"] = ("tests.helpers.hidden",)\n',
        'import builtins\nruntime = builtins\nruntime.exec("pytest_plugins = (\\"tests.helpers.hidden\\",)")\nruntime = object()\n',
        'import builtins\nruntime = object()\nif enabled:\n    runtime = builtins\nruntime.exec("pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
    ],
)
def test_pytest_plugin_discovery_keeps_live_or_conditional_aliases_fail_closed(source: str) -> None:
    """Use-before-shadow, re-alias, and conditional replacement remain unsafe."""
    module = _load_provenance_module()

    with pytest.raises(ValueError, match=r"^prior-red-proof-invalid$"):
        module._pytest_plugin_names(ast.parse(source))


@pytest.mark.parametrize(
    "source",
    [
        '[pytest_plugins for pytest_plugins in [("tests.helpers.local",)]]\n',
        '{pytest_plugins for pytest_plugins in [("tests.helpers.local",)]}\n',
        '{pytest_plugins: True for pytest_plugins in [("tests.helpers.local",)]}\n',
        '(pytest_plugins for pytest_plugins in [("tests.helpers.local",)])\n',
    ],
)
def test_pytest_plugin_discovery_ignores_comprehension_iteration_targets(source: str) -> None:
    """Python 3 comprehension targets do not bind the surrounding module namespace."""
    module = _load_provenance_module()

    assert module._pytest_plugin_names(ast.parse(source)) == []


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
