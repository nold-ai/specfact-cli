#!/usr/bin/env python3
"""Validate ``specfact …`` examples in docs against the Typer CLI (``--help`` on each path)."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from collections.abc import Mapping
from pathlib import Path

import yaml
from beartype import beartype
from icontract import ensure
from rich.console import Console
from typer.testing import CliRunner


_REPO_ROOT = Path(__file__).resolve().parents[1]

_ERR = Console(stderr=True)
_OUT = Console()

# Historical / illustrative pages: command lines are not guaranteed to match the current CLI.
_EXCLUDED_DOC_PATHS: frozenset[str] = frozenset()

# Root ``@app.callback`` options on ``specfact`` (see ``cli.py``). Values must be skipped so
# ``specfact --mode copilot import …`` yields ``import …`` for validation.
_GLOBAL_FLAGS_WITH_VALUE: frozenset[str] = frozenset(
    {
        "--mode",
        "--input-format",
        "--output-format",
    }
)
_GENERATED_COMMANDS_PATH = _REPO_ROOT / "docs" / "reference" / "commands.generated.json"
_GENERATED_PREFIX_CACHE: set[tuple[str, ...]] | None = None
_GUIDANCE_TEXT_SUFFIXES: frozenset[str] = frozenset(
    {
        ".jinja",
        ".j2",
        ".jinja2",
        ".json",
        ".md",
        ".mdc",
        ".py",
        ".rst",
        ".toml",
        ".txt",
        ".yaml",
        ".yml",
    }
)
_ADDITIONAL_GUIDANCE_ROOTS: tuple[Path, ...] = (
    _REPO_ROOT / ".github",
    _REPO_ROOT / "resources",
    _REPO_ROOT / "src",
    _REPO_ROOT / "src" / "specfact_cli" / "resources",
)
_GUIDANCE_INLINE_COMMAND_RE = re.compile(r"`(specfact\s+[^`\n]+)`")


def _ensure_repo_path() -> None:
    os.environ.setdefault("SPECFACT_REPO_ROOT", str(_REPO_ROOT))
    os.environ.setdefault("TEST_MODE", "true")
    src = _REPO_ROOT / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


_ensure_repo_path()

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
        if token in {"...", "COMMAND", "ARGS...", "[OPTIONS]", "[ARGS]", "[ARGS]...", "[COMMAND]", "[BUNDLE]"}:
            continue
        if token.startswith("[") and token.endswith("]"):
            continue
        out.append(token)
    return out


@beartype
@ensure(lambda result: isinstance(result, list), "must return a list")
def collect_specfact_commands_from_text(text: str) -> list[list[str]]:
    """Collect ``specfact …`` command token lists from Markdown *text*."""
    commands: list[list[str]] = []
    for body in _extract_code_block_bodies(text):
        for raw_line in body.splitlines():
            for segment in _split_shell_segments(raw_line):
                tokens = _tokens_from_specfact_line(segment)
                if tokens:
                    commands.append(tokens)
    return commands


@beartype
@ensure(lambda result: isinstance(result, list), "must return a list")
def collect_specfact_commands_from_guidance_text(text: str) -> list[list[str]]:
    """Collect command token lists from prose, templates, YAML, JSON, and Markdown guidance."""
    commands = collect_specfact_commands_from_text(text)
    for line in text.splitlines():
        for match in _GUIDANCE_INLINE_COMMAND_RE.finditer(line):
            tokens = _tokens_from_specfact_line(match.group(1))
            if tokens:
                commands.append(tokens)
        stripped = line.strip().lstrip("-").strip()
        candidates = [stripped]
        if ":" in stripped:
            candidates.append(stripped.split(":", 1)[1].strip())
        for candidate in candidates:
            candidate = candidate.strip().strip(",").strip("\"'")
            if not candidate.startswith("specfact "):
                continue
            tokens = _tokens_from_specfact_line(candidate)
            if tokens:
                commands.append(tokens)
            break
    return commands


def _cli_invoke_streams_text(result: object) -> str:
    """Stdout + stderr text for a CliRunner ``Result`` (stderr via bytes when split, else safe)."""
    out = (getattr(result, "stdout", None) or "").strip()
    err = ""
    stderr_bytes = getattr(result, "stderr_bytes", None)
    if stderr_bytes is not None:
        runner_obj = getattr(result, "runner", None)
        charset = getattr(runner_obj, "charset", "utf-8") if runner_obj else "utf-8"
        err = stderr_bytes.decode(charset, "replace").replace("\r\n", "\n").strip()
    else:
        try:
            err = (getattr(result, "stderr", None) or "").strip()
        except ValueError:
            err = ""
    return f"{out}\n{err}".strip()


@beartype
def _eval_prefix_help(runner: CliRunner, prefix: list[str]) -> tuple[bool, str]:
    """Return ``(True, "")`` if ``--help`` succeeds or the CLI is not installed; else ``(False, err)``."""
    result = runner.invoke(app, [*prefix, "--help"], catch_exceptions=True)
    exc = getattr(result, "exception", None)
    if result.exit_code == 0 and exc is None:
        return True, ""
    streams = _cli_invoke_streams_text(result)
    if exc is not None:
        last_err = f"{type(exc).__name__}: {exc!s}"[:800]
    else:
        last_err = streams[:800] if streams else f"exit {result.exit_code}"
    combined = (streams or last_err or "").lower()
    if "not installed" in combined and "install" in combined:
        return True, ""
    return False, last_err


def _generated_command_prefixes() -> set[tuple[str, ...]]:
    global _GENERATED_PREFIX_CACHE
    if _GENERATED_PREFIX_CACHE is not None:
        return _GENERATED_PREFIX_CACHE
    if not _GENERATED_COMMANDS_PATH.is_file():
        _GENERATED_PREFIX_CACHE = set()
        return _GENERATED_PREFIX_CACHE
    raw = json.loads(_GENERATED_COMMANDS_PATH.read_text(encoding="utf-8"))
    prefixes: set[tuple[str, ...]] = set()
    if isinstance(raw, list):
        for entry in raw:
            if not isinstance(entry, dict):
                continue
            command = entry.get("command")
            if not isinstance(command, str):
                continue
            parts = tuple(command.split())
            if parts[:1] == ("specfact",) and len(parts) > 1:
                prefixes.add(parts[1:])
    _GENERATED_PREFIX_CACHE = prefixes
    return prefixes


def _generated_prefix_match(tokens: list[str]) -> bool:
    generated = _generated_command_prefixes()
    if not generated:
        return False
    return any(tuple(tokens[:size]) in generated for size in range(len(tokens), 0, -1))


@beartype
@ensure(
    lambda result: (
        isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], bool) and isinstance(result[1], str)
    ),
    "must return (bool, str)",
)
def validate_command_tokens(tokens: list[str]) -> tuple[bool, str]:
    """True if some prefix of *tokens* is a valid CLI path (``… --help`` exits 0)."""
    tokens = _sanitize_command_tokens(tokens)
    if not tokens:
        return True, ""
    invalid_code_import = _invalid_code_import_order_message(tokens)
    if invalid_code_import:
        return False, invalid_code_import
    if _generated_prefix_match(tokens):
        return True, ""
    if _generated_command_prefixes():
        return (
            False,
            "Command path is not present in docs/reference/commands.generated.json. "
            "Run `hatch run generate-command-overview` if the CLI changed; otherwise fix the docs.",
        )

    runner = CliRunner()
    last_err = ""
    for k in range(len(tokens), 0, -1):
        prefix = tokens[:k]
        ok, msg = _eval_prefix_help(runner, prefix)
        if ok:
            return True, ""
        last_err = msg

    return False, last_err


@beartype
def _invalid_code_import_order_message(tokens: list[str]) -> str:
    if len(tokens) < 4 or tokens[:2] != ["code", "import"]:
        return ""
    try:
        first_flag_index = next(index for index, token in enumerate(tokens[2:], start=2) if token.startswith("-"))
    except StopIteration:
        return ""
    positional_before_flag = [
        token
        for token in tokens[2:first_flag_index]
        if token not in {"from-code", "from-bridge"} and not re.match(r"^<[^>]+>$", token)
    ]
    if not positional_before_flag:
        return ""
    return (
        "Invalid specfact code import option order: options such as --repo must appear before the bundle "
        "argument, for example `specfact code import --repo . legacy-api`, or use the explicit "
        "`specfact code import from-code legacy-api --repo .` form."
    )


@beartype
def _should_skip_markdown_path(rel: Path, rel_posix: str) -> bool:
    if "_site" in rel.parts or "vendor" in rel.parts:
        return True
    if rel_posix == "docs/migration/migration-guide.md":
        return False
    return rel_posix.startswith("docs/migration/") or rel_posix in _EXCLUDED_DOC_PATHS


@beartype
def _should_skip_guidance_path(rel: Path) -> bool:
    if any(part in {"_site", "vendor", ".venv", "__pycache__"} for part in rel.parts):
        return True
    return rel.as_posix() in _EXCLUDED_DOC_PATHS


@beartype
def _scan_docs_for_command_validation(docs_root: Path) -> tuple[set[tuple[str, ...]], list[str]]:
    seen: set[tuple[str, ...]] = set()
    failures: list[str] = []
    for md_path in sorted(docs_root.rglob("*.md")):
        rel = md_path.relative_to(_REPO_ROOT)
        rel_posix = rel.as_posix()
        if _should_skip_markdown_path(rel, rel_posix):
            continue
        try:
            text = md_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            failures.append(f"{rel}: cannot decode file as UTF-8 ({exc})")
            continue
        for tokens in collect_specfact_commands_from_text(text):
            key = tuple(tokens)
            if key in seen:
                continue
            seen.add(key)
            ok, msg = validate_command_tokens(tokens)
            if not ok:
                failures.append(f"{rel}: specfact {' '.join(tokens)} — {msg}")
    return seen, failures


@beartype
def _iter_additional_guidance_paths(docs_root: Path) -> list[Path]:
    """Return non-doc guidance/template files whose command examples must stay current."""
    roots = [docs_root, *_ADDITIONAL_GUIDANCE_ROOTS]
    paths: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in _GUIDANCE_TEXT_SUFFIXES:
                continue
            rel = path.relative_to(_REPO_ROOT)
            if _should_skip_guidance_path(rel):
                continue
            if rel.parts[0] == "docs" and path.suffix.lower() == ".md":
                continue
            paths.add(path)
    return sorted(paths)


@beartype
def _scan_guidance_templates_for_command_validation(docs_root: Path) -> tuple[set[tuple[str, ...]], list[str]]:
    """Validate command examples in non-Markdown docs, prompts, Jinja2 templates, YAML, JSON, and text assets."""
    seen: set[tuple[str, ...]] = set()
    failures: list[str] = []
    for path in _iter_additional_guidance_paths(docs_root):
        rel = path.relative_to(_REPO_ROOT)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            failures.append(f"{rel}: cannot decode file as UTF-8 ({exc})")
            continue
        for tokens in collect_specfact_commands_from_guidance_text(text):
            key = tuple(tokens)
            if key in seen:
                continue
            seen.add(key)
            ok, msg = validate_command_tokens(tokens)
            if not ok:
                failures.append(f"{rel}: specfact {' '.join(tokens)} — {msg}")
    return seen, failures


@beartype
def _extract_front_matter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}

    lines = text.splitlines()
    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break
    if end_index is None:
        return {}

    metadata: dict[str, str] = {}
    for raw_line in lines[1:end_index]:
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata


@beartype
def _published_route_for_path(path: Path, metadata: dict[str, str], docs_root: Path) -> str:
    permalink = metadata.get("permalink")
    if permalink:
        route = permalink
    else:
        rel = path.relative_to(docs_root)
        route = "/" + str(rel.with_suffix("")).replace(os.sep, "/").lstrip("/")
    if route != "/" and not route.endswith("/"):
        route += "/"
    return route


@beartype
def _build_published_docs_index(docs_root: Path) -> dict[str, Path]:
    route_to_path: dict[str, Path] = {}
    for md_path in sorted(docs_root.rglob("*.md")):
        rel = md_path.relative_to(_REPO_ROOT)
        if "_site" in rel.parts or "vendor" in rel.parts:
            continue
        metadata = _extract_front_matter(md_path.read_text(encoding="utf-8"))
        route_to_path[_published_route_for_path(md_path, metadata, docs_root)] = md_path
    return route_to_path


@beartype
def _mapping_entries(raw_value: object) -> list[Mapping[str, object]]:
    if not isinstance(raw_value, list):
        return []
    return [entry for entry in raw_value if isinstance(entry, Mapping)]


@beartype
def _mapping_list_entries(mapping: Mapping[str, object], key: str) -> list[Mapping[str, object]]:
    return _mapping_entries(mapping.get(key))


@beartype
def _mapping_string(mapping: Mapping[str, object], key: str) -> str | None:
    value = mapping.get(key)
    return value if isinstance(value, str) else None


@beartype
def _iter_nav_urls(nav_data: list[dict[str, object]]) -> list[str]:
    urls: list[str] = []
    for section in nav_data:
        for item in _mapping_list_entries(section, "items"):
            url = _mapping_string(item, "url")
            if url is not None:
                urls.append(url)
        for bundle in _mapping_list_entries(section, "bundles"):
            for item in _mapping_list_entries(bundle, "items"):
                url = _mapping_string(item, "url")
                if url is not None:
                    urls.append(url)
    return urls


@beartype
def _validate_nav_targets(docs_root: Path) -> list[str]:
    nav_path = docs_root / "_data" / "nav.yml"
    if not nav_path.is_file():
        return [f"{nav_path.relative_to(_REPO_ROOT)}: missing nav data file"]

    try:
        nav_data = yaml.safe_load(nav_path.read_text(encoding="utf-8")) or []
    except yaml.YAMLError as exc:
        return [f"{nav_path.relative_to(_REPO_ROOT)}: unable to parse nav data ({exc})"]
    if not isinstance(nav_data, list):
        return [f"{nav_path.relative_to(_REPO_ROOT)}: nav data must be a list"]

    route_index = _build_published_docs_index(docs_root)
    failures: list[str] = []
    for raw_url in _iter_nav_urls(nav_data):
        url = raw_url if raw_url == "/" else raw_url.rstrip("/") + "/"
        if url not in route_index:
            failures.append(f"{nav_path.relative_to(_REPO_ROOT)}: unknown docs route {raw_url}")
    return failures


@beartype
@ensure(lambda result: result in (0, 1), "exit code must be 0 or 1")
def main() -> int:
    docs_root = _REPO_ROOT / "docs"
    if not docs_root.is_dir():
        _ERR.print("check-docs-commands: no docs/ directory", markup=False)
        return 1

    seen, failures = _scan_docs_for_command_validation(docs_root)
    guidance_seen, guidance_failures = _scan_guidance_templates_for_command_validation(docs_root)
    seen.update(guidance_seen)
    failures.extend(guidance_failures)
    failures.extend(_validate_nav_targets(docs_root))

    if failures:
        _ERR.print("Docs command validation failed:", markup=False)
        for line in failures:
            _ERR.print(line, markup=False)
        return 1
    _OUT.print(
        f"check-docs-commands: OK ({len(seen)} unique command prefix(es) checked)",
        markup=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
