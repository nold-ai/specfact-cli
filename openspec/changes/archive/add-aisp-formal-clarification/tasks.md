## 1. Git Workflow

- [ ] 1.1 Create git branch `feature/add-aisp-formal-clarification` from `dev` branch
  - [ ] 1.1.1 Ensure we're on dev and up to date: `git checkout dev && git pull origin dev`
  - [ ] 1.1.2 Create branch: `git checkout -b feature/add-aisp-formal-clarification`
  - [ ] 1.1.3 Verify branch was created: `git branch --show-current`

## 2. AISP Data Models and Parser

- [ ] 2.1 Create AISP data models
  - [ ] 2.1.1 Create `src/specfact_cli/models/aisp.py` with `AispProofBlock`, `AispBinding`, `AispParseResult`, `AispDecision`, `AispOutcome` models
  - [ ] 2.1.2 Add Pydantic models with proper type hints and field validators
  - [ ] 2.1.3 Add `@beartype` decorators for runtime type checking
  - [ ] 2.1.4 Add `@icontract` decorators with `@require`/`@ensure` contracts
  - [ ] 2.1.5 Add docstrings following Google style guide

- [ ] 2.2 Create AISP parser
  - [ ] 2.2.1 Create `src/specfact_cli/parsers/aisp.py` for parsing AISP blocks from project bundle storage
  - [ ] 2.2.2 Implement AISP file reading from `.specfact/projects/<bundle>/aisp/` directory
  - [ ] 2.2.3 Implement proof ID extraction (format: `proof[id]:`)
  - [ ] 2.2.4 Implement input schema parsing
  - [ ] 2.2.5 Implement decision tree parsing (choice points, branches)
  - [ ] 2.2.6 Implement outcome parsing (success/failure)
  - [ ] 2.2.7 Implement invariant parsing
  - [ ] 2.2.8 Add `@beartype` decorators for runtime type checking
  - [ ] 2.2.9 Add `@icontract` decorators with `@require`/`@ensure` contracts
  - [ ] 2.2.10 Add error handling and error collection in `AispParseResult`

- [ ] 2.3 Create AISP validator
  - [ ] 2.3.1 Create `src/specfact_cli/validators/aisp_schema.py` for syntax and binding validation
  - [ ] 2.3.2 Implement proof ID uniqueness validation within spec
  - [ ] 2.3.3 Implement requirement binding validation (proof IDs referenced by requirements)
  - [ ] 2.3.4 Implement coverage gap detection (requirements without proofs, orphaned proofs)
  - [ ] 2.3.5 Implement AISP v5.1 syntax validation (reference: <https://github.com/bar181/aisp-open-core/blob/main/AI_GUIDE.md>)
  - [ ] 2.3.6 Add `@beartype` decorators for runtime type checking
  - [ ] 2.3.7 Add `@icontract` decorators with `@require`/`@ensure` contracts

## 3. Adapter Integration

- [ ] 3.1 Extend OpenSpec adapter for AISP generation
  - [ ] 3.1.1 Modify `src/specfact_cli/adapters/openspec.py` to generate AISP blocks from requirements
  - [ ] 3.1.2 Add AISP generation during spec import/sync
  - [ ] 3.1.3 Add AISP generation during change proposal processing
  - [ ] 3.1.4 Store generated AISP blocks in `.specfact/projects/<bundle>/aisp/` directory
  - [ ] 3.1.5 Map AISP blocks to requirement IDs (no modification of source spec files)
  - [ ] 3.1.6 Support cross-repository AISP generation via `external_base_path`
  - [ ] 3.1.7 Add `@beartype` decorators for runtime type checking
  - [ ] 3.1.8 Add `@icontract` decorators with `@require`/`@ensure` contracts

- [ ] 3.2 Extend Spec-Kit adapter for AISP generation
  - [ ] 3.2.1 Modify `src/specfact_cli/adapters/speckit.py` to generate AISP blocks from spec.md requirements
  - [ ] 3.2.2 Add AISP generation from plan.md requirements
  - [ ] 3.2.3 Store generated AISP blocks in project bundle (not in exported spec.md)
  - [ ] 3.2.4 Maintain proof IDs and bindings in project bundle
  - [ ] 3.2.5 Ensure source spec files remain unchanged (no AISP notation)
  - [ ] 3.2.6 Add `@beartype` decorators for runtime type checking
  - [ ] 3.2.7 Add `@icontract` decorators with `@require`/`@ensure` contracts

## 4. CLI Commands

- [ ] 4.1 Extend validate command with AISP support
  - [ ] 4.1.1 Modify `src/specfact_cli/commands/validate.py` to add `--aisp` flag
  - [ ] 4.1.2 Implement AISP block loading from project bundle when `--aisp` flag is used
  - [ ] 4.1.3 Add `--aisp --against-code` flag for contract matching
  - [ ] 4.1.4 Implement contract-to-AISP comparison logic
  - [ ] 4.1.5 Add deviation reporting (extra branches, missing invariants, different outcomes)
  - [ ] 4.1.6 Integrate AISP validation reports into existing validate output
  - [ ] 4.1.7 Add `@beartype` decorators for runtime type checking
  - [ ] 4.1.8 Add `@icontract` decorators with `@require`/`@ensure` contracts

- [ ] 4.2 Create clarify command
  - [ ] 4.2.1 Create `src/specfact_cli/commands/clarify.py` for clarification workflow
  - [ ] 4.2.2 Implement `specfact clarify requirement <requirement-id>` command
  - [ ] 4.2.3 Generate structured prompt based on requirement content
  - [ ] 4.2.4 Create YAML response template for AISP block structure
  - [ ] 4.2.5 Generate/update AISP block and store in `.specfact/projects/<bundle>/aisp/`
  - [ ] 4.2.6 Clarify vague/ambiguous elements in requirement text
  - [ ] 4.2.7 Add `@beartype` decorators for runtime type checking
  - [ ] 4.2.8 Add `@icontract` decorators with `@require`/`@ensure` contracts

- [ ] 4.3 Add slash command prompts for AISP compilation and AI LLM consumption
  - [ ] 4.3.1 Create `/specfact.compile-aisp` slash command prompt template
    - [ ] 4.3.1.1 Instruct AI LLM to update internal AISP spec from available spec
    - [ ] 4.3.1.2 Instruct AI LLM to clarify vague/ambiguous elements
    - [ ] 4.3.1.3 Instruct AI LLM to execute AISP spec instead of markdown spec
  - [ ] 4.3.2 Create `/specfact.update-aisp` slash command prompt template
    - [ ] 4.3.2.1 Detect spec changes and update corresponding AISP blocks
    - [ ] 4.3.2.2 Flag vague/ambiguous elements for clarification
  - [ ] 4.3.3 Reference AISP v5.1 specification in prompt templates
  - [ ] 4.3.4 Implement AISP loading from project bundle in slash commands
  - [ ] 4.3.5 Store prompt templates in `resources/templates/slash-commands/`
  - [ ] 4.3.6 Document slash command usage in CLI documentation

## 5. AISP Proof Artifact Storage in Project Bundles

- [ ] 5.1 Implement proof artifact storage in project bundles
  - [ ] 5.1.1 Create `.specfact/projects/<bundle>/aisp/` directory structure support
  - [ ] 5.1.2 Implement proof artifact file storage (e.g., `proof-<requirement-id>.aisp.md`)
  - [ ] 5.1.3 Implement proof ID to requirement ID mapping in project bundle metadata
  - [ ] 5.1.4 Ensure storage does not conflict with existing project bundle structure
  - [ ] 5.1.5 Add AISP storage to `src/specfact_cli/utils/bundle_loader.py`

- [ ] 5.2 Implement AISP as internal representation
  - [ ] 5.2.1 Ensure AISP blocks are not visible in source spec files
  - [ ] 5.2.2 Ensure AISP blocks are accessible only through SpecFact CLI
  - [ ] 5.2.3 Implement AISP loading from project bundle for slash commands
  - [ ] 5.2.4 Ensure developers work with natural language specs (no AISP exposure)

## 6. Templates and Examples

- [ ] 6.1 Create AISP block templates
  - [ ] 6.1.1 Create `resources/templates/aisp/` directory
  - [ ] 6.1.2 Add template for authentication pattern
  - [ ] 6.1.3 Add template for payment processing pattern
  - [ ] 6.1.4 Add template for state machine pattern
  - [ ] 6.1.5 Add template for generic decision tree pattern

- [ ] 6.2 Create integration examples
  - [ ] 6.2.1 Create example OpenSpec spec with embedded AISP blocks
  - [ ] 6.2.2 Create example Spec-Kit spec with AISP blocks
  - [ ] 6.2.3 Create example showing AISP block in change proposal
  - [ ] 6.2.4 Store examples in `docs/examples/aisp-integration/`

## 7. Documentation

- [ ] 7.1 Create AISP integration guide
  - [ ] 7.1.1 Create `docs/guides/aisp-integration.md`
  - [ ] 7.1.2 Document AISP block syntax and structure
  - [ ] 7.1.3 Document when to use AISP blocks (heuristics)
  - [ ] 7.1.4 Document authoring guidelines
  - [ ] 7.1.5 Document integration with OpenSpec and Spec-Kit workflows

- [ ] 7.2 Update existing documentation
  - [ ] 7.2.1 Update OpenSpec adapter documentation with AISP support
  - [ ] 7.2.2 Update Spec-Kit adapter documentation with AISP support
  - [ ] 7.2.3 Update validate command documentation with `--aisp` flags
  - [ ] 7.2.4 Add clarify command documentation
  - [ ] 7.2.5 Add slash command documentation for AISP conversion

## 8. Code Quality and Contract Validation

- [ ] 8.1 Apply code formatting
  - [ ] 8.1.1 Run `hatch run format` to apply black and isort
  - [ ] 8.1.2 Verify all files are properly formatted

- [ ] 8.2 Run linting checks
  - [ ] 8.2.1 Run `hatch run lint` to check for linting errors
  - [ ] 8.2.2 Fix all pylint, ruff, and other linter errors

- [ ] 8.3 Run type checking
  - [ ] 8.3.1 Run `hatch run type-check` to verify type annotations
  - [ ] 8.3.2 Fix all basedpyright type errors

- [ ] 8.4 Verify contract decorators
  - [ ] 8.4.1 Ensure all new public functions have `@beartype` decorators
  - [ ] 8.4.2 Ensure all new public functions have `@icontract` decorators with appropriate `@require`/`@ensure`

## 9. Testing and Validation

- [ ] 9.1 Add unit tests for AISP parser
  - [ ] 9.1.1 Create `tests/unit/parsers/test_aisp.py`
  - [ ] 9.1.2 Test fenced code block detection
  - [ ] 9.1.3 Test proof ID extraction
  - [ ] 9.1.4 Test input schema parsing
  - [ ] 9.1.5 Test decision tree parsing
  - [ ] 9.1.6 Test outcome parsing
  - [ ] 9.1.7 Test invariant parsing
  - [ ] 9.1.8 Test error handling

- [ ] 9.2 Add unit tests for AISP validator
  - [ ] 9.2.1 Create `tests/unit/validators/test_aisp_schema.py`
  - [ ] 9.2.2 Test proof ID uniqueness validation
  - [ ] 9.2.3 Test requirement binding validation
  - [ ] 9.2.4 Test coverage gap detection
  - [ ] 9.2.5 Test AISP v5.1 syntax validation

- [ ] 9.3 Add unit tests for AISP data models
  - [ ] 9.3.1 Create `tests/unit/models/test_aisp.py`
  - [ ] 9.3.2 Test `AispProofBlock` model creation and validation
  - [ ] 9.3.3 Test `AispBinding` model creation and validation
  - [ ] 9.3.4 Test `AispParseResult` model creation and validation
  - [ ] 9.3.5 Test `AispDecision` and `AispOutcome` models

- [ ] 9.4 Add integration tests for adapter AISP support
  - [ ] 9.4.1 Create `tests/integration/adapters/test_openspec_aisp.py`
  - [ ] 9.4.2 Test OpenSpec adapter AISP block detection
  - [ ] 9.4.3 Test OpenSpec adapter AISP block parsing
  - [ ] 9.4.4 Test cross-repository AISP block support
  - [ ] 9.4.5 Create `tests/integration/adapters/test_speckit_aisp.py`
  - [ ] 9.4.6 Test Spec-Kit adapter AISP block reading
  - [ ] 9.4.7 Test Spec-Kit adapter AISP block preservation on export

- [ ] 9.5 Add integration tests for CLI commands
  - [ ] 9.5.1 Create `tests/integration/commands/test_validate_aisp.py`
  - [ ] 9.5.2 Test `specfact validate --aisp` command
  - [ ] 9.5.3 Test `specfact validate --aisp --against-code` command
  - [ ] 9.5.4 Create `tests/integration/commands/test_clarify.py`
  - [ ] 9.5.5 Test `specfact clarify requirement <requirement-id>` command

- [ ] 9.6 Run full test suite
  - [ ] 9.6.1 Run `hatch run smart-test` to execute tests for modified files
  - [ ] 9.6.2 Verify all modified tests pass (unit, integration)

- [ ] 9.7 Final validation
  - [ ] 9.7.1 Run `hatch run format` one final time
  - [ ] 9.7.2 Run `hatch run lint` one final time
  - [ ] 9.7.3 Run `hatch run type-check` one final time
  - [ ] 9.7.4 Run `hatch run contract-test` for contract validation
  - [ ] 9.7.5 Run `hatch test --cover -v` one final time
  - [ ] 9.7.6 Verify no errors remain (formatting, linting, type-checking, tests)

## 10. OpenSpec Validation

- [ ] 10.1 Validate OpenSpec change proposal
  - [ ] 10.1.1 Run `openspec validate add-aisp-formal-clarification --strict`
  - [ ] 10.1.2 Fix any validation errors
  - [ ] 10.1.3 Re-run validation until passing

- [ ] 10.2 Markdown linting
  - [ ] 10.2.1 Run markdownlint on all markdown files in change directory
  - [ ] 10.2.2 Fix any linting errors
  - [ ] 10.2.3 Verify all markdown files pass linting

## 11. Pull Request Creation

- [ ] 11.1 Prepare changes for commit
  - [ ] 11.1.1 Ensure all changes are committed: `git add .`
  - [ ] 11.1.2 Commit with conventional message: `git commit -m "feat: add AISP formal clarification to Spec-Kit and OpenSpec workflows"`
  - [ ] 11.1.3 Push to remote: `git push origin feature/add-aisp-formal-clarification`

- [ ] 11.2 Create Pull Request
  - [ ] 11.2.1 Create PR from `feature/add-aisp-formal-clarification` to `dev` branch
  - [ ] 11.2.2 Use PR template with proper description
  - [ ] 11.2.3 Link to OpenSpec change proposal
  - [ ] 11.2.4 Verify PR is ready for review
