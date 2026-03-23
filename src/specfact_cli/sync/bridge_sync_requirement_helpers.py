"""Helpers for extracting OpenSpec-style requirement text from proposal descriptions (radon split)."""

from __future__ import annotations

import re
from typing import Any

from beartype import beartype
from icontract import ensure, require


@require(lambda section_content: section_content is None or isinstance(section_content, str))
@ensure(lambda result: isinstance(result, list))
@beartype
def bridge_sync_extract_section_details(section_content: str | None) -> list[str]:
    """Pull bullet/detail lines from a markdown subsection."""
    if not section_content:
        return []

    details: list[str] = []
    in_code_block = False

    for raw_line in section_content.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if not stripped:
            continue

        if in_code_block:
            cleaned = re.sub(r"^[-*]\s*", "", stripped).strip()
            if cleaned.startswith("#") or not cleaned:
                continue
            cleaned = re.sub(r"^\[\s*[xX]?\s*\]\s*", "", cleaned).strip()
            details.append(cleaned)
            continue

        if stripped.startswith(("#", "---")):
            continue

        cleaned = re.sub(r"^[-*]\s*", "", stripped)
        cleaned = re.sub(r"^\d+\.\s*", "", cleaned)
        cleaned = cleaned.strip()
        cleaned = re.sub(r"^\[\s*[xX]?\s*\]\s*", "", cleaned).strip()
        if cleaned:
            details.append(cleaned)

    return details


def _normalize_detail_leading_patterns(cleaned: str, lower: str) -> tuple[str, str]:
    if lower.startswith("new command group"):
        rest = re.sub(r"^new\s+command\s+group\s*:\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = f"provides command group {rest}".strip()
        return cleaned, cleaned.lower()
    if lower.startswith("location:"):
        rest = re.sub(r"^location\s*:\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = f"stores tokens at {rest}".strip()
        return cleaned, cleaned.lower()
    if lower.startswith("format:"):
        rest = re.sub(r"^format\s*:\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = f"uses format {rest}".strip()
        return cleaned, cleaned.lower()
    if lower.startswith("permissions:"):
        rest = re.sub(r"^permissions\s*:\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = f"enforces permissions {rest}".strip()
        return cleaned, cleaned.lower()
    if ":" in cleaned:
        _prefix, rest = cleaned.split(":", 1)
        if rest.strip():
            cleaned = rest.strip()
            return cleaned, cleaned.lower()
    return cleaned, lower


def _normalize_detail_phrase_forms(cleaned: str, lower: str) -> tuple[str, str]:
    if lower.startswith("users can"):
        cleaned = f"allows users to {cleaned[10:].lstrip()}".strip()
        return cleaned, cleaned.lower()
    if re.match(r"^specfact\s+", cleaned):
        cleaned = f"supports `{cleaned}` command"
        return cleaned, cleaned.lower()
    return cleaned, lower


_VERBS_LOWER_FIRST = frozenset(
    {
        "uses",
        "use",
        "provides",
        "provide",
        "stores",
        "store",
        "supports",
        "support",
        "enforces",
        "enforce",
        "allows",
        "allow",
        "leverages",
        "leverage",
        "adds",
        "add",
        "can",
        "custom",
        "supported",
        "zero-configuration",
    }
)


def _lowercase_leading_verb_sentence(cleaned: str) -> str:
    if not cleaned:
        return cleaned
    first_word = cleaned.split()[0].rstrip(".,;:!?")
    if first_word.lower() in _VERBS_LOWER_FIRST and cleaned[0].isupper():
        return cleaned[0].lower() + cleaned[1:]
    return cleaned


@require(lambda detail: isinstance(detail, str))
@ensure(lambda result: isinstance(result, str))
@beartype
def bridge_sync_normalize_detail_for_and(detail: str) -> str:
    """Normalize a detail line for AND clauses in requirement scenarios."""
    cleaned = detail.strip()
    if not cleaned:
        return ""

    cleaned = cleaned.replace("**", "").strip()
    cleaned = cleaned.lstrip("*").strip()
    if cleaned.lower() in {"commands:", "commands"}:
        return ""

    cleaned = re.sub(r"^\d+\.\s*", "", cleaned).strip()
    cleaned = re.sub(r"^\[\s*[xX]?\s*\]\s*", "", cleaned).strip()
    lower = cleaned.lower()

    cleaned, lower = _normalize_detail_leading_patterns(cleaned, lower)
    cleaned, lower = _normalize_detail_phrase_forms(cleaned, lower)

    cleaned = _lowercase_leading_verb_sentence(cleaned)

    if cleaned and not cleaned.endswith("."):
        cleaned += "."

    return cleaned


@require(lambda text: isinstance(text, str))
@ensure(lambda result: isinstance(result, list))
@beartype
def bridge_sync_parse_formatted_sections(text: str) -> list[dict[str, Any]]:
    """Parse NEW/EXTEND/MODIFY marker sections from a What Changes body."""
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    marker_pattern = re.compile(
        r"^-\s*\*\*(NEW|EXTEND|FIX|ADD|MODIFY|UPDATE|REMOVE|REFACTOR)\*\*:\s*(.+)$",
        re.IGNORECASE,
    )

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        marker_match = marker_pattern.match(stripped)
        if marker_match:
            if current:
                sections.append(
                    {
                        "title": current["title"],
                        "content": "\n".join(current["content"]).strip(),
                    }
                )
            current = {"title": marker_match.group(2).strip(), "content": []}
            continue
        if current is not None:
            current["content"].append(raw_line)

    if current:
        sections.append(
            {
                "title": current["title"],
                "content": "\n".join(current["content"]).strip(),
            }
        )

    return sections
