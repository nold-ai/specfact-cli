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
from dataclasses import dataclass
from datetime import datetime


try:
    from datetime import UTC
except ImportError:
    UTC = UTC  # type: ignore[assignment]
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require
from rich.progress import Progress
from rich.table import Table

from specfact_cli.adapters.registry import AdapterRegistry
from specfact_cli.models.bridge import BridgeConfig
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
            tmp_file: Optional custom temporary file path. Default: `/tmp/specfact-proposal-<change-id>.md`.

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
            adapter_kwargs: dict[str, Any] = {
                "repo_owner": repo_owner,
                "repo_name": repo_name,
                "api_token": api_token,
            }
            # GitHub adapter requires use_gh_cli flag
            if adapter_type.lower() == "github":
                adapter_kwargs["use_gh_cli"] = use_gh_cli

            adapter = AdapterRegistry.get_adapter(adapter_type, **adapter_kwargs)

            # TODO: Read OpenSpec change proposals via OpenSpec adapter
            # This requires the OpenSpec bridge adapter to be implemented first
            # For now, this is a placeholder
            try:
                # Attempt to read OpenSpec change proposals
                # This will fail gracefully if OpenSpec adapter is not available
                change_proposals = self._read_openspec_change_proposals()
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

            # Derive target_repo from repo_owner and repo_name if not provided
            if not target_repo and repo_owner and repo_name:
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

                    if issue_number and target_entry:
                        # Issue exists - check if status changed or metadata needs update
                        source_metadata = target_entry.get("source_metadata", {})
                        if not isinstance(source_metadata, dict):
                            source_metadata = {}
                        last_synced_status = source_metadata.get("last_synced_status")
                        current_status = proposal.get("status")

                        if last_synced_status != current_status:
                            # Status changed - update issue
                            result = adapter.export_artifact(
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
                        # (even if status hasn't changed, we want to update sanitized flag, etc.)
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
                        # This ensures sanitized flag and other metadata are always up-to-date
                        if target_repo:
                            source_tracking_list = self._update_source_tracking_entry(
                                source_tracking_list, target_repo, updated_entry
                            )
                            proposal["source_tracking"] = source_tracking_list
                        else:
                            # Backward compatibility: update single dict entry directly
                            # If original was a dict, keep it as a dict; otherwise use list
                            if isinstance(source_tracking_raw, dict):
                                # Single dict entry - update and keep as dict
                                proposal["source_tracking"] = updated_entry
                            else:
                                # List of entries - update the matching entry
                                for i, entry in enumerate(source_tracking_list):
                                    if isinstance(entry, dict):
                                        # Find entry matching this repository (by source_id or source_repo)
                                        entry_id = entry.get("source_id")
                                        entry_repo = entry.get("source_repo")
                                        updated_id = updated_entry.get("source_id")
                                        updated_repo = updated_entry.get("source_repo")

                                        if (entry_id and entry_id == updated_id) or (
                                            entry_repo and entry_repo == updated_repo
                                        ):
                                            # Update matching entry with new metadata
                                            source_tracking_list[i] = updated_entry
                                            break
                                proposal["source_tracking"] = source_tracking_list

                        # Track metadata update operation (even if status didn't change)
                        # This ensures we record that a sync operation occurred
                        if last_synced_status == current_status:
                            # Status didn't change, but metadata was updated (sanitized flag, etc.)
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
                            # Handle sanitized content updates (when import_from_tmp is used)
                            if import_from_tmp:
                                change_id = proposal.get("change_id", "unknown")
                                sanitized_file = tmp_file or Path(f"/tmp/specfact-proposal-{change_id}-sanitized.md")
                                if sanitized_file.exists():
                                    # Read sanitized content and use it for hash calculation
                                    sanitized_content = sanitized_file.read_text(encoding="utf-8")
                                    # Parse sanitized content to extract rationale and description
                                    # For now, use the sanitized content directly as description
                                    proposal_for_hash = {
                                        "rationale": "",  # Sanitized content typically doesn't have separate rationale
                                        "description": sanitized_content,
                                    }
                                    current_hash = self._calculate_content_hash(proposal_for_hash)
                                else:
                                    # Fallback to original proposal content
                                    current_hash = self._calculate_content_hash(proposal)
                            else:
                                current_hash = self._calculate_content_hash(proposal)

                            # Get stored hash from target repository entry
                            stored_hash = None
                            if target_entry:
                                source_metadata = target_entry.get("source_metadata", {})
                                if isinstance(source_metadata, dict):
                                    stored_hash = source_metadata.get("content_hash")

                            # Check if title or state needs update (get current issue data)
                            current_issue_title = None
                            current_issue_state = None
                            needs_title_update = False
                            needs_state_update = False
                            if target_entry:
                                issue_number = target_entry.get("source_id")
                                if issue_number:
                                    # Fetch current issue to check title and state
                                    try:
                                        from specfact_cli.adapters.registry import AdapterRegistry

                                        adapter_instance = AdapterRegistry.get_adapter(adapter_type)
                                        if adapter_instance and hasattr(adapter_instance, "api_token"):
                                            import requests

                                            url = f"{adapter_instance.base_url}/repos/{repo_owner}/{repo_name}/issues/{issue_number}"
                                            headers = {
                                                "Authorization": f"token {adapter_instance.api_token}",
                                                "Accept": "application/vnd.github.v3+json",
                                            }
                                            response = requests.get(url, headers=headers, timeout=30)
                                            response.raise_for_status()
                                            issue_data = response.json()
                                            current_issue_title = issue_data.get("title", "")
                                            current_issue_state = issue_data.get("state", "open")
                                            proposal_title = proposal.get("title", "")
                                            proposal_status = proposal.get("status", "proposed")
                                            needs_title_update = (
                                                current_issue_title
                                                and proposal_title
                                                and current_issue_title != proposal_title
                                            )
                                            # Check if state needs update (applied/deprecated/discarded should be closed)
                                            should_close = proposal_status in ("applied", "deprecated", "discarded")
                                            desired_state = "closed" if should_close else "open"
                                            needs_state_update = current_issue_state != desired_state
                                    except Exception:
                                        # If we can't fetch, proceed without title/state check
                                        pass

                            if stored_hash != current_hash or needs_title_update or needs_state_update:
                                # Content changed or title needs update - update issue body and/or title
                                try:
                                    # If using sanitized content, update proposal with sanitized content
                                    if import_from_tmp:
                                        change_id = proposal.get("change_id", "unknown")
                                        sanitized_file = tmp_file or Path(
                                            f"/tmp/specfact-proposal-{change_id}-sanitized.md"
                                        )
                                        if sanitized_file.exists():
                                            sanitized_content = sanitized_file.read_text(encoding="utf-8")
                                            # Update proposal with sanitized content for issue update
                                            proposal_for_update = {
                                                **proposal,
                                                "description": sanitized_content,
                                                "rationale": "",  # Sanitized content typically doesn't have separate rationale
                                            }
                                        else:
                                            proposal_for_update = proposal
                                    else:
                                        proposal_for_update = proposal

                                    result = adapter.export_artifact(
                                        artifact_key="change_proposal_update",
                                        artifact_data=proposal_for_update,
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
                                    else:
                                        # Create new entry for this repository
                                        if target_repo:
                                            new_entry = {
                                                "source_repo": target_repo,
                                                "source_metadata": {"content_hash": current_hash},
                                            }
                                            source_tracking_list = self._update_source_tracking_entry(
                                                source_tracking_list, target_repo, new_entry
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
                                    # Log error but don't fail entire sync
                                    errors.append(
                                        f"Failed to update issue body for {proposal.get('change_id', 'unknown')}: {e}"
                                    )

                        # Code change tracking and progress comments (when enabled)
                        if track_code_changes or add_progress_comment:
                            from specfact_cli.utils.code_change_detector import (
                                calculate_comment_hash,
                                detect_code_changes,
                                format_progress_comment,
                            )

                            change_id = proposal.get("change_id", "unknown")
                            progress_data: dict[str, Any] = {}

                            if track_code_changes:
                                # Detect code changes via git
                                try:
                                    # Get last detection timestamp from source tracking
                                    last_detection = None
                                    if target_entry:
                                        source_metadata = target_entry.get("source_metadata", {})
                                        if isinstance(source_metadata, dict):
                                            last_detection = source_metadata.get("last_code_change_detected")

                                    # Detect code changes
                                    # Use code_repo_path if provided (for separate source code repo),
                                    # otherwise fall back to self.repo_path (OpenSpec repo)
                                    code_repo = code_repo_path if code_repo_path else self.repo_path
                                    code_changes = detect_code_changes(
                                        repo_path=code_repo,
                                        change_id=change_id,
                                        since_timestamp=last_detection,
                                    )

                                    if code_changes.get("has_changes"):
                                        progress_data = code_changes
                                    else:
                                        # No code changes detected
                                        continue
                                except Exception as e:
                                    # Log error but don't fail entire sync
                                    errors.append(f"Failed to detect code changes for {change_id}: {e}")
                                    continue

                            if add_progress_comment and not progress_data:
                                # Manual progress comment (no code change detection)
                                progress_data = {
                                    "summary": "Manual progress update",
                                    "detection_timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                                }

                            if progress_data:
                                # Check for duplicate comments
                                # Calculate hash on sanitized version if sanitization is enabled
                                # (to detect duplicates based on what will actually be posted)
                                comment_text = format_progress_comment(
                                    progress_data, sanitize=should_sanitize if should_sanitize is not None else False
                                )
                                comment_hash = calculate_comment_hash(comment_text)

                                # Get existing progress comments from source tracking
                                progress_comments = []
                                if target_entry:
                                    source_metadata = target_entry.get("source_metadata", {})
                                    if isinstance(source_metadata, dict):
                                        progress_comments = source_metadata.get("progress_comments", [])

                                # Check if this comment already exists
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
                                        # Add progress comment to issue
                                        # Ensure source_tracking is included for adapter to extract issue number
                                        proposal_with_progress = {
                                            **proposal,
                                            "source_tracking": source_tracking_list,  # Ensure source_tracking is available
                                            "progress_data": progress_data,
                                            "sanitize": should_sanitize if should_sanitize is not None else False,
                                        }
                                        result = adapter.export_artifact(
                                            artifact_key="code_change_progress",
                                            artifact_data=proposal_with_progress,
                                            bridge_config=self.bridge_config,
                                        )

                                        # Update source tracking with progress comment
                                        if target_entry:
                                            source_metadata = target_entry.get("source_metadata", {})
                                            if not isinstance(source_metadata, dict):
                                                source_metadata = {}
                                            progress_comments = source_metadata.get("progress_comments", [])
                                            if not isinstance(progress_comments, list):
                                                progress_comments = []

                                            # Add new comment to history
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
                                                    "last_code_change_detected": progress_data.get(
                                                        "detection_timestamp"
                                                    ),
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

                                        # Save updated proposal with progress comment metadata
                                        self._save_openspec_change_proposal(proposal)
                                    except Exception as e:
                                        # Log error but don't fail entire sync
                                        errors.append(f"Failed to add progress comment for {change_id}: {e}")
                                else:
                                    # Duplicate comment - skip
                                    warnings.append(f"Skipped duplicate progress comment for {change_id}")
                    else:
                        # No issue exists - create one
                        # Handle temporary file workflow if requested
                        change_id = proposal.get("change_id", "unknown")
                        if export_to_tmp:
                            # Export proposal content to temporary file for LLM review
                            tmp_file_path = tmp_file or Path(f"/tmp/specfact-proposal-{change_id}.md")
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
                            sanitized_file_path = tmp_file or Path(f"/tmp/specfact-proposal-{change_id}-sanitized.md")
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
                                    original_tmp = Path(f"/tmp/specfact-proposal-{change_id}.md")
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
                                    why_match = re.search(
                                        r"##\s*Why\s*\n\n(.*?)(?=\n##|\Z)", sanitized_markdown, re.DOTALL
                                    )
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
                            repo_identifier = target_repo or f"{repo_owner}/{repo_name}"
                            new_entry = {
                                "source_id": str(result.get("issue_number", "")),
                                "source_url": str(result.get("issue_url", "")),
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

    def _read_openspec_change_proposals(self) -> list[dict[str, Any]]:
        """
        Read OpenSpec change proposals from openspec/changes/ directory.

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
                status = "proposed"  # Default status

                lines = proposal_content.split("\n")
                in_why = False
                in_what = False
                in_source_tracking = False

                for line in lines:
                    line_stripped = line.strip()
                    if line_stripped.startswith("# Change:"):
                        title = line_stripped.replace("# Change:", "").strip()
                    elif line_stripped == "## Why":
                        in_why = True
                        in_what = False
                        in_source_tracking = False
                    elif line_stripped == "## What Changes":
                        in_why = False
                        in_what = True
                        in_source_tracking = False
                    elif line_stripped == "## Impact":
                        # Skip Impact section (not used in current implementation)
                        in_why = False
                        in_what = False
                        in_source_tracking = False
                    elif line_stripped == "## Source Tracking":
                        in_why = False
                        in_what = False
                        in_source_tracking = True
                    elif in_source_tracking:
                        # Skip source tracking section (we'll parse it separately)
                        continue
                    elif in_why and not line_stripped.startswith("#") and not line_stripped.startswith("---"):
                        # Preserve line breaks in rationale
                        if rationale and not rationale.endswith("\n"):
                            rationale += "\n"
                        rationale += line + "\n"
                    elif in_what and not line_stripped.startswith("#") and not line_stripped.startswith("---"):
                        # Preserve line breaks in description
                        if description and not description.endswith("\n"):
                            description += "\n"
                        description += line + "\n"

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
                            entry = self._parse_source_tracking_entry(tracking_content, None)
                            if entry:
                                source_tracking_list.append(entry)

                # Check for status indicators in proposal content or directory name
                # Status could be inferred from directory structure or metadata files
                # For now, default to "proposed" - can be enhanced later

                # Clean up description and rationale (remove extra newlines)
                description_clean = description.strip() if description else ""
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
                    status = "applied"  # Archived changes are treated as "applied"

                    lines = proposal_content.split("\n")
                    in_why = False
                    in_what = False
                    in_source_tracking = False

                    for line in lines:
                        line_stripped = line.strip()
                        if line_stripped.startswith("# Change:"):
                            title = line_stripped.replace("# Change:", "").strip()
                            continue
                        if line_stripped == "## Why":
                            in_why = True
                            in_what = False
                            in_source_tracking = False
                        elif line_stripped == "## What Changes":
                            in_why = False
                            in_what = True
                            in_source_tracking = False
                        elif line_stripped == "## Impact":
                            in_why = False
                            in_what = False
                            in_source_tracking = False
                        elif line_stripped == "## Source Tracking":
                            in_why = False
                            in_what = False
                            in_source_tracking = True
                        elif in_source_tracking:
                            continue
                        elif in_why and not line_stripped.startswith("#") and not line_stripped.startswith("---"):
                            if rationale and not rationale.endswith("\n"):
                                rationale += "\n"
                            rationale += line + "\n"
                        elif in_what and not line_stripped.startswith("#") and not line_stripped.startswith("---"):
                            if description and not description.endswith("\n"):
                                description += "\n"
                            description += line + "\n"

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
                    description_clean = description.strip() if description else ""
                    rationale_clean = rationale.strip() if rationale else ""

                    proposal = {
                        "change_id": change_id,
                        "title": title or change_id,
                        "description": description_clean or "No description provided.",
                        "rationale": rationale_clean or "No rationale provided.",
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
            # Check if it matches target_repo (extract from source_url if available)
            if target_repo:
                source_url = source_tracking.get("source_url", "")
                if source_url:
                    url_repo_match = re.search(r"github\.com/([^/]+/[^/]+)/", source_url)
                    if url_repo_match:
                        source_repo = url_repo_match.group(1)
                        if source_repo == target_repo:
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
                    if entry_repo == target_repo:
                        return entry
                    # Backward compatibility: if no source_repo, try to extract from source_url
                    if not entry_repo and target_repo:
                        source_url = entry.get("source_url", "")
                        if source_url:
                            url_repo_match = re.search(r"github\.com/([^/]+/[^/]+)/", source_url)
                            if url_repo_match:
                                source_repo = url_repo_match.group(1)
                                if source_repo == target_repo:
                                    return entry

        return None

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
        # Ensure source_repo is set
        entry_data["source_repo"] = target_repo

        # Find existing entry for this repo
        for i, entry in enumerate(source_tracking_list):
            if isinstance(entry, dict) and entry.get("source_repo") == target_repo:
                # Update existing entry
                source_tracking_list[i] = {**entry, **entry_data}
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
                url_repo_match = re.search(r"github\.com/([^/]+/[^/]+)/", entry["source_url"])
                if url_repo_match:
                    entry["source_repo"] = url_repo_match.group(1)

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
                source_repo = entry.get("source_repo")
                if source_repo and (len(source_tracking_list) > 1 or i > 0):
                    metadata_lines.append(f"### Repository: {source_repo}")
                    metadata_lines.append("")

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
