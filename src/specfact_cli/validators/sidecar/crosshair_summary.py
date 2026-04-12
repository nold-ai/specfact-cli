"""
CrossHair summary parser for sidecar validation.

This module parses CrossHair output to extract summary statistics
(confirmed, not confirmed, violations counts).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure


def _summary_output_path_exists(result: Path) -> bool:
    return result.exists()


def _parse_counterexample_key_value(part: str) -> tuple[str, Any]:
    key, value = part.split("=", 1)
    key = key.strip()
    value = value.strip()
    try:
        if value.startswith('"') and value.endswith('"'):
            return key, value[1:-1]
        if value.lower() in ("true", "false"):
            return key, value.lower() == "true"
        if "." in value:
            return key, float(value)
        return key, int(value)
    except (ValueError, AttributeError):
        return key, value


def _collect_counterexample_violations(
    counterexamples: list[tuple[str, str]],
) -> list[dict[str, Any]]:
    violation_details: list[dict[str, Any]] = []
    for func_name, counterexample_str in counterexamples:
        counterexample_dict: dict[str, Any] = {}
        for part in counterexample_str.split(","):
            part = part.strip()
            if "=" not in part:
                continue
            k, v = _parse_counterexample_key_value(part)
            counterexample_dict[k] = v

        violation_details.append(
            {
                "function": func_name.strip(),
                "counterexample": counterexample_dict,
                "raw": f"{func_name}: Rejected (counterexample: {counterexample_str})",
            }
        )
    return violation_details


def _append_rejected_line_violation(
    line: str,
    function_name_pattern: re.Pattern[str],
    violation_details: list[dict[str, Any]],
) -> None:
    if any(v["function"] in line for v in violation_details):
        return
    match = function_name_pattern.match(line)
    if not match:
        return
    func_name = match.group(1).strip()
    if "/" in func_name or func_name.startswith("/"):
        return
    violation_details.append({"function": func_name, "counterexample": {}, "raw": line.strip()})


def _count_lines_by_status(
    lines: list[str],
    confirmed_pattern: re.Pattern[str],
    rejected_pattern: re.Pattern[str],
    unknown_pattern: re.Pattern[str],
    function_name_pattern: re.Pattern[str],
    violation_details: list[dict[str, Any]],
) -> tuple[int, int, int]:
    confirmed = 0
    not_confirmed = 0
    violations = 0
    for line in lines:
        if confirmed_pattern.search(line):
            confirmed += 1
            continue
        if rejected_pattern.search(line):
            violations += 1
            _append_rejected_line_violation(line, function_name_pattern, violation_details)
            continue
        if unknown_pattern.search(line):
            not_confirmed += 1
    return confirmed, not_confirmed, violations


def _apply_crosshair_fallback_heuristic(
    combined_output: str,
    function_name_pattern: re.Pattern[str],
    confirmed: int,
    not_confirmed: int,
    violations: int,
    violation_details: list[dict[str, Any]],
) -> tuple[int, int, int]:
    if confirmed != 0 or not_confirmed != 0 or violations != 0:
        return confirmed, not_confirmed, violations
    lower = combined_output.lower()
    if any(k in lower for k in ("error", "violation", "counterexample", "failed", "rejected")):
        violations = 1
        match = function_name_pattern.search(combined_output)
        if match:
            func_name = match.group(1).strip()
            if "/" not in func_name and not func_name.startswith("/"):
                violation_details.append(
                    {
                        "function": func_name,
                        "counterexample": {},
                        "raw": combined_output.strip()[:200],
                    }
                )
    elif combined_output.strip() and "not found" not in lower:
        not_confirmed = 1
    return confirmed, not_confirmed, violations


@beartype
@ensure(lambda result: isinstance(result, dict), "Must return dict")
@ensure(lambda result: "confirmed" in result, "Must include confirmed count")
@ensure(lambda result: "not_confirmed" in result, "Must include not_confirmed count")
@ensure(lambda result: "violations" in result, "Must include violations count")
def parse_crosshair_output(stdout: str, stderr: str) -> dict[str, Any]:
    """
    Parse CrossHair output to extract summary statistics and detailed violations.

    CrossHair output format:
    - By default, only reports "Rejected" (violations)
    - With --report_all, reports "Confirmed", "Rejected", and "Unknown"
    - Output format: "FunctionName: <status>" or "FunctionName: <status> <details>"
    - Counterexamples: "FunctionName: Rejected (counterexample: x=5, result=-5)"

    Args:
        stdout: CrossHair stdout output
        stderr: CrossHair stderr output

    Returns:
        Dictionary with summary statistics and detailed violations:
        - confirmed: int - Number of confirmed contracts
        - not_confirmed: int - Number of not confirmed (unknown) contracts
        - violations: int - Number of violations (rejected) contracts
        - total: int - Total number of contracts analyzed
        - violation_details: list[dict] - Detailed violation information with counterexamples
    """
    combined_output = stdout + "\n" + stderr

    confirmed_pattern = re.compile(r":\s*Confirmed", re.IGNORECASE)
    rejected_pattern = re.compile(r":\s*Rejected\b", re.IGNORECASE)
    unknown_pattern = re.compile(r":\s*(Unknown|Not confirmed)", re.IGNORECASE)
    counterexample_pattern = re.compile(
        r"^([^:]+):\s*Rejected\s*\(counterexample:\s*(.+?)\)", re.IGNORECASE | re.MULTILINE
    )
    function_name_pattern = re.compile(r"^([^:]+):", re.MULTILINE)

    violation_details = _collect_counterexample_violations(counterexample_pattern.findall(combined_output))

    confirmed, not_confirmed, violations = _count_lines_by_status(
        combined_output.split("\n"),
        confirmed_pattern,
        rejected_pattern,
        unknown_pattern,
        function_name_pattern,
        violation_details,
    )

    confirmed, not_confirmed, violations = _apply_crosshair_fallback_heuristic(
        combined_output,
        function_name_pattern,
        confirmed,
        not_confirmed,
        violations,
        violation_details,
    )

    total = confirmed + not_confirmed + violations

    result: dict[str, Any] = {
        "confirmed": confirmed,
        "not_confirmed": not_confirmed,
        "violations": violations,
        "total": total,
    }

    # Add violation details if any were found
    if violation_details:
        result["violation_details"] = violation_details

    return result


@beartype
@ensure(_summary_output_path_exists, "Summary file path must be valid")
def generate_summary_file(
    summary: dict[str, Any],
    reports_dir: Path,
    timestamp: str | None = None,
) -> Path:
    """
    Generate CrossHair summary JSON file.

    Args:
        summary: Summary statistics dictionary
        reports_dir: Directory to save summary file (will be created if it doesn't exist)
        timestamp: Optional timestamp for filename (defaults to current time)

    Returns:
        Path to generated summary file
    """
    from datetime import UTC, datetime

    if timestamp is None:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

    # Ensure reports directory exists (creates parent directories if needed)
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Create summary file path
    summary_file = reports_dir / f"crosshair-summary-{timestamp}.json"

    # Add metadata to summary
    summary_with_metadata = {
        "timestamp": timestamp,
        "summary": summary,
    }

    # Include violation details if present
    if "violation_details" in summary:
        summary_with_metadata["violation_details"] = summary["violation_details"]

    # Write summary file
    with summary_file.open("w") as f:
        json.dump(summary_with_metadata, f, indent=2)

    return summary_file


def _is_violation_function_displayable(func_name: str) -> bool:
    if "/" in func_name or func_name.startswith("/") or func_name == "unknown":
        return False
    return func_name.replace("_", "").replace(".", "").isalnum() or func_name.startswith("harness_")


def _preview_violation_function_names(violation_details: list[dict[str, Any]], head: int = 3) -> str | None:
    names: list[str] = []
    for v in violation_details[:head]:
        func_name = v.get("function", "unknown")
        if _is_violation_function_displayable(str(func_name)):
            names.append(str(func_name))
    if not names:
        return None
    if len(violation_details) > head:
        names.append(f"... ({len(violation_details) - head} more)")
    return f"({', '.join(names)})"


@beartype
@ensure(lambda result: isinstance(result, str), "Must return string")
def format_summary_line(summary: dict[str, Any]) -> str:
    """
    Format summary statistics as a single line for console display.

    Args:
        summary: Summary statistics dictionary (may include violation_details)

    Returns:
        Formatted summary line string
    """
    confirmed = summary.get("confirmed", 0)
    not_confirmed = summary.get("not_confirmed", 0)
    violations = summary.get("violations", 0)
    total = summary.get("total", 0)
    violation_details_raw = summary.get("violation_details", [])
    violation_details: list[dict[str, Any]] = [
        v for v in (violation_details_raw if isinstance(violation_details_raw, list) else []) if isinstance(v, dict)
    ]

    parts: list[str] = []
    if confirmed > 0:
        parts.append(f"{confirmed} confirmed")
    if not_confirmed > 0:
        parts.append(f"{not_confirmed} not confirmed")
    if violations > 0:
        parts.append(f"{violations} violations")
        if violation_details:
            preview = _preview_violation_function_names(violation_details)
            if preview:
                parts.append(preview)
    if total == 0:
        parts.append("no contracts analyzed")

    return f"CrossHair: {', '.join(parts)}" if parts else "CrossHair: no results"
