"""Format 'What Changes' bodies with OpenSpec NEW/EXTEND/MODIFY markers (split from bridge_sync for CC)."""

from __future__ import annotations

import re

from beartype import beartype
from icontract import ensure, require


_NEW_KW = ("new", "add", "introduce", "create", "implement", "support")
_EXT_KW = ("extend", "enhance", "improve", "expand", "additional")
_MOD_KW = ("modify", "update", "change", "refactor", "fix", "correct")


def _has_openspec_markers(description: str) -> bool:
    return bool(
        re.search(
            r"^-\s*\*\*(NEW|EXTEND|FIX|ADD|MODIFY|UPDATE|REMOVE|REFACTOR)\*\*:",
            description,
            re.MULTILINE | re.IGNORECASE,
        )
    )


def _infer_change_type_from_lookahead(lookahead_lower: str) -> str | None:
    if not (
        any(k in lookahead_lower for k in ("new command", "new feature", "add ", "introduce", "create"))
        and "extend" not in lookahead_lower
        and "modify" not in lookahead_lower
    ):
        return None
    return "NEW"


def _infer_change_type(section_lower: str, section_title: str, lookahead: str) -> str:
    """Match legacy ordering: keyword scan, then NEW overrides, then lookahead NEW."""
    change_type = "MODIFY"
    if any(k in section_lower for k in _NEW_KW):
        change_type = "NEW"
    elif any(k in section_lower for k in _EXT_KW):
        change_type = "EXTEND"
    elif any(k in section_lower for k in _MOD_KW):
        change_type = "MODIFY"
    if "new" in section_lower or section_title.startswith("New "):
        change_type = "NEW"
    la_type = _infer_change_type_from_lookahead(lookahead.lower())
    if la_type is not None:
        change_type = la_type
    return change_type


def _is_h3_heading(stripped: str) -> bool:
    return stripped.startswith("- ###") or (stripped.startswith("###") and not stripped.startswith("####"))


def _collect_subsection_lines(lines: list[str], start: int) -> tuple[list[str], int]:
    """Collect lines under an h3 until next h2/h3 or blank section break."""
    out: list[str] = []
    i = start
    while i < len(lines):
        next_line = lines[i]
        next_stripped = next_line.strip()
        if _is_h3_heading(next_stripped) or (next_stripped.startswith("##") and not next_stripped.startswith("###")):
            break
        if not out and not next_stripped:
            i += 1
            continue
        if next_stripped:
            content = next_stripped[2:].strip() if next_stripped.startswith("- ") else next_stripped
            if content:
                if content.startswith(("```", "**", "*")):
                    out.append(f"  {content}")
                else:
                    out.append(f"  - {content}")
        else:
            out.append("")
        i += 1
    return out, i


def _keyword_line_marker(line_lower: str, stripped: str) -> str | None:
    if any(k in line_lower for k in _NEW_KW):
        body = stripped[2:].strip() if stripped.startswith("- ") else stripped
        return f"- **NEW**: {body}"
    if any(k in line_lower for k in _EXT_KW):
        body = stripped[2:].strip() if stripped.startswith("- ") else stripped
        return f"- **EXTEND**: {body}"
    if any(k in line_lower for k in _MOD_KW):
        body = stripped[2:].strip() if stripped.startswith("- ") else stripped
        return f"- **MODIFY**: {body}"
    return None


def _format_plain_line(stripped: str) -> str:
    line_lower = stripped.lower()
    if re.search(
        r"\bnew\s+(command|feature|capability|functionality|system|module|component)",
        line_lower,
    ) or any(k in line_lower for k in _NEW_KW):
        return f"- **NEW**: {stripped}"
    if any(k in line_lower for k in _EXT_KW):
        return f"- **EXTEND**: {stripped}"
    if any(k in line_lower for k in _MOD_KW):
        return f"- **MODIFY**: {stripped}"
    return f"- {stripped}"


def _ensure_markers_on_first_content_line(result: str) -> str:
    if "**NEW**" in result or "**EXTEND**" in result or "**MODIFY**" in result:
        return result
    lines_list = result.split("\n")
    for idx, line in enumerate(lines_list):
        if not line.strip() or line.strip().startswith("#"):
            continue
        line_lower = line.lower()
        if any(k in line_lower for k in ("new", "add", "introduce", "create")):
            lines_list[idx] = f"- **NEW**: {line.strip().lstrip('- ')}"
        elif any(k in line_lower for k in ("extend", "enhance", "improve")):
            lines_list[idx] = f"- **EXTEND**: {line.strip().lstrip('- ')}"
        else:
            lines_list[idx] = f"- **MODIFY**: {line.strip().lstrip('- ')}"
        break
    return "\n".join(lines_list)


def _append_non_heading_what_change_line(formatted_lines: list[str], line: str, stripped: str) -> None:
    if stripped.startswith(("- [ ]", "- [x]", "-")):
        if any(marker in stripped for marker in ("**NEW**", "**EXTEND**", "**MODIFY**", "**FIX**")):
            formatted_lines.append(line)
            return
        line_lower = stripped.lower()
        marked = _keyword_line_marker(line_lower, stripped)
        formatted_lines.append(marked if marked is not None else line)
        return
    if stripped:
        formatted_lines.append(_format_plain_line(stripped))
    else:
        formatted_lines.append("")


@require(lambda description: isinstance(description, str))
@ensure(lambda result: isinstance(result, str))
@beartype
def bridge_sync_format_what_changes_section(description: str) -> str:
    """Format description with NEW/EXTEND/MODIFY markers per OpenSpec conventions."""
    if not description or not description.strip():
        return "No description provided."

    if _has_openspec_markers(description):
        return description.strip()

    lines = description.split("\n")
    formatted_lines: list[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if _is_h3_heading(stripped):
            section_title = stripped[5:].strip() if stripped.startswith("- ###") else stripped[3:].strip()
            section_lower = section_title.lower()
            lookahead = "\n".join(lines[i + 1 : min(i + 5, len(lines))]).lower()
            change_type = _infer_change_type(section_lower, section_title, lookahead)
            formatted_lines.append(f"- **{change_type}**: {section_title}")
            i += 1
            subsection_content, i = _collect_subsection_lines(lines, i)
            if subsection_content:
                formatted_lines.extend(subsection_content)
                formatted_lines.append("")
            continue

        _append_non_heading_what_change_line(formatted_lines, line, stripped)

        i += 1

    result = "\n".join(formatted_lines)
    return _ensure_markers_on_first_content_line(result)
