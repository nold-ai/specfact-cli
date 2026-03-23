"""Generate tasks.md content from ChangeProposal (split from bridge_sync for CC)."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from beartype import beartype
from icontract import ensure, require


def _section_task_line_from_code_block(stripped: str) -> str | None:
    if not stripped or stripped.startswith("#"):
        return None
    if stripped.startswith("specfact "):
        return f"Support `{stripped}` command"
    return stripped


def _section_task_line_from_bullet(stripped: str) -> str | None:
    content = stripped[2:].strip() if stripped.startswith("- ") else stripped
    content = re.sub(r"^\d+\.\s*", "", content).strip()
    if content.lower() in {"**commands:**", "commands:", "commands"}:
        return None
    return content or None


def _extract_section_tasks(text: str, marker_pattern: re.Pattern[str]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_code_block = False

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        marker_match = marker_pattern.match(stripped)
        if marker_match:
            if current:
                sections.append(current)
            current = {"title": marker_match.group(2).strip(), "tasks": []}
            in_code_block = False
            continue

        if current is None:
            continue

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            task_line = _section_task_line_from_code_block(stripped)
            if task_line:
                current["tasks"].append(task_line)
            continue

        if not stripped:
            continue

        task_line = _section_task_line_from_bullet(stripped)
        if task_line:
            current["tasks"].append(task_line)

    if current:
        sections.append(current)

    return sections


_ACCEPTANCE_SECTION_NAMES = {
    1: "Implementation",
    2: "Testing",
    3: "Documentation",
    4: "Security & Quality",
    5: "Code Quality",
}

_ACCEPTANCE_SECTION_MAP = {
    "testing": 2,
    "documentation": 3,
    "security": 4,
    "security & quality": 4,
    "code quality": 5,
}


def _acceptance_clean_subsection_title(stripped: str) -> str:
    subsection_title = stripped[5:].strip() if stripped.startswith("- ###") else stripped[3:].strip()
    subsection_title_clean = re.sub(r"\(.*?\)", "", subsection_title).strip()
    subsection_title_clean = re.sub(r"^#+\s*", "", subsection_title_clean).strip()
    return re.sub(r"^\d+\.\s*", "", subsection_title_clean).strip()


def _acceptance_apply_heading(
    lines: list[str],
    stripped: str,
    section_num: int,
    subsection_num: int,
    task_num: int,
    current_subsection: str | None,
    first_subsection: bool,
) -> tuple[int, int, int, str | None, bool]:
    subsection_title_clean = _acceptance_clean_subsection_title(stripped)
    subsection_lower = subsection_title_clean.lower()
    new_section_num = _ACCEPTANCE_SECTION_MAP.get(subsection_lower)

    if new_section_num and new_section_num != section_num:
        section_num = new_section_num
        subsection_num = 1
        task_num = 1
        current_section_name = _ACCEPTANCE_SECTION_NAMES.get(section_num, "Implementation")
        if not first_subsection:
            lines.append("")
        lines.append(f"## {section_num}. {current_section_name}")
        lines.append("")
        first_subsection = True

    if current_subsection is not None and not first_subsection:
        lines.append("")
        subsection_num += 1
        task_num = 1

    current_subsection = subsection_title_clean
    lines.append(f"### {section_num}.{subsection_num} {current_subsection}")
    lines.append("")
    task_num = 1
    first_subsection = False
    return section_num, subsection_num, task_num, current_subsection, first_subsection


def _acceptance_apply_checkbox(
    lines: list[str],
    stripped: str,
    section_num: int,
    subsection_num: int,
    task_num: int,
    current_subsection: str | None,
    first_subsection: bool,
) -> tuple[int, str | None, bool, bool]:
    tasks_found = False
    task_text = re.sub(r"^[-*]\s*\[[ x]\]\s*", "", stripped).strip()
    if not task_text:
        return task_num, current_subsection, first_subsection, tasks_found
    if current_subsection is None:
        current_subsection = "Tasks"
        lines.append(f"### {section_num}.{subsection_num} {current_subsection}")
        lines.append("")
        task_num = 1
        first_subsection = False
    lines.append(f"- [ ] {section_num}.{subsection_num}.{task_num} {task_text}")
    task_num += 1
    tasks_found = True
    return task_num, current_subsection, first_subsection, tasks_found


def _append_tasks_from_acceptance_criteria(
    lines: list[str],
    criteria_content: str,
) -> bool:
    section_num = 1
    subsection_num = 1
    task_num = 1
    current_subsection = None
    first_subsection = True
    tasks_found = False

    lines.append("## 1. Implementation")
    lines.append("")

    for line in criteria_content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("- ###") or (stripped.startswith("###") and not stripped.startswith("####")):
            section_num, subsection_num, task_num, current_subsection, first_subsection = _acceptance_apply_heading(
                lines, stripped, section_num, subsection_num, task_num, current_subsection, first_subsection
            )
        elif stripped.startswith(("- [ ]", "- [x]", "[ ]", "[x]")):
            task_num, current_subsection, first_subsection, found = _acceptance_apply_checkbox(
                lines, stripped, section_num, subsection_num, task_num, current_subsection, first_subsection
            )
            tasks_found = tasks_found or found

    return tasks_found


def _append_tasks_from_checkbox_list(lines: list[str], description: str) -> bool:
    task_items: list[str] = []
    for line in description.split("\n"):
        stripped = line.strip()
        if stripped.startswith(("- [ ]", "- [x]", "[ ]", "[x]")):
            task_text = re.sub(r"^[-*]\s*\[[ x]\]\s*", "", stripped).strip()
            if task_text:
                task_items.append(task_text)
    if not task_items:
        return False
    lines.append("## 1. Implementation")
    lines.append("")
    for idx, task in enumerate(task_items, start=1):
        lines.append(f"- [ ] 1.{idx} {task}")
    lines.append("")
    return True


def _append_tasks_from_what_changes_markers(
    lines: list[str],
    formatted_description: str,
    marker_pattern: re.Pattern[str],
) -> bool:
    sections = _extract_section_tasks(formatted_description, marker_pattern)
    if not sections:
        return False
    lines.append("## 1. Implementation")
    lines.append("")
    subsection_num = 1
    for section in sections:
        section_title = section.get("title", "").strip()
        if not section_title:
            continue
        section_title_clean = re.sub(r"\([^)]*\)", "", section_title).strip()
        if not section_title_clean:
            continue
        lines.append(f"### 1.{subsection_num} {section_title_clean}")
        lines.append("")
        task_num = 1
        tasks = section.get("tasks") or [f"Implement {section_title_clean.lower()}"]
        for task in tasks:
            task_text = str(task).strip()
            if not task_text:
                continue
            lines.append(f"- [ ] 1.{subsection_num}.{task_num} {task_text}")
            task_num += 1
        lines.append("")
        subsection_num += 1
    return True


def _append_placeholder_tasks(lines: list[str]) -> None:
    lines.append("## 1. Implementation")
    lines.append("")
    lines.append("- [ ] 1.1 Implement changes as described in proposal")
    lines.append("")
    lines.append("## 2. Testing")
    lines.append("")
    lines.append("- [ ] 2.1 Add unit tests")
    lines.append("- [ ] 2.2 Add integration tests")
    lines.append("")
    lines.append("## 3. Code Quality")
    lines.append("")
    lines.append("- [ ] 3.1 Run linting: `hatch run format`")
    lines.append("- [ ] 3.2 Run type checking: `hatch run type-check`")


def _description_has_checkbox_markers(description: str) -> bool:
    return "- [ ]" in description or "- [x]" in description or "[ ]" in description


def _formatted_description_for_markers(
    description: str,
    marker_pattern: re.Pattern[str],
    format_what_changes_section: Callable[[str], str],
    extract_what_changes_content: Callable[[str], str],
) -> str:
    if description and not marker_pattern.search(description):
        return format_what_changes_section(extract_what_changes_content(description))
    return description


@require(
    lambda proposal, format_proposal_title, format_what_changes_section, extract_what_changes_content: (
        callable(format_proposal_title)
        and callable(format_what_changes_section)
        and callable(extract_what_changes_content)
    )
)
@ensure(lambda result: isinstance(result, str))
@beartype
def bridge_sync_generate_tasks_from_proposal(
    proposal: Any,
    *,
    format_proposal_title: Callable[[str], str],
    format_what_changes_section: Callable[[str], str],
    extract_what_changes_content: Callable[[str], str],
) -> str:
    """Generate tasks.md content from proposal."""
    proposal_title: str = str(proposal.title) if proposal.title else ""
    lines: list[str] = ["# Tasks: " + format_proposal_title(proposal_title), ""]
    description: str = str(proposal.description) if proposal.description else ""
    tasks_found = False
    marker_pattern = re.compile(
        r"^-\s*\*\*(NEW|EXTEND|FIX|ADD|MODIFY|UPDATE|REMOVE|REFACTOR)\*\*:\s*(.+)$",
        re.IGNORECASE | re.MULTILINE,
    )

    acceptance_criteria_match = re.search(
        r"(?i)(?:-\s*)?##\s*Acceptance\s+Criteria\s*\n(.*?)(?=\n\s*(?:-\s*)?##|\Z)",
        description,
        re.DOTALL,
    )
    if acceptance_criteria_match:
        criteria_content = acceptance_criteria_match.group(1)
        tasks_found = _append_tasks_from_acceptance_criteria(lines, criteria_content)

    if not tasks_found and _description_has_checkbox_markers(description):
        tasks_found = _append_tasks_from_checkbox_list(lines, description)

    formatted_description = _formatted_description_for_markers(
        description, marker_pattern, format_what_changes_section, extract_what_changes_content
    )

    if not tasks_found and formatted_description and marker_pattern.search(formatted_description):
        tasks_found = _append_tasks_from_what_changes_markers(lines, formatted_description, marker_pattern)

    if not tasks_found:
        _append_placeholder_tasks(lines)

    return "\n".join(lines)
