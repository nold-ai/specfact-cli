"""Shared fixtures for doc frontmatter integration tests."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _clear_doc_frontmatter_root(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DOC_FRONTMATTER_ROOT", raising=False)
