## 1. Git Workflow

- [ ] 1.1 Create git branch `feature/add-bundle-mapping-strategy` from `dev` branch
  - [ ] 1.1.1 Ensure we're on dev and up to date: `git checkout dev && git pull origin dev`
  - [ ] 1.1.2 Create branch: `git checkout -b feature/add-bundle-mapping-strategy`
  - [ ] 1.1.3 Verify branch was created: `git branch --show-current`

## 2. BundleMapping Model

- [ ] 2.1 Create `src/specfact_cli/models/bundle_mapping.py`
  - [ ] 2.1.1 Define `BundleMapping` dataclass with fields: primary_bundle_id, confidence, candidates, explained_reasoning
  - [ ] 2.1.2 Add `@beartype` decorator for runtime type checking
  - [ ] 2.1.3 Add `@icontract` decorators with `@require`/`@ensure` contracts

## 3. BundleMapper Engine

- [ ] 3.1 Create `modules/bundle-mapper/src/bundle_mapper/mapper/engine.py`
  - [ ] 3.1.1 Implement `BundleMapper` class with `compute_mapping(item: BacklogItem) -> BundleMapping`
  - [ ] 3.1.2 Implement `_score_explicit_mapping()` for explicit label signals (bundle:xyz tags)
  - [ ] 3.1.3 Implement `_score_historical_mapping()` for historical pattern signals
  - [ ] 3.1.4 Implement `_score_content_similarity()` for content-based signals (keyword matching)
  - [ ] 3.1.5 Implement weighted confidence calculation (0.8 × explicit + 0.15 × historical + 0.05 × content)
  - [ ] 3.1.6 Implement `_item_key()` for creating metadata keys for history matching
  - [ ] 3.1.7 Implement `_item_keys_similar()` for comparing metadata keys
  - [ ] 3.1.8 Implement `_explain_score()` for human-readable explanations
  - [ ] 3.1.9 Implement `_build_explanation()` for detailed mapping rationale
  - [ ] 3.1.10 Add `@beartype` decorator for runtime type checking
  - [ ] 3.1.11 Add `@icontract` decorators with `@require`/`@ensure` contracts

## 4. Mapping History Persistence

- [ ] 4.1 Extend `.specfact/config.yaml` structure
  - [ ] 4.1.1 Add `backlog.bundle_mapping.rules` section for persistent mapping rules
  - [ ] 4.1.2 Add `backlog.bundle_mapping.history` section for auto-populated historical mappings
  - [ ] 4.1.3 Add `backlog.bundle_mapping.explicit_label_prefix` config (default: "bundle:")
  - [ ] 4.1.4 Add `backlog.bundle_mapping.auto_assign_threshold` config (default: 0.8)
  - [ ] 4.1.5 Add `backlog.bundle_mapping.confirm_threshold` config (default: 0.5)

## 5. Mapping Rule Model

- [ ] 5.1 Create `MappingRule` Pydantic model
  - [ ] 5.1.1 Define fields: pattern, bundle_id, action, confidence
  - [ ] 5.1.2 Implement `matches(item: BacklogItem) -> bool` method
  - [ ] 5.1.3 Support pattern matching: tag=~regex, assignee=exact, area=exact
  - [ ] 5.1.4 Add `@beartype` decorator for runtime type checking

## 6. Mapping History Functions

- [ ] 6.1 Implement `save_user_confirmed_mapping()` function
  - [ ] 6.1.1 Create item_key from item metadata
  - [ ] 6.1.2 Increment mapping count in history
  - [ ] 6.1.3 Save to config file
  - [ ] 6.1.4 Add `@beartype` decorator for runtime type checking

## 7. Interactive Mapping UI

- [ ] 7.1 Implement `ask_bundle_mapping()` function in `src/specfact_cli/cli/backlog_commands.py`
  - [ ] 7.1.1 Display confidence level (✓ high, ? medium, ! low)
  - [ ] 7.1.2 Show suggested bundle with reasoning
  - [ ] 7.1.3 Display alternative candidates with scores
  - [ ] 7.1.4 Provide options: accept, select from candidates, show all bundles, skip
  - [ ] 7.1.5 Handle user selection and return bundle_id
  - [ ] 7.1.6 Add `@beartype` decorator for runtime type checking

## 8. CLI Integration: --auto-bundle Flag

- [ ] 8.1 Extend `backlog refine` command
  - [ ] 8.1.1 Add `--auto-bundle` flag option
  - [ ] 8.1.2 Add `--auto-accept-bundle` flag option
  - [ ] 8.1.3 Integrate bundle mapping into refinement workflow
  - [ ] 8.1.4 Auto-assign if confidence >= 0.8
  - [ ] 8.1.5 Prompt user if confidence 0.5-0.8
  - [ ] 8.1.6 Require explicit selection if confidence < 0.5

- [ ] 8.2 Extend `backlog import` command
  - [ ] 8.2.1 Add `--auto-bundle` flag option
  - [ ] 8.2.2 Add `--auto-accept-bundle` flag option
  - [ ] 8.2.3 Integrate bundle mapping into import workflow
  - [ ] 8.2.4 Use mapping if `--bundle` not specified

## 9. Source Tracking Extension

- [ ] 9.1 Extend `src/specfact_cli/models/source_tracking.py`
  - [ ] 9.1.1 Add `bundle_id` field (Optional[str])
  - [ ] 9.1.2 Add `mapping_confidence` field (Optional[float])
  - [ ] 9.1.3 Add `mapping_method` field (Optional[str]) - "explicit_label", "historical", "content_similarity", "user_confirmed"
  - [ ] 9.1.4 Add `mapping_timestamp` field (Optional[datetime])
  - [ ] 9.1.5 Ensure backward compatibility (all fields optional)

## 10. OpenSpec Generation Integration

- [ ] 10.1 Extend `_write_openspec_change_from_proposal()` function
  - [ ] 10.1.1 Add `mapping: Optional[BundleMapping]` parameter
  - [ ] 10.1.2 Update source_tracking with mapping metadata
  - [ ] 10.1.3 Include mapping information in proposal.md source tracking section
  - [ ] 10.1.4 Ensure backward compatibility (parameter optional)

## 11. Code Quality and Contract Validation

- [ ] 11.1 Apply code formatting
  - [ ] 11.1.1 Run `hatch run format` to apply black and isort
  - [ ] 11.1.2 Verify all files are properly formatted
- [ ] 11.2 Run linting checks
  - [ ] 11.2.1 Run `hatch run lint` to check for linting errors
  - [ ] 11.2.2 Fix all pylint, ruff, and other linter errors
- [ ] 11.3 Run type checking
  - [ ] 11.3.1 Run `hatch run type-check` to verify type annotations
  - [ ] 11.3.2 Fix all basedpyright type errors
- [ ] 11.4 Verify contract decorators
  - [ ] 11.4.1 Ensure all new public functions have `@beartype` decorators
  - [ ] 11.4.2 Ensure all new public functions have `@icontract` decorators with appropriate `@require`/`@ensure`

## 12. Testing and Validation

- [ ] 12.1 Add new tests
  - [ ] 12.1.1 Add unit tests for BundleMapper (9+ tests: 3 signals × 3 confidence levels)
  - [ ] 12.1.2 Add unit tests for explicit mapping signal (3+ tests)
  - [ ] 12.1.3 Add unit tests for historical mapping signal (3+ tests)
  - [ ] 12.1.4 Add unit tests for content similarity signal (3+ tests)
  - [ ] 12.1.5 Add unit tests for confidence scoring (5+ tests)
  - [ ] 12.1.6 Add unit tests for mapping history persistence (5+ tests)
  - [ ] 12.1.7 Add unit tests for interactive UI (5+ tests: user selections)
  - [ ] 12.1.8 Add integration tests: end-to-end mapping workflow (5+ tests)
- [ ] 12.2 Update existing tests
  - [ ] 12.2.1 Update source_tracking tests to include new mapping fields
  - [ ] 12.2.2 Update OpenSpec generation tests to handle mapping parameter
- [ ] 12.3 Run full test suite of modified tests only
  - [ ] 12.3.1 Run `hatch run smart-test` to execute only the tests that are relevant to the changes
  - [ ] 12.3.2 Verify all modified tests pass (unit, integration, E2E)
- [ ] 12.4 Final validation
  - [ ] 12.4.1 Run `hatch run format` one final time
  - [ ] 12.4.2 Run `hatch run lint` one final time
  - [ ] 12.4.3 Run `hatch run type-check` one final time
  - [ ] 12.4.4 Run `hatch test --cover -v` one final time
  - [ ] 12.4.5 Verify no errors remain (formatting, linting, type-checking, tests)

## 13. OpenSpec Validation

- [ ] 13.1 Validate change proposal
  - [ ] 13.1.1 Run `openspec validate add-bundle-mapping-strategy --strict`
  - [ ] 13.1.2 Fix any validation errors
  - [ ] 13.1.3 Re-run validation until passing

## 14. Pull Request Creation

- [ ] 14.1 Prepare changes for commit
  - [ ] 14.1.1 Ensure all changes are committed: `git add .`
  - [ ] 14.1.2 Commit with conventional message: `git commit -m "feat: add bundle mapping strategy with confidence scoring"`
  - [ ] 14.1.3 Push to remote: `git push origin feature/add-bundle-mapping-strategy`
- [ ] 14.2 Create Pull Request
  - [ ] 14.2.1 Create PR in specfact-cli repository
  - [ ] 14.2.2 Changes are ready for review in the branch
