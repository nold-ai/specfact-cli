---
layout: default
title: Competitive Analysis
permalink: /competitive-analysis/
---

# What You Gain with SpecFact CLI

How SpecFact CLI complements and extends other development tools.

## Overview

SpecFact CLI is a **brownfield-first legacy code modernization tool** that reverse engineers existing Python code into documented specs, then enforces them as runtime contracts. It builds on the strengths of specification tools like GitHub Spec-Kit and works alongside AI coding platforms to provide production-ready quality gates for legacy codebases.

---

## Building on GitHub Spec-Kit

### What Spec-Kit Does Great

GitHub Spec-Kit pioneered the concept of **living specifications** with interactive slash commands. It's excellent for:

- ✅ **Interactive Specification** - Slash commands (`/speckit.specify`, `/speckit.plan`) with AI assistance
- ✅ **Rapid Prototyping** - Quick spec → plan → tasks → code workflow for **new features**
- ✅ **Learning & Exploration** - Great for understanding state machines, contracts, requirements
- ✅ **IDE Integration** - CoPilot chat makes it accessible to less technical developers
- ✅ **Constitution & Planning** - Add constitution, plans, and feature breakdowns for new features
- ✅ **Single-Developer Projects** - Perfect for personal projects and learning

**Note**: Spec-Kit excels at working with **new features** - you can add constitution, create plans, and break down features for things you're building from scratch.

### What SpecFact CLI Adds To GitHub Spec-Kit

SpecFact CLI **complements Spec-Kit** by adding automation and enforcement:

| Enhancement | What You Get |
|-------------|--------------|
| **Automated enforcement** | Runtime + static contract validation, CI/CD gates |
| **Shared plans** | **Shared structured plans** enable team collaboration with automated bidirectional sync (not just manual markdown sharing like Spec-Kit) |
| **Code vs plan drift detection** | Automated comparison of intended design (manual plan) vs actual implementation (code-derived plan from `import from-code`) |
| **CI/CD integration** | Automated quality gates in your pipeline |
| **Brownfield support** | Analyze existing code to complement Spec-Kit's greenfield focus |
| **Property testing** | FSM fuzzing, Hypothesis-based validation |
| **No-escape gates** | Budget-based enforcement prevents violations |
| **Bidirectional sync** | Keep using Spec-Kit interactively, sync automatically with SpecFact |

### The Journey: From Spec-Kit to SpecFact

**Spec-Kit and SpecFact are complementary, not competitive:**

- **Stage 1: Spec-Kit** - Interactive authoring with slash commands (`/speckit.specify`, `/speckit.plan`)
- **Stage 2: SpecFact** - Automated enforcement (CI/CD gates, contract validation)
- **Stage 3: Bidirectional Sync** - Use both tools together (Spec-Kit authoring + SpecFact enforcement)

**[Learn the full journey →](speckit-journey.md)**

### Seamless Migration

Already using Spec-Kit? SpecFact CLI **imports your work** in one command:

```bash
specfact import from-bridge --adapter speckit --repo ./my-speckit-project --write
```

**Result**: Your Spec-Kit artifacts (spec.md, plan.md, tasks.md) become production-ready contracts with zero manual work.

**Ongoing**: Keep using Spec-Kit interactively, sync automatically with SpecFact:

```bash
# Enable bidirectional sync (bridge-based, adapter-agnostic)
specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional --watch
```

**Best of both worlds**: Interactive authoring (Spec-Kit) + Automated enforcement (SpecFact)

**Team collaboration**: **Shared structured plans** enable multiple developers to work on the same plan with automated deviation detection. Unlike Spec-Kit's manual markdown sharing, SpecFact provides automated bidirectional sync that keeps plans synchronized across team members:

```bash
# Enable bidirectional sync for team collaboration
specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional --watch
# → Automatically syncs Spec-Kit artifacts ↔ SpecFact project bundles
# → Multiple developers can work on the same plan with automated synchronization
# → No manual markdown sharing required

# Detect code vs plan drift automatically
specfact plan compare --bundle legacy-api --code-vs-plan
# → Compares intended design (manual plan = what you planned) vs actual implementation (code-derived plan = what's in your code)
# → Auto-derived plans come from `import from-code` (code analysis), so comparison IS "code vs plan drift"
# → Identifies deviations automatically (not just artifact consistency like Spec-Kit's /speckit.analyze)
```

---

## Working With AI Coding Tools

### What AI Tools Do Great

Tools like **Replit Agent 3, Lovable, Cursor, and Copilot** excel at:

- ✅ Rapid code generation
- ✅ Quick prototyping
- ✅ Learning and exploration
- ✅ Boilerplate reduction

### What SpecFact CLI Adds To AI Coding Tools

SpecFact CLI **validates AI-generated code** with:

| Enhancement | What You Get |
|-------------|--------------|
| **Contract validation** | Ensure AI code meets your specs |
| **Runtime sentinels** | Catch async anti-patterns automatically |
| **No-escape gates** | Block broken code from merging |
| **Offline validation** | Works in air-gapped environments |
| **Evidence trails** | Reproducible proof of quality |
| **Team standards** | Enforce consistent patterns across AI-generated code |
| **CoPilot integration** | Slash commands for seamless IDE workflow |
| **Agent mode routing** | Enhanced prompts for better AI assistance |

### Perfect Combination

**AI tools generate code fast** → **SpecFact CLI ensures it's correct**

Use AI for speed, use SpecFact for quality.

### CoPilot-Enabled Mode

When using Cursor, Copilot, or other AI assistants, SpecFact CLI integrates seamlessly:

```bash
# Slash commands in IDE (after specfact init)
specfact init --ide cursor
/specfact.01-import legacy-api --repo . --confidence 0.7
/specfact.02-plan init legacy-api
/specfact.06-sync --repo . --bidirectional
```

**Benefits:**

- **Automatic mode detection** - Switches to CoPilot mode when available
- **Context injection** - Uses current file, selection, and workspace context
- **Enhanced prompts** - Optimized for AI understanding
- **Agent mode routing** - Specialized prompts for different operations

---

## Key Capabilities

### 1. Temporal Contracts

**What it means**: State machines with runtime validation

**Why developers love it**: Catches state transition bugs automatically

**Example**:

```yaml
# Protocol enforces valid state transitions
transitions:
  - from_state: CONNECTED
    on_event: disconnect
    to_state: DISCONNECTING
    guard: no_pending_messages  # ✅ Checked at runtime
```

### 2. Proof-Carrying Promotion

**What it means**: Evidence required before code merges

**Why developers love it**: "Works on my machine" becomes provable

**Example**:

```bash
# PR includes reproducible evidence
specfact repro --budget 120 --report evidence.md
```

### 3. Brownfield-First ⭐ PRIMARY

**What it means**: **Primary use case** - Reverse engineer existing legacy code into documented specs, then enforce contracts to prevent regressions during modernization.

**Why developers love it**: Understand undocumented legacy code in minutes, not weeks. Modernize with confidence knowing contracts catch regressions automatically.

**Example**:

```bash
# Primary use case: Analyze legacy code
specfact import from-code --bundle legacy-api --repo ./legacy-app

# Extract specs from existing code in < 10 seconds
# Then enforce contracts to prevent regressions
specfact enforce stage --preset balanced
```

**How it complements Spec-Kit**: Spec-Kit focuses on new feature authoring (greenfield); SpecFact CLI's **primary focus** is brownfield code modernization with runtime enforcement.

### 4. Code vs Plan Drift Detection

**What it means**: Automated comparison of intended design (manual plan = what you planned) vs actual implementation (code-derived plan = what's in your code). Auto-derived plans come from `import from-code` (code analysis), so comparison IS "code vs plan drift".

**Why developers love it**: Detects code vs plan drift automatically (not just artifact consistency like Spec-Kit's `/speckit.analyze`). Spec-Kit's `/speckit.analyze` only checks artifact consistency between markdown files; SpecFact CLI detects actual code vs plan drift by comparing manual plans (intended design) with code-derived plans (actual implementation from code analysis).

**Example**:

```bash
# Detect code vs plan drift automatically
specfact plan compare --bundle legacy-api --code-vs-plan
# → Compares intended design (manual plan = what you planned) vs actual implementation (code-derived plan = what's in your code)
# → Auto-derived plans come from `import from-code` (code analysis), so comparison IS "code vs plan drift"
# → Identifies deviations automatically (not just artifact consistency like Spec-Kit's /speckit.analyze)
```

**How it complements Spec-Kit**: Spec-Kit's `/speckit.analyze` only checks artifact consistency between markdown files; SpecFact CLI detects code vs plan drift by comparing manual plans (intended design) with code-derived plans (actual implementation from `import from-code`).

### 5. Evidence-Based

**What it means**: Reproducible validation and reports

**Why developers love it**: Debug failures with concrete data

**Example**:

```bash
# Generate reproducible evidence
specfact repro --report evidence.md
```

### 6. Offline-First

**What it means**: Works without internet connection

**Why developers love it**: Air-gapped environments, no data exfiltration, fast

**Example**:

```bash
# Works completely offline
uvx specfact-cli@latest plan init --interactive
```

---

## When to Use SpecFact CLI

### SpecFact CLI is Perfect For ⭐ PRIMARY

- ✅ **Legacy code modernization** ⭐ - Reverse engineer undocumented code into specs
- ✅ **Brownfield projects** ⭐ - Understand and modernize existing Python codebases
- ✅ **High-risk refactoring** ⭐ - Prevent regressions with runtime contract enforcement
- ✅ **Production systems** - Need quality gates and validation
- ✅ **Team projects** - Multiple developers need consistent standards
- ✅ **Compliance environments** - Evidence-based validation required
- ✅ **Air-gapped deployments** - Offline-first architecture
- ✅ **Open source projects** - Transparent, inspectable tooling

### SpecFact CLI Works Alongside

- ✅ **AI coding assistants** - Validate AI-generated code
- ✅ **Spec-Kit projects** - One-command import
- ✅ **Existing CI/CD** - Drop-in quality gates
- ✅ **Your IDE** - Command-line or extension (v0.2)

---

## Getting Started With SpecFact CLI

### Modernizing Legacy Code? ⭐ PRIMARY

**Reverse engineer existing code**:

```bash
# Primary use case: Analyze legacy codebase
specfact import from-code --bundle legacy-api --repo ./legacy-app
```

See [Use Cases: Brownfield Modernization](use-cases.md#use-case-1-brownfield-code-modernization-primary) ⭐

### Already Using Spec-Kit? (Secondary)

**One-command import**:

```bash
specfact import from-bridge --adapter speckit --repo . --write
```

See [Use Cases: Spec-Kit Migration](use-cases.md#use-case-2-github-spec-kit-migration-secondary)

### Using AI Coding Tools?

**Add validation layer**:

1. Let AI generate code as usual
2. Run `specfact import from-code --repo .` (auto-detects CoPilot mode)
3. Review auto-generated plan
4. Enable `specfact enforce stage --preset balanced`

**With CoPilot Integration:**

Use slash commands directly in your IDE:

```bash
# First, initialize IDE integration
specfact init --ide cursor

# Then use slash commands in IDE chat
/specfact.01-import legacy-api --repo . --confidence 0.7
/specfact.compare --bundle legacy-api
/specfact.06-sync --repo . --bidirectional
```

SpecFact CLI automatically detects CoPilot and switches to enhanced mode.

### Starting From Scratch?

**Greenfield approach**:

1. `specfact plan init --bundle legacy-api --interactive`
2. Add features and stories
3. Enable strict enforcement
4. Let SpecFact guide development

See [Getting Started](../getting-started/README.md) for detailed setup.

---

See [Getting Started](../getting-started/README.md) for quick setup and [Use Cases](use-cases.md) for detailed scenarios.
