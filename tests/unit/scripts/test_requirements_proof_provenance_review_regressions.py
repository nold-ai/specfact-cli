"""Regression coverage for security-review bypasses outside the retained red selector set."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[3]
PROVENANCE_SCRIPT = REPO_ROOT / "scripts" / "requirements_proof_provenance.py"


def _load_provenance_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("requirements_proof_provenance_review", PROVENANCE_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


HOSTILE_SOURCES = (
    "def __getattr__(name):\n    if name == 'pytest_plugins':\n        return ('tests.helpers.hidden',)\n    raise AttributeError(name)\n",
    "__getattr__ = lambda name: ('tests.helpers.hidden',) if name == 'pytest_plugins' else None\n",
    'import sys\nsys.modules[__name__].__dict__["pytest_plugins"] = ("tests.helpers.hidden",)\n',
    'import sys\nvars(sys.modules[__name__])["pytest_plugins"] = ("tests.helpers.hidden",)\n',
    "def bind():\n    global pytest_plugins\n    pytest_plugins = ('tests.helpers.hidden',)\nbind()\n",
    'import sys as runtime\nruntime.modules[__name__].pytest_plugins = ("tests.helpers.hidden",)\n',
    'import sys\nmodules = sys.modules\nmodules[__name__].pytest_plugins = ("tests.helpers.hidden",)\n',
    'from sys import modules\nmodules[__name__].pytest_plugins = ("tests.helpers.hidden",)\n',
    'import builtins, sys\nbuiltins.setattr(sys.modules[__name__], "pytest_plugins", ("tests.helpers.hidden",))\n',
    'import sys\nfrom builtins import setattr as assign\nassign(sys.modules[__name__], "pytest_plugins", '
    '("tests.helpers.hidden",))\n',
    'import sys\nassign = setattr\nassign(sys.modules[__name__], "pytest_plugins", ("tests.helpers.hidden",))\n',
    "import sys\nmodule = sys.modules.setdefault(__name__, object())\n"
    'module.pytest_plugins = ("tests.helpers.hidden",)\n',
    'import sys\nmodule = sys.modules.get(__name__)\nmodule.pytest_plugins = ("tests.helpers.hidden",)\n',
    'import sys\nmodule = sys.modules.__getitem__(__name__)\nmodule.pytest_plugins = ("tests.helpers.hidden",)\n',
    "import sys\nmodule_name = __name__\nmodule = sys.modules.get(module_name)\n"
    'module.pytest_plugins = ("tests.helpers.hidden",)\n',
    'import sys\nsys.modules[__name__].pytest_plugins = ("tests.helpers.hidden",)\n',
    'import sys\nsetattr(sys.modules[__name__], "pytest_plugins", ("tests.helpers.hidden",))\n',
    'import sys\nmodule = sys.modules[__name__]\nmodule.pytest_plugins = ("tests.helpers.hidden",)\n',
    'import sys\nmodule = sys.modules[__name__]\nsetattr(module, "pytest_plugins", ("tests.helpers.hidden",))\n',
    'import importlib\nmodule = importlib.import_module(__name__)\nmodule.pytest_plugins = ("tests.helpers.hidden",)\n',
    'module = __import__(__name__, fromlist=("pytest_plugins",))\nmodule.pytest_plugins = ("tests.helpers.hidden",)\n',
    'import importlib as loader\nmodule = loader.import_module(__name__)\nmodule.pytest_plugins = ("tests.helpers.hidden",)\n',
    'module_name = __name__\nmodule = __import__(module_name, fromlist=("pytest_plugins",))\nmodule.pytest_plugins = ("tests.helpers.hidden",)\n',
    'import builtins\nruntime = builtins.__dict__\nruntime["exec"]("pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
    'import operator\noperator.setitem(globals(), "pytest_plugins", ("tests.helpers.hidden",))\n',
    'from operator import setitem as bind\nbind(globals(), "pytest_plugins", ("tests.helpers.hidden",))\n',
    'import operator\nput = operator.setitem\nput(globals(), "pytest_plugins", ("tests.helpers.hidden",))\n',
    'import operator\noperator.setitem(*(globals(), "pytest_plugins", ("tests.helpers.hidden",)))\n',
    'import operator\noperator.setitem.__call__(globals(), "pytest_plugins", ("tests.helpers.hidden",))\n',
    'import operator\ngetattr(operator.setitem, "__call__")(globals(), "pytest_plugins", ("tests.helpers.hidden",))\n',
    'import operator\ngetattr(getattr(operator, "setitem"), "__call__")('
    'globals(), "pytest_plugins", ("tests.helpers.hidden",))\n',
    'dict.__setitem__(*(globals(), "pytest_plugins", ("tests.helpers.hidden",)))\n',
    'import operator\ngetattr(operator, "setitem")(globals(), "pytest_plugins", ("tests.helpers.hidden",))\n',
    'getattr(dict, "__setitem__")(globals(), "pytest_plugins", ("tests.helpers.hidden",))\n',
    'import operator\noperator.__dict__["setitem"](globals(), "pytest_plugins", ("tests.helpers.hidden",))\n',
    'import operator\nvars(operator)["setitem"](globals(), "pytest_plugins", ("tests.helpers.hidden",))\n',
    'dict.__setitem__(globals(), "pytest_plugins", ("tests.helpers.hidden",))\n',
    'import builtins\nruntime = builtins.__dict__\nruntime.get("exec")('
    '"pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
    'import builtins\nruntime = builtins.__dict__\nruntime.__getitem__("exec")('
    '"pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
    'import builtins\nruntime = builtins.__dict__\nruntime.setdefault("exec")('
    '"pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
    'import builtins\nruntime = builtins.__dict__\nruntime.pop("exec")('
    '"pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
    'exec.__call__("pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
    'import builtins\nruntime = builtins.__dict__\nruntime["exec"].__call__('
    '"pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
    'getattr(exec, "__call__")("pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
    'import builtins\nruntime = builtins.__dict__.copy()\nruntime["exec"]('
    '"pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
    'import builtins\nruntime = dict(builtins.__dict__)\nruntime["exec"]('
    '"pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
    'import builtins\nruntime = {**builtins.__dict__}\nruntime["exec"]('
    '"pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
    'import builtins\nruntime = builtins.__dict__\ngetattr(runtime, "get")("exec")('
    '"pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
    'import builtins\nruntime = builtins.__dict__\ngetattr(runtime, "__getitem__")("exec")('
    '"pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
    'if enabled:\n    print = exec\nrun = print\nrun("pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
    "from types import SimpleNamespace\nif enabled:\n    SimpleNamespace = factory\n"
    "runtime = SimpleNamespace(exec=lambda value: None)\n"
    'runtime.exec("pytest_plugins = (\\"tests.helpers.hidden\\",)")\n',
)


def _commit(repo_root: Path, message: str) -> str:
    subprocess.run(["git", "add", "."], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "--no-gpg-sign", "-m", message], cwd=repo_root, check=True)
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_root, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _initialize_bound_red_proof(
    module: ModuleType,
    repo_root: Path,
    *,
    pytest_configuration: tuple[str, str] | None = None,
    initial_files: dict[str, str] | None = None,
) -> tuple[Path, str]:
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "requirements@example.test"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Requirements proof"], cwd=repo_root, check=True)
    (repo_root / "README.md").write_text("# proof\n", encoding="utf-8")
    if pytest_configuration is not None:
        config_path, content = pytest_configuration
        (repo_root / config_path).write_text(content, encoding="utf-8")
    for relative_path, content in (initial_files or {}).items():
        target = repo_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    base_ref = _commit(repo_root, "base")
    test_path = repo_root / "tests" / "test_proof.py"
    test_path.parent.mkdir(exist_ok=True)
    test_path.write_text("def test_selected() -> None: assert False\n", encoding="utf-8")
    red_ref = _commit(repo_root, "red test")
    proof_path = repo_root / ".git" / "red.json"
    junit = (
        b'<testsuite><testcase><properties><property name="specfact.selector" '
        b'value="tests/test_proof.py::test_selected"/><property name="specfact.runner" value="pytest"/>'
        b'<property name="specfact.python" value="3.12"/><property name="specfact.pytest" value="9.1"/>'
        b"</properties><failure/></testcase></testsuite>"
    )
    proof_path.with_suffix(".xml").write_bytes(junit)
    proof_path.write_text(
        json.dumps(
            {
                "gate_decision": "pass",
                "observed_maturity": "red",
                "mapping_digest": f"sha256:{'a' * 64}",
                "plan_digest": f"sha256:{'b' * 64}",
                "execution_proof": {
                    "run_stage": "red",
                    "source_ref": red_ref,
                    "selectors": ["tests/test_proof.py::test_selected"],
                    "junit_digest": f"sha256:{hashlib.sha256(junit).hexdigest()}",
                },
            }
        ),
        encoding="utf-8",
    )
    module.bind_red_proof(proof_path, repo_root, base_ref=base_ref)
    return proof_path, base_ref


def test_pytest_configuration_plugin_changed_after_red_invalidates_proof(tmp_path: Path) -> None:
    """A plugin loaded by red-time addopts remains part of the immutable harness."""
    configurations = (
        ("pytest.ini", "[pytest]\naddopts = -p tests.helpers.hidden\n"),
        ("pytest.toml", '[pytest]\naddopts = ["-p", "tests.helpers.hidden"]\n'),
    )
    for index, configuration in enumerate(configurations):
        module = _load_provenance_module()
        repository = tmp_path / f"repository-{index}"
        repository.mkdir()
        proof_path, base_ref = _initialize_bound_red_proof(module, repository, pytest_configuration=configuration)
        plugin_path = repository / "tests" / "helpers" / "hidden.py"
        plugin_path.parent.mkdir()
        plugin_path.write_text("VALUE = True\n", encoding="utf-8")
        final_ref = _commit(repository, "add configured pytest plugin")
        assert module.validate_prior_red_proof(proof_path, repository, base_ref=base_ref, final_ref=final_ref) == [
            "stale-red-proof"
        ]


def test_compact_pytest_plugin_options_changed_after_red_invalidate_proof(tmp_path: Path) -> None:
    """Compact pytest plugin flags retain the same repository plugin inputs."""
    for index, option in enumerate(("-ptests.helpers.hidden", "-p=tests.helpers.hidden")):
        module = _load_provenance_module()
        repository = tmp_path / f"repository-{index}"
        repository.mkdir()
        proof_path, base_ref = _initialize_bound_red_proof(
            module,
            repository,
            pytest_configuration=("pytest.ini", f"[pytest]\naddopts = {option}\n"),
            initial_files={"tests/helpers/hidden.py": "VALUE = 'red'\n"},
        )
        plugin_path = repository / "tests" / "helpers" / "hidden.py"
        plugin_path.write_text("VALUE = 'final'\n", encoding="utf-8")
        final_ref = _commit(repository, "change configured pytest plugin")
        assert module.validate_prior_red_proof(proof_path, repository, base_ref=base_ref, final_ref=final_ref) == [
            "stale-red-proof"
        ]


def test_pytest_configuration_added_after_red_invalidates_proof(tmp_path: Path) -> None:
    """A post-red addopts plugin cannot change the selected-test harness."""
    config_paths = (
        "pytest.toml",
        ".pytest.toml",
        "pytest.ini",
        ".pytest.ini",
        "pyproject.toml",
        "tox.ini",
        "setup.cfg",
        "tests/pytest.ini",
    )
    for index, config_path in enumerate(config_paths):
        module = _load_provenance_module()
        repository = tmp_path / f"repository-{index}"
        repository.mkdir()
        proof_path, base_ref = _initialize_bound_red_proof(module, repository)
        (repository / config_path).write_text("[pytest]\naddopts = -p tests.helpers.hidden\n", encoding="utf-8")
        final_ref = _commit(repository, "inject pytest plugin")
        assert module.validate_prior_red_proof(proof_path, repository, base_ref=base_ref, final_ref=final_ref) == [
            "stale-red-proof"
        ]


def test_review_bypasses_fail_closed() -> None:
    """Every reviewed import-time namespace binding remains authoritative."""
    for source in HOSTILE_SOURCES:
        module = _load_provenance_module()
        try:
            module._pytest_plugin_names(ast.parse(source))
        except ValueError as error:
            assert str(error) == "prior-red-proof-invalid"
        else:
            raise AssertionError(f"review bypass was accepted: {source}")


SAFE_SOURCES = (
    'import sys\nmodule = sys.modules.get("unrelated")\nmodule.ordinary = ("ordinary",)\n',
    'run = exec\nrun = print\nrun("ordinary payload")\n',
    'update = globals().update\nupdate = {}.update\nupdate(value="ordinary payload")\n',
    "from types import SimpleNamespace\nruntime = SimpleNamespace(exec=lambda value: None)\n"
    'runtime.exec("ordinary payload")\n',
    "from types import SimpleNamespace\nruntime = SimpleNamespace(exec=lambda value: None)\n"
    'runtime.exec.__call__("ordinary payload")\n',
)


DYNAMIC_IMPORT_SOURCES = (
    'import importlib\nimportlib.import_module("tests.helpers.hidden")\n',
    '__import__("tests.helpers.hidden", fromlist=("VALUE",))\n',
    'import importlib as loader\nload = loader.import_module\nload("tests.helpers.hidden")\n',
    'import importlib\ngetattr(importlib, "import_module")("tests.helpers.hidden")\n',
    'import importlib\nload = getattr(importlib, "import_module")\nload("tests.helpers.hidden")\n',
    'import importlib\ngetattr(importlib, "import_module").__call__("tests.helpers.hidden")\n',
    'import importlib\nload = getattr(importlib, "import_module").__call__\nload("tests.helpers.hidden")\n',
    'import importlib\ngetattr(getattr(importlib, "import_module"), "__call__")("tests.helpers.hidden")\n',
    'import importlib\nvars(importlib)["import_module"]("tests.helpers.hidden")\n',
    'import importlib\nimportlib.__dict__["import_module"]("tests.helpers.hidden")\n',
    'import importlib\nnamespace = vars(importlib)\nnamespace["import_module"]("tests.helpers.hidden")\n',
    'import importlib\nnamespace = importlib.__dict__\nnamespace["import_module"]("tests.helpers.hidden")\n',
    'import importlib\nvars(importlib).get("import_module")("tests.helpers.hidden")\n',
    'import importlib\nimportlib.__dict__.__getitem__("import_module")("tests.helpers.hidden")\n',
    "import importlib\nnamespace = vars(importlib)\nlookup = namespace.get\n"
    'lookup("import_module")("tests.helpers.hidden")\n',
    "import importlib\nnamespace = importlib.__dict__\nlookup = namespace.__getitem__\n"
    'lookup("import_module")("tests.helpers.hidden")\n',
    'import importlib\nnamespace = vars(importlib)\nnamespace.get.__call__("import_module")("tests.helpers.hidden")\n',
)

AMBIGUOUS_DYNAMIC_IMPORT_SOURCES = (
    "import importlib\nimportlib.import_module(module_name)\n",
    "import importlib\ngetattr(importlib, loader_name)('tests.helpers.hidden')\n",
    'import importlib\nnamespace = vars(importlib)\nnamespace[loader_name]("tests.helpers.hidden")\n',
    'import importlib\nnamespace = importlib.__dict__\nnamespace.get(loader_name)("tests.helpers.hidden")\n',
    'import importlib\nnamespace = vars(importlib)\ngetattr(namespace, selector)("import_module")('
    '"tests.helpers.hidden")\n',
    "import importlib\nnamespace = vars(importlib)\nlookup = namespace.get\n"
    'lookup(loader_name)("tests.helpers.hidden")\n',
)


def _assert_dynamic_import_retained(module: ModuleType, source: str) -> None:
    imported = module._import_module_names(ast.parse(source), "tests/test_proof.py")
    assert ["tests", "helpers", "hidden"] in imported


def _assert_dynamic_import_rejected(module: ModuleType, source: str) -> None:
    try:
        module._import_module_names(ast.parse(source), "tests/test_proof.py")
    except ValueError as error:
        assert str(error) == "prior-red-proof-invalid"
    else:
        raise AssertionError("ambiguous dynamic import was accepted")


def test_dynamic_repository_imports_are_retained_or_fail_closed(tmp_path: Path) -> None:
    """Dynamic import APIs must retain literal targets and reject ambiguity."""
    del tmp_path
    module = _load_provenance_module()
    for source in DYNAMIC_IMPORT_SOURCES:
        _assert_dynamic_import_retained(module, source)
    assert ["json"] in module._import_module_names(
        ast.parse('import importlib\nimportlib.import_module("json")\n'),
        "tests/test_proof.py",
    )
    for source in AMBIGUOUS_DYNAMIC_IMPORT_SOURCES:
        _assert_dynamic_import_rejected(module, source)


def test_dynamic_repository_import_change_after_red_invalidates_proof(tmp_path: Path) -> None:
    """A dynamically imported helper remains immutable after the red source."""
    module = _load_provenance_module()
    repository = tmp_path / "repository"
    repository.mkdir()
    proof_path, base_ref = _initialize_bound_red_proof(
        module,
        repository,
        initial_files={
            "conftest.py": 'import importlib\nimportlib.import_module("tests.helpers.hidden")\n',
            "tests/helpers/hidden.py": "VALUE = 'red'\n",
        },
    )
    helper = repository / "tests" / "helpers" / "hidden.py"
    helper.write_text("VALUE = 'final'\n", encoding="utf-8")
    final_ref = _commit(repository, "change dynamically imported helper")
    assert module.validate_prior_red_proof(
        proof_path,
        repository,
        base_ref=base_ref,
        final_ref=final_ref,
    ) == ["stale-red-proof"]


def test_core_proof_inputs_and_selected_package_initializers_are_retained(tmp_path: Path) -> None:
    """Every fixed producer and implicit package initializer must be freshness-bound."""
    module = _load_provenance_module()
    repository = tmp_path / "repository"
    repository.mkdir()
    proof_path, base_ref = _initialize_bound_red_proof(
        module,
        repository,
        initial_files={
            "tests/__init__.py": "VALUE = 'red'\n",
            "scripts/__init__.py": "VALUE = 'red'\n",
            "uv.lock": "version = 1\n",
            "scripts/requirements_proof_executor.py": "VALUE = 'red'\n",
            "scripts/requirements_proof_pytest_plugin.py": "VALUE = 'red'\n",
        },
    )

    for index, path in enumerate(
        (
            "tests/__init__.py",
            "scripts/__init__.py",
            "uv.lock",
            "scripts/requirements_proof_executor.py",
            "scripts/requirements_proof_pytest_plugin.py",
        )
    ):
        checkout = repository.parent / f"candidate-{index}"
        subprocess.run(["git", "clone", "--quiet", str(repository), str(checkout)], check=True)
        target = checkout / path
        target.write_text(target.read_text(encoding="utf-8") + "VALUE = 'final'\n", encoding="utf-8")
        final_ref = _commit(checkout, f"change {path}")
        candidate_proof = checkout / ".git" / "red.json"
        candidate_proof.write_bytes(proof_path.read_bytes())
        candidate_proof.with_suffix(".xml").write_bytes(proof_path.with_suffix(".xml").read_bytes())
        assert module.validate_prior_red_proof(
            candidate_proof,
            checkout,
            base_ref=base_ref,
            final_ref=final_ref,
        ) == ["stale-red-proof"]


def test_review_controls_preserve_proven_safe_shadows() -> None:
    """Definite inert replacements remain compatible after fail-closed review fixes."""
    for source in SAFE_SOURCES:
        module = _load_provenance_module()
        assert module._pytest_plugin_names(ast.parse(source)) == []
    module = _load_provenance_module()
    assert (
        module._pytest_plugin_names(
            ast.parse(
                'from types import SimpleNamespace\nmodule = SimpleNamespace()\nmodule.pytest_plugins = ("ordinary",)\n'
            )
        )
        == []
    )
    assert (
        module._pytest_plugin_names(
            ast.parse("class Box:\n    pass\nbox = Box()\nbox.pytest_plugins = ('ordinary',)\n")
        )
        == []
    )


def test_external_digest_is_forwarded_during_ordinary_cycle_revalidation(tmp_path: Path) -> None:
    """A derived cycle receipt must revalidate the exact external green binding."""
    module = _load_provenance_module()
    observed: dict[str, object] = {}
    trusted = type(
        "Trusted",
        (),
        {"cycle_base": "a" * 40, "run_id": 42, "artifact_id": 84, "artifact_digest": f"sha256:{'b' * 64}"},
    )()

    class CycleModule:
        CycleBasePaths = staticmethod(lambda *arguments: arguments)
        CycleBaseContext = staticmethod(lambda *arguments: arguments)

        @staticmethod
        def validated_cycle_base(*_arguments: object, **keywords: object) -> object:
            observed.update(keywords)
            return trusted

    module.__dict__["_cycle_module"] = lambda: CycleModule
    context = module.CycleAuthorityContext(
        tmp_path,
        "c" * 40,
        "d" * 40,
        "e" * 40,
        "nold-ai/specfact-cli",
        698,
        "codex/692-computed-owner-red-proof-v2",
    )
    external_digest = f"sha256:{'f' * 64}"
    external_receipt = {"authority_digest": external_digest}

    assert (
        module._validated_live_cycle(
            context,
            tmp_path,
            module._LiveCyclePayload("{}", "{}"),
            external_authority_digest=external_digest,
            external_authority_receipt=external_receipt,
        )
        is trusted
    )
    assert observed["external_authority_digest"] == external_digest
    assert observed["external_authority_receipt"] == external_receipt


def test_ordinary_cycle_revalidates_the_live_external_capability(tmp_path: Path) -> None:
    """A public digest in an ordinary hint is not authority without a fresh external receipt."""
    module = _load_provenance_module()
    external_digest = f"sha256:{'a' * 64}"
    observed: list[str] = []
    context = module.CycleAuthorityContext(
        tmp_path,
        "b" * 40,
        "c" * 40,
        "d" * 40,
        "nold-ai/specfact-cli",
        698,
        "codex/692-computed-owner-red-proof-v2",
    )
    authority_path = tmp_path / "authority.json"
    authority_path.write_text("{}", encoding="utf-8")
    receipt = tmp_path / "external-receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "kind": module.EXTERNAL_AMENDMENT_KIND,
                "comment_id": module.EXTERNAL_AMENDMENT_COMMENT_ID,
                "repository": context.repository,
                "pull_request": context.pull_request,
                "head_branch": context.head_branch,
                "authority_digest": external_digest,
            }
        ),
        encoding="utf-8",
    )
    module.__dict__["_fetch_external_amendment"] = lambda *_arguments: (
        observed.append("fetched") or SimpleNamespace(receipt=receipt)
    )
    module.__dict__["_external_validator_command"] = lambda *_arguments: ["/usr/bin/true"]
    revalidated_digest, revalidated_receipt = module._revalidated_external_authority(
        context,
        tmp_path / "external-capability",
        external_digest,
    )
    assert revalidated_digest == external_digest
    assert revalidated_receipt["comment_id"] == module.EXTERNAL_AMENDMENT_COMMENT_ID
    assert observed == ["fetched"]
    observed.clear()
    hint = {
        "kind": "verified-pr-run",
        "prior_green_run_id": 42,
        "cycle_base": "e" * 40,
        "prior_green_artifact_id": 84,
        "prior_green_artifact_digest": f"sha256:{'f' * 64}",
        "external_authority_digest": external_digest,
    }
    trusted = type(
        "Trusted",
        (),
        {
            "cycle_base": hint["cycle_base"],
            "run_id": 42,
            "artifact_id": 84,
            "artifact_digest": hint["prior_green_artifact_digest"],
        },
    )()
    module.__dict__["_authority_hint"] = lambda *_arguments: hint
    module.__dict__["_revalidated_external_authority"] = lambda *_arguments: (
        observed.append(external_digest) or (external_digest, json.loads(receipt.read_text(encoding="utf-8")))
    )
    module.__dict__["_fetch_cycle_evidence"] = lambda *_arguments: ("{}", "{}", tmp_path)
    module.__dict__["_validated_live_cycle"] = lambda *_arguments, **_keywords: trusted
    module.__dict__["_cycle_payload_digest"] = lambda *_arguments: f"sha256:{'1' * 64}"

    assert module._read_cycle_authority(authority_path, context) is not None
    assert observed == [external_digest]


def test_nested_compound_review_avoids_exponential_rescanning() -> None:
    """Nested compound review remains bounded well below its former exponential cost."""
    module = _load_provenance_module()
    original = module._compound_binding_regions
    calls = 0

    def counted(node: ast.AST, aliases: object) -> object:
        nonlocal calls
        calls += 1
        return original(node, aliases)

    module.__dict__["_compound_binding_regions"] = counted
    nested = 'globals()["ordinary"] = 1\n'
    for index in range(20):
        nested = f"for item_{index} in [{{}}]:\n" + "\n".join(f"    {line}" for line in nested.splitlines()) + "\n"

    assert module._pytest_plugin_names(ast.parse(nested)) == []
    assert calls < 500
