"""
Change proposal validation integration.

This module provides utilities for integrating OpenSpec change proposals with
SpecFact validation, enabling validation against proposed specifications.

This includes:
- Loading active change proposals from OpenSpec
- Merging current Spec-Kit specs with proposed OpenSpec changes
- Updating validation status in change proposals
- Reporting validation results to backlog (GitHub Issues)
"""

from __future__ import annotations

import re
from contextlib import suppress
from pathlib import Path
from typing import Any

import requests
from beartype import beartype
from icontract import ensure, require

from specfact_cli.adapters.registry import AdapterRegistry
from specfact_cli.models.bridge import BridgeConfig
from specfact_cli.models.change import ChangeProposal, ChangeTracking, FeatureDelta


@beartype
@require(lambda repo_path: repo_path.exists(), "Repository path must exist")
@require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
@ensure(lambda result: result is None or isinstance(result, ChangeTracking), "Must return ChangeTracking or None")
def load_active_change_proposals(repo_path: Path, bridge_config: BridgeConfig | None = None) -> ChangeTracking | None:
    """
    Load active change proposals from OpenSpec repository.

    Loads change proposals with status "proposed" or "in-progress" and their
    associated spec deltas.

    Args:
        repo_path: Path to repository root (may contain OpenSpec)
        bridge_config: Optional bridge configuration (for cross-repo OpenSpec support)

    Returns:
        ChangeTracking instance with active proposals and feature deltas, or None if OpenSpec not found

    Note:
        This function checks bridge_config.external_base_path for cross-repository
        OpenSpec support. If external_base_path is set, it will load from the
        external OpenSpec repository instead of the local one.
    """
    # Detect OpenSpec adapter
    try:
        adapter_instance = AdapterRegistry.get_adapter("openspec")
    except ValueError:
        # Adapter not registered
        return None

    # Check if OpenSpec repository exists
    if not adapter_instance.detect(repo_path, bridge_config):
        return None

    # Try to load change tracking
    # For OpenSpec, bundle_dir is typically .specfact/projects/<bundle>/
    # or openspec/ directory
    openspec_path = repo_path / "openspec"
    if bridge_config and bridge_config.external_base_path:
        openspec_path = bridge_config.external_base_path / "openspec"

    if not openspec_path.exists():
        return None

    # Load change tracking from OpenSpec
    # adapter_instance is already an instance, not a class
    change_tracking = adapter_instance.load_change_tracking(openspec_path, bridge_config)

    if not change_tracking:
        return None

    # Filter to only active proposals (proposed or in-progress)
    active_proposals: dict[str, ChangeProposal] = {}
    active_feature_deltas: dict[str, list[FeatureDelta]] = {}

    for change_name, proposal in change_tracking.proposals.items():
        if proposal.status in ("proposed", "in-progress"):
            active_proposals[change_name] = proposal
            # Include feature deltas for this change
            if change_name in change_tracking.feature_deltas:
                active_feature_deltas[change_name] = change_tracking.feature_deltas[change_name]

    if not active_proposals:
        return None

    # Create filtered change tracking
    return ChangeTracking(proposals=active_proposals, feature_deltas=active_feature_deltas)


@beartype
@require(
    lambda current_specs: isinstance(current_specs, dict), "Current specs must be dict (feature_key -> spec_content)"
)
@require(lambda change_tracking: isinstance(change_tracking, ChangeTracking), "Change tracking must be ChangeTracking")
@ensure(lambda result: isinstance(result, dict), "Must return dict with merged specs")
def merge_specs_with_change_proposals(current_specs: dict[str, Any], change_tracking: ChangeTracking) -> dict[str, Any]:
    """
    Merge current Spec-Kit specs with proposed OpenSpec changes.

    Merges specs according to change proposal deltas:
    - ADDED requirements: Include in validation set
    - MODIFIED requirements: Replace existing with proposed
    - REMOVED requirements: Exclude from validation set

    Args:
        current_specs: Current Spec-Kit specs (feature_key -> spec_content dict)
        change_tracking: ChangeTracking with active proposals and feature deltas

    Returns:
        Dict with merged specs (feature_key -> spec_content)

    Raises:
        ValueError: If conflicts detected (same requirement modified in multiple proposals)

    Note:
        This implements the spec merging mechanism for validation integration.
        Conflicts occur when the same requirement is modified in multiple active proposals.
    """
    merged_specs = current_specs.copy()

    # Track conflicts (same feature modified in multiple proposals)
    modified_features: dict[str, list[str]] = {}  # feature_key -> [change_names]

    # Process feature deltas from all active proposals
    for change_name, feature_deltas in change_tracking.feature_deltas.items():
        for delta in feature_deltas:
            feature_key = delta.feature_key

            if delta.change_type.value == "added":
                # ADDED: Include in validation set
                if delta.proposed_feature:
                    merged_specs[feature_key] = _feature_to_spec_content(delta.proposed_feature)
            elif delta.change_type.value == "modified":
                # MODIFIED: Replace existing with proposed
                if delta.proposed_feature:
                    merged_specs[feature_key] = _feature_to_spec_content(delta.proposed_feature)
                    # Track for conflict detection
                    if feature_key not in modified_features:
                        modified_features[feature_key] = []
                    modified_features[feature_key].append(change_name)
            elif delta.change_type.value == "removed" and feature_key in merged_specs:
                # REMOVED: Exclude from validation set
                del merged_specs[feature_key]

    # Check for conflicts
    conflicts = {feature_key: changes for feature_key, changes in modified_features.items() if len(changes) > 1}
    if conflicts:
        conflict_messages = [
            f"Feature {feature_key} modified in multiple proposals: {', '.join(changes)}"
            for feature_key, changes in conflicts.items()
        ]
        msg = "Spec merging conflicts detected:\n" + "\n".join(conflict_messages)
        raise ValueError(msg)

    return merged_specs


@beartype
@require(lambda feature: feature is not None, "Feature must not be None")
@ensure(lambda result: isinstance(result, dict), "Must return dict with spec content")
def _feature_to_spec_content(feature: Any) -> dict[str, Any]:
    """
    Convert Feature to spec content dict (internal helper).

    Args:
        feature: Feature instance

    Returns:
        Dict with spec content
    """
    # Extract feature data as dict
    if hasattr(feature, "model_dump"):
        return feature.model_dump()
    if hasattr(feature, "dict"):
        return feature.dict()
    if isinstance(feature, dict):
        return feature
    # Fallback: create minimal dict
    return {"key": getattr(feature, "key", "unknown"), "title": getattr(feature, "title", "")}


@beartype
@require(lambda change_tracking: isinstance(change_tracking, ChangeTracking), "Change tracking must be ChangeTracking")
@require(lambda validation_results: isinstance(validation_results, dict), "Validation results must be dict")
@ensure(lambda result: result is None, "Must return None")
def update_validation_status(
    change_tracking: ChangeTracking,
    validation_results: dict[str, Any],
    repo_path: Path,
    bridge_config: BridgeConfig | None = None,
) -> None:
    """
    Update validation status in change proposals after validation.

    Updates validation_status and validation_results in FeatureDelta models
    and saves updated change tracking back to OpenSpec.

    Args:
        change_tracking: ChangeTracking with proposals and feature deltas
        validation_results: Validation results dict (feature_key -> validation_result)
        repo_path: Path to repository root
        bridge_config: Optional bridge configuration (for cross-repo OpenSpec support)

    Note:
        This implements the validation status update mechanism. Validation results
        are stored in FeatureDelta.validation_results and status is updated in
        FeatureDelta.validation_status.
    """
    # Update validation status for each feature delta
    for _change_name, feature_deltas in change_tracking.feature_deltas.items():
        for delta in feature_deltas:
            feature_key = delta.feature_key

            # Get validation result for this feature
            # Check for key presence to handle False and empty dict results correctly
            if feature_key in validation_results:
                feature_result = validation_results[feature_key]
                # Update validation status
                if isinstance(feature_result, dict):
                    success = feature_result.get("success", False)
                    delta.validation_status = "passed" if success else "failed"
                    delta.validation_results = feature_result
                elif isinstance(feature_result, bool):
                    delta.validation_status = "passed" if feature_result else "failed"
                    delta.validation_results = {"success": feature_result}
                else:
                    delta.validation_status = "passed"
                    delta.validation_results = {"result": feature_result}
            else:
                # No validation result for this feature
                delta.validation_status = "pending"
                delta.validation_results = None

    # Save updated change tracking back to OpenSpec
    try:
        adapter_instance = AdapterRegistry.get_adapter("openspec")
    except ValueError:
        # Adapter not registered, skip save
        return

    # Determine OpenSpec path
    openspec_path = repo_path / "openspec"
    if bridge_config and bridge_config.external_base_path:
        openspec_path = bridge_config.external_base_path / "openspec"

    if openspec_path.exists():
        adapter_instance.save_change_tracking(openspec_path, change_tracking, bridge_config)


@beartype
@require(lambda change_tracking: isinstance(change_tracking, ChangeTracking), "Change tracking must be ChangeTracking")
@require(lambda validation_results: isinstance(validation_results, dict), "Validation results must be dict")
@ensure(lambda result: result is None, "Must return None")
def report_validation_results_to_backlog(
    change_tracking: ChangeTracking,
    validation_results: dict[str, Any],
    bridge_config: BridgeConfig | None = None,
) -> None:
    """
    Report validation results to backlog (GitHub Issues, future: ADO, Jira, Linear).

    Updates backlog item comments/notes with validation status and updates
    backlog item status/labels based on validation status.

    Args:
        change_tracking: ChangeTracking with proposals and feature deltas
        validation_results: Validation results dict (feature_key -> validation_result)
        bridge_config: Optional bridge configuration (may contain backlog adapter config)

    Note:
        This implements the validation result reporting pattern. Currently supports
        GitHub Issues; future backlog adapters (ADO, Jira, Linear) should follow
        the same pattern.
    """
    # Get GitHub adapter if configured
    try:
        adapter_instance = AdapterRegistry.get_adapter("github")
    except ValueError:
        # GitHub adapter not registered, skip reporting
        return

    # Check if bridge_config specifies GitHub adapter
    if bridge_config and bridge_config.adapter and bridge_config.adapter.value != "github":
        return  # Not using GitHub adapter

    # Report validation results for each proposal
    for change_name, proposal in change_tracking.proposals.items():
        # Check if proposal has GitHub issue tracking
        source_tracking = proposal.source_tracking
        if not source_tracking:
            continue

        # Extract GitHub issue info from source_tracking
        source_metadata = getattr(source_tracking, "source_metadata", {}) if source_tracking else {}
        issue_number = source_metadata.get("source_id") if isinstance(source_metadata, dict) else None
        source_url = source_metadata.get("source_url", "") if isinstance(source_metadata, dict) else ""

        if not issue_number and source_url:
            # Try to extract issue number from URL
            match = re.search(r"/issues/(\d+)", source_url)
            if match:
                issue_number = match.group(1)  # Keep as string, convert to int when needed

        if not issue_number:
            continue  # No GitHub issue linked

        # Extract repo owner/name from source_url or bridge_config
        repo_owner = None
        repo_name = None

        if source_url:
            # Extract from URL: https://github.com/{owner}/{repo}/issues/{number}
            match = re.search(r"github\.com/([^/]+)/([^/]+)", source_url)
            if match:
                repo_owner = match.group(1)
                repo_name = match.group(2)

        if (not repo_owner or not repo_name) and bridge_config:
            # Try bridge_config
            repo_owner = getattr(bridge_config, "repo_owner", None)
            repo_name = getattr(bridge_config, "repo_name", None)

        if not repo_owner or not repo_name:
            continue  # Cannot determine repository

        # Get validation status for this proposal
        proposal_validation_status = "pending"
        proposal_validation_results = {}

        # Check feature deltas for this proposal
        if change_name in change_tracking.feature_deltas:
            for delta in change_tracking.feature_deltas[change_name]:
                feature_key = delta.feature_key
                # Check for key presence to handle False and empty dict results correctly
                if feature_key in validation_results:
                    feature_result = validation_results[feature_key]
                    if isinstance(feature_result, dict):
                        success = feature_result.get("success", False)
                        if not success:
                            proposal_validation_status = "failed"
                        elif proposal_validation_status == "pending":
                            proposal_validation_status = "passed"
                    elif isinstance(feature_result, bool):
                        if not feature_result:
                            proposal_validation_status = "failed"
                        elif proposal_validation_status == "pending":
                            proposal_validation_status = "passed"

                    proposal_validation_results[feature_key] = feature_result

        # Create validation comment
        comment_parts = [
            "## Validation Results",
            "",
            f"**Status**: {proposal_validation_status.upper()}",
            "",
        ]

        if proposal_validation_results:
            comment_parts.append("**Feature Validation**:")
            for feature_key, result in proposal_validation_results.items():
                success = result.get("success", False) if isinstance(result, dict) else bool(result)
                status_icon = "✅" if success else "❌"
                comment_parts.append(f"- {status_icon} {feature_key}")

        comment_text = "\n".join(comment_parts)

        # Add comment to GitHub issue
        # Convert issue_number to int if it's a string
        try:
            issue_number_int = int(issue_number) if isinstance(issue_number, str) else issue_number
        except (ValueError, TypeError):
            continue  # Invalid issue number

        with suppress(Exception):
            # Log but don't fail - reporting is non-critical
            adapter_instance._add_issue_comment(repo_owner, repo_name, issue_number_int, comment_text)

        # Update issue labels based on validation status
        if proposal_validation_status == "failed":
            # Add "validation-failed" label
            with suppress(Exception):
                # Log but don't fail - label update is non-critical
                # Get current issue
                url = f"{adapter_instance.base_url}/repos/{repo_owner}/{repo_name}/issues/{issue_number_int}"
                headers = {
                    "Authorization": f"token {adapter_instance.api_token}",
                    "Accept": "application/vnd.github.v3+json",
                }
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                current_issue = response.json()

                # Get current labels
                current_labels = [label.get("name", "") for label in current_issue.get("labels", [])]

                # Add validation-failed label if not present
                if "validation-failed" not in current_labels:
                    all_labels = [*current_labels, "validation-failed"]
                    patch_url = f"{adapter_instance.base_url}/repos/{repo_owner}/{repo_name}/issues/{issue_number_int}"
                    patch_payload = {"labels": all_labels}
                    patch_response = requests.patch(patch_url, json=patch_payload, headers=headers, timeout=30)
                    patch_response.raise_for_status()
