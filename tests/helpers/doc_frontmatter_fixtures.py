"""Shared pytest fixtures for doc frontmatter unit and integration tests."""

from __future__ import annotations

from collections.abc import Generator

import pytest

from tests.helpers.doc_frontmatter import load_check_doc_frontmatter_module
from tests.helpers.doc_frontmatter_types import CheckDocFrontmatterModule


@pytest.fixture(scope="session")
def check_doc_frontmatter_module() -> CheckDocFrontmatterModule:
    """Single loaded instance of ``scripts/check_doc_frontmatter.py`` (no ``sys.path`` hacks)."""
    return load_check_doc_frontmatter_module()


@pytest.fixture(autouse=True)
def _clear_doc_frontmatter_root(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DOC_FRONTMATTER_ROOT", raising=False)


@pytest.fixture(autouse=True)
def _clear_resolve_owner_cache(check_doc_frontmatter_module: CheckDocFrontmatterModule) -> Generator[None, None, None]:
    """Isolate ``lru_cache`` on owner resolution across tests."""
    check_doc_frontmatter_module._resolve_owner_impl.cache_clear()
    yield
