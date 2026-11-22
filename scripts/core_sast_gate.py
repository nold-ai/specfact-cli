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
from collections.abc import Mapping
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
SUPPORTED_MODULES = {"builtins", "hashlib", "os", "pickle", "random", "subprocess"}
RULES = {*CALL_RULES.values(), "hardcoded-secret", "unsafe-eval-usage"}


class Finding(NamedTuple):
    rule_id: str
    path: str
    line: int


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

    baseline: set[Finding] = set()
    for index, raw in enumerate(raw_findings):
        if (
            not isinstance(raw, list)
            or len(raw) != 3
            or not isinstance(raw[0], str)
            or not isinstance(raw[1], str)
            or not _valid_path(raw[1])
            or type(raw[2]) is not int
            or raw[2] < 1
        ):
            raise ValueError(f"invalid accepted finding at index {index}")
        rule = raw[0].removeprefix("tools.semgrep.sast.")
        if rule not in RULES:
            raise ValueError(f"unknown baseline rule at index {index}")
        baseline.add(Finding(rule, raw[1], raw[2]))
    return baseline


def _import_aliases(nodes: list[ast.AST]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in nodes:
        if isinstance(node, ast.Import):
            aliases.update(
                {item.asname or item.name: item.name for item in node.names if item.name in SUPPORTED_MODULES}
            )
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module in SUPPORTED_MODULES:
            aliases.update(
                {item.asname or item.name: f"{node.module}.{item.name}" for item in node.names if item.name != "*"}
            )
    return aliases


def _call_name(func: ast.expr, aliases: dict[str, str]) -> str:
    if isinstance(func, ast.Name):
        return aliases.get(func.id, func.id)
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        return f"{aliases.get(func.value.id, func.value.id)}.{func.attr}"
    return ""


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


def _findings(tree: ast.AST, path: str) -> set[Finding]:
    nodes = list(ast.walk(tree))
    aliases = _import_aliases(nodes)
    findings: set[Finding] = set()
    for node in nodes:
        if isinstance(node, ast.Call):
            rule = _call_rule(node, _call_name(node.func, aliases))
            if rule:
                findings.add(Finding(rule, path, node.lineno))
        elif isinstance(node, (ast.Assign, ast.AnnAssign)) and _has_secret(node):
            findings.add(Finding("hardcoded-secret", path, node.lineno))
    return findings


def _read_source(root: Path, path: str) -> ast.AST:
    source = root / path
    if not _valid_path(path) or source.resolve(strict=True) != source or not stat.S_ISREG(source.lstat().st_mode):
        raise OSError("expected a regular file inside the Git worktree")
    with tokenize.open(source) as stream:
        return ast.parse(stream.read(), filename=path)


def _run(root: Path, baseline_path: Path, output: Path) -> int:
    diagnostics: list[dict[str, str]] = []
    eligible_paths: list[str] = []
    scanned_paths: list[str] = []
    excluded_test_paths: list[str] = []
    findings: set[Finding] = set()
    baseline: set[Finding] = set()
    try:
        baseline = _load_baseline(baseline_path)
    except (OSError, ValueError):
        diagnostics.append({"path": str(baseline_path), "message": "invalid or unavailable SAST baseline"})
    try:
        for path in _tracked_paths(root):
            if "tests" in PurePosixPath(path).parts[:-1]:
                excluded_test_paths.append(path)
            else:
                eligible_paths.append(path)
        if not eligible_paths:
            diagnostics.append({"path": str(root), "message": "no eligible tracked Python inputs"})
    except (OSError, subprocess.CalledProcessError, ValueError):
        diagnostics.append({"path": str(root), "message": "could not enumerate tracked Python inputs"})

    for path in eligible_paths:
        try:
            tree = _read_source(root, path)
        except (OSError, RuntimeError):
            diagnostics.append({"path": path, "message": "unavailable input"})
        except (SyntaxError, ValueError):
            diagnostics.append({"path": path, "message": "invalid Python"})
        else:
            scanned_paths.append(path)
            findings.update(_findings(tree, path))

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
        print(f"Could not write the SAST report at {output}", file=sys.stderr)
        return 2
    print(
        f"Python SAST: {status}, {len(scanned_paths)}/{len(eligible_paths)} scanned, {len(new_findings)} new findings"
    )
    return {"pass": 0, "findings": 1, "incomplete": 2}[status]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="Git worktree root")
    parser.add_argument("--baseline", required=True, type=Path, help="Reviewed SAST findings baseline")
    parser.add_argument("--output", required=True, type=Path, help="Path for the JSON report")
    args = parser.parse_args()
    return _run(args.root.resolve(), args.baseline, args.output)


if __name__ == "__main__":
    sys.exit(main())
