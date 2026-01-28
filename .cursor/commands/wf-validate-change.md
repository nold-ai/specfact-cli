---
name: /wf-validate-change
id: wf-validate-change
category: Workflow
description: Validate OpenSpec change proposal for breaking changes and dependencies before implementation.
---

<!-- WORKFLOW:START -->
**Purpose**

Perform a dry-run validation of an OpenSpec change proposal to detect breaking changes, verify dependencies, and ensure codebase integrity before implementation. Creates a validation report for audit purposes.

**When to use:** Before implementing an OpenSpec change proposal, especially when the change involves code modifications, interface changes, or contract updates that might affect other components.

**Quick:** `/wf-validate-change <change-id>` or `/wf-validate-change` (interactive selection)

**Guardrails**

- Never modify the actual codebase during validation - only work in `/tmp` directories
- Focus on interface/contract/parameter analysis, not implementation details
- Identify breaking changes, not style or formatting issues
- Always create CHANGE_VALIDATION.md for audit trail
- Ask for user confirmation before extending change scope or rejecting proposals

**Workflow Steps**

### Step 1: Change Selection and Discovery

**If change ID provided in user input:**

1. Parse the change ID from user input (e.g., `improve-documentation-structure`)
2. Resolve to change directory: `openspec/changes/<change-id>/`
3. Verify change directory exists and contains `proposal.md`
4. If not found, search for similar changes and suggest alternatives

**If no change ID provided:**

1. Search for active changes in workspace:
   - Run: `openspec list --json` to get active changes
   - Parse JSON to extract change information
   - Display numbered list of changes with:
     - Change ID
     - Schema (from JSON, default "spec-driven")
     - Status (from proposal.md or JSON)
     - Brief description (from proposal.md summary)
     - Last modified date (if available)
2. Prompt user: "Select change to validate (enter number, or provide change-id):"
3. Parse selection and resolve to change directory
4. Verify change directory exists and is readable

**Output:** Change ID, path to change directory

### Step 2: Read and Parse Change Proposal

**2.1: Check Change Status and Read Artifacts**

1. **Read openspec/config.yaml for validation rules:**
   - Read `openspec/config.yaml` to understand:
     - Project context (tech stack, constraints, architecture patterns)
     - Per-artifact rules (proposal, specs, design, tasks)
   - Use these rules to validate artifact compliance

2. **Check change status using OPSX pattern:**

   ```bash
   openspec status --change "<change-id>" --json
   ```

   - Parse JSON to understand:
     - `schemaName`: The workflow being used (e.g., "spec-driven")
     - `artifacts`: Array of artifacts with their status ("done", "ready", "blocked")
     - `isComplete`: Boolean indicating if all artifacts are complete
   - Verify all required artifacts exist before validation

3. **Get artifact context using OPSX pattern:**

   ```bash
   openspec instructions apply --change "<change-id>" --json
   ```

   - This returns context files to read
   - For spec-driven schema: proposal, specs, design, tasks

4. **Verify proposal.md format (per config.yaml rules):**
   - Check title format: Must be `# Change: [Brief description]` (not `# [Title]` or `# Change:[Title]` without space)
   - Check required sections: Must have `## Why`, `## What Changes`, `## Capabilities`, `## Impact` (per config.yaml)
   - Check "What Changes" format: Must use bullet list with NEW/EXTEND/MODIFY markers
   - Check "Capabilities" section: Critical - each capability listed will need a spec file
   - Check "Impact" format: Must list Affected specs, Affected code, Integration points
   - If format issues found, note them for reporting

5. **Read `proposal.md`:**
   - Extract: summary (from "Why" section), rationale (from "Why" section), scope (from "What Changes" section), capabilities (from "Capabilities" section), affected files/modules
   - Identify: breaking changes markers, dependencies
   - Note: target repository, Source Tracking section (if present)

6. **Verify tasks.md format (per config.yaml rules):**
   - Check section headers: Must use hierarchical numbered format (`## 1.`, `## 2.`, etc., not `## Task 1:` or `## Phase 1:`)
   - Check task format: Must use `- [ ] 1.1 [Description]` (not `- Task 1:` or `- [ ] Task 1:`)
   - Check sub-task format: Must use `- [ ] 1.1.1 [Description]` (indented, not `- [ ] 1.1.1:` without description)
   - Verify tasks follow config.yaml rules: 2-hour maximum chunks, contract decorator tasks, test tasks, quality gate tasks, git workflow tasks
   - If format issues found, note them for reporting

7. **Read `tasks.md`:**
   - Extract: implementation tasks
   - Identify: files to create/modify/delete
   - Note: dependencies between tasks
   - Verify: Branch creation is first task, PR creation is last task (per config.yaml)

8. **Read `design.md` (if exists):**
   - Extract: architectural decisions, trade-offs
   - Identify: interface changes, contract modifications
   - Note: migration plans, risks
   - Verify: Bridge adapter integration documented, sequence diagrams for multi-repo flows (per config.yaml)

9. **Read spec deltas (`specs/<capability>/spec.md`):**
   - Extract: ADDED/MODIFIED/REMOVED requirements
   - Identify: interface changes, parameter changes, contract changes
   - Note: cross-references to other capabilities
   - Verify: Specs use Given/When/Then format, reference existing patterns (per config.yaml)

**2.2: Identify Change Scope**

1. **Files to modify:**
   - Extract from tasks.md and proposal.md
   - Categorize: code files, tests, documentation, configuration
   - Note: file paths relative to repository root

2. **Modules/Components affected:**
   - Identify Python modules, classes, functions
   - Identify interfaces, contracts, APIs
   - Note: public vs private interfaces

3. **Dependencies:**
   - Extract from proposal.md "Dependencies" section
   - Extract from tasks.md task dependencies
   - Note: external dependencies, internal dependencies

**Output:** Parsed change proposal with identified scope, files, modules, and dependencies

### Step 3: Simulate Change Application (Dry-Run)

**3.1: Create Temporary Workspace**

1. **Create temporary directory:**

   ```bash
   TEMP_WORKSPACE="/tmp/specfact-validation-<change-id>-$(date +%s)"
   mkdir -p "$TEMP_WORKSPACE"
   ```

2. **Clone or copy repository structure:**
   - If target repository is in workspace: Copy repository to temp workspace
   - If target repository is external: Note that full validation requires repository access
   - Preserve directory structure and file organization

**3.2: Analyze Spec Deltas for Interface Changes**

1. **For each spec delta file:**
   - Parse ADDED/MODIFIED/REMOVED requirements
   - Extract interface/contract/parameter changes:
     - Function signatures (parameters, return types)
     - Class interfaces (methods, properties)
     - Contract decorators (`@icontract`, `@require`, `@ensure`)
     - Type hints (`@beartype`)
     - API endpoints (if applicable)

2. **Create interface scaffold in temp workspace:**
   - For MODIFIED requirements: Create interface stub showing old vs new signature
   - For ADDED requirements: Create interface stub showing new signature
   - For REMOVED requirements: Mark interface as removed
   - **DO NOT** implement function bodies or logic - only interface/contract layer

3. **Example interface scaffold:**

   ```python
   # OLD INTERFACE (from existing codebase)
   def process_data(data: str, options: dict) -> dict:
       """Old signature"""
       pass
   
   # NEW INTERFACE (from change proposal)
   def process_data(data: str, options: dict, validate: bool = True) -> dict:
       """New signature with added parameter"""
       pass
   ```

**3.3: Map Tasks to File Modifications**

1. **For each task in tasks.md:**
   - Identify files to create/modify/delete
   - Categorize modification type:
     - **Interface change**: Function/class signature modification
     - **Contract change**: `@icontract` decorator modification
     - **Type change**: Type hint modification
     - **New file**: New module/class/function
     - **Delete file**: Removal of module/class/function
     - **Documentation**: Documentation-only changes (non-breaking)

2. **Create modification map:**
   - File path → Modification type → Interface changes
   - Store in structured format for analysis

**Output:** Temporary workspace with interface scaffolds, modification map

### Step 4: Dependency Analysis and Breaking Change Detection

**4.1: Find Dependent Code**

1. **For each modified file/interface:**
   - Search codebase for imports/usages:
     - `rg -n "from.*import.*<module>"` - Find imports
     - `rg -n "<function_name>\(|<class_name>\("` - Find usages
     - `rg -n "@<decorator>"` - Find contract decorators
   - Identify all files that import or use the modified interfaces

2. **Build dependency graph:**
   - Modified interface → List of dependent files
   - Categorize dependencies:
     - **Direct**: Direct import/usage
     - **Indirect**: Import through intermediate modules
     - **Test dependencies**: Test files that use the interface

**4.2: Analyze Breaking Changes**

1. **For each modified interface:**
   - Compare old vs new interface scaffold
   - Detect breaking changes:
     - **Parameter removal**: Required parameter removed
     - **Parameter addition**: Required parameter added (without default)
     - **Parameter type change**: Type changed incompatibly
     - **Return type change**: Return type changed incompatibly
     - **Contract strengthening**: `@require` made stricter, `@ensure` made weaker
     - **Method removal**: Public method removed from class
     - **Class removal**: Public class removed
     - **Module removal**: Public module removed

2. **For each dependent file:**
   - Check if it would break with new interface:
     - Missing required parameter
     - Wrong parameter type
     - Wrong return type usage
     - Missing method/class/module
   - Categorize impact:
     - **Would break**: Incompatible usage detected
     - **Would need update**: Compatible but may need adjustment
     - **No impact**: Usage is compatible

**4.3: Identify Required Updates**

1. **List all dependent files that need updates:**
   - Files that would break (must be updated)
   - Files that should be updated (recommended)
   - Files that are unaffected (no action needed)

2. **Categorize update requirements:**
   - **Critical**: Breaking change, must update or code won't work
   - **Recommended**: Non-breaking but should update for consistency
   - **Optional**: No update needed, but update would improve code

**Output:** Dependency graph, breaking change analysis, required updates list

### Step 5: Validation Report and User Decision

**5.1: Generate Validation Summary**

1. **Breaking changes detected:**
   - Count of breaking changes
   - List of affected interfaces
   - List of dependent files that would break

2. **Dependencies affected:**
   - Count of dependent files
   - Categorization: critical/recommended/optional

3. **Impact assessment:**
   - **High impact**: Many breaking changes, many dependent files
   - **Medium impact**: Some breaking changes, some dependent files
   - **Low impact**: Few/no breaking changes, few dependent files

**5.2: Present Findings to User**

Display validation summary:

```text
Change Validation Report: <change-id>

Breaking Changes Detected: <count>
  - <interface 1>: <description>
  - <interface 2>: <description>

Dependent Files Affected: <count>
  Critical (must update): <count>
    - <file 1>: <reason>
    - <file 2>: <reason>
  Recommended (should update): <count>
    - <file 3>: <reason>
  Optional (no action needed): <count>

Impact Assessment: <High/Medium/Low>
```

**5.3: User Decision Options**

**If breaking changes detected:**

1. **Option A: Extend Change Scope**
   - Prompt: "Extend change scope to update dependent files? (y/n):"
   - If yes:
     - Add tasks to update dependent files
     - Update proposal.md to include extended scope
     - Note: This may require major version upgrade
     - Create extended change proposal

2. **Option B: Adjust Change to Avoid Breaking**
   - Prompt: "Adjust change to avoid breaking changes? (y/n):"
   - If yes:
     - Propose adjustments:
       - Add default parameters instead of required
       - Keep old interface, add new interface (deprecation)
       - Use optional parameters, backward-compatible types
     - Update proposal.md with adjusted approach
     - Re-validate with adjusted changes

3. **Option C: Reject and Defer**
   - Prompt: "Reject change and defer to later? (y/n):"
   - If yes:
     - Update proposal.md status to "deferred"
     - Add deferral reason and conditions
     - Document breaking changes in CHANGE_VALIDATION.md
     - Note: Change will be reconsidered when conditions are met

**If no breaking changes detected:**

- Proceed to Step 5.4 (OpenSpec Validation)

**Output:** User decision, updated change proposal (if scope extended or adjusted)

**5.4: OpenSpec Validation (Safety Check)**

1. **Check change status before validation:**

   ```bash
   openspec status --change "<change-id>" --json
   ```

   - Verify all required artifacts are complete (status: "done")
   - Check artifact dependencies are satisfied

2. **Run OpenSpec validation:**

   ```bash
   openspec validate <change-id> --strict
   ```

3. **If validation fails:**
   - Read validation errors
   - Fix issues in proposal.md, tasks.md, design.md (if exists), or spec deltas
   - **If proposal was updated** (scope extended or adjusted in Step 5.3):
     - Re-validate the updated proposal
     - Ensure all changes are properly reflected in OpenSpec artifacts
     - Re-check status: `openspec status --change "<change-id>" --json`
   - Re-run validation
   - Continue until validation passes

4. **If validation passes:**
   - Proceed to Step 6 (Create Validation Report)
   - Note validation status in CHANGE_VALIDATION.md

5. **Validation status:**
   - Document OpenSpec validation result in validation report
   - Include any fixes made during validation
   - Note if proposal was updated and re-validated
   - Document schema used (from status JSON)

**Output:** Validated change proposal, passing OpenSpec validation

### Step 6: Create Validation Report

**6.1: Generate CHANGE_VALIDATION.md**

1. **Create validation report:**
   - Location: `openspec/changes/<change-id>/CHANGE_VALIDATION.md`
   - Include:
     - Validation date and timestamp
     - Change ID and proposal reference
     - Validation method (dry-run simulation)
     - Breaking changes detected
     - Dependencies affected
     - Impact assessment
     - User decision and rationale
     - Next steps

2. **Report structure:**

   ```markdown
   # Change Validation Report: <change-id>
   
   **Validation Date**: <timestamp>
   **Change Proposal**: [proposal.md](./proposal.md)
   **Validation Method**: Dry-run simulation in temporary workspace
   
   ## Executive Summary
   
   - Breaking Changes: <count> detected / <count> resolved
   - Dependent Files: <count> affected
   - Impact Level: <High/Medium/Low>
   - Validation Result: <Pass/Fail/Deferred>
   - User Decision: <Extend Scope/Adjust Change/Reject>
   
   ## Breaking Changes Detected
   
   ### Interface: <interface-name>
   - **Type**: Parameter addition/removal/type change
   - **Old Signature**: `<old signature>`
   - **New Signature**: `<new signature>`
   - **Breaking**: Yes/No
   - **Dependent Files**: 
     - `<file1>`: <impact description>
     - `<file2>`: <impact description>
   
   ## Dependencies Affected
   
   ### Critical Updates Required
   - `<file1>`: <reason>
   - `<file2>`: <reason>
   
   ### Recommended Updates
   - `<file3>`: <reason>
   
   ## Impact Assessment
   
   - **Code Impact**: <description>
   - **Test Impact**: <description>
   - **Documentation Impact**: <description>
   - **Release Impact**: <Minor/Major/Patch>
   
   ## User Decision
   
   **Decision**: <Extend Scope/Adjust Change/Reject>
   **Rationale**: <user-provided reason>
   **Next Steps**: <action items>
   
   ## Format Validation
   
   - **proposal.md Format**: <Pass/Fail>
     - Title format: <Correct/Incorrect>
     - Required sections: <All present/Missing sections> (Why, What Changes, Capabilities, Impact per config.yaml)
     - "What Changes" format: <Correct/Incorrect>
     - "Capabilities" section: <Present/Missing> (critical per config.yaml)
     - "Impact" format: <Correct/Incorrect>
     - Source Tracking section: <Present/Missing> (if public-facing change per config.yaml)
   - **tasks.md Format**: <Pass/Fail>
     - Section headers: <Correct/Incorrect>
     - Task format: <Correct/Incorrect>
     - Sub-task format: <Correct/Incorrect>
     - Config.yaml compliance: <Pass/Fail>
       - 2-hour maximum chunks: <Verified/Not verified>
       - Contract decorator tasks: <Present/Missing>
       - Test tasks: <Present/Missing>
       - Quality gate tasks: <Present/Missing>
       - Git workflow tasks: <Present/Missing> (branch creation first, PR creation last)
       - GitHub issue creation task: <Present/Missing> (if public-facing change per config.yaml)
   - **specs Format**: <Pass/Fail>
     - Given/When/Then format: <Verified/Not verified>
     - References existing patterns: <Verified/Not verified>
   - **design.md Format**: <Pass/Fail> (if exists)
     - Bridge adapter integration: <Documented/Missing>
     - Sequence diagrams: <Present/Missing> (if multi-repo flows)
   - **Format Issues Found**: <count>
   - **Format Issues Fixed**: <count>
   - **Config.yaml Compliance**: <Pass/Fail>
   
   ## OpenSpec Validation
   
   - **Status**: <Pass/Fail>
   - **Validation Command**: `openspec validate <change-id> --strict`
   - **Issues Found**: <count>
   - **Issues Fixed**: <count>
   - **Re-validated**: <Yes/No> (if proposal was updated)
   
   ## Validation Artifacts
   
   - Temporary workspace: `/tmp/specfact-validation-<change-id>-<timestamp>`
   - Interface scaffolds: `<path>`
   - Dependency graph: `<path>`
   ```

**6.2: Update Proposal Status (if needed)**

1. **If change was deferred:**
   - Update `proposal.md` status to "deferred"
   - Add deferral section with conditions
   - Link to CHANGE_VALIDATION.md

2. **If change scope was extended:**
   - Update `proposal.md` scope section
   - Add extended dependencies
   - Note: May require major version upgrade

3. **If change was adjusted:**
   - Update `proposal.md` with adjusted approach
   - Note backward compatibility measures

**Output:** CHANGE_VALIDATION.md created, proposal.md updated (if needed)

### Step 7: Completion and Summary

**7.1: Present Results**

Display summary:

```text
✓ Change validation completed

Change ID: <change-id>
Validation Report: openspec/changes/<change-id>/CHANGE_VALIDATION.md

Findings:
  - Breaking Changes: <count>
  - Dependent Files: <count>
  - Impact Level: <High/Medium/Low>
  - Validation Result: <Pass/Fail/Deferred>

User Decision: <Extend Scope/Adjust Change/Reject>

Next Steps:
  1. Review validation report: CHANGE_VALIDATION.md
  2. <action based on decision>
  3. Re-validate if change was adjusted
  4. Proceed with implementation when ready
```

**7.2: Provide Next Actions**

1. **If validation passed:**
   - Inform: "Change is safe to implement. OpenSpec validation passed. Proceed with `/opsx:apply <change-id>` (OPSX workflow) or `/openspec-apply <change-id>` (legacy)"

2. **If scope was extended:**
   - Inform: "Change scope extended. Review updated proposal.md and tasks.md"
   - Suggest: "Re-validate after reviewing extended scope"

3. **If change was adjusted:**
   - Inform: "Change adjusted for backward compatibility. Review updated proposal.md"
   - Suggest: "Re-validate with adjusted changes"

4. **If change was deferred:**
   - Inform: "Change deferred. Review CHANGE_VALIDATION.md for conditions"
   - Suggest: "Reconsider when conditions are met or major version upgrade planned"

**Output:** Completion summary, next action guidance

**Reference**

- OPSX commands: `/opsx:new`, `/opsx:ff`, `/opsx:continue`, `/opsx:apply`, `/opsx:verify`, `/opsx:archive`
- OpenSpec config: `openspec/config.yaml` (project context and per-artifact rules)
- Legacy commands: `/openspec-proposal` (use `/opsx:ff` instead), `/openspec-apply` (use `/opsx:apply` instead)
- OpenSpec CLI: `openspec list`, `openspec status`, `openspec instructions`, `openspec validate`
- Project rules: `specfact-cli/.cursor/rules/`
- OpenSpec conventions: `openspec/AGENTS.md`

**Error Handling**

- **Change not found:** Search and suggest alternatives, ask user to confirm
- **Repository not accessible:** Inform user, provide manual validation instructions
- **Breaking changes detected:** Present options clearly, don't proceed without user decision
- **Dependency analysis fails:** Log error, continue with partial analysis, note limitations

**Common Patterns**

```bash
# With change ID
/wf-validate-change improve-documentation-structure

# Interactive selection
/wf-validate-change

# Validate before implementation
/wf-validate-change <change-id>
# Then review CHANGE_VALIDATION.md
# Then proceed with /opsx:apply <change-id> (or /openspec-apply <change-id> for legacy)
```

**Technical Notes**

- **Interface Analysis**: Focus on function signatures, class interfaces, contract decorators, type hints
- **Dependency Detection**: Use `rg` (ripgrep) for code search, AST parsing for Python imports
- **Breaking Change Detection**: Compare interface scaffolds, check parameter compatibility, return type compatibility
- **Temporary Workspace**: Use `/tmp/specfact-validation-<change-id>-<timestamp>` for isolation
- **Validation Artifacts**: Preserve interface scaffolds and dependency graphs for audit trail

<!-- WORKFLOW:END -->

--- End Command ---
