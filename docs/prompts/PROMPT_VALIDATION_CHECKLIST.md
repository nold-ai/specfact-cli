# Prompt Validation Checklist

This checklist helps ensure prompt templates are correct, aligned with CLI commands, and provide good UX.

## Automated Validation

Run the automated validator:

```bash
# Validate all prompts
hatch run validate-prompts

# Or directly
python tools/validate_prompts.py
```

The validator checks:

- ✅ Required sections present
- ✅ CLI commands match actual CLI
- ✅ CLI enforcement rules present
- ✅ Wait state rules present
- ✅ Dual-stack workflow (if applicable)
- ✅ Consistency across prompts

## Manual Review Checklist

### 1. Structure & Formatting

- [ ] **Frontmatter present**: YAML frontmatter with `description` field
- [ ] **Required sections present**:
  - [ ] `## ⚠️ CRITICAL: CLI Usage Enforcement`
  - [ ] `## ⏸️ Wait States: User Input Required`
  - [ ] `## Goal`
  - [ ] `## Operating Constraints`
- [ ] **Markdown formatting**: Proper headers, code blocks, lists
- [ ] **$ARGUMENTS placeholder**: Present in "User Input" section

### 2. CLI Alignment

- [ ] **CLI command matches**: The command in the prompt matches the actual CLI command
- [ ] **CLI enforcement rules present**:
  - [ ] "ALWAYS execute CLI first"
  - [ ] "NEVER create YAML/JSON directly"
  - [ ] "NEVER bypass CLI validation"
  - [ ] "Use CLI output as grounding"
  - [ ] "NEVER manipulate internal code" (explicitly forbids direct Python code manipulation)
  - [ ] "No internal knowledge required" (explicitly states that internal implementation details should not be needed)
- [ ] **Available CLI commands documented**: Prompt lists available CLI commands for plan updates (e.g., `update-idea`, `update-feature`, `add-feature`, `add-story`)
- [ ] **FORBIDDEN examples present**: Prompt shows examples of what NOT to do (direct code manipulation)
- [ ] **CORRECT examples present**: Prompt shows examples of what TO do (using CLI commands)
- [ ] **Command examples**: Examples show actual CLI usage with correct flags
- [ ] **Flag documentation**: All flags are documented with defaults and descriptions
- [ ] **Filter options documented** (for `plan select`): `--current`, `--stages`, `--last`, `--non-interactive` flags are documented with use cases and examples
- [ ] **Positional vs option arguments**: Correctly distinguishes between positional arguments and `--option` flags (e.g., `specfact plan select 20` not `specfact plan select --plan 20`)
- [ ] **Boolean flags documented correctly**: Boolean flags use `--flag/--no-flag` syntax, not `--flag true/false`
  - ❌ **WRONG**: `--draft true` or `--draft false` (Typer boolean flags don't accept values)
  - ✅ **CORRECT**: `--draft` (sets True) or `--no-draft` (sets False) or omit (leaves unchanged)
- [ ] **Entry point flag documented** (for `import from-code`): `--entry-point` flag is documented with use cases (multi-project repos, partial analysis, incremental modernization)

### 3. Wait States & User Input

- [ ] **Wait state rules present**:
  - [ ] "Never assume"
  - [ ] "Never continue"
  - [ ] "Be explicit"
  - [ ] "Provide options"
- [ ] **Explicit wait markers**: `[WAIT FOR USER RESPONSE - DO NOT CONTINUE]` present where needed
- [ ] **Missing argument handling**: Clear instructions for what to do when arguments are missing
- [ ] **User prompts**: Examples show how to ask for user input
- [ ] **No assumptions**: Prompt doesn't allow LLM to assume values and continue

### 4. Flow Logic

- [ ] **Dual-stack workflow** (if applicable):
  - [ ] Phase 1: CLI Grounding documented
  - [ ] Phase 2: LLM Enrichment documented
    - [ ] **CRITICAL**: Stories are required for features in enrichment reports
    - [ ] Story format example provided in prompt
    - [ ] Explanation: Stories are required for promotion validation
  - [ ] Phase 3: CLI Artifact Creation documented
  - [ ] Enrichment report location specified (`.specfact/reports/enrichment/`)
- [ ] **Auto-enrichment workflow** (for `plan review`):
  - [ ] `--auto-enrich` flag documented with when to use it
  - [ ] LLM reasoning guidance for detecting when enrichment is needed
  - [ ] Post-enrichment analysis steps documented
  - [ ] **MANDATORY automatic refinement**: LLM must automatically refine generic criteria with code-specific details after auto-enrichment
  - [ ] Two-phase enrichment strategy (automatic + LLM-enhanced refinement)
  - [ ] Continuous improvement loop documented
  - [ ] Examples of enrichment output and refinement process
  - [ ] **Generic criteria detection**: Instructions to identify and replace generic patterns ("interact with the system", "works correctly")
  - [ ] **Code-specific criteria generation**: Instructions to research codebase and create testable criteria with method names, parameters, return values
- [ ] **Feature deduplication** (for `sync`, `plan review`, `import from-code`):
  - [ ] **Automated deduplication documented**: CLI automatically deduplicates features using normalized key matching
  - [ ] **Deduplication scope explained**:
    - [ ] Exact normalized key matches (e.g., `FEATURE-001` vs `001_FEATURE_NAME`)
    - [ ] Prefix matches for Spec-Kit features (e.g., `FEATURE-IDEINTEGRATION` vs `041_IDE_INTEGRATION_SYSTEM`)
    - [ ] Only matches when at least one key has numbered prefix (Spec-Kit origin) to avoid false positives
  - [ ] **LLM semantic deduplication guidance**: Instructions for LLM to identify semantic/logical duplicates that automated deduplication might miss
    - [ ] Review feature titles and descriptions for semantic similarity
    - [ ] Identify features that represent the same functionality with different names
    - [ ] Suggest consolidation when multiple features cover the same code/functionality
    - [ ] Use `specfact plan update-feature` or `specfact plan add-feature` to consolidate
  - [ ] **Deduplication output**: CLI shows "✓ Removed N duplicate features" - LLM should acknowledge this
  - [ ] **Post-deduplication review**: LLM should review remaining features for semantic duplicates
- [ ] **Execution steps**: Clear, sequential steps
- [ ] **Error handling**: Instructions for handling errors
- [ ] **Validation**: CLI validation steps documented
- [ ] **Coverage validation** (for `plan promote`): Documentation of coverage status checks (critical vs important categories)
- [ ] **Copilot-friendly formatting** (if applicable): Instructions for formatting output as Markdown tables for better readability
- [ ] **Interactive workflows** (if applicable): Support for "details" requests and other interactive options (e.g., "20 details" for plan selection)

### 5. Consistency

- [ ] **Consistent terminology**: Uses same terms as other prompts
- [ ] **Consistent formatting**: Same markdown style as other prompts
- [ ] **Consistent structure**: Same section order as other prompts
- [ ] **Consistent examples**: Examples follow same pattern

### 6. UX & Clarity

- [ ] **Clear goal**: Goal section clearly explains what the command does
- [ ] **Clear constraints**: Operating constraints are explicit
- [ ] **Helpful examples**: Examples are realistic and helpful
- [ ] **Error messages**: Shows what happens if rules aren't followed
- [ ] **User-friendly**: Language is clear and not overly technical

## Testing with Copilot

### Step 1: Run Automated Validation

```bash
hatch run validate-prompts
```

All prompts should pass with 0 errors.

### Step 2: Manual Testing

For each prompt, test the following scenarios:

#### Scenario 1: Missing Required Arguments

1. Invoke the slash command without required arguments
2. Verify the LLM:
   - ✅ Asks for missing arguments
   - ✅ Shows `[WAIT FOR USER RESPONSE - DO NOT CONTINUE]`
   - ✅ Does NOT assume values and continue
   - ✅ Provides helpful examples or defaults

#### Scenario 2: All Arguments Provided

1. Invoke the slash command with all required arguments
2. Verify the LLM:
   - ✅ Executes the CLI command immediately
   - ✅ Uses the provided arguments correctly
   - ✅ Uses boolean flags correctly (`--draft` not `--draft true`)
   - ✅ Uses `--entry-point` when user specifies partial analysis
   - ✅ Does NOT create artifacts directly
   - ✅ Parses CLI output correctly

#### Scenario 3: Dual-Stack Workflow (for import-from-code)

1. Invoke `/specfact-import-from-code` without `--enrichment`
2. Verify the LLM:
   - ✅ Executes Phase 1: CLI Grounding
   - ✅ Reads CLI-generated artifacts
   - ✅ Generates enrichment report (Phase 2)
     - ✅ **CRITICAL**: Each missing feature includes at least one story
     - ✅ Stories follow the format shown in prompt example
   - ✅ Saves enrichment to `.specfact/reports/enrichment/` with correct naming
   - ✅ Executes Phase 3: CLI Artifact Creation with `--enrichment` flag
   - ✅ Final artifacts are CLI-generated
   - ✅ Enriched plan can be promoted (features have stories)

#### Scenario 4: Plan Review Workflow (for plan-review)

1. Invoke `/specfact-plan-review` with a plan bundle
2. Verify the LLM:
   - ✅ Executes `specfact plan review` CLI command
   - ✅ Parses CLI output for ambiguity findings
   - ✅ Waits for user input when questions are asked
   - ✅ Does NOT create clarifications directly in YAML
   - ✅ Uses CLI to save updated plan bundle after each answer
   - ✅ Follows interactive Q&A workflow correctly

#### Scenario 4a: Plan Review with Auto-Enrichment (for plan-review)

1. Invoke `/specfact-plan-review` with a plan bundle that has vague acceptance criteria or incomplete requirements
2. Verify the LLM:
   - ✅ **Detects need for enrichment**: Recognizes vague patterns ("is implemented", "System MUST Helper class", generic tasks)
   - ✅ **Suggests or uses `--auto-enrich`**: Either suggests using `--auto-enrich` flag or automatically uses it based on plan quality indicators
   - ✅ **Executes enrichment**: Runs `specfact plan review --auto-enrich --plan <path>`
   - ✅ **Parses enrichment results**: Captures enrichment summary (features updated, stories updated, acceptance criteria enhanced, etc.)
   - ✅ **Analyzes enrichment quality**: Uses LLM reasoning to review what was enhanced
   - ✅ **Identifies generic patterns**: Finds placeholder text like "interact with the system" that needs refinement
   - ✅ **Proposes specific refinements**: Suggests domain-specific improvements using CLI commands
   - ✅ **Executes refinements**: Uses `specfact plan update-feature` to refine generic improvements
   - ✅ **Re-runs review**: Executes `specfact plan review` again to verify improvements
3. Test with explicit enrichment request (e.g., "enrich the plan"):
   - ✅ Uses `--auto-enrich` flag immediately
   - ✅ Reviews enrichment results
   - ✅ Suggests further improvements if needed

#### Scenario 5: Plan Selection Workflow (for plan-select)

1. Invoke `/specfact-plan-select` without arguments
2. Verify the LLM:
   - ✅ Executes `specfact plan select` CLI command
   - ✅ Formats plan list as copilot-friendly Markdown table (not Rich table)
   - ✅ Provides selection options (number, "number details", "q" to quit)
   - ✅ Waits for user response with `[WAIT FOR USER RESPONSE - DO NOT CONTINUE]`
3. Request plan details (e.g., "20 details"):
   - ✅ Loads plan bundle YAML file
   - ✅ Extracts and displays detailed information (idea, themes, top features, business context)
   - ✅ Asks if user wants to select the plan
   - ✅ Waits for user confirmation
4. Select a plan (e.g., "20" or "y" after details):
   - ✅ Uses **positional argument** syntax: `specfact plan select 20` (NOT `--plan 20`)
   - ✅ Confirms selection with CLI output
   - ✅ Does NOT create config.yaml directly
5. Test filter options:
   - ✅ Uses `--current` flag to show only active plan: `specfact plan select --current`
   - ✅ Uses `--stages` flag to filter by stages: `specfact plan select --stages draft,review`
   - ✅ Uses `--last N` flag to show recent plans: `specfact plan select --last 5`
6. Test non-interactive mode (CI/CD):
   - ✅ Uses `--non-interactive` flag with `--current`: `specfact plan select --non-interactive --current`
   - ✅ Uses `--non-interactive` flag with `--last 1`: `specfact plan select --non-interactive --last 1`
   - ✅ Handles error when multiple plans match filters in non-interactive mode
   - ✅ Does NOT prompt for input when `--non-interactive` is used

#### Scenario 6: Plan Promotion with Coverage Validation (for plan-promote)

1. Invoke `/specfact-plan-promote` with a plan that has missing critical categories
2. Verify the LLM:
   - ✅ Executes `specfact plan promote --stage review --validate` CLI command
   - ✅ Parses CLI output showing coverage validation errors
   - ✅ Shows which critical categories are Missing
   - ✅ Suggests running `specfact plan review` to resolve ambiguities
   - ✅ Does NOT attempt to bypass validation by creating artifacts directly
   - ✅ Waits for user decision (use `--force` or run `plan review` first)
3. Invoke promotion with `--force` flag:
   - ✅ Uses `--force` flag correctly: `specfact plan promote --stage review --force`
   - ✅ Explains that `--force` bypasses validation (not recommended)
   - ✅ Does NOT create plan bundle directly

#### Scenario 7: Error Handling

1. Invoke command with invalid arguments or paths
2. Verify the LLM:
   - ✅ Shows CLI error messages
   - ✅ Doesn't try to fix errors by creating artifacts
   - ✅ Asks user for correct input
   - ✅ Waits for user response

### Step 3: Review Output

After testing, review:

- [ ] **CLI commands executed**: All commands use `specfact` CLI
- [ ] **Artifacts CLI-generated**: No YAML/JSON created directly by LLM
- [ ] **Wait states respected**: LLM waits for user input when needed
- [ ] **Enrichment workflow** (if applicable): Three-phase workflow followed correctly
- [ ] **Review workflow** (if applicable): Interactive Q&A workflow followed correctly, clarifications saved via CLI
- [ ] **Auto-enrichment workflow** (if applicable):
  - [ ] LLM detects when enrichment is needed (vague criteria, incomplete requirements, generic tasks)
  - [ ] Uses `--auto-enrich` flag appropriately
  - [ ] Analyzes enrichment results with reasoning
  - [ ] Proposes and executes specific refinements using CLI commands
  - [ ] Iterates until plan quality meets standards
- [ ] **Selection workflow** (if applicable): Copilot-friendly table formatting, details option, correct CLI syntax (positional arguments), filter options (`--current`, `--stages`, `--last`), non-interactive mode (`--non-interactive`)
- [ ] **Promotion workflow** (if applicable): Coverage validation respected, suggestions to run `plan review` when categories are Missing
- [ ] **Error handling**: Errors handled gracefully without assumptions

## Common Issues to Watch For

### ❌ LLM Creates Artifacts Directly

**Symptom**: LLM generates YAML/JSON instead of using CLI

**Fix**: Strengthen CLI enforcement section, add more examples of what NOT to do

### ❌ LLM Assumes Values

**Symptom**: LLM continues without waiting for user input

**Fix**: Add more explicit wait state markers, show more examples of correct wait behavior

### ❌ Wrong CLI Command

**Symptom**: LLM uses incorrect command or flags

**Fix**: Update command examples, verify CLI help text matches prompt

### ❌ Wrong Argument Format (Positional vs Option)

**Symptom**: LLM uses `--option` flag when command expects positional argument (e.g., `specfact plan select --plan 20` instead of `specfact plan select 20`)

**Fix**:

- Verify actual CLI command signature (use `specfact <command> --help`)
- Update prompt to explicitly state positional vs option arguments
- Add examples showing correct syntax
- Add warning about common mistakes (e.g., "NOT `specfact plan select --plan 20` (this will fail)")

### ❌ Wrong Boolean Flag Usage

**Symptom**: LLM uses `--flag true` or `--flag false` when flag is boolean (e.g., `--draft true` instead of `--draft`)

**Fix**:

- Verify actual CLI command signature (use `specfact <command> --help`)
- Update prompt to explicitly state boolean flag syntax: `--flag` sets True, `--no-flag` sets False, omit to leave unchanged
- Add examples showing correct syntax: `--draft` (not `--draft true`)
- Add warning about common mistakes: "NOT `--draft true` (this will fail - Typer boolean flags don't accept values)"
- Document when to use `--no-flag` vs omitting the flag entirely

### ❌ Missing Enrichment Workflow

**Symptom**: LLM doesn't follow three-phase workflow for import-from-code

**Fix**: Strengthen dual-stack workflow section, add more explicit phase markers

### ❌ Missing Coverage Validation

**Symptom**: LLM promotes plans without checking coverage status, or doesn't suggest running `plan review` when categories are Missing

**Fix**:

- Update prompt to document coverage validation clearly
- Add examples showing validation errors
- Emphasize that `--force` should only be used when explicitly requested
- Document critical vs important categories

### ❌ Missing Auto-Enrichment

**Symptom**: LLM doesn't detect or use `--auto-enrich` flag when plan has vague acceptance criteria or incomplete requirements

**Fix**:

- Update prompt to document `--auto-enrich` flag and when to use it
- Add LLM reasoning guidance for detecting enrichment needs
- Document decision flow for when to suggest or use auto-enrichment
- Add examples of enrichment output and refinement process
- Emphasize two-phase approach: automatic enrichment + LLM-enhanced refinement

## Validation Commands

```bash
# Run automated validation
hatch run validate-prompts

# Run unit tests for validation
hatch test tests/unit/prompts/test_prompt_validation.py -v

# Check specific prompt
python tools/validate_prompts.py --prompt specfact-import-from-code
```

## Continuous Improvement

After each prompt update:

1. Run automated validation
2. Test with Copilot in real scenarios
3. Document any issues found
4. Update checklist based on learnings
5. Share findings with team

## Available Prompts

The following prompts are available for SpecFact CLI commands:

### Plan Management

- `specfact-plan-init.md` - Initialize a new development plan bundle
- `specfact-plan-add-feature.md` - Add a new feature to an existing plan
- `specfact-plan-add-story.md` - Add a new story to a feature
- `specfact-plan-update-idea.md` - Update idea section metadata
- `specfact-plan-update-feature.md` - Update an existing feature's metadata
- `specfact-plan-compare.md` - Compare manual and auto-derived plans
- `specfact-plan-promote.md` - Promote a plan bundle through stages
- `specfact-plan-review.md` - Review plan bundle to identify ambiguities
- `specfact-plan-select.md` - Select active plan from available bundles

### Import & Sync

- `specfact-import-from-code.md` - Import codebase structure (brownfield)
- `specfact-sync.md` - Synchronize Spec-Kit artifacts and repository changes

### Constitution Management

- Constitution commands are integrated into `specfact-sync.md` and `specfact-import-from-code.md` workflows
- Constitution bootstrap/enrich/validate commands are suggested automatically when constitution is missing or minimal

### Validation & Enforcement

- `specfact-enforce.md` - Configure quality gates and enforcement modes
- `specfact-repro.md` - Run validation suite for reproducibility

---

**Last Updated**: 2025-11-20  
**Version**: 1.9

## Changelog

### Version 1.9 (2025-11-20)

- Added filter options validation for `plan select` command (`--current`, `--stages`, `--last`)
- Added non-interactive mode validation for `plan select` command (`--non-interactive`)
- Updated Scenario 5 to include filter options and non-interactive mode testing
- Added filter options documentation requirements to CLI alignment checklist
- Updated selection workflow checklist to include filter options and non-interactive mode

### Version 1.8 (2025-11-20)

- Added feature deduplication validation checks
- Added automated deduplication documentation requirements (exact matches, prefix matches for Spec-Kit features)
- Added LLM semantic deduplication guidance (identifying semantic/logical duplicates)
- Added deduplication workflow to testing scenarios
- Added common issue: Missing Semantic Deduplication
- Updated Scenario 2 to verify deduplication acknowledgment and semantic review

### Version 1.7 (2025-11-19)

- Added boolean flag validation checks
- Added `--entry-point` flag documentation requirements
- Added common issue: Wrong Boolean Flag Usage
- Updated Scenario 2 to verify boolean flag usage
- Added checks for `--entry-point` usage in partial analysis scenarios

### Version 1.6 (2025-11-18)

- Added constitution management commands integration
- Updated sync prompt to include constitution bootstrap/enrich/validate commands
- Added constitution bootstrap suggestion workflow for brownfield projects
- Updated prerequisites section to document constitution command options

### Version 1.5 (2025-11-18)

- Added auto-enrichment workflow validation for `plan review` command
- Added Scenario 4a: Plan Review with Auto-Enrichment
- Added checks for enrichment detection, execution, and refinement
- Added common issue: Missing Auto-Enrichment
- Updated flow logic section to include auto-enrichment workflow documentation requirements
