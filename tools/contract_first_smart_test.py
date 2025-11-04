#!/usr/bin/env python3
"""
Contract-First Smart Test System

This system implements the 3-layer contract-first quality model:
1. Runtime contracts (icontract + beartype)
2. Automated exploration (CrossHair + Hypothesis)
3. Scenario/E2E tests (business workflow validation)

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
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from smart_test_coverage import SmartCoverageManager


class ContractFirstTestManager(SmartCoverageManager):
    """Contract-first test manager extending the smart coverage system."""

    STANDARD_CROSSHAIR_TIMEOUT = 60

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
        hasher = hashlib.sha256()
        with open(file_path, "rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

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

    def _run_contract_validation(
        self,
        modified_files: list[Path],
        *,
        force: bool = False,
    ) -> tuple[bool, list[dict[str, Any]]]:
        """Run contract validation on modified files."""
        print("🔍 Running contract validation...")

        # Check tool availability
        tool_status = self._check_contract_tools()
        missing_tools = [tool for tool, available in tool_status.items() if not available]
        if missing_tools:
            print(f"⚠️  Missing contract tools: {', '.join(missing_tools)}")
            print("💡 Install missing tools: pip install icontract beartype crosshair hypothesis")
            return False, []

        violations = []
        success = True

        validation_cache: dict[str, Any] = self.contract_cache.setdefault("validation_cache", {})

        for file_path in modified_files:
            try:
                relative_path = file_path.relative_to(self.project_root)
                file_key = str(relative_path)
            except ValueError:
                file_key = str(file_path)

            file_hash = self._compute_file_hash(file_path)
            cache_entry = validation_cache.get(file_key, {})

            if (
                not force
                and cache_entry
                and cache_entry.get("hash") == file_hash
                and cache_entry.get("status") == "success"
            ):
                print(f"   ⏭️  Skipping {file_path.name}; validation cache hit")
                continue

            print(f"   Validating contracts in: {file_path.name}")

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
                    violations.append(
                        {
                            "file": str(file_path),
                            "tool": "icontract",
                            "error": result.stderr,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                    validation_cache[file_key] = {
                        "hash": file_hash,
                        "status": "failure",
                        "timestamp": datetime.now().isoformat(),
                        "stderr": result.stderr,
                    }
                    success = False
                else:
                    validation_cache[file_key] = {
                        "hash": file_hash,
                        "status": "success",
                        "timestamp": datetime.now().isoformat(),
                    }

            except subprocess.TimeoutExpired:
                violations.append(
                    {
                        "file": str(file_path),
                        "tool": "icontract",
                        "error": "Contract validation timed out",
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                validation_cache[file_key] = {
                    "hash": file_hash,
                    "status": "timeout",
                    "timestamp": datetime.now().isoformat(),
                }
                success = False
            except Exception as e:
                violations.append(
                    {
                        "file": str(file_path),
                        "tool": "icontract",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                validation_cache[file_key] = {
                    "hash": file_hash,
                    "status": "error",
                    "timestamp": datetime.now().isoformat(),
                    "stderr": str(e),
                }
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
            print("✅ Contract validation passed")
        else:
            print(f"❌ Contract validation failed: {len(violations)} violations")
            for violation in violations:
                print(f"   - {violation['file']}: {violation['error']}")

        return success, violations

    def _run_contract_exploration(
        self,
        modified_files: list[Path],
        *,
        force: bool = False,
    ) -> tuple[bool, dict[str, Any]]:
        """Run CrossHair exploration on modified files."""
        print("🔍 Running contract exploration with CrossHair...")

        exploration_results = {}
        success = True

        exploration_cache: dict[str, Any] = self.contract_cache.setdefault("exploration_cache", {})

        for file_path in modified_files:
            print(f"   Exploring contracts in: {file_path.name}")

            file_key = str(file_path)
            file_hash: str | None = None
            use_fast = self.crosshair_fast
            prefer_fast = False

            try:
                try:
                    relative_path = file_path.relative_to(self.project_root)
                    file_key = str(relative_path)
                except ValueError:
                    file_key = str(file_path)

                file_hash = self._compute_file_hash(file_path)
                cache_entry = exploration_cache.get(file_key, {})
                prefer_fast = bool(cache_entry.get("prefer_fast", False))
                use_fast = self.crosshair_fast or prefer_fast

                if (
                    not force
                    and cache_entry
                    and cache_entry.get("hash") == file_hash
                    and cache_entry.get("status") == "success"
                ):
                    print("      ⏭️  Cached result found, skipping CrossHair run")
                    exploration_results[file_key] = {
                        "return_code": cache_entry.get("return_code", 0),
                        "stdout": cache_entry.get("stdout", ""),
                        "stderr": cache_entry.get("stderr", ""),
                        "timestamp": datetime.now().isoformat(),
                        "cached": True,
                        "fast_mode": cache_entry.get("fast_mode", False),
                    }
                    continue

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
                    print("      ⏳ CrossHair standard run timed out; retrying with fast settings")
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

                exploration_results[file_key] = {
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "timestamp": datetime.now().isoformat(),
                    "fast_mode": use_fast,
                    "timed_out_fallback": timed_out,
                }

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
                }

                if result.returncode != 0:
                    print(f"   ⚠️  CrossHair found issues in {file_path.name}")
                    if result.stdout.strip():
                        print("      ├─ stdout:")
                        for line in result.stdout.strip().splitlines():
                            print(f"      │   {line}")
                    if result.stderr.strip():
                        print("      └─ stderr:")
                        for line in result.stderr.strip().splitlines():
                            print(f"          {line}")

                    if "No module named crosshair.__main__" in result.stderr:
                        print(
                            "      ℹ️  Detected legacy 'crosshair' package (SSH client). Install CrossHair tooling via:"
                        )
                        print("         pip install crosshair-tool")

                    success = False
                else:
                    if timed_out:
                        print(f"   ✅ CrossHair exploration passed for {file_path.name} (fast retry)")
                    else:
                        mode_label = "fast" if use_fast else "standard"
                        print(f"   ✅ CrossHair exploration passed for {file_path.name} ({mode_label})")

            except subprocess.TimeoutExpired:
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
                success = False
            except Exception as e:
                exploration_results[file_key] = {
                    "return_code": -1,
                    "stdout": "",
                    "stderr": str(e),
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
                    "stderr": str(e),
                }
                success = False

        # Update contract cache
        self.contract_cache.update(
            {
                "exploration_results": exploration_results,
            }
        )
        self._save_contract_cache()

        return success, exploration_results

    def _run_scenario_tests(self) -> tuple[bool, int, float]:
        """Run scenario tests (integration tests with contract references)."""
        print("🔗 Running scenario tests...")

        # Get integration tests that reference contracts
        integration_tests = self._get_test_files_by_level("integration")
        scenario_tests = []

        for test_file in integration_tests:
            try:
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
            print("ℹ️  No scenario tests found (integration tests with contract references)")
            return True, 0, 100.0

        print(f"📋 Found {len(scenario_tests)} scenario tests:")
        for test_file in scenario_tests:
            try:
                relative_path = test_file.relative_to(self.project_root)
                print(f"   - {relative_path}")
            except ValueError:
                print(f"   - {test_file}")

        # Run scenario tests using parent class method
        success, test_count, coverage_percentage = self._run_tests(scenario_tests, "scenarios")

        if success:
            print(f"✅ Scenario tests completed: {test_count} tests")
        else:
            print("❌ Scenario tests failed")

        return success, test_count, coverage_percentage

    def run_contract_first_tests(self, test_level: str = "auto", force: bool = False) -> bool:
        """Run contract-first tests with the 3-layer quality model."""

        if test_level == "auto":
            # Auto-detect based on changes
            modified_files = self._get_modified_files()
            if not modified_files:
                print("ℹ️  No modified files detected - using cached results")
                return True

            # Run all layers in sequence
            return self._run_all_contract_layers(modified_files, force=force)

        if test_level == "contracts":
            modified_files = self._get_modified_files()
            if not modified_files:
                print("ℹ️  No modified files detected")
                return True
            success, _ = self._run_contract_validation(modified_files, force=force)
            return success

        if test_level == "exploration":
            modified_files = self._get_modified_files()
            if not modified_files:
                print("ℹ️  No modified files detected")
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
                print("ℹ️  No modified files detected")
                return True
            return self._run_all_contract_layers(modified_files, force=force)

        print(f"❌ Unknown test level: {test_level}")
        return False

    def _run_all_contract_layers(self, modified_files: list[Path], *, force: bool = False) -> bool:
        """Run all contract-first layers in sequence."""
        print("🚀 Running contract-first test layers...")

        # Layer 1: Runtime contracts
        print("\n📋 Layer 1: Runtime Contract Validation")
        contract_success, violations = self._run_contract_validation(modified_files, force=force)
        if not contract_success:
            print("❌ Contract validation failed - stopping here")
            return False

        # Layer 2: Automated exploration
        print("\n🔍 Layer 2: Automated Contract Exploration")
        exploration_success, exploration_results = self._run_contract_exploration(modified_files, force=force)
        if not exploration_success:
            print("⚠️  Contract exploration found issues - continuing to scenarios")

        # Layer 3: Scenario tests
        print("\n🔗 Layer 3: Scenario Tests")
        scenario_success, test_count, coverage = self._run_scenario_tests()
        if not scenario_success:
            print("❌ Scenario tests failed")
            return False

        # Summary
        print("\n📊 Contract-First Test Summary:")
        print(f"   ✅ Runtime contracts: {'PASS' if contract_success else 'FAIL'}")
        print(
            f"   {'✅' if exploration_success else '⚠️ '} Contract exploration: {'PASS' if exploration_success else 'ISSUES FOUND'}"
        )
        print(f"   ✅ Scenario tests: {'PASS' if scenario_success else 'FAIL'} ({test_count} tests)")

        return contract_success and scenario_success

    def get_contract_status(self) -> dict[str, Any]:
        """Get contract-first test status."""
        status = self.get_status()
        contract_status = {
            **status,
            "contract_cache": self.contract_cache,
            "tool_availability": self._check_contract_tools(),
        }
        return contract_status


def main():
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

    try:
        if args.command == "run":
            success = manager.run_contract_first_tests(args.level, args.force)
            sys.exit(0 if success else 1)

        elif args.command == "status":
            status = manager.get_contract_status()
            print("📊 Contract-First Test Status:")
            print(f"   Last Run: {status['last_run'] or 'Never'}")
            print(f"   Coverage: {status['coverage_percentage']:.1f}%")
            print(f"   Test Count: {status['test_count']}")
            print(f"   Source Changed: {status['source_changed']}")
            print("   Tool Availability:")
            for tool, available in status["tool_availability"].items():
                print(f"     - {tool}: {'✅' if available else '❌'}")
            print(f"   Contract Violations: {len(status['contract_cache'].get('contract_violations', []))}")
            sys.exit(0)

        elif args.command == "contracts":
            modified_files = manager._get_modified_files()
            if not modified_files:
                print("ℹ️  No modified files detected")
                sys.exit(0)
            success, _ = manager._run_contract_validation(modified_files, force=args.force)
            sys.exit(0 if success else 1)

        elif args.command == "exploration":
            modified_files = manager._get_modified_files()
            if not modified_files:
                print("ℹ️  No modified files detected")
                sys.exit(0)
            success, _ = manager._run_contract_exploration(modified_files, force=args.force)
            sys.exit(0 if success else 1)

        elif args.command == "scenarios":
            success, _, _ = manager._run_scenario_tests()
            sys.exit(0 if success else 1)

        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
