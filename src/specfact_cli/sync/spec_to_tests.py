"""
Spec-to-tests sync - Generate tests via Specmatic.

This module provides utilities for generating tests from OpenAPI contracts
using Specmatic flows (not LLM guessing).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from beartype import beartype
from icontract import ensure, require

from specfact_cli.sync.change_detector import SpecChange


class SpecToTestsSync:
    """Sync specification changes to tests using Specmatic."""

    def __init__(self, bundle_name: str, repo_path: Path) -> None:
        """
        Initialize spec-to-tests sync.

        Args:
            bundle_name: Project bundle name
            repo_path: Path to repository root
        """
        self.bundle_name = bundle_name
        self.repo_path = repo_path.resolve()

    @beartype
    @require(lambda self, changes: isinstance(changes, list), "Changes must be list")
    @require(lambda self, changes: all(isinstance(c, SpecChange) for c in changes), "All items must be SpecChange")
    @require(lambda self, bundle_name: isinstance(bundle_name, str), "Bundle name must be string")
    @ensure(lambda result: result is None, "Must return None")
    def sync(self, changes: list[SpecChange], bundle_name: str) -> None:
        """
        Generate tests via Specmatic (not LLM).

        Args:
            changes: List of specification changes
            bundle_name: Project bundle name
        """
        from specfact_cli.integrations.specmatic import check_specmatic_available
        from specfact_cli.utils.bundle_loader import load_project_bundle
        from specfact_cli.utils.structure import SpecFactStructure

        # Check if Specmatic is available
        is_available, error_msg = check_specmatic_available()
        if not is_available:
            raise RuntimeError(f"Specmatic not available: {error_msg}")

        # Load project bundle to get contract paths
        bundle_dir = SpecFactStructure.project_dir(base_path=self.repo_path, bundle_name=bundle_name)
        project_bundle = load_project_bundle(bundle_dir)

        # Process each change
        for change in changes:
            feature = project_bundle.features.get(change.feature_key)
            if not feature or not feature.contract:
                continue

            contract_path = bundle_dir / feature.contract
            if not contract_path.exists():
                continue

            # Use Specmatic to generate tests
            try:
                subprocess.run(
                    [
                        "specmatic",
                        "test",
                        "--spec",
                        str(contract_path),
                        "--host",
                        "localhost:8000",
                    ],
                    check=True,
                    cwd=self.repo_path,
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Specmatic test generation failed: {e}") from e
            except FileNotFoundError:
                # Try with npx
                try:
                    subprocess.run(
                        [
                            "npx",
                            "--yes",
                            "specmatic",
                            "test",
                            "--spec",
                            str(contract_path),
                            "--host",
                            "localhost:8000",
                        ],
                        check=True,
                        cwd=self.repo_path,
                    )
                except subprocess.CalledProcessError as e:
                    raise RuntimeError(f"Specmatic test generation failed: {e}") from e
