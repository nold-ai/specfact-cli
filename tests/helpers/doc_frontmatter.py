"""Shared helpers for doc frontmatter unit and integration tests."""

from __future__ import annotations

import datetime
import importlib.util
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast


def repo_root() -> Path:
    """Repository root (parent of ``tests/``)."""
    return Path(__file__).resolve().parents[2]


def load_check_doc_frontmatter_module() -> Any:
    """Load ``scripts/check_doc_frontmatter.py`` without mutating ``sys.path``."""
    script_path = repo_root() / "scripts" / "check_doc_frontmatter.py"
    spec = importlib.util.spec_from_file_location("check_doc_frontmatter", script_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    dfm = getattr(module, "DocFrontmatter", None)
    if dfm is not None:
        dfm.model_rebuild(_types_namespace={"datetime": datetime})
    return module


def validation_main_fn(mod: object) -> Callable[[list[str] | None], int]:
    """Return ``check_doc_frontmatter.main`` with a concrete type for static analysis."""
    return cast(Callable[[list[str] | None], int], mod.main)


VALID_DOC_FRONTMATTER = """---
title: "Valid Document"
doc_owner: src/test/module
tracks:
  - src/test/**
last_reviewed: 2026-03-20
exempt: false
exempt_reason: ""
---

# Valid content"""


def write_enforced(root: Path, *relative_paths: str) -> None:
    """Write ``docs/.doc-frontmatter-enforced`` with the given repo-relative paths."""
    enforced = root / "docs" / ".doc-frontmatter-enforced"
    enforced.parent.mkdir(parents=True, exist_ok=True)
    enforced.write_text("\n".join(relative_paths) + "\n", encoding="utf-8")


def enforce_all_markdown_under_docs(root: Path) -> None:
    """Populate enforced list with every ``docs/**/*.md`` path (except the enforced file itself)."""
    lines: list[str] = []
    docs = root / "docs"
    if docs.exists():
        for p in docs.rglob("*.md"):
            if p.name == ".doc-frontmatter-enforced":
                continue
            lines.append(p.relative_to(root).as_posix())
    write_enforced(root, *lines)
