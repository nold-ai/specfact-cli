# Integrations Overview

> **Comprehensive guide to all SpecFact CLI integrations**  
> Understand when to use each integration and how they work together

---

## Overview

SpecFact CLI integrates with multiple tools and platforms to provide a complete spec-driven development ecosystem. This guide provides an overview of all available integrations, when to use each, and how they complement each other.

---

## Integration Categories

SpecFact CLI integrations fall into four main categories:

1. **Specification Tools** - Tools for creating and managing specifications
2. **Testing & Validation** - Tools for contract testing and validation
3. **DevOps & Backlog** - Tools for syncing change proposals and tracking progress
4. **IDE & Development** - Tools for AI-assisted development workflows

---

## Specification Tools

### Spec-Kit Integration

**Purpose**: Interactive specification authoring for new features

**What it provides**:

- ✅ Interactive slash commands (`/speckit.specify`, `/speckit.plan`) with AI assistance
- ✅ Rapid prototyping workflow: spec → plan → tasks → code
- ✅ Constitution and planning for new features
- ✅ IDE integration with CoPilot chat

**When to use**:

- Creating new features from scratch (greenfield development)
- Interactive specification authoring with AI assistance
- Learning and exploration of state machines and contracts
- Single-developer projects and rapid prototyping

**Key difference**: Spec-Kit focuses on **new feature authoring**, while SpecFact CLI focuses on **brownfield code modernization**.

**See also**: [Spec-Kit Journey Guide](./speckit-journey.md)

---

### OpenSpec Integration

**Purpose**: Specification anchoring and change tracking

**What it provides**:

- ✅ Source-of-truth specifications (`openspec/specs/`) documenting what IS built
- ✅ Change tracking with delta specs (ADDED/MODIFIED/REMOVED)
- ✅ Structured change proposals (`openspec/changes/`) with rationale and tasks
- ✅ Cross-repository support (specs can live separately from code)
- ✅ Spec-driven development workflow: proposal → delta specs → implementation → archive

**When to use**:

- Managing specifications as source of truth
- Tracking changes with structured proposals
- Cross-repository workflows (specs in different repos than code)
- Team collaboration on specifications and change proposals

**Key difference**: OpenSpec manages **what should be built** (proposals) and **what is built** (specs), while SpecFact CLI adds **brownfield analysis** and **runtime enforcement**.

**See also**: [OpenSpec Journey Guide](./openspec-journey.md)

---

## Testing & Validation

> **New in v0.24.0**: [Sidecar Validation](./sidecar-validation.md) - Validate external codebases without modifying source code

### Specmatic Integration

**Purpose**: API contract testing and validation

**What it provides**:

- ✅ OpenAPI/AsyncAPI specification validation
- ✅ Backward compatibility checking between spec versions
- ✅ Mock server generation from specifications
- ✅ Test suite generation from specs
- ✅ Service-level contract testing (complements SpecFact's code-level contracts)

**When to use**:

- Validating API specifications (OpenAPI/AsyncAPI)
- Checking backward compatibility when updating API versions
- Running mock servers for frontend/client development
- Generating contract tests from specifications
- Service-level contract validation (complements code-level contracts)

**Key difference**: Specmatic provides **API-level contract testing**, while SpecFact CLI provides **code-level contract enforcement** (icontract, beartype, CrossHair).

**See also**: [Specmatic Integration Guide](./specmatic-integration.md)

---

### Sidecar Validation Integration 🆕

**Purpose**: Validate external codebases without modifying source code

**What it provides**:

- ✅ Framework detection (Django, FastAPI, DRF, Flask, pure Python)
- ✅ Route and schema extraction from framework patterns
- ✅ Automatic OpenAPI contract population
- ✅ CrossHair harness generation for symbolic execution
- ✅ CrossHair and Specmatic validation execution
- ✅ Environment manager detection (hatch, poetry, uv, pip, venv)

**When to use**:

- Validating third-party libraries without forking
- Testing legacy codebases where modifications are risky
- Contract validation of APIs where you don't control implementation
- Framework validation (Django, FastAPI, DRF, Flask) using extracted routes

**Key difference**: Sidecar validation provides **external codebase validation** without source modification, while standard SpecFact workflows analyze and modify your own codebase.

**See also**: [Sidecar Validation Guide](./sidecar-validation.md) | [Command Chains - Sidecar Validation](./command-chains.md#5-sidecar-validation-chain)

---

## DevOps & Backlog

### DevOps Adapter Integration 🆕 **NEW FEATURE**

**Purpose**: Integrate SpecFact into agile DevOps workflows with bidirectional backlog synchronization

**What it provides**:

- ✅ **Bidirectional sync** - Export OpenSpec change proposals to GitHub Issues AND import GitHub Issues as change proposals
- ✅ **Automatic progress tracking** - Detect code changes and automatically add progress comments to issues
- ✅ **Status synchronization** - Keep OpenSpec change proposal status in sync with GitHub issue labels
- ✅ **Content sanitization** - Protect internal information when syncing to public repositories
- ✅ **Separate repository support** - Handle cases where OpenSpec proposals and code are in different repos
- ✅ **Validation reporting** - Automatically report validation results to GitHub Issues
- ✅ **Conflict resolution** - Smart conflict resolution when status differs between OpenSpec and backlog

**Supported adapters**:

- **GitHub Issues** (`--adapter github`) - ✅ Full bidirectional support
- **Azure DevOps** (`--adapter ado`) - ✅ Full bidirectional support
- **Linear** (`--adapter linear`) - Planned
- **Jira** (`--adapter jira`) - Planned

**When to use**:

- **Integrating SpecFact into agile DevOps workflows** - Keep your backlog in sync with your specifications
- Syncing OpenSpec change proposals to GitHub Issues for sprint planning
- Importing GitHub Issues as change proposals to track work in OpenSpec
- Tracking implementation progress automatically via code change detection
- Managing change proposals in DevOps backlog tools alongside your code
- Coordinating between OpenSpec repositories and code repositories

**Key difference**: DevOps adapters provide **backlog integration and progress tracking**, enabling SpecFact to integrate seamlessly into agile DevOps workflows. This bridges the gap between specification management (OpenSpec) and backlog management (GitHub Issues, ADO, Linear, Jira).

**Why this matters**: This feature allows you to use SpecFact's specification-driven development approach while working within your existing agile DevOps workflows. Change proposals become backlog items, and backlog items become change proposals—keeping everything in sync automatically.

**See also**: [DevOps Adapter Integration Guide](./devops-adapter-integration.md) | [GitHub Adapter Reference](../adapters/github.md) | [Azure DevOps Adapter Reference](../adapters/azuredevops.md) | [Backlog Adapter Patterns](../adapters/backlog-adapter-patterns.md)

---

### Backlog Refinement 🆕 **NEW FEATURE**

**Purpose**: AI-assisted template-driven refinement for standardizing work items from DevOps backlogs

**What it provides**:

- ✅ **Template detection** - Automatically detects which template (user story, defect, spike, enabler) matches a backlog item
- ✅ **AI-assisted refinement** - Generates prompts for IDE AI copilots to refine unstructured input into template-compliant format
- ✅ **Priority-based template resolution** - Resolves templates using provider+framework+persona priority chain
- ✅ **Agile filtering** - Filter by sprint, release, iteration, labels, state, assignee for agile workflows
- ✅ **Persona/framework support** - Filter templates by persona (product-owner, architect, developer) and framework (scrum, safe, kanban)
- ✅ **Definition of Ready (DoR) validation** - Check DoR rules before adding items to sprints with repo-level configuration
- ✅ **Preview/write safety** - Preview mode by default, explicit `--write` flag for writeback
- ✅ **Lossless preservation** - Preserves original backlog data for round-trip synchronization
- ✅ **Sprint/release extraction** - Automatically extracts sprint and release information from GitHub milestones and ADO iteration paths

**Supported adapters**:

- **GitHub Issues** (`--adapter github`) - ✅ Full support with milestone extraction
- **Azure DevOps** (`--adapter ado`) - ✅ Full support with iteration path extraction
- **Jira, Linear** - Planned (extensible architecture)

**When to use**:

- **Standardizing backlog items** - Transform arbitrary DevOps backlog input into structured, template-compliant format
- **Sprint planning preparation** - Refine items before adding to sprints with DoR validation
- **Template enforcement** - Enforce corporate templates (user stories, defects, spikes, enablers) across teams
- **Agile workflow integration** - Filter by sprint, release, iteration for common agile/scrum workflows
- **Persona-specific refinement** - Use role-specific templates (product-owner, architect, developer)
- **Framework-specific refinement** - Use methodology-specific templates (scrum, safe, kanban)

**Key difference**: Backlog refinement provides **template-driven standardization** of backlog items, while DevOps adapter integration provides **bidirectional synchronization** between OpenSpec and backlog tools. Use together: refine items → sync to OpenSpec → track progress.

**Why this matters**: DevOps teams often create backlog items with informal, unstructured descriptions. Backlog refinement helps enforce corporate standards while maintaining lossless synchronization with your backlog tools, enabling seamless integration into agile workflows.

**See also**: [Backlog Refinement Guide](./backlog-refinement.md) | [DevOps Adapter Integration Guide](./devops-adapter-integration.md)

---

## IDE & Development

### AI IDE Integration

**Purpose**: AI-assisted development workflows with slash commands

**What it provides**:

- ✅ Setup process (`init --ide cursor`) for IDE integration
- ✅ Slash commands for common workflows
- ✅ Prompt generation → AI IDE → validation loop
- ✅ Integration with command chains
- ✅ AI-assisted specification and planning

**When to use**:

- AI-assisted development workflows
- Using slash commands for common tasks
- Integrating SpecFact CLI with Cursor, VS Code + Copilot
- Streamlining development workflows with AI assistance

**Key difference**: AI IDE integration provides **interactive AI assistance**, while command chains provide **automated workflows**.

**See also**: [AI IDE Workflow Guide](./ai-ide-workflow.md), [IDE Integration Guide](./ide-integration.md)

---

## Integration Decision Tree

Use this decision tree to determine which integrations to use:

```text
Start: What do you need?

├─ Need to work with existing code?
│  └─ ✅ Use SpecFact CLI `import from-code` (brownfield analysis)
│
├─ Need to create new features interactively?
│  └─ ✅ Use Spec-Kit integration (greenfield development)
│
├─ Need to manage specifications as source of truth?
│  └─ ✅ Use OpenSpec integration (specification anchoring)
│
├─ Need API contract testing?
│  └─ ✅ Use Specmatic integration (API-level contracts)
│
├─ Need to integrate SpecFact into agile DevOps workflows?
│  ├─ Need to standardize backlog items? → Use backlog refinement (template-driven standardization)
│  └─ Need bidirectional sync? → Use DevOps adapter integration (GitHub Issues, etc.) - Bidirectional sync with backlog
│
└─ Need AI-assisted development?
   └─ ✅ Use AI IDE integration (slash commands, AI workflows)
```

---

## Integration Combinations

### Common Workflows

#### 1. Brownfield Modernization with OpenSpec and DevOps Integration

- Use SpecFact CLI `import from-code` to analyze existing code
- Export to OpenSpec for specification anchoring
- Use OpenSpec change proposals for tracking improvements
- **Sync proposals to GitHub Issues via DevOps adapter** - Integrate into agile DevOps workflows
- **Import GitHub Issues as change proposals** - Keep backlog and specs in sync
- **Automatic progress tracking** - Code changes automatically update GitHub Issues

#### 2. Greenfield Development with Spec-Kit

- Use Spec-Kit for interactive specification authoring
- Add SpecFact CLI enforcement for runtime contracts
- Use Specmatic for API contract testing
- Integrate with AI IDE for streamlined workflows

#### 3. Full Stack Development

- Use Spec-Kit/OpenSpec for specification management
- Use SpecFact CLI for code-level contract enforcement
- Use Specmatic for API-level contract testing
- Use DevOps adapter for backlog integration
- Use AI IDE integration for development workflows

---

## Quick Reference

| Integration | Primary Use Case | Key Command | Documentation |
|------------|------------------|-------------|---------------|
| **Spec-Kit** | Interactive spec authoring for new features | `/speckit.specify` | [Spec-Kit Journey](./speckit-journey.md) |
| **OpenSpec** | Specification anchoring and change tracking | `openspec validate` | [OpenSpec Journey](./openspec-journey.md) |
| **Specmatic** | API contract testing and validation | `spec validate` | [Specmatic Integration](./specmatic-integration.md) |
| **Sidecar Validation** 🆕 | Validate external codebases without modifying source | `validate sidecar init/run` | [Sidecar Validation](./sidecar-validation.md) |
| **DevOps Adapter** | Sync proposals to backlog tools | `sync bridge --adapter github` | [DevOps Integration](./devops-adapter-integration.md) |
| **Backlog Refinement** 🆕 | Standardize backlog items with templates | `backlog refine github --sprint "Sprint 1"` | [Backlog Refinement](./backlog-refinement.md) |
| **AI IDE** | AI-assisted development workflows | `init --ide cursor` | [AI IDE Workflow](./ai-ide-workflow.md) |

---

## Getting Started

1. **Choose your primary integration** based on your use case:
   - Working with existing code? → Start with SpecFact CLI brownfield analysis
   - Creating new features? → Start with Spec-Kit integration
   - Managing specifications? → Start with OpenSpec integration

2. **Add complementary integrations** as needed:
   - Need API testing? → Add Specmatic
   - Need backlog sync? → Add DevOps adapter
   - Want AI assistance? → Add AI IDE integration

3. **Follow the detailed guides** for each integration you choose

---

## See Also

- [Command Chains Guide](./command-chains.md) - Complete workflows using integrations
- [Common Tasks Guide](./common-tasks.md) - Quick reference for common integration tasks
- [Team Collaboration Workflow](./team-collaboration-workflow.md) - Using integrations in teams
- [Migration Guide](./migration-guide.md) - Migrating between integrations

---

## Related Workflows

- [Brownfield Modernization Chain](./command-chains.md#brownfield-modernization-chain) - Using SpecFact CLI with existing code
- [API Contract Development Chain](./command-chains.md#api-contract-development-chain) - Using Specmatic for API testing
- [Spec-Driven Development Chain](./command-chains.md#spec-driven-development-chain) - Using OpenSpec for spec management
- [AI IDE Workflow Chain](./command-chains.md#ai-ide-workflow-chain) - Using AI IDE integration
