"""Plan comparator for detecting deviations between plan bundles."""

from __future__ import annotations

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.deviation import Deviation, DeviationReport, DeviationSeverity, DeviationType
from specfact_cli.models.plan import PlanBundle
from specfact_cli.utils.feature_keys import normalize_feature_key


class PlanComparator:
    """
    Compares two plan bundles to detect deviations.

    Identifies differences between manual (source of truth) and auto-derived
    (reverse-engineered from code) plan bundles.
    """

    @beartype
    @require(lambda manual_plan: isinstance(manual_plan, PlanBundle), "Manual plan must be PlanBundle instance")
    @require(lambda auto_plan: isinstance(auto_plan, PlanBundle), "Auto plan must be PlanBundle instance")
    @require(
        lambda manual_label: isinstance(manual_label, str) and len(manual_label) > 0,
        "Manual label must be non-empty string",
    )
    @require(
        lambda auto_label: isinstance(auto_label, str) and len(auto_label) > 0, "Auto label must be non-empty string"
    )
    @ensure(lambda result: isinstance(result, DeviationReport), "Must return DeviationReport")
    @ensure(lambda result: len(result.manual_plan) > 0, "Manual plan label must be non-empty")
    @ensure(lambda result: len(result.auto_plan) > 0, "Auto plan label must be non-empty")
    def compare(
        self,
        manual_plan: PlanBundle,
        auto_plan: PlanBundle,
        manual_label: str = "manual_plan",
        auto_label: str = "auto_plan",
    ) -> DeviationReport:
        """
        Compare two plan bundles and generate deviation report.

        Args:
            manual_plan: Manually created plan (source of truth)
            auto_plan: Auto-derived plan from code analysis
            manual_label: Label for manual plan (e.g., file path)
            auto_label: Label for auto plan (e.g., file path)

        Returns:
            DeviationReport with all detected deviations
        """
        deviations: list[Deviation] = []

        # Compare ideas
        deviations.extend(self._compare_ideas(manual_plan, auto_plan))

        # Compare business context
        deviations.extend(self._compare_business(manual_plan, auto_plan))

        # Compare product
        deviations.extend(self._compare_product(manual_plan, auto_plan))

        # Compare features
        deviations.extend(self._compare_features(manual_plan, auto_plan))

        # Build summary statistics
        summary: dict[str, int] = {}
        for deviation in deviations:
            deviation_type = deviation.type.value
            summary[deviation_type] = summary.get(deviation_type, 0) + 1

        return DeviationReport(
            manual_plan=manual_label,
            auto_plan=auto_label,
            deviations=deviations,
            summary=summary,
        )

    def _compare_ideas(self, manual: PlanBundle, auto: PlanBundle) -> list[Deviation]:
        """Compare idea sections of two plans."""
        deviations: list[Deviation] = []

        # Check if both have ideas
        if manual.idea is None and auto.idea is None:
            return deviations

        if manual.idea is None and auto.idea is not None:
            deviations.append(
                Deviation(
                    type=DeviationType.EXTRA_IMPLEMENTATION,
                    severity=DeviationSeverity.LOW,
                    description="Auto plan has Idea section but manual plan does not",
                    location="idea",
                    fix_hint="Consider removing auto-derived Idea or adding it to manual plan",
                )
            )
            return deviations

        if manual.idea is not None and auto.idea is None:
            deviations.append(
                Deviation(
                    type=DeviationType.MISSING_FEATURE,
                    severity=DeviationSeverity.MEDIUM,
                    description="Manual plan has Idea section but auto plan does not",
                    location="idea",
                    fix_hint="Add Idea section to auto-derived plan",
                )
            )
            return deviations

        # Both have ideas, compare fields
        if manual.idea is not None and auto.idea is not None:
            if manual.idea.title != auto.idea.title:
                deviations.append(
                    Deviation(
                        type=DeviationType.MISMATCH,
                        severity=DeviationSeverity.LOW,
                        description=f"Idea title differs: manual='{manual.idea.title}', auto='{auto.idea.title}'",
                        location="idea.title",
                        fix_hint="Update auto plan title to match manual plan",
                    )
                )

            if manual.idea.narrative != auto.idea.narrative:
                deviations.append(
                    Deviation(
                        type=DeviationType.MISMATCH,
                        severity=DeviationSeverity.LOW,
                        description="Idea narrative differs between plans",
                        location="idea.narrative",
                        fix_hint="Update narrative to match manual plan",
                    )
                )

        return deviations

    def _compare_business(self, manual: PlanBundle, auto: PlanBundle) -> list[Deviation]:
        """Compare business context sections."""
        deviations: list[Deviation] = []

        if manual.business is not None and auto.business is None:
            deviations.append(
                Deviation(
                    type=DeviationType.MISSING_BUSINESS_CONTEXT,
                    severity=DeviationSeverity.MEDIUM,
                    description="Manual plan has Business context but auto plan does not",
                    location="business",
                    fix_hint="Add business context to auto-derived plan",
                )
            )

        return deviations

    def _compare_product(self, manual: PlanBundle, auto: PlanBundle) -> list[Deviation]:
        """Compare product sections (themes, releases)."""
        deviations: list[Deviation] = []

        # Compare themes
        manual_themes = set(manual.product.themes)
        auto_themes = set(auto.product.themes)

        missing_themes = manual_themes - auto_themes
        extra_themes = auto_themes - manual_themes

        for theme in missing_themes:
            deviations.append(
                Deviation(
                    type=DeviationType.MISMATCH,
                    severity=DeviationSeverity.LOW,
                    description=f"Product theme '{theme}' in manual plan but not in auto plan",
                    location="product.themes",
                    fix_hint=f"Add theme '{theme}' to auto plan",
                )
            )

        for theme in extra_themes:
            deviations.append(
                Deviation(
                    type=DeviationType.MISMATCH,
                    severity=DeviationSeverity.LOW,
                    description=f"Product theme '{theme}' in auto plan but not in manual plan",
                    location="product.themes",
                    fix_hint=f"Remove theme '{theme}' from auto plan or add to manual",
                )
            )

        return deviations

    def _compare_features(self, manual: PlanBundle, auto: PlanBundle) -> list[Deviation]:
        """Compare features between two plans using normalized keys."""
        deviations: list[Deviation] = []

        # Build feature maps by normalized key for comparison
        manual_features_by_norm = {normalize_feature_key(f.key): f for f in manual.features}
        auto_features_by_norm = {normalize_feature_key(f.key): f for f in auto.features}

        # Also build by original key for display
        # manual_features = {f.key: f for f in manual.features}  # Not used yet
        # auto_features = {f.key: f for f in auto.features}  # Not used yet

        # Check for missing features (in manual but not in auto) using normalized keys
        for norm_key in manual_features_by_norm:
            if norm_key not in auto_features_by_norm:
                manual_feature = manual_features_by_norm[norm_key]
                # Higher severity if feature has stories
                severity = DeviationSeverity.HIGH if manual_feature.stories else DeviationSeverity.MEDIUM

                deviations.append(
                    Deviation(
                        type=DeviationType.MISSING_FEATURE,
                        severity=severity,
                        description=f"Feature '{manual_feature.key}' ({manual_feature.title}) in manual plan but not implemented",
                        location=f"features[{manual_feature.key}]",
                        fix_hint=f"Implement feature '{manual_feature.key}' or update manual plan",
                    )
                )

        # Check for extra features (in auto but not in manual) using normalized keys
        for norm_key in auto_features_by_norm:
            if norm_key not in manual_features_by_norm:
                auto_feature = auto_features_by_norm[norm_key]
                # Higher severity if feature has many stories or high confidence
                severity = DeviationSeverity.MEDIUM
                if len(auto_feature.stories) > 3 or auto_feature.confidence >= 0.8:
                    severity = DeviationSeverity.HIGH
                elif len(auto_feature.stories) == 0 or auto_feature.confidence < 0.5:
                    severity = DeviationSeverity.LOW

                deviations.append(
                    Deviation(
                        type=DeviationType.EXTRA_IMPLEMENTATION,
                        severity=severity,
                        description=f"Feature '{auto_feature.key}' ({auto_feature.title}) found in code but not in manual plan",
                        location=f"features[{auto_feature.key}]",
                        fix_hint=f"Add feature '{auto_feature.key}' to manual plan or remove from code",
                    )
                )

        # Compare common features using normalized keys
        common_norm_keys = set(manual_features_by_norm.keys()) & set(auto_features_by_norm.keys())
        for norm_key in common_norm_keys:
            manual_feature = manual_features_by_norm[norm_key]
            auto_feature = auto_features_by_norm[norm_key]
            key = manual_feature.key  # Use manual key for display

            # Compare feature titles
            if manual_feature.title != auto_feature.title:
                deviations.append(
                    Deviation(
                        type=DeviationType.MISMATCH,
                        severity=DeviationSeverity.LOW,
                        description=f"Feature '{key}' title differs: manual='{manual_feature.title}', auto='{auto_feature.title}'",
                        location=f"features[{key}].title",
                        fix_hint="Update feature title in code or manual plan",
                    )
                )

            # Compare stories
            deviations.extend(self._compare_stories(manual_feature, auto_feature, key))

        return deviations

    def _compare_stories(self, manual_feature, auto_feature, feature_key: str) -> list[Deviation]:
        """Compare stories within a feature with enhanced detection."""
        deviations: list[Deviation] = []

        # Build story maps by key
        manual_stories = {s.key: s for s in manual_feature.stories}
        auto_stories = {s.key: s for s in auto_feature.stories}

        # Check for missing stories
        for key in manual_stories:
            if key not in auto_stories:
                manual_story = manual_stories[key]
                # Higher severity if story has high value points or is not a draft
                value_points = manual_story.value_points or 0
                severity = (
                    DeviationSeverity.HIGH
                    if (value_points >= 8 or not manual_story.draft)
                    else DeviationSeverity.MEDIUM
                )

                deviations.append(
                    Deviation(
                        type=DeviationType.MISSING_STORY,
                        severity=severity,
                        description=f"Story '{key}' ({manual_story.title}) in manual plan but not implemented",
                        location=f"features[{feature_key}].stories[{key}]",
                        fix_hint=f"Implement story '{key}' or update manual plan",
                    )
                )

        # Check for extra stories
        for key in auto_stories:
            if key not in manual_stories:
                auto_story = auto_stories[key]
                # Medium severity if story has high confidence or value points
                value_points = auto_story.value_points or 0
                severity = (
                    DeviationSeverity.MEDIUM
                    if (auto_story.confidence >= 0.8 or value_points >= 8)
                    else DeviationSeverity.LOW
                )

                deviations.append(
                    Deviation(
                        type=DeviationType.EXTRA_IMPLEMENTATION,
                        severity=severity,
                        description=f"Story '{key}' ({auto_story.title}) found in code but not in manual plan",
                        location=f"features[{feature_key}].stories[{key}]",
                        fix_hint=f"Add story '{key}' to manual plan or remove from code",
                    )
                )

        # Compare common stories
        common_keys = set(manual_stories.keys()) & set(auto_stories.keys())
        for key in common_keys:
            manual_story = manual_stories[key]
            auto_story = auto_stories[key]

            # Title mismatch
            if manual_story.title != auto_story.title:
                deviations.append(
                    Deviation(
                        type=DeviationType.MISMATCH,
                        severity=DeviationSeverity.LOW,
                        description=f"Story '{key}' title differs: manual='{manual_story.title}', auto='{auto_story.title}'",
                        location=f"features[{feature_key}].stories[{key}].title",
                        fix_hint="Update story title in code or manual plan",
                    )
                )

            # Acceptance criteria drift
            manual_acceptance = set(manual_story.acceptance or [])
            auto_acceptance = set(auto_story.acceptance or [])
            if manual_acceptance != auto_acceptance:
                missing_criteria = manual_acceptance - auto_acceptance
                extra_criteria = auto_acceptance - manual_acceptance

                if missing_criteria:
                    deviations.append(
                        Deviation(
                            type=DeviationType.ACCEPTANCE_DRIFT,
                            severity=DeviationSeverity.HIGH,
                            description=f"Story '{key}' missing acceptance criteria: {', '.join(missing_criteria)}",
                            location=f"features[{feature_key}].stories[{key}].acceptance",
                            fix_hint=f"Ensure all acceptance criteria are implemented: {', '.join(missing_criteria)}",
                        )
                    )

                if extra_criteria:
                    deviations.append(
                        Deviation(
                            type=DeviationType.ACCEPTANCE_DRIFT,
                            severity=DeviationSeverity.MEDIUM,
                            description=f"Story '{key}' has extra acceptance criteria in code: {', '.join(extra_criteria)}",
                            location=f"features[{feature_key}].stories[{key}].acceptance",
                            fix_hint=f"Update manual plan to include: {', '.join(extra_criteria)}",
                        )
                    )

            # Story points mismatch (if significant)
            manual_points = manual_story.story_points or 0
            auto_points = auto_story.story_points or 0
            if abs(manual_points - auto_points) >= 3:
                deviations.append(
                    Deviation(
                        type=DeviationType.MISMATCH,
                        severity=DeviationSeverity.MEDIUM,
                        description=f"Story '{key}' story points differ significantly: manual={manual_points}, auto={auto_points}",
                        location=f"features[{feature_key}].stories[{key}].story_points",
                        fix_hint="Re-evaluate story complexity or update manual plan",
                    )
                )

            # Value points mismatch (if significant)
            manual_value = manual_story.value_points or 0
            auto_value = auto_story.value_points or 0
            if abs(manual_value - auto_value) >= 5:
                deviations.append(
                    Deviation(
                        type=DeviationType.MISMATCH,
                        severity=DeviationSeverity.MEDIUM,
                        description=f"Story '{key}' value points differ significantly: manual={manual_value}, auto={auto_value}",
                        location=f"features[{feature_key}].stories[{key}].value_points",
                        fix_hint="Re-evaluate business value or update manual plan",
                    )
                )

        return deviations
