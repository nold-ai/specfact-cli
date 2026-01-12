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
    confirmed = 0
    not_confirmed = 0
    violations = 0
    violation_details: list[dict[str, Any]] = []

    # Combine stdout and stderr for parsing
    combined_output = stdout + "\n" + stderr

    # Pattern for CrossHair output lines
    # Examples:
    # "function_name: Confirmed" or "function_name: Confirmed over all paths"
    # "function_name: Rejected (counterexample: ...)"
    # "function_name: Unknown" or "function_name: Not confirmed"
    # "function_name: <status>"
    confirmed_pattern = re.compile(r":\s*Confirmed", re.IGNORECASE)
    rejected_pattern = re.compile(r":\s*Rejected\b", re.IGNORECASE)
    unknown_pattern = re.compile(r":\s*(Unknown|Not confirmed)", re.IGNORECASE)

    # Pattern for extracting function name and counterexample
    # Format: "function_name: Rejected (counterexample: x=5, result=-5)"
    counterexample_pattern = re.compile(
        r"^([^:]+):\s*Rejected\s*\(counterexample:\s*(.+?)\)", re.IGNORECASE | re.MULTILINE
    )

    # Pattern for extracting function name from status lines
    function_name_pattern = re.compile(r"^([^:]+):", re.MULTILINE)

    # Extract counterexamples first
    counterexamples = counterexample_pattern.findall(combined_output)
    for func_name, counterexample_str in counterexamples:
        # Parse counterexample string (e.g., "x=5, result=-5")
        counterexample_dict: dict[str, Any] = {}
        for part in counterexample_str.split(","):
            part = part.strip()
            if "=" in part:
                key, value = part.split("=", 1)
                key = key.strip()
                value = value.strip()
                # Try to parse value as appropriate type
                try:
                    if value.startswith('"') and value.endswith('"'):
                        counterexample_dict[key] = value[1:-1]  # String
                    elif value.lower() in ("true", "false"):
                        counterexample_dict[key] = value.lower() == "true"
                    elif "." in value:
                        counterexample_dict[key] = float(value)
                    else:
                        counterexample_dict[key] = int(value)
                except (ValueError, AttributeError):
                    counterexample_dict[key] = value  # Keep as string if parsing fails

        violation_details.append(
            {
                "function": func_name.strip(),
                "counterexample": counterexample_dict,
                "raw": f"{func_name}: Rejected (counterexample: {counterexample_str})",
            }
        )

    # Count by status
    lines = combined_output.split("\n")
    for line in lines:
        if confirmed_pattern.search(line):
            confirmed += 1
        elif rejected_pattern.search(line):
            violations += 1
            # If we haven't captured this violation yet, try to extract function name
            if not any(v["function"] in line for v in violation_details):
                match = function_name_pattern.match(line)
                if match:
                    func_name = match.group(1).strip()
                    # Filter out paths - only keep valid function names
                    # Skip if it looks like a path (contains / or starts with /)
                    if "/" not in func_name and not func_name.startswith("/"):
                        violation_details.append(
                            {
                                "function": func_name,
                                "counterexample": {},
                                "raw": line.strip(),
                            }
                        )
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
            # Try to extract function name from error
            match = function_name_pattern.search(combined_output)
            if match:
                func_name = match.group(1).strip()
                # Filter out paths - only keep valid function names
                # Skip if it looks like a path (contains / or starts with /)
                if "/" not in func_name and not func_name.startswith("/"):
                    violation_details.append(
                        {
                            "function": func_name,
                            "counterexample": {},
                            "raw": combined_output.strip()[:200],  # First 200 chars
                        }
                    )
        elif combined_output.strip() and "not found" not in combined_output.lower():
            # Has output but no clear status - likely unknown/not confirmed
            not_confirmed = 1

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
    from datetime import datetime

    if timestamp is None:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

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
    violation_details = summary.get("violation_details", [])

    parts = []
    if confirmed > 0:
        parts.append(f"{confirmed} confirmed")
    if not_confirmed > 0:
        parts.append(f"{not_confirmed} not confirmed")
    if violations > 0:
        parts.append(f"{violations} violations")
        # Add violation details if available
        if violation_details:
            # Filter out paths and invalid function names (only keep valid Python identifiers)
            violation_funcs = []
            for v in violation_details[:3]:
                func_name = v.get("function", "unknown")
                # Skip if it looks like a path (contains / or starts with /)
                # Only include if it looks like a valid function name (alphanumeric + underscore)
                if (
                    "/" not in func_name
                    and not func_name.startswith("/")
                    and func_name != "unknown"
                    and (func_name.replace("_", "").replace(".", "").isalnum() or func_name.startswith("harness_"))
                ):
                    violation_funcs.append(func_name)

            if violation_funcs:
                if len(violation_details) > 3:
                    violation_funcs.append(f"... ({len(violation_details) - 3} more)")
                parts.append(f"({', '.join(violation_funcs)})")
    if total == 0:
        parts.append("no contracts analyzed")

    return f"CrossHair: {', '.join(parts)}" if parts else "CrossHair: no results"
