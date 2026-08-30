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


def _assert_plugin_discovery_rejected(module: ModuleType, sources: tuple[str, ...]) -> None:
    accepted_sources: list[str] = []
    for source in sources:
        try:
            module._pytest_plugin_names(ast.parse(source))
        except ValueError as error:
            assert str(error) == "prior-red-proof-invalid"
        else:
            accepted_sources.append(source)
    assert not accepted_sources, "hostile plugin discovery sources were accepted:\n" + "\n---\n".join(accepted_sources)


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


def test_custom_current_module_type_fails_closed() -> None:
    """A custom current-module type can synthesize pytest_plugins on attribute read."""
    module = _load_provenance_module()
    custom_getattribute_type = (
        "import sys\n"
        "import types\n"
        "class Plugins(types.ModuleType):\n"
        "    def __getattribute__(self, name):\n"
        '        if name == "pytest_plugins":\n'
        '            return ("tests.helpers.hidden",)\n'
        "        return super().__getattribute__(name)\n"
    )
    hostile_operations = (
        "sys.modules[__name__].__class__ = Plugins\n",
        "module = sys.modules[__name__]\nmodule.__class__ = Plugins\n",
        'setattr(sys.modules[__name__], "__class__", Plugins)\n',
        'object.__setattr__(sys.modules[__name__], "__class__", Plugins)\n',
        'getattr(object, "__setattr__")(sys.modules[__name__], "__class__", Plugins)\n',
        'sys.modules[__name__].__setattr__("__class__", Plugins)\n',
        "setattr(sys.modules[__name__], attribute_name, Plugins)\n",
    )
    alternate_custom_types = (
        "import sys\nimport types\nclass Plugins(types.ModuleType):\n"
        '    pytest_plugins = ("tests.helpers.hidden",)\n'
        "sys.modules[__name__].__class__ = Plugins\n",
        "import sys\nimport types\nclass Plugins(types.ModuleType):\n"
        "    def __getattr__(self, name):\n"
        '        return ("tests.helpers.hidden",) if name == "pytest_plugins" else None\n'
        "sys.modules[__name__].__class__ = Plugins\n",
    )
    ordinary_source = "class Payload:\n    pass\ntarget.__class__ = Payload\n"

    hostile_sources = tuple(custom_getattribute_type + operation for operation in hostile_operations)
    _assert_plugin_discovery_rejected(module, hostile_sources + alternate_custom_types)
    assert module._pytest_plugin_names(ast.parse(ordinary_source)) == []


def test_current_module_registry_replacement_fails_closed() -> None:
    """Replacing a sys.modules entry can substitute hidden plugin declarations."""
    module = _load_provenance_module()
    replacement = 'import sys\nclass Replacement:\n    pytest_plugins = ("tests.helpers.hidden",)\n'
    hostile_operations = (
        "sys.modules[__name__] = Replacement()\n",
        "modules = sys.modules\nmodules[__name__] = Replacement()\n",
        "sys.modules.__setitem__(__name__, Replacement())\n",
        "sys.modules.update({__name__: Replacement()})\n",
    )
    read_only = "import sys\nmodule = sys.modules[__name__]\nvalue = sys.modules.get('unrelated')\n"

    _assert_plugin_discovery_rejected(module, tuple(replacement + operation for operation in hostile_operations))
    assert module._pytest_plugin_names(ast.parse(read_only)) == []


def test_builtins_getattr_mutation_fails_closed() -> None:
    """Mutating builtin getattr can synthesize a hidden plugin declaration for pytest."""
    module = _load_provenance_module()
    hostile_sources = (
        'import builtins\nbuiltins.getattr = lambda owner, name, default=None: ("tests.helpers.hidden",)\n',
        'import builtins\nsetattr(builtins, "getattr", replacement)\n',
        'import builtins\nbuiltins.__dict__["getattr"] = replacement\n',
        'import builtins\nvars(builtins).update({"getattr": replacement})\n',
    )
    unrelated = "import builtins\nbuiltins.ordinary = object()\n"

    _assert_plugin_discovery_rejected(module, hostile_sources)
    assert module._pytest_plugin_names(ast.parse(unrelated)) == []


def test_pytest_configure_import_plugin_is_retained_or_rejected() -> None:
    """Plugins loaded by pytest_configure must remain frozen proof inputs."""
    module = _load_provenance_module()
    literal_source = 'def pytest_configure(config):\n    config.pluginmanager.import_plugin("tests.helpers.hidden")\n'
    dynamic_source = "def pytest_configure(config):\n    config.pluginmanager.import_plugin(plugin_name)\n"

    assert ["tests", "helpers", "hidden"] in module._import_module_names(ast.parse(literal_source), "tests/conftest.py")
    try:
        module._import_module_names(ast.parse(dynamic_source), "tests/conftest.py")
    except ValueError as error:
        assert str(error) == "prior-red-proof-invalid"
    else:
        raise AssertionError("dynamic pytest pluginmanager import was accepted")


def test_higher_order_plugin_namespace_mutator_fails_closed() -> None:
    """Eager higher-order wrappers must not hide active-module plugin writes."""
    module = _load_provenance_module()
    hostile_sources = (
        "import functools\nimport sys\n"
        'functools.partial(setattr, sys.modules[__name__], "pytest_plugins", '
        '("tests.helpers.hidden",))()\n',
        "from functools import partial\nimport sys\n"
        'assign = partial(object.__setattr__, sys.modules[__name__], "pytest_plugins", '
        '("tests.helpers.hidden",))\nassign()\n',
        "import functools\nimport operator\nimport sys\n"
        'functools.partial(operator.setitem, vars(sys.modules[__name__]), "pytest_plugins", '
        '("tests.helpers.hidden",))()\n',
        "import operator\n"
        'operator.methodcaller("__setitem__", "pytest_plugins", ("tests.helpers.hidden",))(globals())\n',
        'import operator\noperator.attrgetter("__setitem__")(globals())("pytest_plugins", ("tests.helpers.hidden",))\n',
        "def bind(function):\n"
        "    global pytest_plugins\n"
        '    pytest_plugins = ("tests.helpers.hidden",)\n'
        "    return function\n"
        "@bind\n"
        "def target():\n"
        "    pass\n",
        "from tests.helpers.binder import bind\nbind(globals())\n",
    )
    ordinary_source = 'import functools\nfunctools.partial(setattr, target, "ordinary", 1)()\n'

    _assert_plugin_discovery_rejected(module, hostile_sources)
    assert module._pytest_plugin_names(ast.parse(ordinary_source)) == []


def test_higher_order_import_factory_is_retained_or_rejected() -> None:
    """Eager higher-order import wrappers must remain frozen proof inputs."""
    module = _load_provenance_module()
    literal_sources = (
        'import functools\nfunctools.partial(__import__, "tests.helpers.hidden")()\n',
        'from functools import partial\nload = partial(__import__, "tests.helpers.hidden")\nload()\n',
        'import functools\nimport importlib\nfunctools.partial(importlib.import_module, "tests.helpers.hidden")()\n',
        "import importlib\nimport operator\n"
        'operator.methodcaller("import_module", "tests.helpers.hidden")(importlib)\n',
        'import importlib\nimport operator\noperator.attrgetter("import_module")(importlib)("tests.helpers.hidden")\n',
        "import importlib\nimport operator\n"
        'operator.itemgetter("import_module")(vars(importlib))("tests.helpers.hidden")\n',
        'import importlib\nlist(map(importlib.import_module, ["tests.helpers.hidden"]))\n',
        "import importlib\nimport itertools\n"
        'list(itertools.starmap(importlib.import_module, [("tests.helpers.hidden",)]))\n',
    )
    dynamic_sources = (
        "import functools\nfunctools.partial(__import__, module_name)()\n",
        "import importlib\nlist(map(importlib.import_module, module_names))\n",
    )

    for source in literal_sources:
        imported = module._import_module_names(ast.parse(source), "tests/conftest.py")
        assert ["tests", "helpers", "hidden"] in imported, source
    for source in dynamic_sources:
        try:
            module._import_module_names(ast.parse(source), "tests/conftest.py")
        except ValueError as error:
            assert str(error) == "prior-red-proof-invalid"
        else:
            raise AssertionError(f"dynamic higher-order import wrapper was accepted: {source}")


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
