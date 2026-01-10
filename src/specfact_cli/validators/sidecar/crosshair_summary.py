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


@beartype
@ensure(lambda result: isinstance(result, dict), "Must return dict")
@ensure(lambda result: "confirmed" in result, "Must include confirmed count")
@ensure(lambda result: "not_confirmed" in result, "Must include not_confirmed count")
@ensure(lambda result: "violations" in result, "Must include violations count")
def parse_crosshair_output(stdout: str, stderr: str) -> dict[str, Any]:
    """
    Parse CrossHair output to extract summary statistics.

    CrossHair output format:
    - By default, only reports "Rejected" (violations)
    - With --report_all, reports "Confirmed", "Rejected", and "Unknown"
    - Output format: "FunctionName: <status>" or "FunctionName: <status> <details>"

    Args:
        stdout: CrossHair stdout output
        stderr: CrossHair stderr output

    Returns:
        Dictionary with summary statistics:
        - confirmed: int - Number of confirmed contracts
        - not_confirmed: int - Number of not confirmed (unknown) contracts
        - violations: int - Number of violations (rejected) contracts
        - total: int - Total number of contracts analyzed
    """
    confirmed = 0
    not_confirmed = 0
    violations = 0

    # Combine stdout and stderr for parsing
    combined_output = stdout + "\n" + stderr

    # Pattern for CrossHair output lines
    # Examples:
    # "function_name: Confirmed"
    # "function_name: Rejected (counterexample: ...)"
    # "function_name: Unknown"
    # "function_name: <status>"
    confirmed_pattern = re.compile(r":\s*Confirmed\b", re.IGNORECASE)
    rejected_pattern = re.compile(r":\s*Rejected\b", re.IGNORECASE)
    unknown_pattern = re.compile(r":\s*Unknown\b", re.IGNORECASE)

    # Count by status
    lines = combined_output.split("\n")
    for line in lines:
        if confirmed_pattern.search(line):
            confirmed += 1
        elif rejected_pattern.search(line):
            violations += 1
        elif unknown_pattern.search(line):
            not_confirmed += 1

    # If no explicit status found but there's output, check for error patterns
    # CrossHair may report violations in different formats
    if confirmed == 0 and not_confirmed == 0 and violations == 0:
        # Check for error/violation indicators
        if any(
            keyword in combined_output.lower()
            for keyword in ["error", "violation", "counterexample", "failed", "rejected"]
        ):
            # Likely violations but not in standard format
            violations = 1
        elif combined_output.strip() and "not found" not in combined_output.lower():
            # Has output but no clear status - likely unknown/not confirmed
            not_confirmed = 1

    total = confirmed + not_confirmed + violations

    return {
        "confirmed": confirmed,
        "not_confirmed": not_confirmed,
        "violations": violations,
        "total": total,
    }


@beartype
@ensure(lambda result: result.exists() if result else True, "Summary file path must be valid")
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

    # Write summary file
    with summary_file.open("w") as f:
        json.dump(summary_with_metadata, f, indent=2)

    return summary_file


@beartype
@ensure(lambda result: isinstance(result, str), "Must return string")
def format_summary_line(summary: dict[str, Any]) -> str:
    """
    Format summary statistics as a single line for console display.

    Args:
        summary: Summary statistics dictionary

    Returns:
        Formatted summary line string
    """
    confirmed = summary.get("confirmed", 0)
    not_confirmed = summary.get("not_confirmed", 0)
    violations = summary.get("violations", 0)
    total = summary.get("total", 0)

    parts = []
    if confirmed > 0:
        parts.append(f"{confirmed} confirmed")
    if not_confirmed > 0:
        parts.append(f"{not_confirmed} not confirmed")
    if violations > 0:
        parts.append(f"{violations} violations")
    if total == 0:
        parts.append("no contracts analyzed")

    return f"CrossHair: {', '.join(parts)}" if parts else "CrossHair: no results"
