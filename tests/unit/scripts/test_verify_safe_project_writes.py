"""Tests for scripts/verify_safe_project_writes.py."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path


def _load_verify_module() -> object:
    root = Path(__file__).resolve().parents[3]
    path = root / "scripts" / "verify_safe_project_writes.py"
    spec = importlib.util.spec_from_file_location("_verify_safe_project_writes", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_collect_json_io_flags_from_json_import_loads() -> None:
    mod = _load_verify_module()
    tree = ast.parse('from json import loads\nloads("{}")')
    offenders = mod._collect_json_io_offenders(tree)
    assert offenders
    assert any(name == "json.loads" for _, name in offenders)


def test_collect_json_io_flags_aliased_json_import() -> None:
    mod = _load_verify_module()
    tree = ast.parse('from json import dump as dumper\nx = None\ndumper(x, open("f","w"))')
    offenders = mod._collect_json_io_offenders(tree)
    assert any(name == "json.dump" for _, name in offenders)


def test_collect_json_io_flags_import_json_as_module_alias() -> None:
    mod = _load_verify_module()
    tree = ast.parse('import json as js\nx = None\njs.dump(x, open("f","w"))')
    offenders = mod._collect_json_io_offenders(tree)
    assert any(name == "json.dump" for _, name in offenders)


def test_collect_json_io_flags_from_json_star_import() -> None:
    mod = _load_verify_module()
    tree = ast.parse('from json import *\nx = None\ndump(x, open("f","w"))')
    offenders = mod._collect_json_io_offenders(tree)
    assert any(name == "json.dump" for _, name in offenders)


def test_collect_json_io_ignores_shadowed_json_dump_alias() -> None:
    mod = _load_verify_module()
    tree = ast.parse('from json import dump as dumper\ndumper = 1\ndef f():\n    dumper(1, open("f","w"))\n')
    offenders = mod._collect_json_io_offenders(tree)
    assert not any(name == "json.dump" for _, name in offenders)


def test_collect_json_io_ignores_shadow_from_enclosing_function() -> None:
    mod = _load_verify_module()
    source = "import json\ndef outer():\n    json = {}\n    def inner():\n        json.dump(1, None)\n"
    offenders = mod._collect_json_io_offenders(ast.parse(source))
    assert not offenders


def test_collect_json_io_flags_method_call_under_class_attribute() -> None:
    mod = _load_verify_module()
    source = "import json\nclass C:\n    json = None\n    def m(self, path):\n        json.dump({}, path)\n"
    offenders = mod._collect_json_io_offenders(ast.parse(source))
    assert any(name == "json.dump" for _, name in offenders)


def test_collect_json_io_ignores_class_body_call_on_class_attribute() -> None:
    mod = _load_verify_module()
    source = "import json\nclass C:\n    json = None\n    value = json.dump({}, None)\n"
    offenders = mod._collect_json_io_offenders(ast.parse(source))
    assert not offenders


def test_collect_json_io_flags_call_after_except_alias_unbinds() -> None:
    mod = _load_verify_module()
    source = "import json\ntry:\n    pass\nexcept OSError as json:\n    pass\njson.dump({}, None)\n"
    offenders = mod._collect_json_io_offenders(ast.parse(source))
    assert any(name == "json.dump" for _, name in offenders)


def test_collect_json_io_ignores_call_inside_except_alias_body() -> None:
    mod = _load_verify_module()
    source = "import json\ntry:\n    pass\nexcept OSError as json:\n    json.dump({}, None)\n"
    offenders = mod._collect_json_io_offenders(ast.parse(source))
    assert not offenders


def test_collect_json_io_flags_call_in_function_default() -> None:
    mod = _load_verify_module()
    offenders = mod._collect_json_io_offenders(ast.parse("import json\ndef f(x=json.dumps({})):\n    return x\n"))
    assert any(name == "json.dumps" for _, name in offenders)


def test_collect_json_io_flags_call_in_keyword_only_default() -> None:
    mod = _load_verify_module()
    source = "import json\ndef f(*, x=json.dumps({})):\n    return x\n"
    offenders = mod._collect_json_io_offenders(ast.parse(source))
    assert any(name == "json.dumps" for _, name in offenders)


def test_collect_json_io_flags_call_in_decorator() -> None:
    mod = _load_verify_module()
    offenders = mod._collect_json_io_offenders(ast.parse("import json\n@json.loads\ndef f():\n    return None\n"))
    assert any(name == "json.loads" for _, name in offenders)


def test_collect_json_io_flags_call_in_decorator_factory() -> None:
    mod = _load_verify_module()
    source = 'import json\n@json.loads("{}")\ndef f():\n    return None\n'
    offenders = mod._collect_json_io_offenders(ast.parse(source))
    assert any(name == "json.loads" for _, name in offenders)


def test_collect_json_io_ignores_shadowed_bare_decorator() -> None:
    mod = _load_verify_module()
    source = "import json\njson = None\n@json.loads\ndef f():\n    return None\n"
    offenders = mod._collect_json_io_offenders(ast.parse(source))
    assert not offenders


def test_collect_json_io_flags_call_in_class_base() -> None:
    mod = _load_verify_module()
    offenders = mod._collect_json_io_offenders(ast.parse('import json\nclass C(json.loads("{}")):\n    pass\n'))
    assert any(name == "json.loads" for _, name in offenders)


def test_collect_json_io_flags_call_in_method_default() -> None:
    mod = _load_verify_module()
    source = "import json\nclass C:\n    def m(self, x=json.dumps({})):\n        return x\n"
    offenders = mod._collect_json_io_offenders(ast.parse(source))
    assert any(name == "json.dumps" for _, name in offenders)


def test_collect_json_io_ignores_method_default_under_class_attribute() -> None:
    mod = _load_verify_module()
    source = "import json\nclass C:\n    json = None\n    def m(self, x=json.dumps({})):\n        return x\n"
    offenders = mod._collect_json_io_offenders(ast.parse(source))
    assert not offenders


def test_collect_json_io_flags_evaluated_annotation_call() -> None:
    mod = _load_verify_module()
    offenders = mod._collect_json_io_offenders(ast.parse('import json\ndef f(x: json.loads("{}")):\n    return x\n'))
    assert any(name == "json.loads" for _, name in offenders)


def test_collect_json_io_ignores_deferred_annotation_call() -> None:
    mod = _load_verify_module()
    source = 'from __future__ import annotations\nimport json\ndef f(x: json.loads("{}")):\n    return x\n'
    offenders = mod._collect_json_io_offenders(ast.parse(source))
    assert not offenders


def test_collect_json_io_ignores_lambda_parameter_shadow() -> None:
    mod = _load_verify_module()
    offenders = mod._collect_json_io_offenders(ast.parse("import json\nf = lambda json: json.dump({}, None)\n"))
    assert not offenders


def test_collect_json_io_flags_call_in_lambda_default() -> None:
    mod = _load_verify_module()
    offenders = mod._collect_json_io_offenders(ast.parse("import json\nf = lambda x=json.dumps({}): x\n"))
    assert any(name == "json.dumps" for _, name in offenders)
