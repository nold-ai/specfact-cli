"""Post-red review regressions for retained Requirements proof provenance."""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[3]
PROVENANCE_SCRIPT = REPO_ROOT / "scripts" / "requirements_proof_provenance.py"


def _load_provenance_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("requirements_proof_provenance_review_v2", PROVENANCE_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_object_setattr_current_module_binding_fails_closed() -> None:
    """Object-level attribute setters can install the active pytest plugin binding."""
    module = _load_provenance_module()
    sources = (
        'object.__setattr__(module, "pytest_plugins", ("tests.helpers.hidden",))\n',
        'getattr(object, "__setattr__")(module, "pytest_plugins", ("tests.helpers.hidden",))\n',
        'module.__setattr__("pytest_plugins", ("tests.helpers.hidden",))\n',
        'object.__setattr__(module, attribute_name, ("tests.helpers.hidden",))\n',
    )
    for operation in sources:
        source = "import sys\nmodule = sys.modules[__name__]\n" + operation
        try:
            module._pytest_plugin_names(ast.parse(source))
        except ValueError as error:
            assert str(error) == "prior-red-proof-invalid"
        else:
            raise AssertionError(f"current-module binding was accepted: {operation}")


def test_object_setattr_unrelated_object_remains_allowed() -> None:
    """The fail-closed rule must not reject an ordinary object mutation."""
    module = _load_provenance_module()
    source = (
        "import sys\n"
        "module = sys.modules[__name__]\n"
        'object.__setattr__(target, "pytest_plugins", ())\n'
        'object.__setattr__(module, "ordinary", 1)\n'
    )

    assert module._pytest_plugin_names(ast.parse(source)) == []


def test_builtins_dynamic_import_forms_are_retained_or_rejected() -> None:
    """Builtins-qualified import factories must not hide repository proof inputs."""
    module = _load_provenance_module()
    retained_sources = (
        'import builtins\nbuiltins.__import__("tests.helpers.hidden")\n',
        'import builtins\ngetattr(builtins, "__import__")("tests.helpers.hidden")\n',
        'import builtins\nload = builtins.__import__\nload("tests.helpers.hidden")\n',
        '__import__.__call__("tests.helpers.hidden")\n',
        'getattr(__import__, "__call__")("tests.helpers.hidden")\n',
        'import builtins\nbuiltins.__dict__["__import__"]("tests.helpers.hidden")\n',
        'import builtins\nvars(builtins).get("__import__")("tests.helpers.hidden")\n',
        'import builtins\nnamespace = vars(builtins)\nnamespace["__import__"]("tests.helpers.hidden")\n',
        "import builtins\nnamespace = builtins.__dict__\nlookup = namespace.get\n"
        'lookup("__import__")("tests.helpers.hidden")\n',
        "import builtins\nnamespace = vars(builtins)\n"
        'getattr(namespace, "__getitem__")("__import__")("tests.helpers.hidden")\n',
    )
    for source in retained_sources:
        imported = module._import_module_names(ast.parse(source), "tests/test_proof.py")
        assert ["tests", "helpers", "hidden"] in imported, source

    ambiguous_sources = (
        "import builtins\nbuiltins.__import__(module_name)\n",
        'import builtins\ngetattr(builtins, loader_name)("tests.helpers.hidden")\n',
        'import builtins\nvars(builtins)[loader_name]("tests.helpers.hidden")\n',
        'import builtins\nnamespace = vars(builtins)\nnamespace[loader_name]("tests.helpers.hidden")\n',
    )
    for source in ambiguous_sources:
        try:
            module._import_module_names(ast.parse(source), "tests/test_proof.py")
        except ValueError as error:
            assert str(error) == "prior-red-proof-invalid"
        else:
            raise AssertionError(f"ambiguous builtins import was accepted: {source}")
