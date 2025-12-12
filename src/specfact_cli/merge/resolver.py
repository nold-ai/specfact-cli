"""
Persona-aware merge conflict resolver for project bundles.

This module implements three-way merge resolution with persona ownership rules,
enabling automatic conflict resolution based on section ownership.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.project import BundleManifest, ProjectBundle


class MergeStrategy(str, Enum):
    """Merge resolution strategy."""

    AUTO = "auto"  # Automatic resolution based on persona ownership
    OURS = "ours"  # Prefer our version
    THEIRS = "theirs"  # Prefer their version
    BASE = "base"  # Keep base version
    MANUAL = "manual"  # Manual resolution required


@dataclass
class MergeConflict:
    """Represents a merge conflict in a project bundle."""

    section_path: str
    field_name: str
    base_value: Any
    ours_value: Any
    theirs_value: Any
    owner_ours: str | None = None
    owner_theirs: str | None = None
    resolution: MergeStrategy | None = None
    resolved_value: Any | None = None


@dataclass
class MergeResolution:
    """Result of a merge operation."""

    merged_bundle: ProjectBundle
    conflicts: list[MergeConflict]
    auto_resolved: int = 0
    manual_resolved: int = 0
    unresolved: int = 0


class PersonaMergeResolver:
    """Three-way merge resolver with persona-aware conflict resolution."""

    @beartype
    @require(lambda base: isinstance(base, ProjectBundle), "Base must be ProjectBundle")
    @require(lambda ours: isinstance(ours, ProjectBundle), "Ours must be ProjectBundle")
    @require(lambda theirs: isinstance(theirs, ProjectBundle), "Theirs must be ProjectBundle")
    @require(
        lambda persona_ours: isinstance(persona_ours, str) and len(persona_ours) > 0,
        "Persona ours must be non-empty string",
    )
    @require(
        lambda persona_theirs: isinstance(persona_theirs, str) and len(persona_theirs) > 0,
        "Persona theirs must be non-empty string",
    )
    @ensure(lambda result: isinstance(result, MergeResolution), "Must return MergeResolution")
    def resolve(
        self,
        base: ProjectBundle,
        ours: ProjectBundle,
        theirs: ProjectBundle,
        persona_ours: str,
        persona_theirs: str,
    ) -> MergeResolution:
        """
        Resolve merge conflicts using persona ownership rules.

        Args:
            base: Base version (common ancestor)
            ours: Our version (current branch)
            theirs: Their version (incoming branch)
            persona_ours: Persona who made our changes
            persona_theirs: Persona who made their changes

        Returns:
            MergeResolution with merged bundle and conflict details
        """

        # Start with base bundle
        merged = base.model_copy(deep=True)
        conflicts: list[MergeConflict] = []

        # Use the manifest from base (or merge manifests if needed)
        merged_manifest = base.manifest.model_copy(deep=True)

        # Rule 1: Check for non-overlapping sections (auto-merge)
        if self._sections_disjoint(ours, theirs):
            # No conflicts - merge all changes
            merged = self._merge_sections(base, ours, theirs)
            return MergeResolution(merged_bundle=merged, conflicts=[], auto_resolved=0, manual_resolved=0, unresolved=0)

        # Rule 2: Find conflicts and resolve based on persona ownership
        field_conflicts = self._find_conflicts(base, ours, theirs)

        auto_resolved = 0
        manual_resolved = 0
        unresolved = 0

        for conflict_path, (base_val, ours_val, theirs_val) in field_conflicts.items():
            # Determine section path from conflict path
            section_path = self._get_section_path(conflict_path)

            # Check persona ownership
            owner_ours = self._get_owner(section_path, merged_manifest, persona_ours)
            owner_theirs = self._get_owner(section_path, merged_manifest, persona_theirs)

            conflict = MergeConflict(
                section_path=section_path,
                field_name=conflict_path,
                base_value=base_val,
                ours_value=ours_val,
                theirs_value=theirs_val,
                owner_ours=owner_ours,
                owner_theirs=owner_theirs,
            )

            # Resolve based on ownership
            if owner_ours == persona_ours and owner_theirs != persona_theirs:
                # Our persona owns this section
                conflict.resolution = MergeStrategy.OURS
                conflict.resolved_value = ours_val
                self._apply_resolution(merged, conflict_path, ours_val)
                auto_resolved += 1
            elif owner_theirs == persona_theirs and owner_ours != persona_ours:
                # Their persona owns this section
                conflict.resolution = MergeStrategy.THEIRS
                conflict.resolved_value = theirs_val
                self._apply_resolution(merged, conflict_path, theirs_val)
                auto_resolved += 1
            elif owner_ours == persona_ours and owner_theirs == persona_theirs:
                # Both personas own it - prefer ours if same persona, otherwise manual
                if persona_ours == persona_theirs:
                    conflict.resolution = MergeStrategy.OURS
                    conflict.resolved_value = ours_val
                    self._apply_resolution(merged, conflict_path, ours_val)
                    auto_resolved += 1
                else:
                    # Different personas both own it - manual resolution required
                    conflict.resolution = MergeStrategy.MANUAL
                    unresolved += 1
            else:
                # No clear owner - manual resolution required
                conflict.resolution = MergeStrategy.MANUAL
                unresolved += 1

            conflicts.append(conflict)

        return MergeResolution(
            merged_bundle=merged,
            conflicts=conflicts,
            auto_resolved=auto_resolved,
            manual_resolved=manual_resolved,
            unresolved=unresolved,
        )

    @beartype
    @require(lambda ours: isinstance(ours, ProjectBundle), "Ours must be ProjectBundle")
    @require(lambda theirs: isinstance(theirs, ProjectBundle), "Theirs must be ProjectBundle")
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def _sections_disjoint(self, ours: ProjectBundle, theirs: ProjectBundle) -> bool:
        """
        Check if sections modified in ours and theirs are disjoint.

        Args:
            ours: Our version
            theirs: Their version

        Returns:
            True if sections are disjoint (no conflicts possible)
        """
        # Simple heuristic: if bundles are identical except for different features,
        # sections are likely disjoint
        # This is a simplified check - full implementation would compare field-by-field
        return False  # Conservative: always check for conflicts

    @beartype
    @require(lambda base: isinstance(base, ProjectBundle), "Base must be ProjectBundle")
    @require(lambda ours: isinstance(ours, ProjectBundle), "Ours must be ProjectBundle")
    @require(lambda theirs: isinstance(theirs, ProjectBundle), "Theirs must be ProjectBundle")
    @ensure(lambda result: isinstance(result, ProjectBundle), "Must return ProjectBundle")
    def _merge_sections(self, base: ProjectBundle, ours: ProjectBundle, theirs: ProjectBundle) -> ProjectBundle:
        """
        Merge non-conflicting sections from ours and theirs into base.

        Args:
            base: Base version
            ours: Our version
            theirs: Their version

        Returns:
            Merged ProjectBundle
        """
        merged = base.model_copy(deep=True)

        # Merge features (combine from both)
        for key, feature in ours.features.items():
            if key not in merged.features:
                merged.features[key] = feature.model_copy(deep=True)
            else:
                # Merge feature fields (prefer ours for conflicts in non-disjoint case)
                merged.features[key] = feature.model_copy(deep=True)

        for key, feature in theirs.features.items():
            if key not in merged.features:
                merged.features[key] = feature.model_copy(deep=True)

        # Merge other sections (idea, business, product)
        if ours.idea and not merged.idea:
            merged.idea = ours.idea.model_copy(deep=True)
        if theirs.idea and not merged.idea:
            merged.idea = theirs.idea.model_copy(deep=True)

        if ours.business and not merged.business:
            merged.business = ours.business.model_copy(deep=True)
        if theirs.business and not merged.business:
            merged.business = theirs.business.model_copy(deep=True)

        if ours.product:
            merged.product = ours.product.model_copy(deep=True)
        if theirs.product:
            # Merge product fields
            merged.product = theirs.product.model_copy(deep=True)

        return merged

    @beartype
    @require(lambda base: isinstance(base, ProjectBundle), "Base must be ProjectBundle")
    @require(lambda ours: isinstance(ours, ProjectBundle), "Ours must be ProjectBundle")
    @require(lambda theirs: isinstance(theirs, ProjectBundle), "Theirs must be ProjectBundle")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def _find_conflicts(
        self, base: ProjectBundle, ours: ProjectBundle, theirs: ProjectBundle
    ) -> dict[str, tuple[Any, Any, Any]]:
        """
        Find conflicts between base, ours, and theirs.

        Args:
            base: Base version
            ours: Our version
            theirs: Their version

        Returns:
            Dictionary mapping field paths to (base_value, ours_value, theirs_value) tuples
        """
        conflicts: dict[str, tuple[Any, Any, Any]] = {}

        # Compare features
        all_feature_keys = set(base.features.keys()) | set(ours.features.keys()) | set(theirs.features.keys())

        for key in all_feature_keys:
            base_feature = base.features.get(key)
            ours_feature = ours.features.get(key)
            theirs_feature = theirs.features.get(key)

            if (
                base_feature
                and ours_feature
                and theirs_feature
                and base_feature.title != ours_feature.title
                and base_feature.title != theirs_feature.title
                and ours_feature.title != theirs_feature.title
            ):
                conflicts[f"features.{key}.title"] = (base_feature.title, ours_feature.title, theirs_feature.title)

                # Compare stories
                base_story_keys = {s.key for s in (base_feature.stories or [])}
                ours_story_keys = {s.key for s in (ours_feature.stories or [])}
                theirs_story_keys = {s.key for s in (theirs_feature.stories or [])}

                # Check for story conflicts (added/modified in both)
                common_stories = (ours_story_keys & theirs_story_keys) - base_story_keys
                for story_key in common_stories:
                    ours_story = next((s for s in (ours_feature.stories or []) if s.key == story_key), None)
                    theirs_story = next((s for s in (theirs_feature.stories or []) if s.key == story_key), None)
                    if ours_story and theirs_story and ours_story.description != theirs_story.description:
                        conflicts[f"features.{key}.stories.{story_key}.description"] = (
                            None,  # New story, no base
                            ours_story.description,
                            theirs_story.description,
                        )

        # Compare idea, business, product
        if (
            base.idea
            and ours.idea
            and theirs.idea
            and base.idea.title != ours.idea.title
            and base.idea.title != theirs.idea.title
            and ours.idea.title != theirs.idea.title
        ):
            conflicts["idea.title"] = (base.idea.title, ours.idea.title, theirs.idea.title)

        if (
            base.business
            and ours.business
            and theirs.business
            and base.business.value_proposition != ours.business.value_proposition
            and base.business.value_proposition != theirs.business.value_proposition
            and ours.business.value_proposition != theirs.business.value_proposition
        ):
            conflicts["business.value_proposition"] = (
                base.business.value_proposition,
                ours.business.value_proposition,
                theirs.business.value_proposition,
            )

        # Product conflicts - compare themes
        if (
            base.product
            and ours.product
            and theirs.product
            and ours.product.themes != theirs.product.themes
            and (ours.product.themes != base.product.themes or theirs.product.themes != base.product.themes)
            and ours.product.themes != base.product.themes
            and theirs.product.themes != base.product.themes
        ):
            # Only report conflict if both changed differently
            conflicts["product.themes"] = (
                list(base.product.themes),
                list(ours.product.themes),
                list(theirs.product.themes),
            )

        return conflicts

    @beartype
    @require(lambda section_path: isinstance(section_path, str), "Section path must be str")
    @require(lambda manifest: isinstance(manifest, BundleManifest), "Manifest must be BundleManifest")
    @require(lambda persona: isinstance(persona, str) and len(persona) > 0, "Persona must be non-empty string")
    @ensure(lambda result: isinstance(result, str) or result is None, "Must return str or None")
    def _get_owner(self, section_path: str, manifest: BundleManifest, persona: str) -> str | None:
        """
        Get the owner persona for a section path.

        Args:
            section_path: Section path (e.g., "idea", "features.FEATURE-001.stories")
            manifest: Bundle manifest with persona mappings
            persona: Persona to check ownership for

        Returns:
            Persona name if persona owns section, None otherwise
        """
        from specfact_cli.commands.project_cmd import check_persona_ownership

        if check_persona_ownership(persona, manifest, section_path):
            return persona
        return None

    @beartype
    @require(lambda conflict_path: isinstance(conflict_path, str), "Conflict path must be str")
    @ensure(lambda result: isinstance(result, str), "Must return str")
    def _get_section_path(self, conflict_path: str) -> str:
        """
        Extract section path from conflict field path.

        Args:
            conflict_path: Field path (e.g., "features.FEATURE-001.title", "idea.intent")

        Returns:
            Section path (e.g., "features.FEATURE-001", "idea")
        """
        # Extract section from path
        parts = conflict_path.split(".")
        if parts[0] in ("idea", "business", "product", "protocols", "contracts"):
            return parts[0]
        if parts[0] == "features" and len(parts) > 1:
            # features.FEATURE-001.title -> features.FEATURE-001
            # features.FEATURE-001.stories.STORY-001 -> features.FEATURE-001.stories
            if len(parts) > 2 and parts[2] == "stories":
                return f"features.{parts[1]}.stories"
            return f"features.{parts[1]}"
        return conflict_path

    @beartype
    @require(lambda bundle: isinstance(bundle, ProjectBundle), "Bundle must be ProjectBundle")
    @require(lambda path: isinstance(path, str), "Path must be str")
    def _apply_resolution(self, bundle: ProjectBundle, path: str, value: Any) -> None:
        """
        Apply resolution to a field in the bundle.

        Args:
            bundle: Bundle to modify
            path: Field path (e.g., "features.FEATURE-001.title")
            value: Value to set
        """
        parts = path.split(".")

        if parts[0] == "idea" and bundle.idea:
            if len(parts) > 1 and parts[1] == "title":
                bundle.idea.title = value
        elif parts[0] == "business" and bundle.business:
            if len(parts) > 1 and parts[1] == "value_proposition":
                bundle.business.value_proposition = value
        elif (
            parts[0] == "product"
            and bundle.product
            and len(parts) > 1
            and parts[1] == "themes"
            and isinstance(value, list)
        ):
            bundle.product.themes = value
        elif parts[0] == "features" and len(parts) > 1:
            feature_key = parts[1]
            if feature_key in bundle.features:
                feature = bundle.features[feature_key]
                if len(parts) > 2:
                    if parts[2] == "title":
                        feature.title = value
                    elif parts[2] == "stories" and len(parts) > 3:
                        story_key = parts[3]
                        if feature.stories:
                            story = next((s for s in feature.stories if s.key == story_key), None)
                            if story and len(parts) > 4 and parts[4] == "description":
                                story.description = value
