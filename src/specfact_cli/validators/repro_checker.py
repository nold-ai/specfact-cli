"""
Reproducibility checker - Runs various validation tools and aggregates results.

This module provides functionality to run linting, type checking, contract
exploration, and test suites with time budgets and result aggregation.

CrossHair: skip (known signature synthesis limitation on complex pathlib/type signatures)
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require
from rich.console import Console


console = Console()


class CheckStatus(Enum):
    """Status of a validation check."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@beartype
@require(lambda text: isinstance(text, str), "Text must be string")
@ensure(lambda result: isinstance(result, str), "Must return string")
def _strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def _append_unique_pythonpath(pythonpath_roots: list[str], root: Path) -> None:
    s = str(root)
    if s not in pythonpath_roots:
        pythonpath_roots.append(s)


def _module_roots_for_path(repo_path: Path, file_path: Path, src_root: Path, lib_root: Path) -> tuple[Path, Path]:
    if file_path.is_relative_to(src_root):
        return src_root, src_root
    if file_path.is_relative_to(lib_root):
        return lib_root, lib_root
    r = repo_path.resolve()
    return r, r


def _crosshair_dir_append_py(module_root: Path, py_file: Path, expanded: list[str]) -> bool:
    """Append module for ``py_file``; return True if ``__main__.py`` was skipped."""
    if py_file.name == "__main__.py":
        return True
    module_name = _module_name_from_path(module_root, py_file)
    if module_name:
        expanded.append(module_name)
    return False


def _expand_crosshair_dir_target(
    repo_path: Path,
    target_root: Path,
    src_root: Path,
    lib_root: Path,
    expanded: list[str],
    pythonpath_roots: list[str],
) -> bool:
    """Expand a directory target; return whether any __main__.py was skipped."""
    tr = target_root.resolve()
    if tr in (src_root, lib_root):
        module_root = tr
        pythonpath_root = tr
    else:
        r = repo_path.resolve()
        module_root = r
        pythonpath_root = r
    _append_unique_pythonpath(pythonpath_roots, pythonpath_root)
    excluded_main = False
    for py_file in tr.rglob("*.py"):
        if _crosshair_dir_append_py(module_root, py_file, expanded):
            excluded_main = True
    return excluded_main


def _expand_crosshair_file_target(
    repo_path: Path,
    target_path: Path,
    src_root: Path,
    lib_root: Path,
    expanded: list[str],
    pythonpath_roots: list[str],
) -> bool:
    """Expand a single file target; return whether __main__.py was skipped."""
    if target_path.name == "__main__.py":
        return True
    if target_path.suffix != ".py":
        return False
    file_path = target_path.resolve()
    module_root, pythonpath_root = _module_roots_for_path(repo_path, file_path, src_root, lib_root)
    _append_unique_pythonpath(pythonpath_roots, pythonpath_root)
    module_name = _module_name_from_path(module_root, file_path)
    if module_name:
        expanded.append(module_name)
    return False


def _expand_one_crosshair_target(
    repo_path: Path,
    target: str,
    src_root: Path,
    lib_root: Path,
    expanded: list[str],
    pythonpath_roots: list[str],
) -> bool:
    """Process one target string; return True if any ``__main__.py`` was skipped."""
    target_path = repo_path / target
    if not target_path.exists():
        return False
    if target_path.is_dir():
        return _expand_crosshair_dir_target(repo_path, target_path, src_root, lib_root, expanded, pythonpath_roots)
    return _expand_crosshair_file_target(repo_path, target_path, src_root, lib_root, expanded, pythonpath_roots)


@beartype
@require(lambda repo_path: isinstance(repo_path, Path), "repo_path must be Path")
@require(lambda targets: isinstance(targets, list), "targets must be list")
@ensure(lambda result: isinstance(result, tuple) and len(result) == 3, "Must return (list, bool, list)")
@ensure(
    lambda result: isinstance(result[0], list) and isinstance(result[1], bool) and isinstance(result[2], list),
    "Must return (list, bool, list)",
)
def _expand_crosshair_targets(repo_path: Path, targets: list[str]) -> tuple[list[str], bool, list[str]]:
    """
    Expand directory targets into module names and PYTHONPATH roots, excluding __main__.py.
    """
    expanded: list[str] = []
    excluded_main = False
    pythonpath_roots: list[str] = []
    src_root = (repo_path / "src").resolve()
    lib_root = (repo_path / "lib").resolve()

    for target in targets:
        if _expand_one_crosshair_target(repo_path, target, src_root, lib_root, expanded, pythonpath_roots):
            excluded_main = True

    expanded = sorted(set(expanded))
    return expanded, excluded_main, pythonpath_roots


@beartype
@require(lambda root: isinstance(root, Path), "root must be Path")
@require(lambda file_path: isinstance(file_path, Path), "file_path must be Path")
@ensure(lambda result: result is None or isinstance(result, str), "Must return str or None")
def _module_name_from_path(root: Path, file_path: Path) -> str | None:
    """Convert a file path to a module name relative to the root."""
    try:
        rel_path = file_path.relative_to(root)
    except ValueError:
        return None
    parts = list(rel_path.parts)
    if not parts:
        return None
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1].removesuffix(".py")
    if not parts or any(part == "" for part in parts):
        return None
    return ".".join(parts)


@beartype
@require(lambda pythonpath_roots: isinstance(pythonpath_roots, list), "pythonpath_roots must be list")
@ensure(lambda result: result is None or isinstance(result, dict), "Must return dict or None")
def _build_crosshair_env(pythonpath_roots: list[str]) -> dict[str, str] | None:
    """Build environment with PYTHONPATH for CrossHair module imports."""
    if not pythonpath_roots:
        return None
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    combined = os.pathsep.join(pythonpath_roots + ([existing] if existing else []))
    env["PYTHONPATH"] = combined
    return env


@beartype
@require(lambda repo_path: isinstance(repo_path, Path), "repo_path must be Path")
@ensure(lambda result: isinstance(result, tuple) and len(result) == 2, "Must return (list, list)")
def _find_crosshair_property_targets(repo_path: Path) -> tuple[list[str], list[str]]:
    """
    Find explicit CrossHair property test modules to narrow analysis scope.

    Returns:
        (targets, pythonpath_roots)
    """
    marker_re = re.compile(r"(?mi)^\s*(?:#\s*)?CrossHair property(?:-based)? test(?:s)?\b")
    skip_re = re.compile(r"(?mi)^\s*(?:#\s*)?CrossHair:\s*(?:skip|ignore)\b")
    targets: list[str] = []
    pythonpath_roots: list[str] = []

    src_root = (repo_path / "src").resolve()
    lib_root = (repo_path / "lib").resolve()
    search_roots = [src_root, repo_path / "tools"]

    for root in search_roots:
        if not root.exists():
            continue
        for py_file in root.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
            except OSError:
                continue
            if not marker_re.search(content):
                continue
            if skip_re.search(content):
                continue
            file_path = py_file.resolve()
            if file_path.is_relative_to(src_root):
                module_root = src_root
                pythonpath_root = src_root
            elif file_path.is_relative_to(lib_root):
                module_root = lib_root
                pythonpath_root = lib_root
            else:
                module_root = repo_path.resolve()
                pythonpath_root = repo_path.resolve()
            pythonpath_root_str = str(pythonpath_root)
            if pythonpath_root_str not in pythonpath_roots:
                pythonpath_roots.append(pythonpath_root_str)
            module_name = _module_name_from_path(module_root, file_path)
            if module_name:
                targets.append(module_name)

    targets = sorted(set(targets))
    return targets, pythonpath_roots


@beartype
@require(lambda output: isinstance(output, str), "Output must be string")
@ensure(lambda result: isinstance(result, dict), "Must return dictionary")
@ensure(
    lambda result: "violations" in result and "total_violations" in result,
    "Must include violations and total_violations",
)
def _extract_ruff_findings(output: str) -> dict[str, Any]:
    """Extract structured findings from ruff output."""
    findings: dict[str, Any] = {
        "violations": [],
        "total_violations": 0,
        "files_checked": 0,
    }

    # Strip ANSI codes
    clean_output = _strip_ansi_codes(output)

    # Parse ruff output format:
    # Format 1: "W293 [*] Blank line contains whitespace\n--> src/file.py:240:1"
    # Format 2: "src/file.py:240:1: W293 Blank line contains whitespace"
    lines = clean_output.split("\n")
    i = 0
    while i < len(lines):
        line_stripped = lines[i].strip()
        if not line_stripped:
            i += 1
            continue

        # Skip help lines and code block markers
        if line_stripped.startswith(("help:", "|", "    |")):
            i += 1
            continue

        # Try format 1: "W293 [*] message" followed by "--> file:line:col"
        code_match = re.match(r"^([A-Z]\d+)\s+\[[^\]]+\]\s+(.+)$", line_stripped)
        if code_match:
            code = code_match.group(1)
            message = code_match.group(2)
            # Look for location line: "--> file:line:col"
            if i + 1 < len(lines):
                location_line = lines[i + 1].strip()
                location_match = re.match(r"-->\s+([^:]+):(\d+):(\d+)", location_line)
                if location_match:
                    file_path = location_match.group(1)
                    line_num = int(location_match.group(2))
                    col_num = int(location_match.group(3))
                    findings["violations"].append(
                        {
                            "file": file_path,
                            "line": line_num,
                            "column": col_num,
                            "code": code,
                            "message": message,
                        }
                    )
                    i += 2  # Skip both lines
                    continue

        # Try format 2: "file:line:col: code message"
        pattern = r"^([^:]+):(\d+):(\d+):\s+([A-Z]\d+)\s+(.+)$"
        match = re.match(pattern, line_stripped)
        if match:
            file_path, line_num, col_num, code, message = match.groups()
            findings["violations"].append(
                {
                    "file": file_path,
                    "line": int(line_num),
                    "column": int(col_num),
                    "code": code,
                    "message": message,
                }
            )

        i += 1

    # Set total_violations from list length
    findings["total_violations"] = len(findings["violations"])

    # Extract files checked count
    files_match = re.search(r"(\d+)\s+files?\s+checked", clean_output, re.IGNORECASE)
    if files_match:
        findings["files_checked"] = int(files_match.group(1))

    return findings


@beartype
@require(lambda output: isinstance(output, str), "Output must be string")
@require(lambda error: isinstance(error, str), "Error must be string")
@ensure(lambda result: isinstance(result, dict), "Must return dictionary")
@ensure(lambda result: "total_findings" in result, "Must include total_findings")
def _extract_semgrep_findings(output: str, error: str) -> dict[str, Any]:
    """Extract structured findings from semgrep output."""
    findings: dict[str, Any] = {
        "findings": [],
        "total_findings": 0,
        "rules_run": 0,
        "targets_scanned": 0,
    }

    # Combine output and error (semgrep uses stderr for status)
    combined = _strip_ansi_codes((output + "\n" + error).strip())

    # Extract findings count
    findings_match = re.search(r"Findings:\s*(\d+)", combined, re.IGNORECASE)
    if findings_match:
        findings["total_findings"] = int(findings_match.group(1))

    # Extract rules run
    rules_match = re.search(r"Rules\s+run:\s*(\d+)", combined, re.IGNORECASE)
    if rules_match:
        findings["rules_run"] = int(rules_match.group(1))

    # Extract targets scanned
    targets_match = re.search(r"Targets\s+scanned:\s*(\d+)", combined, re.IGNORECASE)
    if targets_match:
        findings["targets_scanned"] = int(targets_match.group(1))

    return findings


@beartype
@require(lambda output: isinstance(output, str), "Output must be string")
@ensure(lambda result: isinstance(result, dict), "Must return dictionary")
@ensure(lambda result: "errors" in result and "warnings" in result, "Must include errors and warnings")
def _extract_basedpyright_findings(output: str) -> dict[str, Any]:
    """Extract structured findings from basedpyright output."""
    findings: dict[str, Any] = {
        "errors": [],
        "warnings": [],
        "total_errors": 0,
        "total_warnings": 0,
    }

    # Strip ANSI codes
    clean_output = _strip_ansi_codes(output)

    # Parse basedpyright output in common formats:
    # 1) path:line:col: error|warning: message
    # 2) "  path:line:col - error|warning: message" (pretty output)
    patterns = [
        r"^([^:]+):(\d+):(\d+):\s+(error|warning):\s+(.+)$",
        r"^\s*([^:]+):(\d+):(\d+)\s+-\s+(error|warning):\s+(.+)$",
    ]
    for line in clean_output.split("\n"):
        line_stripped = line.strip()
        if not line_stripped:
            continue
        match = None
        for pattern in patterns:
            match = re.match(pattern, line_stripped)
            if match:
                break
        if match:
            file_path, line_num, col_num, level, message = match.groups()
            finding = {
                "file": file_path,
                "line": int(line_num),
                "column": int(col_num),
                "message": message,
            }
            if level == "error":
                findings["errors"].append(finding)
                findings["total_errors"] += 1
            else:
                findings["warnings"].append(finding)
                findings["total_warnings"] += 1

    # Fallback to summary line counts if detailed lines were not parseable.
    if findings["total_errors"] == 0 and findings["total_warnings"] == 0:
        summary_match = re.search(r"(\d+)\s+errors?,\s+(\d+)\s+warnings?", clean_output, re.IGNORECASE)
        if summary_match:
            findings["total_errors"] = int(summary_match.group(1))
            findings["total_warnings"] = int(summary_match.group(2))

    return findings


@beartype
@require(lambda output: isinstance(output, str), "Output must be string")
@ensure(lambda result: isinstance(result, dict), "Must return dictionary")
@ensure(lambda result: "counterexamples" in result, "Must include counterexamples")
def _extract_crosshair_findings(output: str) -> dict[str, Any]:
    """Extract structured findings from CrossHair output."""
    findings: dict[str, Any] = {
        "counterexamples": [],
        "total_counterexamples": 0,
    }

    # Strip ANSI codes
    clean_output = _strip_ansi_codes(output)

    # CrossHair typically outputs counterexamples
    # Format varies, but we can extract basic info
    if "counterexample" in clean_output.lower() or "failed" in clean_output.lower():
        # Try to extract file and line info
        pattern = r"([^:]+):(\d+):.*?(counterexample|failed)"
        matches = re.finditer(pattern, clean_output, re.IGNORECASE)
        for match in matches:
            findings["counterexamples"].append(
                {
                    "file": match.group(1),
                    "line": int(match.group(2)),
                    "type": match.group(3).lower(),
                }
            )
            findings["total_counterexamples"] += 1

    return findings


@beartype
@require(lambda output: isinstance(output, str), "Output must be string")
@ensure(lambda result: isinstance(result, dict), "Must return dictionary")
@ensure(lambda result: "tests_run" in result, "Must include tests_run")
@ensure(lambda result: result["tests_run"] >= 0, "tests_run must be non-negative")
def _extract_pytest_findings(output: str) -> dict[str, Any]:
    """Extract structured findings from pytest output."""
    findings: dict[str, Any] = {
        "tests_run": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "tests_skipped": 0,
        "failures": [],
    }

    # Strip ANSI codes
    clean_output = _strip_ansi_codes(output)

    # Extract test summary
    summary_match = re.search(r"(\d+)\s+passed", clean_output, re.IGNORECASE)
    if summary_match:
        findings["tests_passed"] = int(summary_match.group(1))

    failed_match = re.search(r"(\d+)\s+failed", clean_output, re.IGNORECASE)
    if failed_match:
        findings["tests_failed"] = int(failed_match.group(1))

    skipped_match = re.search(r"(\d+)\s+skipped", clean_output, re.IGNORECASE)
    if skipped_match:
        findings["tests_skipped"] = int(skipped_match.group(1))

    findings["tests_run"] = findings["tests_passed"] + findings["tests_failed"] + findings["tests_skipped"]

    return findings


@beartype
@require(lambda tool: isinstance(tool, str) and len(tool) > 0, "Tool must be non-empty string")
@require(lambda output: isinstance(output, str), "Output must be string")
@require(lambda error: isinstance(error, str), "Error must be string")
@ensure(lambda result: isinstance(result, dict), "Must return dictionary")
def _extract_findings(tool: str, output: str, error: str) -> dict[str, Any]:
    """
    Extract structured findings from tool output based on tool type.

    Args:
        tool: Tool name (ruff, semgrep, basedpyright, crosshair, pytest)
        output: Tool stdout output
        error: Tool stderr output

    Returns:
        Dictionary with structured findings for the specific tool
    """
    tool_lower = tool.lower()
    if tool_lower == "ruff":
        return _extract_ruff_findings(output)
    if tool_lower == "semgrep":
        return _extract_semgrep_findings(output, error)
    if tool_lower == "basedpyright":
        return _extract_basedpyright_findings(output)
    if tool_lower == "crosshair":
        return _extract_crosshair_findings(output)
    if tool_lower == "pytest":
        return _extract_pytest_findings(output)
    # Unknown tool - return empty findings
    return {}


@dataclass
class CheckResult:
    """Result of a single validation check."""

    name: str
    tool: str
    status: CheckStatus
    duration: float | None = None
    exit_code: int | None = None
    output: str = ""
    error: str = ""
    timeout: bool = False

    def __post_init__(self) -> None:
        """Validate that tool is non-empty if findings extraction is needed."""
        if not self.tool:
            self.tool = "unknown"  # Default to "unknown" if tool is empty

    @beartype
    @require(lambda max_output_length: max_output_length > 0, "max_output_length must be positive")
    @ensure(lambda result: isinstance(result, dict), "Must return dictionary")
    @ensure(
        lambda result: "name" in result and "tool" in result and "status" in result,
        "Must include name, tool, and status",
    )
    def to_dict(self, include_findings: bool = True, max_output_length: int = 50000) -> dict[str, Any]:
        """
        Convert result to dictionary with structured findings.

        Args:
            include_findings: Whether to include structured findings (default: True)
            max_output_length: Maximum length of raw output/error to include if findings unavailable (truncates if longer)

        Returns:
            Dictionary representation of the check result with structured findings
        """
        result = {
            "name": self.name,
            "tool": self.tool,
            "status": self.status.value,
            "duration": self.duration,
            "exit_code": self.exit_code,
            "timeout": self.timeout,
            "output_length": len(self.output),
            "error_length": len(self.error),
        }

        # Extract structured findings based on tool type
        if include_findings and self.tool:
            try:
                findings = _extract_findings(self.tool, self.output, self.error)
                if findings:
                    result["findings"] = findings
            except Exception:
                # If extraction fails, fall back to raw output (truncated)
                if self.output:
                    if len(self.output) <= max_output_length:
                        result["output"] = _strip_ansi_codes(self.output)
                    else:
                        result["output"] = _strip_ansi_codes(self.output[:max_output_length])
                        result["output_truncated"] = True
                else:
                    result["output"] = ""

                if self.error:
                    if len(self.error) <= max_output_length:
                        result["error"] = _strip_ansi_codes(self.error)
                    else:
                        result["error"] = _strip_ansi_codes(self.error[:max_output_length])
                        result["error_truncated"] = True
                else:
                    result["error"] = ""

        return result


def _repro_report_metadata_fields(report: ReproReport) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    if report.timestamp:
        metadata["timestamp"] = report.timestamp
    if report.repo_path:
        metadata["repo_path"] = report.repo_path
    if report.budget is not None:
        metadata["budget"] = report.budget
    if report.active_plan_path:
        metadata["active_plan_path"] = report.active_plan_path
    if report.enforcement_config_path:
        metadata["enforcement_config_path"] = report.enforcement_config_path
    if report.enforcement_preset:
        metadata["enforcement_preset"] = report.enforcement_preset
    if report.fix_enabled:
        metadata["fix_enabled"] = report.fix_enabled
    if report.fail_fast:
        metadata["fail_fast"] = report.fail_fast
    if report.crosshair_required:
        metadata["crosshair_required"] = report.crosshair_required
    if report.crosshair_requirement_violated:
        metadata["crosshair_requirement_violated"] = report.crosshair_requirement_violated
    return metadata


@dataclass
class ReproReport:
    """Aggregated report of all validation checks."""

    checks: list[CheckResult] = field(default_factory=list)
    total_duration: float = 0.0
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    timeout_checks: int = 0
    skipped_checks: int = 0
    budget_exceeded: bool = False
    # Metadata fields
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    repo_path: str | None = None
    budget: int | None = None
    active_plan_path: str | None = None
    enforcement_config_path: str | None = None
    enforcement_preset: str | None = None
    fix_enabled: bool = False
    fail_fast: bool = False
    crosshair_required: bool = False
    crosshair_requirement_violated: bool = False

    @beartype
    @require(lambda result: isinstance(result, CheckResult), "Must be CheckResult instance")
    def add_check(self, result: CheckResult) -> None:
        """Add a check result to the report."""
        self.checks.append(result)
        self.total_checks += 1

        if result.duration:
            self.total_duration += result.duration

        if result.status == CheckStatus.PASSED:
            self.passed_checks += 1
        elif result.status == CheckStatus.FAILED:
            self.failed_checks += 1
        elif result.status == CheckStatus.TIMEOUT:
            self.timeout_checks += 1
        elif result.status == CheckStatus.SKIPPED:
            self.skipped_checks += 1

    @beartype
    @ensure(lambda result: result in (0, 1, 2), "Exit code must be 0, 1, or 2")
    def get_exit_code(self) -> int:
        """
        Get exit code for the repro command.

        Returns:
            0 = all passed, 1 = some failed, 2 = budget exceeded
        """
        if self.budget_exceeded or self.timeout_checks > 0:
            return 2
        if self.crosshair_requirement_violated:
            return 1
        # CrossHair failures are non-blocking (advisory only) - don't count them
        failed_checks_blocking = [
            check for check in self.checks if check.status == CheckStatus.FAILED and check.tool != "crosshair"
        ]
        if failed_checks_blocking:
            return 1
        return 0

    @beartype
    @require(lambda max_finding_length: max_finding_length > 0, "max_finding_length must be positive")
    @ensure(lambda result: isinstance(result, dict), "Must return dictionary")
    @ensure(lambda result: "total_checks" in result and "checks" in result, "Must include total_checks and checks")
    def to_dict(self, include_findings: bool = True, max_finding_length: int = 50000) -> dict[str, Any]:
        """
        Convert report to dictionary with structured findings.

        Args:
            include_findings: Whether to include structured findings for each check (default: True)
            max_finding_length: Maximum length of raw output/error to include if findings unavailable (truncates if longer)

        Returns:
            Dictionary representation of the report with structured findings
        """
        result = {
            "total_duration": self.total_duration,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "timeout_checks": self.timeout_checks,
            "skipped_checks": self.skipped_checks,
            "budget_exceeded": self.budget_exceeded,
            "checks": [
                check.to_dict(include_findings=include_findings, max_output_length=max_finding_length)
                for check in self.checks
            ],
        }

        metadata = _repro_report_metadata_fields(self)
        if metadata:
            result["metadata"] = metadata

        return result


def _check_result_duration_nonnegative(result: CheckResult) -> bool:
    return result.duration is None or result.duration >= 0


def _repro_report_totals_consistent(result: ReproReport) -> bool:
    return (
        result.total_checks
        == result.passed_checks + result.failed_checks + result.timeout_checks + result.skipped_checks
    )


def _repro_report_total_checks_nonnegative(result: ReproReport) -> bool:
    return result.total_checks >= 0


def _repro_checker_budget_ok(self: Any) -> bool:
    return getattr(self, "budget", 0) > 0


def _crosshair_failure_flags(combined_lower: str) -> tuple[bool, bool]:
    is_signature = (
        "wrong parameter order" in combined_lower
        or "keyword-only parameter" in combined_lower
        or "valueerror: wrong parameter" in combined_lower
        or ("signature" in combined_lower and ("error" in combined_lower or "failure" in combined_lower))
    )
    is_side = "sideeffectdetected" in combined_lower or "side effect" in combined_lower
    return is_signature, is_side


def _apply_crosshair_process_exit(
    result: CheckResult, proc: subprocess.CompletedProcess[str], tool: str, command: list[str]
) -> None:
    if proc.returncode == 0:
        result.status = CheckStatus.PASSED
        return
    if tool.lower() != "crosshair":
        result.status = CheckStatus.FAILED
        return
    combined_lower = f"{proc.stderr} {proc.stdout}".lower()
    sig, side = _crosshair_failure_flags(combined_lower)
    command_preview = " ".join(command[:24])
    if sig:
        result.status = CheckStatus.SKIPPED
        stderr_preview = proc.stderr[:300] if proc.stderr else "signature analysis limitation"
        result.error = (
            "CrossHair signature analysis limitation (non-blocking, runtime contracts valid).\n"
            f"Target command: {command_preview}\n\n{stderr_preview}"
        )
        return
    if side:
        result.status = CheckStatus.SKIPPED
        stderr_preview = proc.stderr[:300] if proc.stderr else "side effect detected"
        result.error = (
            f"CrossHair side-effect detected (non-blocking).\nTarget command: {command_preview}\n\n{stderr_preview}"
        )
        return
    result.status = CheckStatus.FAILED


def _repro_resolve_source_dirs(repo_path: Path) -> list[str]:
    from specfact_cli.utils.env_manager import detect_source_directories

    source_dirs = detect_source_directories(repo_path)
    if source_dirs:
        return source_dirs
    if (repo_path / "src").exists():
        return ["src/"]
    if (repo_path / "lib").exists():
        return ["lib/"]
    return ["."]


class ReproChecker:
    """
    Runs validation checks with time budgets and result aggregation.

    Executes various tools (ruff, semgrep, basedpyright, crosshair, pytest)
    and aggregates their results into a comprehensive report.
    """

    repo_path: Path
    budget: int
    fail_fast: bool
    fix: bool
    crosshair_required: bool
    crosshair_per_path_timeout: int | None
    report: ReproReport
    start_time: float

    @beartype
    @require(lambda budget: budget > 0, "Budget must be positive")
    @ensure(_repro_checker_budget_ok, "Budget must be positive after init")
    def __init__(
        self,
        repo_path: Path | None = None,
        budget: int = 120,
        fail_fast: bool = False,
        fix: bool = False,
        crosshair_required: bool = False,
        crosshair_per_path_timeout: int | None = None,
    ) -> None:
        """
        Initialize reproducibility checker.

        Args:
            repo_path: Path to repository (default: current directory)
            budget: Total time budget in seconds (must be > 0)
            fail_fast: Stop on first failure
            fix: Apply auto-fixes where available (Semgrep auto-fixes)
            crosshair_per_path_timeout: If set, pass --per_path_timeout N to CrossHair (deep validation).
        """
        self.repo_path = Path(repo_path) if repo_path else Path(".")
        self.budget = budget
        self.fail_fast = fail_fast
        self.fix = fix
        self.crosshair_required = crosshair_required
        self.crosshair_per_path_timeout = crosshair_per_path_timeout
        self.report = ReproReport()
        self.start_time = time.time()

        # Initialize metadata in report
        self.report.repo_path = str(self.repo_path.absolute())
        self.report.budget = budget
        self.report.fix_enabled = fix
        self.report.fail_fast = fail_fast
        self.report.crosshair_required = crosshair_required

    @beartype
    @require(lambda name: isinstance(name, str) and len(name) > 0, "Name must be non-empty string")
    @require(lambda tool: isinstance(tool, str) and len(tool) > 0, "Tool must be non-empty string")
    @require(lambda command: isinstance(command, list) and len(command) > 0, "Command must be non-empty list")
    @require(lambda timeout: timeout is None or timeout > 0, "Timeout must be positive if provided")
    @require(lambda env: env is None or isinstance(env, dict), "env must be dict or None")
    @ensure(lambda result: isinstance(result, CheckResult), "Must return CheckResult")
    @ensure(_check_result_duration_nonnegative, "Duration must be non-negative")
    def run_check(
        self,
        name: str,
        tool: str,
        command: list[str],
        timeout: int | None = None,
        skip_if_missing: bool = True,
        env: dict[str, str] | None = None,
    ) -> CheckResult:
        """
        Run a single validation check.

        Args:
            name: Human-readable check name
            tool: Tool name (for display)
            command: Command to execute
            timeout: Per-check timeout (default: budget / number of checks, must be > 0 if provided)
            skip_if_missing: Skip check if tool not found
            env: Optional environment variables to pass to the subprocess

        Returns:
            CheckResult with status and output
        """
        result = CheckResult(name=name, tool=tool, status=CheckStatus.PENDING)

        # Check if tool exists (cross-platform)
        if skip_if_missing:
            tool_path = shutil.which(command[0])
            if tool_path is None:
                result.status = CheckStatus.SKIPPED
                result.error = f"Tool '{command[0]}' not found in PATH, skipping"
                return result

        # Check budget
        elapsed = time.time() - self.start_time
        if elapsed >= self.budget:
            self.report.budget_exceeded = True
            result.status = CheckStatus.TIMEOUT
            result.timeout = True
            result.error = f"Budget exceeded ({self.budget}s)"
            return result

        # Calculate timeout for this check
        remaining_budget = self.budget - elapsed
        check_timeout = min(timeout or (remaining_budget / 2), remaining_budget)

        # Run command
        result.status = CheckStatus.RUNNING
        start = time.time()

        try:
            proc = subprocess.run(
                command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=check_timeout,
                check=False,
                env=env,
            )

            result.duration = time.time() - start
            result.exit_code = proc.returncode
            result.output = proc.stdout
            result.error = proc.stderr
            _apply_crosshair_process_exit(result, proc, tool, command)

        except subprocess.TimeoutExpired:
            result.duration = time.time() - start
            result.status = CheckStatus.TIMEOUT
            result.timeout = True
            result.error = f"Check timed out after {check_timeout}s"

        except Exception as e:
            result.duration = time.time() - start
            result.status = CheckStatus.FAILED
            result.error = f"Check failed with exception: {e!s}"

        return result

    @beartype
    @ensure(lambda result: isinstance(result, ReproReport), "Must return ReproReport")
    @ensure(_repro_report_total_checks_nonnegative, "Total checks must be non-negative")
    @ensure(_repro_report_totals_consistent, "Total checks must equal sum of all status types")
    def run_all_checks(self) -> ReproReport:
        """
        Run all validation checks.

        Detects the target repository's environment manager and builds appropriate
        commands. Makes all tools optional with clear messaging when unavailable.

        Returns:
            ReproReport with aggregated results
        """
        from specfact_cli.utils.env_manager import detect_env_manager

        env_info = detect_env_manager(self.repo_path)
        source_dirs = _repro_resolve_source_dirs(self.repo_path)
        checks = _repro_build_checks_list(self, env_info, source_dirs)
        _repro_run_checks_loop(self, checks, env_info)

        self.report.total_duration = time.time() - self.start_time
        elapsed = time.time() - self.start_time
        if elapsed >= self.budget:
            self.report.budget_exceeded = True

        _repro_populate_report_metadata(self)
        return self.report


def _repro_checks_append_ruff(
    checks: list[tuple[str, str, list[str], int | None, bool, dict[str, str] | None]],
    repo_path: Path,
    env_info: Any,
    source_dirs: list[str],
    tests_dir: Path,
) -> None:
    from specfact_cli.utils.env_manager import build_tool_command, check_tool_in_env

    ruff_available, _ = check_tool_in_env(repo_path, "ruff", env_info)
    if ruff_available:
        ruff_command = ["ruff", "check", "--output-format=full", *source_dirs]
        if tests_dir.exists():
            ruff_command.append("tests/")
        if (repo_path / "tools").exists():
            ruff_command.append("tools/")
        ruff_command = build_tool_command(env_info, ruff_command)
        checks.append(("Linting (ruff)", "ruff", ruff_command, None, True, None))
    else:
        checks.append(("Linting (ruff)", "ruff", [], None, True, None))


def _repro_checks_append_semgrep(
    checks: list[tuple[str, str, list[str], int | None, bool, dict[str, str] | None]],
    checker: ReproChecker,
    env_info: Any,
    repo_path: Path,
    semgrep_config: Path,
) -> None:
    from specfact_cli.utils.env_manager import build_tool_command, check_tool_in_env

    if not semgrep_config.exists():
        return
    semgrep_available, _ = check_tool_in_env(repo_path, "semgrep", env_info)
    if semgrep_available:
        semgrep_log_path = repo_path / ".specfact" / "logs" / "semgrep.log"
        semgrep_cache_path = repo_path / ".specfact" / "cache" / "semgrep_version"
        semgrep_log_path.parent.mkdir(parents=True, exist_ok=True)
        semgrep_cache_path.parent.mkdir(parents=True, exist_ok=True)
        semgrep_env = os.environ.copy()
        semgrep_env["SEMGREP_LOG_FILE"] = str(semgrep_log_path)
        semgrep_env["SEMGREP_VERSION_CACHE_PATH"] = str(semgrep_cache_path)
        semgrep_env["XDG_CACHE_HOME"] = str((repo_path / ".specfact" / "cache").resolve())
        semgrep_command = ["semgrep", "--config", str(semgrep_config.relative_to(repo_path)), "."]
        if checker.fix:
            semgrep_command.append("--autofix")
        semgrep_command = build_tool_command(env_info, semgrep_command)
        checks.append(("Async patterns (semgrep)", "semgrep", semgrep_command, 30, True, semgrep_env))
    else:
        checks.append(("Async patterns (semgrep)", "semgrep", [], 30, True, None))


def _repro_checks_append_basedpyright(
    checks: list[tuple[str, str, list[str], int | None, bool, dict[str, str] | None]],
    repo_path: Path,
    env_info: Any,
    source_dirs: list[str],
    tests_dir: Path,
) -> None:
    from specfact_cli.utils.env_manager import build_tool_command, check_tool_in_env

    basedpyright_available, _ = check_tool_in_env(repo_path, "basedpyright", env_info)
    if basedpyright_available:
        basedpyright_command = ["basedpyright", *source_dirs]
        if tests_dir.exists():
            basedpyright_command.append("tests/")
        if (repo_path / "tools").exists():
            basedpyright_command.append("tools/")
        basedpyright_command = build_tool_command(env_info, basedpyright_command)
        checks.append(("Type checking (basedpyright)", "basedpyright", basedpyright_command, None, True, None))
    else:
        checks.append(("Type checking (basedpyright)", "basedpyright", [], None, True, None))


def _repro_checks_append_crosshair(
    checks: list[tuple[str, str, list[str], int | None, bool, dict[str, str] | None]],
    checker: ReproChecker,
    env_info: Any,
    repo_path: Path,
    source_dirs: list[str],
) -> None:
    from specfact_cli.utils.env_manager import build_tool_command, check_tool_in_env

    if not source_dirs:
        return
    crosshair_available, _ = check_tool_in_env(repo_path, "crosshair", env_info)
    if not crosshair_available:
        checks.append(("Contract exploration (CrossHair)", "crosshair", [], checker.budget, True, None))
        return
    crosshair_targets, pythonpath_roots = _find_crosshair_property_targets(repo_path)
    if not crosshair_targets:
        crosshair_targets = source_dirs.copy()
        if (repo_path / "tools").exists():
            crosshair_targets.append("tools/")
        crosshair_targets, _excluded_main, pythonpath_roots = _expand_crosshair_targets(repo_path, crosshair_targets)

    if not crosshair_targets:
        checks.append(("Contract exploration (CrossHair)", "crosshair", [], checker.budget, True, None))
        return
    crosshair_base = ["python", "-m", "crosshair", "check", *crosshair_targets]
    if checker.crosshair_per_path_timeout is not None and checker.crosshair_per_path_timeout > 0:
        crosshair_base.extend(["--per_path_timeout", str(checker.crosshair_per_path_timeout)])
    crosshair_command = build_tool_command(env_info, crosshair_base)
    crosshair_env = _build_crosshair_env(pythonpath_roots)
    checks.append(
        ("Contract exploration (CrossHair)", "crosshair", crosshair_command, checker.budget, True, crosshair_env)
    )


def _repro_checks_append_pytest_dir(
    checks: list[tuple[str, str, list[str], int | None, bool, dict[str, str] | None]],
    repo_path: Path,
    env_info: Any,
    tests_subdir: str,
    display_name: str,
) -> None:
    from specfact_cli.utils.env_manager import build_tool_command, check_tool_in_env

    if not (repo_path / "tests" / tests_subdir).exists():
        return
    pytest_available, _ = check_tool_in_env(repo_path, "pytest", env_info)
    if pytest_available:
        pytest_command = ["pytest", f"tests/{tests_subdir}/", "-v"]
        pytest_command = build_tool_command(env_info, pytest_command)
        checks.append((display_name, "pytest", pytest_command, 30, True, None))
    else:
        checks.append((display_name, "pytest", [], 30, True, None))


def _repro_build_checks_list(
    checker: ReproChecker,
    env_info: Any,
    source_dirs: list[str],
) -> list[tuple[str, str, list[str], int | None, bool, dict[str, str] | None]]:
    repo_path = checker.repo_path
    semgrep_config = repo_path / "tools" / "semgrep" / "async.yml"
    tests_dir = repo_path / "tests"
    checks: list[tuple[str, str, list[str], int | None, bool, dict[str, str] | None]] = []

    _repro_checks_append_ruff(checks, repo_path, env_info, source_dirs, tests_dir)
    _repro_checks_append_semgrep(checks, checker, env_info, repo_path, semgrep_config)
    _repro_checks_append_basedpyright(checks, repo_path, env_info, source_dirs, tests_dir)
    _repro_checks_append_crosshair(checks, checker, env_info, repo_path, source_dirs)
    _repro_checks_append_pytest_dir(checks, repo_path, env_info, "contracts", "Property tests (pytest contracts)")
    _repro_checks_append_pytest_dir(checks, repo_path, env_info, "smoke", "Smoke tests (pytest smoke)")

    return checks


def _repro_result_for_missing_tool(
    checker: ReproChecker,
    name: str,
    tool: str,
    tool_message: str | None,
) -> CheckResult:
    result = CheckResult(
        name=name,
        tool=tool,
        status=CheckStatus.SKIPPED,
        error=tool_message or f"Tool '{tool}' not available",
    )
    if tool == "crosshair" and checker.crosshair_required:
        result.status = CheckStatus.FAILED
        result.error = f"CrossHair is required but unavailable: {result.error}"
        checker.report.crosshair_requirement_violated = True
    return result


def _repro_normalize_crosshair_required_result(result: CheckResult, checker: ReproChecker) -> None:
    if not (
        result.tool == "crosshair"
        and checker.crosshair_required
        and result.status in {CheckStatus.SKIPPED, CheckStatus.FAILED, CheckStatus.TIMEOUT}
    ):
        return
    checker.report.crosshair_requirement_violated = True
    if result.status == CheckStatus.SKIPPED:
        result.status = CheckStatus.FAILED
        detail = result.error or "CrossHair check was skipped"
        result.error = f"CrossHair is required but did not complete.\n{detail}"


def _repro_run_checks_loop(
    checker: ReproChecker,
    checks: list[tuple[str, str, list[str], int | None, bool, dict[str, str] | None]],
    env_info: Any,
) -> None:
    from specfact_cli.utils.env_manager import check_tool_in_env

    for check_args in checks:
        elapsed = time.time() - checker.start_time
        if elapsed >= checker.budget:
            checker.report.budget_exceeded = True
            break

        name, tool, command, _timeout, _skip_if_missing, _env = check_args
        if not command:
            _, tool_message = check_tool_in_env(checker.repo_path, tool, env_info)
            checker.report.add_check(_repro_result_for_missing_tool(checker, name, tool, tool_message))
            continue

        result = checker.run_check(*check_args)
        _repro_normalize_crosshair_required_result(result, checker)
        checker.report.add_check(result)

        if checker.fail_fast and result.status == CheckStatus.FAILED:
            break


def _repro_populate_report_metadata(checker: ReproChecker) -> None:
    try:
        from specfact_cli.utils.structure import SpecFactStructure

        repo_root = checker.repo_path.resolve()
        active_plan_path = SpecFactStructure.get_default_plan_path(checker.repo_path)
        if active_plan_path.exists():
            active_plan_abs = active_plan_path.resolve()
            if active_plan_abs.is_relative_to(repo_root):
                checker.report.active_plan_path = str(active_plan_abs.relative_to(repo_root))
            else:
                checker.report.active_plan_path = str(active_plan_abs)

        enforcement_config_path = SpecFactStructure.get_enforcement_config_path(checker.repo_path)
        if enforcement_config_path.exists():
            enforce_abs = enforcement_config_path.resolve()
            if enforce_abs.is_relative_to(repo_root):
                checker.report.enforcement_config_path = str(enforce_abs.relative_to(repo_root))
            else:
                checker.report.enforcement_config_path = str(enforce_abs)
            try:
                from specfact_cli.models.enforcement import EnforcementConfig
                from specfact_cli.utils.yaml_utils import load_yaml

                config_data = load_yaml(enforcement_config_path)
                if config_data:
                    enforcement_config = EnforcementConfig(**config_data)
                    checker.report.enforcement_preset = enforcement_config.preset.value
            except Exception as e:
                console.print(f"[dim]Warning: Could not load enforcement config preset: {e}[/dim]")

    except Exception as e:
        console.print(f"[dim]Warning: Could not collect metadata: {e}[/dim]")
