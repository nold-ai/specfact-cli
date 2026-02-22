# TDD Evidence: bundle-mapper-01-mapping-strategy

## Review findings intake (2026-02-22)

- Historical scorer may choose stale bundle IDs not present in current `available_bundle_ids`.
- History key format is ambiguous because `|` is used for both field and tag separators.
- Content signal can boost confidence even when it points to a different bundle than the selected primary bundle.
- Threshold parsing crashes on malformed user config values instead of falling back to defaults.

## Pre-implementation (failing run)

- **Command**: `hatch run pytest modules/bundle-mapper/tests/ -v --no-cov`
- **Timestamp**: 2026-02-18 (session)
- **Result**: Collection errors — `ModuleNotFoundError: No module named 'bundle_mapper'` (resolved by adding `conftest.py` with `sys.path.insert` for module `src`). Then `BeartypeDecorHintPep3119Exception` for `_ItemLike` Protocol (resolved by `@runtime_checkable`).

## Post-implementation (passing run)

- **Command**: `hatch run pytest modules/bundle-mapper/tests/ -v --no-cov`
- **Timestamp**: 2026-02-18
- **Result**: 11 passed in 0.71s
- **Tests**: test_bundle_mapping_model (3), test_bundle_mapper_engine (5), test_mapping_history (3)

## Pre-implementation (review-defect regression tests)

- **Command**: `hatch run pytest modules/bundle-mapper/tests/unit/test_bundle_mapper_engine.py modules/bundle-mapper/tests/unit/test_mapping_history.py -q`
- **Timestamp**: 2026-02-22
- **Result**: 4 failed, 9 passed
- **Failure summary**:
  - `test_historical_mapping_ignores_stale_bundle_ids`: primary mapping was `None`/invalid due to stale history IDs
  - `test_conflicting_content_signal_does_not_increase_primary_confidence`: confidence was `0.85` instead of `0.80`
  - `test_item_key_similarity_does_not_false_match_tag_lists`: returned false-positive similarity (`True`)
  - `test_load_bundle_mapping_config_malformed_thresholds_use_defaults`: `ValueError` raised for non-numeric thresholds

## Post-implementation (review-defect regression tests)

- **Command**: `hatch run pytest modules/bundle-mapper/tests/unit/test_bundle_mapper_engine.py modules/bundle-mapper/tests/unit/test_mapping_history.py -q`
- **Timestamp**: 2026-02-22
- **Result**: 13 passed in 0.75s
- **Tests**:
  - stale historical bundle IDs are ignored during scoring
  - unambiguous history key serialization preserves tag semantics
  - conflicting content signal does not boost different primary bundle confidence
  - malformed thresholds fall back to defaults
