"""Shared pytest fixtures for doc frontmatter unit and integration tests.

Registered from ``tests/conftest.py`` via ``pytest_plugins`` (Pytest 8+ requires a
root-level conftest for plugin lists; nested ``conftest.py`` cannot use
``pytest_plugins``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest


if TYPE_CHECKING:
    from tests.helpers.doc_frontmatter_types import CheckDocFrontmatterModule


@pytest.fixture
def check_doc_frontmatter_module(monkeypatch: pytest.MonkeyPatch) -> CheckDocFrontmatterModule:
    """Load one isolated checker instance for a requesting doc-frontmatter test."""
    from tests.helpers.doc_frontmatter import load_check_doc_frontmatter_module

    monkeypatch.delenv("DOC_FRONTMATTER_ROOT", raising=False)
    module = load_check_doc_frontmatter_module()
    module._resolve_owner_impl.cache_clear()
    return module
