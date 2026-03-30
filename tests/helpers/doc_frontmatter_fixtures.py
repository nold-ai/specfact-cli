"""Shared pytest fixtures for doc frontmatter unit and integration tests.

Registered from ``tests/conftest.py`` via ``pytest_plugins`` (Pytest 8+ requires a
root-level conftest for plugin lists; nested ``conftest.py`` cannot use
``pytest_plugins``).
"""

from __future__ import annotations

import pytest

from tests.helpers.doc_frontmatter import load_check_doc_frontmatter_module
from tests.helpers.doc_frontmatter_types import CheckDocFrontmatterModule


_DOC_FRONTMATTER_PATH = "test_doc_frontmatter"


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Clear owner-resolution cache between doc-frontmatter tests (lru_cache isolation)."""
    nodeid = getattr(item, "nodeid", "") or ""
    path_str = ""
    path = getattr(item, "path", None)
    if path is not None:
        path_str = str(path)
    if _DOC_FRONTMATTER_PATH not in nodeid and _DOC_FRONTMATTER_PATH not in path_str:
        return
    mod = load_check_doc_frontmatter_module()
    mod._resolve_owner_impl.cache_clear()


@pytest.fixture(scope="session")
def check_doc_frontmatter_module() -> CheckDocFrontmatterModule:
    """Single loaded instance of ``scripts/check_doc_frontmatter.py`` (no ``sys.path`` hacks)."""
    return load_check_doc_frontmatter_module()


@pytest.fixture(autouse=True)
def _clear_doc_frontmatter_root(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate ``DOC_FRONTMATTER_ROOT`` for doc-frontmatter tests only."""
    nodeid = getattr(request.node, "nodeid", "") or ""
    path_str = str(getattr(request.node, "path", ""))
    if _DOC_FRONTMATTER_PATH not in nodeid and _DOC_FRONTMATTER_PATH not in path_str:
        return
    monkeypatch.delenv("DOC_FRONTMATTER_ROOT", raising=False)
