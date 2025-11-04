"""
Reproducibility checker - Runs various validation tools and aggregates results.

This module provides functionality to run linting, type checking, contract
exploration, and test suites with time budgets and result aggregation.
"""

from __future__ import annotations

import shutil
import subprocess
import time
from dataclasses import dataclass, field
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

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "name": self.name,
            "tool": self.tool,
            "status": self.status.value,
            "duration": self.duration,
            "exit_code": self.exit_code,
            "timeout": self.timeout,
            "output_length": len(self.output),
            "error_length": len(self.error),
        }


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
        if self.failed_checks > 0:
            return 1
        return 0

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "total_duration": self.total_duration,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "timeout_checks": self.timeout_checks,
            "skipped_checks": self.skipped_checks,
            "budget_exceeded": self.budget_exceeded,
            "checks": [check.to_dict() for check in self.checks],
        }


class ReproChecker:
    """
    Runs validation checks with time budgets and result aggregation.

    Executes various tools (ruff, semgrep, basedpyright, crosshair, pytest)
    and aggregates their results into a comprehensive report.
    """

    @beartype
    @require(lambda budget: budget > 0, "Budget must be positive")
    @ensure(lambda self: self.budget > 0, "Budget must be positive after init")
    def __init__(self, repo_path: Path | None = None, budget: int = 120, fail_fast: bool = False) -> None:
        """
        Initialize reproducibility checker.

        Args:
            repo_path: Path to repository (default: current directory)
            budget: Total time budget in seconds (must be > 0)
            fail_fast: Stop on first failure
        """
        self.repo_path = Path(repo_path) if repo_path else Path(".")
        self.budget = budget
        self.fail_fast = fail_fast
        self.report = ReproReport()
        self.start_time = time.time()

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

            if proc.returncode == 0:
                result.status = CheckStatus.PASSED
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
            result.error = str(e)

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
            ("Linting (ruff)", "ruff", ["ruff", "check", "."], None, True),
        ]

        # Add semgrep only if config exists
        if semgrep_enabled:
            checks.append(
                (
                    "Async patterns (semgrep)",
                    "semgrep",
                    ["semgrep", "--config", str(semgrep_config.relative_to(self.repo_path)), "."],
                    30,
                    True,
                )
            )

        checks.extend(
            [
                ("Type checking (basedpyright)", "basedpyright", ["basedpyright", "."], None, True),
            ]
        )

        # Add CrossHair only if src/ exists
        if src_dir.exists():
            checks.append(("Contract exploration (CrossHair)", "crosshair", ["crosshair", "check", "src/"], 60, True))

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
        return self.report
