---
layout: default
title: Agile/Scrum Workflows with SpecFact CLI
permalink: /guides/agile-scrum-workflows/
---

# Agile/Scrum Workflows with SpecFact CLI

This guide explains how to use SpecFact CLI for agile/scrum workflows, including backlog management, sprint planning, dependency tracking, and Definition of Ready (DoR) validation.

Preferred command paths are `specfact backlog ceremony standup ...` and `specfact backlog ceremony refinement ...`. Legacy `backlog daily`/`backlog refine` remain available for compatibility.

Backlog module command surface:

- `specfact backlog add`
- `specfact backlog analyze-deps`
- `specfact backlog trace-impact`
- `specfact backlog verify-readiness`
- `specfact backlog diff`
- `specfact backlog sync`
- `specfact backlog promote`
- `specfact backlog generate-release-notes`
- `specfact backlog delta status|impact|cost-estimate|rollback-analysis`

## Backlog Issue Creation (`backlog add`)

Use `specfact backlog add` to create a backlog item with optional parent hierarchy validation and DoR checks.

```bash
# Non-interactive creation
specfact backlog add \
  --adapter github \
  --project-id nold-ai/specfact-cli \
  --template github_projects \
  --type story \
  --parent FEAT-123 \
  --title "Implement X" \
  --body "Acceptance criteria: ..." \
  --non-interactive

# Enforce Definition of Ready from .specfact/dor.yaml before create
specfact backlog add \
  --adapter github \
  --project-id nold-ai/specfact-cli \
  --type story \
  --title "Implement X" \
  --body "Acceptance criteria: ..." \
  --check-dor \
  --repo-path .

# Interactive ADO flow with sprint/iteration selection and story-quality fields
specfact backlog add \
  --adapter ado \
  --project-id "dominikusnold/Specfact CLI"
```

Key behavior:

- validates parent exists in current backlog graph before creating
- validates child-parent type compatibility using `creation_hierarchy` from config/template
- supports interactive prompts when required fields are missing (unless `--non-interactive`)
- prompts for ADO sprint/iteration selection and resolves available iterations from `--project-id` context
- supports multiline body and acceptance criteria capture (default sentinel `::END::`)
- captures priority and story points for story-like items
- supports description rendering mode (`markdown` or `classic`)
- auto-selects template by adapter when omitted (`ado_scrum` for ADO, `github_projects` for GitHub)
- creates via adapter protocol (`github` or `ado`) and prints created `id`, `key`, and `url`

## Overview

SpecFact CLI supports real-world agile/scrum practices through:

- **Definition of Ready (DoR)**: Automatic validation of story readiness for sprint planning
- **Backlog Refinement** 🆕: AI-assisted template-driven refinement for standardizing work items from DevOps backlogs
- **Daily Standup**: Use `specfact backlog ceremony standup <adapter>` to list my/filtered items with status and last activity.
  Default scope (state=open, limit=20, optional assignee=me) is applied when not overridden; configure via
  `SPECFACT_STANDUP_STATE`, `SPECFACT_STANDUP_LIMIT`, `SPECFACT_STANDUP_ASSIGNEE` or
  `.specfact/standup.yaml`. Use `--iteration` / `--sprint` (e.g. `--sprint current`) to focus on current
  iteration when the adapter supports it; sprint/iteration end date is shown when provided by adapter or
  config (`standup.sprint_end_date`). A second table **Pending / open for commitment** lists unassigned
  items (same scope); use `--show-unassigned`/`--no-show-unassigned` or `--unassigned-only`. Use
  `--blockers-first` to sort items with blockers first; enable `show_priority` or `show_value` in standup
  config for optional priority/value column (value-driven/SAFe). Optional standup summary
  (yesterday/today/blockers) from item body; optionally post standup comment to linked issue via `--post`
  when the adapter supports comments (e.g. GitHub).
  **Interactive step-by-step review**: Use `--interactive` to select stories with arrow keys (questionary)
  and view full detail (refine-like: description, acceptance criteria, standup fields). Interactive detail
  shows the **latest comment only** plus a hint when older comments exist; use export options for full
  comment history. Navigate with Next/Previous/**Post standup update**/Back to list/Exit. `Post standup update`
  posts yesterday/today/blockers to the currently selected story (adapter support required). Use `--suggest-next`
  to show suggested next item by value score (business_value / (story_points × priority)).
  **Copilot export**: Use `--copilot-export <path>` to write a summarized Markdown file of each story for
  Copilot. Add `--comments` (alias `--annotations`) to include descriptions and comment annotations in
  `--copilot-export` and `--summarize` outputs when the adapter supports `get_comments` (GitHub, ADO). All
  summarize/copilot-export content is **normalized to Markdown-only text** (no raw HTML tags or entities)
  so ADO-style HTML fields and Markdown-native fields render consistently. Use `--first-comments N` or
  `--last-comments N` to scope comment volume when needed (default: include all).
  Use `--first-issues N` or `--last-issues N` (mutually exclusive) to scope daily output to oldest/newest
  items by numeric issue/work-item ID.
  **Kanban**: omit iteration/sprint and use state + limit; unassigned = pullable work. **Scrum/SAFe**: use
  `--sprint current` and optional priority/value. **Out of scope**: Sprint goal is in your board/sprint
  settings (not displayed by CLI). Stale/at-risk flags (e.g. "no update in N days") are not in scope—use
  last updated + blockers. Structured "blocked by" (link to another issue) is not in scope; only free-text
  blockers are supported.
- **Dependency Management**: Track story-to-story and feature-to-feature dependencies
- **Prioritization**: Priority levels, ranking, and business value scoring
- **Sprint Planning**: Target sprint/release assignment and story point tracking
- **Business Value Focus**: User-focused value statements and measurable outcomes
- **Conflict Resolution**: Persona-aware three-way merge with automatic conflict resolution based on section ownership

## Policy Engine Commands (DoR/DoD/Flow/PI)

Use the `policy` command group to run deterministic readiness checks before sprint and refinement ceremonies:

```bash
# Validate configured policy rules against a snapshot
specfact policy validate --repo . --format both

# Generate confidence-scored, patch-ready suggestions (no automatic writes)
specfact policy suggest --repo .
```

Policy configuration is loaded from `.specfact/policy.yaml` and supports Scrum (`dor_required_fields`,
`dod_required_fields`), Kanban column entry/exit requirements, and SAFe PI readiness fields.

**🆕 NEW: Backlog Refinement Integration** - Use `specfact backlog ceremony refinement` to standardize backlog items from GitHub Issues, Azure DevOps, and other tools into template-compliant format before importing into project bundles. See [Backlog Refinement Guide](backlog-refinement.md) for complete documentation.

**Tutorial**: For an end-to-end daily standup and sprint review walkthrough (auto-detect repo, view standup, post comment, interactive, Copilot export), see **[Tutorial: Daily Standup and Sprint Review](../getting-started/tutorial-daily-standup-sprint-review.md)**.

## Daily Standup and Sprint Review

Use **`specfact backlog ceremony standup <adapter>`** to list your standup items (assigned + unassigned) with status and last activity. **By default, GitHub org/repo or Azure DevOps org/project are auto-detected from the git remote** when you run from your cloned repo—no `--repo-owner`/`--repo-name` or `--ado-org`/`--ado-project` needed after authenticating once.

### Auto-Detect from Clone

- **GitHub**: When run from a **GitHub** clone (e.g. `https://github.com/owner/repo` or `git@github.com:owner/repo.git`), SpecFact infers `repo_owner` and `repo_name` from `git remote get-url origin`.
- **Azure DevOps**: When run from an **ADO** clone (e.g. `https://dev.azure.com/org/project/_git/repo`; SSH keys: `git@ssh.dev.azure.com:v3/org/project/repo`; other SSH: `user@dev.azure.com:v3/org/project/repo`), SpecFact infers `org` and `project` from the remote URL.

Override with `.specfact/backlog.yaml`, environment variables (`SPECFACT_GITHUB_REPO_OWNER`, `SPECFACT_ADO_ORG`, etc.), or CLI options when not in the repo or to override. See [Project backlog context](../guides/devops-adapter-integration.md#project-backlog-context-specfactbacklogyaml).

### End-to-End Example: One Standup Session

```bash
# 1. Authenticate once (if not already)
specfact backlog auth github

# 2. From repo root: view standup (repo auto-detected)
cd /path/to/your-repo
specfact backlog ceremony standup github

# 3. Optional: post standup comment to first item (pass values for yesterday/today/blockers)
specfact backlog ceremony standup github \
  --yesterday "Worked on X" \
  --today "Will do Y" \
  --blockers "None" \
  --post

# 4. Optional: interactive step-through, Copilot export, or standup summary prompt
specfact backlog ceremony standup github --interactive   # step-through; detail view shows latest comment + hidden-count hint
# or
specfact backlog ceremony standup github --copilot-export ./standup.md --comments --last-comments 5
# or
specfact backlog ceremony standup github --summarize --comments     # prompt to stdout for AI to generate standup summary (Markdown-only)
specfact backlog ceremony standup github --summarize-to ./standup-prompt.md    # plain Markdown file (no HTML/ANSI)
```

Use the **`specfact.backlog-daily`** (or `specfact.daily`) slash prompt for interactive walkthrough with the
DevOps team story-by-story (current focus, issues/open questions, discussion notes as comments). Default
scope: **state=open**, **limit=20**; configure via `SPECFACT_STANDUP_*` or `.specfact/standup.yaml`. Use
`--assignee me`, `--sprint current`, `--blockers-first`, `--interactive`, `--suggest-next`,
`--copilot-export <path>`, `--summarize`, `--summarize-to <path>`, `--comments`/`--annotations`, and optional
`--first-comments`/`--last-comments` plus `--first-issues`/`--last-issues` as well as global filters
`--search`, `--release`, and `--id` to narrow scope consistently with backlog ceremony refinement.
See [Tutorial: Daily Standup and Sprint Review](../getting-started/tutorial-daily-standup-sprint-review.md)
for the full walkthrough.

## Persona-Based Workflows

SpecFact uses persona-based workflows where different roles work on different aspects:

- **Product Owner**: Owns requirements, user stories, business value, prioritization, sprint planning
- **Architect**: Owns technical constraints, protocols, contracts, architectural decisions, non-functional requirements, risk assessment, deployment architecture
- **Developer**: Owns implementation tasks, technical design, code mappings, test scenarios, Definition of Done

### Exporting Persona Artifacts

Export persona-specific Markdown files for editing:

```bash
# Export Product Owner view
specfact project export --bundle my-project --persona product-owner

# Export Developer view
specfact project export --bundle my-project --persona developer

# Export Architect view
specfact project export --bundle my-project --persona architect

# Export to custom location
specfact project export --bundle my-project --persona product-owner --output docs/backlog.md
```

The exported Markdown includes persona-specific content:

**Product Owner Export**:

- **Definition of Ready Checklist**: Visual indicators for each DoR criterion
- **Prioritization Data**: Priority, rank, business value scores
- **Dependencies**: Clear dependency chains (depends on, blocks)
- **Business Value**: User-focused value statements and metrics
- **Sprint Planning**: Target dates, sprints, and releases

**Developer Export**:

- **Acceptance Criteria**: Feature and story acceptance criteria
- **User Stories**: Detailed story context with tasks, contracts, scenarios
- **Implementation Tasks**: Granular tasks with file paths
- **Code Mappings**: Source and test function mappings
- **Sprint Context**: Story points, priority, dependencies, target sprint/release
- **Definition of Done**: Completion criteria checklist

**Architect Export**:

- **Technical Constraints**: Feature-level technical constraints
- **Architectural Decisions**: Technology choices, patterns, integration approaches
- **Non-Functional Requirements**: Performance, scalability, availability, security, reliability targets
- **Protocols & State Machines**: Complete protocol definitions with states and transitions
- **Contracts**: OpenAPI/AsyncAPI contract details
- **Risk Assessment**: Technical risks and mitigation strategies
- **Deployment Architecture**: Infrastructure and deployment patterns

### Importing Persona Edits

After editing the Markdown file, import changes back:

```bash
# Import Product Owner edits
specfact project import --bundle my-project --persona product-owner --source docs/backlog.md

# Import Developer edits
specfact project import --bundle my-project --persona developer --source docs/developer.md

# Import Architect edits
specfact project import --bundle my-project --persona architect --source docs/architect.md

# Dry-run to validate without applying
specfact project import --bundle my-project --persona product-owner --source docs/backlog.md --dry-run
```

The import process validates:

- **Template Structure**: Required sections present
- **DoR Completeness**: All DoR criteria met
- **Dependency Integrity**: No circular dependencies, all references exist
- **Priority Consistency**: Valid priority formats (P0-P3, MoSCoW)
- **Date Formats**: ISO 8601 date validation
- **Story Point Ranges**: Valid Fibonacci-like values

## Section Locking

SpecFact supports section-level locking to prevent concurrent edits and ensure data integrity when multiple personas work on the same project bundle.

### Lock Workflow

#### Step 1: Lock Section Before Editing

Lock the sections you plan to edit to prevent conflicts:

```bash
# Product Owner locks idea section
specfact project lock --bundle my-project --section idea --persona product-owner

# Architect locks protocols section
specfact project lock --bundle my-project --section protocols --persona architect
```

#### Step 2: Export and Edit

Export your persona view, make edits, then import back:

```bash
# Export
specfact project export --bundle my-project --persona product-owner

# Edit the exported Markdown file
# ... make your changes ...

# Import (will be blocked if section is locked by another persona)
specfact project import --bundle my-project --persona product-owner --input product-owner.md
```

#### Step 3: Unlock After Completing Edits

Unlock the section when you're done:

```bash
# Unlock section
specfact project unlock --bundle my-project --section idea
```

### Lock Enforcement

The `project import` command automatically checks locks before saving:

- **Allowed**: Import succeeds if you own the locked section
- **Blocked**: Import fails if section is locked by another persona
- **Blocked**: Import fails if section is locked and you don't own it

#### Example: Lock Enforcement in Action

```bash
# Product Owner locks idea section
specfact project lock --bundle my-project --section idea --persona product-owner

# Product Owner imports (succeeds - owns the section)
specfact project import --bundle my-project --persona product-owner --input backlog.md
# ✓ Import successful

# Architect tries to import (fails - section is locked)
specfact project import --bundle my-project --persona architect --input architect.md
# ✗ Error: Cannot import: Section(s) are locked
#   - Section 'idea' is locked by 'product-owner' (locked at 2025-12-12T10:00:00Z)
```

### Real-World Workflow Example

**Scenario**: Product Owner and Architect working in parallel

```bash
# Morning: Product Owner locks idea and business sections
specfact project lock --bundle my-project --section idea --persona product-owner
specfact project lock --bundle my-project --section business --persona product-owner

# Product Owner exports and edits
specfact project export --bundle my-project --persona product-owner
# Edit docs/project-plans/my-project/product-owner.md

# Product Owner imports (succeeds)
specfact project import --bundle my-project --persona product-owner \
  --input docs/project-plans/my-project/product-owner.md

# Product Owner unlocks after completing edits
specfact project unlock --bundle my-project --section idea
specfact project unlock --bundle my-project --section business

# Afternoon: Architect locks protocols section
specfact project lock --bundle my-project --section protocols --persona architect

# Architect exports and edits
specfact project export --bundle my-project --persona architect
# Edit docs/project-plans/my-project/architect.md

# Architect imports (succeeds)
specfact project import --bundle my-project --persona architect \
  --input docs/project-plans/my-project/architect.md

# Architect unlocks
specfact project unlock --bundle my-project --section protocols
```

### Checking Locks

List all current locks:

```bash
# List all locks
specfact project locks --bundle my-project
```

**Output:**

```text
Section Locks
┌─────────────────────┬──────────────────┬─────────────────────────┬──────────────────┐
│ Section             │ Owner            │ Locked At               │ Locked By        │
├─────────────────────┼──────────────────┼─────────────────────────┼──────────────────┤
│ idea                │ product-owner    │ 2025-12-12T10:00:00Z    │ user@hostname    │
│ protocols           │ architect        │ 2025-12-12T14:00:00Z    │ user@hostname    │
└─────────────────────┴──────────────────┴─────────────────────────┴──────────────────┘
```

### Lock Best Practices

1. **Lock Before Editing**: Always lock sections before exporting and editing
2. **Unlock Promptly**: Unlock sections immediately after completing edits
3. **Check Locks First**: Use `project locks` to see what's locked before starting work
4. **Coordinate with Team**: Communicate lock usage to avoid blocking teammates
5. **Use Granular Locks**: Lock only the sections you need, not entire bundles

### Troubleshooting Locks

**Issue**: Import fails with "Section(s) are locked"

**Solution**: Check who locked the section and coordinate:

```bash
# Check locks
specfact project locks --bundle my-project

# Contact the lock owner or wait for them to unlock
# Or ask them to unlock: specfact project unlock --section <section>
```

**Issue**: Can't lock section - "already locked"

**Solution**: Someone else has locked it. Check locks and coordinate:

```bash
# See who locked it
specfact project locks --bundle my-project

# Wait for unlock or coordinate with lock owner
```

**Issue**: Locked section but forgot to unlock

**Solution**: Unlock manually:

```bash
# Unlock the section
specfact project unlock --bundle my-project --section <section>
```

## Conflict Resolution

When multiple personas work on the same project bundle in parallel, conflicts can occur when merging changes. SpecFact provides persona-aware conflict resolution that automatically resolves conflicts based on section ownership.

### How Persona-Based Conflict Resolution Works

SpecFact uses a three-way merge algorithm that:

1. **Detects conflicts**: Compares base (common ancestor), ours (current branch), and theirs (incoming branch) versions
2. **Checks ownership**: Determines which persona owns each conflicting section based on bundle manifest
3. **Auto-resolves**: Automatically resolves conflicts when ownership is clear:
   - If only one persona owns the section → that persona's version wins
   - If both personas own it and they're the same → current branch wins
   - If both personas own it and they're different → requires manual resolution
4. **Interactive resolution**: Prompts for manual resolution when ownership is ambiguous

### Merge Workflow

**Step 1: Export and Edit**

Each persona exports their view, edits it, and imports back:

```bash
# Product Owner exports and edits
specfact project export --bundle my-project --persona product-owner
# Edit docs/project-plans/my-project/product-owner.md
specfact project import --bundle my-project --persona product-owner --source docs/project-plans/my-project/product-owner.md

# Architect exports and edits (in parallel)
specfact project export --bundle my-project --persona architect
# Edit docs/project-plans/my-project/architect.md
specfact project import --bundle my-project --persona architect --source docs/project-plans/my-project/architect.md
```

**Step 2: Merge Changes**

When merging branches, use `project merge` with persona information:

```bash
# Merge with automatic persona-based resolution
specfact project merge \
  --bundle my-project \
  --base main \
  --ours po-branch \
  --theirs arch-branch \
  --persona-ours product-owner \
  --persona-theirs architect
```

**Step 3: Resolve Remaining Conflicts**

If conflicts remain after automatic resolution, resolve them interactively:

```bash
# The merge command will prompt for each unresolved conflict:
# Choose resolution: [ours/theirs/base/manual]
```

Or resolve individual conflicts manually:

```bash
# Resolve a specific conflict
specfact project resolve-conflict \
  --bundle my-project \
  --path features.FEATURE-001.title \
  --resolution ours
```

### Example: Resolving a Conflict

**Scenario**: Product Owner and Architect both modified the same feature title.

**Base version** (common ancestor):

```yaml
features:
  FEATURE-001:
    title: "User Authentication"
```

**Product Owner's version** (ours):

```yaml
features:
  FEATURE-001:
    title: "Secure User Authentication"
```

**Architect's version** (theirs):

```yaml
features:
  FEATURE-001:
    title: "OAuth2 User Authentication"
```

**Automatic Resolution**:

1. SpecFact checks ownership: `features.FEATURE-001` is owned by `product-owner` (based on manifest)
2. Since Product Owner owns this section, their version wins automatically
3. Result: `"Secure User Authentication"` is kept

**Manual Resolution** (if both personas own it):

If both personas own the section, SpecFact prompts:

```
Resolving conflict: features.FEATURE-001.title
Base: User Authentication
Ours (product-owner): Secure User Authentication
Theirs (architect): OAuth2 User Authentication

Choose resolution [ours/theirs/base/manual]: manual
Enter manual value: OAuth2 Secure User Authentication
```

### Conflict Resolution Strategies

You can specify a merge strategy to override automatic resolution:

- **`auto`** (default): Persona-based automatic resolution
- **`ours`**: Always prefer our version
- **`theirs`**: Always prefer their version
- **`base`**: Always prefer base version
- **`manual`**: Require manual resolution for all conflicts

```bash
# Use manual strategy for full control
specfact project merge \
  --bundle my-project \
  --base main \
  --ours po-branch \
  --theirs arch-branch \
  --persona-ours product-owner \
  --persona-theirs architect \
  --strategy manual
```

### CI/CD Integration

For automated workflows, use `--no-interactive`:

```bash
# Non-interactive merge (fails if conflicts require manual resolution)
specfact project merge \
  --bundle my-project \
  --base main \
  --ours HEAD \
  --theirs origin/feature \
  --persona-ours product-owner \
  --persona-theirs architect \
  --no-interactive
```

**Note**: In non-interactive mode, the merge will fail if there are conflicts that require manual resolution. Use this in CI/CD pipelines only when you're confident conflicts will be auto-resolved.

### Best Practices

1. **Set Clear Ownership**: Ensure persona ownership is clearly defined in bundle manifest
2. **Merge Frequently**: Merge branches frequently to reduce conflict scope
3. **Review Auto-Resolutions**: Review automatically resolved conflicts before committing
4. **Use Manual Strategy for Complex Conflicts**: When in doubt, use `--strategy manual` for full control
5. **Document Resolution Decisions**: Add comments explaining why certain resolutions were chosen

### Troubleshooting Conflicts

**Issue**: Merge fails with "unresolved conflicts"

**Solution**: Use interactive mode to resolve conflicts:

```bash
# Run merge in interactive mode
specfact project merge \
  --bundle my-project \
  --base main \
  --ours po-branch \
  --theirs arch-branch \
  --persona-ours product-owner \
  --persona-theirs architect
# Follow prompts to resolve each conflict
```

**Issue**: Auto-resolution chose wrong version

**Solution**: Check persona ownership in manifest, or use manual strategy:

```bash
# Check ownership
specfact project export --bundle my-project --list-personas

# Use manual strategy
specfact project merge --strategy manual ...
```

**Issue**: Conflict path not found

**Solution**: Use correct conflict path format:

- `idea.title` - Idea title
- `business.value_proposition` - Business value proposition
- `features.FEATURE-001.title` - Feature title
- `features.FEATURE-001.stories.STORY-001.description` - Story description

## Definition of Ready (DoR)

### DoR Validation in Backlog Refinement 🆕

When refining backlog items from DevOps tools, you can validate DoR rules before refinement:

```bash
# Check DoR before refining backlog items
specfact backlog ceremony refinement github --check-dor --labels feature

# DoR configuration in .specfact/dor.yaml
rules:
  story_points: true
  priority: true
  business_value: true
  acceptance_criteria: true
  dependencies: false  # Optional
```

**See**: [Backlog Refinement Guide](backlog-refinement.md#definition-of-ready-dor) for DoR validation in backlog refinement workflow.

### DoR Checklist

Each story must meet these criteria before sprint planning:

- [x] **Story Points**: Complexity estimated (1, 2, 3, 5, 8, 13, 21...)
- [x] **Value Points**: Business value estimated (1, 2, 3, 5, 8, 13, 21...)
- [x] **Priority**: Priority level set (P0-P3 or MoSCoW)
- [x] **Dependencies**: Dependencies identified and validated
- [x] **Business Value**: Clear business value description present
- [x] **Target Date**: Target completion date set (optional but recommended)
- [x] **Target Sprint**: Target sprint assigned (optional but recommended)

### Example: Story with Complete DoR

```markdown
**Story 1**: User can login with email

**Definition of Ready**:
- [x] Story Points: 5 (Complexity)
- [x] Value Points: 8 (Business Value)
- [x] Priority: P1
- [x] Dependencies: 1 identified
- [x] Business Value: ✓
- [x] Target Date: 2025-01-15
- [x] Target Sprint: Sprint 2025-01

**Story Details**:
- **Story Points**: 5 (Complexity)
- **Value Points**: 8 (Business Value)
- **Priority**: P1
- **Rank**: 1
- **Target Date**: 2025-01-15
- **Target Sprint**: Sprint 2025-01
- **Target Release**: v2.1.0

**Business Value**:
Enables users to securely access their accounts, reducing support tickets by 30% and improving user satisfaction.

**Business Metrics**:
- Reduce support tickets by 30%
- Increase user login success rate to 99.5%
- Reduce password reset requests by 25%

**Dependencies**:
**Depends On**:
- STORY-000: User registration system

**Acceptance Criteria** (User-Focused):
- [ ] As a user, I can enter my email and password to log in
- [ ] As a user, I receive clear error messages if login fails
- [ ] As a user, I am redirected to my dashboard after successful login
```

## Dependency Management

### Story Dependencies

Track dependencies between stories:

```markdown
**Dependencies**:
**Depends On**:
- STORY-001: User registration system
- STORY-002: Email verification

**Blocks**:
- STORY-010: Password reset flow
```

### Feature Dependencies

Track dependencies between features:

```markdown
### FEATURE-001: User Authentication

#### Dependencies

**Depends On Features**:
- FEATURE-000: User Management Infrastructure

**Blocks Features**:
- FEATURE-002: User Profile Management
```

### Validation Rules

The import process validates:

1. **Reference Existence**: All referenced stories/features exist
2. **No Circular Dependencies**: Prevents A → B → A cycles
3. **Format Validation**: Dependency keys match expected format (STORY-001, FEATURE-001)

### Example: Circular Dependency Error

```bash
$ specfact project import --bundle my-project --persona product-owner --source backlog.md

Error: Agile/Scrum validation failed:
  - Story STORY-001: Circular dependency detected with 'STORY-002'
  - Feature FEATURE-001: Circular dependency detected with 'FEATURE-002'
```

## Prioritization

### Priority Levels

Use one of these priority formats:

- **P0-P3**: P0=Critical, P1=High, P2=Medium, P3=Low
- **MoSCoW**: Must, Should, Could, Won't
- **Descriptive**: Critical, High, Medium, Low

### Ranking

Use backlog rank (1 = highest priority):

```markdown
**Priority**: P1 | **Rank**: 1
```

### Business Value Scoring

Score features 0-100 for business value:

```markdown
**Business Value Score**: 75/100
```

### Example: Prioritized Feature

```markdown
### FEATURE-001: User Authentication

**Priority**: P1 | **Rank**: 1  
**Business Value Score**: 75/100  
**Target Release**: v2.1.0  
**Estimated Story Points**: 13

#### Business Value

Enables secure user access, reducing support overhead and improving user experience.

**Target Users**: end-user, admin

**Success Metrics**:
- Reduce support tickets by 30%
- Increase user login success rate to 99.5%
- Reduce password reset requests by 25%
```

## Sprint Planning

### Story Point Estimation

Use Fibonacci-like values: 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 100

```markdown
- **Story Points**: 5 (Complexity)
- **Value Points**: 8 (Business Value)
```

### Backlog Refinement Before Sprint Planning 🆕

Before sprint planning, refine backlog items from DevOps tools (GitHub Issues, Azure DevOps) into structured, template-compliant format:

```bash
# Refine GitHub issues in current sprint
specfact backlog ceremony refinement github --sprint "Sprint 1" --check-dor --labels feature

# Refine ADO work items with DoR validation
specfact backlog ceremony refinement ado --iteration "Project\\Sprint 1" --check-dor --state Active

# Use persona/framework filtering for role-specific templates
specfact backlog ceremony refinement github --persona product-owner --framework scrum --sprint "Sprint 1"
```

**Benefits**:

- Standardizes unstructured backlog input into corporate templates
- Validates DoR before adding items to sprints
- Filters by sprint, release, iteration for agile workflows
- Preserves original backlog data for round-trip synchronization

**See**: [Backlog Refinement Guide](backlog-refinement.md) for complete documentation.

### Target Sprint Assignment

Assign stories to specific sprints:

```markdown
- **Target Sprint**: Sprint 2025-01
- **Target Release**: v2.1.0
- **Target Date**: 2025-01-15
```

### Feature-Level Totals

Feature story point totals are automatically calculated:

```markdown
**Estimated Story Points**: 13
```

This is the sum of all story points for stories in this feature.

## Business Value Focus

### User-Focused Value Statements

Write stories with clear user value:

```markdown
**Business Value**:
As a user, I want to securely log in to my account so that I can access my personalized dashboard and manage my data.

**Business Metrics**:
- Reduce support tickets by 30%
- Increase user login success rate to 99.5%
- Reduce password reset requests by 25%
```

### Acceptance Criteria Format

Use "As a [user], I want [capability] so that [outcome]" format:

```markdown
**Acceptance Criteria** (User-Focused):
- [ ] As a user, I can enter my email and password to log in
- [ ] As a user, I receive clear error messages if login fails
- [ ] As a user, I am redirected to my dashboard after successful login
```

## Template Customization

### Override Default Templates

Create project-specific templates in `.specfact/templates/persona/`:

```bash
.specfact/
└── templates/
    └── persona/
        └── product-owner.md.j2  # Project-specific template
```

The project-specific template overrides the default template in `resources/templates/persona/`.

### Template Structure

Templates use Jinja2 syntax with these variables:

- `bundle_name`: Project bundle name
- `features`: Dictionary of features (key -> feature dict)
- `idea`: Idea section data
- `business`: Business section data
- `locks`: Section locks information

### Example: Custom Template Section

```jinja2
{% raw %}{% if features %}
## Features & User Stories

{% for feature_key, feature in features.items() %}
### {{ feature.key }}: {{ feature.title }}

**Priority**: {{ feature.priority | default('Not Set') }}
**Business Value**: {{ feature.business_value_score | default('Not Set') }}/100

{% if feature.stories %}
#### User Stories

{% for story in feature.stories %}
**Story {{ loop.index }}**: {{ story.title }}

**DoR Status**: {{ '✓ Complete' if story.definition_of_ready.values() | all else '✗ Incomplete' }}

{% endfor %}
{% endif %}

{% endfor %}
{% endif %}{% endraw %}
```

## Validation Examples

### DoR Validation

```bash
$ specfact project import --bundle my-project --persona product-owner --source backlog.md

Error: Agile/Scrum validation failed:
  - Story STORY-001 (Feature FEATURE-001): Missing story points (required for DoR)
  - Story STORY-001 (Feature FEATURE-001): Missing value points (required for DoR)
  - Story STORY-001 (Feature FEATURE-001): Missing priority (required for DoR)
  - Story STORY-001 (Feature FEATURE-001): Missing business value description (required for DoR)
```

### Dependency Validation

```bash
$ specfact project import --bundle my-project --persona product-owner --source backlog.md

Error: Agile/Scrum validation failed:
  - Story STORY-001: Dependency 'STORY-999' does not exist
  - Story STORY-001: Circular dependency detected with 'STORY-002'
  - Feature FEATURE-001: Dependency 'FEATURE-999' does not exist
```

### Priority Validation

```bash
$ specfact project import --bundle my-project --persona product-owner --source backlog.md

Error: Agile/Scrum validation failed:
  - Story STORY-001: Invalid priority 'P5' (must be P0-P3, MoSCoW, or Critical/High/Medium/Low)
  - Feature FEATURE-001: Invalid priority 'Invalid' (must be P0-P3, MoSCoW, or Critical/High/Medium/Low)
```

### Date Format Validation

```bash
$ specfact project import --bundle my-project --persona product-owner --source backlog.md

Error: Agile/Scrum validation failed:
  - Story STORY-001: Invalid date format '2025/01/15' (expected ISO 8601: YYYY-MM-DD)
  - Story STORY-001: Warning - target date '2024-01-15' is in the past (may need updating)
```

## Best Practices

### 1. Complete DoR Before Sprint Planning

Ensure all stories meet DoR criteria before assigning to sprints:

```bash
# Validate DoR completeness
specfact project import --bundle my-project --persona product-owner --source backlog.md --dry-run
```

### 2. Track Dependencies Early

Identify dependencies during story creation to avoid blockers:

```markdown
**Dependencies**:
**Depends On**:
- STORY-001: User registration (must complete first)
```

### 3. Use Consistent Priority Formats

Choose one priority format per project and use consistently:

- **Option 1**: P0-P3 (recommended for technical teams)
- **Option 2**: MoSCoW (recommended for business-focused teams)
- **Option 3**: Descriptive (Critical/High/Medium/Low)

### 4. Set Business Value for All Stories

Every story should have a clear business value statement:

```markdown
**Business Value**:
Enables users to securely access their accounts, reducing support tickets by 30%.
```

### 5. Use Story Points for Capacity Planning

Track story points to estimate sprint capacity:

```markdown
**Estimated Story Points**: 21  # Sum of all stories in feature
```

## Troubleshooting

### Validation Errors

If import fails with validation errors:

1. **Check DoR Completeness**: Ensure all required fields are present
2. **Verify Dependencies**: Check that all referenced stories/features exist
3. **Validate Formats**: Ensure priority, dates, and story points use correct formats
4. **Review Business Value**: Ensure business value descriptions are present and meaningful

### Template Issues

If template rendering fails:

1. **Check Template Syntax**: Verify Jinja2 syntax is correct
2. **Verify Variables**: Ensure template variables match exported data structure
3. **Test Template**: Use `--dry-run` to test template without importing

## Related Documentation

- [Command Reference - Project Commands](../reference/commands.md#project---project-bundle-management) - Complete command documentation including `project merge` and `project resolve-conflict`
- [Project Bundle Structure](../reference/directory-structure.md) - Project bundle organization
- See [Project Commands](../reference/commands.md#project---project-bundle-management) for template customization options
