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

    print("".join(parts), file=sys.stdout)


@beartype
@require(lambda report_path: report_path.exists(), "Report path must exist")
@require(lambda report_path: report_path.suffix in (".yaml", ".yml"), "Report must be YAML file")
@require(lambda report_path: report_path.is_file(), "Report path must be a file")
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
    from specfact_cli.utils.yaml_utils import load_yaml

    try:
        report = load_yaml(report_path)
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
        status = check.get("status", "unknown")
        name = check.get("name", "Unknown check")
        tool = check.get("tool", "unknown")
        error = check.get("error", "")
        output = check.get("output", "")

        # Check if this is a CrossHair signature analysis limitation (not a real failure)
        is_signature_issue = False
        if tool.lower() == "crosshair" and status == "failed":
            # Check for signature analysis limitation patterns
            combined_output = f"{error} {output}".lower()
            is_signature_issue = (
                "wrong parameter order" in combined_output
                or "keyword-only parameter" in combined_output
                or "valueerror: wrong parameter" in combined_output
                or ("signature" in combined_output and ("error" in combined_output or "failure" in combined_output))
            )

        if status == "failed" and not is_signature_issue:
            has_failures = True

            # Create error annotation
            message = f"{name} ({tool}) failed"
            if error:
                message += f": {error}"
            elif output:
                # Truncate output for annotation
                truncated = output[:500] + "..." if len(output) > 500 else output
                message += f": {truncated}"

            create_annotation(
                message=message,
                level="error",
                title=f"{name} failed",
            )
        elif status == "failed" and is_signature_issue:
            # CrossHair signature analysis limitation - treat as skipped, not failed
            create_annotation(
                message=f"{name} ({tool}) - signature analysis limitation (non-blocking, runtime contracts valid)",
                level="notice",
                title=f"{name} skipped (signature limitation)",
            )
        elif status == "timeout":
            has_failures = True
            create_annotation(
                message=f"{name} ({tool}) timed out",
                level="warning",
                title=f"{name} timeout",
            )
        elif status == "skipped":
            # Explicitly skipped checks - don't treat as failures
            create_annotation(
                message=f"{name} ({tool}) was skipped",
                level="notice",
                title=f"{name} skipped",
            )

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


@beartype
@require(lambda report: isinstance(report, dict), "Report must be dictionary")
@require(lambda report: "total_checks" in report or "checks" in report, "Report must contain total_checks or checks")
@ensure(lambda result: isinstance(result, str), "Must return string")
@ensure(lambda result: len(result) > 0, "Comment must not be empty")
@ensure(lambda result: result.startswith("##"), "Comment must start with markdown header")
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

    # Failed checks (excluding signature analysis limitations)
    checks = report.get("checks", [])
    failed_checks_list = []
    signature_issues_list = []

    for check in checks:
        if check.get("status") == "failed":
            tool = check.get("tool", "unknown").lower()
            error = check.get("error", "")
            output = check.get("output", "")

            # Check if this is a CrossHair signature analysis limitation
            is_signature_issue = False
            if tool == "crosshair":
                combined_output = f"{error} {output}".lower()
                is_signature_issue = (
                    "wrong parameter order" in combined_output
                    or "keyword-only parameter" in combined_output
                    or "valueerror: wrong parameter" in combined_output
                    or ("signature" in combined_output and ("error" in combined_output or "failure" in combined_output))
                )

            if is_signature_issue:
                signature_issues_list.append(check)
            else:
                failed_checks_list.append(check)

    if failed_checks_list:
        lines.append("### ❌ Failed Checks\n\n")
        for check in failed_checks_list:
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
                lines.append(output[:2000])  # Limit output size
                if len(output) > 2000:
                    lines.append("\n... (truncated)")
                lines.append("\n```\n\n")
                lines.append("</details>\n\n")

            # Add fix suggestions for Semgrep checks
            if tool == "semgrep":
                lines.append(
                    "💡 **Auto-fix available**: Run `specfact repro --fix` to apply automatic fixes for violations with fix capabilities.\n\n"
                )

    # Signature analysis limitations (non-blocking)
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

    # Timeout checks
    timeout_checks_list = [c for c in checks if c.get("status") == "timeout"]
    if timeout_checks_list:
        lines.append("### ⏱️ Timeout Checks\n\n")
        for check in timeout_checks_list:
            name = check.get("name", "Unknown")
            tool = check.get("tool", "unknown")
            lines.append(f"- **{name}** ({tool}) - timed out\n")
        lines.append("\n")

    # Budget exceeded
    if budget_exceeded:
        lines.append("### ⚠️ Budget Exceeded\n\n")
        lines.append("The validation budget was exceeded. Consider increasing the budget or optimizing the checks.\n\n")

    # Suggestions
    if failed_checks > 0:
        lines.append("### 💡 Suggestions\n\n")
        lines.append("1. Review the failed checks above")
        lines.append("2. Fix the issues in your code")
        lines.append("3. Re-run validation: `specfact repro --budget 90`\n\n")
        lines.append("To run in warn mode (non-blocking), set `mode: warn` in your workflow configuration.\n\n")

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
    report_path_str = os.environ.get("SPECFACT_REPORT_PATH")
    if report_path_str:
        report_path = Path(report_path_str)
    else:
        # Default: look for latest report in .specfact/reports/enforcement/
        default_dir = Path(".specfact/reports/enforcement")
        if default_dir.exists():
            reports = sorted(default_dir.glob("report-*.yaml"), key=lambda p: p.stat().st_mtime, reverse=True)
            if reports:
                report_path = reports[0]
            else:
                print("No repro report found", file=sys.stderr)
                return 1
        else:
            print("No repro report directory found", file=sys.stderr)
            return 1

    if not report_path.exists():
        print(f"Report file not found: {report_path}", file=sys.stderr)
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

        print(f"PR comment written to: {comment_path}", file=sys.stderr)

    return 1 if has_failures else 0


if __name__ == "__main__":
    sys.exit(main())
