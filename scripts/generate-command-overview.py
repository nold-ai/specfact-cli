#!/usr/bin/env python3
"""Generate deterministic command overview artifacts for humans and AI agents."""

from __future__ import annotations

import argparse
import difflib
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any

from typer.main import get_command


REPO_ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = REPO_ROOT / "docs" / "reference" / "commands.generated.json"
MARKDOWN_PATH = REPO_ROOT / "docs" / "reference" / "commands.generated.md"
LLMS_PATH = REPO_ROOT / "llms.txt"
CORE_APP_MOUNTS = (
    ("specfact_cli.modules.init.src.commands", "app", ("specfact", "init"), "core"),
    ("specfact_cli.modules.module_registry.src.commands", "app", ("specfact", "module"), "core"),
    ("specfact_cli.modules.upgrade.src.commands", "app", ("specfact", "upgrade"), "core"),
)
MODULE_APP_MOUNTS = (
    ("specfact_backlog.backlog.commands", "app", ("specfact", "backlog"), "nold-ai/specfact-backlog"),
    ("specfact_codebase.code.commands", "app", ("specfact", "code"), "nold-ai/specfact-codebase"),
    ("specfact_code_review.review.commands", "app", ("specfact", "code", "review"), "nold-ai/specfact-code-review"),
    ("specfact_govern.govern.commands", "app", ("specfact", "govern"), "nold-ai/specfact-govern"),
    ("specfact_project.project.commands", "app", ("specfact", "project"), "nold-ai/specfact-project"),
    ("specfact_spec.spec.commands", "app", ("specfact", "spec"), "nold-ai/specfact-spec"),
)


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
    modules_repo = os.environ.get("SPECFACT_MODULES_REPO", "").strip()
    module_repo_candidates = [
        Path(modules_repo).expanduser() if modules_repo else None,
        REPO_ROOT.parent / "specfact-cli-modules",
        _paired_worktree_repo("specfact-cli-worktrees", "specfact-cli-modules-worktrees"),
    ]
    for candidate in module_repo_candidates:
        if candidate is None:
            continue
        packages_dir = candidate / "packages"
        if not packages_dir.is_dir():
            continue
        os.environ.setdefault("SPECFACT_MODULES_REPO", str(candidate.resolve()))
        for src_path in sorted(packages_dir.glob("*/src")):
            src = str(src_path.resolve())
            if src not in sys.path:
                sys.path.insert(0, src)
    src = str(REPO_ROOT / "src")
    if src not in sys.path:
        sys.path.insert(0, src)


def _import_typer(module_path: str, attr_name: str) -> Any:
    module = importlib.import_module(module_path)
    return getattr(module, attr_name)


def _command_options(command: Any) -> list[str]:
    options: set[str] = set()
    for param in command.params:
        if hasattr(param, "opts"):
            options.update(opt for opt in [*param.opts, *param.secondary_opts] if opt.startswith("--"))
    return sorted(options)


def _command_arguments(command: Any) -> list[dict[str, Any]]:
    arguments: list[dict[str, Any]] = []
    for param in command.params:
        if not hasattr(param, "opts") and hasattr(param, "human_readable_name"):
            arguments.append(
                {
                    "name": param.human_readable_name,
                    "required": bool(param.required),
                    "nargs": param.nargs,
                }
            )
    return arguments


def _command_children(command: Any) -> dict[str, Any]:
    command = _materialized_command(command)
    if not (hasattr(command, "list_commands") and hasattr(command, "get_command")):
        return {}
    context_cls = command.context_class
    with context_cls(command, info_name=command.name) as ctx:
        children: dict[str, Any] = {}
        for name in command.list_commands(ctx):
            if name == "__delegate__":
                continue
            child = command.get_command(ctx, name)
            if child is not None:
                children[name] = child
        return children


def _materialized_command(command: Any) -> Any:
    real_group_loader = getattr(command, "_get_real_click_group", None)
    if callable(real_group_loader):
        real_group = real_group_loader()
        if hasattr(real_group, "params"):
            return real_group
    return command


def _bare_invocation(command: Any) -> str:
    command = _materialized_command(command)
    is_group = hasattr(command, "list_commands") and hasattr(command, "get_command")
    if is_group and bool(getattr(command, "invoke_without_command", False)):
        return "executes"
    if is_group:
        return "requires-subcommand"
    return "executes"


def _walk(
    command: Any,
    path: tuple[str, ...],
    source: str,
    owner_package: str,
    install_prerequisite: str,
) -> list[dict[str, Any]]:
    command = _materialized_command(command)
    children = _command_children(command)
    record = {
        "command": " ".join(path),
        "owner_repo": "nold-ai/specfact-cli",
        "owner_package": owner_package,
        "install_prerequisite": install_prerequisite,
        "short_help": (command.short_help or "").strip(),
        "arguments": _command_arguments(command),
        "bare_invocation": _bare_invocation(command),
        "options": _command_options(command),
        "subcommands": sorted(children),
        "source": source,
        "hidden": bool(getattr(command, "hidden", False)),
        "deprecated": bool(getattr(command, "deprecated", False)),
    }
    records = [record]
    for name, child in sorted(children.items()):
        records.extend(_walk(child, (*path, name), source, owner_package, install_prerequisite))
    return records


def _root_record(root_subcommands: list[str]) -> dict[str, Any]:
    _ensure_imports()
    from specfact_cli.cli import app

    root_command = get_command(app)
    return {
        "command": "specfact",
        "owner_repo": "nold-ai/specfact-cli",
        "owner_package": "core",
        "install_prerequisite": "Install specfact-cli.",
        "short_help": (root_command.short_help or "").strip(),
        "arguments": _command_arguments(root_command),
        "bare_invocation": "executes",
        "options": _command_options(root_command),
        "subcommands": root_subcommands,
        "source": "specfact_cli.cli:app",
        "hidden": bool(getattr(root_command, "hidden", False)),
        "deprecated": bool(getattr(root_command, "deprecated", False)),
    }


def build_records() -> list[dict[str, Any]]:
    _ensure_imports()
    records: list[dict[str, Any]] = []
    for module_path, attr_name, prefix, owner_package in (*CORE_APP_MOUNTS, *MODULE_APP_MOUNTS):
        app = _import_typer(module_path, attr_name)
        install_prerequisite = (
            "Install specfact-cli." if owner_package == "core" else f"specfact module install {owner_package}"
        )
        records.extend(
            _walk(
                get_command(app),
                prefix,
                f"{module_path}:{attr_name}",
                owner_package,
                install_prerequisite,
            )
        )
    root_subcommands = sorted(
        {str(record["command"]).split()[1] for record in records if len(str(record["command"]).split()) > 1}
    )
    return [_root_record(root_subcommands), *sorted(records, key=lambda record: record["command"])]


def _render_markdown(records: list[dict[str, Any]]) -> str:
    lines = [
        "---",
        "layout: default",
        "title: Generated SpecFact CLI Command Overview",
        "permalink: /reference/generated-command-overview/",
        "exempt: true",
        "exempt_reason: Generated command contract artifact.",
        "---",
        "",
        "# Generated SpecFact CLI Command Overview",
        "",
        "This file is generated from the current CLI command tree. Do not edit by hand.",
        "",
        "| Command | Owner | Options | Subcommands | Context |",
        "| --- | --- | --- | --- | --- |",
    ]
    for record in records:
        arguments = ", ".join(
            f"{arg['name']}{' (required)' if arg.get('required') else ''}" for arg in record["arguments"]
        )
        options = ", ".join(record["options"]) or "-"
        subcommands = ", ".join(record["subcommands"]) or "-"
        help_text = str(record["short_help"]).replace("\n", " ")
        lines.append(
            f"| `{record['command']}` | {record['owner_package']} | {options}; args: {arguments or '-'} | "
            f"{subcommands} | {help_text} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_llms(markdown: str) -> str:
    return "\n".join(
        [
            "# SpecFact CLI Commands",
            "",
            "Use this generated overview as the current command contract before following older docs or prompts.",
            "",
            markdown,
        ]
    )


def _desired_outputs() -> dict[Path, str]:
    records = build_records()
    json_text = json.dumps(records, indent=2, sort_keys=True) + "\n"
    markdown = _render_markdown(records)
    return {
        JSON_PATH: json_text,
        MARKDOWN_PATH: markdown,
        LLMS_PATH: _render_llms(markdown),
    }


def _check(outputs: dict[Path, str]) -> int:
    failures = []
    for path, expected in outputs.items():
        actual = path.read_text(encoding="utf-8") if path.exists() else ""
        if actual != expected:
            failures.append(path)
            diff = "\n".join(
                difflib.unified_diff(
                    actual.splitlines(),
                    expected.splitlines(),
                    fromfile=str(path),
                    tofile=f"{path} (generated)",
                    lineterm="",
                )
            )
            print(diff)
    if failures:
        print("Command overview artifacts are stale. Run: python scripts/generate-command-overview.py --write")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write generated artifacts")
    parser.add_argument("--check", action="store_true", help="Check generated artifacts are current")
    args = parser.parse_args(argv)
    outputs = _desired_outputs()
    if args.write:
        for path, text in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return 0
    return _check(outputs)


if __name__ == "__main__":
    raise SystemExit(main())
