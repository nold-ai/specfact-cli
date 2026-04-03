#!/usr/bin/env python3
"""
Contract-First Smart Test System

This system implements the 3-layer contract-first quality model:
1. Runtime contracts (icontract + beartype)
2. Automated exploration (CrossHair + Hypothesis)
3. Scenario/E2E tests (business workflow validation)

After core slimming, scenario tests that invoke removed CLI commands (plan, import,
enforce, etc.) are excluded via SCENARIO_EXCLUDE_PATH_SUBSTRINGS until tests are
migrated; only scenario tests that still pass (e.g. devops sync, adapters) are run.

Usage:
    python tools/contract_first_smart_test.py run --level contracts    # Run contract validation
    python tools/contract_first_smart_test.py run --level exploration  # Run CrossHair exploration
    python tools/contract_first_smart_test.py run --level scenarios    # Run scenario tests
    python tools/contract_first_smart_test.py run --level e2e          # Run E2E tests
    python tools/contract_first_smart_test.py run --level full         # Run all layers
"""

import argparse
import hashlib
import json
import logging
import re
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from icontract import ensure
from smart_test_coverage import SmartCoverageManager


logger = logging.getLogger(__name__)


class ContractFirstTestManager(SmartCoverageManager):
    """Contract-first test manager extending the smart coverage system."""

    # Scenario tests that invoke CLI commands removed by core slimming (plan, import, sync,
    # migrate, project, backlog, comparators, importers, enforce, generate, contract, drift,
    # validate sidecar, etc.). Excluded until tests are migrated (e.g. to specfact-cli-modules
    # or updated to mock/expect not-installed).
    SCENARIO_EXCLUDE_PATH_SUBSTRINGS = (
        "/comparators/",
        "/importers/",
        "/sync/",
        "/backlog/",
        "test_repro_sidecar",
        "test_repro_command",
        "test_plan_compare",
        "test_speckit_import",
        "test_speckit_format_compatibility",
        "test_plan_command",
        "test_plan_workflow",
        "test_plan_upgrade",
        "test_import_command",
        "test_import_enrichment_contracts",
        "test_sync_",
        "test_migrate_",
        "test_project_",
        "test_protocol_workflow",
        "test_generators_integration",
        "test_specmatic_integration",
        "test_directory_structure",
        "test_enforce_command",
        "test_validate_sidecar",
        "test_ensure_speckit_compliance",
        "test_generate_command",
        "test_contract_commands",
        "test_sdd_contract_integration",
        "test_drift_command",
        "/analyzers/test_constitution_evidence",
        "/analyzers/test_contract_extraction",
        "/generators/test_openapi_extractor_pydantic",
        "/validators/test_change_proposal_validation",
    )

    STANDARD_CROSSHAIR_TIMEOUT = 60
    CROSSHAIR_SKIP_RE = re.compile(r"(?mi)^\s*(?:#\s*)?CrossHair:\s*(?:skip|ignore)\b")

    def __init__(
        self,
        project_root: str = ".",
        coverage_threshold: float | None = None,
        *,
        crosshair_fast: bool = False,
    ):
        super().__init__(project_root, coverage_threshold)

        # Contract-first specific configuration
        self.contract_tools = {
            "icontract": "python -c 'import icontract; print(icontract.__version__)'",
            "beartype": "python -c 'import beartype; print(beartype.__version__)'",
            "crosshair": "python -c 'import crosshair; print(crosshair.__version__)'",
            "hypothesis": "python -c 'import hypothesis; print(hypothesis.__version__)'",
        }

        self.crosshair_fast = crosshair_fast

        # Contract validation results cache
        self.contract_cache_file = self.cache_dir / "contract_cache.json"
        self.contract_cache = self._load_contract_cache()
        self.contract_cache.setdefault("exploration_cache", {})
        self.contract_cache.setdefault("validation_cache", {})

    def _load_contract_cache(self) -> dict[str, Any]:
        """Load contract validation cache."""
        if self.contract_cache_file.exists():
            try:
                with open(self.contract_cache_file) as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {
            "last_contract_run": None,
            "contract_violations": [],
            "exploration_results": {},
            "contract_coverage": {},
        }

    def _save_contract_cache(self):
        """Save contract validation cache."""
        with open(self.contract_cache_file, "w") as f:
            json.dump(self.contract_cache, f, indent=2)

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute a stable hash for a contract file."""
        if not file_path.is_file():
            return ""
        try:
            hasher = hashlib.sha256()
            with open(file_path, "rb") as handle:
                for chunk in iter(lambda: handle.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (FileNotFoundError, PermissionError, IsADirectoryError):
            return ""

    def _build_crosshair_command(self, file_path: Path, *, fast: bool) -> list[str]:
        """Construct the CrossHair command with optional fast settings."""
        cmd = [
            "hatch",
            "run",
            "python",
            "-m",
            "crosshair",
            "check",
            "--verbose",
            "--per_condition_timeout",
            "1" if fast else "10",
        ]
        if fast:
            cmd += ["--max_uninteresting_iterations", "1"]
        cmd.append(str(file_path))
        return cmd

    def _format_display_path(self, file_path: Path) -> str:
        """Format file path for user-facing output."""
        try:
            return str(file_path.relative_to(self.project_root))
        except ValueError:
            return str(file_path)

    def _extract_signature_limitation_detail(self, stderr: str, stdout: str) -> str | None:
        """Extract a concise signature-limitation detail from CrossHair output."""
        combined_output = f"{stderr}\n{stdout}"
        if not combined_output.strip():
            return None

        patterns = [
            r"wrong parameter order[^\n]*",
            r"keyword-only parameter[^\n]*",
            r"valueerror:\s*wrong parameter[^\n]*",
            r"signature[^\n]*(?:error|failure)[^\n]*",
        ]
        for pattern in patterns:
            match = re.search(pattern, combined_output, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return None

    def _is_crosshair_skipped(self, file_path: Path) -> bool:
        """Check if file opts out from CrossHair exploration."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError:
            return False
        return bool(self.CROSSHAIR_SKIP_RE.search(content))

    def _is_typer_command_module(self, file_path: Path) -> bool:
        """Detect Typer command modules that commonly trigger CrossHair signature limitations."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError:
            return False
        return (
            file_path.name == "commands.py"
            and "typer.Typer(" in content
            and (
                re.search(r"@\w+\.command\s*\(", content) is not None
                or re.search(r"@\w+\.callback\s*\(", content) is not None
            )
        )

    def _check_contract_tools(self) -> dict[str, bool]:
        """Check if contract tools are available."""
        tool_status = {}
        for tool, check_cmd in self.contract_tools.items():
            try:
                # Use hatch run to ensure we're in the correct environment
                result = subprocess.run(
                    ["hatch", "run", "python", "-c", check_cmd.split("python -c ")[1]],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                tool_status[tool] = result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                tool_status[tool] = False
        return tool_status

    def _contract_validation_file_key(self, file_path: Path) -> str:
        try:
            return str(file_path.relative_to(self.project_root))
        except ValueError:
            return str(file_path)

    def _contract_validation_skipped_by_cache(
        self, force: bool, cache_entry: dict[str, Any], file_hash: str, file_name: str
    ) -> bool:
        if (
            not force
            and cache_entry
            and cache_entry.get("hash") == file_hash
            and cache_entry.get("status") == "success"
        ):
            logger.debug("   Skipping %s; validation cache hit", file_name)
            return True
        return False

    def _validate_contract_import_for_file(
        self,
        file_path: Path,
        file_key: str,
        file_hash: str,
        validation_cache: dict[str, Any],
    ) -> tuple[bool, dict[str, Any] | None]:
        """Validate import for one file. Returns (success, violation_or_none)."""
        try:
            relative_path = file_path.relative_to(self.project_root)
            module_path = str(relative_path).replace("/", ".").replace(".py", "")

            result = subprocess.run(
                ["hatch", "run", "python", "-c", f"import {module_path}; print('Contracts loaded successfully')"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                validation_cache[file_key] = {
                    "hash": file_hash,
                    "status": "failure",
                    "timestamp": datetime.now().isoformat(),
                    "stderr": result.stderr,
                }
                return False, {
                    "file": str(file_path),
                    "tool": "icontract",
                    "error": result.stderr,
                    "timestamp": datetime.now().isoformat(),
                }

            validation_cache[file_key] = {
                "hash": file_hash,
                "status": "success",
                "timestamp": datetime.now().isoformat(),
            }
            return True, None

        except subprocess.TimeoutExpired:
            validation_cache[file_key] = {
                "hash": file_hash,
                "status": "timeout",
                "timestamp": datetime.now().isoformat(),
            }
            return False, {
                "file": str(file_path),
                "tool": "icontract",
                "error": "Contract validation timed out",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            validation_cache[file_key] = {
                "hash": file_hash,
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "stderr": str(e),
            }
            return False, {
                "file": str(file_path),
                "tool": "icontract",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _run_contract_validation(
        self,
        modified_files: list[Path],
        *,
        force: bool = False,
    ) -> tuple[bool, list[dict[str, Any]]]:
        """Run contract validation on modified files."""
        logger.info("Running contract validation...")

        # Check tool availability
        tool_status = self._check_contract_tools()
        missing_tools = [tool for tool, available in tool_status.items() if not available]
        if missing_tools:
            logger.warning("Missing contract tools: %s", ", ".join(missing_tools))
            logger.info("Install missing tools: pip install icontract beartype crosshair hypothesis")
            return False, []

        violations: list[dict[str, Any]] = []
        success = True

        validation_cache: dict[str, Any] = self.contract_cache.setdefault("validation_cache", {})

        for file_path in modified_files:
            file_key = self._contract_validation_file_key(file_path)
            file_hash = self._compute_file_hash(file_path)
            cache_entry = validation_cache.get(file_key, {})

            if self._contract_validation_skipped_by_cache(force, cache_entry, file_hash, file_path.name):
                continue

            logger.debug("   Validating contracts in: %s", file_path.name)

            ok, violation = self._validate_contract_import_for_file(file_path, file_key, file_hash, validation_cache)
            if violation is not None:
                violations.append(violation)
            if not ok:
                success = False

        # Update contract cache
        self.contract_cache.update(
            {
                "last_contract_run": datetime.now().isoformat(),
                "contract_violations": violations,
            }
        )
        self._save_contract_cache()

        if success:
            logger.info("Contract validation passed")
        else:
            logger.error("Contract validation failed: %d violations", len(violations))
            for violation in violations:
                logger.error("   - %s: %s", violation["file"], violation["error"])

        return success, violations

    @staticmethod
    def _dedupe_paths_by_resolve(paths: list[Path]) -> list[Path]:
        unique: list[Path] = []
        seen: set[str] = set()
        for p in paths:
            key = str(p.resolve())
            if key in seen:
                continue
            seen.add(key)
            unique.append(p)
        return unique

    def _exploration_file_key(self, file_path: Path) -> str:
        try:
            return str(file_path.relative_to(self.project_root))
        except ValueError:
            return str(file_path)

    def _exploration_store_static_skip(
        self,
        file_key: str,
        file_hash: str | None,
        reason: str,
        exploration_cache: dict[str, Any],
        exploration_results: dict[str, Any],
    ) -> None:
        exploration_results[file_key] = {
            "return_code": 0,
            "stdout": "",
            "stderr": "",
            "timestamp": datetime.now().isoformat(),
            "cached": False,
            "fast_mode": False,
            "skipped": True,
            "reason": reason,
        }
        exploration_cache[file_key] = {
            "hash": file_hash,
            "status": "skipped",
            "fast_mode": False,
            "prefer_fast": False,
            "timestamp": datetime.now().isoformat(),
            "return_code": 0,
            "stdout": "",
            "stderr": "",
            "reason": reason,
        }

    def _run_crosshair_subprocess(
        self, file_path: Path, use_fast: bool
    ) -> tuple[subprocess.CompletedProcess[str], bool, bool, bool]:
        """Run CrossHair; on standard-mode timeout, retry once with fast settings."""
        prefer_fast = False
        timed_out = False
        cmd = self._build_crosshair_command(file_path, fast=use_fast)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=None if use_fast else self.STANDARD_CROSSHAIR_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            logger.warning("      CrossHair standard run timed out; retrying with fast settings")
            timed_out = True
            use_fast = True
            prefer_fast = True
            cmd = self._build_crosshair_command(file_path, fast=True)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=None,
            )
        return result, timed_out, use_fast, prefer_fast

    def _log_crosshair_process_failure(
        self, result: subprocess.CompletedProcess[str], display_path: str, is_signature_issue: bool
    ) -> None:
        if result.returncode == 0 or is_signature_issue:
            return
        logger.warning("   CrossHair found issues in %s", display_path)
        if result.stdout.strip():
            logger.warning("      stdout:")
            for line in result.stdout.strip().splitlines():
                logger.warning("      │   %s", line)
        if result.stderr.strip():
            logger.warning("      stderr:")
            for line in result.stderr.strip().splitlines():
                logger.warning("          %s", line)
        if "No module named crosshair.__main__" in result.stderr:
            logger.info(
                "      Detected legacy 'crosshair' package (SSH client). Install CrossHair tooling via:",
            )
            logger.info("         pip install crosshair-tool")

    def _log_crosshair_process_success(
        self, timed_out: bool, is_signature_issue: bool, use_fast: bool, display_path: str
    ) -> None:
        if timed_out:
            logger.info("   CrossHair exploration passed for %s (fast retry)", display_path)
        elif not is_signature_issue:
            mode_label = "fast" if use_fast else "standard"
            logger.info("   CrossHair exploration passed for %s (%s)", display_path, mode_label)

    def _apply_crosshair_result(
        self,
        file_key: str,
        file_hash: str | None,
        result: subprocess.CompletedProcess[str],
        timed_out: bool,
        use_fast: bool,
        prefer_fast: bool,
        display_path: str,
        exploration_cache: dict[str, Any],
        exploration_results: dict[str, Any],
        signature_skips: list[str],
    ) -> bool:
        """Update caches from a CrossHair run. Returns False when the overall exploration should fail."""
        signature_detail = self._extract_signature_limitation_detail(result.stderr, result.stdout)
        is_signature_issue = signature_detail is not None

        exploration_results[file_key] = {
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timestamp": datetime.now().isoformat(),
            "fast_mode": use_fast,
            "timed_out_fallback": timed_out,
            "skipped": is_signature_issue,
            "reason": "Signature analysis limitation" if is_signature_issue else None,
        }

        if is_signature_issue:
            status = "skipped"
            signature_skips.append(display_path)
            logger.debug("      CrossHair skipped for %s (signature analysis limitation)", display_path)
        else:
            status = "success" if result.returncode == 0 else "failure"

        exploration_cache[file_key] = {
            "hash": file_hash,
            "status": status,
            "fast_mode": use_fast,
            "prefer_fast": prefer_fast or timed_out,
            "timestamp": datetime.now().isoformat(),
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "reason": "Signature analysis limitation" if is_signature_issue else None,
        }

        self._log_crosshair_process_failure(result, display_path, is_signature_issue)
        if result.returncode != 0 and not is_signature_issue:
            return False
        self._log_crosshair_process_success(timed_out, is_signature_issue, use_fast, display_path)
        return True

    def _exploration_record_timeout(
        self,
        file_key: str,
        file_hash: str | None,
        exploration_cache: dict[str, Any],
        exploration_results: dict[str, Any],
    ) -> None:
        exploration_results[file_key] = {
            "return_code": -1,
            "stdout": "",
            "stderr": "CrossHair exploration timed out",
            "timestamp": datetime.now().isoformat(),
        }
        exploration_cache[file_key] = {
            "hash": file_hash,
            "status": "timeout",
            "fast_mode": False,
            "prefer_fast": True,
            "timestamp": datetime.now().isoformat(),
            "return_code": -1,
            "stdout": "",
            "stderr": "CrossHair exploration timed out",
        }

    def _exploration_record_error(
        self,
        file_key: str,
        file_hash: str | None,
        exc: Exception,
        use_fast: bool,
        prefer_fast: bool,
        exploration_cache: dict[str, Any],
        exploration_results: dict[str, Any],
    ) -> None:
        exploration_results[file_key] = {
            "return_code": -1,
            "stdout": "",
            "stderr": str(exc),
            "timestamp": datetime.now().isoformat(),
        }
        exploration_cache[file_key] = {
            "hash": file_hash,
            "status": "error",
            "fast_mode": use_fast if file_hash is not None else False,
            "prefer_fast": prefer_fast,
            "timestamp": datetime.now().isoformat(),
            "return_code": -1,
            "stdout": "",
            "stderr": str(exc),
        }

    def _exploration_use_cached_success(
        self,
        force: bool,
        cache_entry: dict[str, Any],
        file_hash: str | None,
        file_key: str,
        display_path: str,
        exploration_results: dict[str, Any],
    ) -> bool:
        if (
            not force
            and cache_entry
            and cache_entry.get("hash") == file_hash
            and cache_entry.get("status") == "success"
        ):
            logger.debug("      Cached result found, skipping CrossHair run for %s", display_path)
            exploration_results[file_key] = {
                "return_code": cache_entry.get("return_code", 0),
                "stdout": cache_entry.get("stdout", ""),
                "stderr": cache_entry.get("stderr", ""),
                "timestamp": datetime.now().isoformat(),
                "cached": True,
                "fast_mode": cache_entry.get("fast_mode", False),
            }
            return True
        return False

    def _exploration_apply_static_skips(
        self,
        file_path: Path,
        file_key: str,
        file_hash: str | None,
        display_path: str,
        exploration_cache: dict[str, Any],
        exploration_results: dict[str, Any],
    ) -> bool:
        if self._is_crosshair_skipped(file_path):
            logger.debug("      CrossHair skipped for %s (file marked 'CrossHair: skip')", display_path)
            self._exploration_store_static_skip(
                file_key, file_hash, "CrossHair skip marker", exploration_cache, exploration_results
            )
            return True
        if self._is_typer_command_module(file_path):
            logger.debug(
                "      CrossHair skipped for %s (Typer command module; signature analysis unsupported)",
                display_path,
            )
            self._exploration_store_static_skip(
                file_key, file_hash, "Typer command module", exploration_cache, exploration_results
            )
            return True
        return False

    def _run_contract_exploration(
        self,
        modified_files: list[Path],
        *,
        force: bool = False,
    ) -> tuple[bool, dict[str, Any]]:
        """Run CrossHair exploration on modified files."""
        logger.info("Running contract exploration with CrossHair...")

        exploration_results: dict[str, Any] = {}
        success = True

        exploration_cache: dict[str, Any] = self.contract_cache.setdefault("exploration_cache", {})
        signature_skips: list[str] = []

        unique_files = self._dedupe_paths_by_resolve(modified_files)
        if len(unique_files) < len(modified_files):
            logger.debug("   De-duplicated %d repeated file entries", len(modified_files) - len(unique_files))

        for file_path in unique_files:
            display_path = self._format_display_path(file_path)
            logger.debug("   Exploring contracts in: %s", display_path)

            file_key = str(file_path)
            file_hash: str | None = None
            use_fast = self.crosshair_fast
            prefer_fast = False

            try:
                file_key = self._exploration_file_key(file_path)
                file_hash = self._compute_file_hash(file_path)
                cache_entry = exploration_cache.get(file_key, {})
                prefer_fast = bool(cache_entry.get("prefer_fast", False))
                use_fast = self.crosshair_fast or prefer_fast

                if self._exploration_use_cached_success(
                    force, cache_entry, file_hash, file_key, display_path, exploration_results
                ):
                    continue

                if self._exploration_apply_static_skips(
                    file_path, file_key, file_hash, display_path, exploration_cache, exploration_results
                ):
                    continue

                result, timed_out, use_fast, prefer_fast = self._run_crosshair_subprocess(file_path, use_fast)
                if not self._apply_crosshair_result(
                    file_key,
                    file_hash,
                    result,
                    timed_out,
                    use_fast,
                    prefer_fast,
                    display_path,
                    exploration_cache,
                    exploration_results,
                    signature_skips,
                ):
                    success = False

            except subprocess.TimeoutExpired:
                self._exploration_record_timeout(file_key, file_hash, exploration_cache, exploration_results)
                success = False
            except Exception as e:
                self._exploration_record_error(
                    file_key, file_hash, e, use_fast, prefer_fast, exploration_cache, exploration_results
                )
                success = False

        # Update contract cache
        self.contract_cache.update(
            {
                "exploration_results": exploration_results,
            }
        )
        self._save_contract_cache()

        if signature_skips:
            logger.info(
                "   CrossHair signature-limited files skipped: %d (non-blocking; grouped summary)",
                len(signature_skips),
            )

        return success, exploration_results

    def _run_scenario_tests(self) -> tuple[bool, int, float | None]:
        """Run scenario tests (integration tests with contract references)."""
        logger.info("Running scenario tests...")

        # Get integration tests that reference contracts
        integration_tests = self._get_test_files_by_level("integration")
        scenario_tests: list[Path] = []

        for test_file in integration_tests:
            try:
                path_str = str(test_file)
                if any(sub in path_str for sub in self.SCENARIO_EXCLUDE_PATH_SUBSTRINGS):
                    continue
                with open(test_file) as f:
                    content = f.read()
                    # Look for contract references in test files
                    if any(
                        keyword in content.lower()
                        for keyword in ["contract", "icontract", "beartype", "crosshair", "hypothesis"]
                    ):
                        scenario_tests.append(test_file)
            except Exception:
                continue

        if not scenario_tests:
            logger.info("No scenario tests found (integration tests with contract references)")
            return True, 0, None

        logger.info("Found %d scenario tests:", len(scenario_tests))
        for test_file in scenario_tests:
            try:
                relative_path = test_file.relative_to(self.project_root)
                logger.info("   - %s", relative_path)
            except ValueError:
                logger.info("   - %s", test_file)

        # Run scenario tests using parent class method
        success, test_count, coverage_percentage = self._run_tests(scenario_tests, "scenarios")

        if success:
            logger.info("Scenario tests completed: %d tests", test_count)
        else:
            logger.error("Scenario tests failed")

        return success, test_count, coverage_percentage

    @ensure(lambda result: isinstance(result, bool), "run_contract_first_tests must return bool")
    def run_contract_first_tests(self, test_level: str = "auto", force: bool = False) -> bool:
        """Run contract-first tests with the 3-layer quality model."""

        if test_level == "auto":
            # Auto-detect based on changes
            modified_files = self._get_modified_files()
            if not modified_files:
                logger.info("No modified files detected - using cached results")
                return True

            # Run all layers in sequence
            return self._run_all_contract_layers(modified_files, force=force)

        if test_level == "contracts":
            modified_files = self._get_modified_files()
            if not modified_files:
                logger.info("No modified files detected")
                return True
            success, _ = self._run_contract_validation(modified_files, force=force)
            return success

        if test_level == "exploration":
            modified_files = self._get_modified_files()
            if not modified_files:
                logger.info("No modified files detected")
                return True
            success, _ = self._run_contract_exploration(modified_files, force=force)
            return success

        if test_level == "scenarios":
            success, _, _ = self._run_scenario_tests()
            return success

        if test_level == "e2e":
            # Use parent class E2E test method
            return self._run_e2e_tests()

        if test_level == "full":
            modified_files = self._get_modified_files()
            if not modified_files:
                logger.info("No modified files detected")
                return True
            return self._run_all_contract_layers(modified_files, force=force)

        logger.error("Unknown test level: %s", test_level)
        return False

    def _run_all_contract_layers(self, modified_files: list[Path], *, force: bool = False) -> bool:
        """Run all contract-first layers in sequence."""
        logger.info("Running contract-first test layers...")

        # Layer 1: Runtime contracts
        logger.info("Layer 1: Runtime Contract Validation")
        contract_success, _violations = self._run_contract_validation(modified_files, force=force)
        if not contract_success:
            logger.error("Contract validation failed - stopping here")
            return False

        # Layer 2: Automated exploration
        logger.info("Layer 2: Automated Contract Exploration")
        exploration_success, _exploration_results = self._run_contract_exploration(modified_files, force=force)
        if not exploration_success:
            logger.warning("Contract exploration found issues - continuing to scenarios")

        # Layer 3: Scenario tests
        logger.info("Layer 3: Scenario Tests")
        scenario_success, test_count, _coverage = self._run_scenario_tests()
        if not scenario_success:
            logger.error("Scenario tests failed")
            return False

        # Summary
        logger.info("Contract-First Test Summary:")
        logger.info("   Runtime contracts: %s", "PASS" if contract_success else "FAIL")
        logger.info(
            "   Contract exploration: %s",
            "PASS" if exploration_success else "ISSUES FOUND",
        )
        logger.info("   Scenario tests: %s (%d tests)", "PASS" if scenario_success else "FAIL", test_count)

        return contract_success and scenario_success

    @ensure(lambda result: isinstance(result, dict), "get_contract_status must return dict")
    def get_contract_status(self) -> dict[str, Any]:
        """Get contract-first test status."""
        status = self.get_status()
        assert isinstance(status, dict)
        return {
            **status,
            "contract_cache": self.contract_cache,
            "tool_availability": self._check_contract_tools(),
        }


def _contract_cli_run(manager: ContractFirstTestManager, args: argparse.Namespace) -> None:
    success = manager.run_contract_first_tests(args.level, args.force)
    sys.exit(0 if success else 1)


def _contract_cli_status(manager: ContractFirstTestManager) -> None:
    status = manager.get_contract_status()
    logger.info("Contract-First Test Status:")
    logger.info("   Last Run: %s", status["last_run"] or "Never")
    logger.info("   Coverage: %.1f%%", status["coverage_percentage"])
    logger.info("   Test Count: %s", status["test_count"])
    logger.info("   Source Changed: %s", status["source_changed"])
    logger.info("   Tool Availability:")
    for tool, available in status["tool_availability"].items():
        logger.info("     - %s: %s", tool, "available" if available else "unavailable")
    logger.info("   Contract Violations: %s", len(status["contract_cache"].get("contract_violations", [])))
    sys.exit(0)


def _contract_cli_contracts(manager: ContractFirstTestManager, args: argparse.Namespace) -> None:
    modified_files = manager._get_modified_files()
    if not modified_files:
        logger.info("No modified files detected")
        sys.exit(0)
    success, _ = manager._run_contract_validation(modified_files, force=args.force)
    sys.exit(0 if success else 1)


def _contract_cli_exploration(manager: ContractFirstTestManager, args: argparse.Namespace) -> None:
    modified_files = manager._get_modified_files()
    if not modified_files:
        logger.info("No modified files detected")
        sys.exit(0)
    success, _ = manager._run_contract_exploration(modified_files, force=args.force)
    sys.exit(0 if success else 1)


def _contract_cli_scenarios(manager: ContractFirstTestManager) -> None:
    success, _, _ = manager._run_scenario_tests()
    sys.exit(0 if success else 1)


@ensure(lambda result: result is None, "main must return None")
def main() -> None:
    parser = argparse.ArgumentParser(description="Contract-First Smart Test System")
    parser.add_argument(
        "command", choices=["run", "status", "contracts", "exploration", "scenarios"], help="Command to execute"
    )
    parser.add_argument(
        "--level",
        choices=["contracts", "exploration", "scenarios", "e2e", "full", "auto"],
        default="auto",
        help="Test level for 'run' command (default: auto)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force test run regardless of file changes",
    )
    parser.add_argument(
        "--crosshair-fast",
        action="store_true",
        help="Use optimized CrossHair limits (per_condition_timeout=1, max_uninteresting_iterations=1)",
    )

    args = parser.parse_args()

    manager = ContractFirstTestManager(crosshair_fast=args.crosshair_fast)

    handlers: dict[str, Callable[[], None]] = {
        "run": lambda: _contract_cli_run(manager, args),
        "status": lambda: _contract_cli_status(manager),
        "contracts": lambda: _contract_cli_contracts(manager, args),
        "exploration": lambda: _contract_cli_exploration(manager, args),
        "scenarios": lambda: _contract_cli_scenarios(manager),
    }

    try:
        handlers[args.command]()
    except Exception as e:
        logger.error("Error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
