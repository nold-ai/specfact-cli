#!/usr/bin/env python3
"""Check the Git-tracked Python sources against the independent SAST baseline."""

from __future__ import annotations

import argparse
import ast
import json
import os
import stat
import subprocess
import sys
import tokenize
from collections.abc import Iterator, Mapping
from pathlib import Path, PurePosixPath
from typing import NamedTuple, cast


CALL_RULES = {
    "os.system": "command-injection-risk",
    "hashlib.md5": "weak-cryptographic-hash",
    "pickle.load": "unsafe-pickle-deserialization",
    "pickle.loads": "unsafe-pickle-deserialization",
    "random.random": "insecure-random",
    "random.randint": "insecure-random",
}
SHELL_CALLS = {"subprocess.call", "subprocess.Popen", "subprocess.run"}
RULES = {*CALL_RULES.values(), "hardcoded-secret", "unsafe-eval-usage"}


class Finding(NamedTuple):
    rule_id: str
    path: str
    line: int


class _UnsupportedOuterImportError(ValueError):
    """An import changes a module binding outside its lexical body."""


def _valid_path(path: str) -> bool:
    relative = PurePosixPath(path)
    return not relative.is_absolute() and ".." not in relative.parts and path.endswith(".py") and "\0" not in path


def _tracked_paths(root: Path) -> list[str]:
    command = ["git", "-C", str(root)]
    top = subprocess.run([*command, "rev-parse", "--show-toplevel"], check=True, capture_output=True)
    if Path(os.fsdecode(top.stdout).removesuffix("\n")).resolve() != root:
        raise ValueError("scan root must be the Git worktree root")
    result = subprocess.run([*command, "ls-files", "--cached", "-z", "--", "*.py"], check=True, capture_output=True)
    return sorted({os.fsdecode(path) for path in result.stdout.split(b"\0") if path})


def _load_baseline(path: Path) -> set[Finding]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("baseline must be a version 1 object")
    baseline_object = cast(Mapping[str, object], payload)
    version = baseline_object.get("version")
    if type(version) is not int or version != 1:
        raise ValueError("baseline must be a version 1 object")
    raw_findings = baseline_object.get("accepted_findings")
    if not isinstance(raw_findings, list):
        raise ValueError("baseline must contain an accepted_findings list")

    return {_baseline_entry(raw, index) for index, raw in enumerate(raw_findings)}


def _baseline_entry(raw: object, index: int) -> Finding:
    if not isinstance(raw, list) or len(raw) != 3:
        raise ValueError(f"invalid accepted finding at index {index}")
    raw_rule, path, line = cast(list[object], raw)
    if not isinstance(raw_rule, str) or not isinstance(path, str) or not _valid_path(path):
        raise ValueError(f"invalid accepted finding at index {index}")
    if type(line) is not int or line < 1:
        raise ValueError(f"invalid accepted finding at index {index}")
    rule = raw_rule.removeprefix("tools.semgrep.sast.")
    if rule not in RULES:
        raise ValueError(f"unknown baseline rule at index {index}")
    return Finding(rule, path, line)


def _import_bindings(node: ast.AST) -> dict[str, str]:
    if isinstance(node, ast.Import):
        return {
            item.asname or item.name.partition(".")[0]: item.name if item.asname else item.name.partition(".")[0]
            for item in node.names
        }
    if isinstance(node, ast.ImportFrom):
        module = "." * node.level + (node.module or "")
        return {item.asname or item.name: f"{module}.{item.name}" for item in node.names if item.name != "*"}
    return {}


def _scope_imports(nodes: list[ast.AST]) -> dict[str, set[str]]:
    aliases: dict[str, set[str]] = {}
    for node in nodes:
        for name, target in _import_bindings(node).items():
            aliases.setdefault(name, set()).add(target)
    return aliases


def _call_names(func: ast.expr, aliases: dict[str, set[str]]) -> Iterator[str]:
    if isinstance(func, ast.Name):
        yield from aliases.get(func.id, {func.id})
    elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        for module in aliases.get(func.value.id, {func.value.id}):
            yield f"{module}.{func.attr}"


def _literal_keyword(node: ast.Call, name: str, value: bool) -> bool:
    return any(
        keyword.arg == name and isinstance(keyword.value, ast.Constant) and keyword.value.value is value
        for keyword in node.keywords
    )


def _call_rule(node: ast.Call, name: str) -> str | None:
    builtin = name.removeprefix("builtins.")
    if builtin == "compile" or (builtin in {"eval", "exec"} and len(node.args) == 1 and not node.keywords):
        return "unsafe-eval-usage"
    if name in SHELL_CALLS and _literal_keyword(node, "shell", True):
        return "command-injection-risk"
    if name == "hashlib.sha1" and not _literal_keyword(node, "usedforsecurity", False):
        return "weak-cryptographic-hash"
    return CALL_RULES.get(name)


def _has_secret(node: ast.Assign | ast.AnnAssign) -> bool:
    if not isinstance(node.value, ast.Constant) or not isinstance(node.value.value, str):
        return False
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    return node.value.value.startswith(("api_key:", "password:", "secret:")) or any(
        isinstance(target, ast.Name) and target.id in {"API_KEY", "PASSWORD"} for target in targets
    )


def _scope_nodes(body: list[ast.stmt]) -> Iterator[ast.AST]:
    """Visit definition headers in the current scope and leave their bodies to the child scan."""
    pending: list[ast.AST] = list(reversed(body))
    while pending:
        node = pending.pop()
        yield node
        children = list(ast.iter_child_nodes(node))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            child_body = set(node.body)
            children = [child for child in children if child not in child_body]
        pending.extend(reversed(children))


def _reject_outer_imports(nodes: list[ast.AST], local_aliases: dict[str, set[str]]) -> None:
    for node in nodes:
        if isinstance(node, (ast.Global, ast.Nonlocal)) and local_aliases.keys() & set(node.names):
            scope = "global" if isinstance(node, ast.Global) else "nonlocal"
            raise _UnsupportedOuterImportError(f"{scope} import alias requires flow analysis")


def _retain_loop_imports(node: ast.For | ast.AsyncFor | ast.While, aliases: dict[str, set[str]]) -> None:
    # A later iteration can start with bindings from any preceding iteration.
    for name, targets in _scope_imports(list(_scope_nodes(node.body))).items():
        aliases[name] = aliases.get(name, {name}) | targets


def _scope_findings(
    body: list[ast.stmt], inherited: dict[str, set[str]], path: str, *, class_body: bool = False
) -> Iterator[Finding]:
    nodes = list(_scope_nodes(body))
    local_aliases = _scope_imports(nodes)
    _reject_outer_imports(nodes, local_aliases)
    aliases = inherited.copy()
    # Class namespaces do not close over method bodies. Other nested functions
    # can run before or after an enclosing import rebinds a name.
    nested_inherited = inherited if class_body else inherited | local_aliases
    direct_statements = set(body)
    for node in nodes:
        if isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            _retain_loop_imports(node, aliases)
        for name, target in _import_bindings(node).items():
            # A compound statement can skip an import. Keep both possible bindings.
            aliases[name] = {target} if node in direct_statements else aliases.get(name, {name}) | {target}
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield from _scope_findings(node.body, nested_inherited, path, class_body=isinstance(node, ast.ClassDef))
            continue
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and _has_secret(node):
            yield Finding("hardcoded-secret", path, node.lineno)
            continue
        if not isinstance(node, ast.Call):
            continue
        for name in _call_names(node.func, aliases):
            if rule := _call_rule(node, name):
                yield Finding(rule, path, node.lineno)


def _read_source(root: Path, path: str) -> ast.Module:
    source = root / path
    if not _valid_path(path) or source.resolve(strict=True) != source or not stat.S_ISREG(source.lstat().st_mode):
        raise OSError("expected a regular file inside the Git worktree")
    with tokenize.open(source) as stream:
        return ast.parse(stream.read(), filename=path)


def _scan_scope(root: Path, diagnostics: list[dict[str, str]]) -> tuple[list[str], list[str]]:
    try:
        paths = _tracked_paths(root)
    except (OSError, subprocess.CalledProcessError, ValueError):
        diagnostics.append({"path": str(root), "message": "could not enumerate tracked Python inputs"})
        return [], []
    eligible_paths: list[str] = []
    excluded_test_paths: list[str] = []
    for path in paths:
        bucket = excluded_test_paths if "tests" in PurePosixPath(path).parts[:-1] else eligible_paths
        bucket.append(path)
    if not eligible_paths:
        diagnostics.append({"path": str(root), "message": "no eligible tracked Python inputs"})
    return eligible_paths, excluded_test_paths


def _run(root: Path, baseline_path: Path, output: Path) -> int:
    diagnostics: list[dict[str, str]] = []
    scanned_paths: list[str] = []
    findings: set[Finding] = set()
    baseline: set[Finding] = set()
    try:
        baseline = _load_baseline(baseline_path)
    except (OSError, ValueError):
        diagnostics.append({"path": str(baseline_path), "message": "invalid or unavailable SAST baseline"})
    eligible_paths, excluded_test_paths = _scan_scope(root, diagnostics)

    for path in eligible_paths:
        try:
            tree = _read_source(root, path)
            file_findings = set(_scope_findings(tree.body, {}, path))
        except (OSError, RuntimeError):
            diagnostics.append({"path": path, "message": "unavailable input"})
        except _UnsupportedOuterImportError as error:
            diagnostics.append({"path": path, "message": str(error)})
        except (LookupError, SyntaxError, ValueError):
            diagnostics.append({"path": path, "message": "invalid Python"})
        else:
            scanned_paths.append(path)
            findings.update(file_findings)

    new_findings = findings - baseline
    status = "incomplete" if diagnostics else "findings" if new_findings else "pass"
    report = {
        "engine": "python-ast",
        "policy": "core-python-sast-v1",
        "status": status,
        "eligible_paths": eligible_paths,
        "scanned_paths": scanned_paths,
        "excluded_test_paths": excluded_test_paths,
        "diagnostics": diagnostics,
        "findings": [finding._asdict() for finding in sorted(findings)],
        "new_findings": [finding._asdict() for finding in sorted(new_findings)],
    }
    try:
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except OSError:
        sys.stderr.write(f"Could not write the SAST report at {output}\n")
        return 2
    sys.stdout.write(
        f"Python SAST: {status}, {len(scanned_paths)}/{len(eligible_paths)} scanned, {len(new_findings)} new findings\n"
    )
    return {"pass": 0, "findings": 1, "incomplete": 2}[status]


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="Git worktree root")
    parser.add_argument("--baseline", required=True, type=Path, help="Reviewed SAST findings baseline")
    parser.add_argument("--output", type=Path, default=Path("python-sast.json"), help="Path for the JSON report")
    args = parser.parse_args()
    return _run(args.root.resolve(), args.baseline, args.output)


if __name__ == "__main__":
    sys.exit(_main())
