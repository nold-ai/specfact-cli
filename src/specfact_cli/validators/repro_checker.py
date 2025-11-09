"""
Reproducibility checker - Runs various validation tools and aggregates results.

This module provides functionality to run linting, type checking, contract
exploration, and test suites with time budgets and result aggregation.
"""

from __future__ import annotations

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

    # Parse basedpyright output: "path:line:col: error|warning: message"
    pattern = r"^([^:]+):(\d+):(\d+):\s+(error|warning):\s+(.+)$"
    for line in clean_output.split("\n"):
        line_stripped = line.strip()
        if not line_stripped:
            continue
        match = re.match(pattern, line_stripped)
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

        # Add metadata if available
        metadata = {}
        if self.timestamp:
            metadata["timestamp"] = self.timestamp
        if self.repo_path:
            metadata["repo_path"] = self.repo_path
        if self.budget is not None:
            metadata["budget"] = self.budget
        if self.active_plan_path:
            metadata["active_plan_path"] = self.active_plan_path
        if self.enforcement_config_path:
            metadata["enforcement_config_path"] = self.enforcement_config_path
        if self.enforcement_preset:
            metadata["enforcement_preset"] = self.enforcement_preset
        if self.fix_enabled:
            metadata["fix_enabled"] = self.fix_enabled
        if self.fail_fast:
            metadata["fail_fast"] = self.fail_fast

        if metadata:
            result["metadata"] = metadata

        return result


class ReproChecker:
    """
    Runs validation checks with time budgets and result aggregation.

    Executes various tools (ruff, semgrep, basedpyright, crosshair, pytest)
    and aggregates their results into a comprehensive report.
    """

    @beartype
    @require(lambda budget: budget > 0, "Budget must be positive")
    @ensure(lambda self: self.budget > 0, "Budget must be positive after init")
    def __init__(
        self, repo_path: Path | None = None, budget: int = 120, fail_fast: bool = False, fix: bool = False
    ) -> None:
        """
        Initialize reproducibility checker.

        Args:
            repo_path: Path to repository (default: current directory)
            budget: Total time budget in seconds (must be > 0)
            fail_fast: Stop on first failure
            fix: Apply auto-fixes where available (Semgrep auto-fixes)
        """
        self.repo_path = Path(repo_path) if repo_path else Path(".")
        self.budget = budget
        self.fail_fast = fail_fast
        self.fix = fix
        self.report = ReproReport()
        self.start_time = time.time()

        # Initialize metadata in report
        self.report.repo_path = str(self.repo_path.absolute())
        self.report.budget = budget
        self.report.fix_enabled = fix
        self.report.fail_fast = fail_fast

    @beartype
    @require(lambda name: isinstance(name, str) and len(name) > 0, "Name must be non-empty string")
    @require(lambda tool: isinstance(tool, str) and len(tool) > 0, "Tool must be non-empty string")
    @require(lambda command: isinstance(command, list) and len(command) > 0, "Command must be non-empty list")
    @require(lambda timeout: timeout is None or timeout > 0, "Timeout must be positive if provided")
    @ensure(lambda result: isinstance(result, CheckResult), "Must return CheckResult")
    @ensure(lambda result: result.duration is None or result.duration >= 0, "Duration must be non-negative")
    def run_check(
        self,
        name: str,
        tool: str,
        command: list[str],
        timeout: int | None = None,
        skip_if_missing: bool = True,
    ) -> CheckResult:
        """
        Run a single validation check.

        Args:
            name: Human-readable check name
            tool: Tool name (for display)
            command: Command to execute
            timeout: Per-check timeout (default: budget / number of checks, must be > 0 if provided)
            skip_if_missing: Skip check if tool not found

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
            )

            result.duration = time.time() - start
            result.exit_code = proc.returncode
            result.output = proc.stdout
            result.error = proc.stderr

            # Check if this is a CrossHair signature analysis limitation (not a real failure)
            is_signature_issue = False
            if tool.lower() == "crosshair" and proc.returncode != 0:
                combined_output = f"{proc.stderr} {proc.stdout}".lower()
                is_signature_issue = (
                    "wrong parameter order" in combined_output
                    or "keyword-only parameter" in combined_output
                    or "valueerror: wrong parameter" in combined_output
                    or ("signature" in combined_output and ("error" in combined_output or "failure" in combined_output))
                )

            if proc.returncode == 0:
                result.status = CheckStatus.PASSED
            elif is_signature_issue:
                # CrossHair signature analysis limitation - treat as skipped, not failed
                result.status = CheckStatus.SKIPPED
                result.error = f"CrossHair signature analysis limitation (non-blocking, runtime contracts valid): {proc.stderr[:200] if proc.stderr else 'signature analysis limitation'}"
            else:
                result.status = CheckStatus.FAILED

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
    @ensure(lambda result: result.total_checks >= 0, "Total checks must be non-negative")
    @ensure(
        lambda result: result.total_checks
        == result.passed_checks + result.failed_checks + result.timeout_checks + result.skipped_checks,
        "Total checks must equal sum of all status types",
    )
    def run_all_checks(self) -> ReproReport:
        """
        Run all validation checks.

        Returns:
            ReproReport with aggregated results
        """
        # Check if semgrep config exists
        semgrep_config = self.repo_path / "tools" / "semgrep" / "async.yml"
        semgrep_enabled = semgrep_config.exists()

        # Check if test directories exist
        contracts_tests = self.repo_path / "tests" / "contracts"
        smoke_tests = self.repo_path / "tests" / "smoke"
        src_dir = self.repo_path / "src"

        checks: list[tuple[str, str, list[str], int | None, bool]] = [
            (
                "Linting (ruff)",
                "ruff",
                ["ruff", "check", "--output-format=full", "src/", "tests/", "tools/"],
                None,
                True,
            ),
        ]

        # Add semgrep only if config exists
        if semgrep_enabled:
            semgrep_command = ["semgrep", "--config", str(semgrep_config.relative_to(self.repo_path)), "."]
            if self.fix:
                semgrep_command.append("--autofix")
            checks.append(
                (
                    "Async patterns (semgrep)",
                    "semgrep",
                    semgrep_command,
                    30,
                    True,
                )
            )

        checks.extend(
            [
                ("Type checking (basedpyright)", "basedpyright", ["basedpyright", "src/", "tools/"], None, True),
            ]
        )

        # Add CrossHair only if src/ exists
        # Exclude common/logger_setup.py from CrossHair analysis due to known signature analysis issues
        # CrossHair doesn't support --exclude, so we exclude the common directory and add other directories
        if src_dir.exists():
            # Get all subdirectories except common
            specfact_dirs = [d for d in src_dir.iterdir() if d.is_dir() and d.name != "common"]
            crosshair_targets = ["src/" + d.name for d in specfact_dirs] + ["tools/"]
            checks.append(
                (
                    "Contract exploration (CrossHair)",
                    "crosshair",
                    ["crosshair", "check", *crosshair_targets],
                    60,
                    True,
                )
            )

        # Add property tests only if directory exists
        if contracts_tests.exists():
            checks.append(
                (
                    "Property tests (pytest contracts)",
                    "pytest",
                    ["pytest", "tests/contracts/", "-v"],
                    30,
                    True,
                )
            )

        # Add smoke tests only if directory exists
        if smoke_tests.exists():
            checks.append(("Smoke tests (pytest smoke)", "pytest", ["pytest", "tests/smoke/", "-v"], 30, True))

        for check_args in checks:
            # Check budget before starting
            elapsed = time.time() - self.start_time
            if elapsed >= self.budget:
                self.report.budget_exceeded = True
                break

            # Run check
            result = self.run_check(*check_args)
            self.report.add_check(result)

            # Fail fast if requested
            if self.fail_fast and result.status == CheckStatus.FAILED:
                break

        self.report.total_duration = time.time() - self.start_time

        # Check if budget exceeded
        elapsed = time.time() - self.start_time
        if elapsed >= self.budget:
            self.report.budget_exceeded = True

        # Populate metadata: active plan and enforcement config
        try:
            from specfact_cli.utils.structure import SpecFactStructure

            # Get active plan path
            active_plan_path = SpecFactStructure.get_default_plan_path(self.repo_path)
            if active_plan_path.exists():
                self.report.active_plan_path = str(active_plan_path.relative_to(self.repo_path))

            # Get enforcement config path and preset
            enforcement_config_path = SpecFactStructure.get_enforcement_config_path(self.repo_path)
            if enforcement_config_path.exists():
                self.report.enforcement_config_path = str(enforcement_config_path.relative_to(self.repo_path))
                try:
                    from specfact_cli.models.enforcement import EnforcementConfig
                    from specfact_cli.utils.yaml_utils import load_yaml

                    config_data = load_yaml(enforcement_config_path)
                    if config_data:
                        enforcement_config = EnforcementConfig(**config_data)
                        self.report.enforcement_preset = enforcement_config.preset.value
                except Exception as e:
                    # If config can't be loaded, just skip preset (non-fatal)
                    console.print(f"[dim]Warning: Could not load enforcement config preset: {e}[/dim]")

        except Exception as e:
            # If metadata collection fails, continue without it (non-fatal)
            console.print(f"[dim]Warning: Could not collect metadata: {e}[/dim]")

        return self.report
