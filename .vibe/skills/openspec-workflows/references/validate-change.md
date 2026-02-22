# Workflow: Validate OpenSpec Change

## Table of Contents

- [Guardrails](#guardrails)
- [Step 1: Change Selection](#step-1-change-selection)
- [Step 2: Read and Parse Change](#step-2-read-and-parse-change)
- [Step 3: Simulate Change Application](#step-3-simulate-change-application)
- [Step 4: Dependency Analysis](#step-4-dependency-analysis)
- [Step 5: Validation Report and Decision](#step-5-validation-report-and-decision)
- [Step 6: Create Validation Report](#step-6-create-validation-report)
- [Step 7: Completion](#step-7-completion)

## Guardrails

- Never modify the actual codebase during validation — only work in temp directories.
- Focus on interface/contract/parameter analysis, not implementation details.
- Identify breaking changes, not style or formatting issues.
- Always create CHANGE_VALIDATION.md for audit trail.
- Ask for user confirmation before extending change scope or rejecting proposals.

## Step 1: Change Selection

**If change ID provided**: Resolve to `openspec/changes/<change-id>/`, verify directory and proposal.md exist.

**If no change ID provided**:
1. List active changes: `openspec list --json`.
2. Display numbered list with change ID, schema, status, brief description.
3. Prompt user to select.

## Step 2: Read and Parse Change

### 2.1: Check Status and Read Artifacts

1. **Read `openspec/config.yaml`** for project context, constraints, and per-artifact rules.

2. **Check change status**: `openspec status --change "<change-id>" --json`
   - Verify artifacts exist and are complete (status: "done").

3. **Get artifact context**: `openspec instructions apply --change "<change-id>" --json`

4. **Verify proposal.md format** (per config.yaml):
   - Title: `# Change: [Brief description]`
   - Required sections: `## Why`, `## What Changes`, `## Capabilities`, `## Impact`
   - "What Changes": bullet list with NEW/EXTEND/MODIFY markers
   - "Capabilities": each capability needs a spec file
   - "Impact": Affected specs, Affected code, Integration points

5. **Read proposal.md**: Extract summary, rationale, scope, capabilities, affected files.

6. **Verify tasks.md format** (per config.yaml):
   - Hierarchical numbered sections: `## 1.`, `## 2.`
   - Tasks: `- [ ] 1.1 [Description]`
   - Sub-tasks: `- [ ] 1.1.1 [Description]`
   - Rules: 2-hour max chunks, contract tasks, test tasks, quality gates, git worktree workflow (worktree creation first, PR last, cleanup after merge)

7. **Read tasks.md**: Extract tasks, files to create/modify/delete, task dependencies. Verify worktree creation first, PR creation last, worktree cleanup after merge.

8. **Read design.md** (if exists): Architectural decisions, interface changes, contracts, migration plans. Verify bridge adapter docs, sequence diagrams for multi-repo.

9. **Read spec deltas** (`specs/<capability>/spec.md`): ADDED/MODIFIED/REMOVED requirements, interface/parameter/contract changes, cross-refs. Verify Given/When/Then format.

### 2.2: Identify Change Scope

1. **Files to modify**: Extract from tasks.md and proposal.md. Categorize: code, tests, docs, config.
2. **Modules/Components**: Python modules, classes, functions, interfaces, contracts, APIs. Note public vs private.
3. **Dependencies**: From proposal "Dependencies" section and task dependencies.

## Step 3: Simulate Change Application

### 3.1: Create Temporary Workspace

```bash
TEMP_WORKSPACE="/tmp/specfact-validation-<change-id>-$(date +%s)"
mkdir -p "$TEMP_WORKSPACE"
```

Copy relevant repository structure to temp workspace.

### 3.2: Analyze Spec Deltas for Interface Changes

For each spec delta:
1. Parse ADDED/MODIFIED/REMOVED requirements.
2. Extract interface changes: function signatures, class interfaces, `@icontract`/`@beartype` decorators, type hints, API endpoints.
3. Create interface scaffolds in temp workspace (stubs only, no implementation):

```python
# OLD INTERFACE (from existing codebase)
def process_data(data: str, options: dict) -> dict: ...

# NEW INTERFACE (from change proposal)
def process_data(data: str, options: dict, validate: bool = True) -> dict: ...
```

### 3.3: Map Tasks to File Modifications

For each task, categorize modification type:
- **Interface change**: Function/class signature modification
- **Contract change**: `@icontract` decorator modification
- **Type change**: Type hint modification
- **New/Delete file**: Module/class/function added or removed
- **Documentation**: Non-breaking doc changes

Create modification map: File path -> Modification type -> Interface changes.

## Step 4: Dependency Analysis

### 4.1: Find Dependent Code

For each modified file/interface, search codebase:
- `from...import...<module>` — find imports
- `<function_name>(` or `<class_name>(` — find usages
- `@<decorator>` — find contract decorators

Build dependency graph: Modified interface -> dependent files (direct, indirect, test).

### 4.2: Analyze Breaking Changes

Compare old vs new interface. Detect:
- **Parameter removal**: Required param removed
- **Parameter addition**: Required param added (no default)
- **Parameter type change**: Incompatible type
- **Return type change**: Incompatible return
- **Contract strengthening**: `@require` stricter, `@ensure` weaker
- **Method/class/module removal**: Public API removed

For each dependent file, check if it would break:
- **Would break**: Incompatible usage detected
- **Would need update**: Compatible but may need adjustment
- **No impact**: Usage compatible

### 4.3: Identify Required Updates

Categorize:
- **Critical**: Must update or code breaks
- **Recommended**: Should update for consistency
- **Optional**: No update needed

## Step 5: Validation Report and Decision

### 5.1: Summary

Count breaking changes, affected interfaces, dependent files. Assess impact: High/Medium/Low.

### 5.2: Present Findings

```
Change Validation Report: <change-id>

Breaking Changes Detected: <count>
  - <interface 1>: <description>

Dependent Files Affected: <count>
  Critical (must update): <count>
  Recommended: <count>
  Optional: <count>

Impact Assessment: <High/Medium/Low>
```

### 5.3: User Decision (if breaking changes)

**Option A: Extend Scope** — Add tasks to update dependent files. May require major version.

**Option B: Adjust Change** — Add default params, keep old interface (deprecation), use optional params.

**Option C: Reject and Defer** — Update status to "deferred", document in CHANGE_VALIDATION.md.

**No breaking changes**: Proceed to 5.4.

### 5.4: OpenSpec Validation

1. Check status: `openspec status --change "<change-id>" --json`
2. Run: `openspec validate <change-id> --strict`
3. Fix issues and re-run until passing.
4. If proposal was updated (scope extended/adjusted), re-validate.

## Step 6: Create Validation Report

Create `openspec/changes/<change-id>/CHANGE_VALIDATION.md`:

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
- User Decision: <Extend Scope/Adjust Change/Reject/N/A>

## Breaking Changes Detected

### Interface: <name>
- **Type**: Parameter addition/removal/type change
- **Old Signature**: `<old>`
- **New Signature**: `<new>`
- **Dependent Files**: <file>: <impact>

## Dependencies Affected

### Critical Updates Required
- <file>: <reason>

### Recommended Updates
- <file>: <reason>

## Impact Assessment

- **Code Impact**: <description>
- **Test Impact**: <description>
- **Documentation Impact**: <description>
- **Release Impact**: <Minor/Major/Patch>

## Format Validation

- **proposal.md Format**: <Pass/Fail>
  - Title, sections, capabilities, impact per config.yaml
- **tasks.md Format**: <Pass/Fail>
  - Headers, task format, config.yaml compliance (TDD, git workflow, quality gates)
- **specs Format**: <Pass/Fail>
  - Given/When/Then format, references existing patterns
- **Config.yaml Compliance**: <Pass/Fail>

## OpenSpec Validation

- **Status**: <Pass/Fail>
- **Command**: `openspec validate <change-id> --strict`
- **Issues Found/Fixed**: <count>

## Validation Artifacts

- Temporary workspace: <path>
```

Update proposal status if deferred, scope extended, or adjusted.

## Step 7: Completion

```
Change ID: <change-id>
Validation Report: openspec/changes/<change-id>/CHANGE_VALIDATION.md

Findings:
  - Breaking Changes: <count>
  - Dependent Files: <count>
  - Impact Level: <level>
  - Validation Result: <result>

Next Steps:
  <based on decision — implement, re-validate, or defer>
```

## Error Handling

- **Change not found**: Search and suggest alternatives.
- **Repo not accessible**: Inform user, provide manual validation instructions.
- **Breaking changes**: Present options clearly, don't proceed without user decision.
- **Dependency analysis fails**: Continue with partial analysis, note limitations.
