#!/usr/bin/env python3
"""Validate ``specfact …`` examples in docs against the Typer CLI (``--help`` on each path)."""

from __future__ import annotations

import os
import re
import shlex
import sys
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[1]

# Historical / illustrative pages: command lines are not guaranteed to match the current CLI.
_EXCLUDED_DOC_PATHS: frozenset[str] = frozenset(
    {
        "docs/core-cli/modes.md",
    }
)

# Root ``@app.callback`` options on ``specfact`` (see ``cli.py``). Values must be skipped so
# ``specfact --mode copilot import …`` yields ``import …`` for validation.
_GLOBAL_FLAGS_WITH_VALUE: frozenset[str] = frozenset(
    {
        "--mode",
        "--input-format",
        "--output-format",
    }
)


def _ensure_repo_path() -> None:
    os.environ.setdefault("SPECFACT_REPO_ROOT", str(_REPO_ROOT))
    os.environ.setdefault("TEST_MODE", "true")
    src = _REPO_ROOT / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


_ensure_repo_path()

from beartype import beartype  # noqa: E402
from typer.testing import CliRunner  # noqa: E402

from specfact_cli.cli import app  # noqa: E402


@beartype
def _extract_code_block_bodies(markdown: str) -> list[str]:
    bodies: list[str] = []
    parts = markdown.split("```")
    for index in range(1, len(parts), 2):
        block = parts[index]
        if "\n" not in block:
            continue
        first_nl = block.index("\n")
        bodies.append(block[first_nl + 1 :])
    return bodies


@beartype
def _split_shell_segments(line: str) -> list[str]:
    return [segment.strip() for segment in line.split("&&") if segment.strip()]


@beartype
def _strip_leading_global_options(parts: list[str]) -> list[str]:
    """Remove root-level ``specfact`` flags (``--mode``, ``--debug``, …) before the subcommand path."""
    i = 0
    n = len(parts)
    while i < n:
        tok = parts[i]
        if not tok.startswith("-"):
            break
        if tok in _GLOBAL_FLAGS_WITH_VALUE:
            i += 1
            if i < n and not parts[i].startswith("-"):
                i += 1
            continue
        i += 1
    return parts[i:]


@beartype
def _tokens_from_specfact_line(line: str) -> list[str] | None:
    segment = line.strip()
    if segment.startswith("$"):
        segment = segment[1:].strip()
    if not segment.startswith("specfact "):
        return None
    rest = segment[len("specfact ") :].strip()
    if not rest or rest.startswith("#"):
        return None
    if "#" in rest:
        rest = rest.split("#", 1)[0].strip()
    try:
        parts = shlex.split(rest, posix=True)
    except ValueError:
        return None
    parts = _strip_leading_global_options(parts)
    if not parts:
        return None
    out: list[str] = []
    for part in parts:
        if part.startswith("-"):
            break
        out.append(part)
    return out if out else None


@beartype
def _sanitize_command_tokens(tokens: list[str]) -> list[str]:
    """Drop placeholder tokens like ``<name>`` and ``[OPTIONS]`` from doc examples."""
    out: list[str] = []
    for token in tokens:
        if re.match(r"^<[^>]+>$", token):
            continue
        if token in {"[OPTIONS]", "[ARGS]", "[COMMAND]", "[BUNDLE]"}:
            continue
        if token.startswith("[") and token.endswith("]"):
            continue
        out.append(token)
    return out


@beartype
def collect_specfact_commands_from_text(text: str) -> list[list[str]]:
    commands: list[list[str]] = []
    for body in _extract_code_block_bodies(text):
        for raw_line in body.splitlines():
            for segment in _split_shell_segments(raw_line):
                tokens = _tokens_from_specfact_line(segment)
                if tokens:
                    commands.append(tokens)
    return commands


@beartype
def validate_command_tokens(tokens: list[str]) -> tuple[bool, str]:
    """True if some prefix of *tokens* is a valid CLI path (``… --help`` exits 0)."""
    tokens = _sanitize_command_tokens(tokens)
    if not tokens:
        return True, ""

    runner = CliRunner(mix_stderr=False)
    last_err = ""
    for k in range(len(tokens), 0, -1):
        prefix = tokens[:k]
        result = runner.invoke(app, [*prefix, "--help"], catch_exceptions=False)
        if result.exit_code == 0:
            return True, ""
        err = (result.stderr or result.stdout or getattr(result, "output", None) or "").strip()
        last_err = err[:800] if err else f"exit {result.exit_code}"
        combined = (err or "").lower()
        if "not installed" in combined and "install" in combined:
            return True, ""

    return False, last_err


@beartype
def main() -> int:
    docs_root = _REPO_ROOT / "docs"
    if not docs_root.is_dir():
        print("check-docs-commands: no docs/ directory", file=sys.stderr)
        return 1

    seen: set[tuple[str, ...]] = set()
    failures: list[str] = []

    for md_path in sorted(docs_root.rglob("*.md")):
        if "_site" in md_path.parts or "vendor" in md_path.parts:
            continue
        rel = md_path.relative_to(_REPO_ROOT)
        rel_posix = rel.as_posix()
        if rel_posix.startswith("docs/migration/") or rel_posix in _EXCLUDED_DOC_PATHS:
            continue
        text = md_path.read_text(encoding="utf-8")
        for tokens in collect_specfact_commands_from_text(text):
            key = tuple(tokens)
            if key in seen:
                continue
            seen.add(key)
            ok, msg = validate_command_tokens(tokens)
            if not ok:
                failures.append(f"{rel}: specfact {' '.join(tokens)} — {msg}")

    if failures:
        print("Docs command validation failed:", file=sys.stderr)
        for line in failures:
            print(line, file=sys.stderr)
        return 1
    print(f"check-docs-commands: OK ({len(seen)} unique command prefix(es) checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
