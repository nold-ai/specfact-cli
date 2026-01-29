"""
Bridge-based bidirectional sync implementation.

This module provides adapter-agnostic bidirectional synchronization between
external tool artifacts and SpecFact project bundles using bridge configuration.
The sync layer reads bridge config, resolves paths dynamically, and delegates
to adapter-specific parsers/generators.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import tempfile
from dataclasses import dataclass
from urllib.parse import urlparse


try:
    from datetime import UTC, datetime
except ImportError:
    from datetime import datetime

    UTC = UTC  # type: ignore  # python3.10 backport of UTC
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require
from rich.progress import Progress
from rich.table import Table

from specfact_cli.adapters.registry import AdapterRegistry
from specfact_cli.models.bridge import AdapterType, BridgeConfig
from specfact_cli.runtime import get_configured_console
from specfact_cli.sync.bridge_probe import BridgeProbe
from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle
from specfact_cli.utils.terminal import get_progress_config


console = get_configured_console()


@dataclass
class SyncOperation:
    """Represents a sync operation (import or export)."""

    artifact_key: str  # Artifact key (e.g., "specification", "plan")
    feature_id: str  # Feature identifier (e.g., "001-auth")
    direction: str  # "import" or "export"
    bundle_name: str  # Project bundle name


@dataclass
class SyncResult:
    """Result of a bridge-based sync operation."""

    success: bool
    operations: list[SyncOperation]
    errors: list[str]
    warnings: list[str]


class BridgeSync:
    """
    Adapter-agnostic bidirectional sync using bridge configuration.

    This class provides generic sync functionality that works with any tool
    adapter by using bridge configuration to resolve paths dynamically.

    Note: All adapter-specific logic (import/export) is handled by adapters
    via the AdapterRegistry. This class does NOT contain hard-coded adapter
    checks. Future adapters (SpecKitAdapter, GenericMarkdownAdapter) should
    be created to move any remaining adapter-specific logic out of this class.
    """

    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    def __init__(self, repo_path: Path, bridge_config: BridgeConfig | None = None) -> None:
        """
        Initialize bridge sync.

        Args:
            repo_path: Path to repository root
            bridge_config: Bridge configuration (auto-detected if None)
        """
        self.repo_path = Path(repo_path).resolve()
        self.bridge_config = bridge_config

        if self.bridge_config is None:
            # Auto-detect and load bridge config
            self.bridge_config = self._load_or_generate_bridge_config()

    def _find_code_repo_path(self, repo_owner: str, repo_name: str) -> Path | None:
        """
        Find local path to code repository based on repo_owner and repo_name.

        Args:
            repo_owner: Repository owner (e.g., "nold-ai")
            repo_name: Repository name (e.g., "specfact-cli")

        Returns:
            Path to code repository if found, None otherwise
        """
        # Strategy 1: Check if current working directory is the code repository
        try:
            cwd = Path.cwd()
            if cwd.name == repo_name and (cwd / ".git").exists():
                # Verify it's the right repo by checking remote
                result = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if result.returncode == 0 and repo_name in result.stdout:
                    return cwd
        except Exception:
            pass

        # Strategy 2: Check parent directory (common structure: parent/repo-name)
        try:
            cwd = Path.cwd()
            parent = cwd.parent
            repo_path = parent / repo_name
            if repo_path.exists() and (repo_path / ".git").exists():
                return repo_path
        except Exception:
            pass

        # Strategy 3: Check sibling directories (common structure: sibling/repo-name)
        try:
            cwd = Path.cwd()
            grandparent = cwd.parent.parent if cwd.parent != Path("/") else None
            if grandparent:
                for sibling in grandparent.iterdir():
                    if sibling.is_dir() and sibling.name == repo_name and (sibling / ".git").exists():
                        return sibling
        except Exception:
            pass

        return None

    @beartype
    @ensure(lambda result: isinstance(result, BridgeConfig), "Must return BridgeConfig")
    def _load_or_generate_bridge_config(self) -> BridgeConfig:
        """
        Load bridge config from file or auto-generate if missing.

        Returns:
            BridgeConfig instance
        """
        from specfact_cli.utils.structure import SpecFactStructure

        bridge_path = self.repo_path / SpecFactStructure.CONFIG / "bridge.yaml"

        if bridge_path.exists():
            return BridgeConfig.load_from_file(bridge_path)

        # Auto-generate bridge config
        probe = BridgeProbe(self.repo_path)
        capabilities = probe.detect()
        bridge_config = probe.auto_generate_bridge(capabilities)
        probe.save_bridge_config(bridge_config, overwrite=False)
        return bridge_config

    @beartype
    @require(lambda self: self.bridge_config is not None, "Bridge config must be set")
    @require(lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0, "Bundle name must be non-empty")
    @require(lambda feature_id: isinstance(feature_id, str) and len(feature_id) > 0, "Feature ID must be non-empty")
    @ensure(lambda result: isinstance(result, Path), "Must return Path")
    def resolve_artifact_path(self, artifact_key: str, feature_id: str, bundle_name: str) -> Path:
        """
        Resolve artifact path using bridge configuration.

        Args:
            artifact_key: Artifact key (e.g., "specification", "plan")
            feature_id: Feature identifier (e.g., "001-auth")
            bundle_name: Project bundle name (for context)

        Returns:
            Resolved Path object
        """
        if self.bridge_config is None:
            msg = "Bridge config not initialized"
            raise ValueError(msg)

        base_path = self.repo_path
        if self.bridge_config.external_base_path is not None:
            base_path = self.bridge_config.external_base_path

        if artifact_key == "project_context" and self.bridge_config.adapter == AdapterType.OPENSPEC:
            config_yaml = base_path / "openspec" / "config.yaml"
            project_md = base_path / "openspec" / "project.md"
            if config_yaml.exists():
                return config_yaml
            if project_md.exists():
                return project_md
            return project_md

        context = {
            "feature_id": feature_id,
            "bundle_name": bundle_name,
        }
        return self.bridge_config.resolve_path(artifact_key, context, base_path=self.repo_path)

    @beartype
    @require(lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0, "Bundle name must be non-empty")
    @require(lambda feature_id: isinstance(feature_id, str) and len(feature_id) > 0, "Feature ID must be non-empty")
    @ensure(lambda result: isinstance(result, SyncResult), "Must return SyncResult")
    def import_artifact(
        self,
        artifact_key: str,
        feature_id: str,
        bundle_name: str,
        persona: str | None = None,
    ) -> SyncResult:
        """
        Import artifact from tool format to SpecFact project bundle.

        Args:
            artifact_key: Artifact key (e.g., "specification", "plan")
            feature_id: Feature identifier (e.g., "001-auth")
            bundle_name: Project bundle name
            persona: Persona for ownership validation (optional)

        Returns:
            SyncResult with operation details
        """
        operations: list[SyncOperation] = []
        errors: list[str] = []
        warnings: list[str] = []

        if self.bridge_config is None:
            errors.append("Bridge config not initialized")
            return SyncResult(success=False, operations=operations, errors=errors, warnings=warnings)

        try:
            # Resolve artifact path
            artifact_path = self.resolve_artifact_path(artifact_key, feature_id, bundle_name)

            if not artifact_path.exists():
                errors.append(f"Artifact not found: {artifact_path}")
                return SyncResult(success=False, operations=operations, errors=errors, warnings=warnings)

            # Conflict detection: warn that bundle will be updated
            warnings.append(
                f"Importing {artifact_key} from {artifact_path}. "
                "This will update the project bundle. Existing bundle content may be modified."
            )

            # Load project bundle
            from specfact_cli.utils.structure import SpecFactStructure

            bundle_dir = self.repo_path / SpecFactStructure.PROJECTS / bundle_name
            if not bundle_dir.exists():
                errors.append(f"Project bundle not found: {bundle_dir}")
                return SyncResult(success=False, operations=operations, errors=errors, warnings=warnings)

            project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)

            # Get adapter from registry (universal pattern - no hard-coded checks)
            adapter = AdapterRegistry.get_adapter(self.bridge_config.adapter.value)
            adapter.import_artifact(artifact_key, artifact_path, project_bundle, self.bridge_config)

            # Save updated bundle
            save_project_bundle(project_bundle, bundle_dir, atomic=True)

            operations.append(
                SyncOperation(
                    artifact_key=artifact_key,
                    feature_id=feature_id,
                    direction="import",
                    bundle_name=bundle_name,
                )
            )

        except Exception as e:
            errors.append(f"Import failed: {e}")

        return SyncResult(
            success=len(errors) == 0,
            operations=operations,
            errors=errors,
            warnings=warnings,
        )

    @beartype
    @require(lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0, "Bundle name must be non-empty")
    @require(lambda feature_id: isinstance(feature_id, str) and len(feature_id) > 0, "Feature ID must be non-empty")
    @ensure(lambda result: isinstance(result, SyncResult), "Must return SyncResult")
    def export_artifact(
        self,
        artifact_key: str,
        feature_id: str,
        bundle_name: str,
        persona: str | None = None,
    ) -> SyncResult:
        """
        Export artifact from SpecFact project bundle to tool format.

        Args:
            artifact_key: Artifact key (e.g., "specification", "plan")
            feature_id: Feature identifier (e.g., "001-auth")
            bundle_name: Project bundle name
            persona: Persona for section filtering (optional)

        Returns:
            SyncResult with operation details
        """
        operations: list[SyncOperation] = []
        errors: list[str] = []
        warnings: list[str] = []

        if self.bridge_config is None:
            errors.append("Bridge config not initialized")
            return SyncResult(success=False, operations=operations, errors=errors, warnings=warnings)

        try:
            # Load project bundle
            from specfact_cli.utils.structure import SpecFactStructure

            bundle_dir = self.repo_path / SpecFactStructure.PROJECTS / bundle_name
            if not bundle_dir.exists():
                errors.append(f"Project bundle not found: {bundle_dir}")
                return SyncResult(success=False, operations=operations, errors=errors, warnings=warnings)

            project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)

            # Get adapter from registry (universal pattern - no hard-coded checks)
            adapter = AdapterRegistry.get_adapter(self.bridge_config.adapter.value)

            # Find feature in bundle for export
            feature = None
            for key, feat in project_bundle.features.items():
                if key == feature_id or feature_id in key:
                    feature = feat
                    break

            if feature is None:
                errors.append(f"Feature '{feature_id}' not found in bundle '{bundle_name}'")
                return SyncResult(success=False, operations=operations, errors=errors, warnings=warnings)

            # Export using adapter (adapter handles path resolution and writing)
            exported_result = adapter.export_artifact(artifact_key, feature, self.bridge_config)

            # Handle export result (Path for file-based, dict for API-based)
            if isinstance(exported_result, Path):
                # File-based export - check if file was created
                if not exported_result.exists():
                    warnings.append(f"Adapter exported to {exported_result} but file does not exist")
                else:
                    # Conflict detection: warn if file was overwritten
                    warnings.append(f"Exported to {exported_result}. Use --overwrite flag to suppress this message.")
            elif isinstance(exported_result, dict):
                # API-based export (e.g., GitHub issues)
                # Adapter handles the export, result contains API response data
                pass

            operations.append(
                SyncOperation(
                    artifact_key=artifact_key,
                    feature_id=feature_id,
                    direction="export",
                    bundle_name=bundle_name,
                )
            )

        except Exception as e:
            errors.append(f"Export failed: {e}")

        return SyncResult(
            success=len(errors) == 0,
            operations=operations,
            errors=errors,
            warnings=warnings,
        )

    @beartype
    @require(lambda self: self.bridge_config is not None, "Bridge config must be set")
    @require(lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0, "Bundle name must be non-empty")
    @ensure(lambda result: result is None, "Must return None")
    def generate_alignment_report(self, bundle_name: str, output_file: Path | None = None) -> None:
        """
        Generate alignment report comparing SpecFact features vs OpenSpec specs.

        This method compares features in the SpecFact bundle with specifications
        in OpenSpec to identify gaps and calculate coverage.

        Args:
            bundle_name: Project bundle name
            output_file: Optional file path to save report (if None, only prints to console)
        """
        from specfact_cli.utils.structure import SpecFactStructure

        # Check if adapter supports alignment reports (adapter-agnostic)
        if not self.bridge_config:
            console.print("[yellow]⚠[/yellow] Bridge config not available for alignment report")
            return

        adapter = AdapterRegistry.get_adapter(self.bridge_config.adapter.value)
        if not adapter:
            console.print(
                f"[yellow]⚠[/yellow] Adapter '{self.bridge_config.adapter.value}' not found for alignment report"
            )
            return

        bundle_dir = self.repo_path / SpecFactStructure.PROJECTS / bundle_name
        if not bundle_dir.exists():
            console.print(f"[bold red]✗[/bold red] Project bundle not found: {bundle_dir}")
            return

        progress_columns, progress_kwargs = get_progress_config()
        with Progress(
            *progress_columns,
            console=console,
            **progress_kwargs,
        ) as progress:
            task = progress.add_task("Generating alignment report...", total=None)

            # Load project bundle
            project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)

            # Determine base path for external tool
            base_path = (
                self.bridge_config.external_base_path
                if self.bridge_config and self.bridge_config.external_base_path
                else self.repo_path
            )

            # Get external tool features using adapter (adapter-agnostic)
            external_features = adapter.discover_features(base_path, self.bridge_config)
            external_feature_ids: set[str] = set()
            for feature in external_features:
                feature_key = feature.get("feature_key") or feature.get("key", "")
                if feature_key:
                    external_feature_ids.add(feature_key)

            # Get SpecFact features
            specfact_feature_ids: set[str] = set(project_bundle.features.keys()) if project_bundle.features else set()

            # Calculate alignment
            aligned = specfact_feature_ids & external_feature_ids
            gaps_in_specfact = external_feature_ids - specfact_feature_ids
            gaps_in_external = specfact_feature_ids - external_feature_ids

            total_specs = len(external_feature_ids) if external_feature_ids else 1
            coverage = (len(aligned) / total_specs * 100) if total_specs > 0 else 0.0

            progress.update(task, completed=1)

        # Generate Rich-formatted report (adapter-agnostic)
        adapter_name = self.bridge_config.adapter.value.upper() if self.bridge_config else "External Tool"
        console.print(f"\n[bold]Alignment Report: SpecFact vs {adapter_name}[/bold]\n")

        # Summary table
        summary_table = Table(title="Alignment Summary", show_header=True, header_style="bold magenta")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", style="green", justify="right")
        summary_table.add_row(f"{adapter_name} Specs", str(len(external_feature_ids)))
        summary_table.add_row("SpecFact Features", str(len(specfact_feature_ids)))
        summary_table.add_row("Aligned", str(len(aligned)))
        summary_table.add_row("Gaps in SpecFact", str(len(gaps_in_specfact)))
        summary_table.add_row(f"Gaps in {adapter_name}", str(len(gaps_in_external)))
        summary_table.add_row("Coverage", f"{coverage:.1f}%")
        console.print(summary_table)

        # Gaps table
        if gaps_in_specfact:
            console.print(f"\n[bold yellow]⚠ Gaps in SpecFact ({adapter_name} specs not extracted):[/bold yellow]")
            gaps_table = Table(show_header=True, header_style="bold yellow")
            gaps_table.add_column("Feature ID", style="cyan")
            for feature_id in sorted(gaps_in_specfact):
                gaps_table.add_row(feature_id)
            console.print(gaps_table)

        if gaps_in_external:
            console.print(
                f"\n[bold yellow]⚠ Gaps in {adapter_name} (SpecFact features not in {adapter_name}):[/bold yellow]"
            )
            gaps_table = Table(show_header=True, header_style="bold yellow")
            gaps_table.add_column("Feature ID", style="cyan")
            for feature_id in sorted(gaps_in_external):
                gaps_table.add_row(feature_id)
            console.print(gaps_table)

        # Save to file if requested
        if output_file:
            adapter_name = self.bridge_config.adapter.value.upper() if self.bridge_config else "External Tool"
            report_content = f"""# Alignment Report: SpecFact vs {adapter_name}

## Summary
- {adapter_name} Specs: {len(external_feature_ids)}
- SpecFact Features: {len(specfact_feature_ids)}
- Aligned: {len(aligned)}
- Coverage: {coverage:.1f}%

## Gaps in SpecFact
{chr(10).join(f"- {fid}" for fid in sorted(gaps_in_specfact)) if gaps_in_specfact else "None"}

## Gaps in {adapter_name}
{chr(10).join(f"- {fid}" for fid in sorted(gaps_in_external)) if gaps_in_external else "None"}
"""
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(report_content, encoding="utf-8")
            console.print(f"\n[bold green]✓[/bold green] Report saved to {output_file}")

    @beartype
    @require(lambda self: self.bridge_config is not None, "Bridge config must be set")
    @require(
        lambda adapter_type: isinstance(adapter_type, str) and adapter_type in ("github", "ado", "linear", "jira"),
        "Adapter must be DevOps type",
    )
    @ensure(lambda result: isinstance(result, SyncResult), "Must return SyncResult")
    def export_change_proposals_to_devops(
        self,
        adapter_type: str,
        repo_owner: str | None = None,
        repo_name: str | None = None,
        api_token: str | None = None,
        use_gh_cli: bool = True,
        sanitize: bool | None = None,
        target_repo: str | None = None,
        interactive: bool = False,
        change_ids: list[str] | None = None,
        export_to_tmp: bool = False,
        import_from_tmp: bool = False,
        tmp_file: Path | None = None,
        update_existing: bool = False,
        track_code_changes: bool = False,
        add_progress_comment: bool = False,
        code_repo_path: Path | None = None,
        include_archived: bool = False,
        ado_org: str | None = None,
        ado_project: str | None = None,
        ado_base_url: str | None = None,
        ado_work_item_type: str | None = None,
    ) -> SyncResult:
        """
        Export OpenSpec change proposals to DevOps tools (export-only mode).

        This method reads OpenSpec change proposals and creates/updates DevOps issues
        (GitHub Issues, ADO Work Items, etc.) via the appropriate adapter.

        Args:
            adapter_type: DevOps adapter type (github, ado, linear, jira)
            repo_owner: Repository owner (for GitHub/ADO)
            repo_name: Repository name (for GitHub/ADO)
            api_token: API token (optional, uses env vars, gh CLI, or --github-token if not provided)
            use_gh_cli: If True, try to get token from GitHub CLI (`gh auth token`) for GitHub adapter
            sanitize: If True, sanitize content for public issues. If None, auto-detect based on repo setup.
            target_repo: Target repository for issue creation (format: owner/repo). Default: same as code repo.
            interactive: If True, use interactive mode for AI-assisted sanitization (requires slash command).
            change_ids: Optional list of change proposal IDs to filter. If None, exports all active proposals.
            export_to_tmp: If True, export proposal content to temporary file for LLM review.
            import_from_tmp: If True, import sanitized content from temporary file after LLM review.
            tmp_file: Optional custom temporary file path. Default: <system-temp>/specfact-proposal-<change-id>.md.

        Returns:
            SyncResult with operation details

        Note:
            Requires OpenSpec bridge adapter to be implemented (dependency).
            For now, this is a placeholder that will be fully implemented once
            the OpenSpec adapter is available.
        """
        from specfact_cli.adapters.registry import AdapterRegistry

        operations: list[SyncOperation] = []
        errors: list[str] = []
        warnings: list[str] = []

        try:
            # Get DevOps adapter from registry (adapter-agnostic)
            # Get adapter to determine required kwargs
            adapter_class = AdapterRegistry._adapters.get(adapter_type.lower())
            if not adapter_class:
                errors.append(f"Adapter '{adapter_type}' not found in registry")
                return SyncResult(success=False, operations=[], errors=errors, warnings=warnings)

            # Build adapter kwargs based on adapter type (adapter-agnostic)
            # TODO: Move kwargs determination to adapter capabilities or adapter-specific method
            adapter_kwargs: dict[str, Any] = {}
            if adapter_type.lower() == "github":
                # GitHub adapter requires repo_owner, repo_name, api_token, use_gh_cli
                adapter_kwargs = {
                    "repo_owner": repo_owner,
                    "repo_name": repo_name,
                    "api_token": api_token,
                    "use_gh_cli": use_gh_cli,
                }
            elif adapter_type.lower() == "ado":
                # ADO adapter requires org, project, base_url, api_token, work_item_type
                adapter_kwargs = {
                    "org": ado_org,
                    "project": ado_project,
                    "base_url": ado_base_url,
                    "api_token": api_token,
                    "work_item_type": ado_work_item_type,
                }

            adapter = AdapterRegistry.get_adapter(adapter_type, **adapter_kwargs)

            # TODO: Read OpenSpec change proposals via OpenSpec adapter
            # This requires the OpenSpec bridge adapter to be implemented first
            # For now, this is a placeholder
            try:
                # Attempt to read OpenSpec change proposals
                # This will fail gracefully if OpenSpec adapter is not available
                change_proposals = self._read_openspec_change_proposals(include_archived=include_archived)
            except Exception as e:
                warnings.append(f"OpenSpec adapter not available: {e}. Skipping change proposal sync.")
                return SyncResult(
                    success=True,  # Not an error, just no proposals to sync
                    operations=operations,
                    errors=errors,
                    warnings=warnings,
                )

            # Determine if sanitization is needed (to determine if this is a public repo)
            from specfact_cli.utils.content_sanitizer import ContentSanitizer

            sanitizer = ContentSanitizer()
            # Detect sanitization need (check if code repo != planning repo)
            # For now, we'll use the repo_path as code repo and check for external base path
            planning_repo = self.repo_path
            if self.bridge_config and hasattr(self.bridge_config, "external_base_path"):
                external_path = getattr(self.bridge_config, "external_base_path", None)
                if external_path:
                    planning_repo = Path(external_path)

            should_sanitize = sanitizer.detect_sanitization_need(
                code_repo=self.repo_path,
                planning_repo=planning_repo,
                user_preference=sanitize,
            )

            # Derive target_repo from repo_owner/repo_name or ado_org/ado_project if not provided
            if not target_repo:
                if adapter_type == "ado" and ado_org and ado_project:
                    target_repo = f"{ado_org}/{ado_project}"
                elif repo_owner and repo_name:
                    target_repo = f"{repo_owner}/{repo_name}"

            # Filter proposals based on target repo type and source tracking:
            # - For each proposal, check if it should be synced to the target repo
            # - If proposal has source tracking entry for target repo: sync it (already synced before, needs update)
            # - If proposal doesn't have entry:
            #   - Public repos (sanitize=True): Only sync "applied" proposals (archived/completed)
            #   - Internal repos (sanitize=False/None): Sync all statuses (proposed, in-progress, applied, etc.)
            active_proposals: list[dict[str, Any]] = []
            filtered_count = 0
            for proposal in change_proposals:
                proposal_status = proposal.get("status", "proposed")

                # Check if proposal has source tracking entry for target repo
                source_tracking_raw = proposal.get("source_tracking", {})
                target_entry = self._find_source_tracking_entry(source_tracking_raw, target_repo)
                has_target_entry = target_entry is not None

                # Determine if proposal should be synced
                should_sync = False

                if should_sanitize:
                    # Public repo: only sync applied proposals (archived changes)
                    # Even if proposal has source tracking entry, filter out non-applied proposals
                    should_sync = proposal_status == "applied"
                else:
                    # Internal repo: sync all active proposals
                    if has_target_entry:
                        # Proposal already has entry for this repo - sync it (for updates)
                        should_sync = True
                    else:
                        # New proposal - sync if status is active
                        should_sync = proposal_status in (
                            "proposed",
                            "in-progress",
                            "applied",
                            "deprecated",
                            "discarded",
                        )

                if should_sync:
                    active_proposals.append(proposal)
                else:
                    filtered_count += 1

            if filtered_count > 0:
                if should_sanitize:
                    warnings.append(
                        f"Filtered out {filtered_count} proposal(s) with non-applied status "
                        f"(public repos only sync archived/completed proposals, regardless of source tracking). "
                        f"Only {len(active_proposals)} applied proposal(s) will be synced."
                    )
                else:
                    warnings.append(
                        f"Filtered out {filtered_count} proposal(s) without source tracking entry for target repo "
                        f"and inactive status. Only {len(active_proposals)} proposal(s) will be synced."
                    )

            # Filter by change_ids if specified
            if change_ids:
                # Validate change IDs exist
                valid_change_ids = set(change_ids)
                available_change_ids = {p.get("change_id") for p in active_proposals if p.get("change_id")}
                # Filter out None values
                available_change_ids = {cid for cid in available_change_ids if cid is not None}
                invalid_change_ids = valid_change_ids - available_change_ids
                if invalid_change_ids:
                    errors.append(
                        f"Invalid change IDs: {', '.join(sorted(invalid_change_ids))}. "
                        f"Available: {', '.join(sorted(available_change_ids)) if available_change_ids else 'none'}"
                    )
                # Filter proposals by change_ids
                active_proposals = [p for p in active_proposals if p.get("change_id") in valid_change_ids]

            # Process each proposal
            for proposal in active_proposals:
                try:
                    # proposal is a dict, access via .get()
                    source_tracking_raw = proposal.get("source_tracking", {})
                    # Find entry for target repository (pass original to preserve backward compatibility)
                    # Always call _find_source_tracking_entry - it handles None target_repo for backward compatibility
                    target_entry = self._find_source_tracking_entry(source_tracking_raw, target_repo)

                    # Normalize to list for multi-repository support (after finding entry)
                    source_tracking_list = self._normalize_source_tracking(source_tracking_raw)

                    # Check if issue exists for target repository
                    issue_number = target_entry.get("source_id") if target_entry else None
                    work_item_was_deleted = False  # Track if we detected a deleted work item

                    # If issue_number exists, verify the work item/issue actually exists in the external tool
                    # This handles cases where work items were deleted but source_tracking still references them
                    # Do this BEFORE duplicate prevention check to allow recreation of deleted work items
                    if issue_number and target_entry:
                        entry_type = target_entry.get("source_type", "").lower()

                        # For ADO, verify work item exists (it might have been deleted)
                        if (
                            entry_type == "ado"
                            and adapter_type.lower() == "ado"
                            and ado_org
                            and ado_project
                            and hasattr(adapter, "_work_item_exists")
                        ):
                            try:
                                work_item_exists = adapter._work_item_exists(issue_number, ado_org, ado_project)
                                if not work_item_exists:
                                    # Work item was deleted - clear source_id to allow recreation
                                    warnings.append(
                                        f"Work item #{issue_number} for '{proposal.get('change_id', 'unknown')}' "
                                        f"no longer exists in ADO (may have been deleted). "
                                        f"Will create a new work item."
                                    )
                                    # Clear source_id to allow creation of new work item
                                    issue_number = None
                                    work_item_was_deleted = True
                                    # Also clear it from target_entry for this sync operation
                                    target_entry = {**target_entry, "source_id": None}
                            except Exception as e:
                                # On error checking existence, log warning but allow creation (safer)
                                warnings.append(
                                    f"Could not verify work item #{issue_number} existence: {e}. Proceeding with sync."
                                )

                        # For GitHub, we could add similar verification, but GitHub issues are rarely deleted
                        # (they're usually closed, not deleted), so we skip verification for now

                    # Prevent duplicates: if target_entry exists but has no source_id, skip creation
                    # EXCEPT if we just detected that the work item was deleted (work_item_was_deleted = True)
                    # OR if update_existing is True (clear corrupted entry and create fresh)
                    # This handles cases where source_tracking was partially saved
                    if target_entry and not issue_number and not work_item_was_deleted:
                        if update_existing:
                            # Clear corrupted entry to allow fresh creation
                            # If target_entry was found by _find_source_tracking_entry, it matches target_repo
                            # So we can safely clear it when update_existing=True
                            if isinstance(source_tracking_raw, dict):
                                # Single entry - clear it completely (it's the corrupted one)
                                proposal["source_tracking"] = {}
                                target_entry = None
                            elif isinstance(source_tracking_raw, list):
                                # Multiple entries - remove the specific corrupted entry (target_entry)
                                # Use identity check to remove the exact entry object
                                source_tracking_list = [
                                    entry for entry in source_tracking_list if entry is not target_entry
                                ]
                                proposal["source_tracking"] = source_tracking_list
                                target_entry = None
                            # Continue to creation logic below (target_entry is now None)
                        else:
                            warnings.append(
                                f"Skipping sync for '{proposal.get('change_id', 'unknown')}': "
                                f"source_tracking entry exists for '{target_repo}' but missing source_id. "
                                f"Use --update-existing to force update or manually fix source_tracking."
                            )
                            continue

                    if issue_number and target_entry:
                        # Issue exists - update it
                        self._update_existing_issue(
                            proposal=proposal,
                            target_entry=target_entry,
                            issue_number=issue_number,
                            adapter=adapter,
                            adapter_type=adapter_type,
                            target_repo=target_repo,
                            source_tracking_list=source_tracking_list,
                            source_tracking_raw=source_tracking_raw,
                            repo_owner=repo_owner,
                            repo_name=repo_name,
                            ado_org=ado_org,
                            ado_project=ado_project,
                            update_existing=update_existing,
                            import_from_tmp=import_from_tmp,
                            tmp_file=tmp_file,
                            should_sanitize=should_sanitize,
                            track_code_changes=track_code_changes,
                            add_progress_comment=add_progress_comment,
                            code_repo_path=code_repo_path,
                            operations=operations,
                            errors=errors,
                            warnings=warnings,
                        )
                        # Save updated proposal
                        self._save_openspec_change_proposal(proposal)
                        continue
                    # No issue exists in source_tracking OR work item was deleted (work_item_was_deleted = True)
                    # Verify it doesn't exist before creating (unless we detected it was deleted)
                    change_id = proposal.get("change_id", "unknown")

                    # Check if target_entry exists but doesn't have source_id (corrupted source_tracking)
                    # EXCEPT if we just detected that the work item was deleted (work_item_was_deleted = True)
                    if target_entry and not target_entry.get("source_id") and not work_item_was_deleted:
                        # Source tracking entry exists but missing source_id - don't create duplicate
                        # This could happen if source_tracking was partially saved
                        warnings.append(
                            f"Skipping sync for '{change_id}': source_tracking entry exists for "
                            f"'{target_repo}' but missing source_id. Use --update-existing to force update."
                        )
                        continue

                    # Search for existing issue/work item by change proposal ID if no source_tracking entry exists
                    # This prevents duplicates when a proposal was synced to one tool but not another
                    if not target_entry and adapter_type.lower() == "github" and repo_owner and repo_name:
                        found_entry, found_issue_number = self._search_existing_github_issue(
                            change_id, repo_owner, repo_name, target_repo, warnings
                        )
                        if found_entry and found_issue_number:
                            target_entry = found_entry
                            issue_number = found_issue_number
                            # Add to source_tracking_list
                            source_tracking_list.append(target_entry)
                            proposal["source_tracking"] = source_tracking_list
                    if (
                        not target_entry
                        and adapter_type.lower() == "ado"
                        and ado_org
                        and ado_project
                        and hasattr(adapter, "_find_work_item_by_change_id")
                    ):
                        found_entry = adapter._find_work_item_by_change_id(change_id, ado_org, ado_project)
                        if found_entry:
                            target_entry = found_entry
                            issue_number = found_entry.get("source_id")
                            source_tracking_list.append(found_entry)
                            proposal["source_tracking"] = source_tracking_list

                    # If we found an existing issue via search, update it instead of creating a new one
                    if issue_number and target_entry:
                        # Use the same update logic as above
                        self._update_existing_issue(
                            proposal=proposal,
                            target_entry=target_entry,
                            issue_number=issue_number,
                            adapter=adapter,
                            adapter_type=adapter_type,
                            target_repo=target_repo,
                            source_tracking_list=source_tracking_list,
                            source_tracking_raw=source_tracking_raw,
                            repo_owner=repo_owner,
                            repo_name=repo_name,
                            ado_org=ado_org,
                            ado_project=ado_project,
                            update_existing=update_existing,
                            import_from_tmp=import_from_tmp,
                            tmp_file=tmp_file,
                            should_sanitize=should_sanitize,
                            track_code_changes=track_code_changes,
                            add_progress_comment=add_progress_comment,
                            code_repo_path=code_repo_path,
                            operations=operations,
                            errors=errors,
                            warnings=warnings,
                        )
                        # Save updated proposal
                        self._save_openspec_change_proposal(proposal)
                        continue

                    # Handle temporary file workflow if requested
                    if export_to_tmp:
                        # Export proposal content to temporary file for LLM review
                        tmp_file_path = tmp_file or (Path(tempfile.gettempdir()) / f"specfact-proposal-{change_id}.md")
                        try:
                            # Create markdown content from proposal
                            proposal_content = self._format_proposal_for_export(proposal)
                            tmp_file_path.parent.mkdir(parents=True, exist_ok=True)
                            tmp_file_path.write_text(proposal_content, encoding="utf-8")
                            warnings.append(f"Exported proposal '{change_id}' to {tmp_file_path} for LLM review")
                            # Skip issue creation when exporting to tmp
                            continue
                        except Exception as e:
                            errors.append(f"Failed to export proposal '{change_id}' to temporary file: {e}")
                            continue

                    if import_from_tmp:
                        # Import sanitized content from temporary file
                        sanitized_file_path = tmp_file or (
                            Path(tempfile.gettempdir()) / f"specfact-proposal-{change_id}-sanitized.md"
                        )
                        try:
                            if not sanitized_file_path.exists():
                                errors.append(
                                    f"Sanitized file not found: {sanitized_file_path}. "
                                    f"Please run LLM sanitization first."
                                )
                                continue
                            # Read sanitized content
                            sanitized_content = sanitized_file_path.read_text(encoding="utf-8")
                            # Parse sanitized content back into proposal structure
                            proposal_to_export = self._parse_sanitized_proposal(sanitized_content, proposal)
                            # Cleanup temporary files after import
                            try:
                                original_tmp = Path(tempfile.gettempdir()) / f"specfact-proposal-{change_id}.md"
                                if original_tmp.exists():
                                    original_tmp.unlink()
                                if sanitized_file_path.exists():
                                    sanitized_file_path.unlink()
                            except Exception as cleanup_error:
                                warnings.append(f"Failed to cleanup temporary files: {cleanup_error}")
                        except Exception as e:
                            errors.append(f"Failed to import sanitized content for '{change_id}': {e}")
                            continue
                    else:
                        # Normal flow: use proposal as-is or sanitize if needed
                        proposal_to_export = proposal.copy()
                        if should_sanitize:
                            # Sanitize description and rationale separately
                            # (they're already extracted sections, sanitizer will remove unwanted patterns)
                            original_description = proposal.get("description", "")
                            original_rationale = proposal.get("rationale", "")

                            # Combine into full markdown for sanitization
                            combined_markdown = ""
                            if original_rationale:
                                combined_markdown += f"## Why\n\n{original_rationale}\n\n"
                            if original_description:
                                combined_markdown += f"## What Changes\n\n{original_description}\n\n"

                            if combined_markdown:
                                sanitized_markdown = sanitizer.sanitize_proposal(combined_markdown)

                                # Parse sanitized content back into description/rationale
                                # Extract Why section
                                why_match = re.search(r"##\s*Why\s*\n\n(.*?)(?=\n##|\Z)", sanitized_markdown, re.DOTALL)
                                sanitized_rationale = why_match.group(1).strip() if why_match else ""

                                # Extract What Changes section
                                what_match = re.search(
                                    r"##\s*What\s+Changes\s*\n\n(.*?)(?=\n##|\Z)", sanitized_markdown, re.DOTALL
                                )
                                sanitized_description = what_match.group(1).strip() if what_match else ""

                                # Update proposal with sanitized content
                                proposal_to_export["description"] = sanitized_description or original_description
                                proposal_to_export["rationale"] = sanitized_rationale or original_rationale

                    result = adapter.export_artifact(
                        artifact_key="change_proposal",
                        artifact_data=proposal_to_export,
                        bridge_config=self.bridge_config,
                    )
                    # Store issue info in source_tracking (proposal is a dict)
                    if isinstance(proposal, dict) and isinstance(result, dict):
                        # Normalize existing source_tracking to list
                        source_tracking_list = self._normalize_source_tracking(proposal.get("source_tracking", {}))
                        # Create new entry for this repository
                        # For ADO, use ado_org/ado_project; for GitHub, use repo_owner/repo_name
                        if adapter_type == "ado" and ado_org and ado_project:
                            repo_identifier = target_repo or f"{ado_org}/{ado_project}"
                            source_id = str(result.get("work_item_id", result.get("issue_number", "")))
                            source_url = str(result.get("work_item_url", result.get("issue_url", "")))
                        else:
                            repo_identifier = target_repo or f"{repo_owner}/{repo_name}"
                            source_id = str(result.get("issue_number", result.get("work_item_id", "")))
                            source_url = str(result.get("issue_url", result.get("work_item_url", "")))
                        new_entry = {
                            "source_id": source_id,
                            "source_url": source_url,
                            "source_type": adapter_type,
                            "source_repo": repo_identifier,
                            "source_metadata": {
                                "last_synced_status": proposal.get("status"),
                                "sanitized": should_sanitize if should_sanitize is not None else False,
                            },
                        }
                        source_tracking_list = self._update_source_tracking_entry(
                            source_tracking_list, repo_identifier, new_entry
                        )
                        proposal["source_tracking"] = source_tracking_list
                    operations.append(
                        SyncOperation(
                            artifact_key="change_proposal",
                            feature_id=proposal.get("change_id", "unknown"),
                            direction="export",
                            bundle_name="openspec",
                        )
                    )

                    # Save updated change proposals back to OpenSpec
                    # Store issue IDs in proposal.md metadata section
                    self._save_openspec_change_proposal(proposal)

                except Exception as e:
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.debug(f"Failed to sync proposal {proposal.get('change_id', 'unknown')}: {e}", exc_info=True)
                    errors.append(f"Failed to sync proposal {proposal.get('change_id', 'unknown')}: {e}")

        except Exception as e:
            errors.append(f"Export to DevOps failed: {e}")

        return SyncResult(
            success=len(errors) == 0,
            operations=operations,
            errors=errors,
            warnings=warnings,
        )

    def _read_openspec_change_proposals(self, include_archived: bool = True) -> list[dict[str, Any]]:
        """
        Read OpenSpec change proposals from openspec/changes/ directory.

        Args:
            include_archived: If True, include archived changes (default: True for backward compatibility)

        Returns:
            List of change proposal dicts with keys: change_id, title, description, rationale, status, source_tracking

        Note:
            This is a basic implementation that reads OpenSpec proposal.md files directly.
            Once the OpenSpec bridge adapter is implemented, this should delegate to it.
        """
        proposals: list[dict[str, Any]] = []

        # Look for openspec/changes/ directory (could be in repo or external)
        openspec_changes_dir = None

        # Check if openspec/changes exists in repo
        openspec_dir = self.repo_path / "openspec" / "changes"
        if openspec_dir.exists() and openspec_dir.is_dir():
            openspec_changes_dir = openspec_dir
        else:
            # Check for external base path in bridge config
            if self.bridge_config and hasattr(self.bridge_config, "external_base_path"):
                external_path = getattr(self.bridge_config, "external_base_path", None)
                if external_path:
                    openspec_changes_dir = Path(external_path) / "openspec" / "changes"
                    if not openspec_changes_dir.exists():
                        openspec_changes_dir = None

        if not openspec_changes_dir or not openspec_changes_dir.exists():
            return proposals  # No OpenSpec changes directory found

        # Scan for change proposal directories (including archive subdirectories)
        archive_dir = openspec_changes_dir / "archive"

        # First, scan active changes
        for change_dir in openspec_changes_dir.iterdir():
            if not change_dir.is_dir() or change_dir.name == "archive":
                continue

            proposal_file = change_dir / "proposal.md"
            if not proposal_file.exists():
                continue

            try:
                # Parse proposal.md
                proposal_content = proposal_file.read_text(encoding="utf-8")

                # Extract title (first line after "# Change:")
                title = ""
                description = ""
                rationale = ""
                impact = ""
                status = "proposed"  # Default status

                lines = proposal_content.split("\n")
                in_why = False
                in_what = False
                in_impact = False
                in_source_tracking = False

                for line_idx, line in enumerate(lines):
                    line_stripped = line.strip()
                    if line_stripped.startswith("# Change:"):
                        title = line_stripped.replace("# Change:", "").strip()
                    elif line_stripped == "## Why":
                        in_why = True
                        in_what = False
                        in_impact = False
                        in_source_tracking = False
                    elif line_stripped == "## What Changes":
                        in_why = False
                        in_what = True
                        in_impact = False
                        in_source_tracking = False
                    elif line_stripped == "## Impact":
                        in_why = False
                        in_what = False
                        in_impact = True
                        in_source_tracking = False
                    elif line_stripped == "## Source Tracking":
                        in_why = False
                        in_what = False
                        in_impact = False
                        in_source_tracking = True
                    elif in_source_tracking:
                        # Skip source tracking section (we'll parse it separately)
                        continue
                    elif in_why:
                        if line_stripped == "## What Changes":
                            in_why = False
                            in_what = True
                            in_impact = False
                            in_source_tracking = False
                            continue
                        if line_stripped == "## Impact":
                            in_why = False
                            in_what = False
                            in_impact = True
                            in_source_tracking = False
                            continue
                        if line_stripped == "## Source Tracking":
                            in_why = False
                            in_what = False
                            in_impact = False
                            in_source_tracking = True
                            continue
                        # Stop at --- separator only if it's followed by Source Tracking
                        if line_stripped == "---":
                            # Check if next non-empty line is Source Tracking
                            remaining_lines = lines[line_idx + 1 : line_idx + 5]  # Check next 5 lines
                            if any("## Source Tracking" in line for line in remaining_lines):
                                in_why = False
                                in_impact = False
                                in_source_tracking = True
                                continue
                        # Preserve all content including empty lines and formatting
                        if rationale and not rationale.endswith("\n"):
                            rationale += "\n"
                        rationale += line + "\n"
                    elif in_what:
                        if line_stripped == "## Why":
                            in_what = False
                            in_why = True
                            in_impact = False
                            in_source_tracking = False
                            continue
                        if line_stripped == "## Impact":
                            in_what = False
                            in_why = False
                            in_impact = True
                            in_source_tracking = False
                            continue
                        if line_stripped == "## Source Tracking":
                            in_what = False
                            in_why = False
                            in_impact = False
                            in_source_tracking = True
                            continue
                        # Stop at --- separator only if it's followed by Source Tracking
                        if line_stripped == "---":
                            # Check if next non-empty line is Source Tracking
                            remaining_lines = lines[line_idx + 1 : line_idx + 5]  # Check next 5 lines
                            if any("## Source Tracking" in line for line in remaining_lines):
                                in_what = False
                                in_impact = False
                                in_source_tracking = True
                                continue
                        # Preserve all content including empty lines and formatting
                        if description and not description.endswith("\n"):
                            description += "\n"
                        description += line + "\n"
                    elif in_impact:
                        if line_stripped == "## Why":
                            in_impact = False
                            in_why = True
                            in_what = False
                            in_source_tracking = False
                            continue
                        if line_stripped == "## What Changes":
                            in_impact = False
                            in_why = False
                            in_what = True
                            in_source_tracking = False
                            continue
                        if line_stripped == "## Source Tracking":
                            in_impact = False
                            in_why = False
                            in_what = False
                            in_source_tracking = True
                            continue
                        if line_stripped == "---":
                            remaining_lines = lines[line_idx + 1 : line_idx + 5]
                            if any("## Source Tracking" in line for line in remaining_lines):
                                in_impact = False
                                in_source_tracking = True
                                continue
                        if impact and not impact.endswith("\n"):
                            impact += "\n"
                        impact += line + "\n"

                # Check for existing source tracking in proposal.md
                source_tracking_list: list[dict[str, Any]] = []
                if "## Source Tracking" in proposal_content:
                    # Parse existing source tracking (support multiple entries)
                    source_tracking_match = re.search(
                        r"## Source Tracking\s*\n(.*?)(?=\n## |\Z)", proposal_content, re.DOTALL
                    )
                    if source_tracking_match:
                        tracking_content = source_tracking_match.group(1)
                        # Split by repository sections (### Repository: ...)
                        # Pattern: ### Repository: <repo> followed by entries until next ### or ---
                        repo_sections = re.split(r"###\s+Repository:\s*([^\n]+)\s*\n", tracking_content)
                        # repo_sections alternates: [content_before_first, repo1, content1, repo2, content2, ...]
                        if len(repo_sections) > 1:
                            # Multiple repository entries
                            for i in range(1, len(repo_sections), 2):
                                if i + 1 < len(repo_sections):
                                    repo_name = repo_sections[i].strip()
                                    entry_content = repo_sections[i + 1]
                                    entry = self._parse_source_tracking_entry(entry_content, repo_name)
                                    if entry:
                                        source_tracking_list.append(entry)
                        else:
                            # Single entry (backward compatibility - no repository header)
                            # Check if source_repo is in a hidden comment first
                            entry = self._parse_source_tracking_entry(tracking_content, None)
                            if entry:
                                # If source_repo was extracted from hidden comment, ensure it's set
                                if not entry.get("source_repo"):
                                    # Try to extract from URL as fallback
                                    source_url = entry.get("source_url", "")
                                    if source_url:
                                        # Try GitHub URL pattern
                                        url_repo_match = re.search(r"github\.com/([^/]+/[^/]+)/", source_url)
                                        if url_repo_match:
                                            entry["source_repo"] = url_repo_match.group(1)
                                        # Try ADO URL pattern - extract org, but we need project name from elsewhere
                                        else:
                                            # Use proper URL parsing to validate ADO URLs
                                            try:
                                                parsed = urlparse(source_url)
                                                if parsed.hostname and parsed.hostname.lower() == "dev.azure.com":
                                                    # For ADO, we can't reliably extract project name from URL (GUID)
                                                    # The source_repo should have been saved in the hidden comment
                                                    # If not, we'll need to match by org only later
                                                    pass
                                            except Exception:
                                                pass
                                source_tracking_list.append(entry)

                # Check for status indicators in proposal content or directory name
                # Status could be inferred from directory structure or metadata files
                # For now, default to "proposed" - can be enhanced later

                # Clean up description and rationale (remove extra newlines)
                description_clean = self._dedupe_duplicate_sections(description.strip()) if description else ""
                impact_clean = impact.strip() if impact else ""
                rationale_clean = rationale.strip() if rationale else ""

                # Create proposal dict
                # Convert source_tracking_list to single dict for backward compatibility if only one entry
                # Otherwise keep as list
                source_tracking_final: list[dict[str, Any]] | dict[str, Any] = (
                    (source_tracking_list[0] if len(source_tracking_list) == 1 else source_tracking_list)
                    if source_tracking_list
                    else {}
                )

                proposal = {
                    "change_id": change_dir.name,
                    "title": title or change_dir.name,
                    "description": description_clean or "No description provided.",
                    "rationale": rationale_clean or "No rationale provided.",
                    "impact": impact_clean,
                    "status": status,
                    "source_tracking": source_tracking_final,
                }

                proposals.append(proposal)

            except Exception as e:
                # Log error but continue processing other proposals
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to parse proposal from {proposal_file}: {e}")

        # Also scan archived changes (treat as "applied" status for status updates)
        if include_archived:
            archive_dir = openspec_changes_dir / "archive"
            if archive_dir.exists() and archive_dir.is_dir():
                for archive_subdir in archive_dir.iterdir():
                    if not archive_subdir.is_dir():
                        continue

                    # Extract change ID from archive directory name (format: YYYY-MM-DD-<change-id>)
                    archive_name = archive_subdir.name
                    if "-" in archive_name:
                        # Extract change_id from "2025-12-29-add-devops-backlog-tracking"
                        parts = archive_name.split("-", 3)
                        change_id = parts[3] if len(parts) >= 4 else archive_subdir.name
                    else:
                        change_id = archive_subdir.name

                    proposal_file = archive_subdir / "proposal.md"
                    if not proposal_file.exists():
                        continue

                    try:
                        # Parse proposal.md (reuse same parsing logic)
                        proposal_content = proposal_file.read_text(encoding="utf-8")

                        # Extract title, description, rationale (same parsing logic)
                        title = ""
                        description = ""
                        rationale = ""
                        impact = ""
                        status = "applied"  # Archived changes are treated as "applied"

                        lines = proposal_content.split("\n")
                        in_why = False
                        in_what = False
                        in_impact = False
                        in_source_tracking = False

                        for line_idx, line in enumerate(lines):
                            line_stripped = line.strip()
                            if line_stripped.startswith("# Change:"):
                                title = line_stripped.replace("# Change:", "").strip()
                                continue
                            if line_stripped == "## Why":
                                in_why = True
                                in_what = False
                                in_impact = False
                                in_source_tracking = False
                            elif line_stripped == "## What Changes":
                                in_why = False
                                in_what = True
                                in_impact = False
                                in_source_tracking = False
                            elif line_stripped == "## Impact":
                                in_why = False
                                in_what = False
                                in_impact = True
                                in_source_tracking = False
                            elif line_stripped == "## Source Tracking":
                                in_why = False
                                in_what = False
                                in_impact = False
                                in_source_tracking = True
                            elif in_source_tracking:
                                continue
                            elif in_why:
                                if line_stripped == "## What Changes":
                                    in_why = False
                                    in_what = True
                                    in_impact = False
                                    in_source_tracking = False
                                    continue
                                if line_stripped == "## Impact":
                                    in_why = False
                                    in_what = False
                                    in_impact = True
                                    in_source_tracking = False
                                    continue
                                if line_stripped == "## Source Tracking":
                                    in_why = False
                                    in_what = False
                                    in_impact = False
                                    in_source_tracking = True
                                    continue
                                if line_stripped == "---":
                                    remaining_lines = lines[line_idx + 1 : line_idx + 5]
                                    if any("## Source Tracking" in line for line in remaining_lines):
                                        in_why = False
                                        in_impact = False
                                        in_source_tracking = True
                                        continue
                                if rationale and not rationale.endswith("\n"):
                                    rationale += "\n"
                                rationale += line + "\n"
                            elif in_what:
                                if line_stripped == "## Why":
                                    in_what = False
                                    in_why = True
                                    in_impact = False
                                    in_source_tracking = False
                                    continue
                                if line_stripped == "## Impact":
                                    in_what = False
                                    in_why = False
                                    in_impact = True
                                    in_source_tracking = False
                                    continue
                                if line_stripped == "## Source Tracking":
                                    in_what = False
                                    in_why = False
                                    in_impact = False
                                    in_source_tracking = True
                                    continue
                                if line_stripped == "---":
                                    remaining_lines = lines[line_idx + 1 : line_idx + 5]
                                    if any("## Source Tracking" in line for line in remaining_lines):
                                        in_what = False
                                        in_impact = False
                                        in_source_tracking = True
                                        continue
                                if description and not description.endswith("\n"):
                                    description += "\n"
                                description += line + "\n"
                            elif in_impact:
                                if line_stripped == "## Why":
                                    in_impact = False
                                    in_why = True
                                    in_what = False
                                    in_source_tracking = False
                                    continue
                                if line_stripped == "## What Changes":
                                    in_impact = False
                                    in_why = False
                                    in_what = True
                                    in_source_tracking = False
                                    continue
                                if line_stripped == "## Source Tracking":
                                    in_impact = False
                                    in_why = False
                                    in_what = False
                                    in_source_tracking = True
                                    continue
                                if line_stripped == "---":
                                    remaining_lines = lines[line_idx + 1 : line_idx + 5]
                                    if any("## Source Tracking" in line for line in remaining_lines):
                                        in_impact = False
                                        in_source_tracking = True
                                        continue
                                if impact and not impact.endswith("\n"):
                                    impact += "\n"
                                impact += line + "\n"

                        # Parse source tracking (same logic as active changes)
                        archive_source_tracking_list: list[dict[str, Any]] = []
                        if "## Source Tracking" in proposal_content:
                            source_tracking_match = re.search(
                                r"## Source Tracking\s*\n(.*?)(?=\n## |\Z)", proposal_content, re.DOTALL
                            )
                            if source_tracking_match:
                                tracking_content = source_tracking_match.group(1)
                                repo_sections = re.split(r"###\s+Repository:\s*([^\n]+)\s*\n", tracking_content)
                                if len(repo_sections) > 1:
                                    for i in range(1, len(repo_sections), 2):
                                        if i + 1 < len(repo_sections):
                                            repo_name = repo_sections[i].strip()
                                            entry_content = repo_sections[i + 1]
                                            entry = self._parse_source_tracking_entry(entry_content, repo_name)
                                            if entry:
                                                archive_source_tracking_list.append(entry)
                                else:
                                    entry = self._parse_source_tracking_entry(tracking_content, None)
                                    if entry:
                                        archive_source_tracking_list.append(entry)

                        # Convert to single dict for backward compatibility if only one entry
                        archive_source_tracking_final: list[dict[str, Any]] | dict[str, Any] = (
                            (
                                archive_source_tracking_list[0]
                                if len(archive_source_tracking_list) == 1
                                else archive_source_tracking_list
                            )
                            if archive_source_tracking_list
                            else {}
                        )

                        # Clean up description and rationale
                        description_clean = self._dedupe_duplicate_sections(description.strip()) if description else ""
                        impact_clean = impact.strip() if impact else ""
                        rationale_clean = rationale.strip() if rationale else ""

                        proposal = {
                            "change_id": change_id,
                            "title": title or change_id,
                            "description": description_clean or "No description provided.",
                            "rationale": rationale_clean or "No rationale provided.",
                            "impact": impact_clean,
                            "status": status,  # "applied" for archived changes
                            "source_tracking": archive_source_tracking_final,
                        }

                        proposals.append(proposal)

                    except Exception as e:
                        # Log error but continue processing other proposals
                        import logging

                        logger = logging.getLogger(__name__)
                        logger.warning(f"Failed to parse archived proposal from {proposal_file}: {e}")

        return proposals

    def _find_source_tracking_entry(
        self, source_tracking: list[dict[str, Any]] | dict[str, Any] | None, target_repo: str | None
    ) -> dict[str, Any] | None:
        """
        Find source tracking entry for a specific repository.

        Args:
            source_tracking: Source tracking (list of entries or single dict for backward compatibility)
            target_repo: Target repository identifier (e.g., "nold-ai/specfact-cli")

        Returns:
            Matching entry dict or None if not found
        """
        if not source_tracking:
            return None

        # Handle backward compatibility: single dict -> convert to list
        if isinstance(source_tracking, dict):
            entry_type = source_tracking.get("source_type", "").lower()
            entry_repo = source_tracking.get("source_repo")

            # Primary match: exact source_repo match
            if entry_repo == target_repo:
                return source_tracking

            # Check if it matches target_repo (extract from source_url if available)
            if target_repo:
                source_url = source_tracking.get("source_url", "")
                if source_url:
                    # Try GitHub URL pattern
                    url_repo_match = re.search(r"github\.com/([^/]+/[^/]+)/", source_url)
                    if url_repo_match:
                        source_repo = url_repo_match.group(1)
                        if source_repo == target_repo:
                            return source_tracking
                    # Try ADO URL pattern (ADO URLs contain GUIDs, not project names)
                    # For ADO, match by org if target_repo contains the org
                    elif "/" in target_repo:
                        try:
                            parsed = urlparse(source_url)
                            if parsed.hostname and parsed.hostname.lower() == "dev.azure.com":
                                target_org = target_repo.split("/")[0]
                                ado_org_match = re.search(r"dev\.azure\.com/([^/]+)/", source_url)
                                # Org matches and source_type is "ado" - return entry (project name may differ due to GUID in URL)
                                if (
                                    ado_org_match
                                    and ado_org_match.group(1) == target_org
                                    and (entry_type == "ado" or entry_type == "")
                                ):
                                    return source_tracking
                        except Exception:
                            pass

                # Tertiary match: for ADO, only match by org when project is truly unknown (GUID-only URLs)
                # This prevents cross-project matches when both entry_repo and target_repo have project names
                if entry_repo and target_repo and entry_type == "ado":
                    entry_org = entry_repo.split("/")[0] if "/" in entry_repo else None
                    target_org = target_repo.split("/")[0] if "/" in target_repo else None
                    entry_project = entry_repo.split("/", 1)[1] if "/" in entry_repo else None
                    target_project = target_repo.split("/", 1)[1] if "/" in target_repo else None

                    # Only use org-only match when:
                    # 1. Org matches
                    # 2. source_id exists (for single dict, check source_tracking dict)
                    # 3. AND (project is unknown in entry OR project is unknown in target OR both contain GUIDs)
                    # This prevents matching org/project-a with org/project-b when both have known project names
                    source_url = source_tracking.get("source_url", "") if isinstance(source_tracking, dict) else ""
                    entry_has_guid = source_url and re.search(
                        r"dev\.azure\.com/[^/]+/[0-9a-f-]{36}", source_url, re.IGNORECASE
                    )
                    project_unknown = (
                        not entry_project  # Entry has no project part
                        or not target_project  # Target has no project part
                        or entry_has_guid  # Entry URL contains GUID (project name unknown)
                        or (
                            entry_project and len(entry_project) == 36 and "-" in entry_project
                        )  # Entry project is a GUID
                        or (
                            target_project and len(target_project) == 36 and "-" in target_project
                        )  # Target project is a GUID
                    )

                    if (
                        entry_org
                        and target_org
                        and entry_org == target_org
                        and (isinstance(source_tracking, dict) and source_tracking.get("source_id"))
                        and project_unknown
                    ):
                        return source_tracking

            # If no target_repo specified or doesn't match, return the single entry
            # (for backward compatibility when no target_repo is specified)
            if not target_repo:
                return source_tracking
            return None

        # Handle list of entries
        if isinstance(source_tracking, list):
            for entry in source_tracking:
                if isinstance(entry, dict):
                    entry_repo = entry.get("source_repo")
                    entry_type = entry.get("source_type", "").lower()

                    # Primary match: exact source_repo match
                    if entry_repo == target_repo:
                        return entry

                    # Secondary match: extract from source_url if source_repo not set
                    if not entry_repo and target_repo:
                        source_url = entry.get("source_url", "")
                        if source_url:
                            # Try GitHub URL pattern
                            url_repo_match = re.search(r"github\.com/([^/]+/[^/]+)/", source_url)
                            if url_repo_match:
                                source_repo = url_repo_match.group(1)
                                if source_repo == target_repo:
                                    return entry
                            # Try ADO URL pattern (but note: ADO URLs contain GUIDs, not project names)
                            # For ADO, match by org if target_repo contains the org
                            elif "/" in target_repo:
                                try:
                                    parsed = urlparse(source_url)
                                    if parsed.hostname and parsed.hostname.lower() == "dev.azure.com":
                                        target_org = target_repo.split("/")[0]
                                        ado_org_match = re.search(r"dev\.azure\.com/([^/]+)/", source_url)
                                        # Org matches and source_type is "ado" - return entry (project name may differ due to GUID in URL)
                                        if (
                                            ado_org_match
                                            and ado_org_match.group(1) == target_org
                                            and (entry_type == "ado" or entry_type == "")
                                        ):
                                            return entry
                                except Exception:
                                    pass

                    # Tertiary match: for ADO, only match by org when project is truly unknown (GUID-only URLs)
                    # This prevents cross-project matches when both entry_repo and target_repo have project names
                    if entry_repo and target_repo and entry_type == "ado":
                        entry_org = entry_repo.split("/")[0] if "/" in entry_repo else None
                        target_org = target_repo.split("/")[0] if "/" in target_repo else None
                        entry_project = entry_repo.split("/", 1)[1] if "/" in entry_repo else None
                        target_project = target_repo.split("/", 1)[1] if "/" in target_repo else None

                        # Only use org-only match when:
                        # 1. Org matches
                        # 2. source_id exists
                        # 3. AND (project is unknown in entry OR project is unknown in target OR both contain GUIDs)
                        # This prevents matching org/project-a with org/project-b when both have known project names
                        source_url = entry.get("source_url", "")
                        entry_has_guid = source_url and re.search(
                            r"dev\.azure\.com/[^/]+/[0-9a-f-]{36}", source_url, re.IGNORECASE
                        )
                        project_unknown = (
                            not entry_project  # Entry has no project part
                            or not target_project  # Target has no project part
                            or entry_has_guid  # Entry URL contains GUID (project name unknown)
                            or (
                                entry_project and len(entry_project) == 36 and "-" in entry_project
                            )  # Entry project is a GUID
                            or (
                                target_project and len(target_project) == 36 and "-" in target_project
                            )  # Target project is a GUID
                        )

                        if (
                            entry_org
                            and target_org
                            and entry_org == target_org
                            and entry.get("source_id")
                            and project_unknown
                        ):
                            return entry

        return None

    @beartype
    @require(lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0, "Bundle name must be non-empty")
    @require(lambda backlog_items: isinstance(backlog_items, list), "Backlog items must be list")
    @ensure(lambda result: isinstance(result, SyncResult), "Must return SyncResult")
    def import_backlog_items_to_bundle(
        self,
        adapter_type: str,
        bundle_name: str,
        backlog_items: list[str],
        adapter_kwargs: dict[str, Any] | None = None,
    ) -> SyncResult:
        """
        Import selected backlog items into a project bundle.

        Args:
            adapter_type: Backlog adapter type (github, ado)
            bundle_name: Project bundle name
            backlog_items: Backlog item identifiers (IDs or URLs)
            adapter_kwargs: Adapter-specific kwargs for initialization

        Returns:
            SyncResult with operation details
        """
        operations: list[SyncOperation] = []
        errors: list[str] = []
        warnings: list[str] = []

        adapter_kwargs = adapter_kwargs or {}
        adapter = AdapterRegistry.get_adapter(adapter_type, **adapter_kwargs)
        artifact_key_map = {"github": "github_issue", "ado": "ado_work_item"}
        artifact_key = artifact_key_map.get(adapter_type)
        if not artifact_key:
            errors.append(f"Unsupported backlog adapter: {adapter_type}")
            return SyncResult(success=False, operations=operations, errors=errors, warnings=warnings)

        if not hasattr(adapter, "fetch_backlog_item"):
            errors.append(f"Adapter '{adapter_type}' does not support backlog fetch operations")
            return SyncResult(success=False, operations=operations, errors=errors, warnings=warnings)

        from specfact_cli.utils.structure import SpecFactStructure

        bundle_dir = SpecFactStructure.project_dir(base_path=self.repo_path, bundle_name=bundle_name)
        if not bundle_dir.exists():
            errors.append(f"Project bundle not found: {bundle_dir}")
            return SyncResult(success=False, operations=operations, errors=errors, warnings=warnings)

        project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        bridge_config = adapter.generate_bridge_config(self.repo_path)

        for item_ref in backlog_items:
            try:
                item_data = adapter.fetch_backlog_item(item_ref)
                adapter.import_artifact(artifact_key, item_data, project_bundle, bridge_config)

                # Get the imported proposal from bundle to create OpenSpec files
                if hasattr(project_bundle, "change_tracking") and project_bundle.change_tracking:
                    # Find the proposal that was just imported
                    # The adapter stores it with proposal.name as the key
                    imported_proposal = None

                    # Try to find by matching source tracking (backlog entry ID)
                    item_ref_clean = str(item_ref).split("/")[-1]  # Extract number from URL if needed
                    item_ref_str = str(item_ref)

                    import logging

                    logger = logging.getLogger(__name__)
                    logger.debug(f"Looking for proposal matching backlog item '{item_ref}' (clean: '{item_ref_clean}')")

                    for proposal in project_bundle.change_tracking.proposals.values():
                        if proposal.source_tracking:
                            source_metadata = proposal.source_tracking.source_metadata
                            if isinstance(source_metadata, dict):
                                backlog_entries = source_metadata.get("backlog_entries", [])
                                for entry in backlog_entries:
                                    if isinstance(entry, dict):
                                        entry_id = entry.get("source_id")
                                        # Match by issue number (item_ref could be "111" or full URL)
                                        if entry_id:
                                            entry_id_str = str(entry_id)
                                            # Try multiple matching strategies
                                            if entry_id_str in (item_ref_str, item_ref_clean) or item_ref_str.endswith(
                                                (f"/{entry_id_str}", f"#{entry_id_str}")
                                            ):
                                                imported_proposal = proposal
                                                logger.debug(f"Found proposal '{proposal.name}' by source_id match")
                                                break
                        if imported_proposal:
                            break

                    # If not found by ID, use the most recently added proposal
                    # (the one we just imported should be the last one)
                    if not imported_proposal and project_bundle.change_tracking.proposals:
                        # Get proposals as list and take the last one
                        proposal_list = list(project_bundle.change_tracking.proposals.values())
                        if proposal_list:
                            imported_proposal = proposal_list[-1]
                            # Verify this proposal was just imported by checking if it has source_tracking
                            # and matches the adapter type
                            if imported_proposal.source_tracking:
                                source_tool = imported_proposal.source_tracking.tool
                                if source_tool != adapter_type:
                                    # Tool mismatch - might not be the right one, but log and use as fallback
                                    import logging

                                    logger = logging.getLogger(__name__)
                                    logger.debug(
                                        f"Fallback proposal has different source tool ({source_tool} vs {adapter_type}), "
                                        f"but using it anyway as it's the most recent proposal"
                                    )

                    # Create OpenSpec files from proposal
                    if imported_proposal:
                        file_warnings = self._write_openspec_change_from_proposal(imported_proposal, bridge_config)
                        warnings.extend(file_warnings)
                    else:
                        # Log warning if proposal not found
                        import logging

                        logger = logging.getLogger(__name__)
                        warning_msg = (
                            f"Could not find imported proposal for backlog item '{item_ref}'. "
                            f"OpenSpec files will not be created. "
                            f"Proposals in bundle: {list(project_bundle.change_tracking.proposals.keys()) if project_bundle.change_tracking.proposals else 'none'}"
                        )
                        logger.warning(warning_msg)
                        warnings.append(warning_msg)

                operations.append(
                    SyncOperation(
                        artifact_key=artifact_key,
                        feature_id=str(item_ref),
                        direction="import",
                        bundle_name=bundle_name,
                    )
                )
            except Exception as e:
                errors.append(f"Failed to import backlog item '{item_ref}': {e}")

        if operations:
            save_project_bundle(project_bundle, bundle_dir, atomic=True)

        return SyncResult(
            success=len(errors) == 0,
            operations=operations,
            errors=errors,
            warnings=warnings,
        )

    @beartype
    @require(lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0, "Bundle name must be non-empty")
    @ensure(lambda result: isinstance(result, SyncResult), "Must return SyncResult")
    def export_backlog_from_bundle(
        self,
        adapter_type: str,
        bundle_name: str,
        adapter_kwargs: dict[str, Any] | None = None,
        update_existing: bool = False,
        change_ids: list[str] | None = None,
    ) -> SyncResult:
        """
        Export backlog items stored in a project bundle to a backlog adapter.

        Args:
            adapter_type: Backlog adapter type (github, ado)
            bundle_name: Project bundle name
            adapter_kwargs: Adapter-specific kwargs for initialization
            update_existing: If True, update existing backlog items with stored content
            change_ids: Optional list of change IDs to export (filter)

        Returns:
            SyncResult with operation details
        """
        from specfact_cli.models.source_tracking import SourceTracking
        from specfact_cli.utils.structure import SpecFactStructure

        operations: list[SyncOperation] = []
        errors: list[str] = []
        warnings: list[str] = []

        adapter_kwargs = adapter_kwargs or {}
        adapter = AdapterRegistry.get_adapter(adapter_type, **adapter_kwargs)
        bridge_config = adapter.generate_bridge_config(self.repo_path)

        bundle_dir = SpecFactStructure.project_dir(base_path=self.repo_path, bundle_name=bundle_name)
        if not bundle_dir.exists():
            errors.append(f"Project bundle not found: {bundle_dir}")
            return SyncResult(success=False, operations=operations, errors=errors, warnings=warnings)

        project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        change_tracking = project_bundle.change_tracking or project_bundle.manifest.change_tracking
        if not change_tracking or not change_tracking.proposals:
            warnings.append(f"No change proposals found in bundle '{bundle_name}'")
            return SyncResult(success=True, operations=operations, errors=errors, warnings=warnings)

        target_repo = None
        if adapter_type == "github":
            repo_owner = getattr(adapter, "repo_owner", None)
            repo_name = getattr(adapter, "repo_name", None)
            if repo_owner and repo_name:
                target_repo = f"{repo_owner}/{repo_name}"
        elif adapter_type == "ado":
            org = getattr(adapter, "org", None)
            project = getattr(adapter, "project", None)
            if org and project:
                target_repo = f"{org}/{project}"

        for proposal in change_tracking.proposals.values():
            if change_ids and proposal.name not in change_ids:
                continue

            if proposal.source_tracking is None:
                proposal.source_tracking = SourceTracking(tool=adapter_type, source_metadata={})

            entries = self._get_backlog_entries(proposal)
            if isinstance(proposal.source_tracking.source_metadata, dict):
                proposal.source_tracking.source_metadata["backlog_entries"] = entries
            target_entry = None
            if target_repo:
                target_entry = next(
                    (entry for entry in entries if isinstance(entry, dict) and entry.get("source_repo") == target_repo),
                    None,
                )
            if not target_entry:
                target_entry = next(
                    (
                        entry
                        for entry in entries
                        if isinstance(entry, dict)
                        and entry.get("source_type") == adapter_type
                        and entry.get("source_id")
                    ),
                    None,
                )

            proposal_dict: dict[str, Any] = {
                "change_id": proposal.name,
                "title": proposal.title,
                "description": proposal.description,
                "rationale": proposal.rationale,
                "status": proposal.status,
                "source_tracking": entries,
            }

            # Extract source state from backlog entries (for cross-adapter sync state preservation)
            # Check for source backlog entry from a different adapter (generic approach)
            source_state = None
            source_type = None
            for entry in entries:
                if isinstance(entry, dict):
                    entry_type = entry.get("source_type", "").lower()
                    # Look for entry from a different adapter (not the target adapter)
                    if entry_type and entry_type != adapter_type.lower():
                        source_metadata = entry.get("source_metadata", {})
                        entry_source_state = source_metadata.get("source_state")
                        if entry_source_state:
                            source_state = entry_source_state
                            source_type = entry_type
                            break

            if source_state and source_type:
                proposal_dict["source_state"] = source_state
                proposal_dict["source_type"] = source_type

            if isinstance(proposal.source_tracking.source_metadata, dict):
                raw_title = proposal.source_tracking.source_metadata.get("raw_title")
                raw_body = proposal.source_tracking.source_metadata.get("raw_body")
                if raw_title:
                    proposal_dict["raw_title"] = raw_title
                if raw_body:
                    proposal_dict["raw_body"] = raw_body

            try:
                if target_entry and target_entry.get("source_id"):
                    last_synced = target_entry.get("source_metadata", {}).get("last_synced_status")
                    if last_synced != proposal.status:
                        adapter.export_artifact("change_status", proposal_dict, bridge_config)
                        operations.append(
                            SyncOperation(
                                artifact_key="change_status",
                                feature_id=proposal.name,
                                direction="export",
                                bundle_name=bundle_name,
                            )
                        )
                        target_entry.setdefault("source_metadata", {})["last_synced_status"] = proposal.status

                    if update_existing:
                        export_result = adapter.export_artifact("change_proposal_update", proposal_dict, bridge_config)
                        operations.append(
                            SyncOperation(
                                artifact_key="change_proposal_update",
                                feature_id=proposal.name,
                                direction="export",
                                bundle_name=bundle_name,
                            )
                        )
                    else:
                        export_result = {}
                else:
                    export_result = adapter.export_artifact("change_proposal", proposal_dict, bridge_config)
                    operations.append(
                        SyncOperation(
                            artifact_key="change_proposal",
                            feature_id=proposal.name,
                            direction="export",
                            bundle_name=bundle_name,
                        )
                    )

                # Only build backlog entry if export_result is a dict (backlog adapters return dicts)
                # Non-backlog adapters (like SpecKit) return Path, which we skip
                if isinstance(export_result, dict):
                    entry_update = self._build_backlog_entry_from_result(
                        adapter_type,
                        target_repo,
                        export_result,
                        proposal.status,
                    )
                    if entry_update:
                        entries = self._upsert_backlog_entry(entries, entry_update)
                        proposal.source_tracking.source_metadata["backlog_entries"] = entries
            except Exception as e:
                errors.append(f"Failed to export '{proposal.name}' to {adapter_type}: {e}")

        if operations:
            save_project_bundle(project_bundle, bundle_dir, atomic=True)

        return SyncResult(
            success=len(errors) == 0,
            operations=operations,
            errors=errors,
            warnings=warnings,
        )

    def _build_backlog_entry_from_result(
        self,
        adapter_type: str,
        target_repo: str | None,
        export_result: dict[str, Any],
        status: str,
    ) -> dict[str, Any] | None:
        """
        Build a backlog entry from adapter export result.

        Args:
            adapter_type: Backlog adapter type
            target_repo: Target repository identifier
            export_result: Adapter export response dict
            status: Proposal status for sync metadata

        Returns:
            Backlog entry dict or None if no IDs were returned
        """
        if adapter_type == "github":
            source_id = export_result.get("issue_number")
            source_url = export_result.get("issue_url")
        elif adapter_type == "ado":
            source_id = export_result.get("work_item_id")
            source_url = export_result.get("work_item_url")
        else:
            return None

        if source_id is None:
            return None

        return {
            "source_id": str(source_id),
            "source_url": source_url or "",
            "source_type": adapter_type,
            "source_repo": target_repo or "",
            "source_metadata": {"last_synced_status": status},
        }

    def _get_backlog_entries(self, proposal: Any) -> list[dict[str, Any]]:
        """
        Retrieve backlog entries stored on a change proposal.

        Args:
            proposal: ChangeProposal instance

        Returns:
            List of backlog entry dicts
        """
        if not hasattr(proposal, "source_tracking") or not proposal.source_tracking:
            return []
        source_metadata = proposal.source_tracking.source_metadata
        if not isinstance(source_metadata, dict):
            return []
        entries = source_metadata.get("backlog_entries")
        if isinstance(entries, list):
            return [entry for entry in entries if isinstance(entry, dict)]

        fallback_id = source_metadata.get("source_id")
        fallback_url = source_metadata.get("source_url")
        fallback_repo = source_metadata.get("source_repo", "")
        fallback_type = source_metadata.get("source_type") or getattr(proposal.source_tracking, "tool", None)
        if fallback_id or fallback_url:
            return [
                {
                    "source_id": str(fallback_id) if fallback_id is not None else None,
                    "source_url": fallback_url or "",
                    "source_type": fallback_type or "",
                    "source_repo": fallback_repo,
                    "source_metadata": {},
                }
            ]

        return []

    def _upsert_backlog_entry(self, entries: list[dict[str, Any]], new_entry: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Insert or update a backlog entry in the entries list.

        Args:
            entries: Existing backlog entries
            new_entry: New or updated backlog entry

        Returns:
            Updated backlog entries list
        """
        new_repo = new_entry.get("source_repo")
        new_type = new_entry.get("source_type")
        new_id = new_entry.get("source_id")
        for idx, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            if new_repo and entry.get("source_repo") == new_repo and entry.get("source_type") == new_type:
                entries[idx] = {**entry, **new_entry}
                return entries
            if new_id and entry.get("source_id") == new_id and entry.get("source_type") == new_type:
                entries[idx] = {**entry, **new_entry}
                return entries
        entries.append(new_entry)
        return entries

    def _normalize_source_tracking(
        self, source_tracking: list[dict[str, Any]] | dict[str, Any] | None
    ) -> list[dict[str, Any]]:
        """
        Normalize source_tracking to a list of entries (for backward compatibility).

        Args:
            source_tracking: Source tracking (list or single dict)

        Returns:
            List of source tracking entries
        """
        if not source_tracking:
            return []
        if isinstance(source_tracking, dict):
            return [source_tracking]
        if isinstance(source_tracking, list):
            return source_tracking
        return []

    def _dedupe_duplicate_sections(self, text: str) -> str:
        """
        Remove duplicated level-2 sections (##) while preserving the first occurrence.

        Args:
            text: Markdown content to de-duplicate

        Returns:
            De-duplicated markdown content
        """
        if not text:
            return text
        parts = re.split(r"(?m)^##\s+([^\n]+)\s*\n", text)
        if len(parts) < 3:
            return text
        preamble = parts[0].rstrip()
        seen: set[str] = set()
        blocks: list[str] = []
        if preamble.strip():
            blocks.append(preamble.rstrip())
        for i in range(1, len(parts), 2):
            header = parts[i].strip()
            body = parts[i + 1].rstrip()
            if header in seen:
                continue
            seen.add(header)
            blocks.append(f"## {header}\n{body}".rstrip())
        return "\n\n".join(blocks).strip()

    def _verify_work_item_exists(
        self,
        issue_number: str | int | None,
        target_entry: dict[str, Any] | None,
        adapter_type: str,
        adapter: Any,
        ado_org: str | None,
        ado_project: str | None,
        proposal: dict[str, Any],
        warnings: list[str],
    ) -> tuple[str | int | None, bool]:
        """
        Verify if work item/issue exists in external tool (handles deleted items).

        Args:
            issue_number: Current issue/work item number
            target_entry: Source tracking entry
            adapter_type: Adapter type (github, ado, etc.)
            adapter: Adapter instance
            ado_org: ADO organization (for ADO adapter)
            ado_project: ADO project (for ADO adapter)
            proposal: Change proposal dict
            warnings: Warnings list to append to

        Returns:
            Tuple of (issue_number, work_item_was_deleted)
        """
        work_item_was_deleted = False

        if issue_number and target_entry:
            entry_type = target_entry.get("source_type", "").lower()

            # For ADO, verify work item exists (it might have been deleted)
            if (
                entry_type == "ado"
                and adapter_type.lower() == "ado"
                and ado_org
                and ado_project
                and hasattr(adapter, "_work_item_exists")
            ):
                try:
                    work_item_exists = adapter._work_item_exists(issue_number, ado_org, ado_project)
                    if not work_item_exists:
                        # Work item was deleted - clear source_id to allow recreation
                        warnings.append(
                            f"Work item #{issue_number} for '{proposal.get('change_id', 'unknown')}' "
                            f"no longer exists in ADO (may have been deleted). "
                            f"Will create a new work item."
                        )
                        # Clear source_id to allow creation of new work item
                        issue_number = None
                        work_item_was_deleted = True
                except Exception as e:
                    # On error checking existence, log warning but allow creation (safer)
                    warnings.append(f"Could not verify work item #{issue_number} existence: {e}. Proceeding with sync.")

        return issue_number, work_item_was_deleted

    def _search_existing_github_issue(
        self,
        change_id: str,
        repo_owner: str,
        repo_name: str,
        target_repo: str | None,
        warnings: list[str],
    ) -> tuple[dict[str, Any] | None, str | None]:
        """
        Search for existing GitHub issue by change proposal ID.

        Args:
            change_id: Change proposal ID
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            target_repo: Target repository identifier
            warnings: Warnings list to append to

        Returns:
            Tuple of (target_entry, issue_number) if found, (None, None) otherwise
        """
        try:
            import requests

            from specfact_cli.adapters.registry import AdapterRegistry

            adapter_instance = AdapterRegistry.get_adapter("github")
            if adapter_instance and hasattr(adapter_instance, "api_token") and adapter_instance.api_token:
                # Search for issues containing the change proposal ID in the footer
                search_url = f"{adapter_instance.base_url}/search/issues"
                search_query = f'repo:{repo_owner}/{repo_name} "OpenSpec Change Proposal: `{change_id}`" in:body'
                headers = {
                    "Authorization": f"token {adapter_instance.api_token}",
                    "Accept": "application/vnd.github.v3+json",
                }
                params = {"q": search_query}
                search_response = requests.get(search_url, headers=headers, params=params, timeout=30)
                if search_response.status_code == 200:
                    search_results = search_response.json()
                    items = search_results.get("items", [])
                    if items:
                        # Found existing issue - use it instead of creating a new one
                        existing_issue = items[0]  # Use the first match
                        existing_issue_number = existing_issue.get("number")
                        existing_issue_url = existing_issue.get("html_url", "")
                        warnings.append(
                            f"Found existing GitHub issue #{existing_issue_number} for change proposal '{change_id}'. "
                            f"Will update it instead of creating a new issue."
                        )
                        # Create source_tracking entry for the found issue
                        target_entry = {
                            "source_type": "github",
                            "source_id": str(existing_issue_number),
                            "source_url": existing_issue_url,
                            "source_repo": target_repo or f"{repo_owner}/{repo_name}",
                            "source_metadata": {},
                        }
                        return target_entry, str(existing_issue_number)
        except Exception as e:
            # If search fails, proceed with creation (safer than blocking)
            warnings.append(
                f"Could not search for existing GitHub issue for '{change_id}': {e}. Proceeding with creation."
            )

        return None, None

    def _update_existing_issue(
        self,
        proposal: dict[str, Any],
        target_entry: dict[str, Any],
        issue_number: str | int,
        adapter: Any,
        adapter_type: str,
        target_repo: str | None,
        source_tracking_list: list[dict[str, Any]],
        source_tracking_raw: dict[str, Any] | list[dict[str, Any]],
        repo_owner: str | None,
        repo_name: str | None,
        ado_org: str | None,
        ado_project: str | None,
        update_existing: bool,
        import_from_tmp: bool,
        tmp_file: Path | None,
        should_sanitize: bool | None,
        track_code_changes: bool,
        add_progress_comment: bool,
        code_repo_path: Path | None,
        operations: list[Any],
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """
        Update existing issue/work item with new status, metadata, and content.

        Args:
            proposal: Change proposal dict
            target_entry: Source tracking entry for this repository
            issue_number: Issue/work item number
            adapter: Adapter instance
            adapter_type: Adapter type (github, ado, etc.)
            target_repo: Target repository identifier
            source_tracking_list: Normalized source tracking list
            source_tracking_raw: Original source tracking (dict or list)
            repo_owner: Repository owner (for GitHub)
            repo_name: Repository name (for GitHub)
            ado_org: ADO organization (for ADO)
            ado_project: ADO project (for ADO)
            update_existing: Whether to update content when hash changes
            import_from_tmp: Whether importing from temporary file
            tmp_file: Temporary file path
            should_sanitize: Whether to sanitize content
            operations: Operations list to append to
            errors: Errors list to append to
            warnings: Warnings list to append to
        """
        # Issue exists - check if status changed or metadata needs update
        source_metadata = target_entry.get("source_metadata", {})
        if not isinstance(source_metadata, dict):
            source_metadata = {}
        last_synced_status = source_metadata.get("last_synced_status")
        current_status = proposal.get("status")

        if last_synced_status != current_status:
            # Status changed - update issue
            adapter.export_artifact(
                artifact_key="change_status",
                artifact_data=proposal,
                bridge_config=self.bridge_config,
            )
            # Track status update operation
            operations.append(
                SyncOperation(
                    artifact_key="change_status",
                    feature_id=proposal.get("change_id", "unknown"),
                    direction="export",
                    bundle_name="openspec",
                )
            )

        # Always update metadata to ensure it reflects the current sync operation
        source_metadata = target_entry.get("source_metadata", {})
        if not isinstance(source_metadata, dict):
            source_metadata = {}
        updated_entry = {
            **target_entry,
            "source_metadata": {
                **source_metadata,
                "last_synced_status": current_status,
                "sanitized": should_sanitize if should_sanitize is not None else False,
            },
        }

        # Always update source_tracking metadata to reflect current sync operation
        if target_repo:
            source_tracking_list = self._update_source_tracking_entry(source_tracking_list, target_repo, updated_entry)
            proposal["source_tracking"] = source_tracking_list
        else:
            # Backward compatibility: update single dict entry directly
            if isinstance(source_tracking_raw, dict):
                proposal["source_tracking"] = updated_entry
            else:
                # List of entries - update the matching entry
                for i, entry in enumerate(source_tracking_list):
                    if isinstance(entry, dict):
                        entry_id = entry.get("source_id")
                        entry_repo = entry.get("source_repo")
                        updated_id = updated_entry.get("source_id")
                        updated_repo = updated_entry.get("source_repo")

                        if (entry_id and entry_id == updated_id) or (entry_repo and entry_repo == updated_repo):
                            source_tracking_list[i] = updated_entry
                            break
                proposal["source_tracking"] = source_tracking_list

        # Track metadata update operation (even if status didn't change)
        if last_synced_status == current_status:
            operations.append(
                SyncOperation(
                    artifact_key="change_proposal_metadata",
                    feature_id=proposal.get("change_id", "unknown"),
                    direction="export",
                    bundle_name="openspec",
                )
            )

        # Check if content changed (when update_existing is enabled)
        if update_existing:
            self._update_issue_content_if_needed(
                proposal,
                target_entry,
                issue_number,
                adapter,
                adapter_type,
                target_repo,
                source_tracking_list,
                repo_owner,
                repo_name,
                ado_org,
                ado_project,
                import_from_tmp,
                tmp_file,
                operations,
                errors,
            )

        # Code change tracking and progress comments (when enabled)
        if track_code_changes or add_progress_comment:
            self._handle_code_change_tracking(
                proposal,
                target_entry,
                target_repo,
                source_tracking_list,
                adapter,
                track_code_changes,
                add_progress_comment,
                code_repo_path,
                should_sanitize,
                operations,
                errors,
                warnings,
            )

    def _update_issue_content_if_needed(
        self,
        proposal: dict[str, Any],
        target_entry: dict[str, Any],
        issue_number: str | int,
        adapter: Any,
        adapter_type: str,
        target_repo: str | None,
        source_tracking_list: list[dict[str, Any]],
        repo_owner: str | None,
        repo_name: str | None,
        ado_org: str | None,
        ado_project: str | None,
        import_from_tmp: bool,
        tmp_file: Path | None,
        operations: list[Any],
        errors: list[str],
    ) -> None:
        """
        Update issue/work item content if hash changed or title needs update.

        Args:
            proposal: Change proposal dict
            target_entry: Source tracking entry
            issue_number: Issue/work item number
            adapter: Adapter instance
            adapter_type: Adapter type
            target_repo: Target repository identifier
            source_tracking_list: Source tracking list
            repo_owner: Repository owner (for GitHub)
            repo_name: Repository name (for GitHub)
            ado_org: ADO organization (for ADO)
            ado_project: ADO project (for ADO)
            import_from_tmp: Whether importing from temporary file
            tmp_file: Temporary file path
            operations: Operations list to append to
            errors: Errors list to append to
        """
        # Handle sanitized content updates (when import_from_tmp is used)
        if import_from_tmp:
            change_id = proposal.get("change_id", "unknown")
            sanitized_file = tmp_file or (Path(tempfile.gettempdir()) / f"specfact-proposal-{change_id}-sanitized.md")
            if sanitized_file.exists():
                sanitized_content = sanitized_file.read_text(encoding="utf-8")
                proposal_for_hash = {
                    "rationale": "",
                    "description": sanitized_content,
                }
                current_hash = self._calculate_content_hash(proposal_for_hash)
            else:
                current_hash = self._calculate_content_hash(proposal)
        else:
            current_hash = self._calculate_content_hash(proposal)

        # Get stored hash from target repository entry
        stored_hash = None
        source_metadata = target_entry.get("source_metadata", {})
        if isinstance(source_metadata, dict):
            stored_hash = source_metadata.get("content_hash")

        # Check if title or state needs update
        current_issue_title = None
        current_issue_state = None
        needs_title_update = False
        needs_state_update = False
        if target_entry:
            issue_num = target_entry.get("source_id")
            if issue_num:
                try:
                    from specfact_cli.adapters.registry import AdapterRegistry

                    adapter_instance = AdapterRegistry.get_adapter(adapter_type)
                    if adapter_instance and hasattr(adapter_instance, "api_token"):
                        proposal_title = proposal.get("title", "")
                        proposal_status = proposal.get("status", "proposed")

                        if adapter_type.lower() == "github":
                            import requests

                            url = f"{adapter_instance.base_url}/repos/{repo_owner}/{repo_name}/issues/{issue_num}"
                            headers = {
                                "Authorization": f"token {adapter_instance.api_token}",
                                "Accept": "application/vnd.github.v3+json",
                            }
                            response = requests.get(url, headers=headers, timeout=30)
                            response.raise_for_status()
                            issue_data = response.json()
                            current_issue_title = issue_data.get("title", "")
                            current_issue_state = issue_data.get("state", "open")
                            needs_title_update = (
                                current_issue_title and proposal_title and current_issue_title != proposal_title
                            )
                            should_close = proposal_status in ("applied", "deprecated", "discarded")
                            desired_state = "closed" if should_close else "open"
                            needs_state_update = current_issue_state != desired_state
                        elif adapter_type.lower() == "ado":
                            if hasattr(adapter_instance, "_get_work_item_data") and ado_org and ado_project:
                                work_item_data = adapter_instance._get_work_item_data(issue_num, ado_org, ado_project)
                                if work_item_data:
                                    current_issue_title = work_item_data.get("title", "")
                                    current_issue_state = work_item_data.get("state", "")
                                    needs_title_update = (
                                        current_issue_title and proposal_title and current_issue_title != proposal_title
                                    )
                                    desired_ado_state = adapter_instance.map_openspec_status_to_backlog(proposal_status)
                                    needs_state_update = current_issue_state != desired_ado_state
                except Exception:
                    pass

        # Check if we need to add a comment for applied status
        needs_comment_for_applied = False
        if proposal.get("status") == "applied" and target_entry:
            issue_num = target_entry.get("source_id")
            if issue_num and adapter_type.lower() == "github":
                try:
                    import requests

                    from specfact_cli.adapters.registry import AdapterRegistry

                    adapter_instance = AdapterRegistry.get_adapter(adapter_type)
                    if adapter_instance and hasattr(adapter_instance, "api_token") and adapter_instance.api_token:
                        url = f"{adapter_instance.base_url}/repos/{repo_owner}/{repo_name}/issues/{issue_num}"
                        headers = {
                            "Authorization": f"token {adapter_instance.api_token}",
                            "Accept": "application/vnd.github.v3+json",
                        }
                        response = requests.get(url, headers=headers, timeout=30)
                        response.raise_for_status()
                        issue_data = response.json()
                        current_issue_state = issue_data.get("state", "open")
                        if current_issue_state == "closed":
                            needs_comment_for_applied = True
                except Exception:
                    pass

        if stored_hash != current_hash or needs_title_update or needs_state_update or needs_comment_for_applied:
            # Content changed, title needs update, state needs update, or need to add comment
            try:
                if import_from_tmp:
                    change_id = proposal.get("change_id", "unknown")
                    sanitized_file = tmp_file or (
                        Path(tempfile.gettempdir()) / f"specfact-proposal-{change_id}-sanitized.md"
                    )
                    if sanitized_file.exists():
                        sanitized_content = sanitized_file.read_text(encoding="utf-8")
                        proposal_for_update = {
                            **proposal,
                            "description": sanitized_content,
                            "rationale": "",
                        }
                    else:
                        proposal_for_update = proposal
                else:
                    proposal_for_update = proposal

                # Determine code repository path for branch verification
                code_repo_path = None
                if repo_owner and repo_name:
                    code_repo_path = self._find_code_repo_path(repo_owner, repo_name)

                if needs_comment_for_applied and not (
                    stored_hash != current_hash or needs_title_update or needs_state_update
                ):
                    # Only add comment, no body/state update
                    proposal_with_repo = {
                        **proposal_for_update,
                        "_code_repo_path": str(code_repo_path) if code_repo_path else None,
                    }
                    adapter.export_artifact(
                        artifact_key="change_proposal_comment",
                        artifact_data=proposal_with_repo,
                        bridge_config=self.bridge_config,
                    )
                else:
                    # Add code repository path to artifact_data for branch verification
                    proposal_with_repo = {
                        **proposal_for_update,
                        "_code_repo_path": str(code_repo_path) if code_repo_path else None,
                    }
                    adapter.export_artifact(
                        artifact_key="change_proposal_update",
                        artifact_data=proposal_with_repo,
                        bridge_config=self.bridge_config,
                    )

                # Update stored hash in target repository entry
                if target_entry:
                    source_metadata = target_entry.get("source_metadata", {})
                    if not isinstance(source_metadata, dict):
                        source_metadata = {}
                    updated_entry = {
                        **target_entry,
                        "source_metadata": {
                            **source_metadata,
                            "content_hash": current_hash,
                        },
                    }
                    if target_repo:
                        source_tracking_list = self._update_source_tracking_entry(
                            source_tracking_list, target_repo, updated_entry
                        )
                        proposal["source_tracking"] = source_tracking_list

                operations.append(
                    SyncOperation(
                        artifact_key="change_proposal_update",
                        feature_id=proposal.get("change_id", "unknown"),
                        direction="export",
                        bundle_name="openspec",
                    )
                )
            except Exception as e:
                errors.append(f"Failed to update issue body for {proposal.get('change_id', 'unknown')}: {e}")

    def _handle_code_change_tracking(
        self,
        proposal: dict[str, Any],
        target_entry: dict[str, Any] | None,
        target_repo: str | None,
        source_tracking_list: list[dict[str, Any]],
        adapter: Any,
        track_code_changes: bool,
        add_progress_comment: bool,
        code_repo_path: Path | None,
        should_sanitize: bool | None,
        operations: list[Any],
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """
        Handle code change tracking and add progress comments if enabled.
        """
        from specfact_cli.utils.code_change_detector import (
            calculate_comment_hash,
            detect_code_changes,
            format_progress_comment,
        )

        change_id = proposal.get("change_id", "unknown")
        progress_data: dict[str, Any] = {}

        if track_code_changes:
            try:
                last_detection = None
                if target_entry:
                    source_metadata = target_entry.get("source_metadata", {})
                    if isinstance(source_metadata, dict):
                        last_detection = source_metadata.get("last_code_change_detected")

                code_repo = code_repo_path if code_repo_path else self.repo_path
                code_changes = detect_code_changes(
                    repo_path=code_repo,
                    change_id=change_id,
                    since_timestamp=last_detection,
                )

                if code_changes.get("has_changes"):
                    progress_data = code_changes
                else:
                    return  # No code changes detected

            except Exception as e:
                errors.append(f"Failed to detect code changes for {change_id}: {e}")
                return

        if add_progress_comment and not progress_data:
            from datetime import UTC, datetime

            progress_data = {
                "summary": "Manual progress update",
                "detection_timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            }

        if progress_data:
            comment_text = format_progress_comment(
                progress_data, sanitize=should_sanitize if should_sanitize is not None else False
            )
            comment_hash = calculate_comment_hash(comment_text)

            progress_comments = []
            if target_entry:
                source_metadata = target_entry.get("source_metadata", {})
                if isinstance(source_metadata, dict):
                    progress_comments = source_metadata.get("progress_comments", [])

            is_duplicate = False
            if isinstance(progress_comments, list):
                for existing_comment in progress_comments:
                    if isinstance(existing_comment, dict):
                        existing_hash = existing_comment.get("comment_hash")
                        if existing_hash == comment_hash:
                            is_duplicate = True
                            break

            if not is_duplicate:
                try:
                    proposal_with_progress = {
                        **proposal,
                        "source_tracking": source_tracking_list,
                        "progress_data": progress_data,
                        "sanitize": should_sanitize if should_sanitize is not None else False,
                    }
                    adapter.export_artifact(
                        artifact_key="code_change_progress",
                        artifact_data=proposal_with_progress,
                        bridge_config=self.bridge_config,
                    )

                    if target_entry:
                        source_metadata = target_entry.get("source_metadata", {})
                        if not isinstance(source_metadata, dict):
                            source_metadata = {}
                        progress_comments = source_metadata.get("progress_comments", [])
                        if not isinstance(progress_comments, list):
                            progress_comments = []

                        progress_comments.append(
                            {
                                "comment_hash": comment_hash,
                                "timestamp": progress_data.get("detection_timestamp"),
                                "summary": progress_data.get("summary", ""),
                            }
                        )

                        updated_entry = {
                            **target_entry,
                            "source_metadata": {
                                **source_metadata,
                                "progress_comments": progress_comments,
                                "last_code_change_detected": progress_data.get("detection_timestamp"),
                            },
                        }

                        if target_repo:
                            source_tracking_list = self._update_source_tracking_entry(
                                source_tracking_list, target_repo, updated_entry
                            )
                            proposal["source_tracking"] = source_tracking_list

                    operations.append(
                        SyncOperation(
                            artifact_key="code_change_progress",
                            feature_id=change_id,
                            direction="export",
                            bundle_name="openspec",
                        )
                    )
                    self._save_openspec_change_proposal(proposal)
                except Exception as e:
                    errors.append(f"Failed to add progress comment for {change_id}: {e}")
            else:
                warnings.append(f"Skipped duplicate progress comment for {change_id}")

    def _update_source_tracking_entry(
        self,
        source_tracking_list: list[dict[str, Any]],
        target_repo: str,
        entry_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Update or add source tracking entry for a specific repository.

        Args:
            source_tracking_list: List of source tracking entries
            target_repo: Target repository identifier
            entry_data: Entry data to update/add

        Returns:
            Updated list of source tracking entries
        """
        # Ensure source_repo is set in entry_data
        if "source_repo" not in entry_data:
            entry_data["source_repo"] = target_repo

        entry_type = entry_data.get("source_type", "").lower()
        new_source_id = entry_data.get("source_id")

        # Find existing entry for this repo
        for i, entry in enumerate(source_tracking_list):
            if not isinstance(entry, dict):
                continue

            entry_repo = entry.get("source_repo")
            entry_type_existing = entry.get("source_type", "").lower()

            # Primary match: exact source_repo match
            if entry_repo == target_repo:
                # Update existing entry
                source_tracking_list[i] = {**entry, **entry_data}
                return source_tracking_list

            # Secondary match: for ADO, match by org + source_id if project name differs
            # This handles cases where ADO URLs contain GUIDs instead of project names
            if entry_type == "ado" and entry_type_existing == "ado" and entry_repo and target_repo:
                entry_org = entry_repo.split("/")[0] if "/" in entry_repo else None
                target_org = target_repo.split("/")[0] if "/" in target_repo else None
                entry_source_id = entry.get("source_id")

                if entry_org and target_org and entry_org == target_org:
                    # Org matches
                    if entry_source_id and new_source_id and entry_source_id == new_source_id:
                        # Same work item - update existing entry
                        source_tracking_list[i] = {**entry, **entry_data}
                        return source_tracking_list
                    # Org matches but different/no source_id - update repo identifier to match target
                    # This handles project name changes or encoding differences
                    updated_entry = {**entry, **entry_data}
                    updated_entry["source_repo"] = target_repo  # Update to correct repo identifier
                    source_tracking_list[i] = updated_entry
                    return source_tracking_list

        # No existing entry found - add new one
        source_tracking_list.append(entry_data)
        return source_tracking_list

    def _parse_source_tracking_entry(self, entry_content: str, repo_name: str | None) -> dict[str, Any] | None:
        """
        Parse a single source tracking entry from markdown content.

        Args:
            entry_content: Markdown content for this entry
            repo_name: Repository name (if specified in header)

        Returns:
            Source tracking entry dict or None if no valid entry found
        """
        entry: dict[str, Any] = {}
        if repo_name:
            entry["source_repo"] = repo_name

        # Extract GitHub issue number
        issue_match = re.search(r"\*\*.*Issue\*\*:\s*#(\d+)", entry_content)
        if issue_match:
            entry["source_id"] = issue_match.group(1)

        # Extract issue URL (handle angle brackets for MD034 compliance)
        url_match = re.search(r"\*\*Issue URL\*\*:\s*<?(https://[^\s>]+)>?", entry_content)
        if url_match:
            entry["source_url"] = url_match.group(1)
            # If no repo_name provided, try to extract from URL
            if not repo_name:
                # Try GitHub URL pattern
                url_repo_match = re.search(r"github\.com/([^/]+/[^/]+)/", entry["source_url"])
                if url_repo_match:
                    entry["source_repo"] = url_repo_match.group(1)
                else:
                    # Try ADO URL pattern: dev.azure.com/{org}/{project}/...
                    ado_repo_match = re.search(r"dev\.azure\.com/([^/]+)/([^/]+)/", entry["source_url"])
                    if ado_repo_match:
                        entry["source_repo"] = f"{ado_repo_match.group(1)}/{ado_repo_match.group(2)}"

        # Extract source type
        type_match = re.search(r"\*\*(\w+)\s+Issue\*\*:", entry_content)
        if type_match:
            entry["source_type"] = type_match.group(1).lower()

        # Extract last synced status
        status_match = re.search(r"\*\*Last Synced Status\*\*:\s*(\w+)", entry_content)
        if status_match:
            if "source_metadata" not in entry:
                entry["source_metadata"] = {}
            entry["source_metadata"]["last_synced_status"] = status_match.group(1)

        # Extract sanitized flag
        sanitized_match = re.search(r"\*\*Sanitized\*\*:\s*(true|false)", entry_content, re.IGNORECASE)
        if sanitized_match:
            if "source_metadata" not in entry:
                entry["source_metadata"] = {}
            entry["source_metadata"]["sanitized"] = sanitized_match.group(1).lower() == "true"

        # Extract content_hash from HTML comment
        hash_match = re.search(r"<!--\s*content_hash:\s*([a-f0-9]{16})\s*-->", entry_content)
        if hash_match:
            if "source_metadata" not in entry:
                entry["source_metadata"] = {}
            entry["source_metadata"]["content_hash"] = hash_match.group(1)

        # Extract progress_comments from HTML comment
        progress_comments_match = re.search(r"<!--\s*progress_comments:\s*(\[.*?\])\s*-->", entry_content, re.DOTALL)
        if progress_comments_match:
            import json

            try:
                progress_comments = json.loads(progress_comments_match.group(1))
                if "source_metadata" not in entry:
                    entry["source_metadata"] = {}
                entry["source_metadata"]["progress_comments"] = progress_comments
            except (json.JSONDecodeError, ValueError):
                # Ignore invalid JSON
                pass

        # Extract last_code_change_detected from HTML comment
        last_detection_match = re.search(r"<!--\s*last_code_change_detected:\s*([^\s]+)\s*-->", entry_content)
        if last_detection_match:
            if "source_metadata" not in entry:
                entry["source_metadata"] = {}
            entry["source_metadata"]["last_code_change_detected"] = last_detection_match.group(1)

        # Extract source_repo from hidden comment (for single entries)
        # This is critical for ADO where URLs contain GUIDs instead of project names
        source_repo_match = re.search(r"<!--\s*source_repo:\s*([^>]+?)\s*-->", entry_content)
        if source_repo_match:
            entry["source_repo"] = source_repo_match.group(1).strip()
        # Also check for source_repo in the content itself (might be in a comment or elsewhere)
        elif not entry.get("source_repo"):
            # Try to find it in the content as a fallback
            source_repo_in_content = re.search(r"source_repo[:\s]+([^\n]+)", entry_content, re.IGNORECASE)
            if source_repo_in_content:
                entry["source_repo"] = source_repo_in_content.group(1).strip()

        # Only return entry if it has at least source_id or source_url
        if entry.get("source_id") or entry.get("source_url"):
            return entry
        return None

    def _calculate_content_hash(self, proposal: dict[str, Any]) -> str:
        """
        Calculate content hash for change proposal (Why + What Changes sections).

        Args:
            proposal: Change proposal dict with description and rationale

        Returns:
            SHA-256 hash (first 16 characters) of proposal content
        """
        rationale = proposal.get("rationale", "")
        description = proposal.get("description", "")
        # Combine Why + What Changes sections for hash calculation
        content = f"{rationale}\n{description}".strip()
        hash_obj = hashlib.sha256(content.encode("utf-8"))
        # Return first 16 chars for storage efficiency
        return hash_obj.hexdigest()[:16]

    def _save_openspec_change_proposal(self, proposal: dict[str, Any]) -> None:
        """
        Save updated change proposal back to OpenSpec proposal.md file.

        Adds or updates a metadata section at the end of proposal.md with
        source_tracking information (GitHub issue IDs, etc.).

        Args:
            proposal: Change proposal dict with updated source_tracking
        """
        change_id = proposal.get("change_id")
        if not change_id:
            return  # Cannot save without change ID

        # Find openspec/changes directory
        openspec_changes_dir = None
        openspec_dir = self.repo_path / "openspec" / "changes"
        if openspec_dir.exists() and openspec_dir.is_dir():
            openspec_changes_dir = openspec_dir
        else:
            # Check for external base path in bridge config
            if self.bridge_config and hasattr(self.bridge_config, "external_base_path"):
                external_path = getattr(self.bridge_config, "external_base_path", None)
                if external_path:
                    openspec_changes_dir = Path(external_path) / "openspec" / "changes"
                    if not openspec_changes_dir.exists():
                        openspec_changes_dir = None

        if not openspec_changes_dir or not openspec_changes_dir.exists():
            return  # Cannot save without OpenSpec directory

        # Try active changes directory first
        proposal_file = openspec_changes_dir / change_id / "proposal.md"
        if not proposal_file.exists():
            # Try archive directory (format: YYYY-MM-DD-<change-id>)
            archive_dir = openspec_changes_dir / "archive"
            if archive_dir.exists() and archive_dir.is_dir():
                for archive_subdir in archive_dir.iterdir():
                    if archive_subdir.is_dir():
                        archive_name = archive_subdir.name
                        # Extract change_id from "2025-12-29-add-devops-backlog-tracking"
                        if "-" in archive_name:
                            parts = archive_name.split("-", 3)
                            if len(parts) >= 4 and parts[3] == change_id:
                                proposal_file = archive_subdir / "proposal.md"
                                break

        if not proposal_file.exists():
            return  # Proposal file doesn't exist

        try:
            # Read existing content
            content = proposal_file.read_text(encoding="utf-8")

            # Extract source_tracking info (normalize to list)
            source_tracking_raw = proposal.get("source_tracking", {})
            source_tracking_list = self._normalize_source_tracking(source_tracking_raw)
            if not source_tracking_list:
                return  # No source tracking to save

            # Map source types to proper capitalization (MD034 compliance for URLs)
            source_type_capitalization = {
                "github": "GitHub",
                "ado": "ADO",
                "linear": "Linear",
                "jira": "Jira",
                "unknown": "Unknown",
            }

            metadata_lines = [
                "",
                "---",
                "",
                "## Source Tracking",
                "",
            ]

            # Write each entry (one per repository)
            for i, entry in enumerate(source_tracking_list):
                if not isinstance(entry, dict):
                    continue

                # Add repository header if multiple entries or if source_repo is present
                # Always include source_repo for ADO to ensure proper matching (ADO URLs contain GUIDs, not project names)
                source_repo = entry.get("source_repo")
                if source_repo:
                    if len(source_tracking_list) > 1 or i > 0:
                        metadata_lines.append(f"### Repository: {source_repo}")
                        metadata_lines.append("")
                    # For single entries, save source_repo as a hidden comment for matching
                    elif len(source_tracking_list) == 1:
                        metadata_lines.append(f"<!-- source_repo: {source_repo} -->")

                source_type_raw = entry.get("source_type", "unknown")
                source_type_display = source_type_capitalization.get(source_type_raw.lower(), "Unknown")

                source_id = entry.get("source_id")
                source_url = entry.get("source_url")

                if source_id:
                    metadata_lines.append(f"- **{source_type_display} Issue**: #{source_id}")
                if source_url:
                    # Enclose URL in angle brackets for MD034 compliance
                    metadata_lines.append(f"- **Issue URL**: <{source_url}>")

                source_metadata = entry.get("source_metadata", {})
                if isinstance(source_metadata, dict) and source_metadata:
                    last_synced_status = source_metadata.get("last_synced_status")
                    if last_synced_status:
                        metadata_lines.append(f"- **Last Synced Status**: {last_synced_status}")
                    sanitized = source_metadata.get("sanitized")
                    if sanitized is not None:
                        metadata_lines.append(f"- **Sanitized**: {str(sanitized).lower()}")
                    # Save content_hash as a hidden HTML comment for persistence
                    # Format: <!-- content_hash: <hash> -->
                    content_hash = source_metadata.get("content_hash")
                    if content_hash:
                        metadata_lines.append(f"<!-- content_hash: {content_hash} -->")

                    # Save progress_comments and last_code_change_detected as hidden HTML comments
                    # Format: <!-- progress_comments: <json> --> and <!-- last_code_change_detected: <timestamp> -->
                    progress_comments = source_metadata.get("progress_comments")
                    if progress_comments and isinstance(progress_comments, list) and len(progress_comments) > 0:
                        import json

                        # Save as JSON in HTML comment for persistence
                        progress_comments_json = json.dumps(progress_comments, separators=(",", ":"))
                        metadata_lines.append(f"<!-- progress_comments: {progress_comments_json} -->")

                    last_code_change_detected = source_metadata.get("last_code_change_detected")
                    if last_code_change_detected:
                        metadata_lines.append(f"<!-- last_code_change_detected: {last_code_change_detected} -->")

                # Add separator between entries (except for last one)
                if i < len(source_tracking_list) - 1:
                    metadata_lines.append("")
                    metadata_lines.append("---")
                    metadata_lines.append("")

            metadata_lines.append("")
            metadata_section = "\n".join(metadata_lines)

            # Update title, description, and rationale if they're provided in the proposal
            # This ensures the proposal.md file stays in sync with the proposal data
            title = proposal.get("title")
            description = proposal.get("description", "")
            rationale = proposal.get("rationale", "")

            if title:
                # Update title line (# Change: ...)
                title_pattern = r"^#\s+Change:\s*.*$"
                if re.search(title_pattern, content, re.MULTILINE):
                    content = re.sub(title_pattern, f"# Change: {title}", content, flags=re.MULTILINE)
                else:
                    # Title line doesn't exist, add it at the beginning
                    content = f"# Change: {title}\n\n{content}"

            # Update Why section - use more precise pattern to stop at correct boundaries
            if rationale:
                rationale_clean = rationale.strip()
                if "## Why" in content:
                    # Replace existing Why section - stop at next ## section (not Why) or ---\n\n## Source Tracking
                    # Pattern: ## Why\n...content... until next ## (excluding Why) or ---\n\n## Source Tracking
                    why_pattern = r"(##\s+Why\s*\n)(.*?)(?=\n##\s+(?!Why\s)|(?:\n---\s*\n\s*##\s+Source\s+Tracking)|\Z)"
                    if re.search(why_pattern, content, re.DOTALL | re.IGNORECASE):
                        # Replace content but preserve header
                        content = re.sub(
                            why_pattern, r"\1\n" + rationale_clean + r"\n", content, flags=re.DOTALL | re.IGNORECASE
                        )
                    else:
                        # Fallback: simpler pattern
                        why_pattern_simple = r"(##\s+Why\s*\n)(.*?)(?=\n##\s+|\Z)"
                        content = re.sub(
                            why_pattern_simple,
                            r"\1\n" + rationale_clean + r"\n",
                            content,
                            flags=re.DOTALL | re.IGNORECASE,
                        )
                else:
                    # Why section doesn't exist, add it before What Changes or Source Tracking
                    insert_before = re.search(r"(##\s+(What Changes|Source Tracking))", content, re.IGNORECASE)
                    if insert_before:
                        insert_pos = insert_before.start()
                        content = content[:insert_pos] + f"## Why\n\n{rationale_clean}\n\n" + content[insert_pos:]
                    else:
                        # No sections found, add at end (before Source Tracking if it exists)
                        if "## Source Tracking" in content:
                            content = content.replace(
                                "## Source Tracking", f"## Why\n\n{rationale_clean}\n\n## Source Tracking"
                            )
                        else:
                            content = f"{content}\n\n## Why\n\n{rationale_clean}\n"

            # Update What Changes section - use more precise pattern to stop at correct boundaries
            if description:
                description_clean = self._dedupe_duplicate_sections(description.strip())
                if "## What Changes" in content:
                    # Replace existing What Changes section - stop at Source Tracking or end
                    what_pattern = r"(##\s+What\s+Changes\s*\n)(.*?)(?=(?:\n---\s*\n\s*##\s+Source\s+Tracking)|\Z)"
                    if re.search(what_pattern, content, re.DOTALL | re.IGNORECASE):
                        content = re.sub(
                            what_pattern,
                            r"\1\n" + description_clean + r"\n",
                            content,
                            flags=re.DOTALL | re.IGNORECASE,
                        )
                    else:
                        what_pattern_simple = (
                            r"(##\s+What\s+Changes\s*\n)(.*?)(?=(?:\n---\s*\n\s*##\s+Source\s+Tracking)|\Z)"
                        )
                        content = re.sub(
                            what_pattern_simple,
                            r"\1\n" + description_clean + r"\n",
                            content,
                            flags=re.DOTALL | re.IGNORECASE,
                        )
                else:
                    # What Changes section doesn't exist, add it after Why or before Source Tracking
                    insert_after_why = re.search(r"(##\s+Why\s*\n.*?\n)(?=##\s+|$)", content, re.DOTALL | re.IGNORECASE)
                    if insert_after_why:
                        insert_pos = insert_after_why.end()
                        content = (
                            content[:insert_pos] + f"## What Changes\n\n{description_clean}\n\n" + content[insert_pos:]
                        )
                    elif "## Source Tracking" in content:
                        content = content.replace(
                            "## Source Tracking",
                            f"## What Changes\n\n{description_clean}\n\n## Source Tracking",
                        )
                    else:
                        content = f"{content}\n\n## What Changes\n\n{description_clean}\n"

            # Check if metadata section already exists
            if "## Source Tracking" in content:
                # Replace existing metadata section
                # Pattern matches: optional --- separator, then ## Source Tracking and everything until next ## section or end
                # The metadata_section already includes the --- separator, so we match and replace the entire block
                # Try with --- separator first (most common case)
                pattern_with_sep = r"\n---\n\n## Source Tracking.*?(?=\n## |\Z)"
                if re.search(pattern_with_sep, content, flags=re.DOTALL):
                    content = re.sub(pattern_with_sep, "\n" + metadata_section.rstrip(), content, flags=re.DOTALL)
                else:
                    # Fallback: no --- separator before section
                    pattern_no_sep = r"\n## Source Tracking.*?(?=\n## |\Z)"
                    content = re.sub(pattern_no_sep, "\n" + metadata_section.rstrip(), content, flags=re.DOTALL)
            else:
                # Append new metadata section
                content = content.rstrip() + "\n" + metadata_section

            # Write back to file
            proposal_file.write_text(content, encoding="utf-8")

        except Exception as e:
            # Log error but don't fail the sync
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to save source tracking to {proposal_file}: {e}")

    def _format_proposal_for_export(self, proposal: dict[str, Any]) -> str:
        """
        Format proposal as markdown for export to temporary file.

        Args:
            proposal: Change proposal dict

        Returns:
            Markdown-formatted proposal content
        """
        lines = []
        lines.append(f"# Change: {proposal.get('title', 'Untitled')}")
        lines.append("")

        rationale = proposal.get("rationale", "")
        if rationale:
            lines.append("## Why")
            lines.append("")
            lines.append(rationale.strip())
            lines.append("")

        description = proposal.get("description", "")
        if description:
            lines.append("## What Changes")
            lines.append("")
            lines.append(description.strip())
            lines.append("")

        return "\n".join(lines)

    def _parse_sanitized_proposal(self, sanitized_content: str, original_proposal: dict[str, Any]) -> dict[str, Any]:
        """
        Parse sanitized markdown content back into proposal structure.

        Args:
            sanitized_content: Sanitized markdown content from temporary file
            original_proposal: Original proposal dict (for metadata)

        Returns:
            Updated proposal dict with sanitized content
        """

        proposal = original_proposal.copy()

        # Extract Why section
        why_match = re.search(r"##\s*Why\s*\n\n(.*?)(?=\n##|\Z)", sanitized_content, re.DOTALL)
        if why_match:
            proposal["rationale"] = why_match.group(1).strip()

        # Extract What Changes section
        what_match = re.search(r"##\s*What\s+Changes\s*\n\n(.*?)(?=\n##|\Z)", sanitized_content, re.DOTALL)
        if what_match:
            proposal["description"] = what_match.group(1).strip()

        return proposal

    def _get_openspec_changes_dir(self) -> Path | None:
        """
        Get OpenSpec changes directory path.

        Checks repo_path first, then external_base_path if available.

        Returns:
            Path to openspec/changes directory, or None if not found
        """
        # Check if openspec/changes exists in repo
        openspec_dir = self.repo_path / "openspec" / "changes"
        if openspec_dir.exists() and openspec_dir.is_dir():
            return openspec_dir

        # Check for external base path in bridge config
        if self.bridge_config and hasattr(self.bridge_config, "external_base_path"):
            external_path = getattr(self.bridge_config, "external_base_path", None)
            if external_path:
                openspec_changes_dir = Path(external_path) / "openspec" / "changes"
                if openspec_changes_dir.exists():
                    return openspec_changes_dir

        return None

    def _determine_affected_specs(self, proposal: Any) -> list[str]:
        """
        Determine affected specs from proposal content.

        Args:
            proposal: ChangeProposal instance

        Returns:
            List of affected spec IDs (e.g., ["devops-sync", "bridge-adapter"])
        """
        # Search proposal description and rationale for spec references
        content = f"{proposal.description} {proposal.rationale}".lower()

        affected_specs: list[str] = []
        known_specs = ["devops-sync", "bridge-adapter", "auth-management", "backlog-analysis"]

        for spec_id in known_specs:
            if spec_id.replace("-", " ") in content or spec_id in content:
                affected_specs.append(spec_id)

        # Default to devops-sync if no specs found (since most backlog imports affect devops-sync)
        if not affected_specs:
            affected_specs = ["devops-sync"]

        return affected_specs

    def _extract_requirement_from_proposal(self, proposal: Any, spec_id: str) -> str:
        """
        Extract requirement text from proposal content.

        Args:
            proposal: ChangeProposal instance
            spec_id: Spec ID to extract requirement for

        Returns:
            Requirement text in OpenSpec format, or empty string if extraction fails
        """
        description = proposal.description or ""
        rationale = proposal.rationale or ""

        # Try to extract meaningful requirement from "What Changes" section
        # Look for bullet points that describe what the system should do
        requirement_lines = []

        def _extract_section_details(section_content: str | None) -> list[str]:
            if not section_content:
                return []

            details: list[str] = []
            in_code_block = False

            for raw_line in section_content.splitlines():
                stripped = raw_line.strip()
                if stripped.startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if not stripped:
                    continue

                if in_code_block:
                    cleaned = re.sub(r"^[-*]\s*", "", stripped).strip()
                    if cleaned.startswith("#") or not cleaned:
                        continue
                    cleaned = re.sub(r"^\[\s*[xX]?\s*\]\s*", "", cleaned).strip()
                    details.append(cleaned)
                    continue

                if stripped.startswith(("#", "---")):
                    continue

                cleaned = re.sub(r"^[-*]\s*", "", stripped)
                cleaned = re.sub(r"^\d+\.\s*", "", cleaned)
                cleaned = cleaned.strip()
                cleaned = re.sub(r"^\[\s*[xX]?\s*\]\s*", "", cleaned).strip()
                if cleaned:
                    details.append(cleaned)

            return details

        def _normalize_detail_for_and(detail: str) -> str:
            cleaned = detail.strip()
            if not cleaned:
                return ""

            cleaned = cleaned.replace("**", "").strip()
            cleaned = cleaned.lstrip("*").strip()
            if cleaned.lower() in {"commands:", "commands"}:
                return ""

            cleaned = re.sub(r"^\d+\.\s*", "", cleaned).strip()
            cleaned = re.sub(r"^\[\s*[xX]?\s*\]\s*", "", cleaned).strip()
            lower = cleaned.lower()

            if lower.startswith("new command group"):
                rest = re.sub(r"^new\s+command\s+group\s*:\s*", "", cleaned, flags=re.IGNORECASE)
                cleaned = f"provides command group {rest}".strip()
                lower = cleaned.lower()
            elif lower.startswith("location:"):
                rest = re.sub(r"^location\s*:\s*", "", cleaned, flags=re.IGNORECASE)
                cleaned = f"stores tokens at {rest}".strip()
                lower = cleaned.lower()
            elif lower.startswith("format:"):
                rest = re.sub(r"^format\s*:\s*", "", cleaned, flags=re.IGNORECASE)
                cleaned = f"uses format {rest}".strip()
                lower = cleaned.lower()
            elif lower.startswith("permissions:"):
                rest = re.sub(r"^permissions\s*:\s*", "", cleaned, flags=re.IGNORECASE)
                cleaned = f"enforces permissions {rest}".strip()
                lower = cleaned.lower()
            elif ":" in cleaned:
                _prefix, rest = cleaned.split(":", 1)
                if rest.strip():
                    cleaned = rest.strip()
                    lower = cleaned.lower()

            if lower.startswith("users can"):
                cleaned = f"allows users to {cleaned[10:].lstrip()}".strip()
                lower = cleaned.lower()
            elif re.match(r"^specfact\s+", cleaned):
                cleaned = f"supports `{cleaned}` command"
                lower = cleaned.lower()

            if cleaned:
                first_word = cleaned.split()[0].rstrip(".,;:!?")
                verbs_to_lower = {
                    "uses",
                    "use",
                    "provides",
                    "provide",
                    "stores",
                    "store",
                    "supports",
                    "support",
                    "enforces",
                    "enforce",
                    "allows",
                    "allow",
                    "leverages",
                    "leverage",
                    "adds",
                    "add",
                    "can",
                    "custom",
                    "supported",
                    "zero-configuration",
                }
                if first_word.lower() in verbs_to_lower and cleaned[0].isupper():
                    cleaned = cleaned[0].lower() + cleaned[1:]

            if cleaned and not cleaned.endswith("."):
                cleaned += "."

            return cleaned

        def _parse_formatted_sections(text: str) -> list[dict[str, str]]:
            sections: list[dict[str, str]] = []
            current: dict[str, Any] | None = None
            marker_pattern = re.compile(
                r"^-\s*\*\*(NEW|EXTEND|FIX|ADD|MODIFY|UPDATE|REMOVE|REFACTOR)\*\*:\s*(.+)$",
                re.IGNORECASE,
            )

            for raw_line in text.splitlines():
                stripped = raw_line.strip()
                marker_match = marker_pattern.match(stripped)
                if marker_match:
                    if current:
                        sections.append(
                            {
                                "title": current["title"],
                                "content": "\n".join(current["content"]).strip(),
                            }
                        )
                    current = {"title": marker_match.group(2).strip(), "content": []}
                    continue
                if current is not None:
                    current["content"].append(raw_line)

            if current:
                sections.append(
                    {
                        "title": current["title"],
                        "content": "\n".join(current["content"]).strip(),
                    }
                )

            return sections

        formatted_sections = _parse_formatted_sections(description)

        requirement_index = 0
        seen_sections: set[str] = set()

        if formatted_sections:
            for section in formatted_sections:
                section_title = section["title"]
                section_content = section["content"] or None
                section_title_lower = section_title.lower()
                normalized_title = re.sub(r"\([^)]*\)", "", section_title_lower).strip()
                normalized_title = re.sub(r"^\d+\.\s*", "", normalized_title).strip()
                if normalized_title in seen_sections:
                    continue
                seen_sections.add(normalized_title)
                section_details = _extract_section_details(section_content)

                # Skip generic section titles that don't represent requirements
                skip_titles = [
                    "architecture overview",
                    "purpose",
                    "introduction",
                    "overview",
                    "documentation",
                    "testing",
                    "security & quality",
                    "security and quality",
                    "non-functional requirements",
                    "three-phase delivery",
                    "additional context",
                    "platform roadmap",
                    "similar implementations",
                    "required python packages",
                    "optional packages",
                    "known limitations & mitigations",
                    "known limitations and mitigations",
                    "security model",
                    "update required",
                ]
                if normalized_title in skip_titles:
                    continue

                # Generate requirement name from section title
                req_name = section_title.strip()
                req_name = re.sub(r"^(new|add|implement|support|provide|enable)\s+", "", req_name, flags=re.IGNORECASE)
                req_name = re.sub(r"\([^)]*\)", "", req_name, flags=re.IGNORECASE).strip()
                req_name = re.sub(r"^\d+\.\s*", "", req_name).strip()
                req_name = re.sub(r"\s+", " ", req_name)[:60].strip()

                # Ensure req_name is meaningful (at least 8 chars)
                if not req_name or len(req_name) < 8:
                    req_name = self._format_proposal_title(proposal.title)
                    req_name = re.sub(r"^(feat|fix|add|update|remove|refactor):\s*", "", req_name, flags=re.IGNORECASE)
                    req_name = req_name.replace("[Change]", "").strip()
                    if requirement_index > 0:
                        req_name = f"{req_name} ({requirement_index + 1})"

                title_lower = section_title_lower

                if spec_id == "devops-sync":
                    if "device code" in title_lower:
                        if "azure" in title_lower or "devops" in title_lower:
                            change_desc = (
                                "use Azure DevOps device code authentication for sync operations with Azure DevOps"
                            )
                        elif "github" in title_lower:
                            change_desc = "use GitHub device code authentication for sync operations with GitHub"
                        else:
                            change_desc = f"use device code authentication for {section_title.lower()} sync operations"
                    elif "token" in title_lower or "storage" in title_lower or "management" in title_lower:
                        change_desc = "use stored authentication tokens for DevOps sync operations when available"
                    elif "cli" in title_lower or "command" in title_lower or "integration" in title_lower:
                        change_desc = "provide CLI authentication commands for DevOps sync operations"
                    elif "architectural" in title_lower or "decision" in title_lower:
                        change_desc = (
                            "follow documented authentication architecture decisions for DevOps sync operations"
                        )
                    else:
                        change_desc = f"support {section_title.lower()} for DevOps sync operations"
                elif spec_id == "auth-management":
                    if "device code" in title_lower:
                        if "azure" in title_lower or "devops" in title_lower:
                            change_desc = "support Azure DevOps device code authentication using Entra ID"
                        elif "github" in title_lower:
                            change_desc = "support GitHub device code authentication using RFC 8628 OAuth device authorization flow"
                        else:
                            change_desc = f"support device code authentication for {section_title.lower()}"
                    elif "token" in title_lower or "storage" in title_lower or "management" in title_lower:
                        change_desc = (
                            "store and manage authentication tokens securely with appropriate file permissions"
                        )
                    elif "cli" in title_lower or "command" in title_lower:
                        change_desc = "provide CLI commands for authentication operations"
                    else:
                        change_desc = f"support {section_title.lower()}"
                else:
                    if "device code" in title_lower:
                        change_desc = f"support {section_title.lower()} authentication"
                    elif "token" in title_lower or "storage" in title_lower:
                        change_desc = "store and manage authentication tokens securely"
                    elif "architectural" in title_lower or "decision" in title_lower:
                        change_desc = "follow documented architecture decisions"
                    else:
                        change_desc = f"support {section_title.lower()}"

                if not change_desc.endswith("."):
                    change_desc = change_desc + "."
                if change_desc and change_desc[0].isupper():
                    change_desc = change_desc[0].lower() + change_desc[1:]

                requirement_lines.append(f"### Requirement: {req_name}")
                requirement_lines.append("")
                requirement_lines.append(f"The system SHALL {change_desc}")
                requirement_lines.append("")

                scenario_name = (
                    req_name.split(":")[0]
                    if ":" in req_name
                    else req_name.split()[0]
                    if req_name.split()
                    else "Implementation"
                )
                requirement_lines.append(f"#### Scenario: {scenario_name}")
                requirement_lines.append("")
                when_action = req_name.lower().replace("device code", "device code authentication")
                when_clause = f"a user requests {when_action}"
                if "architectural" in title_lower or "decision" in title_lower:
                    when_clause = "the system performs authentication operations"
                requirement_lines.append(f"- **WHEN** {when_clause}")

                then_response = change_desc
                verbs_to_fix = {
                    "support": "supports",
                    "store": "stores",
                    "manage": "manages",
                    "provide": "provides",
                    "implement": "implements",
                    "enable": "enables",
                    "allow": "allows",
                    "use": "uses",
                    "create": "creates",
                    "handle": "handles",
                    "follow": "follows",
                }
                words = then_response.split()
                if words:
                    first_word = words[0].rstrip(".,;:!?")
                    if first_word.lower() in verbs_to_fix:
                        words[0] = verbs_to_fix[first_word.lower()] + words[0][len(first_word) :]
                    for i in range(1, len(words) - 1):
                        if words[i].lower() == "and" and i + 1 < len(words):
                            next_word = words[i + 1].rstrip(".,;:!?")
                            if next_word.lower() in verbs_to_fix:
                                words[i + 1] = verbs_to_fix[next_word.lower()] + words[i + 1][len(next_word) :]
                    then_response = " ".join(words)
                requirement_lines.append(f"- **THEN** the system {then_response}")
                if section_details:
                    for detail in section_details:
                        normalized_detail = _normalize_detail_for_and(detail)
                        if normalized_detail:
                            requirement_lines.append(f"- **AND** {normalized_detail}")
                requirement_lines.append("")

                requirement_index += 1
        else:
            # If no formatted markers found, try extracting from raw description structure
            change_patterns = re.finditer(
                r"(?i)(?:^|\n)(?:-\s*)?###\s*([^\n]+)\s*\n(.*?)(?=\n(?:-\s*)?###\s+|\n(?:-\s*)?##\s+|\Z)",
                description,
                re.MULTILINE | re.DOTALL,
            )
            for match in change_patterns:
                section_title = match.group(1).strip()
                section_content = match.group(2).strip()

                section_title_lower = section_title.lower()
                normalized_title = re.sub(r"\([^)]*\)", "", section_title_lower).strip()
                normalized_title = re.sub(r"^\d+\.\s*", "", normalized_title).strip()
                if normalized_title in seen_sections:
                    continue
                seen_sections.add(normalized_title)
                section_details = _extract_section_details(section_content)

                skip_titles = [
                    "architecture overview",
                    "purpose",
                    "introduction",
                    "overview",
                    "documentation",
                    "testing",
                    "security & quality",
                    "security and quality",
                    "non-functional requirements",
                    "three-phase delivery",
                    "additional context",
                    "platform roadmap",
                    "similar implementations",
                    "required python packages",
                    "optional packages",
                    "known limitations & mitigations",
                    "known limitations and mitigations",
                    "security model",
                    "update required",
                ]
                if normalized_title in skip_titles:
                    continue

                req_name = section_title.strip()
                req_name = re.sub(r"^(new|add|implement|support|provide|enable)\s+", "", req_name, flags=re.IGNORECASE)
                req_name = re.sub(r"\([^)]*\)", "", req_name, flags=re.IGNORECASE).strip()
                req_name = re.sub(r"^\d+\.\s*", "", req_name).strip()
                req_name = re.sub(r"\s+", " ", req_name)[:60].strip()

                if not req_name or len(req_name) < 8:
                    req_name = self._format_proposal_title(proposal.title)
                    req_name = re.sub(r"^(feat|fix|add|update|remove|refactor):\s*", "", req_name, flags=re.IGNORECASE)
                    req_name = req_name.replace("[Change]", "").strip()
                    if requirement_index > 0:
                        req_name = f"{req_name} ({requirement_index + 1})"

                title_lower = section_title_lower

                if spec_id == "devops-sync":
                    if "device code" in title_lower:
                        if "azure" in title_lower or "devops" in title_lower:
                            change_desc = (
                                "use Azure DevOps device code authentication for sync operations with Azure DevOps"
                            )
                        elif "github" in title_lower:
                            change_desc = "use GitHub device code authentication for sync operations with GitHub"
                        else:
                            change_desc = f"use device code authentication for {section_title.lower()} sync operations"
                    elif "token" in title_lower or "storage" in title_lower or "management" in title_lower:
                        change_desc = "use stored authentication tokens for DevOps sync operations when available"
                    elif "cli" in title_lower or "command" in title_lower or "integration" in title_lower:
                        change_desc = "provide CLI authentication commands for DevOps sync operations"
                    elif "architectural" in title_lower or "decision" in title_lower:
                        change_desc = (
                            "follow documented authentication architecture decisions for DevOps sync operations"
                        )
                    else:
                        change_desc = f"support {section_title.lower()} for DevOps sync operations"
                elif spec_id == "auth-management":
                    if "device code" in title_lower:
                        if "azure" in title_lower or "devops" in title_lower:
                            change_desc = "support Azure DevOps device code authentication using Entra ID"
                        elif "github" in title_lower:
                            change_desc = "support GitHub device code authentication using RFC 8628 OAuth device authorization flow"
                        else:
                            change_desc = f"support device code authentication for {section_title.lower()}"
                    elif "token" in title_lower or "storage" in title_lower or "management" in title_lower:
                        change_desc = (
                            "store and manage authentication tokens securely with appropriate file permissions"
                        )
                    elif "cli" in title_lower or "command" in title_lower:
                        change_desc = "provide CLI commands for authentication operations"
                    else:
                        change_desc = f"support {section_title.lower()}"
                else:
                    if "device code" in title_lower:
                        change_desc = f"support {section_title.lower()} authentication"
                    elif "token" in title_lower or "storage" in title_lower:
                        change_desc = "store and manage authentication tokens securely"
                    elif "architectural" in title_lower or "decision" in title_lower:
                        change_desc = "follow documented architecture decisions"
                    else:
                        change_desc = f"support {section_title.lower()}"

                if not change_desc.endswith("."):
                    change_desc = change_desc + "."
                if change_desc and change_desc[0].isupper():
                    change_desc = change_desc[0].lower() + change_desc[1:]

                requirement_lines.append(f"### Requirement: {req_name}")
                requirement_lines.append("")
                requirement_lines.append(f"The system SHALL {change_desc}")
                requirement_lines.append("")

                scenario_name = (
                    req_name.split(":")[0]
                    if ":" in req_name
                    else req_name.split()[0]
                    if req_name.split()
                    else "Implementation"
                )
                requirement_lines.append(f"#### Scenario: {scenario_name}")
                requirement_lines.append("")
                when_action = req_name.lower().replace("device code", "device code authentication")
                when_clause = f"a user requests {when_action}"
                if "architectural" in title_lower or "decision" in title_lower:
                    when_clause = "the system performs authentication operations"
                requirement_lines.append(f"- **WHEN** {when_clause}")

                then_response = change_desc
                verbs_to_fix = {
                    "support": "supports",
                    "store": "stores",
                    "manage": "manages",
                    "provide": "provides",
                    "implement": "implements",
                    "enable": "enables",
                    "allow": "allows",
                    "use": "uses",
                    "create": "creates",
                    "handle": "handles",
                    "follow": "follows",
                }
                words = then_response.split()
                if words:
                    first_word = words[0].rstrip(".,;:!?")
                    if first_word.lower() in verbs_to_fix:
                        words[0] = verbs_to_fix[first_word.lower()] + words[0][len(first_word) :]
                    for i in range(1, len(words) - 1):
                        if words[i].lower() == "and" and i + 1 < len(words):
                            next_word = words[i + 1].rstrip(".,;:!?")
                            if next_word.lower() in verbs_to_fix:
                                words[i + 1] = verbs_to_fix[next_word.lower()] + words[i + 1][len(next_word) :]
                    then_response = " ".join(words)
                requirement_lines.append(f"- **THEN** the system {then_response}")
                if section_details:
                    for detail in section_details:
                        normalized_detail = _normalize_detail_for_and(detail)
                        if normalized_detail:
                            requirement_lines.append(f"- **AND** {normalized_detail}")
                requirement_lines.append("")

                requirement_index += 1

        # If no structured changes found, try to extract from "What Changes" section
        # Look for subsections like "- ### Architecture Overview", "- ### Azure DevOps Device Code"
        if not requirement_lines and description:
            # Extract first meaningful subsection or bullet point
            # Pattern: "- ### Title" followed by "- Content" on next line
            # The description may have been converted to bullet list, so everything has "- " prefix
            # Match: "- ### Architecture Overview\n- This change adds device code authentication flows..."
            subsection_match = re.search(r"-\s*###\s*([^\n]+)\s*\n\s*-\s*([^\n]+)", description, re.MULTILINE)
            if subsection_match:
                subsection_title = subsection_match.group(1).strip()
                first_line = subsection_match.group(2).strip()
                # Remove leading "- " if still present
                if first_line.startswith("- "):
                    first_line = first_line[2:].strip()

                # Skip if first_line is just the subsection title or too short
                if first_line.lower() != subsection_title.lower() and len(first_line) > 10:
                    # Take first sentence (up to 200 chars)
                    if "." in first_line:
                        first_line = first_line.split(".")[0].strip() + "."
                    if len(first_line) > 200:
                        first_line = first_line[:200] + "..."

                    req_name = self._format_proposal_title(proposal.title)
                    req_name = re.sub(r"^(feat|fix|add|update|remove|refactor):\s*", "", req_name, flags=re.IGNORECASE)
                    req_name = req_name.replace("[Change]", "").strip()

                    requirement_lines.append(f"### Requirement: {req_name}")
                    requirement_lines.append("")
                    requirement_lines.append(f"The system SHALL {first_line}")
                    requirement_lines.append("")
                    requirement_lines.append(f"#### Scenario: {subsection_title}")
                    requirement_lines.append("")
                    requirement_lines.append("- **WHEN** the system processes the change")
                    requirement_lines.append(f"- **THEN** {first_line.lower()}")
                    requirement_lines.append("")

        # If still no requirement extracted, create from title and description
        if not requirement_lines and (description or rationale):
            req_name = self._format_proposal_title(proposal.title)
            req_name = re.sub(r"^(feat|fix|add|update|remove|refactor):\s*", "", req_name, flags=re.IGNORECASE)
            req_name = req_name.replace("[Change]", "").strip()

            # Extract first sentence or meaningful phrase from description
            first_sentence = (
                description.split(".")[0].strip()
                if description
                else rationale.split(".")[0].strip()
                if rationale
                else "implement the change"
            )
            # Remove leading "- " or "### " if present
            first_sentence = re.sub(r"^[-#\s]+", "", first_sentence).strip()
            if len(first_sentence) > 200:
                first_sentence = first_sentence[:200] + "..."

            requirement_lines.append(f"### Requirement: {req_name}")
            requirement_lines.append("")
            requirement_lines.append(f"The system SHALL {first_sentence}")
            requirement_lines.append("")
            requirement_lines.append(f"#### Scenario: {req_name}")
            requirement_lines.append("")
            requirement_lines.append("- **WHEN** the change is applied")
            requirement_lines.append(f"- **THEN** {first_sentence.lower()}")
            requirement_lines.append("")

        return "\n".join(requirement_lines) if requirement_lines else ""

    def _generate_tasks_from_proposal(self, proposal: Any) -> str:
        """
        Generate tasks.md content from proposal.

        Extracts tasks from "Acceptance Criteria" section if present,
        otherwise creates placeholder structure.

        Args:
            proposal: ChangeProposal instance

        Returns:
            Markdown content for tasks.md file
        """
        lines = ["# Tasks: " + self._format_proposal_title(proposal.title), ""]

        # Try to extract tasks from description, focusing on "Acceptance Criteria" section
        description = proposal.description or ""
        tasks_found = False
        marker_pattern = re.compile(
            r"^-\s*\*\*(NEW|EXTEND|FIX|ADD|MODIFY|UPDATE|REMOVE|REFACTOR)\*\*:\s*(.+)$",
            re.IGNORECASE | re.MULTILINE,
        )

        def _extract_section_tasks(text: str) -> list[dict[str, Any]]:
            sections: list[dict[str, Any]] = []
            current: dict[str, Any] | None = None
            in_code_block = False

            for raw_line in text.splitlines():
                stripped = raw_line.strip()
                marker_match = marker_pattern.match(stripped)
                if marker_match:
                    if current:
                        sections.append(current)
                    current = {"title": marker_match.group(2).strip(), "tasks": []}
                    in_code_block = False
                    continue

                if current is None:
                    continue

                if stripped.startswith("```"):
                    in_code_block = not in_code_block
                    continue

                if in_code_block:
                    if stripped and not stripped.startswith("#"):
                        if stripped.startswith("specfact "):
                            current["tasks"].append(f"Support `{stripped}` command")
                        else:
                            current["tasks"].append(stripped)
                    continue

                if not stripped:
                    continue

                content = stripped[2:].strip() if stripped.startswith("- ") else stripped
                content = re.sub(r"^\d+\.\s*", "", content).strip()
                if content.lower() in {"**commands:**", "commands:", "commands"}:
                    continue
                if content:
                    current["tasks"].append(content)

            if current:
                sections.append(current)

            return sections

        # Look for "Acceptance Criteria" section first
        # Pattern may have leading "- " (when converted to bullet list format)
        # Match: "- ## Acceptance Criteria\n...content..." or "## Acceptance Criteria\n...content..."
        acceptance_criteria_match = re.search(
            r"(?i)(?:-\s*)?##\s*Acceptance\s+Criteria\s*\n(.*?)(?=\n\s*(?:-\s*)?##|\Z)",
            description,
            re.DOTALL,
        )

        if acceptance_criteria_match:
            # Found Acceptance Criteria section, extract tasks
            criteria_content = acceptance_criteria_match.group(1)

            # Map acceptance criteria subsections to main task sections
            # Some subsections like "Testing", "Documentation", "Security & Quality" should be separate main sections
            section_mapping = {
                "testing": 2,
                "documentation": 3,
                "security": 4,
                "security & quality": 4,
                "code quality": 5,
            }

            section_num = 1  # Start with Implementation
            subsection_num = 1
            task_num = 1
            current_subsection = None
            first_subsection = True
            current_section_name = "Implementation"

            # Add main section header
            lines.append("## 1. Implementation")
            lines.append("")

            for line in criteria_content.split("\n"):
                stripped = line.strip()

                # Check for subsection header (###) - may have leading "- "
                # Pattern: "- ### Title" or "### Title"
                if stripped.startswith("- ###") or (stripped.startswith("###") and not stripped.startswith("####")):
                    # Extract subsection title
                    subsection_title = stripped[5:].strip() if stripped.startswith("- ###") else stripped[3:].strip()

                    # Remove any item count like "(11 items)"
                    subsection_title_clean = re.sub(r"\(.*?\)", "", subsection_title).strip()
                    # Remove leading "#" if present
                    subsection_title_clean = re.sub(r"^#+\s*", "", subsection_title_clean).strip()
                    # Remove leading numbers if present
                    subsection_title_clean = re.sub(r"^\d+\.\s*", "", subsection_title_clean).strip()

                    # Check if this subsection should be in a different main section
                    subsection_lower = subsection_title_clean.lower()
                    new_section_num = section_mapping.get(subsection_lower)

                    if new_section_num and new_section_num != section_num:
                        # Switch to new main section
                        section_num = new_section_num
                        subsection_num = 1
                        task_num = 1

                        # Map section number to name
                        section_names = {
                            1: "Implementation",
                            2: "Testing",
                            3: "Documentation",
                            4: "Security & Quality",
                            5: "Code Quality",
                        }
                        current_section_name = section_names.get(section_num, "Implementation")

                        # Close previous section and start new one
                        if not first_subsection:
                            lines.append("")
                        lines.append(f"## {section_num}. {current_section_name}")
                        lines.append("")
                        first_subsection = True

                    # Start new subsection
                    if current_subsection is not None and not first_subsection:
                        # Close previous subsection (add blank line)
                        lines.append("")
                        subsection_num += 1
                        task_num = 1

                    current_subsection = subsection_title_clean
                    lines.append(f"### {section_num}.{subsection_num} {current_subsection}")
                    lines.append("")
                    task_num = 1
                    first_subsection = False
                # Check for task items (may have leading "- " or be standalone)
                elif stripped.startswith(("- [ ]", "- [x]", "[ ]", "[x]")):
                    # Remove checkbox and extract task text
                    task_text = re.sub(r"^[-*]\s*\[[ x]\]\s*", "", stripped).strip()
                    if task_text:
                        if current_subsection is None:
                            # No subsection, create default
                            current_subsection = "Tasks"
                            lines.append(f"### {section_num}.{subsection_num} {current_subsection}")
                            lines.append("")
                            task_num = 1
                            first_subsection = False

                        lines.append(f"- [ ] {section_num}.{subsection_num}.{task_num} {task_text}")
                        task_num += 1
                        tasks_found = True

        # If no Acceptance Criteria found, look for any task lists in description
        if not tasks_found and ("- [ ]" in description or "- [x]" in description or "[ ]" in description):
            # Extract all task-like items
            task_items = []
            for line in description.split("\n"):
                stripped = line.strip()
                if stripped.startswith(("- [ ]", "- [x]", "[ ]", "[x]")):
                    task_text = re.sub(r"^[-*]\s*\[[ x]\]\s*", "", stripped).strip()
                    if task_text:
                        task_items.append(task_text)

            if task_items:
                lines.append("## 1. Implementation")
                lines.append("")
                for idx, task in enumerate(task_items, start=1):
                    lines.append(f"- [ ] 1.{idx} {task}")
                lines.append("")
                tasks_found = True

        formatted_description = description
        if description and not marker_pattern.search(description):
            formatted_description = self._format_what_changes_section(self._extract_what_changes_content(description))

        # If no explicit tasks, build from "What Changes" sections
        if not tasks_found and formatted_description and marker_pattern.search(formatted_description):
            sections = _extract_section_tasks(formatted_description)
            if sections:
                lines.append("## 1. Implementation")
                lines.append("")
                subsection_num = 1
                for section in sections:
                    section_title = section.get("title", "").strip()
                    if not section_title:
                        continue

                    section_title_clean = re.sub(r"\([^)]*\)", "", section_title).strip()
                    if not section_title_clean:
                        continue

                    lines.append(f"### 1.{subsection_num} {section_title_clean}")
                    lines.append("")
                    task_num = 1
                    tasks = section.get("tasks") or [f"Implement {section_title_clean.lower()}"]
                    for task in tasks:
                        task_text = str(task).strip()
                        if not task_text:
                            continue
                        lines.append(f"- [ ] 1.{subsection_num}.{task_num} {task_text}")
                        task_num += 1
                    lines.append("")
                    subsection_num += 1

                tasks_found = True

        # If no tasks found, create placeholder structure
        if not tasks_found:
            lines.append("## 1. Implementation")
            lines.append("")
            lines.append("- [ ] 1.1 Implement changes as described in proposal")
            lines.append("")
            lines.append("## 2. Testing")
            lines.append("")
            lines.append("- [ ] 2.1 Add unit tests")
            lines.append("- [ ] 2.2 Add integration tests")
            lines.append("")
            lines.append("## 3. Code Quality")
            lines.append("")
            lines.append("- [ ] 3.1 Run linting: `hatch run format`")
            lines.append("- [ ] 3.2 Run type checking: `hatch run type-check`")

        return "\n".join(lines)

    def _format_proposal_title(self, title: str) -> str:
        """
        Format proposal title for OpenSpec (remove [Change] prefix and conventional commit prefixes).

        Args:
            title: Original title

        Returns:
            Formatted title
        """
        # Remove [Change] prefix if present
        if title.startswith("[Change]"):
            title = title.replace("[Change]", "").strip()
        if title.startswith("[Change] "):
            title = title.replace("[Change] ", "").strip()

        # Remove conventional commit prefixes (feat:, fix:, etc.)
        return re.sub(
            r"^(feat|fix|add|update|remove|refactor|docs|test|chore|style|perf|ci|build|revert):\s*",
            "",
            title,
            flags=re.IGNORECASE,
        ).strip()

    def _format_what_changes_section(self, description: str) -> str:
        """
        Format "What Changes" section with NEW/EXTEND/MODIFY markers per OpenSpec conventions.

        Args:
            description: Original description text

        Returns:
            Formatted description with proper markers
        """
        if not description or not description.strip():
            return "No description provided."

        if re.search(
            r"^-\s*\*\*(NEW|EXTEND|FIX|ADD|MODIFY|UPDATE|REMOVE|REFACTOR)\*\*:",
            description,
            re.MULTILINE | re.IGNORECASE,
        ):
            return description.strip()

        lines = description.split("\n")
        formatted_lines = []

        # Keywords that indicate NEW functionality
        new_keywords = ["new", "add", "introduce", "create", "implement", "support"]
        # Keywords that indicate EXTEND functionality
        extend_keywords = ["extend", "enhance", "improve", "expand", "additional"]
        # Keywords that indicate MODIFY functionality
        modify_keywords = ["modify", "update", "change", "refactor", "fix", "correct"]

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Check for subsection headers (###)
            if stripped.startswith("- ###") or (stripped.startswith("###") and not stripped.startswith("####")):
                # Extract subsection title
                section_title = stripped[5:].strip() if stripped.startswith("- ###") else stripped[3:].strip()

                # Determine change type based on section title and content
                section_lower = section_title.lower()
                change_type = "MODIFY"  # Default

                # Check section title for keywords
                if any(keyword in section_lower for keyword in new_keywords):
                    change_type = "NEW"
                elif any(keyword in section_lower for keyword in extend_keywords):
                    change_type = "EXTEND"
                elif any(keyword in section_lower for keyword in modify_keywords):
                    change_type = "MODIFY"

                # Also check if section title contains "New" explicitly
                if "new" in section_lower or section_title.startswith("New "):
                    change_type = "NEW"

                # Check section content for better detection
                # Look ahead a few lines to see if content suggests NEW
                lookahead = "\n".join(lines[i + 1 : min(i + 5, len(lines))]).lower()
                if (
                    any(
                        keyword in lookahead
                        for keyword in ["new command", "new feature", "add ", "introduce", "create"]
                    )
                    and "extend" not in lookahead
                    and "modify" not in lookahead
                ):
                    change_type = "NEW"

                # Format as bullet with marker
                formatted_lines.append(f"- **{change_type}**: {section_title}")
                i += 1

                # Process content under this subsection
                subsection_content = []
                while i < len(lines):
                    next_line = lines[i]
                    next_stripped = next_line.strip()

                    # Stop at next subsection or section
                    if (
                        next_stripped.startswith("- ###")
                        or (next_stripped.startswith("###") and not next_stripped.startswith("####"))
                        or (next_stripped.startswith("##") and not next_stripped.startswith("###"))
                    ):
                        break

                    # Skip empty lines at start of subsection
                    if not subsection_content and not next_stripped:
                        i += 1
                        continue

                    # Process content line
                    if next_stripped:
                        # Remove leading "- " if present (from previous bullet conversion)
                        content = next_stripped[2:].strip() if next_stripped.startswith("- ") else next_stripped

                        # Format as sub-bullet under the change marker
                        if content:
                            # Check if it's a code block or special formatting
                            if content.startswith(("```", "**", "*")):
                                subsection_content.append(f"  {content}")
                            else:
                                subsection_content.append(f"  - {content}")
                    else:
                        subsection_content.append("")

                    i += 1

                # Add subsection content
                if subsection_content:
                    formatted_lines.extend(subsection_content)
                    formatted_lines.append("")  # Blank line after subsection

                continue

            # Handle regular bullet points (already formatted)
            if stripped.startswith(("- [ ]", "- [x]", "-")):
                # Check if it needs a marker
                if not any(marker in stripped for marker in ["**NEW**", "**EXTEND**", "**MODIFY**", "**FIX**"]):
                    # Try to infer marker from content
                    line_lower = stripped.lower()
                    if any(keyword in line_lower for keyword in new_keywords):
                        # Replace first "- " with "- **NEW**: "
                        if stripped.startswith("- "):
                            formatted_lines.append(f"- **NEW**: {stripped[2:].strip()}")
                        else:
                            formatted_lines.append(f"- **NEW**: {stripped}")
                    elif any(keyword in line_lower for keyword in extend_keywords):
                        if stripped.startswith("- "):
                            formatted_lines.append(f"- **EXTEND**: {stripped[2:].strip()}")
                        else:
                            formatted_lines.append(f"- **EXTEND**: {stripped}")
                    elif any(keyword in line_lower for keyword in modify_keywords):
                        if stripped.startswith("- "):
                            formatted_lines.append(f"- **MODIFY**: {stripped[2:].strip()}")
                        else:
                            formatted_lines.append(f"- **MODIFY**: {stripped}")
                    else:
                        formatted_lines.append(line)
                else:
                    formatted_lines.append(line)

            # Handle regular text lines
            elif stripped:
                # Check for explicit "New" patterns first
                line_lower = stripped.lower()
                # Look for patterns like "New command group", "New feature", etc.
                if re.search(
                    r"\bnew\s+(command|feature|capability|functionality|system|module|component)", line_lower
                ) or any(keyword in line_lower for keyword in new_keywords):
                    formatted_lines.append(f"- **NEW**: {stripped}")
                elif any(keyword in line_lower for keyword in extend_keywords):
                    formatted_lines.append(f"- **EXTEND**: {stripped}")
                elif any(keyword in line_lower for keyword in modify_keywords):
                    formatted_lines.append(f"- **MODIFY**: {stripped}")
                else:
                    # Default to bullet without marker (will be treated as continuation)
                    formatted_lines.append(f"- {stripped}")
            else:
                # Empty line
                formatted_lines.append("")

            i += 1

        result = "\n".join(formatted_lines)

        # If no markers were added, ensure at least basic formatting
        if "**NEW**" not in result and "**EXTEND**" not in result and "**MODIFY**" not in result:
            # Try to add marker to first meaningful line
            lines_list = result.split("\n")
            for idx, line in enumerate(lines_list):
                if line.strip() and not line.strip().startswith("#"):
                    # Check content for new functionality
                    line_lower = line.lower()
                    if any(keyword in line_lower for keyword in ["new", "add", "introduce", "create"]):
                        lines_list[idx] = f"- **NEW**: {line.strip().lstrip('- ')}"
                    elif any(keyword in line_lower for keyword in ["extend", "enhance", "improve"]):
                        lines_list[idx] = f"- **EXTEND**: {line.strip().lstrip('- ')}"
                    else:
                        lines_list[idx] = f"- **MODIFY**: {line.strip().lstrip('- ')}"
                    break
            result = "\n".join(lines_list)

        return result

    def _extract_what_changes_content(self, description: str) -> str:
        """
        Extract only the "What Changes" content from description, excluding sections
        that should be separate (Acceptance Criteria, Dependencies, etc.).

        Args:
            description: Full proposal description

        Returns:
            Only the "What Changes" portion of the description
        """
        if not description or not description.strip():
            return "No description provided."

        # Sections that mark the end of "What Changes" content
        # Check for both "## Section" and "- ## Section" patterns
        end_section_keywords = [
            "acceptance criteria",
            "dependencies",
            "related issues",
            "related prs",
            "related issues/prs",
            "additional context",
            "testing",
            "documentation",
            "security",
            "quality",
            "non-functional",
            "three-phase",
            "known limitations",
            "security model",
        ]

        lines = description.split("\n")
        what_changes_lines = []

        for line in lines:
            stripped = line.strip()

            # Check if this line starts a section that should be excluded
            # Handle both "## Section" and "- ## Section" patterns
            if stripped.startswith("##") or (stripped.startswith("-") and "##" in stripped):
                # Extract section title (remove leading "- " and "## ")
                # Handle patterns like "- ## Section", "## Section", "- ### Section"
                section_title = re.sub(r"^-\s*#+\s*|^#+\s*", "", stripped).strip().lower()

                # Check if this is an excluded section
                if any(keyword in section_title for keyword in end_section_keywords):
                    break

                # If it's a major section (##) that's not "What Changes" or "Why", we're done
                # But allow subsections (###) within What Changes
                # Check if it starts with ## (not ###)
                if (
                    stripped.startswith(("##", "- ##"))
                    and not stripped.startswith(("###", "- ###"))
                    and section_title not in ["what changes", "why"]
                ):
                    break

            what_changes_lines.append(line)

        result = "\n".join(what_changes_lines).strip()

        # If we didn't extract anything meaningful, return the original
        # (but this shouldn't happen if description is well-formed)
        if not result or len(result) < 20:
            return description

        return result

    def _extract_dependencies_section(self, description: str) -> str:
        """
        Extract Dependencies section from proposal description.

        Args:
            description: Proposal description text

        Returns:
            Dependencies section content, or empty string if not found
        """
        if not description:
            return ""

        # Look for Dependencies section (may have leading "- " from bullet conversion)
        # Pattern: "- ## Dependencies" or "## Dependencies"
        deps_match = re.search(
            r"(?i)(?:-\s*)?##\s*Dependencies\s*\n(.*?)(?=\n\s*(?:-\s*)?##|\Z)",
            description,
            re.DOTALL,
        )

        if deps_match:
            deps_content = deps_match.group(1).strip()
            # Remove leading "- " from lines if present (from bullet conversion)
            lines = deps_content.split("\n")
            cleaned_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("- "):
                    cleaned_lines.append(stripped[2:])
                elif stripped.startswith("-"):
                    cleaned_lines.append(stripped[1:].lstrip())
                else:
                    cleaned_lines.append(line)
            return "\n".join(cleaned_lines)

        return ""

    def _write_openspec_change_from_proposal(
        self,
        proposal: Any,
        bridge_config: Any,
        template_id: str | None = None,
        refinement_confidence: float | None = None,
    ) -> list[str]:
        """
        Write OpenSpec change files from imported ChangeProposal.

        Args:
            proposal: ChangeProposal instance
            bridge_config: Bridge configuration
            template_id: Optional template ID used for refinement
            refinement_confidence: Optional refinement confidence score (0.0-1.0)

        Returns:
            List of warnings (empty if successful)
        """
        warnings: list[str] = []
        import logging

        logger = logging.getLogger(__name__)

        # Get OpenSpec changes directory
        openspec_changes_dir = self._get_openspec_changes_dir()
        if not openspec_changes_dir:
            warning = "OpenSpec changes directory not found. Skipping file creation."
            warnings.append(warning)
            logger.warning(warning)
            console.print(f"[yellow]⚠[/yellow] {warning}")
            return warnings

        # Validate and generate change ID
        change_id = proposal.name
        if change_id == "unknown" or not change_id:
            # Generate from title
            title_clean = self._format_proposal_title(proposal.title)
            change_id = re.sub(r"[^a-z0-9]+", "-", title_clean.lower()).strip("-")
            if not change_id:
                change_id = "imported-change"

        # Check if change directory already exists (for updates)
        change_dir = openspec_changes_dir / change_id

        # If directory exists with proposal.md, update it (don't create duplicate)
        # Only create new directory if it doesn't exist or is empty
        if change_dir.exists() and change_dir.is_dir() and (change_dir / "proposal.md").exists():
            # Existing change - we'll update the files
            logger.info(f"Updating existing OpenSpec change: {change_id}")
        else:
            # New change or empty directory - handle duplicates only if directory exists but is different change
            counter = 1
            original_change_id = change_id
            while change_dir.exists() and change_dir.is_dir():
                change_id = f"{original_change_id}-{counter}"
                change_dir = openspec_changes_dir / change_id
                counter += 1

        try:
            # Create change directory (or use existing)
            change_dir.mkdir(parents=True, exist_ok=True)

            # Write proposal.md
            proposal_lines = []
            proposal_lines.append(f"# Change: {self._format_proposal_title(proposal.title)}")
            proposal_lines.append("")
            proposal_lines.append("## Why")
            proposal_lines.append("")
            proposal_lines.append(proposal.rationale or "No rationale provided.")
            proposal_lines.append("")
            proposal_lines.append("## What Changes")
            proposal_lines.append("")
            description = proposal.description or "No description provided."
            # Extract only the "What Changes" content (exclude Acceptance Criteria, Dependencies, etc.)
            what_changes_content = self._extract_what_changes_content(description)
            # Format description with NEW/EXTEND/MODIFY markers
            formatted_description = self._format_what_changes_section(what_changes_content)
            proposal_lines.append(formatted_description)
            proposal_lines.append("")

            # Generate Impact section
            affected_specs = self._determine_affected_specs(proposal)
            proposal_lines.append("## Impact")
            proposal_lines.append("")
            proposal_lines.append(f"- **Affected specs**: {', '.join(f'`{s}`' for s in affected_specs)}")
            proposal_lines.append("- **Affected code**: See implementation tasks")
            proposal_lines.append("- **Integration points**: See spec deltas")
            proposal_lines.append("")

            # Extract and add Dependencies section if present
            dependencies_section = self._extract_dependencies_section(proposal.description or "")
            if dependencies_section:
                proposal_lines.append("---")
                proposal_lines.append("")
                proposal_lines.append("## Dependencies")
                proposal_lines.append("")
                proposal_lines.append(dependencies_section)
                proposal_lines.append("")

            # Update source_tracking with refinement metadata if provided
            if proposal.source_tracking and (template_id is not None or refinement_confidence is not None):
                if template_id is not None:
                    proposal.source_tracking.template_id = template_id
                if refinement_confidence is not None:
                    proposal.source_tracking.refinement_confidence = refinement_confidence
                    proposal.source_tracking.refinement_timestamp = datetime.now(UTC)

            # Write Source Tracking section
            if proposal.source_tracking:
                proposal_lines.append("---")
                proposal_lines.append("")
                proposal_lines.append("## Source Tracking")
                proposal_lines.append("")

                # Extract source tracking info
                source_metadata = (
                    proposal.source_tracking.source_metadata if proposal.source_tracking.source_metadata else {}
                )

                # Add refinement metadata if present
                if proposal.source_tracking.template_id:
                    proposal_lines.append(f"- **Template ID**: {proposal.source_tracking.template_id}")
                if proposal.source_tracking.refinement_confidence is not None:
                    proposal_lines.append(
                        f"- **Refinement Confidence**: {proposal.source_tracking.refinement_confidence:.2f}"
                    )
                if proposal.source_tracking.refinement_timestamp:
                    proposal_lines.append(
                        f"- **Refinement Timestamp**: {proposal.source_tracking.refinement_timestamp.isoformat()}"
                    )
                if proposal.source_tracking.refinement_ai_model:
                    proposal_lines.append(f"- **Refinement AI Model**: {proposal.source_tracking.refinement_ai_model}")
                if proposal.source_tracking.template_id or proposal.source_tracking.refinement_confidence is not None:
                    proposal_lines.append("")
                if isinstance(source_metadata, dict):
                    backlog_entries = source_metadata.get("backlog_entries", [])
                    if backlog_entries:
                        for entry in backlog_entries:
                            if isinstance(entry, dict):
                                source_repo = entry.get("source_repo", "")
                                source_id = entry.get("source_id", "")
                                source_url = entry.get("source_url", "")
                                source_type = entry.get("source_type", "unknown")

                                if source_repo:
                                    proposal_lines.append(f"<!-- source_repo: {source_repo} -->")

                                # Map source types to proper capitalization (MD034 compliance for URLs)
                                source_type_capitalization = {
                                    "github": "GitHub",
                                    "ado": "ADO",
                                    "linear": "Linear",
                                    "jira": "Jira",
                                    "unknown": "Unknown",
                                }
                                source_type_display = source_type_capitalization.get(source_type.lower(), "Unknown")
                                if source_id:
                                    proposal_lines.append(f"- **{source_type_display} Issue**: #{source_id}")
                                if source_url:
                                    proposal_lines.append(f"- **Issue URL**: <{source_url}>")
                                proposal_lines.append(f"- **Last Synced Status**: {proposal.status}")
                                proposal_lines.append("")

            proposal_file = change_dir / "proposal.md"
            proposal_file.write_text("\n".join(proposal_lines), encoding="utf-8")
            logger.info(f"Created proposal.md: {proposal_file}")

            # Write tasks.md (avoid overwriting existing curated tasks)
            tasks_file = change_dir / "tasks.md"
            if tasks_file.exists():
                warning = f"tasks.md already exists for change '{change_id}', leaving it untouched."
                warnings.append(warning)
                logger.info(warning)
            else:
                tasks_content = self._generate_tasks_from_proposal(proposal)
                tasks_file.write_text(tasks_content, encoding="utf-8")
                logger.info(f"Created tasks.md: {tasks_file}")

            # Write spec deltas
            specs_dir = change_dir / "specs"
            specs_dir.mkdir(exist_ok=True)

            for spec_id in affected_specs:
                spec_dir = specs_dir / spec_id
                spec_dir.mkdir(exist_ok=True)

                spec_lines = []
                spec_lines.append(f"# {spec_id} Specification")
                spec_lines.append("")
                spec_lines.append("## Purpose")
                spec_lines.append("")
                spec_lines.append("TBD - created by importing backlog item")
                spec_lines.append("")
                spec_lines.append("## Requirements")
                spec_lines.append("")

                # Extract requirements from proposal content
                requirement_text = self._extract_requirement_from_proposal(proposal, spec_id)
                if requirement_text:
                    # Determine if this is ADDED or MODIFIED based on proposal content
                    change_type = "MODIFIED"
                    if any(
                        keyword in proposal.description.lower()
                        for keyword in ["new", "add", "introduce", "create", "implement"]
                    ):
                        # Check if it's clearly a new feature vs modification
                        if any(
                            keyword in proposal.description.lower()
                            for keyword in ["extend", "modify", "update", "fix", "improve"]
                        ):
                            change_type = "MODIFIED"
                        else:
                            change_type = "ADDED"

                    spec_lines.append(f"## {change_type} Requirements")
                    spec_lines.append("")
                    spec_lines.append(requirement_text)
                else:
                    # Fallback to placeholder
                    spec_lines.append("## MODIFIED Requirements")
                    spec_lines.append("")
                    spec_lines.append("### Requirement: [Requirement name from proposal]")
                    spec_lines.append("")
                    spec_lines.append("The system SHALL [requirement description]")
                    spec_lines.append("")
                    spec_lines.append("#### Scenario: [Scenario name]")
                    spec_lines.append("")
                    spec_lines.append("- **WHEN** [condition]")
                    spec_lines.append("- **THEN** [expected result]")
                    spec_lines.append("")

                spec_file = spec_dir / "spec.md"
                if spec_file.exists():
                    warning = f"Spec delta already exists for change '{change_id}' ({spec_id}), leaving it untouched."
                    warnings.append(warning)
                    logger.info(warning)
                else:
                    spec_file.write_text("\n".join(spec_lines), encoding="utf-8")
                    logger.info(f"Created spec delta: {spec_file}")

            console.print(f"[green]✓[/green] Created OpenSpec change: {change_id} at {change_dir}")

        except Exception as e:
            warning = f"Failed to create OpenSpec files for change '{change_id}': {e}"
            warnings.append(warning)
            logger.warning(warning, exc_info=True)

        return warnings

    @beartype
    @require(lambda bundle_name: isinstance(bundle_name, str) and len(bundle_name) > 0, "Bundle name must be non-empty")
    @ensure(lambda result: isinstance(result, SyncResult), "Must return SyncResult")
    def sync_bidirectional(self, bundle_name: str, feature_ids: list[str] | None = None) -> SyncResult:
        """
        Perform bidirectional sync for all artifacts.

        Args:
            bundle_name: Project bundle name
            feature_ids: List of feature IDs to sync (all if None)

        Returns:
            SyncResult with all operations
        """
        operations: list[SyncOperation] = []
        errors: list[str] = []
        warnings: list[str] = []

        if self.bridge_config is None:
            errors.append("Bridge config not initialized")
            return SyncResult(success=False, operations=operations, errors=errors, warnings=warnings)

        # Validate bridge config before sync
        probe = BridgeProbe(self.repo_path)
        validation = probe.validate_bridge(self.bridge_config)
        warnings.extend(validation["warnings"])
        errors.extend(validation["errors"])

        if errors:
            return SyncResult(success=False, operations=operations, errors=errors, warnings=warnings)

        # If feature_ids not provided, discover from bridge-resolved paths
        if feature_ids is None:
            feature_ids = self._discover_feature_ids()

        # Sync each feature
        for feature_id in feature_ids:
            # Import from tool → bundle
            for _artifact_key in ["specification", "plan", "tasks"]:
                if _artifact_key in self.bridge_config.artifacts:
                    import_result = self.import_artifact(_artifact_key, feature_id, bundle_name)
                    operations.extend(import_result.operations)
                    errors.extend(import_result.errors)
                    warnings.extend(import_result.warnings)

            # Export from bundle → tool (optional, can be controlled by flag)
            # This would be done separately via export_artifact calls

        return SyncResult(
            success=len(errors) == 0,
            operations=operations,
            errors=errors,
            warnings=warnings,
        )

    @beartype
    @require(lambda self: self.bridge_config is not None, "Bridge config must be set")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def _discover_feature_ids(self) -> list[str]:
        """
        Discover feature IDs from bridge-resolved paths.

        Returns:
            List of feature IDs found in repository
        """
        feature_ids: list[str] = []

        if self.bridge_config is None:
            return feature_ids

        # Try to discover from first artifact pattern
        if "specification" in self.bridge_config.artifacts:
            artifact = self.bridge_config.artifacts["specification"]
            # Extract base directory from pattern (e.g., "specs/{feature_id}/spec.md" -> "specs")
            pattern_parts = artifact.path_pattern.split("/")
            if len(pattern_parts) > 0:
                base_dir = self.repo_path / pattern_parts[0]
                if base_dir.exists():
                    # Find all subdirectories (potential feature IDs)
                    for item in base_dir.iterdir():
                        if item.is_dir():
                            # Check if it contains the expected artifact file
                            test_path = self.resolve_artifact_path("specification", item.name, "test")
                            if test_path.exists() or (item / "spec.md").exists():
                                feature_ids.append(item.name)

        return feature_ids
