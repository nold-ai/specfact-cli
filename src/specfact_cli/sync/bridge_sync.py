"""
Bridge-based bidirectional sync implementation.

This module provides adapter-agnostic bidirectional synchronization between
external tool artifacts and SpecFact project bundles using bridge configuration.
The sync layer reads bridge config, resolves paths dynamically, and delegates
to adapter-specific parsers/generators.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import logging
import re
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlparse

from beartype import beartype
from icontract import ensure, require
from rich.progress import Progress
from rich.table import Table

from specfact_cli.adapters.registry import AdapterRegistry
from specfact_cli.models.bridge import AdapterType, BridgeConfig
from specfact_cli.runtime import get_configured_console
from specfact_cli.sync.bridge_probe import BridgeProbe
from specfact_cli.sync.bridge_sync_openspec_md_parse import bridge_sync_parse_openspec_proposal_markdown
from specfact_cli.sync.bridge_sync_requirement_from_proposal import bridge_sync_extract_requirement_from_proposal
from specfact_cli.sync.bridge_sync_tasks_from_proposal import bridge_sync_generate_tasks_from_proposal
from specfact_cli.sync.bridge_sync_what_changes_format import bridge_sync_format_what_changes_section
from specfact_cli.sync.bridge_sync_write_openspec_from_proposal import bridge_sync_write_openspec_change_from_proposal
from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle
from specfact_cli.utils.terminal import get_progress_config


console = get_configured_console()


def _repo_path_exists(repo_path: Path) -> bool:
    return repo_path.exists()


def _repo_path_is_dir(repo_path: Path) -> bool:
    return repo_path.is_dir()


def _code_repo_from_cwd(repo_name: str) -> Path | None:
    """Return repo path if cwd matches repo_name and origin URL contains repo_name."""
    try:
        cwd = Path.cwd()
        if cwd.name != repo_name or not (cwd / ".git").exists():
            return None
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
    except (OSError, ValueError):
        pass
    return None


def _code_repo_from_parent(repo_name: str) -> Path | None:
    """Return repo path if parent/<repo_name> is a git checkout."""
    try:
        cwd = Path.cwd()
        repo_path = cwd.parent / repo_name
        if repo_path.exists() and (repo_path / ".git").exists():
            return repo_path
    except (OSError, ValueError):
        pass
    return None


def _code_repo_from_grandparent_siblings(repo_name: str) -> Path | None:
    """Return repo path if a sibling under grandparent matches repo_name."""
    try:
        cwd = Path.cwd()
        grandparent = cwd.parent.parent if cwd.parent != Path("/") else None
        if not grandparent:
            return None
        for sibling in grandparent.iterdir():
            if sibling.is_dir() and sibling.name == repo_name and (sibling / ".git").exists():
                return sibling
    except (OSError, ValueError):
        pass
    return None


def _bridge_config_set(self: BridgeSync) -> bool:
    return self.bridge_config is not None


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


@dataclass(frozen=True)
class ExportChangeProposalsOptions:
    """Keyword options for :meth:`BridgeSync.export_change_proposals_to_devops`."""

    repo_owner: str | None = None
    repo_name: str | None = None
    api_token: str | None = None
    use_gh_cli: bool = True
    sanitize: bool | None = None
    target_repo: str | None = None
    interactive: bool = False
    change_ids: list[str] | None = None
    export_to_tmp: bool = False
    import_from_tmp: bool = False
    tmp_file: Path | None = None
    update_existing: bool = False
    track_code_changes: bool = False
    add_progress_comment: bool = False
    code_repo_path: Path | None = None
    include_archived: bool = False
    ado_org: str | None = None
    ado_project: str | None = None
    ado_base_url: str | None = None
    ado_work_item_type: str | None = None


@dataclass
class _AlignmentReportContentInput:
    adapter_name: str
    external_feature_ids: set[str]
    specfact_feature_ids: set[str]
    aligned: set[str]
    gaps_in_specfact: set[str]
    gaps_in_external: set[str]
    coverage: float


@dataclass
class _AdoWorkItemVerifyInput:
    issue_number: str | int | None
    target_entry: dict[str, Any] | None
    adapter_type: str
    adapter: Any
    ado_org: str | None
    ado_project: str | None


@dataclass
class _GithubIssueSearchInput:
    proposal: dict[str, Any]
    change_id: str
    adapter_type: str
    repo_owner: str | None
    repo_name: str | None
    target_repo: str | None
    source_tracking_list: list[dict[str, Any]]
    warnings: list[str]
    target_entry: dict[str, Any] | None
    issue_number: str | int | None


@dataclass
class _AdoIssueSearchInput:
    proposal: dict[str, Any]
    change_id: str
    adapter_type: str
    adapter: Any
    ado_org: str | None
    ado_project: str | None
    source_tracking_list: list[dict[str, Any]]
    target_entry: dict[str, Any] | None
    issue_number: str | int | None


@dataclass
class _RemoteIssueResolutionInput:
    proposal: dict[str, Any]
    change_id: str
    adapter_type: str
    adapter: Any
    repo_owner: str | None
    repo_name: str | None
    ado_org: str | None
    ado_project: str | None
    target_repo: str | None
    source_tracking_list: list[dict[str, Any]]
    warnings: list[str]
    target_entry: dict[str, Any] | None
    issue_number: str | int | None


@dataclass
class _RecordCreatedIssueInput:
    result: dict[str, Any]
    adapter_type: str
    ado_org: str | None
    ado_project: str | None
    repo_owner: str | None
    repo_name: str | None
    target_repo: str | None
    should_sanitize: bool | None


@dataclass
class _DevOpsAdapterKwargsInput:
    adapter_type: str
    repo_owner: str | None
    repo_name: str | None
    api_token: str | None
    use_gh_cli: bool
    ado_org: str | None
    ado_project: str | None
    ado_base_url: str | None
    ado_work_item_type: str | None


@dataclass
class _IssueUpdatePayload:
    proposal: dict[str, Any]
    target_entry: dict[str, Any] | None
    issue_number: str | int | None
    adapter: Any
    adapter_type: str
    target_repo: str | None
    source_tracking_list: list[dict[str, Any]]
    source_tracking_raw: dict[str, Any] | list[dict[str, Any]]
    repo_owner: str | None
    repo_name: str | None
    ado_org: str | None
    ado_project: str | None
    update_existing: bool
    import_from_tmp: bool
    tmp_file: Path | None
    should_sanitize: bool | None
    track_code_changes: bool
    add_progress_comment: bool
    code_repo_path: Path | None
    operations: list[SyncOperation]
    errors: list[str]
    warnings: list[str]


@dataclass(frozen=True)
class _ExportIterationTracking:
    source_tracking_list: list[dict[str, Any]]
    source_tracking_raw: dict[str, Any] | list[dict[str, Any]]


@dataclass
class _ChangeProposalExportLoopContext:
    adapter: Any
    adapter_type: str
    target_repo: str | None
    repo_owner: str | None
    repo_name: str | None
    ado_org: str | None
    ado_project: str | None
    update_existing: bool
    import_from_tmp: bool
    export_to_tmp: bool
    tmp_file: Path | None
    should_sanitize: bool | None
    sanitizer: Any
    track_code_changes: bool
    add_progress_comment: bool
    code_repo_path: Path | None
    operations: list[SyncOperation]
    errors: list[str]
    warnings: list[str]


@dataclass
class _BundleAdapterExportInput:
    proposal: Any
    proposal_dict: dict[str, Any]
    target_entry: dict[str, Any] | None
    adapter: Any
    adapter_type: str
    bridge_config: Any
    bundle_name: str
    target_repo: str | None
    update_existing: bool
    entries: list[dict[str, Any]]
    operations: list[SyncOperation]
    errors: list[str]


@dataclass
class _BundleSingleExportInput:
    proposal: Any
    adapter: Any
    adapter_type: str
    bridge_config: Any
    bundle_name: str
    target_repo: str | None
    update_existing: bool
    operations: list[SyncOperation]
    errors: list[str]


@dataclass
class _WorkItemVerifyInput:
    issue_number: str | int | None
    target_entry: dict[str, Any] | None
    adapter_type: str
    adapter: Any
    ado_org: str | None
    ado_project: str | None


@dataclass
class _FetchIssueSyncStateInput:
    adapter_type: str
    issue_num: str | int
    repo_owner: str | None
    repo_name: str | None
    ado_org: str | None
    ado_project: str | None
    proposal_title: str
    proposal_status: str


@dataclass
class _PushIssueBodyInput:
    proposal: dict[str, Any]
    target_entry: dict[str, Any]
    adapter: Any
    import_from_tmp: bool
    tmp_file: Path | None
    repo_owner: str | None
    repo_name: str | None
    target_repo: str | None
    source_tracking_list: list[dict[str, Any]]
    current_hash: str
    content_or_meta_changed: bool
    needs_comment_for_applied: bool
    operations: list[Any]
    errors: list[str]


@dataclass
class _IssueContentUpdateInput:
    proposal: dict[str, Any]
    target_entry: dict[str, Any]
    issue_number: str | int
    adapter: Any
    adapter_type: str
    target_repo: str | None
    source_tracking_list: list[dict[str, Any]]
    repo_owner: str | None
    repo_name: str | None
    ado_org: str | None
    ado_project: str | None
    import_from_tmp: bool
    tmp_file: Path | None
    operations: list[Any]
    errors: list[str]


@dataclass
class _EmitCodeChangeProgressInput:
    proposal: dict[str, Any]
    change_id: str
    target_entry: dict[str, Any] | None
    target_repo: str | None
    source_tracking_list: list[dict[str, Any]]
    progress_data: dict[str, Any]
    adapter: Any
    should_sanitize: bool | None
    operations: list[Any]
    errors: list[str]
    warnings: list[str]


@dataclass
class _CodeChangeTrackingInput:
    proposal: dict[str, Any]
    target_entry: dict[str, Any] | None
    target_repo: str | None
    source_tracking_list: list[dict[str, Any]]
    adapter: Any
    track_code_changes: bool
    add_progress_comment: bool
    code_repo_path: Path | None
    should_sanitize: bool | None
    operations: list[Any]
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

    def _resolve_alignment_adapter(self) -> tuple[Any | None, str]:
        """Return the configured adapter instance and display name for alignment reporting."""
        if not self.bridge_config:
            return None, "External Tool"

        adapter_name = self.bridge_config.adapter.value
        adapter = AdapterRegistry.get_adapter(adapter_name)
        return adapter, adapter_name.upper()

    def _load_alignment_report_inputs(self, bundle_name: str) -> tuple[set[str], set[str], str] | None:
        """Load external and SpecFact feature IDs for an alignment report."""
        from specfact_cli.utils.structure import SpecFactStructure

        adapter, adapter_name = self._resolve_alignment_adapter()
        if not self.bridge_config or not adapter:
            return None

        bundle_dir = self.repo_path / SpecFactStructure.PROJECTS / bundle_name
        if not bundle_dir.exists():
            return None

        project_bundle = load_project_bundle(bundle_dir, validate_hashes=False)
        base_path = self.bridge_config.external_base_path if self.bridge_config.external_base_path else self.repo_path
        adapter_any = cast(Any, adapter)
        external_features: list[dict[str, Any]] = adapter_any.discover_features(base_path, self.bridge_config)
        external_feature_ids = {
            str(feature.get("feature_key") or feature.get("key") or "")
            for feature in external_features
            if str(feature.get("feature_key") or feature.get("key") or "")
        }
        specfact_feature_ids = set(project_bundle.features.keys()) if project_bundle.features else set()
        return external_feature_ids, specfact_feature_ids, adapter_name

    def _render_alignment_gaps(self, gaps: set[str], heading: str) -> None:
        """Render a gap table when there are missing features."""
        if not gaps:
            return

        console.print(f"\n[bold yellow]⚠ {heading}[/bold yellow]")
        gaps_table = Table(show_header=True, header_style="bold yellow")
        gaps_table.add_column("Feature ID", style="cyan")
        for feature_id in sorted(gaps):
            gaps_table.add_row(feature_id)
        console.print(gaps_table)

    def _build_alignment_report_content(self, snap: _AlignmentReportContentInput) -> str:
        """Build markdown content for a saved alignment report."""
        adapter_name = snap.adapter_name
        external_feature_ids = snap.external_feature_ids
        specfact_feature_ids = snap.specfact_feature_ids
        aligned = snap.aligned
        gaps_in_specfact = snap.gaps_in_specfact
        gaps_in_external = snap.gaps_in_external
        coverage = snap.coverage
        return f"""# Alignment Report: SpecFact vs {adapter_name}

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

    @beartype
    @require(_repo_path_exists, "Repository path must exist")
    @require(_repo_path_is_dir, "Repository path must be a directory")
    def __init__(self, repo_path: Path, bridge_config: BridgeConfig | None = None) -> None:
        """
        Initialize bridge sync.

        Args:
            repo_path: Path to repository root
            bridge_config: Bridge configuration (auto-detected if None)
        """
        assert repo_path.exists(), "Repository path must exist"
        assert repo_path.is_dir(), "Repository path must be a directory"
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
        _ = repo_owner
        return (
            _code_repo_from_cwd(repo_name)
            or _code_repo_from_parent(repo_name)
            or _code_repo_from_grandparent_siblings(repo_name)
        )

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
    @require(_bridge_config_set, "Bridge config must be set")
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
    @require(_bridge_config_set, "Bridge config must be set")
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
        if not self.bridge_config:
            console.print("[yellow]⚠[/yellow] Bridge config not available for alignment report")
            return

        inputs = self._load_alignment_report_inputs(bundle_name)
        if not inputs:
            adapter_name = self.bridge_config.adapter.value.upper() if self.bridge_config else "External Tool"
            console.print(f"[bold red]✗[/bold red] Could not load alignment inputs for {adapter_name}")
            return

        external_feature_ids, specfact_feature_ids, adapter_name = inputs

        progress_columns, progress_kwargs = get_progress_config()
        with Progress(
            *progress_columns,
            console=console,
            **progress_kwargs,
        ) as progress:
            task = progress.add_task("Generating alignment report...", total=None)
            aligned = specfact_feature_ids & external_feature_ids
            gaps_in_specfact = external_feature_ids - specfact_feature_ids
            gaps_in_external = specfact_feature_ids - external_feature_ids

            total_specs = len(external_feature_ids) if external_feature_ids else 1
            coverage = (len(aligned) / total_specs * 100) if total_specs > 0 else 0.0

            progress.update(task, completed=1)

        # Generate Rich-formatted report (adapter-agnostic)
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
        self._render_alignment_gaps(gaps_in_specfact, f"Gaps in SpecFact ({adapter_name} specs not extracted):")
        self._render_alignment_gaps(
            gaps_in_external,
            f"Gaps in {adapter_name} (SpecFact features not in {adapter_name}):",
        )

        # Save to file if requested
        if output_file:
            report_content = self._build_alignment_report_content(
                _AlignmentReportContentInput(
                    adapter_name,
                    external_feature_ids,
                    specfact_feature_ids,
                    aligned,
                    gaps_in_specfact,
                    gaps_in_external,
                    coverage,
                )
            )
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(report_content, encoding="utf-8")
            console.print(f"\n[bold green]✓[/bold green] Report saved to {output_file}")

    def _bridge_sync_effective_planning_repo(self) -> Path:
        """Planning repo path for sanitization detection (may be external_base_path)."""
        planning_repo = self.repo_path
        if self.bridge_config and hasattr(self.bridge_config, "external_base_path"):
            external_path = getattr(self.bridge_config, "external_base_path", None)
            if external_path:
                planning_repo = Path(external_path)
        return planning_repo

    def _bridge_sync_filter_devops_proposals(
        self,
        change_proposals: list[dict[str, Any]],
        should_sanitize: bool,
        target_repo: str | None,
    ) -> tuple[list[dict[str, Any]], int]:
        """Return proposals to sync and count of filtered-out proposals."""
        active_proposals: list[dict[str, Any]] = []
        filtered_count = 0
        for proposal in change_proposals:
            proposal_status = proposal.get("status", "proposed")
            source_tracking_raw = proposal.get("source_tracking", {})
            target_entry = self._find_source_tracking_entry(source_tracking_raw, target_repo)
            has_target_entry = target_entry is not None
            if should_sanitize:
                should_sync = proposal_status == "applied"
            elif has_target_entry:
                should_sync = True
            else:
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
        return active_proposals, filtered_count

    def _bridge_sync_verify_ado_tracked_work_item(
        self,
        verify: _AdoWorkItemVerifyInput,
        proposal: dict[str, Any],
        warnings: list[str],
    ) -> tuple[str | int | None, bool, dict[str, Any] | None]:
        """Clear ADO source_id when the tracked work item no longer exists."""
        issue_number = verify.issue_number
        target_entry = verify.target_entry
        adapter_type = verify.adapter_type
        adapter = verify.adapter
        ado_org = verify.ado_org
        ado_project = verify.ado_project
        work_item_was_deleted = False
        if not issue_number or not target_entry:
            return issue_number, work_item_was_deleted, target_entry

        entry_type = target_entry.get("source_type", "").lower()
        if not (
            entry_type == "ado"
            and adapter_type.lower() == "ado"
            and ado_org
            and ado_project
            and hasattr(adapter, "_work_item_exists")
        ):
            return issue_number, work_item_was_deleted, target_entry

        try:
            adapter_any = cast(Any, adapter)
            work_item_exists = adapter_any._work_item_exists(issue_number, ado_org, ado_project)
            if not work_item_exists:
                warnings.append(
                    f"Work item #{issue_number} for '{proposal.get('change_id', 'unknown')}' "
                    f"no longer exists in ADO (may have been deleted). "
                    f"Will create a new work item."
                )
                cleared_entry = cast(dict[str, Any], {**target_entry, "source_id": None})
                return None, True, cleared_entry
        except Exception as e:
            warnings.append(f"Could not verify work item #{issue_number} existence: {e}. Proceeding with sync.")

        return issue_number, work_item_was_deleted, target_entry

    def _bridge_sync_clear_corrupted_tracking_entry(
        self,
        proposal: dict[str, Any],
        source_tracking_raw: dict[str, Any] | list[dict[str, Any]],
        source_tracking_list: list[dict[str, Any]],
        target_entry: dict[str, Any],
    ) -> tuple[None, list[dict[str, Any]]]:
        """Remove unusable source_tracking entries when update_existing is set."""
        if isinstance(source_tracking_raw, dict):
            proposal["source_tracking"] = {}
            return None, source_tracking_list
        pruned = [entry for entry in source_tracking_list if entry is not target_entry]
        proposal["source_tracking"] = pruned
        return None, pruned

    def _bridge_sync_try_github_issue_by_search(
        self,
        search: _GithubIssueSearchInput,
    ) -> tuple[dict[str, Any] | None, str | int | None, list[dict[str, Any]]]:
        proposal = search.proposal
        change_id = search.change_id
        adapter_type = search.adapter_type
        repo_owner = search.repo_owner
        repo_name = search.repo_name
        target_repo = search.target_repo
        source_tracking_list = search.source_tracking_list
        warnings = search.warnings
        target_entry = search.target_entry
        issue_number = search.issue_number
        if target_entry or adapter_type.lower() != "github" or not repo_owner or not repo_name:
            return target_entry, issue_number, source_tracking_list
        found_entry, found_issue_number = self._search_existing_github_issue(
            change_id, repo_owner, repo_name, target_repo, warnings
        )
        if not (found_entry and found_issue_number):
            return target_entry, issue_number, source_tracking_list
        source_tracking_list.append(found_entry)
        proposal["source_tracking"] = source_tracking_list
        return found_entry, found_issue_number, source_tracking_list

    def _bridge_sync_try_ado_issue_by_search(
        self,
        search: _AdoIssueSearchInput,
    ) -> tuple[dict[str, Any] | None, str | int | None, list[dict[str, Any]]]:
        proposal = search.proposal
        change_id = search.change_id
        adapter_type = search.adapter_type
        adapter = search.adapter
        ado_org = search.ado_org
        ado_project = search.ado_project
        source_tracking_list = search.source_tracking_list
        target_entry = search.target_entry
        issue_number = search.issue_number
        if (
            target_entry
            or adapter_type.lower() != "ado"
            or not ado_org
            or not ado_project
            or not hasattr(adapter, "_find_work_item_by_change_id")
        ):
            return target_entry, issue_number, source_tracking_list
        found_ado: dict[str, Any] | None = cast(Any, adapter)._find_work_item_by_change_id(
            change_id, ado_org, ado_project
        )
        if not found_ado:
            return target_entry, issue_number, source_tracking_list
        source_tracking_list.append(found_ado)
        proposal["source_tracking"] = source_tracking_list
        return found_ado, found_ado.get("source_id"), source_tracking_list

    def _bridge_sync_resolve_remote_issue_by_search(
        self,
        resolve: _RemoteIssueResolutionInput,
    ) -> tuple[dict[str, Any] | None, str | int | None, list[dict[str, Any]]]:
        """Attach GitHub/ADO issues discovered by change-id search."""
        proposal = resolve.proposal
        change_id = resolve.change_id
        adapter_type = resolve.adapter_type
        adapter = resolve.adapter
        repo_owner = resolve.repo_owner
        repo_name = resolve.repo_name
        ado_org = resolve.ado_org
        ado_project = resolve.ado_project
        target_repo = resolve.target_repo
        source_tracking_list = resolve.source_tracking_list
        warnings = resolve.warnings
        target_entry = resolve.target_entry
        issue_number = resolve.issue_number
        target_entry, issue_number, source_tracking_list = self._bridge_sync_try_github_issue_by_search(
            _GithubIssueSearchInput(
                proposal,
                change_id,
                adapter_type,
                repo_owner,
                repo_name,
                target_repo,
                source_tracking_list,
                warnings,
                target_entry,
                issue_number,
            )
        )
        return self._bridge_sync_try_ado_issue_by_search(
            _AdoIssueSearchInput(
                proposal,
                change_id,
                adapter_type,
                adapter,
                ado_org,
                ado_project,
                source_tracking_list,
                target_entry,
                issue_number,
            )
        )

    def _bridge_sync_record_created_issue(
        self,
        proposal: dict[str, Any],
        created: _RecordCreatedIssueInput,
    ) -> None:
        """Merge export result into proposal source_tracking for a newly created issue."""
        result = created.result
        adapter_type = created.adapter_type
        ado_org = created.ado_org
        ado_project = created.ado_project
        repo_owner = created.repo_owner
        repo_name = created.repo_name
        target_repo = created.target_repo
        should_sanitize = created.should_sanitize
        source_tracking_list = self._normalize_source_tracking(proposal.get("source_tracking", {}))
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
        proposal["source_tracking"] = self._update_source_tracking_entry(
            source_tracking_list, repo_identifier, new_entry
        )

    def _bridge_sync_import_sanitized_proposal_from_tmp(
        self,
        proposal: dict[str, Any],
        change_id: str,
        tmp_file: Path | None,
        errors: list[str],
        warnings: list[str],
    ) -> dict[str, Any] | None:
        """Load proposal content from sanitized temp file."""
        sanitized_file_path = tmp_file or (Path(tempfile.gettempdir()) / f"specfact-proposal-{change_id}-sanitized.md")
        try:
            if not sanitized_file_path.exists():
                errors.append(f"Sanitized file not found: {sanitized_file_path}. Please run LLM sanitization first.")
                return None
            sanitized_content = sanitized_file_path.read_text(encoding="utf-8")
            proposal_to_export = self._parse_sanitized_proposal(sanitized_content, proposal)
            try:
                original_tmp = Path(tempfile.gettempdir()) / f"specfact-proposal-{change_id}.md"
                if original_tmp.exists():
                    original_tmp.unlink()
                if sanitized_file_path.exists():
                    sanitized_file_path.unlink()
            except Exception as cleanup_error:
                warnings.append(f"Failed to cleanup temporary files: {cleanup_error}")
            return proposal_to_export
        except Exception as e:
            errors.append(f"Failed to import sanitized content for '{change_id}': {e}")
            return None

    def _bridge_sync_clone_and_maybe_sanitize_proposal(
        self,
        proposal: dict[str, Any],
        should_sanitize: bool,
        sanitizer: Any,
    ) -> dict[str, Any]:
        """Copy proposal and optionally run public-repo sanitization on markdown sections."""
        proposal_to_export = proposal.copy()
        if not should_sanitize:
            return proposal_to_export

        original_description = proposal.get("description", "")
        original_rationale = proposal.get("rationale", "")
        combined_markdown = ""
        if original_rationale:
            combined_markdown += f"## Why\n\n{original_rationale}\n\n"
        if original_description:
            combined_markdown += f"## What Changes\n\n{original_description}\n\n"

        if not combined_markdown:
            return proposal_to_export

        sanitized_markdown = sanitizer.sanitize_proposal(combined_markdown)
        why_match = re.search(r"##\s*Why\s*\n\n(.*?)(?=\n##|\Z)", sanitized_markdown, re.DOTALL)
        sanitized_rationale = why_match.group(1).strip() if why_match else ""
        what_match = re.search(r"##\s*What\s+Changes\s*\n\n(.*?)(?=\n##|\Z)", sanitized_markdown, re.DOTALL)
        sanitized_description = what_match.group(1).strip() if what_match else ""
        proposal_to_export["description"] = sanitized_description or original_description
        proposal_to_export["rationale"] = sanitized_rationale or original_rationale
        return proposal_to_export

    def _bridge_sync_make_devops_adapter_kwargs(self, cfg: _DevOpsAdapterKwargsInput) -> dict[str, Any]:
        """Build kwargs for AdapterRegistry.get_adapter for supported DevOps adapters."""
        adapter_type = cfg.adapter_type
        repo_owner = cfg.repo_owner
        repo_name = cfg.repo_name
        api_token = cfg.api_token
        use_gh_cli = cfg.use_gh_cli
        ado_org = cfg.ado_org
        ado_project = cfg.ado_project
        ado_base_url = cfg.ado_base_url
        ado_work_item_type = cfg.ado_work_item_type
        lowered = adapter_type.lower()
        if lowered == "github":
            return {
                "repo_owner": repo_owner,
                "repo_name": repo_name,
                "api_token": api_token,
                "use_gh_cli": use_gh_cli,
            }
        if lowered == "ado":
            return {
                "org": ado_org,
                "project": ado_project,
                "base_url": ado_base_url,
                "api_token": api_token,
                "work_item_type": ado_work_item_type,
            }
        return {}

    def _bridge_sync_apply_change_id_filter(
        self,
        active_proposals: list[dict[str, Any]],
        change_ids: list[str] | None,
        errors: list[str],
    ) -> list[dict[str, Any]]:
        """Restrict proposals to the requested change IDs when provided."""
        if not change_ids:
            return active_proposals
        valid_change_ids = set(change_ids)
        available_change_ids = {p.get("change_id") for p in active_proposals if p.get("change_id")}
        available_change_ids = {cid for cid in available_change_ids if cid is not None}
        invalid_change_ids = valid_change_ids - available_change_ids
        if invalid_change_ids:
            errors.append(
                f"Invalid change IDs: {', '.join(sorted(invalid_change_ids))}. "
                f"Available: {', '.join(sorted(available_change_ids)) if available_change_ids else 'none'}"
            )
        return [p for p in active_proposals if p.get("change_id") in valid_change_ids]

    def _bridge_sync_update_existing_issue_then_save(self, payload: _IssueUpdatePayload) -> None:
        """Run _update_existing_issue and persist proposal (shared by two branches)."""
        assert payload.target_entry is not None and payload.issue_number is not None
        self._update_existing_issue(payload)
        self._save_openspec_change_proposal(payload.proposal)

    def _bridge_sync_if_tracked_update_and_return(self, payload: _IssueUpdatePayload) -> bool:
        if not (payload.issue_number and payload.target_entry):
            return False
        self._bridge_sync_update_existing_issue_then_save(payload)
        return True

    def _bridge_sync_issue_update_payload(
        self,
        proposal: dict[str, Any],
        target_entry: dict[str, Any] | None,
        issue_number: str | int | None,
        tracking: _ExportIterationTracking,
        ctx: _ChangeProposalExportLoopContext,
    ) -> _IssueUpdatePayload:
        return _IssueUpdatePayload(
            proposal=proposal,
            target_entry=target_entry,
            issue_number=issue_number,
            adapter=ctx.adapter,
            adapter_type=ctx.adapter_type,
            target_repo=ctx.target_repo,
            source_tracking_list=tracking.source_tracking_list,
            source_tracking_raw=tracking.source_tracking_raw,
            repo_owner=ctx.repo_owner,
            repo_name=ctx.repo_name,
            ado_org=ctx.ado_org,
            ado_project=ctx.ado_project,
            update_existing=ctx.update_existing,
            import_from_tmp=ctx.import_from_tmp,
            tmp_file=ctx.tmp_file,
            should_sanitize=ctx.should_sanitize,
            track_code_changes=ctx.track_code_changes,
            add_progress_comment=ctx.add_progress_comment,
            code_repo_path=ctx.code_repo_path,
            operations=ctx.operations,
            errors=ctx.errors,
            warnings=ctx.warnings,
        )

    def _bridge_sync_try_export_proposal_to_tmp(
        self,
        export_to_tmp: bool,
        change_id: str,
        tmp_file: Path | None,
        proposal: dict[str, Any],
        errors: list[str],
        warnings: list[str],
    ) -> bool:
        """If export_to_tmp is set, write proposal markdown to a temp path; return True when done."""
        if not export_to_tmp:
            return False
        tmp_file_path = tmp_file or (Path(tempfile.gettempdir()) / f"specfact-proposal-{change_id}.md")
        try:
            proposal_content = self._format_proposal_for_export(proposal)
            tmp_file_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_file_path.write_text(proposal_content, encoding="utf-8")
            warnings.append(f"Exported proposal '{change_id}' to {tmp_file_path} for LLM review")
        except Exception as e:
            errors.append(f"Failed to export proposal '{change_id}' to temporary file: {e}")
        return True

    def _bridge_sync_export_new_change_proposal_remote(
        self,
        proposal: dict[str, Any],
        change_id: str,
        ctx: _ChangeProposalExportLoopContext,
    ) -> None:
        """Import/sanitize proposal payload and create a new remote change proposal artifact."""
        if ctx.import_from_tmp:
            proposal_to_export = self._bridge_sync_import_sanitized_proposal_from_tmp(
                proposal, change_id, ctx.tmp_file, ctx.errors, ctx.warnings
            )
            if proposal_to_export is None:
                return
        else:
            proposal_to_export = self._bridge_sync_clone_and_maybe_sanitize_proposal(
                proposal, bool(ctx.should_sanitize), ctx.sanitizer
            )
        result = ctx.adapter.export_artifact(
            artifact_key="change_proposal",
            artifact_data=proposal_to_export,
            bridge_config=self.bridge_config,
        )
        if isinstance(proposal, dict) and isinstance(result, dict):
            self._bridge_sync_record_created_issue(
                proposal,
                _RecordCreatedIssueInput(
                    result,
                    ctx.adapter_type,
                    ctx.ado_org,
                    ctx.ado_project,
                    ctx.repo_owner,
                    ctx.repo_name,
                    ctx.target_repo,
                    ctx.should_sanitize,
                ),
            )
        ctx.operations.append(
            SyncOperation(
                artifact_key="change_proposal",
                feature_id=proposal.get("change_id", "unknown"),
                direction="export",
                bundle_name="openspec",
            )
        )
        self._save_openspec_change_proposal(proposal)

    def _bridge_sync_export_single_change_proposal_iteration(
        self,
        proposal: dict[str, Any],
        ctx: _ChangeProposalExportLoopContext,
    ) -> None:
        """One loop iteration for export_change_proposals_to_devops."""
        source_tracking_raw = proposal.get("source_tracking", {})
        target_repo = ctx.target_repo
        target_entry = self._find_source_tracking_entry(source_tracking_raw, target_repo)
        source_tracking_list = self._normalize_source_tracking(source_tracking_raw)
        tracking = _ExportIterationTracking(source_tracking_list, source_tracking_raw)

        issue_number = target_entry.get("source_id") if target_entry else None
        work_item_was_deleted = False

        issue_number, work_item_was_deleted, target_entry = self._bridge_sync_verify_ado_tracked_work_item(
            _AdoWorkItemVerifyInput(
                issue_number,
                target_entry,
                ctx.adapter_type,
                ctx.adapter,
                ctx.ado_org,
                ctx.ado_project,
            ),
            proposal,
            ctx.warnings,
        )

        if target_entry and not issue_number and not work_item_was_deleted:
            if ctx.update_existing:
                _, source_tracking_list = self._bridge_sync_clear_corrupted_tracking_entry(
                    proposal, source_tracking_raw, source_tracking_list, target_entry
                )
                tracking = _ExportIterationTracking(source_tracking_list, source_tracking_raw)
                target_entry = None
            else:
                ctx.warnings.append(
                    f"Skipping sync for '{proposal.get('change_id', 'unknown')}': "
                    f"source_tracking entry exists for '{target_repo}' but missing source_id. "
                    f"Use --update-existing to force update or manually fix source_tracking."
                )
                return

        if self._bridge_sync_if_tracked_update_and_return(
            self._bridge_sync_issue_update_payload(proposal, target_entry, issue_number, tracking, ctx)
        ):
            return

        change_id = proposal.get("change_id", "unknown")

        if target_entry and not target_entry.get("source_id") and not work_item_was_deleted:
            ctx.warnings.append(
                f"Skipping sync for '{change_id}': source_tracking entry exists for "
                f"'{target_repo}' but missing source_id. Use --update-existing to force update."
            )
            return

        target_entry, issue_number, source_tracking_list = self._bridge_sync_resolve_remote_issue_by_search(
            _RemoteIssueResolutionInput(
                proposal,
                change_id,
                ctx.adapter_type,
                ctx.adapter,
                ctx.repo_owner,
                ctx.repo_name,
                ctx.ado_org,
                ctx.ado_project,
                target_repo,
                source_tracking_list,
                ctx.warnings,
                target_entry,
                issue_number,
            )
        )
        tracking = _ExportIterationTracking(source_tracking_list, source_tracking_raw)

        if self._bridge_sync_if_tracked_update_and_return(
            self._bridge_sync_issue_update_payload(proposal, target_entry, issue_number, tracking, ctx)
        ):
            return

        if self._bridge_sync_try_export_proposal_to_tmp(
            ctx.export_to_tmp, change_id, ctx.tmp_file, proposal, ctx.errors, ctx.warnings
        ):
            return

        self._bridge_sync_export_new_change_proposal_remote(proposal, change_id, ctx)

    def _bridge_sync_export_each_change_proposal(
        self,
        active_proposals: list[dict[str, Any]],
        ctx: _ChangeProposalExportLoopContext,
    ) -> None:
        """Create or update remote issues for each filtered proposal dict."""
        for proposal in active_proposals:
            try:
                self._bridge_sync_export_single_change_proposal_iteration(proposal, ctx)
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.debug(f"Failed to sync proposal {proposal.get('change_id', 'unknown')}: {e}", exc_info=True)
                ctx.errors.append(f"Failed to sync proposal {proposal.get('change_id', 'unknown')}: {e}")

    def _export_change_proposals_load_list(
        self, include_archived: bool, warnings: list[str]
    ) -> list[dict[str, Any]] | None:
        try:
            return self._read_openspec_change_proposals(include_archived=include_archived)
        except Exception as e:
            warnings.append(f"OpenSpec adapter not available: {e}. Skipping change proposal sync.")
            return None

    def _export_change_proposals_append_filter_warnings(
        self, filtered_count: int, should_sanitize: bool, active_len: int, warnings: list[str]
    ) -> None:
        if filtered_count <= 0:
            return
        if should_sanitize:
            warnings.append(
                f"Filtered out {filtered_count} proposal(s) with non-applied status "
                f"(public repos only sync archived/completed proposals, regardless of source tracking). "
                f"Only {active_len} applied proposal(s) will be synced."
            )
            return
        warnings.append(
            f"Filtered out {filtered_count} proposal(s) without source tracking entry for target repo "
            f"and inactive status. Only {active_len} proposal(s) will be synced."
        )

    @beartype
    @require(_bridge_config_set, "Bridge config must be set")
    @require(
        lambda adapter_type: isinstance(adapter_type, str) and adapter_type in ("github", "ado", "linear", "jira"),
        "Adapter must be DevOps type",
    )
    @ensure(lambda result: isinstance(result, SyncResult), "Must return SyncResult")
    def export_change_proposals_to_devops(
        self,
        adapter_type: str,
        options: ExportChangeProposalsOptions | None = None,
    ) -> SyncResult:
        """
        Export OpenSpec change proposals to DevOps tools (export-only mode).

        Pass fields via :class:`ExportChangeProposalsOptions` (defaults apply when ``options`` is omitted).
        """
        from specfact_cli.adapters.registry import AdapterRegistry
        from specfact_cli.utils.content_sanitizer import ContentSanitizer

        opt = options or ExportChangeProposalsOptions()
        repo_owner = opt.repo_owner
        repo_name = opt.repo_name
        api_token = opt.api_token
        use_gh_cli = opt.use_gh_cli
        sanitize = opt.sanitize
        target_repo = opt.target_repo
        change_ids = opt.change_ids
        export_to_tmp = opt.export_to_tmp
        import_from_tmp = opt.import_from_tmp
        tmp_file = opt.tmp_file
        update_existing = opt.update_existing
        track_code_changes = opt.track_code_changes
        add_progress_comment = opt.add_progress_comment
        code_repo_path = opt.code_repo_path
        include_archived = opt.include_archived
        ado_org = opt.ado_org
        ado_project = opt.ado_project
        ado_base_url = opt.ado_base_url
        ado_work_item_type = opt.ado_work_item_type

        operations: list[SyncOperation] = []
        errors: list[str] = []
        warnings: list[str] = []

        try:
            adapter_class = AdapterRegistry._adapters.get(adapter_type.lower())
            if not adapter_class:
                errors.append(f"Adapter '{adapter_type}' not found in registry")
                return SyncResult(success=False, operations=[], errors=errors, warnings=warnings)

            adapter_kwargs = self._bridge_sync_make_devops_adapter_kwargs(
                _DevOpsAdapterKwargsInput(
                    adapter_type,
                    repo_owner,
                    repo_name,
                    api_token,
                    use_gh_cli,
                    ado_org,
                    ado_project,
                    ado_base_url,
                    ado_work_item_type,
                )
            )
            adapter = AdapterRegistry.get_adapter(adapter_type, **adapter_kwargs)

            change_proposals = self._export_change_proposals_load_list(include_archived, warnings)
            if change_proposals is None:
                return SyncResult(success=True, operations=operations, errors=errors, warnings=warnings)

            sanitizer = ContentSanitizer()
            planning_repo = self._bridge_sync_effective_planning_repo()
            should_sanitize = sanitizer.detect_sanitization_need(
                code_repo=self.repo_path,
                planning_repo=planning_repo,
                user_preference=sanitize,
            )

            derived_target_repo = target_repo
            if not derived_target_repo:
                if adapter_type == "ado" and ado_org and ado_project:
                    derived_target_repo = f"{ado_org}/{ado_project}"
                elif repo_owner and repo_name:
                    derived_target_repo = f"{repo_owner}/{repo_name}"

            active_proposals, filtered_count = self._bridge_sync_filter_devops_proposals(
                change_proposals, should_sanitize, derived_target_repo
            )
            self._export_change_proposals_append_filter_warnings(
                filtered_count, should_sanitize, len(active_proposals), warnings
            )
            active_proposals = self._bridge_sync_apply_change_id_filter(active_proposals, change_ids, errors)

            loop_ctx = _ChangeProposalExportLoopContext(
                adapter=adapter,
                adapter_type=adapter_type,
                target_repo=derived_target_repo,
                repo_owner=repo_owner,
                repo_name=repo_name,
                ado_org=ado_org,
                ado_project=ado_project,
                update_existing=update_existing,
                import_from_tmp=import_from_tmp,
                export_to_tmp=export_to_tmp,
                tmp_file=tmp_file,
                should_sanitize=should_sanitize,
                sanitizer=sanitizer,
                track_code_changes=track_code_changes,
                add_progress_comment=add_progress_comment,
                code_repo_path=code_repo_path,
                operations=operations,
                errors=errors,
                warnings=warnings,
            )
            self._bridge_sync_export_each_change_proposal(active_proposals, loop_ctx)

        except Exception as e:
            errors.append(f"Export to DevOps failed: {e}")

        return SyncResult(
            success=len(errors) == 0,
            operations=operations,
            errors=errors,
            warnings=warnings,
        )

    def _parse_openspec_proposal_markdown(self, proposal_content: str) -> tuple[str, str, str, str]:
        """Parse title, rationale, description, and impact from proposal.md body."""
        return bridge_sync_parse_openspec_proposal_markdown(proposal_content)

    def _append_archived_openspec_proposals(self, openspec_changes_dir: Path, proposals: list[dict[str, Any]]) -> None:
        """Append proposals from openspec/changes/archive into the given list."""
        archive_dir = openspec_changes_dir / "archive"
        if not archive_dir.exists() or not archive_dir.is_dir():
            return
        for archive_subdir in archive_dir.iterdir():
            if not archive_subdir.is_dir():
                continue
            archive_name = archive_subdir.name
            if "-" in archive_name:
                parts = archive_name.split("-", 3)
                change_id = parts[3] if len(parts) >= 4 else archive_subdir.name
            else:
                change_id = archive_name
            proposal_file = archive_subdir / "proposal.md"
            if not proposal_file.exists():
                continue
            proposal = self._proposal_dict_from_openspec_file(proposal_file, change_id, "applied", archived=True)
            if proposal:
                proposals.append(proposal)

    def _enrich_source_tracking_entry_repo(self, entry: dict[str, Any]) -> None:
        if entry.get("source_repo"):
            return
        source_url = entry.get("source_url", "")
        if not source_url:
            return
        url_repo_match = re.search(r"github\.com/([^/]+/[^/]+)/", source_url)
        if url_repo_match:
            entry["source_repo"] = url_repo_match.group(1)
            return
        try:
            parsed = urlparse(source_url)
            parsed_hostname: str | None = cast(str | None, parsed.hostname)
            if parsed_hostname and parsed_hostname.lower() == "dev.azure.com":
                pass
        except ValueError:
            pass

    def _collect_source_tracking_entries_from_proposal_text(self, proposal_content: str) -> list[dict[str, Any]]:
        """Parse Source Tracking section into entry dicts (shared by active and archived reads)."""
        source_tracking_list: list[dict[str, Any]] = []
        if "## Source Tracking" not in proposal_content:
            return source_tracking_list

        source_tracking_match = re.search(r"## Source Tracking\s*\n(.*?)(?=\n## |\Z)", proposal_content, re.DOTALL)
        if not source_tracking_match:
            return source_tracking_list

        tracking_content = source_tracking_match.group(1)
        repo_sections = re.split(r"###\s+Repository:\s*([^\n]+)\s*\n", tracking_content)

        if len(repo_sections) > 1:
            for i in range(1, len(repo_sections), 2):
                if i + 1 < len(repo_sections):
                    repo_name = repo_sections[i].strip()
                    entry_content = repo_sections[i + 1]
                    entry = self._parse_source_tracking_entry(entry_content, repo_name)
                    if entry:
                        source_tracking_list.append(entry)
        else:
            entry = self._parse_source_tracking_entry(tracking_content, None)
            if entry:
                self._enrich_source_tracking_entry_repo(entry)
                source_tracking_list.append(entry)

        return source_tracking_list

    def _proposal_dict_from_openspec_file(
        self,
        proposal_file: Path,
        change_id: str,
        status: str,
        *,
        archived: bool = False,
    ) -> dict[str, Any] | None:
        """Load and parse a single proposal.md into a proposal dict."""
        import logging

        logger = logging.getLogger(__name__)
        try:
            proposal_content = proposal_file.read_text(encoding="utf-8")
            title, rationale, description, impact = self._parse_openspec_proposal_markdown(proposal_content)
            source_tracking_list = self._collect_source_tracking_entries_from_proposal_text(proposal_content)

            description_clean = self._dedupe_duplicate_sections(description.strip()) if description else ""
            impact_clean = impact.strip() if impact else ""
            rationale_clean = rationale.strip() if rationale else ""

            source_tracking_final: list[dict[str, Any]] | dict[str, Any] = (
                (source_tracking_list[0] if len(source_tracking_list) == 1 else source_tracking_list)
                if source_tracking_list
                else {}
            )

            return {
                "change_id": change_id,
                "title": title or change_id,
                "description": description_clean or "No description provided.",
                "rationale": rationale_clean or "No rationale provided.",
                "impact": impact_clean,
                "status": status,
                "source_tracking": source_tracking_final,
            }
        except Exception as e:
            kind = "archived proposal" if archived else "proposal"
            logger.warning("Failed to parse %s from %s: %s", kind, proposal_file, e)
            return None

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
        openspec_changes_dir = self._get_openspec_changes_dir()
        if not openspec_changes_dir or not openspec_changes_dir.exists():
            return proposals

        for change_dir in openspec_changes_dir.iterdir():
            if not change_dir.is_dir() or change_dir.name == "archive":
                continue
            proposal_file = change_dir / "proposal.md"
            if not proposal_file.exists():
                continue
            proposal = self._proposal_dict_from_openspec_file(proposal_file, change_dir.name, "proposed")
            if proposal:
                proposals.append(proposal)

        if include_archived:
            self._append_archived_openspec_proposals(openspec_changes_dir, proposals)

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
        entries = [source_tracking] if isinstance(source_tracking, dict) else source_tracking or []
        for raw_entry in entries:
            if isinstance(raw_entry, dict) and self._source_tracking_entry_matches_repo(raw_entry, target_repo):
                return raw_entry
        return source_tracking if isinstance(source_tracking, dict) and not target_repo else None

    def _source_tracking_entry_matches_repo(self, entry: dict[str, Any], target_repo: str | None) -> bool:
        """Return whether a source-tracking entry matches the requested repository."""
        if not target_repo:
            return True

        entry_repo = entry.get("source_repo")
        entry_type = str(entry.get("source_type", "")).lower()
        source_url = str(entry.get("source_url", ""))
        if entry_repo == target_repo:
            return True
        if not entry_repo and self._source_url_matches_target_repo(source_url, target_repo, entry_type):
            return True
        return self._ado_repo_matches_target(entry_repo, target_repo, entry_type, source_url, entry.get("source_id"))

    def _source_url_matches_target_repo(self, source_url: str, target_repo: str, entry_type: str) -> bool:
        """Match GitHub and ADO source URLs back to a target repository identifier."""
        if not source_url:
            return False

        url_repo_match = re.search(r"github\.com/([^/]+/[^/]+)/", source_url)
        if url_repo_match:
            return url_repo_match.group(1) == target_repo

        if "/" not in target_repo:
            return False

        try:
            parsed = urlparse(source_url)
            hostname = cast(str | None, parsed.hostname)
            if not hostname or hostname.lower() != "dev.azure.com":
                return False
            ado_org_match = re.search(r"dev\.azure\.com/([^/]+)/", source_url)
            return bool(
                ado_org_match and ado_org_match.group(1) == target_repo.split("/")[0] and entry_type in {"ado", ""}
            )
        except Exception:
            return False

    def _ado_repo_matches_target(
        self,
        entry_repo: Any,
        target_repo: str,
        entry_type: str,
        source_url: str,
        source_id: Any,
    ) -> bool:
        """Handle fallback matching for ADO entries whose URLs may contain GUIDs instead of project names."""
        if not entry_repo or entry_type != "ado" or "/" not in target_repo or not source_id:
            return False

        entry_repo_str = str(entry_repo)
        entry_org = entry_repo_str.split("/")[0] if "/" in entry_repo_str else None
        target_org = target_repo.split("/")[0]
        entry_project = entry_repo_str.split("/", 1)[1] if "/" in entry_repo_str else None
        target_project = target_repo.split("/", 1)[1] if "/" in target_repo else None
        entry_has_guid = bool(
            source_url and re.search(r"dev\.azure\.com/[^/]+/[0-9a-f-]{36}", source_url, re.IGNORECASE)
        )
        project_unknown = self._ado_project_identifier_unknown(entry_project, target_project, entry_has_guid)
        return bool(entry_org and entry_org == target_org and project_unknown)

    def _ado_project_identifier_unknown(
        self,
        entry_project: str | None,
        target_project: str | None,
        entry_has_guid: bool,
    ) -> bool:
        """Return whether an ADO project identifier is too ambiguous to compare directly."""
        if not entry_project or not target_project or entry_has_guid:
            return True
        return self._looks_like_guid(entry_project) or self._looks_like_guid(target_project)

    @staticmethod
    def _looks_like_guid(value: str | None) -> bool:
        """Return whether the value resembles a GUID-style identifier."""
        return bool(value and len(value) == 36 and "-" in value)

    @staticmethod
    def _artifact_key_for_adapter(adapter_type: str) -> str | None:
        """Return the backlog import artifact key for a supported adapter."""
        return {"github": "github_issue", "ado": "ado_work_item"}.get(adapter_type)

    @staticmethod
    def _clean_backlog_item_ref(item_ref: str) -> tuple[str, str]:
        """Return the raw backlog reference and its trailing identifier."""
        item_ref_str = str(item_ref)
        return item_ref_str, item_ref_str.split("/")[-1]

    def _proposal_matches_backlog_item(self, proposal: Any, item_ref_str: str, item_ref_clean: str) -> bool:
        """Return whether a proposal contains source tracking for the requested backlog item."""
        if not proposal.source_tracking:
            return False
        source_metadata_raw = proposal.source_tracking.source_metadata
        if not isinstance(source_metadata_raw, dict):
            return False
        backlog_entries = cast(dict[str, Any], source_metadata_raw).get("backlog_entries") or []
        for entry in backlog_entries:
            if not isinstance(entry, dict):
                continue
            ed = cast(dict[str, Any], entry)
            entry_id = ed.get("source_id")
            if not entry_id:
                continue
            entry_id_str = str(entry_id)
            if entry_id_str in (item_ref_str, item_ref_clean) or item_ref_str.endswith(
                (f"/{entry_id_str}", f"#{entry_id_str}")
            ):
                return True
        return False

    def _fallback_imported_proposal(self, project_bundle: Any, adapter_type: str) -> Any | None:
        """Return the most recently imported proposal as a fallback for backlog import."""
        proposal_list = list(project_bundle.change_tracking.proposals.values())
        if not proposal_list:
            return None
        imported_proposal = proposal_list[-1]
        if not imported_proposal.source_tracking:
            return imported_proposal
        source_tool = imported_proposal.source_tracking.tool
        if source_tool != adapter_type:
            logger = logging.getLogger(__name__)
            logger.debug(
                "Fallback proposal has different source tool (%s vs %s), but using it anyway as it's the most recent proposal",
                source_tool,
                adapter_type,
            )
        return imported_proposal

    def _find_imported_proposal_for_item(self, project_bundle: Any, item_ref: str, adapter_type: str) -> Any | None:
        """Find the proposal imported for a backlog item by ID match or recency fallback."""
        logger = logging.getLogger(__name__)
        item_ref_str, item_ref_clean = self._clean_backlog_item_ref(item_ref)
        logger.debug("Looking for proposal matching backlog item '%s' (clean: '%s')", item_ref, item_ref_clean)

        for proposal in project_bundle.change_tracking.proposals.values():
            if self._proposal_matches_backlog_item(proposal, item_ref_str, item_ref_clean):
                logger.debug("Found proposal '%s' by source_id match", proposal.name)
                return proposal

        return self._fallback_imported_proposal(project_bundle, adapter_type)

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
        artifact_key = self._artifact_key_for_adapter(adapter_type)
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
                item_data = cast(Any, adapter).fetch_backlog_item(item_ref)
                adapter.import_artifact(artifact_key, item_data, project_bundle, bridge_config)

                # Get the imported proposal from bundle to create OpenSpec files
                if hasattr(project_bundle, "change_tracking") and project_bundle.change_tracking:
                    imported_proposal = self._find_imported_proposal_for_item(project_bundle, item_ref, adapter_type)

                    # Create OpenSpec files from proposal
                    if imported_proposal:
                        file_warnings = self._write_openspec_change_from_proposal(imported_proposal, bridge_config)
                        warnings.extend(file_warnings)
                    else:
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

    def _bridge_sync_target_repo_for_backlog_adapter(self, adapter: Any, adapter_type: str) -> str | None:
        """Derive owner/repo or org/project string for backlog export matching."""
        if adapter_type == "github":
            repo_owner = getattr(adapter, "repo_owner", None)
            repo_name = getattr(adapter, "repo_name", None)
            if repo_owner and repo_name:
                return f"{repo_owner}/{repo_name}"
            return None
        if adapter_type == "ado":
            org = getattr(adapter, "org", None)
            project = getattr(adapter, "project", None)
            if org and project:
                return f"{org}/{project}"
        return None

    def _bridge_sync_resolve_bundle_target_entry(
        self,
        entries: list[dict[str, Any]],
        adapter_type: str,
        target_repo: str | None,
    ) -> dict[str, Any] | None:
        if target_repo:
            match = next(
                (e for e in entries if isinstance(e, dict) and e.get("source_repo") == target_repo),
                None,
            )
            if match:
                return match
        return next(
            (e for e in entries if isinstance(e, dict) and e.get("source_type") == adapter_type and e.get("source_id")),
            None,
        )

    def _bridge_sync_build_bundle_proposal_dict(
        self,
        proposal: Any,
        adapter_type: str,
        entries: list[dict[str, Any]],
    ) -> dict[str, Any]:
        proposal_dict: dict[str, Any] = {
            "change_id": proposal.name,
            "title": proposal.title,
            "description": proposal.description,
            "rationale": proposal.rationale,
            "status": proposal.status,
            "source_tracking": entries,
        }
        source_state = None
        source_type = None
        for entry in entries:
            if isinstance(entry, dict):
                ent = cast(dict[str, Any], entry)
                entry_type = str(ent.get("source_type", "")).lower()
                if entry_type and entry_type != adapter_type.lower():
                    sm_raw = ent.get("source_metadata", {})
                    sm = cast(dict[str, Any], sm_raw) if isinstance(sm_raw, dict) else {}
                    entry_source_state = sm.get("source_state")
                    if entry_source_state:
                        source_state = entry_source_state
                        source_type = entry_type
                        break
        if source_state and source_type:
            proposal_dict["source_state"] = source_state
            proposal_dict["source_type"] = source_type
        if isinstance(proposal.source_tracking.source_metadata, dict):
            meta = cast(dict[str, Any], proposal.source_tracking.source_metadata)
            raw_title = meta.get("raw_title")
            raw_body = meta.get("raw_body")
            if raw_title:
                proposal_dict["raw_title"] = raw_title
            if raw_body:
                proposal_dict["raw_body"] = raw_body
        return proposal_dict

    def _bridge_sync_run_bundle_adapter_export(self, export_bundle: _BundleAdapterExportInput) -> None:
        proposal = export_bundle.proposal
        proposal_dict = export_bundle.proposal_dict
        target_entry = export_bundle.target_entry
        adapter = export_bundle.adapter
        adapter_type = export_bundle.adapter_type
        bridge_config = export_bundle.bridge_config
        bundle_name = export_bundle.bundle_name
        target_repo = export_bundle.target_repo
        update_existing = export_bundle.update_existing
        entries = export_bundle.entries
        operations = export_bundle.operations
        errors = export_bundle.errors
        try:
            export_result: dict[str, Any] | Any = {}
            if target_entry and target_entry.get("source_id"):
                sm0 = target_entry.get("source_metadata")
                last_synced = cast(dict[str, Any], sm0).get("last_synced_status") if isinstance(sm0, dict) else None
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
            if isinstance(export_result, dict):
                entry_update = self._build_backlog_entry_from_result(
                    adapter_type,
                    target_repo,
                    export_result,
                    proposal.status,
                )
                if entry_update and isinstance(proposal.source_tracking.source_metadata, dict):
                    entries = self._upsert_backlog_entry(entries, entry_update)
                    sm_up = cast(dict[str, Any], proposal.source_tracking.source_metadata)
                    sm_up["backlog_entries"] = entries
        except Exception as e:
            errors.append(f"Failed to export '{proposal.name}' to {adapter_type}: {e}")

    def _bridge_sync_export_one_bundle_proposal(self, bundle_export: _BundleSingleExportInput) -> None:
        """Export a single ChangeProposal from a bundle to the backlog adapter."""
        from specfact_cli.models.source_tracking import SourceTracking

        proposal = bundle_export.proposal
        adapter = bundle_export.adapter
        adapter_type = bundle_export.adapter_type
        bridge_config = bundle_export.bridge_config
        bundle_name = bundle_export.bundle_name
        target_repo = bundle_export.target_repo
        update_existing = bundle_export.update_existing
        operations = bundle_export.operations
        errors = bundle_export.errors
        if proposal.source_tracking is None:
            proposal.source_tracking = SourceTracking(tool=adapter_type, source_metadata={})

        entries = self._get_backlog_entries(proposal)
        if isinstance(proposal.source_tracking.source_metadata, dict):
            sm_e = cast(dict[str, Any], proposal.source_tracking.source_metadata)
            sm_e["backlog_entries"] = entries
        target_entry = self._bridge_sync_resolve_bundle_target_entry(entries, adapter_type, target_repo)
        proposal_dict = self._bridge_sync_build_bundle_proposal_dict(proposal, adapter_type, entries)
        self._bridge_sync_run_bundle_adapter_export(
            _BundleAdapterExportInput(
                proposal,
                proposal_dict,
                target_entry,
                adapter,
                adapter_type,
                bridge_config,
                bundle_name,
                target_repo,
                update_existing,
                entries,
                operations,
                errors,
            )
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

        target_repo = self._bridge_sync_target_repo_for_backlog_adapter(adapter, adapter_type)

        for proposal in change_tracking.proposals.values():
            if change_ids and proposal.name not in change_ids:
                continue
            self._bridge_sync_export_one_bundle_proposal(
                _BundleSingleExportInput(
                    proposal,
                    adapter,
                    adapter_type,
                    bridge_config,
                    bundle_name,
                    target_repo,
                    update_existing,
                    operations,
                    errors,
                )
            )

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

    def _backlog_entries_from_metadata_fallback(
        self, source_metadata: dict[str, Any], proposal: Any
    ) -> list[dict[str, Any]]:
        fallback_id = source_metadata.get("source_id")
        fallback_url = source_metadata.get("source_url")
        fallback_repo = source_metadata.get("source_repo", "")
        fallback_type = source_metadata.get("source_type") or getattr(proposal.source_tracking, "tool", None)
        if not (fallback_id or fallback_url):
            return []
        return [
            {
                "source_id": str(fallback_id) if fallback_id is not None else None,
                "source_url": fallback_url or "",
                "source_type": fallback_type or "",
                "source_repo": fallback_repo,
                "source_metadata": {},
            }
        ]

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
        raw_source_metadata = proposal.source_tracking.source_metadata
        if not isinstance(raw_source_metadata, dict):
            return []
        source_metadata: dict[str, Any] = cast(dict[str, Any], raw_source_metadata)
        entries = source_metadata.get("backlog_entries")
        if isinstance(entries, list):
            return [entry for entry in entries if isinstance(entry, dict)]

        return self._backlog_entries_from_metadata_fallback(source_metadata, proposal)

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
        verify: _WorkItemVerifyInput,
        proposal: dict[str, Any],
        warnings: list[str],
    ) -> tuple[str | int | None, bool]:
        """Verify if work item/issue exists in external tool (handles deleted items)."""
        issue_number = verify.issue_number
        target_entry = verify.target_entry
        adapter_type = verify.adapter_type
        adapter = verify.adapter
        ado_org = verify.ado_org
        ado_project = verify.ado_project
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
            adapter_instance_any = cast(Any, adapter_instance)
            if adapter_instance and hasattr(adapter_instance, "api_token") and adapter_instance_any.api_token:
                # Search for issues containing the change proposal ID in the footer
                search_url = f"{adapter_instance_any.base_url}/search/issues"
                search_query = f'repo:{repo_owner}/{repo_name} "OpenSpec Change Proposal: `{change_id}`" in:body'
                headers: dict[str, str | bytes] = {
                    "Authorization": f"token {adapter_instance_any.api_token}",
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

    def _update_existing_issue(self, payload: _IssueUpdatePayload) -> None:
        """Update existing issue/work item with new status, metadata, and content."""
        proposal = payload.proposal
        target_entry = payload.target_entry
        issue_number = payload.issue_number
        adapter = payload.adapter
        adapter_type = payload.adapter_type
        target_repo = payload.target_repo
        source_tracking_list = payload.source_tracking_list
        source_tracking_raw = payload.source_tracking_raw
        repo_owner = payload.repo_owner
        repo_name = payload.repo_name
        ado_org = payload.ado_org
        ado_project = payload.ado_project
        update_existing = payload.update_existing
        import_from_tmp = payload.import_from_tmp
        tmp_file = payload.tmp_file
        should_sanitize = payload.should_sanitize
        track_code_changes = payload.track_code_changes
        add_progress_comment = payload.add_progress_comment
        code_repo_path = payload.code_repo_path
        operations = payload.operations
        errors = payload.errors
        warnings = payload.warnings
        assert target_entry is not None and issue_number is not None
        # Issue exists - check if status changed or metadata needs update
        source_metadata = self._source_metadata_dict(target_entry)
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
        updated_entry = self._updated_target_entry(target_entry, current_status, should_sanitize)

        # Always update source_tracking metadata to reflect current sync operation
        source_tracking_list = self._store_updated_source_tracking(
            proposal,
            source_tracking_raw,
            source_tracking_list,
            target_repo,
            updated_entry,
        )

        target_entry = updated_entry

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
                _IssueContentUpdateInput(
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
            )

        # Code change tracking and progress comments (when enabled)
        if track_code_changes or add_progress_comment:
            self._handle_code_change_tracking(
                _CodeChangeTrackingInput(
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
            )

    def _proposal_update_hash(self, proposal: dict[str, Any], import_from_tmp: bool, tmp_file: Path | None) -> str:
        """Calculate the proposal hash, optionally using sanitized temporary content."""
        if not import_from_tmp:
            return self._calculate_content_hash(proposal)

        change_id = proposal.get("change_id", "unknown")
        sanitized_file = tmp_file or (Path(tempfile.gettempdir()) / f"specfact-proposal-{change_id}-sanitized.md")
        if not sanitized_file.exists():
            return self._calculate_content_hash(proposal)

        sanitized_content = sanitized_file.read_text(encoding="utf-8")
        return self._calculate_content_hash({"rationale": "", "description": sanitized_content})

    def _proposal_update_payload(
        self,
        proposal: dict[str, Any],
        import_from_tmp: bool,
        tmp_file: Path | None,
    ) -> dict[str, Any]:
        """Build the proposal payload used for backlog update operations."""
        if not import_from_tmp:
            return proposal

        change_id = proposal.get("change_id", "unknown")
        sanitized_file = tmp_file or (Path(tempfile.gettempdir()) / f"specfact-proposal-{change_id}-sanitized.md")
        if not sanitized_file.exists():
            return proposal

        sanitized_content = sanitized_file.read_text(encoding="utf-8")
        return {**proposal, "description": sanitized_content, "rationale": ""}

    def _fetch_issue_sync_state(self, fetch: _FetchIssueSyncStateInput) -> tuple[bool, bool, bool]:
        """Return title/state update flags and whether an applied comment is needed."""
        from specfact_cli.adapters.registry import AdapterRegistry

        adapter_type = fetch.adapter_type
        issue_num = fetch.issue_num
        repo_owner = fetch.repo_owner
        repo_name = fetch.repo_name
        ado_org = fetch.ado_org
        ado_project = fetch.ado_project
        proposal_title = fetch.proposal_title
        proposal_status = fetch.proposal_status
        adapter_instance = AdapterRegistry.get_adapter(adapter_type)
        adapter_inst_any = cast(Any, adapter_instance)
        if not adapter_instance or not hasattr(adapter_instance, "api_token"):
            return False, False, False

        if adapter_type.lower() == "github" and repo_owner and repo_name and adapter_inst_any.api_token:
            return self._fetch_github_issue_sync_state(
                adapter_inst_any,
                issue_num,
                repo_owner,
                repo_name,
                proposal_title,
                proposal_status,
            )

        if (
            adapter_type.lower() == "ado"
            and hasattr(adapter_instance, "_get_work_item_data")
            and ado_org
            and ado_project
        ):
            return self._fetch_ado_issue_sync_state(
                adapter_inst_any,
                issue_num,
                ado_org,
                ado_project,
                proposal_title,
                proposal_status,
            )

        return False, False, False

    def _fetch_github_issue_sync_state(
        self,
        adapter_inst_any: Any,
        issue_num: str | int,
        repo_owner: str,
        repo_name: str,
        proposal_title: str,
        proposal_status: str,
    ) -> tuple[bool, bool, bool]:
        """Return title/state update flags for a GitHub issue."""
        import requests

        url = f"{adapter_inst_any.base_url}/repos/{repo_owner}/{repo_name}/issues/{issue_num}"
        headers: dict[str, str | bytes] = {
            "Authorization": f"token {adapter_inst_any.api_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        issue_data = response.json()
        current_issue_title = issue_data.get("title", "")
        current_issue_state = issue_data.get("state", "open")
        desired_state = "closed" if proposal_status in ("applied", "deprecated", "discarded") else "open"
        needs_comment_for_applied = proposal_status == "applied" and current_issue_state == "closed"
        return (
            bool(current_issue_title and proposal_title and current_issue_title != proposal_title),
            current_issue_state != desired_state,
            needs_comment_for_applied,
        )

    def _fetch_ado_issue_sync_state(
        self,
        adapter_inst_any: Any,
        issue_num: str | int,
        ado_org: str,
        ado_project: str,
        proposal_title: str,
        proposal_status: str,
    ) -> tuple[bool, bool, bool]:
        """Return title/state update flags for an ADO work item."""
        work_item_data: dict[str, Any] | None = adapter_inst_any._get_work_item_data(issue_num, ado_org, ado_project)
        if not work_item_data:
            return False, False, False
        current_issue_title = work_item_data.get("title", "")
        current_issue_state = work_item_data.get("state", "")
        desired_ado_state: str = adapter_inst_any.map_openspec_status_to_backlog(proposal_status)
        return (
            bool(current_issue_title and proposal_title and current_issue_title != proposal_title),
            current_issue_state != desired_ado_state,
            False,
        )

    @staticmethod
    def _source_metadata_dict(entry: dict[str, Any]) -> dict[str, Any]:
        """Return a normalized source_metadata mapping."""
        source_metadata = entry.get("source_metadata", {})
        return cast(dict[str, Any], source_metadata) if isinstance(source_metadata, dict) else {}

    def _updated_target_entry(
        self,
        target_entry: dict[str, Any],
        current_status: Any,
        should_sanitize: bool | None,
    ) -> dict[str, Any]:
        """Build the updated source-tracking entry for the current sync."""
        source_metadata = self._source_metadata_dict(target_entry)
        return {
            **target_entry,
            "source_metadata": {
                **source_metadata,
                "last_synced_status": current_status,
                "sanitized": should_sanitize if should_sanitize is not None else False,
            },
        }

    def _store_updated_source_tracking(
        self,
        proposal: dict[str, Any],
        source_tracking_raw: dict[str, Any] | list[dict[str, Any]],
        source_tracking_list: list[dict[str, Any]],
        target_repo: str | None,
        updated_entry: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Persist an updated source-tracking entry back to the proposal payload."""
        if target_repo:
            updated_list = self._update_source_tracking_entry(source_tracking_list, target_repo, updated_entry)
            proposal["source_tracking"] = updated_list
            return updated_list

        if isinstance(source_tracking_raw, dict):
            proposal["source_tracking"] = updated_entry
            return source_tracking_list

        for index, entry in enumerate(source_tracking_list):
            if not isinstance(entry, dict):
                continue
            entry_id = entry.get("source_id")
            entry_repo = entry.get("source_repo")
            updated_id = updated_entry.get("source_id")
            updated_repo = updated_entry.get("source_repo")
            if (entry_id and entry_id == updated_id) or (entry_repo and entry_repo == updated_repo):
                source_tracking_list[index] = updated_entry
                break
        proposal["source_tracking"] = source_tracking_list
        return source_tracking_list

    def _update_issue_content_hash(
        self,
        proposal: dict[str, Any],
        target_entry: dict[str, Any],
        target_repo: str | None,
        source_tracking_list: list[dict[str, Any]],
        current_hash: str,
    ) -> None:
        """Persist the latest content hash in source-tracking metadata."""
        source_metadata = target_entry.get("source_metadata", {})
        if not isinstance(source_metadata, dict):
            source_metadata = {}
        updated_entry = {**target_entry, "source_metadata": {**source_metadata, "content_hash": current_hash}}
        if target_repo:
            proposal["source_tracking"] = self._update_source_tracking_entry(
                source_tracking_list, target_repo, updated_entry
            )

    def _push_issue_body_update_to_adapter(self, push: _PushIssueBodyInput) -> None:
        proposal = push.proposal
        target_entry = push.target_entry
        adapter = push.adapter
        import_from_tmp = push.import_from_tmp
        tmp_file = push.tmp_file
        repo_owner = push.repo_owner
        repo_name = push.repo_name
        target_repo = push.target_repo
        source_tracking_list = push.source_tracking_list
        current_hash = push.current_hash
        content_or_meta_changed = push.content_or_meta_changed
        needs_comment_for_applied = push.needs_comment_for_applied
        operations = push.operations
        errors = push.errors
        try:
            proposal_for_update = self._proposal_update_payload(proposal, import_from_tmp, tmp_file)
            code_repo_path = self._find_code_repo_path(repo_owner, repo_name) if repo_owner and repo_name else None
            proposal_with_repo = {
                **proposal_for_update,
                "_code_repo_path": str(code_repo_path) if code_repo_path else None,
            }
            comment_only = needs_comment_for_applied and not content_or_meta_changed
            adapter.export_artifact(
                artifact_key="change_proposal_comment" if comment_only else "change_proposal_update",
                artifact_data=proposal_with_repo,
                bridge_config=self.bridge_config,
            )

            if target_entry:
                self._update_issue_content_hash(proposal, target_entry, target_repo, source_tracking_list, current_hash)

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

    def _update_issue_content_if_needed(self, refresh: _IssueContentUpdateInput) -> None:
        """Update issue/work item content if hash changed or title needs update."""
        proposal = refresh.proposal
        target_entry = refresh.target_entry
        adapter = refresh.adapter
        adapter_type = refresh.adapter_type
        target_repo = refresh.target_repo
        source_tracking_list = refresh.source_tracking_list
        repo_owner = refresh.repo_owner
        repo_name = refresh.repo_name
        ado_org = refresh.ado_org
        ado_project = refresh.ado_project
        import_from_tmp = refresh.import_from_tmp
        tmp_file = refresh.tmp_file
        operations = refresh.operations
        errors = refresh.errors
        current_hash = self._proposal_update_hash(proposal, import_from_tmp, tmp_file)

        # Get stored hash from target repository entry
        stored_hash = None
        _sm_hash = target_entry.get("source_metadata")
        if isinstance(_sm_hash, dict):
            stored_hash = cast(dict[str, Any], _sm_hash).get("content_hash")

        needs_title_update = False
        needs_state_update = False
        needs_comment_for_applied = False
        issue_num = target_entry.get("source_id") if target_entry else None
        if issue_num:
            with contextlib.suppress(Exception):
                needs_title_update, needs_state_update, needs_comment_for_applied = self._fetch_issue_sync_state(
                    _FetchIssueSyncStateInput(
                        adapter_type,
                        issue_num,
                        repo_owner,
                        repo_name,
                        ado_org,
                        ado_project,
                        str(proposal.get("title", "")),
                        str(proposal.get("status", "proposed")),
                    )
                )

        content_or_meta_changed = stored_hash != current_hash or needs_title_update or needs_state_update
        if content_or_meta_changed or needs_comment_for_applied:
            self._push_issue_body_update_to_adapter(
                _PushIssueBodyInput(
                    proposal,
                    target_entry,
                    adapter,
                    import_from_tmp,
                    tmp_file,
                    repo_owner,
                    repo_name,
                    target_repo,
                    source_tracking_list,
                    current_hash,
                    content_or_meta_changed,
                    needs_comment_for_applied,
                    operations,
                    errors,
                )
            )

    def _bridge_sync_list_progress_comment_dicts(self, target_entry: dict[str, Any] | None) -> list[dict[str, Any]]:
        if not target_entry:
            return []
        sm_raw = target_entry.get("source_metadata")
        if not isinstance(sm_raw, dict):
            return []
        pc_raw = cast(dict[str, Any], sm_raw).get("progress_comments")
        if not isinstance(pc_raw, list):
            return []
        return [c for c in pc_raw if isinstance(c, dict)]

    def _bridge_sync_resolve_progress_data(
        self,
        *,
        track_code_changes: bool,
        add_progress_comment: bool,
        change_id: str,
        target_entry: dict[str, Any] | None,
        code_repo_path: Path | None,
        errors: list[str],
    ) -> dict[str, Any] | None:
        from datetime import datetime

        from specfact_cli.utils.code_change_detector import detect_code_changes

        if track_code_changes:
            try:
                last_detection = None
                if target_entry:
                    sm = target_entry.get("source_metadata")
                    if isinstance(sm, dict):
                        last_detection = cast(dict[str, Any], sm).get("last_code_change_detected")
                code_repo = code_repo_path if code_repo_path else self.repo_path
                code_changes = detect_code_changes(
                    repo_path=code_repo,
                    change_id=change_id,
                    since_timestamp=last_detection,
                )
                if code_changes.get("has_changes"):
                    return code_changes
                return None
            except Exception as e:
                errors.append(f"Failed to detect code changes for {change_id}: {e}")
                return None
        if add_progress_comment:
            return {
                "summary": "Manual progress update",
                "detection_timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            }
        return None

    def _bridge_sync_emit_code_change_progress(self, emit: _EmitCodeChangeProgressInput) -> None:
        from specfact_cli.utils.code_change_detector import calculate_comment_hash, format_progress_comment

        proposal = emit.proposal
        change_id = emit.change_id
        target_entry = emit.target_entry
        target_repo = emit.target_repo
        source_tracking_list = emit.source_tracking_list
        progress_data = emit.progress_data
        adapter = emit.adapter
        should_sanitize = emit.should_sanitize
        operations = emit.operations
        errors = emit.errors
        warnings = emit.warnings
        sanitize_flag = should_sanitize if should_sanitize is not None else False
        comment_text = format_progress_comment(progress_data, sanitize=sanitize_flag)
        comment_hash = calculate_comment_hash(comment_text)
        progress_comments = self._bridge_sync_list_progress_comment_dicts(target_entry)
        if any(c.get("comment_hash") == comment_hash for c in progress_comments):
            warnings.append(f"Skipped duplicate progress comment for {change_id}")
            return
        try:
            proposal_with_progress = {
                **proposal,
                "source_tracking": source_tracking_list,
                "progress_data": progress_data,
                "sanitize": sanitize_flag,
            }
            adapter.export_artifact(
                artifact_key="code_change_progress",
                artifact_data=proposal_with_progress,
                bridge_config=self.bridge_config,
            )
            if target_entry:
                sm_raw2 = target_entry.get("source_metadata")
                source_metadata2: dict[str, Any] = cast(dict[str, Any], sm_raw2) if isinstance(sm_raw2, dict) else {}
                pc_raw2 = source_metadata2.get("progress_comments")
                merged_comments: list[dict[str, Any]] = (
                    [c for c in pc_raw2 if isinstance(c, dict)] if isinstance(pc_raw2, list) else []
                )
                merged_comments.append(
                    {
                        "comment_hash": comment_hash,
                        "timestamp": progress_data.get("detection_timestamp"),
                        "summary": progress_data.get("summary", ""),
                    }
                )
                updated_entry = {
                    **target_entry,
                    "source_metadata": {
                        **source_metadata2,
                        "progress_comments": merged_comments,
                        "last_code_change_detected": progress_data.get("detection_timestamp"),
                    },
                }
                if target_repo:
                    new_list = self._update_source_tracking_entry(source_tracking_list, target_repo, updated_entry)
                    proposal["source_tracking"] = new_list
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

    def _handle_code_change_tracking(self, tracking: _CodeChangeTrackingInput) -> None:
        """Handle code change tracking and add progress comments if enabled."""
        proposal = tracking.proposal
        target_entry = tracking.target_entry
        target_repo = tracking.target_repo
        source_tracking_list = tracking.source_tracking_list
        adapter = tracking.adapter
        track_code_changes = tracking.track_code_changes
        add_progress_comment = tracking.add_progress_comment
        code_repo_path = tracking.code_repo_path
        should_sanitize = tracking.should_sanitize
        operations = tracking.operations
        errors = tracking.errors
        warnings = tracking.warnings
        change_id = proposal.get("change_id", "unknown")
        progress_data = self._bridge_sync_resolve_progress_data(
            track_code_changes=track_code_changes,
            add_progress_comment=add_progress_comment,
            change_id=change_id,
            target_entry=target_entry,
            code_repo_path=code_repo_path,
            errors=errors,
        )
        if not progress_data:
            return
        self._bridge_sync_emit_code_change_progress(
            _EmitCodeChangeProgressInput(
                proposal,
                change_id,
                target_entry,
                target_repo,
                source_tracking_list,
                progress_data,
                adapter,
                should_sanitize,
                operations,
                errors,
                warnings,
            )
        )

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

        for i, entry in enumerate(source_tracking_list):
            if not isinstance(entry, dict):
                continue
            if self._source_tracking_entries_match(entry, entry_data, target_repo):
                updated_entry = {**entry, **entry_data}
                if self._ado_repo_matches_target(
                    entry.get("source_repo"),
                    target_repo,
                    str(entry_data.get("source_type", "")).lower(),
                    str(entry.get("source_url", "")),
                    entry.get("source_id") or entry_data.get("source_id"),
                ):
                    updated_entry["source_repo"] = target_repo
                source_tracking_list[i] = updated_entry
                return source_tracking_list

        # No existing entry found - add new one
        source_tracking_list.append(entry_data)
        return source_tracking_list

    def _source_tracking_entries_match(
        self,
        existing_entry: dict[str, Any],
        new_entry: dict[str, Any],
        target_repo: str,
    ) -> bool:
        """Return whether two source-tracking entries refer to the same repository item."""
        existing_repo = existing_entry.get("source_repo")
        existing_id = existing_entry.get("source_id")
        new_id = new_entry.get("source_id")
        if existing_repo == target_repo:
            return True
        return bool(
            self._ado_repo_matches_target(
                existing_repo,
                target_repo,
                str(new_entry.get("source_type", existing_entry.get("source_type", ""))).lower(),
                str(existing_entry.get("source_url", "")),
                existing_id or new_id,
            )
            and (not existing_id or not new_id or existing_id == new_id)
        )

    def _entry_source_metadata(self, entry: dict[str, Any]) -> dict[str, Any]:
        """Return a mutable source_metadata dict for a tracking entry."""
        source_metadata = entry.get("source_metadata")
        if not isinstance(source_metadata, dict):
            source_metadata = {}
            entry["source_metadata"] = source_metadata
        return cast(dict[str, Any], source_metadata)

    def _populate_source_repo_from_url(self, entry: dict[str, Any], source_url: str) -> None:
        """Infer a repository identifier from a source URL when metadata omitted it."""
        url_repo_match = re.search(r"github\.com/([^/]+/[^/]+)/", source_url)
        if url_repo_match:
            entry["source_repo"] = url_repo_match.group(1)
            return

        ado_repo_match = re.search(r"dev\.azure\.com/([^/]+)/([^/]+)/", source_url)
        if ado_repo_match:
            entry["source_repo"] = f"{ado_repo_match.group(1)}/{ado_repo_match.group(2)}"

    def _apply_source_tracking_metadata(self, entry: dict[str, Any], entry_content: str) -> None:
        """Extract source-tracking metadata comments and fields from markdown content."""
        metadata_patterns: list[tuple[str, str, Any]] = [
            (r"\*\*Last Synced Status\*\*:\s*(\w+)", "last_synced_status", lambda value: str(value)),
            (r"\*\*Sanitized\*\*:\s*(true|false)", "sanitized", lambda value: str(value).lower() == "true"),
            (r"<!--\s*content_hash:\s*([a-f0-9]{16})\s*-->", "content_hash", lambda value: str(value)),
            (
                r"<!--\s*last_code_change_detected:\s*([^\s]+)\s*-->",
                "last_code_change_detected",
                lambda value: str(value),
            ),
        ]
        source_metadata = self._entry_source_metadata(entry)
        for pattern, key, converter in metadata_patterns:
            match = re.search(pattern, entry_content, re.IGNORECASE)
            if match:
                source_metadata[key] = converter(match.group(1))

        progress_comments_match = re.search(r"<!--\s*progress_comments:\s*(\[.*?\])\s*-->", entry_content, re.DOTALL)
        if progress_comments_match:
            with contextlib.suppress(json.JSONDecodeError, ValueError):
                source_metadata["progress_comments"] = json.loads(progress_comments_match.group(1))

    def _apply_source_repo_override(self, entry: dict[str, Any], entry_content: str) -> None:
        """Load hidden source_repo metadata when explicit repository headers are absent."""
        source_repo_match = re.search(r"<!--\s*source_repo:\s*([^>]+?)\s*-->", entry_content)
        if source_repo_match:
            entry["source_repo"] = source_repo_match.group(1).strip()
            return

        if not entry.get("source_repo"):
            source_repo_in_content = re.search(r"source_repo[:\s]+([^\n]+)", entry_content, re.IGNORECASE)
            if source_repo_in_content:
                entry["source_repo"] = source_repo_in_content.group(1).strip()

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
            if not repo_name:
                self._populate_source_repo_from_url(entry, entry["source_url"])

        # Extract source type
        type_match = re.search(r"\*\*(\w+)\s+Issue\*\*:", entry_content)
        if type_match:
            entry["source_type"] = type_match.group(1).lower()

        self._apply_source_tracking_metadata(entry, entry_content)
        self._apply_source_repo_override(entry, entry_content)

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

    def _find_proposal_file(self, openspec_changes_dir: Path, change_id: str) -> Path | None:
        """Locate the proposal.md path for an active or archived OpenSpec change."""
        proposal_file = openspec_changes_dir / change_id / "proposal.md"
        if proposal_file.exists():
            return proposal_file

        archive_dir = openspec_changes_dir / "archive"
        if not archive_dir.exists() or not archive_dir.is_dir():
            return None

        for archive_subdir in archive_dir.iterdir():
            if not archive_subdir.is_dir() or "-" not in archive_subdir.name:
                continue
            parts = archive_subdir.name.split("-", 3)
            if len(parts) >= 4 and parts[3] == change_id:
                candidate = archive_subdir / "proposal.md"
                if candidate.exists():
                    return candidate
        return None

    def _source_type_display_name(self, source_type_raw: Any) -> str:
        """Return the markdown display name for a source type."""
        source_type_capitalization = {
            "github": "GitHub",
            "ado": "ADO",
            "linear": "Linear",
            "jira": "Jira",
            "unknown": "Unknown",
        }
        return source_type_capitalization.get(str(source_type_raw).lower(), "Unknown")

    def _append_source_metadata_tracking_lines(self, lines: list[str], source_metadata: dict[str, Any]) -> None:
        last_synced_status = source_metadata.get("last_synced_status")
        if last_synced_status:
            lines.append(f"- **Last Synced Status**: {last_synced_status}")
        sanitized = source_metadata.get("sanitized")
        if sanitized is not None:
            lines.append(f"- **Sanitized**: {str(sanitized).lower()}")
        content_hash = source_metadata.get("content_hash")
        if content_hash:
            lines.append(f"<!-- content_hash: {content_hash} -->")
        progress_comments = source_metadata.get("progress_comments")
        if isinstance(progress_comments, list) and progress_comments:
            lines.append(f"<!-- progress_comments: {json.dumps(progress_comments, separators=(',', ':'))} -->")
        last_detection = source_metadata.get("last_code_change_detected")
        if last_detection:
            lines.append(f"<!-- last_code_change_detected: {last_detection} -->")

    def _build_source_tracking_entry_lines(
        self,
        entry: dict[str, Any],
        index: int,
        total_entries: int,
    ) -> list[str]:
        """Build markdown lines for a single source-tracking entry."""
        lines: list[str] = []
        source_repo = entry.get("source_repo")
        if source_repo:
            if total_entries > 1 or index > 0:
                lines.extend([f"### Repository: {source_repo}", ""])
            elif total_entries == 1:
                lines.append(f"<!-- source_repo: {source_repo} -->")

        source_id = entry.get("source_id")
        source_url = entry.get("source_url")
        if source_id:
            lines.append(
                f"- **{self._source_type_display_name(entry.get('source_type', 'unknown'))} Issue**: #{source_id}"
            )
        if source_url:
            lines.append(f"- **Issue URL**: <{source_url}>")

        sm_in = entry.get("source_metadata")
        if isinstance(sm_in, dict):
            self._append_source_metadata_tracking_lines(lines, cast(dict[str, Any], sm_in))
        return lines

    def _build_source_tracking_metadata_section(self, source_tracking_list: list[dict[str, Any]]) -> str:
        """Build the markdown source-tracking section for a proposal file."""
        metadata_lines: list[str] = ["", "---", "", "## Source Tracking", ""]
        for index, entry in enumerate(source_tracking_list):
            if not isinstance(entry, dict):
                continue
            metadata_lines.extend(self._build_source_tracking_entry_lines(entry, index, len(source_tracking_list)))
            if index < len(source_tracking_list) - 1:
                metadata_lines.extend(["", "---", ""])
        metadata_lines.append("")
        return "\n".join(metadata_lines)

    def _replace_markdown_section(self, content: str, section_name: str, section_body: str) -> str:
        """Replace or append a markdown section while preserving surrounding content."""
        if not section_body:
            return content

        section_header = f"## {section_name}"
        replacement = f"{section_header}\n\n{section_body}\n"
        section_pattern = (
            rf"(##\s+{re.escape(section_name)}\s*\n)(.*?)(?=\n##\s+|\n---\s*\n\s*##\s+Source\s+Tracking|\Z)"
        )
        if re.search(section_pattern, content, flags=re.DOTALL | re.IGNORECASE):
            return re.sub(section_pattern, replacement, content, flags=re.DOTALL | re.IGNORECASE)

        insert_before = re.search(r"(##\s+(What Changes|Source Tracking))", content, re.IGNORECASE)
        if section_name == "Why" and insert_before:
            insert_pos = insert_before.start()
            return content[:insert_pos] + replacement + "\n" + content[insert_pos:]

        if section_name == "What Changes":
            insert_after_why = re.search(r"(##\s+Why\s*\n.*?\n)(?=##\s+|$)", content, re.DOTALL | re.IGNORECASE)
            if insert_after_why:
                insert_pos = insert_after_why.end()
                return content[:insert_pos] + replacement + "\n" + content[insert_pos:]

        if "## Source Tracking" in content:
            return content.replace("## Source Tracking", replacement + "\n## Source Tracking", 1)
        return f"{content.rstrip()}\n\n{replacement}"

    def _upsert_source_tracking_section(self, content: str, metadata_section: str) -> str:
        """Replace or append the source-tracking metadata block."""
        pattern_with_sep = r"\n---\n\n## Source Tracking.*?(?=\n## |\Z)"
        if re.search(pattern_with_sep, content, flags=re.DOTALL):
            return re.sub(pattern_with_sep, "\n" + metadata_section.rstrip(), content, flags=re.DOTALL)

        pattern_no_sep = r"\n## Source Tracking.*?(?=\n## |\Z)"
        if re.search(pattern_no_sep, content, flags=re.DOTALL):
            return re.sub(pattern_no_sep, "\n" + metadata_section.rstrip(), content, flags=re.DOTALL)

        return content.rstrip() + "\n" + metadata_section

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

        openspec_changes_dir = self._get_openspec_changes_dir()
        if not openspec_changes_dir or not openspec_changes_dir.exists():
            return  # Cannot save without OpenSpec directory

        proposal_file = self._find_proposal_file(openspec_changes_dir, str(change_id))
        if not proposal_file or not proposal_file.exists():
            return  # Proposal file doesn't exist

        try:
            # Read existing content
            content = proposal_file.read_text(encoding="utf-8")
            content = self._proposal_content_with_source_tracking(content, proposal)
            if not content:
                return

            # Write back to file
            proposal_file.write_text(content, encoding="utf-8")

        except Exception as e:
            # Log error but don't fail the sync
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to save source tracking to {proposal_file}: {e}")

    def _proposal_content_with_source_tracking(self, content: str, proposal: dict[str, Any]) -> str | None:
        """Return updated proposal markdown including proposal fields and source tracking."""
        source_tracking_raw = proposal.get("source_tracking", {})
        source_tracking_list = self._normalize_source_tracking(source_tracking_raw)
        if not source_tracking_list:
            return None

        metadata_section = self._build_source_tracking_metadata_section(source_tracking_list)
        content = self._apply_proposal_title(content, proposal.get("title"))
        content = self._apply_proposal_sections(content, proposal.get("rationale", ""), proposal.get("description", ""))
        return self._upsert_source_tracking_section(content, metadata_section)

    def _apply_proposal_title(self, content: str, title: Any) -> str:
        """Replace or insert the proposal title in markdown content."""
        if not title:
            return content
        title_pattern = r"^#\s+Change:\s*.*$"
        if re.search(title_pattern, content, re.MULTILINE):
            return re.sub(title_pattern, f"# Change: {title}", content, flags=re.MULTILINE)
        return f"# Change: {title}\n\n{content}"

    def _apply_proposal_sections(self, content: str, rationale: str, description: str) -> str:
        """Keep Why and What Changes sections in sync with proposal data."""
        if rationale:
            content = self._replace_markdown_section(content, "Why", rationale.strip())
        if description:
            description_clean = self._dedupe_duplicate_sections(description.strip())
            content = self._replace_markdown_section(content, "What Changes", description_clean)
        return content

    def _format_proposal_for_export(self, proposal: dict[str, Any]) -> str:
        """
        Format proposal as markdown for export to temporary file.

        Args:
            proposal: Change proposal dict

        Returns:
            Markdown-formatted proposal content
        """
        lines: list[str] = []
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
        """Extract requirement text from proposal content."""
        return bridge_sync_extract_requirement_from_proposal(proposal, spec_id, self._format_proposal_title)

    def _generate_tasks_from_proposal(self, proposal: Any) -> str:
        """Generate tasks.md content from proposal."""
        return bridge_sync_generate_tasks_from_proposal(
            proposal,
            format_proposal_title=self._format_proposal_title,
            format_what_changes_section=self._format_what_changes_section,
            extract_what_changes_content=self._extract_what_changes_content,
        )

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
        """Format \"What Changes\" with NEW/EXTEND/MODIFY markers (delegates to helper module)."""
        return bridge_sync_format_what_changes_section(description)

    def _line_ends_what_changes_extraction(self, stripped: str, end_section_keywords: tuple[str, ...]) -> bool:
        if not (stripped.startswith("##") or (stripped.startswith("-") and "##" in stripped)):
            return False
        section_title = re.sub(r"^-\s*#+\s*|^#+\s*", "", stripped).strip().lower()
        if any(keyword in section_title for keyword in end_section_keywords):
            return True
        return bool(
            stripped.startswith(("##", "- ##"))
            and not stripped.startswith(("###", "- ###"))
            and section_title not in ("what changes", "why")
        )

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

        end_section_keywords = (
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
        )

        lines = description.split("\n")
        what_changes_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            if self._line_ends_what_changes_extraction(stripped, end_section_keywords):
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
            cleaned_lines: list[str] = []
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
        """Write OpenSpec change files from imported ChangeProposal."""
        return bridge_sync_write_openspec_change_from_proposal(
            self,
            proposal,
            bridge_config,
            template_id=template_id,
            refinement_confidence=refinement_confidence,
        )

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

    def _append_specification_feature_ids(self, artifact: Any, feature_ids: list[str]) -> None:
        pattern_parts = str(artifact.path_pattern).split("/")
        if not pattern_parts:
            return
        base_dir = self.repo_path / pattern_parts[0]
        if not base_dir.exists():
            return
        for item in base_dir.iterdir():
            if not item.is_dir():
                continue
            test_path = self.resolve_artifact_path("specification", item.name, "test")
            if test_path.exists() or (item / "spec.md").exists():
                feature_ids.append(item.name)

    @beartype
    @require(_bridge_config_set, "Bridge config must be set")
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

        if "specification" in self.bridge_config.artifacts:
            self._append_specification_feature_ids(
                self.bridge_config.artifacts["specification"],
                feature_ids,
            )

        return feature_ids
