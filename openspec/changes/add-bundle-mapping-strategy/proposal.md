# Change: Bundle/Spec Mapping Strategy

## Why



Teams need intelligent spec-to-bundle assignment with confidence scoring and user confirmation to prevent mis-bundled specs. Currently, bundle assignment is manual or based on simple heuristics, leading to specs landing in wrong bundles and making conflict detection unreliable.

This change implements Plan C from the SpecFact Backlog & OpenSpec Implementation Roadmap (2026-01-18), providing intelligent bundle mapping with three confidence signals (explicit labels, historical patterns, content similarity) and interactive review for ambiguous mappings.

## What Changes



- **NEW**: `BundleMapper` engine (`src/specfact_cli/backlog/bundle_mapper.py`) - Confidence-based mapping with three signals
- **NEW**: `BundleMapping` model (`src/specfact_cli/models/bundle_mapping.py`) - Result model with bundle_id, confidence, candidates, explanation
- **NEW**: Mapping history persistence (`.specfact/config.yaml`) - Auto-learned rules from user confirmations
- **NEW**: Interactive mapping UI (`src/specfact_cli/cli/backlog_commands.py`) - User prompts with confidence visualization
- **EXTEND**: `--auto-bundle` flag for `backlog refine` (from `add-template-driven-backlog-refinement`) and `backlog import` commands
- **NOTE**: The `backlog refine` command from `add-template-driven-backlog-refinement` uses `BundleMapper` for bundle mapping when `--auto-bundle` is specified.
- **EXTEND**: `SourceTracking` model - Add mapping metadata fields (bundle_id, mapping_confidence, mapping_method, mapping_timestamp)
- **EXTEND**: OpenSpec generation pipeline - Accept `BundleMapping` parameter and record mapping decisions


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #121
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/121>
- **Last Synced Status**: proposed
- **Sanitized**: true
<!-- content_hash: fbcbfafae68636a6 -->