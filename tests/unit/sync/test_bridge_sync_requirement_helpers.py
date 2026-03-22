"""Unit tests for bridge_sync_requirement_helpers."""

from specfact_cli.sync.bridge_sync_requirement_helpers import (
    bridge_sync_extract_section_details,
    bridge_sync_normalize_detail_for_and,
    bridge_sync_parse_formatted_sections,
)


def test_bridge_sync_parse_formatted_sections_parses_markers() -> None:
    text = """- **NEW**: Auth
line one
- **EXTEND**: Other
keep
"""
    sections = bridge_sync_parse_formatted_sections(text)
    assert len(sections) == 2
    assert sections[0]["title"] == "Auth"
    assert "line one" in sections[0]["content"]
    assert sections[1]["title"] == "Other"


def test_bridge_sync_extract_section_details_skips_headers() -> None:
    body = "- one\n- two\n"
    assert bridge_sync_extract_section_details(body) == ["one", "two"]


def test_bridge_sync_normalize_detail_for_and() -> None:
    assert "provides command group" in bridge_sync_normalize_detail_for_and("New command group: foo")
    assert bridge_sync_normalize_detail_for_and("") == ""
