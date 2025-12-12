"""
Agile/Scrum validation rules for persona imports.

This module provides validation for Definition of Ready (DoR), dependencies,
prioritization, and business value requirements.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from beartype import beartype
from icontract import ensure, require


class AgileValidationError(Exception):
    """Error during agile/scrum validation."""


class AgileValidator:
    """Validator for agile/scrum requirements in persona imports."""

    # Valid priority formats
    PRIORITY_PATTERNS = [
        r"^P[0-3]$",  # P0, P1, P2, P3
        r"^(Must|Should|Could|Won't)$",  # MoSCoW
        r"^(Critical|High|Medium|Low)$",  # Descriptive
    ]

    # Valid story point values (Fibonacci-like)
    VALID_STORY_POINTS = [0, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 100]

    # ISO 8601 date pattern
    ISO_DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"

    @beartype
    @require(lambda story: isinstance(story, dict), "Story must be dict")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def validate_dor(self, story: dict[str, Any], feature_key: str | None = None) -> list[str]:
        """
        Validate Definition of Ready (DoR) for a story.

        Args:
            story: Story dictionary with DoR fields
            feature_key: Optional feature key for error context

        Returns:
            List of validation errors (empty if valid)
        """
        errors: list[str] = []
        story_key = story.get("key", "UNKNOWN")
        context = f"Story {story_key}" + (f" (Feature {feature_key})" if feature_key else "")

        # Check story points
        story_points = story.get("story_points")
        if story_points is None:
            errors.append(f"{context}: Missing story points (required for DoR)")
        elif story_points not in self.VALID_STORY_POINTS:
            errors.append(
                f"{context}: Invalid story points '{story_points}' (must be one of {self.VALID_STORY_POINTS})"
            )

        # Check value points
        value_points = story.get("value_points")
        if value_points is None:
            errors.append(f"{context}: Missing value points (required for DoR)")
        elif value_points not in self.VALID_STORY_POINTS:
            errors.append(
                f"{context}: Invalid value points '{value_points}' (must be one of {self.VALID_STORY_POINTS})"
            )

        # Check priority
        priority = story.get("priority")
        if priority is None:
            errors.append(f"{context}: Missing priority (required for DoR)")
        elif not self._is_valid_priority(priority):
            errors.append(
                f"{context}: Invalid priority '{priority}' (must be P0-P3, MoSCoW, or Critical/High/Medium/Low)"
            )

        # Check business value description
        business_value = story.get("business_value_description")
        if not business_value or not business_value.strip():
            errors.append(f"{context}: Missing business value description (required for DoR)")

        # Check dependencies are valid (if present)
        depends_on = story.get("depends_on_stories", [])
        blocks = story.get("blocks_stories", [])
        if depends_on or blocks:
            # Validate dependency format (should be story keys)
            for dep in depends_on:
                if not re.match(r"^[A-Z]+-\d+$", dep):
                    errors.append(f"{context}: Invalid dependency format '{dep}' (expected STORY-001 format)")

        # Check target date format (if present)
        due_date = story.get("due_date")
        if due_date and not re.match(self.ISO_DATE_PATTERN, due_date):
            errors.append(f"{context}: Invalid date format '{due_date}' (expected ISO 8601: YYYY-MM-DD)")

        # Check target date is in future (warn if past)
        if due_date and re.match(self.ISO_DATE_PATTERN, due_date):
            try:
                date_obj = datetime.strptime(due_date, "%Y-%m-%d")
                if date_obj.date() < datetime.now().date():
                    errors.append(f"{context}: Warning - target date '{due_date}' is in the past (may need updating)")
            except ValueError:
                pass  # Already caught by format check

        return errors

    @beartype
    @require(lambda feature: isinstance(feature, dict), "Feature must be dict")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def validate_feature_prioritization(self, feature: dict[str, Any]) -> list[str]:
        """
        Validate feature prioritization fields.

        Args:
            feature: Feature dictionary with prioritization fields

        Returns:
            List of validation errors (empty if valid)
        """
        errors: list[str] = []
        feature_key = feature.get("key", "UNKNOWN")

        # Check priority format (if present)
        priority = feature.get("priority")
        if priority and not self._is_valid_priority(priority):
            errors.append(
                f"Feature {feature_key}: Invalid priority '{priority}' (must be P0-P3, MoSCoW, or Critical/High/Medium/Low)"
            )

        # Check business value score range (if present)
        business_value_score = feature.get("business_value_score")
        if business_value_score is not None and (
            not isinstance(business_value_score, int) or business_value_score < 0 or business_value_score > 100
        ):
            errors.append(
                f"Feature {feature_key}: Invalid business value score '{business_value_score}' (must be 0-100)"
            )

        # Check business value description (if present)
        business_value = feature.get("business_value_description")
        if business_value and not business_value.strip():
            errors.append(f"Feature {feature_key}: Business value description is empty")

        return errors

    @beartype
    @require(lambda stories: isinstance(stories, list), "Stories must be list")
    @require(lambda features: isinstance(features, dict), "Features must be dict")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def validate_dependency_integrity(
        self, stories: list[dict[str, Any]], features: dict[str, dict[str, Any]]
    ) -> list[str]:
        """
        Validate dependency integrity (no circular dependencies, all references exist).

        Args:
            stories: List of story dictionaries
            features: Dictionary of feature dictionaries (key -> feature dict)

        Returns:
            List of validation errors (empty if valid)
        """
        errors: list[str] = []

        # Build story key index
        story_keys: set[str] = {
            key for story in stories if (key := story.get("key")) is not None and isinstance(key, str)
        }
        feature_keys: set[str] = set(features.keys())

        # Validate story dependencies
        for story in stories:
            story_key = story.get("key")
            if not story_key:
                continue

            # Check depends_on_stories references exist
            depends_on = story.get("depends_on_stories", [])
            for dep in depends_on:
                if dep not in story_keys:
                    errors.append(f"Story {story_key}: Dependency '{dep}' does not exist")

            # Check blocks_stories references exist
            blocks = story.get("blocks_stories", [])
            for blocked in blocks:
                if blocked not in story_keys:
                    errors.append(f"Story {story_key}: Blocked story '{blocked}' does not exist")

            # Check for circular dependencies (simple check: if A depends on B and B depends on A)
            for dep in depends_on:
                dep_story = next((s for s in stories if s.get("key") == dep), None)
                if dep_story:
                    dep_depends_on = dep_story.get("depends_on_stories", [])
                    if story_key in dep_depends_on:
                        errors.append(f"Story {story_key}: Circular dependency detected with '{dep}'")

        # Validate feature dependencies
        for feature_key, feature in features.items():
            depends_on = feature.get("depends_on_features", [])
            for dep in depends_on:
                if dep not in feature_keys:
                    errors.append(f"Feature {feature_key}: Dependency '{dep}' does not exist")

            blocks = feature.get("blocks_features", [])
            for blocked in blocks:
                if blocked not in feature_keys:
                    errors.append(f"Feature {feature_key}: Blocked feature '{blocked}' does not exist")

            # Check for circular dependencies
            for dep in depends_on:
                dep_feature = features.get(dep)
                if dep_feature:
                    dep_depends_on = dep_feature.get("depends_on_features", [])
                    if feature_key in dep_depends_on:
                        errors.append(f"Feature {feature_key}: Circular dependency detected with '{dep}'")

        return errors

    @beartype
    @require(lambda stories: isinstance(stories, list), "Stories must be list")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def validate_story_point_ranges(self, stories: list[dict[str, Any]]) -> list[str]:
        """
        Validate story point and value point ranges.

        Args:
            stories: List of story dictionaries

        Returns:
            List of validation errors (empty if valid)
        """
        errors: list[str] = []

        for story in stories:
            story_key = story.get("key", "UNKNOWN")

            story_points = story.get("story_points")
            if story_points is not None and story_points not in self.VALID_STORY_POINTS:
                errors.append(
                    f"Story {story_key}: Story points '{story_points}' not in valid range {self.VALID_STORY_POINTS}"
                )

            value_points = story.get("value_points")
            if value_points is not None and value_points not in self.VALID_STORY_POINTS:
                errors.append(
                    f"Story {story_key}: Value points '{value_points}' not in valid range {self.VALID_STORY_POINTS}"
                )

        return errors

    @beartype
    @require(lambda date_str: isinstance(date_str, str), "Date string must be str")
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def validate_date_format(self, date_str: str) -> bool:
        """
        Validate ISO 8601 date format.

        Args:
            date_str: Date string to validate

        Returns:
            True if valid, False otherwise
        """
        return bool(re.match(self.ISO_DATE_PATTERN, date_str))

    @beartype
    @require(lambda priority: isinstance(priority, str), "Priority must be str")
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def _is_valid_priority(self, priority: str) -> bool:
        """
        Check if priority matches valid formats.

        Args:
            priority: Priority string to validate

        Returns:
            True if valid, False otherwise
        """
        priority_upper = priority.strip()
        return any(re.match(pattern, priority_upper, re.IGNORECASE) for pattern in self.PRIORITY_PATTERNS)

    @beartype
    @require(lambda bundle_data: isinstance(bundle_data, dict), "Bundle data must be dict")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def validate_bundle_agile_requirements(self, bundle_data: dict[str, Any]) -> list[str]:
        """
        Validate all agile/scrum requirements for a bundle.

        Args:
            bundle_data: Bundle data dictionary with features and stories

        Returns:
            List of validation errors (empty if valid)
        """
        errors: list[str] = []

        features = bundle_data.get("features", {})
        all_stories: list[dict[str, Any]] = []

        # Collect all stories from features
        for feature_key, feature in features.items():
            # Validate feature prioritization
            feature_errors = self.validate_feature_prioritization(feature)
            errors.extend(feature_errors)

            # Collect stories
            stories = feature.get("stories", [])
            all_stories.extend(stories)

            # Validate DoR for each story
            for story in stories:
                dor_errors = self.validate_dor(story, feature_key)
                errors.extend(dor_errors)

        # Validate story point ranges
        story_point_errors = self.validate_story_point_ranges(all_stories)
        errors.extend(story_point_errors)

        # Validate dependency integrity
        dependency_errors = self.validate_dependency_integrity(all_stories, features)
        errors.extend(dependency_errors)

        return errors
