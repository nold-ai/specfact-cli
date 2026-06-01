#!/usr/bin/env python3
"""Validate generated command overview paths against the live CLI behavior."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, cast

import typer
from typer.testing import CliRunner


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMANDS_JSON = REPO_ROOT / "docs" / "reference" / "commands.generated.json"
HELP_FLAGS = ("--help", "-h")
APP_MOUNTS = (
    ("specfact_cli.modules.init.src.commands", "app", ("specfact", "init")),
    ("specfact_cli.modules.module_registry.src.commands", "app", ("specfact", "module")),
    ("specfact_cli.modules.upgrade.src.commands", "app", ("specfact", "upgrade")),
    ("specfact_backlog.backlog.commands", "app", ("specfact", "backlog")),
    ("specfact_codebase.code.commands", "app", ("specfact", "code")),
    ("specfact_code_review.review.commands", "app", ("specfact", "code", "review")),
    ("specfact_govern.govern.commands", "app", ("specfact", "govern")),
    ("specfact_project.project.commands", "app", ("specfact", "project")),
    ("specfact_spec.spec.commands", "app", ("specfact", "spec")),
)
MISSING_MARKERS = (
    "missing",
    "requires an argument",
    "no such option",
    "no such command",
    "not a valid command",
)
_TEMP_HOME: tempfile.TemporaryDirectory[str] | None = None
MountedApps = dict[tuple[str, ...], tuple[object, tuple[str, ...]]]


def _paired_worktree_repo(source_marker: str, target_marker: str) -> Path | None:
    parts = REPO_ROOT.parts
    if source_marker not in parts:
        return None
    marker_index = parts.index(source_marker)
    base = Path(*parts[:marker_index])
    suffix = Path(*parts[marker_index + 1 :])
    return base / target_marker / suffix


def _ensure_imports() -> None:
    os.environ.setdefault("TEST_MODE", "true")
    global _TEMP_HOME
    if os.environ.get("SPECFACT_COMMAND_CONTRACT_USE_REAL_HOME") != "1":
        _TEMP_HOME = tempfile.TemporaryDirectory(prefix="specfact-command-contract-home-")
        os.environ["HOME"] = _TEMP_HOME.name
    src = str(REPO_ROOT / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    modules_repo = os.environ.get("SPECFACT_MODULES_REPO", "").strip()
    candidates = [Path(modules_repo).expanduser()] if modules_repo else []
    candidates.append(REPO_ROOT.parent / "specfact-cli-modules")
    paired_modules_repo = _paired_worktree_repo("specfact-cli-worktrees", "specfact-cli-modules-worktrees")
    if paired_modules_repo is not None:
        candidates.append(paired_modules_repo)
    for candidate in candidates:
        if candidate is None:
            continue
        packages_dir = candidate / "packages"
        if not packages_dir.is_dir():
            continue
        os.environ.setdefault("SPECFACT_MODULES_REPO", str(candidate.resolve()))
        for src_path in sorted(packages_dir.glob("*/src")):
            package_src = str(src_path.resolve())
            if package_src not in sys.path:
                sys.path.insert(0, package_src)


def _load_records() -> list[dict[str, Any]]:
    raw = json.loads(COMMANDS_JSON.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"{COMMANDS_JSON} must contain a JSON list")
    return [entry for entry in raw if isinstance(entry, dict)]


def _command_args(record: dict[str, Any]) -> list[str]:
    command = record.get("command")
    if not isinstance(command, str):
        return []
    parts = command.split()
    if parts[:1] != ["specfact"]:
        return []
    return parts[1:]


def _has_required_argument(record: dict[str, Any]) -> bool:
    arguments = record.get("arguments")
    if not isinstance(arguments, list):
        return False
    return any(isinstance(argument, dict) and argument.get("required") for argument in arguments)


def _is_group(record: dict[str, Any]) -> bool:
    subcommands = record.get("subcommands")
    return isinstance(subcommands, list) and len(subcommands) > 0


def _load_apps() -> MountedApps:
    from specfact_cli.cli import app as root_app

    apps: MountedApps = {("specfact",): (root_app, ())}
    for module_path, attr_name, prefix in APP_MOUNTS:
        module = importlib.import_module(module_path)
        internal_prefix = ("review",) if prefix == ("specfact", "code", "review") else ()
        apps[prefix] = (getattr(module, attr_name), internal_prefix)
    return apps


def _select_app(apps: MountedApps, command_parts: list[str]) -> tuple[object, list[str]]:
    best_prefix: tuple[str, ...] = ("specfact",)
    for prefix in apps:
        if len(prefix) > len(best_prefix) and tuple(command_parts[: len(prefix)]) == prefix:
            best_prefix = prefix
    app, internal_prefix = apps[best_prefix]
    return app, [*internal_prefix, *command_parts[len(best_prefix) :]]


def _invoke(runner: CliRunner, apps: MountedApps, command_parts: list[str], suffix: list[str]) -> tuple[int, str]:
    app, args = _select_app(apps, command_parts)
    invoke_args = [*args, *suffix]
    result = runner.invoke(cast(typer.Typer, app), invoke_args)
    stdout = getattr(result, "stdout", "") or ""
    try:
        stderr = getattr(result, "stderr", "") or ""
    except ValueError:
        stderr = ""
    return result.exit_code, f"{stdout}{stderr}"


def _usage_lines(raw_output: str) -> list[str]:
    lines: list[str] = []
    capture_usage = False
    for line in raw_output.splitlines():
        if "Usage:" in line:
            capture_usage = True
        if capture_usage:
            if not line.strip():
                break
            lines.append(line.lower())
    return lines


def _allows_parent_help(record: dict[str, Any]) -> bool:
    return record.get("command") in {
        "specfact code import from-bridge",
        "specfact code import from-code",
    }


def _check_help(runner: CliRunner, apps: MountedApps, record: dict[str, Any]) -> list[str]:
    args = _command_args(record)
    if not args and record.get("command") != "specfact":
        return [f"{record.get('command')}: invalid command path in generated JSON"]
    command_parts = ["specfact", *args]
    exit_code, raw_output = _invoke(runner, apps, command_parts, ["--help"])
    if exit_code != 0 and _allows_parent_help(record):
        # Typer treats the alias token as the optional import BUNDLE argument
        # before it can resolve these legacy aliases as subcommands.
        exit_code, raw_output = _invoke(runner, apps, command_parts[:-1], ["--help"])
    output = raw_output.lower()
    if exit_code != 0:
        return [f"{record.get('command')}: --help exited {exit_code}\n{raw_output}"]
    if "usage:" not in output:
        return [f"{record.get('command')}: --help did not render usage\n{raw_output}"]
    _selected_app, selected_args = _select_app(apps, command_parts)
    if not _is_group(record) and selected_args and not _allows_parent_help(record):
        usage_lines = _usage_lines(raw_output)
        if args[-1].lower() not in " ".join(usage_lines):
            return [f"{record.get('command')}: --help rendered parent usage instead of leaf usage\n{raw_output}"]
    return []


def _check_group_missing_subcommand(runner: CliRunner, apps: MountedApps, record: dict[str, Any]) -> list[str]:
    if record.get("command") == "specfact" or not _is_group(record) or record.get("bare_invocation") == "executes":
        return []
    args = _command_args(record)
    command_parts = ["specfact", *args]
    exit_code, raw_output = _invoke(runner, apps, command_parts, [])
    output = raw_output.lower()
    failures: list[str] = []
    if exit_code == 0:
        failures.append(f"{record.get('command')}: bare group unexpectedly exited 0")
    if "usage:" not in output:
        failures.append(f"{record.get('command')}: bare group did not render usage")
    if "missing subcommand" not in output:
        failures.append(f"{record.get('command')}: bare group did not explain the missing subcommand")
    if output.count("usage:") != 1:
        failures.append(f"{record.get('command')}: expected exactly one usage block, saw {output.count('usage:')}")
    if failures:
        failures.append(raw_output)
    return failures


def _check_missing_required_argument(runner: CliRunner, apps: MountedApps, record: dict[str, Any]) -> list[str]:
    if _is_group(record) or not _has_required_argument(record):
        return []
    args = _command_args(record)
    command_parts = ["specfact", *args]
    exit_code, raw_output = _invoke(runner, apps, command_parts, [])
    output = raw_output.lower()
    failures: list[str] = []
    if exit_code == 0:
        failures.append(f"{record.get('command')}: missing required argument unexpectedly exited 0")
    if "usage:" not in output:
        failures.append(f"{record.get('command')}: missing required argument did not render usage")
    if not any(marker in output for marker in MISSING_MARKERS):
        failures.append(f"{record.get('command')}: missing required argument did not explain the failure")
    if output.count("usage:") != 1:
        failures.append(f"{record.get('command')}: expected exactly one usage block, saw {output.count('usage:')}")
    if failures:
        failures.append(raw_output)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0, help="Validate only the first N generated commands")
    args = parser.parse_args(argv)

    _ensure_imports()
    apps = _load_apps()
    records = _load_records()
    records = sorted(records, key=lambda record: len(str(record.get("command", "")).split()), reverse=True)
    if args.limit > 0:
        records = records[: args.limit]

    runner = CliRunner()
    failures: list[str] = []
    for record in records:
        failures.extend(_check_help(runner, apps, record))
        failures.extend(_check_group_missing_subcommand(runner, apps, record))
        failures.extend(_check_missing_required_argument(runner, apps, record))

    if failures:
        print("Generated command contract validation failed:")
        print("\n\n".join(failures))
        return 1
    print(f"check-command-contract: OK ({len(records)} generated command path(s) validated)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
