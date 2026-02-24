"""Tests for module denylist and publisher trust checks."""

from __future__ import annotations

from pathlib import Path

import pytest

from specfact_cli.registry import module_security


def test_get_denylisted_modules_parses_lines_and_comments(tmp_path: Path) -> None:
    denylist = tmp_path / "denylist.txt"
    denylist.write_text(
        "\n# comment\nblocked\nanother-blocked # inline comment\n\n",
        encoding="utf-8",
    )

    values = module_security.get_denylisted_modules(denylist)

    assert values == {"blocked", "another-blocked"}


def test_assert_module_allowed_raises_for_denylisted(monkeypatch) -> None:
    monkeypatch.setattr(
        "specfact_cli.registry.module_security.get_denylisted_modules",
        lambda path=None: {"blocked"},
    )
    monkeypatch.setattr(
        "specfact_cli.registry.module_security.get_denylist_path",
        lambda: Path("/tmp/denylist.txt"),
    )

    with pytest.raises(ValueError, match="denylisted"):
        module_security.assert_module_allowed("blocked")


def test_ensure_publisher_trusted_requires_flag_in_non_interactive(monkeypatch) -> None:
    monkeypatch.setattr("specfact_cli.registry.module_security.get_trusted_publishers", set)

    with pytest.raises(ValueError, match="--trust-non-official"):
        module_security.ensure_publisher_trusted(
            "community-dev",
            trust_non_official=False,
            non_interactive=True,
        )


def test_ensure_publisher_trusted_persists_when_flag_enabled(monkeypatch) -> None:
    persisted: dict[str, list[str]] = {"trusted_module_publishers": []}
    monkeypatch.setattr("specfact_cli.registry.module_security.get_trusted_publishers", set)
    monkeypatch.setattr(
        "specfact_cli.registry.module_security._persist_trusted_publishers",
        lambda publishers: persisted.update({"trusted_module_publishers": sorted(publishers)}),
    )

    module_security.ensure_publisher_trusted(
        "community-dev",
        trust_non_official=True,
        non_interactive=True,
    )

    assert persisted["trusted_module_publishers"] == ["community-dev"]
