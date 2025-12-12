"""
Plan bundle enricher for automatic enhancement of vague acceptance criteria,
incomplete requirements, and generic tasks.

This module provides automatic enrichment capabilities that can be triggered
during plan review to improve plan quality without manual intervention.
"""

from __future__ import annotations

import re
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.models.plan import PlanBundle


class PlanEnricher:
    """
    Enricher for automatically enhancing plan bundles.

    Detects and fixes vague acceptance criteria, incomplete requirements,
    and generic tasks using pattern-based improvements.
    """

    @beartype
    @require(lambda plan_bundle: isinstance(plan_bundle, PlanBundle), "Plan bundle must be PlanBundle")
    @ensure(lambda result: isinstance(result, dict), "Must return dict with enrichment summary")
    def enrich_plan(self, plan_bundle: PlanBundle) -> dict[str, Any]:
        """
        Enrich plan bundle by enhancing vague acceptance criteria, incomplete requirements, and generic tasks.

        Args:
            plan_bundle: Plan bundle to enrich

        Returns:
            Dictionary with enrichment summary (features_updated, stories_updated, tasks_updated, etc.)
        """
        summary: dict[str, Any] = {
            "features_updated": 0,
            "stories_updated": 0,
            "acceptance_criteria_enhanced": 0,
            "requirements_enhanced": 0,
            "tasks_enhanced": 0,
            "changes": [],
        }

        for feature in plan_bundle.features:
            feature_updated = False

            # Enhance incomplete requirements in outcomes
            enhanced_outcomes = []
            for outcome in feature.outcomes:
                enhanced = self._enhance_incomplete_requirement(outcome, feature.title)
                if enhanced != outcome:
                    enhanced_outcomes.append(enhanced)
                    summary["requirements_enhanced"] += 1
                    summary["changes"].append(f"Feature {feature.key}: Enhanced requirement '{outcome}' → '{enhanced}'")
                    feature_updated = True
                else:
                    enhanced_outcomes.append(outcome)

            if feature_updated:
                feature.outcomes = enhanced_outcomes
                summary["features_updated"] += 1

            # Enhance stories
            for story in feature.stories:
                story_updated = False

                # Enhance vague acceptance criteria
                enhanced_acceptance = []
                for acc in story.acceptance:
                    enhanced = self._enhance_vague_acceptance_criteria(acc, story.title, feature.title)
                    if enhanced != acc:
                        enhanced_acceptance.append(enhanced)
                        summary["acceptance_criteria_enhanced"] += 1
                        summary["changes"].append(
                            f"Story {story.key}: Enhanced acceptance criteria '{acc}' → '{enhanced}'"
                        )
                        story_updated = True
                    else:
                        enhanced_acceptance.append(acc)

                if story_updated:
                    story.acceptance = enhanced_acceptance
                    summary["stories_updated"] += 1

                # Enhance generic tasks
                if story.tasks:
                    enhanced_tasks = []
                    for task in story.tasks:
                        enhanced = self._enhance_generic_task(task, story.title, feature.title)
                        if enhanced != task:
                            enhanced_tasks.append(enhanced)
                            summary["tasks_enhanced"] += 1
                            summary["changes"].append(f"Story {story.key}: Enhanced task '{task}' → '{enhanced}'")
                            story_updated = True
                        else:
                            enhanced_tasks.append(task)

                    if story_updated and enhanced_tasks:
                        story.tasks = enhanced_tasks

        return summary

    @beartype
    @require(lambda requirement: isinstance(requirement, str), "Requirement must be string")
    @require(lambda feature_title: isinstance(feature_title, str), "Feature title must be string")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    @ensure(lambda result: len(result) > 0, "Result must be non-empty")
    def _enhance_incomplete_requirement(self, requirement: str, feature_title: str) -> str:
        """
        Enhance incomplete requirement (e.g., "System MUST Helper class" → "System MUST provide a Helper class").

        Args:
            requirement: Requirement text to enhance
            feature_title: Feature title for context

        Returns:
            Enhanced requirement text
        """
        requirement_lower = requirement.lower()
        incomplete_patterns = [
            ("system must", "System MUST provide"),
            ("system should", "System SHOULD provide"),
            ("must", "MUST provide"),
            ("should", "SHOULD provide"),
        ]

        for pattern, replacement_prefix in incomplete_patterns:
            if requirement_lower.startswith(pattern):
                remaining = requirement[len(pattern) :].strip()
                # Check if it's incomplete (just a noun phrase without verb)
                if (
                    remaining
                    and len(remaining.split()) < 3
                    and any(
                        keyword in remaining.lower()
                        for keyword in ["class", "helper", "module", "component", "service", "function"]
                    )
                ):
                    # Enhance: "System MUST Helper class" → "System MUST provide a Helper class for [feature]"
                    # Extract the component name
                    component_name = remaining.strip()
                    # Capitalize first letter if needed
                    if component_name and component_name[0].islower():
                        component_name = component_name[0].upper() + component_name[1:]
                    # Generate enhanced requirement
                    if "class" in component_name.lower():
                        return f"{replacement_prefix} a {component_name} for {feature_title.lower()} operations"
                    if "helper" in component_name.lower():
                        return f"{replacement_prefix} a {component_name} class for {feature_title.lower()} operations"
                    return f"{replacement_prefix} a {component_name} for {feature_title.lower()}"

        return requirement

    @beartype
    @require(lambda acceptance: isinstance(acceptance, str), "Acceptance must be string")
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def _is_code_specific_criteria(self, acceptance: str) -> bool:
        """
        Check if acceptance criteria are already code-specific (should not be replaced).

        Delegates to shared utility function for consistency.

        Args:
            acceptance: Acceptance criteria text to check

        Returns:
            True if criteria are code-specific, False if vague/generic
        """
        from specfact_cli.utils.acceptance_criteria import is_code_specific_criteria

        return is_code_specific_criteria(acceptance)

    @beartype
    @require(lambda acceptance: isinstance(acceptance, str), "Acceptance must be string")
    @require(lambda story_title: isinstance(story_title, str), "Story title must be string")
    @require(lambda feature_title: isinstance(feature_title, str), "Feature title must be string")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    @ensure(lambda result: len(result) > 0, "Result must be non-empty")
    def _enhance_vague_acceptance_criteria(self, acceptance: str, story_title: str, feature_title: str) -> str:
        """
        Enhance vague acceptance criteria using simple text format (not GWT format).

        This method only enhances vague/generic criteria. Code-specific criteria (containing method names,
        class names, file paths, type hints) are preserved unchanged.

        Args:
            acceptance: Acceptance criteria text to enhance
            story_title: Story title for context
            feature_title: Feature title for context

        Returns:
            Enhanced acceptance criteria in simple text format, or original if already code-specific
        """
        acceptance_lower = acceptance.lower()

        # FIRST: Check if it's already in Given/When/Then format and convert it
        # This must happen before code-specific check, as GWT format might be misidentified as code-specific
        has_gwt_format = (
            re.search(r"\bgiven\b", acceptance_lower, re.IGNORECASE)
            and re.search(r"\bwhen\b", acceptance_lower, re.IGNORECASE)
            and re.search(r"\bthen\b", acceptance_lower, re.IGNORECASE)
        )
        if has_gwt_format:
            # Extract the "Then" part as the core requirement
            # Split by "then" (case-insensitive) and take the last part
            parts = re.split(r"\bthen\b", acceptance_lower, flags=re.IGNORECASE)
            if len(parts) > 1:
                then_part = parts[-1].strip()
                # Remove common trailing phrases and clean up
                then_part = re.sub(r"\bsuccessfully\b", "", then_part).strip()
                then_part = re.sub(r"\s+", " ", then_part)  # Normalize whitespace
                if then_part:
                    # Capitalize first letter and create simple format
                    then_capitalized = then_part[0].upper() + then_part[1:] if len(then_part) > 1 else then_part.upper()
                    return f"Must verify {then_capitalized}"
            return acceptance

        # Skip enrichment if criteria are already code-specific
        if self._is_code_specific_criteria(acceptance):
            return acceptance

        vague_patterns = [
            (
                "is implemented",
                "Must verify {story} is functional",
            ),
            (
                "is functional",
                "Must verify {story} functions correctly",
            ),
            (
                "works",
                "Must verify {story} functions correctly",
            ),
            (
                "is done",
                "Must verify {story} is completed successfully",
            ),
            (
                "is complete",
                "Must verify {story} is completed successfully",
            ),
            (
                "is ready",
                "Must verify {story} is available",
            ),
        ]

        for pattern, template in vague_patterns:
            # Only match if acceptance is exactly the pattern or starts with it (simple statement)
            # Use word boundaries to avoid partial matches
            pattern_re = re.compile(rf"\b{re.escape(pattern)}\b")
            if pattern_re.search(acceptance_lower):
                # Only enhance if the entire acceptance is just the vague pattern
                # or if it's a very simple statement (1-2 words) without code-specific details
                acceptance_stripped = acceptance_lower.strip()
                if acceptance_stripped == pattern or (
                    len(acceptance_stripped.split()) <= 2 and not self._is_code_specific_criteria(acceptance)
                ):
                    # Replace placeholder with story title
                    return template.format(story=story_title)

        # If it's a simple statement without testable keywords, enhance it
        testable_keywords = ["must", "should", "will", "verify", "validate", "check", "ensure"]
        if not any(keyword in acceptance_lower for keyword in testable_keywords):
            # Convert to testable format
            if acceptance_lower.startswith(("user can", "system can")):
                return f"Must verify {acceptance.lower()}"
            # Generate simple text format from simple statement
            return f"Must verify {acceptance}"

        return acceptance

    @beartype
    @require(lambda task: isinstance(task, str), "Task must be string")
    @require(lambda story_title: isinstance(story_title, str), "Story title must be string")
    @require(lambda feature_title: isinstance(feature_title, str), "Feature title must be string")
    @ensure(lambda result: isinstance(result, str), "Must return string")
    @ensure(lambda result: len(result) > 0, "Result must be non-empty")
    def _enhance_generic_task(self, task: str, story_title: str, feature_title: str) -> str:
        """
        Enhance generic task (e.g., "Implement [story]" → "Implement [story] in src/... with methods for ...").

        Args:
            task: Task description to enhance
            story_title: Story title for context
            feature_title: Feature title for context

        Returns:
            Enhanced task with implementation details
        """
        task_lower = task.lower()
        generic_patterns = [
            ("implement", "Implement {story} in src/specfact_cli/... with methods for {feature} operations"),
            ("create", "Create {story} component in src/specfact_cli/... with {feature} functionality"),
            ("add", "Add {story} functionality to src/specfact_cli/... with {feature} support"),
            ("set up", "Set up {story} infrastructure in src/specfact_cli/... for {feature} operations"),
        ]

        # Check if task is generic (has pattern but no implementation details)
        has_details = any(
            detail in task_lower
            for detail in ["file", "path", "method", "class", "component", "module", "function", "src/", "tests/"]
        )

        if not has_details:
            for pattern, template in generic_patterns:
                if pattern in task_lower:
                    # Extract the story/feature name from task
                    remaining = task_lower.replace(pattern, "").strip()
                    if not remaining or remaining == story_title.lower():
                        # Use template with story and feature
                        return template.format(story=story_title, feature=feature_title.lower())
                    # Keep original but add implementation details
                    return f"{task} in src/specfact_cli/... with methods and tests"

        return task
