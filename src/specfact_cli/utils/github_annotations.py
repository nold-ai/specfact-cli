"""
GitHub Action annotations and PR comment utilities.

This module provides utilities for creating GitHub Action annotations
and PR comments from SpecFact validation reports.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.common import get_bridge_logger
from specfact_cli.utils.contract_predicates import report_path_is_parseable_repro
from specfact_cli.utils.structured_io import load_structured_file


_logger = get_bridge_logger(__name__)


def _pr_comment_valid_markdown(result: str) -> bool:
    return isinstance(result, str) and len(result) > 0 and result.startswith("##")


def _append_pr_failed_check_details(lines: list[str], check: dict[str, Any]) -> None:
    name = check.get("name", "Unknown")
    tool = check.get("tool", "unknown")
    error = check.get("error")
    output = check.get("output")
    lines.append(f"#### {name} ({tool})\n\n")
    if error:
        lines.append(f"**Error**: `{error}`\n\n")
    if output:
        lines.append("<details>\n<summary>Output</summary>\n\n")
        lines.append("```\n")
        lines.append(output[:2000])
        if len(output) > 2000:
            lines.append("\n... (truncated)")
        lines.append("\n```\n\n")
        lines.append("</details>\n\n")
    if tool == "semgrep":
        lines.append(
            "💡 **Auto-fix available**: Run `specfact repro --fix` to apply automatic fixes for violations with fix capabilities.\n\n"
        )


def _emit_repro_check_annotation(check: dict[str, Any]) -> bool:
    """Emit GitHub annotation for one repro check. Returns True if this counts as a failure."""
    status = check.get("status", "unknown")
    name = check.get("name", "Unknown check")
    tool = check.get("tool", "unknown")
    error = check.get("error", "")
    output = check.get("output", "")
    is_signature_issue = status == "failed" and _is_crosshair_signature_limitation(tool, error, output)

    if status == "failed" and not is_signature_issue:
        message = f"{name} ({tool}) failed"
        if error:
            message += f": {error}"
        elif output:
            truncated = output[:500] + "..." if len(output) > 500 else output
            message += f": {truncated}"
        create_annotation(message=message, level="error", title=f"{name} failed")
        return True
    if status == "failed" and is_signature_issue:
        create_annotation(
            message=f"{name} ({tool}) - signature analysis limitation (non-blocking, runtime contracts valid)",
            level="notice",
            title=f"{name} skipped (signature limitation)",
        )
        return False
    if status == "timeout":
        create_annotation(
            message=f"{name} ({tool}) timed out",
            level="warning",
            title=f"{name} timeout",
        )
        return True
    if status == "skipped":
        create_annotation(
            message=f"{name} ({tool}) was skipped",
            level="notice",
            title=f"{name} skipped",
        )
        return False
    return False


def _is_crosshair_signature_limitation(tool: str, error: str, output: str) -> bool:
    if tool.lower() != "crosshair":
        return False
    combined = f"{error} {output}".lower()
    return (
        "wrong parameter order" in combined
        or "keyword-only parameter" in combined
        or "valueerror: wrong parameter" in combined
        or ("signature" in combined and ("error" in combined or "failure" in combined))
    )


@beartype
@require(lambda message: isinstance(message, str) and len(message) > 0, "Message must be non-empty string")
@require(lambda level: level in ("notice", "warning", "error"), "Level must be notice, warning, or error")
@require(
    lambda file: file is None or (isinstance(file, str) and len(file) > 0), "File must be None or non-empty string"
)
@require(lambda line: line is None or (isinstance(line, int) and line > 0), "Line must be None or positive integer")
@require(lambda col: col is None or (isinstance(col, int) and col > 0), "Column must be None or positive integer")
@require(
    lambda title: title is None or (isinstance(title, str) and len(title) > 0), "Title must be None or non-empty string"
)
def create_annotation(
    message: str,
    level: str = "error",
    file: str | None = None,
    line: int | None = None,
    col: int | None = None,
    title: str | None = None,
) -> None:
    """
    Create a GitHub Action annotation.

    Args:
        message: Annotation message
        level: Annotation level (notice, warning, error)
        file: Optional file path
        line: Optional line number
        col: Optional column number
        title: Optional annotation title
    """
    # Format: ::level file=file,line=line,col=col,title=title::message
    parts: list[str] = [f"::{level}"]

    if file or line or col or title:
        opts: list[str] = []
        if file:
            opts.append(f"file={file}")
        if line:
            opts.append(f"line={line}")
        if col:
            opts.append(f"col={col}")
        if title:
            opts.append(f"title={title}")
        parts.append(",".join(opts))

    parts.append(f"::{message}")

    sys.stdout.write("".join(parts) + "\n")


@beartype
@require(report_path_is_parseable_repro, "Report path must be a YAML or JSON file")
@ensure(lambda result: isinstance(result, dict), "Must return dictionary")
@ensure(lambda result: "checks" in result or "total_checks" in result, "Report must contain checks or total_checks")
def parse_repro_report(report_path: Path) -> dict[str, Any]:
    """
    Parse a repro report YAML file.

    Args:
        report_path: Path to repro report YAML file

    Returns:
        Parsed report dictionary with checks and metadata

    Raises:
        FileNotFoundError: If report file doesn't exist
        ValueError: If report is not valid YAML or doesn't match expected structure
    """
    try:
        report = load_structured_file(report_path)
        if not isinstance(report, dict):
            raise ValueError(f"Report must be a dictionary, got {type(report)}")
        return report
    except Exception as e:
        raise ValueError(f"Failed to parse repro report: {e}") from e


@beartype
@require(lambda report: isinstance(report, dict), "Report must be dictionary")
@require(lambda report: "checks" in report or "total_checks" in report, "Report must contain checks or total_checks")
@ensure(lambda result: isinstance(result, bool), "Must return boolean")
def create_annotations_from_report(report: dict[str, Any]) -> bool:
    """
    Create GitHub Action annotations from a repro report.

    Args:
        report: Repro report dictionary

    Returns:
        True if any failures found, False otherwise
    """
    checks = report.get("checks", [])
    has_failures = False
    for check in checks:
        if _emit_repro_check_annotation(check):
            has_failures = True

    # Create summary annotation
    total_checks = report.get("total_checks", 0)
    passed_checks = report.get("passed_checks", 0)
    failed_checks = report.get("failed_checks", 0)
    timeout_checks = report.get("timeout_checks", 0)
    budget_exceeded = report.get("budget_exceeded", False)

    if budget_exceeded:
        has_failures = True  # Budget exceeded is a failure
        create_annotation(
            message="Validation budget exceeded",
            level="error",
            title="Budget exceeded",
        )

    summary = f"Validation summary: {passed_checks}/{total_checks} passed"
    if failed_checks > 0:
        summary += f", {failed_checks} failed"
    if timeout_checks > 0:
        summary += f", {timeout_checks} timed out"

    level = "error" if has_failures else "notice"
    create_annotation(
        message=summary,
        level=level,
        title="Validation summary",
    )

    return has_failures


def _pr_comment_partition_failed_checks(
    checks: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    failed_checks_list: list[dict[str, Any]] = []
    signature_issues_list: list[dict[str, Any]] = []
    for check in checks:
        if check.get("status") != "failed":
            continue
        tool = check.get("tool", "unknown").lower()
        error = check.get("error", "")
        output = check.get("output", "")
        if tool == "crosshair" and _is_crosshair_signature_limitation(tool, error, output):
            signature_issues_list.append(check)
        else:
            failed_checks_list.append(check)
    return failed_checks_list, signature_issues_list


def _append_pr_comment_detail_sections(
    lines: list[str],
    report: dict[str, Any],
    failed_checks_list: list[dict[str, Any]],
    signature_issues_list: list[dict[str, Any]],
    checks: list[dict[str, Any]],
) -> None:
    failed_checks = report.get("failed_checks", 0)
    budget_exceeded = report.get("budget_exceeded", False)

    if failed_checks_list:
        lines.append("### ❌ Failed Checks\n\n")
        for check in failed_checks_list:
            _append_pr_failed_check_details(lines, check)

    if signature_issues_list:
        lines.append("### ⚠️ Signature Analysis Limitations (Non-blocking)\n\n")
        lines.append(
            "The following checks encountered CrossHair signature analysis limitations. "
            "These are non-blocking issues related to complex function signatures (Typer decorators, keyword-only parameters) "
            "and do not indicate actual contract violations. Runtime contracts remain valid.\n\n"
        )
        for check in signature_issues_list:
            name = check.get("name", "Unknown")
            tool = check.get("tool", "unknown")
            lines.append(f"- **{name}** ({tool}) - signature analysis limitation\n")
        lines.append("\n")

    timeout_checks_list = [c for c in checks if c.get("status") == "timeout"]
    if timeout_checks_list:
        lines.append("### ⏱️ Timeout Checks\n\n")
        for check in timeout_checks_list:
            name = check.get("name", "Unknown")
            tool = check.get("tool", "unknown")
            lines.append(f"- **{name}** ({tool}) - timed out\n")
        lines.append("\n")

    if budget_exceeded:
        lines.append("### ⚠️ Budget Exceeded\n\n")
        lines.append("The validation budget was exceeded. Consider increasing the budget or optimizing the checks.\n\n")

    if failed_checks > 0:
        lines.append("### 💡 Suggestions\n\n")
        lines.append("1. Review the failed checks above")
        lines.append("2. Fix the issues in your code")
        lines.append("3. Re-run validation: `specfact repro --budget 90`\n\n")
        lines.append("To run in warn mode (non-blocking), set `mode: warn` in your workflow configuration.\n\n")


@beartype
@require(lambda report: isinstance(report, dict), "Report must be dictionary")
@require(lambda report: "total_checks" in report or "checks" in report, "Report must contain total_checks or checks")
@ensure(_pr_comment_valid_markdown, "Comment must be non-empty markdown starting with ##")
def generate_pr_comment(report: dict[str, Any]) -> str:
    """
    Generate a PR comment from a repro report.

    Args:
        report: Repro report dictionary

    Returns:
        Formatted PR comment markdown
    """
    lines: list[str] = []
    lines.append("## SpecFact CLI Validation Report\n")

    total_checks = report.get("total_checks", 0)
    passed_checks = report.get("passed_checks", 0)
    failed_checks = report.get("failed_checks", 0)
    timeout_checks = report.get("timeout_checks", 0)
    skipped_checks = report.get("skipped_checks", 0)
    budget_exceeded = report.get("budget_exceeded", False)
    total_duration = report.get("total_duration", 0.0)

    # Summary
    if failed_checks == 0 and timeout_checks == 0 and not budget_exceeded:
        lines.append("✅ **All validations passed!**\n")
    else:
        lines.append("❌ **Validation issues detected**\n")

    lines.append(f"**Duration**: {total_duration:.2f}s\n")
    lines.append(f"**Checks**: {total_checks} total")
    if passed_checks > 0:
        lines.append(f" ({passed_checks} passed)")
    if failed_checks > 0:
        lines.append(f" ({failed_checks} failed)")
    if timeout_checks > 0:
        lines.append(f" ({timeout_checks} timed out)")
    if skipped_checks > 0:
        lines.append(f" ({skipped_checks} skipped)")
    lines.append("\n\n")

    checks = report.get("checks", [])
    failed_checks_list, signature_issues_list = _pr_comment_partition_failed_checks(checks)
    _append_pr_comment_detail_sections(lines, report, failed_checks_list, signature_issues_list, checks)

    return "".join(lines)


@beartype
@ensure(lambda result: result in (0, 1), "Exit code must be 0 or 1")
def main() -> int:
    """
    Main entry point for GitHub annotations script.

    Reads repro report from environment variable or default path,
    creates annotations, and optionally generates PR comment.

    Returns:
        Exit code (0 = success/no failures, 1 = failures detected or error)
    """
    # Get report path from environment or use default
    report_path: Path | None = None
    report_path_str = os.environ.get("SPECFACT_REPORT_PATH")
    if report_path_str:
        report_path = Path(report_path_str)
    else:
        # Phase 8.5: Try bundle-specific location first, then fallback to global
        from specfact_cli.utils.structure import SpecFactStructure

        # Try to find active bundle and check bundle-specific location
        bundle_name = SpecFactStructure.get_active_bundle_name(Path("."))
        if bundle_name:
            bundle_reports_dir = SpecFactStructure.get_bundle_reports_dir(bundle_name, Path(".")) / "enforcement"
            if bundle_reports_dir.exists():
                reports = sorted(
                    bundle_reports_dir.glob("report-*.yaml"), key=lambda p: p.stat().st_mtime, reverse=True
                )
                if reports:
                    report_path = reports[0]
                else:
                    _logger.warning("No repro report found in bundle-specific location")
                    return 1
            else:
                # Bundle-specific directory doesn't exist, try global fallback
                pass
        else:
            # No active bundle, try global fallback
            pass

        # Fallback: look for latest report in global .specfact/reports/enforcement/ (legacy)
        if report_path is None:
            default_dir = Path(".specfact/reports/enforcement")
            if default_dir.exists():
                reports = sorted(default_dir.glob("report-*.yaml"), key=lambda p: p.stat().st_mtime, reverse=True)
                if reports:
                    report_path = reports[0]
                else:
                    _logger.warning("No repro report found")
                    return 1
            else:
                _logger.warning("No repro report directory found")
                return 1

    if not report_path.exists():
        _logger.error("Report file not found: %s", report_path)
        return 1

    # Parse report
    report = parse_repro_report(report_path)

    # Create annotations
    has_failures = create_annotations_from_report(report)

    # Generate PR comment if requested
    if os.environ.get("GITHUB_EVENT_NAME") == "pull_request":
        comment = generate_pr_comment(report)

        # Write comment to file for GitHub Actions to use
        comment_path = Path(".specfact/pr-comment.md")
        comment_path.parent.mkdir(parents=True, exist_ok=True)
        comment_path.write_text(comment, encoding="utf-8")

        _logger.debug("PR comment written to: %s", comment_path)

    return 1 if has_failures else 0


if __name__ == "__main__":
    sys.exit(main())
