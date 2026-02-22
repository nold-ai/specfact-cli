## 1. Git Workflow

- [x] 1.1 Create git worktree branch `feature/add-bundle-mapping-strategy` from `dev` branch
  - [x] 1.1.1 Ensure primary checkout is on dev and up to date: `git checkout dev && git pull origin dev`
  - [x] 1.1.2 Create branch: `scripts/worktree.sh create feature/add-bundle-mapping-strategy`
  - [x] 1.1.3 Verify branch in worktree: `git worktree list` includes the branch path; then run `git branch --show-current` inside that worktree.

## 2. BundleMapping Model

- [x] 2.1 Create `src/specfact_cli/models/bundle_mapping.py`
  - [x] 2.1.1 Define `BundleMapping` dataclass with fields: primary_bundle_id, confidence, candidates, explained_reasoning
  - [x] 2.1.2 Add `@beartype` decorator for runtime type checking
  - [x] 2.1.3 Add `@icontract` decorators with `@require`/`@ensure` contracts

## 3. BundleMapper Engine

- [x] 3.1 Create `modules/bundle-mapper/src/bundle_mapper/mapper/engine.py`
  - [x] 3.1.1 Implement `BundleMapper` class with `compute_mapping(item: BacklogItem) -> BundleMapping`
  - [x] 3.1.2 Implement `_score_explicit_mapping()` for explicit label signals (bundle:xyz tags)
  - [x] 3.1.3 Implement `_score_historical_mapping()` for historical pattern signals
  - [x] 3.1.4 Implement `_score_content_similarity()` for content-based signals (keyword matching)
  - [x] 3.1.5 Implement weighted confidence calculation (0.8 × explicit + 0.15 × historical + 0.05 × content)
  - [x] 3.1.6 Implement `_item_key()` for creating metadata keys for history matching
  - [x] 3.1.7 Implement `_item_keys_similar()` for comparing metadata keys
  - [x] 3.1.8 Implement `_explain_score()` for human-readable explanations
  - [x] 3.1.9 Implement `_build_explanation()` for detailed mapping rationale
  - [x] 3.1.10 Add `@beartype` decorator for runtime type checking
  - [x] 3.1.11 Add `@icontract` decorators with `@require`/`@ensure` contracts

## 4. Mapping History Persistence

- [x] 4.1 Extend `.specfact/config.yaml` structure
  - [x] 4.1.1 Add `backlog.bundle_mapping.rules` section for persistent mapping rules
  - [x] 4.1.2 Add `backlog.bundle_mapping.history` section for auto-populated historical mappings
  - [x] 4.1.3 Add `backlog.bundle_mapping.explicit_label_prefix` config (default: "bundle:")
  - [x] 4.1.4 Add `backlog.bundle_mapping.auto_assign_threshold` config (default: 0.8)
  - [x] 4.1.5 Add `backlog.bundle_mapping.confirm_threshold` config (default: 0.5)

## 5. Mapping Rule Model

- [x] 5.1 Create `MappingRule` Pydantic model
  - [x] 5.1.1 Define fields: pattern, bundle_id, action, confidence
  - [x] 5.1.2 Implement `matches(item: BacklogItem) -> bool` method
  - [x] 5.1.3 Support pattern matching: tag=~regex, assignee=exact, area=exact
  - [x] 5.1.4 Add `@beartype` decorator for runtime type checking

## 6. Mapping History Functions

- [x] 6.1 Implement `save_user_confirmed_mapping()` function
  - [x] 6.1.1 Create item_key from item metadata
  - [x] 6.1.2 Increment mapping count in history
  - [x] 6.1.3 Save to config file
  - [x] 6.1.4 Add `@beartype` decorator for runtime type checking

## 7. Interactive Mapping UI

- [x] 7.1 Implement `ask_bundle_mapping()` function in `src/specfact_cli/cli/backlog_commands.py`
  - [x] 7.1.1 Display confidence level (✓ high, ? medium, ! low)
  - [x] 7.1.2 Show suggested bundle with reasoning
  - [x] 7.1.3 Display alternative candidates with scores
  - [x] 7.1.4 Provide options: accept, select from candidates, show all bundles, skip
  - [x] 7.1.5 Handle user selection and return bundle_id
  - [x] 7.1.6 Add `@beartype` decorator for runtime type checking

## 8. CLI Integration: --auto-bundle Flag

- [x] 8.1 Extend `backlog refine` command
  - [x] 8.1.1 Add `--auto-bundle` flag option
  - [x] 8.1.2 Add `--auto-accept-bundle` flag option
  - [x] 8.1.3 Integrate bundle mapping into refinement workflow
  - [x] 8.1.4 Auto-assign if confidence >= 0.8
  - [x] 8.1.5 Prompt user if confidence 0.5-0.8
  - [x] 8.1.6 Require explicit selection if confidence < 0.5

- [x] 8.2 Extend `backlog import` command
  - [x] 8.2.1 Add `--auto-bundle` flag option
  - [x] 8.2.2 Add `--auto-accept-bundle` flag option
  - [x] 8.2.3 Integrate bundle mapping into import workflow
  - [x] 8.2.4 Use mapping if `--bundle` not specified

## 9. Source Tracking Extension

- [x] 9.1 Extend `src/specfact_cli/models/source_tracking.py`
  - [x] 9.1.1 Add `bundle_id` field (Optional[str])
  - [x] 9.1.2 Add `mapping_confidence` field (Optional[float])
  - [x] 9.1.3 Add `mapping_method` field (Optional[str]) - "explicit_label", "historical", "content_similarity", "user_confirmed"
  - [x] 9.1.4 Add `mapping_timestamp` field (Optional[datetime])
  - [x] 9.1.5 Ensure backward compatibility (all fields optional)

## 10. OpenSpec Generation Integration

- [x] 10.1 Extend `_write_openspec_change_from_proposal()` function
  - [x] 10.1.1 Add `mapping: Optional[BundleMapping]` parameter
  - [x] 10.1.2 Update source_tracking with mapping metadata
  - [x] 10.1.3 Include mapping information in proposal.md source tracking section
  - [x] 10.1.4 Ensure backward compatibility (parameter optional)

## 11. Code Quality and Contract Validation

- [x] 11.1 Apply code formatting
  - [x] 11.1.1 Run `hatch run format` to apply black and isort
  - [x] 11.1.2 Verify all files are properly formatted
- [x] 11.2 Run linting checks
  - [x] 11.2.1 Run `hatch run lint` to check for linting errors
  - [x] 11.2.2 Fix all pylint, ruff, and other linter errors
- [x] 11.3 Run type checking
  - [x] 11.3.1 Run `hatch run type-check` to verify type annotations
  - [x] 11.3.2 Fix all basedpyright type errors
- [x] 11.4 Verify contract decorators
  - [x] 11.4.1 Ensure all new public functions have `@beartype` decorators
  - [x] 11.4.2 Ensure all new public functions have `@icontract` decorators with appropriate `@require`/`@ensure`

## 12. Testing and Validation

- [x] 12.1 Add new tests
  - [x] 12.1.1 Add unit tests for BundleMapper (9+ tests: 3 signals × 3 confidence levels)
  - [x] 12.1.2 Add unit tests for explicit mapping signal (3+ tests)
  - [x] 12.1.3 Add unit tests for historical mapping signal (3+ tests)
  - [x] 12.1.4 Add unit tests for content similarity signal (3+ tests)
  - [x] 12.1.5 Add unit tests for confidence scoring (5+ tests)
  - [x] 12.1.6 Add unit tests for mapping history persistence (5+ tests)
  - [x] 12.1.7 Add unit tests for interactive UI (5+ tests: user selections)
  - [x] 12.1.8 Add integration tests: end-to-end mapping workflow (5+ tests)
- [x] 12.2 Update existing tests
  - [x] 12.2.1 Update source_tracking tests to include new mapping fields
  - [x] 12.2.2 Update OpenSpec generation tests to handle mapping parameter
- [x] 12.3 Run full test suite of modified tests only
  - [x] 12.3.1 Run `hatch run smart-test` to execute only the tests that are relevant to the changes
  - [x] 12.3.2 Verify all modified tests pass (unit, integration, E2E)
- [x] 12.4 Final validation
  - [x] 12.4.1 Run `hatch run format` one final time
  - [x] 12.4.2 Run `hatch run lint` one final time
  - [x] 12.4.3 Run `hatch run type-check` one final time
  - [x] 12.4.4 Run `hatch test --cover -v` one final time
  - [x] 12.4.5 Verify no errors remain (formatting, linting, type-checking, tests)

## 12R. Review Defect Remediation (2026-02-22)

- [x] 12R.1 Add regression tests first (must fail before implementation)
  - [x] 12R.1.1 Historical scoring ignores stale bundle IDs not present in available bundles
  - [x] 12R.1.2 History key encoding is unambiguous and does not lose tag values
  - [x] 12R.1.3 Conflicting content signal does not boost confidence for another primary bundle
  - [x] 12R.1.4 Malformed threshold config values fall back to defaults without crashing
- [x] 12R.2 Record failing run in `TDD_EVIDENCE.md` with command, timestamp, and failure summary
- [x] 12R.3 Implement production fixes in mapper/history modules
- [x] 12R.4 Re-run regression tests and record passing run in `TDD_EVIDENCE.md`

## 13. OpenSpec Validation

- [x] 13.1 Validate change proposal
  - [x] 13.1.1 Run `openspec validate add-bundle-mapping-strategy --strict`
  - [x] 13.1.2 Fix any validation errors
  - [x] 13.1.3 Re-run validation until passing

## 14. Pull Request Creation

- [x] 14.1 Prepare changes for commit
  - [x] 14.1.1 Ensure all changes are committed: `git add .`
  - [x] 14.1.2 Commit with conventional message: `git commit -m "feat: add bundle mapping strategy with confidence scoring"`
  - [x] 14.1.3 Push to remote: `git push origin feature/add-bundle-mapping-strategy`
- [x] 14.2 Create Pull Request
  - [x] 14.2.1 Create PR in specfact-cli repository
  - [x] 14.2.2 Changes are ready for review in the branch
