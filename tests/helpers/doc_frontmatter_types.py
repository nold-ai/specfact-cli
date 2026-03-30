"""Typing helpers for dynamically loaded ``check_doc_frontmatter`` module."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ResolveOwnerImplWithCache(Protocol):
    """Callable owner resolver exposing ``cache_clear`` like ``functools.lru_cache``."""

    def __call__(self, owner: str, root_key: str) -> bool:
        raise NotImplementedError

    def cache_clear(self) -> None:
        raise NotImplementedError


@runtime_checkable
class CheckDocFrontmatterModule(Protocol):
    """Structural type for ``scripts/check_doc_frontmatter.py`` loaded via importlib."""

    DocFrontmatter: type[DocFrontmatterModel]
    parse_frontmatter: Callable[[Path], dict[str, Any]]
    resolve_owner: Callable[[str], bool]
    validate_glob_patterns: Callable[[list[str]], bool]
    suggest_frontmatter: Callable[[Path], str]
    extract_doc_owner: Callable[[str], str | None]
    get_all_md_files: Callable[[], list[Path]]
    rg_missing_doc_owner: Callable[[list[Path]], list[Path]]
    main: Callable[[list[str] | None], int]
    datetime: Any
    _resolve_owner_impl: ResolveOwnerImplWithCache


@runtime_checkable
class DocFrontmatterRecord(Protocol):
    """Minimal validated model instance shape used by tests."""

    title: str
    doc_owner: str
    tracks: list[str]
    last_reviewed: date


@runtime_checkable
class DocFrontmatterModel(Protocol):
    """Minimal model type exposing ``model_validate`` for tests."""

    @classmethod
    def model_validate(cls, data: dict[str, object]) -> DocFrontmatterRecord:
        raise NotImplementedError
