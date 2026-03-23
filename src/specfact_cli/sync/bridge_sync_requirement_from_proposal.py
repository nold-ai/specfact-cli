"""Build OpenSpec requirement text from ChangeProposal content (split from bridge_sync for CC)."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.sync.bridge_sync_requirement_helpers import (
    bridge_sync_extract_section_details,
    bridge_sync_normalize_detail_for_and,
    bridge_sync_parse_formatted_sections,
)


_SKIP_SECTION_TITLES = frozenset(
    {
        "architecture overview",
        "purpose",
        "introduction",
        "overview",
        "documentation",
        "testing",
        "security & quality",
        "security and quality",
        "non-functional requirements",
        "three-phase delivery",
        "additional context",
        "platform roadmap",
        "similar implementations",
        "required python packages",
        "optional packages",
        "known limitations & mitigations",
        "known limitations and mitigations",
        "security model",
        "update required",
    }
)

_VERBS_TO_FIX = {
    "support": "supports",
    "store": "stores",
    "manage": "manages",
    "provide": "provides",
    "implement": "implements",
    "enable": "enables",
    "allow": "allows",
    "use": "uses",
    "create": "creates",
    "handle": "handles",
    "follow": "follows",
}


def _normalize_title_key(section_title: str) -> str:
    section_title_lower = section_title.lower()
    normalized = re.sub(r"\([^)]*\)", "", section_title_lower).strip()
    return re.sub(r"^\d+\.\s*", "", normalized).strip()


def _resolve_req_name(
    section_title: str,
    proposal: Any,
    requirement_index: int,
    format_proposal_title: Callable[[str], str],
) -> str:
    req_name = section_title.strip()
    req_name = re.sub(r"^(new|add|implement|support|provide|enable)\s+", "", req_name, flags=re.IGNORECASE)
    req_name = re.sub(r"\([^)]*\)", "", req_name, flags=re.IGNORECASE).strip()
    req_name = re.sub(r"^\d+\.\s*", "", req_name).strip()
    req_name = re.sub(r"\s+", " ", req_name)[:60].strip()
    if not req_name or len(req_name) < 8:
        req_name = format_proposal_title(proposal.title)
        req_name = re.sub(r"^(feat|fix|add|update|remove|refactor):\s*", "", req_name, flags=re.IGNORECASE)
        req_name = req_name.replace("[Change]", "").strip()
        if requirement_index > 0:
            req_name = f"{req_name} ({requirement_index + 1})"
    return req_name


def _derive_devops_device_code_phrase(title_lower: str, section_title: str) -> str | None:
    if "device code" not in title_lower:
        return None
    if "azure" in title_lower or "devops" in title_lower:
        return "use Azure DevOps device code authentication for sync operations with Azure DevOps"
    if "github" in title_lower:
        return "use GitHub device code authentication for sync operations with GitHub"
    return f"use device code authentication for {section_title.lower()} sync operations"


def _derive_devops_sync(title_lower: str, section_title: str) -> str:
    device = _derive_devops_device_code_phrase(title_lower, section_title)
    if device is not None:
        return device
    if "token" in title_lower or "storage" in title_lower or "management" in title_lower:
        return "use stored authentication tokens for DevOps sync operations when available"
    if "cli" in title_lower or "command" in title_lower or "integration" in title_lower:
        return "provide CLI authentication commands for DevOps sync operations"
    if "architectural" in title_lower or "decision" in title_lower:
        return "follow documented authentication architecture decisions for DevOps sync operations"
    return f"support {section_title.lower()} for DevOps sync operations"


def _derive_auth_management(title_lower: str, section_title: str) -> str:
    if "device code" in title_lower:
        if "azure" in title_lower or "devops" in title_lower:
            return "support Azure DevOps device code authentication using Entra ID"
        if "github" in title_lower:
            return "support GitHub device code authentication using RFC 8628 OAuth device authorization flow"
        return f"support device code authentication for {section_title.lower()}"
    if "token" in title_lower or "storage" in title_lower or "management" in title_lower:
        return "store and manage authentication tokens securely with appropriate file permissions"
    if "cli" in title_lower or "command" in title_lower:
        return "provide CLI commands for authentication operations"
    return f"support {section_title.lower()}"


def _derive_default(title_lower: str, section_title: str) -> str:
    if "device code" in title_lower:
        return f"support {section_title.lower()} authentication"
    if "token" in title_lower or "storage" in title_lower:
        return "store and manage authentication tokens securely"
    if "architectural" in title_lower or "decision" in title_lower:
        return "follow documented architecture decisions"
    return f"support {section_title.lower()}"


@require(lambda spec_id, section_title: isinstance(spec_id, str) and isinstance(section_title, str))
@ensure(lambda result: isinstance(result, str))
@beartype
def bridge_sync_derive_change_description(spec_id: str, section_title: str) -> str:
    title_lower = section_title.lower()
    if spec_id == "devops-sync":
        return _derive_devops_sync(title_lower, section_title)
    if spec_id == "auth-management":
        return _derive_auth_management(title_lower, section_title)
    return _derive_default(title_lower, section_title)


def _normalize_change_desc_sentence(change_desc: str) -> str:
    if not change_desc.endswith("."):
        change_desc = change_desc + "."
    if change_desc and change_desc[0].isupper():
        change_desc = change_desc[0].lower() + change_desc[1:]
    return change_desc


def _fix_then_response(then_response: str) -> str:
    words = then_response.split()
    if not words:
        return then_response
    first_word = words[0].rstrip(".,;:!?")
    if first_word.lower() in _VERBS_TO_FIX:
        words[0] = _VERBS_TO_FIX[first_word.lower()] + words[0][len(first_word) :]
    for i in range(1, len(words) - 1):
        if words[i].lower() == "and" and i + 1 < len(words):
            next_word = words[i + 1].rstrip(".,;:!?")
            if next_word.lower() in _VERBS_TO_FIX:
                words[i + 1] = _VERBS_TO_FIX[next_word.lower()] + words[i + 1][len(next_word) :]
    return " ".join(words)


def _append_single_requirement_block(
    spec_id: str,
    section_title: str,
    section_content: str | None,
    proposal: Any,
    requirement_index: int,
    requirement_lines: list[str],
    format_proposal_title: Callable[[str], str],
) -> None:
    """Append one requirement block from a section title + body."""
    title_lower = section_title.lower()
    req_name = _resolve_req_name(section_title, proposal, requirement_index, format_proposal_title)
    change_desc = bridge_sync_derive_change_description(spec_id, section_title)
    change_desc = _normalize_change_desc_sentence(change_desc)
    section_details = bridge_sync_extract_section_details(section_content)

    requirement_lines.append(f"### Requirement: {req_name}")
    requirement_lines.append("")
    requirement_lines.append(f"The system SHALL {change_desc}")
    requirement_lines.append("")

    scenario_name = (
        req_name.split(":")[0] if ":" in req_name else req_name.split()[0] if req_name.split() else "Implementation"
    )
    requirement_lines.append(f"#### Scenario: {scenario_name}")
    requirement_lines.append("")
    when_action = req_name.lower().replace("device code", "device code authentication")
    when_clause = f"a user requests {when_action}"
    if "architectural" in title_lower or "decision" in title_lower:
        when_clause = "the system performs authentication operations"
    requirement_lines.append(f"- **WHEN** {when_clause}")

    then_response = _fix_then_response(change_desc)
    requirement_lines.append(f"- **THEN** the system {then_response}")
    if section_details:
        for detail in section_details:
            normalized_detail = bridge_sync_normalize_detail_for_and(detail)
            if normalized_detail:
                requirement_lines.append(f"- **AND** {normalized_detail}")
    requirement_lines.append("")


def _try_append_subsection_fallback(
    proposal: Any,
    description: str,
    requirement_lines: list[str],
    format_proposal_title: Callable[[str], str],
) -> None:
    subsection_match = re.search(r"-\s*###\s*([^\n]+)\s*\n\s*-\s*([^\n]+)", description, re.MULTILINE)
    if not subsection_match:
        return
    subsection_title = subsection_match.group(1).strip()
    first_line = subsection_match.group(2).strip()
    if first_line.startswith("- "):
        first_line = first_line[2:].strip()
    if first_line.lower() == subsection_title.lower() or len(first_line) <= 10:
        return
    if "." in first_line:
        first_line = first_line.split(".")[0].strip() + "."
    if len(first_line) > 200:
        first_line = first_line[:200] + "..."

    req_name = format_proposal_title(proposal.title)
    req_name = re.sub(r"^(feat|fix|add|update|remove|refactor):\s*", "", req_name, flags=re.IGNORECASE)
    req_name = req_name.replace("[Change]", "").strip()

    requirement_lines.append(f"### Requirement: {req_name}")
    requirement_lines.append("")
    requirement_lines.append(f"The system SHALL {first_line}")
    requirement_lines.append("")
    requirement_lines.append(f"#### Scenario: {subsection_title}")
    requirement_lines.append("")
    requirement_lines.append("- **WHEN** the system processes the change")
    requirement_lines.append(f"- **THEN** {first_line.lower()}")
    requirement_lines.append("")


def _append_title_description_fallback(
    proposal: Any,
    description: str,
    rationale: str,
    requirement_lines: list[str],
    format_proposal_title: Callable[[str], str],
) -> None:
    req_name = format_proposal_title(proposal.title)
    req_name = re.sub(r"^(feat|fix|add|update|remove|refactor):\s*", "", req_name, flags=re.IGNORECASE)
    req_name = req_name.replace("[Change]", "").strip()
    first_sentence = (
        description.split(".")[0].strip()
        if description
        else rationale.split(".")[0].strip()
        if rationale
        else "implement the change"
    )
    first_sentence = re.sub(r"^[-#\s]+", "", first_sentence).strip()
    if len(first_sentence) > 200:
        first_sentence = first_sentence[:200] + "..."

    requirement_lines.append(f"### Requirement: {req_name}")
    requirement_lines.append("")
    requirement_lines.append(f"The system SHALL {first_sentence}")
    requirement_lines.append("")
    requirement_lines.append(f"#### Scenario: {req_name}")
    requirement_lines.append("")
    requirement_lines.append("- **WHEN** the change is applied")
    requirement_lines.append(f"- **THEN** {first_sentence.lower()}")
    requirement_lines.append("")


def _gather_requirement_blocks_from_description(
    description: str,
    proposal: Any,
    spec_id: str,
    format_proposal_title: Callable[[str], str],
) -> list[str]:
    requirement_lines: list[str] = []
    requirement_index = 0
    seen_sections: set[str] = set()

    formatted_sections = bridge_sync_parse_formatted_sections(description)
    if formatted_sections:
        for section in formatted_sections:
            section_title = section["title"]
            normalized_title = _normalize_title_key(section_title)
            if normalized_title in seen_sections or normalized_title in _SKIP_SECTION_TITLES:
                continue
            seen_sections.add(normalized_title)
            _append_single_requirement_block(
                spec_id,
                section_title,
                section.get("content"),
                proposal,
                requirement_index,
                requirement_lines,
                format_proposal_title,
            )
            requirement_index += 1
    else:
        change_patterns = re.finditer(
            r"(?i)(?:^|\n)(?:-\s*)?###\s*([^\n]+)\s*\n(.*?)(?=\n(?:-\s*)?###\s+|\n(?:-\s*)?##\s+|\Z)",
            description,
            re.MULTILINE | re.DOTALL,
        )
        for match in change_patterns:
            section_title = match.group(1).strip()
            section_content = match.group(2).strip()
            normalized_title = _normalize_title_key(section_title)
            if normalized_title in seen_sections or normalized_title in _SKIP_SECTION_TITLES:
                continue
            seen_sections.add(normalized_title)
            _append_single_requirement_block(
                spec_id,
                section_title,
                section_content,
                proposal,
                requirement_index,
                requirement_lines,
                format_proposal_title,
            )
            requirement_index += 1

    return requirement_lines


@require(lambda proposal, spec_id, format_proposal_title: isinstance(spec_id, str) and callable(format_proposal_title))
@ensure(lambda result: isinstance(result, str))
@beartype
def bridge_sync_extract_requirement_from_proposal(
    proposal: Any,
    spec_id: str,
    format_proposal_title: Callable[[str], str],
) -> str:
    """Extract requirement text from proposal content."""
    description = proposal.description or ""
    rationale = proposal.rationale or ""
    requirement_lines = _gather_requirement_blocks_from_description(
        description, proposal, spec_id, format_proposal_title
    )

    if not requirement_lines and description:
        _try_append_subsection_fallback(proposal, description, requirement_lines, format_proposal_title)

    if not requirement_lines and (description or rationale):
        _append_title_description_fallback(proposal, description, rationale, requirement_lines, format_proposal_title)

    return "\n".join(requirement_lines) if requirement_lines else ""
