"""
Merge conflict resolution for project bundles.

This module provides persona-aware three-way merge resolution for project bundles,
enabling automatic conflict resolution based on persona ownership rules.
"""

from specfact_cli.merge.resolver import MergeConflict, MergeResolution, PersonaMergeResolver


__all__ = ["MergeConflict", "MergeResolution", "PersonaMergeResolver"]
