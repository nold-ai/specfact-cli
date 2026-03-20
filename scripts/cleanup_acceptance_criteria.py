#!/usr/bin/env python3
"""
Cleanup script to remove duplicate replacement instruction text from acceptance criteria.

This script removes acceptance criteria that contain replacement instruction text
(e.g., "Yes, these should be more specific. Replace generic 'works correctly'...")
that were added during previous enrichment runs before the fix was implemented.

Usage:
    hatch run python scripts/cleanup_acceptance_criteria.py [bundle_name]

    If bundle_name is not provided, uses the active bundle.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle
from specfact_cli.utils.structure import SpecFactStructure


logger = logging.getLogger(__name__)


@beartype
@require(lambda acceptance: bool(acceptance.strip()), "acceptance must be non-empty")
def should_remove_criteria(acceptance: str) -> bool:
    """
    Check if acceptance criteria should be removed.

    Removes criteria that contain replacement instruction text.
    """
    acc_lower = acceptance.lower()

    # Remove replacement instruction text
    return (
        "replace generic" in acc_lower
        or ("should be more specific" in acc_lower and "testable criteria:" in acc_lower)
        or ("yes, these should be more specific" in acc_lower)
    )


@beartype
def _resolve_bundle_name(base_path: Path, bundle_name: str | None) -> str | None:
    """Resolve explicit or active bundle name."""
    if bundle_name is not None:
        return bundle_name
    return SpecFactStructure.get_active_bundle_name(base_path)


@beartype
def _clean_acceptance_lists(bundle: Any) -> tuple[int, list[tuple[str, int]], list[tuple[str, str, int]]]:
    """Remove replacement-instruction acceptance criteria from bundle features and stories."""
    total_removed = 0
    features_cleaned: list[tuple[str, int]] = []
    stories_cleaned: list[tuple[str, str, int]] = []

    for feature_key, feature in bundle.features.items():
        if feature.acceptance:
            original_count = len(feature.acceptance)
            feature.acceptance = [acc for acc in feature.acceptance if not should_remove_criteria(acc)]
            removed = original_count - len(feature.acceptance)
            if removed > 0:
                total_removed += removed
                features_cleaned.append((feature_key, removed))

        if not feature.stories:
            continue
        for story in feature.stories:
            if not story.acceptance:
                continue
            original_count = len(story.acceptance)
            story.acceptance = [acc for acc in story.acceptance if not should_remove_criteria(acc)]
            removed = original_count - len(story.acceptance)
            if removed > 0:
                total_removed += removed
                stories_cleaned.append((feature_key, story.key, removed))

    return total_removed, features_cleaned, stories_cleaned


@beartype
def _log_cleanup_summary(
    total_removed: int,
    features_cleaned: list[tuple[str, int]],
    stories_cleaned: list[tuple[str, str, int]],
) -> None:
    """Log cleanup results."""
    logger.info("Cleaned up %d acceptance criteria:", total_removed)
    if features_cleaned:
        logger.info("  Features: %d", len(features_cleaned))
        for feature_key, count in features_cleaned:
            logger.info("    - %s: removed %d", feature_key, count)
    if stories_cleaned:
        logger.info("  Stories: %d", len(stories_cleaned))
        for feature_key, story_key, count in stories_cleaned:
            logger.info("    - %s.%s: removed %d", feature_key, story_key, count)


@beartype
@ensure(lambda result: result >= 0, "exit code must be non-negative")
def cleanup_acceptance_criteria(bundle_name: str | None = None) -> int:
    """
    Clean up acceptance criteria by removing replacement instruction text.

    Args:
        bundle_name: Bundle name to clean (default: active bundle)

    Returns:
        Number of criteria removed
    """
    base_path = Path(".")

    # Get bundle name
    bundle_name = _resolve_bundle_name(base_path, bundle_name)
    if bundle_name is None:
        logger.error("No active bundle found. Please specify bundle name or run 'specfact plan select'")
        return 1

    # Load bundle
    bundle_dir = base_path / SpecFactStructure.PROJECTS / bundle_name
    if not bundle_dir.exists():
        logger.error("Bundle directory not found: %s", bundle_dir)
        return 1

    logger.info("Loading bundle: %s", bundle_name)
    try:
        bundle = load_project_bundle(bundle_dir)
    except Exception as e:
        logger.error("Failed to load bundle: %s", e)
        return 1

    total_removed, features_cleaned, stories_cleaned = _clean_acceptance_lists(bundle)

    # Save bundle if changes were made
    if total_removed > 0:
        _log_cleanup_summary(total_removed, features_cleaned, stories_cleaned)
        logger.info("Saving bundle...")
        try:
            save_project_bundle(bundle, bundle_dir)
            logger.info("Bundle saved successfully")
            return 0
        except Exception as e:
            logger.error("Failed to save bundle: %s", e)
            return 1
    else:
        logger.info("No cleanup needed - no replacement instruction text found")
        return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    bundle_name = sys.argv[1] if len(sys.argv) > 1 else None
    exit_code = cleanup_acceptance_criteria(bundle_name)
    sys.exit(exit_code)
