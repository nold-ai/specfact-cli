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
- ✅ Backward compatibility with template-based sidecar workspaces

**When to use**:

- Validating third-party libraries without forking
- Testing legacy codebases where modifications are risky
- Contract validation of APIs where you don't control implementation
- Framework validation (Django, FastAPI, DRF, Flask) using extracted routes

**Key difference**: Sidecar validation provides **external codebase validation** without source modification, while standard SpecFact workflows analyze and modify your own codebase.

**See also**: [Sidecar Validation Guide](./sidecar-validation.md) | [Command Chains - Sidecar Validation](./command-chains.md#5-sidecar-validation-chain)

---

## DevOps & Backlog

### DevOps Adapter Integration

**Purpose**: Sync change proposals to DevOps backlog tools and track progress

**What it provides**:

- ✅ Export OpenSpec change proposals to GitHub Issues (or other DevOps tools)
- ✅ Automatic progress tracking via code change detection
- ✅ Content sanitization for public repositories
- ✅ Separate repository support (OpenSpec proposals and code in different repos)
- ✅ Automated comment annotations on issues

**Supported adapters**:

- **GitHub Issues** (`--adapter github`) - ✅ Full support
- **Azure DevOps** (`--adapter ado`) - Planned
- **Linear** (`--adapter linear`) - Planned
- **Jira** (`--adapter jira`) - Planned

**When to use**:

- Syncing OpenSpec change proposals to GitHub Issues
- Tracking implementation progress automatically
- Managing change proposals in DevOps backlog tools
- Coordinating between OpenSpec repositories and code repositories

**Key difference**: DevOps adapters provide **backlog integration and progress tracking**, while OpenSpec provides **specification management**.

**See also**: [DevOps Adapter Integration Guide](./devops-adapter-integration.md)

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
├─ Need to sync change proposals to backlog?
│  └─ ✅ Use DevOps adapter integration (GitHub Issues, etc.)
│
└─ Need AI-assisted development?
   └─ ✅ Use AI IDE integration (slash commands, AI workflows)
```

---

## Integration Combinations

### Common Workflows

#### 1. Brownfield Modernization with OpenSpec

- Use SpecFact CLI `import from-code` to analyze existing code
- Export to OpenSpec for specification anchoring
- Use OpenSpec change proposals for tracking improvements
- Sync proposals to GitHub Issues via DevOps adapter

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
