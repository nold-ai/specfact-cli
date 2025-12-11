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

import sys
from pathlib import Path

from specfact_cli.utils.bundle_loader import load_project_bundle, save_project_bundle
from specfact_cli.utils.structure import SpecFactStructure


def should_remove_criteria(acceptance: str) -> bool:
    """
    Check if acceptance criteria should be removed.
    
    Removes criteria that contain replacement instruction text.
    """
    acc_lower = acceptance.lower()
    
    # Remove replacement instruction text
    contains_replacement_instruction = (
        "replace generic" in acc_lower
        or ("should be more specific" in acc_lower and "testable criteria:" in acc_lower)
        or ("yes, these should be more specific" in acc_lower)
    )
    
    return contains_replacement_instruction


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
    if bundle_name is None:
        bundle_name = SpecFactStructure.get_active_bundle_name(base_path)
        if bundle_name is None:
            print("❌ No active bundle found. Please specify bundle name or run 'specfact plan select'")
            return 1
    
    # Load bundle
    bundle_dir = base_path / SpecFactStructure.PROJECTS / bundle_name
    if not bundle_dir.exists():
        print(f"❌ Bundle directory not found: {bundle_dir}")
        return 1
    
    print(f"📦 Loading bundle: {bundle_name}")
    try:
        bundle = load_project_bundle(bundle_dir)
    except Exception as e:
        print(f"❌ Failed to load bundle: {e}")
        return 1
    
    # Track removals
    total_removed = 0
    features_cleaned = []
    stories_cleaned = []
    
    # Clean feature-level acceptance criteria
    for feature_key, feature in bundle.features.items():
        if feature.acceptance:
            original_count = len(feature.acceptance)
            feature.acceptance = [
                acc for acc in feature.acceptance if not should_remove_criteria(acc)
            ]
            removed = original_count - len(feature.acceptance)
            if removed > 0:
                total_removed += removed
                features_cleaned.append((feature_key, removed))
        
        # Clean story-level acceptance criteria
        if feature.stories:
            for story in feature.stories:
                if story.acceptance:
                    original_count = len(story.acceptance)
                    story.acceptance = [
                        acc for acc in story.acceptance if not should_remove_criteria(acc)
                    ]
                    removed = original_count - len(story.acceptance)
                    if removed > 0:
                        total_removed += removed
                        stories_cleaned.append((feature_key, story.key, removed))
    
    # Save bundle if changes were made
    if total_removed > 0:
        print(f"\n🧹 Cleaned up {total_removed} acceptance criteria:")
        if features_cleaned:
            print(f"  Features: {len(features_cleaned)}")
            for feature_key, count in features_cleaned:
                print(f"    - {feature_key}: removed {count}")
        if stories_cleaned:
            print(f"  Stories: {len(stories_cleaned)}")
            for feature_key, story_key, count in stories_cleaned:
                print(f"    - {feature_key}.{story_key}: removed {count}")
        
        print(f"\n💾 Saving bundle...")
        try:
            save_project_bundle(bundle, bundle_dir)
            print(f"✅ Bundle saved successfully")
            return 0
        except Exception as e:
            print(f"❌ Failed to save bundle: {e}")
            return 1
    else:
        print("✅ No cleanup needed - no replacement instruction text found")
        return 0


if __name__ == "__main__":
    bundle_name = sys.argv[1] if len(sys.argv) > 1 else None
    exit_code = cleanup_acceptance_criteria(bundle_name)
    sys.exit(exit_code)

