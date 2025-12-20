# The Journey: From Spec-Kit to SpecFact

> **Spec-Kit and SpecFact are complementary, not competitive.**  
> **Primary Use Case**: SpecFact CLI for brownfield code modernization  
> **Secondary Use Case**: Add SpecFact enforcement to Spec-Kit's interactive authoring for new features

---

## 🎯 Why Level Up?

### **What Spec-Kit Does Great**

Spec-Kit is **excellent** for:

- ✅ **Interactive Specification** - Slash commands (`/speckit.specify`, `/speckit.plan`) with AI assistance
- ✅ **Rapid Prototyping** - Quick spec → plan → tasks → code workflow for **NEW features**
- ✅ **Learning & Exploration** - Great for understanding state machines, contracts, requirements
- ✅ **IDE Integration** - CoPilot chat makes it accessible to less technical developers
- ✅ **Constitution & Planning** - Add constitution, plans, and feature breakdowns for new features
- ✅ **Single-Developer Projects** - Perfect for personal projects and learning

**Note**: Spec-Kit excels at working with **new features** - you can add constitution, create plans, and break down features for things you're building from scratch.

### **What Spec-Kit Is Designed For (vs. SpecFact CLI)**

Spec-Kit **is designed primarily for**:

- ✅ **Greenfield Development** - Interactive authoring of new features via slash commands
- ✅ **Specification-First Workflow** - Natural language → spec → plan → tasks → code
- ✅ **Interactive AI Assistance** - CoPilot chat-based specification and planning
- ✅ **New Feature Planning** - Add constitution, plans, and feature breakdowns for new features

Spec-Kit **is not designed primarily for** (but SpecFact CLI provides):

- ⚠️ **Work with Existing Code** - **Not designed primarily for analyzing existing repositories or iterating on existing features**
  - Spec-Kit allows you to add constitution, plans, and feature breakdowns for **NEW features** via interactive slash commands
  - Current design focuses on greenfield development and interactive authoring
  - **This is the primary area where SpecFact CLI complements Spec-Kit** 🎯
- ⚠️ **Brownfield Analysis** - Not designed primarily for reverse-engineering from existing code
- ⚠️ **Automated Enforcement** - Not designed for CI/CD gates or automated contract validation
- ⚠️ **Team Collaboration** - Not designed for shared plans or deviation detection between developers
- ⚠️ **Production Quality Gates** - Not designed for proof bundles or budget-based enforcement
- ⚠️ **Multi-Repository Sync** - Not designed for cross-repo consistency validation
- ⚠️ **Deterministic Execution** - Designed for interactive AI interactions rather than scriptable automation

### **When to Level Up**

| Need | Spec-Kit Solution | SpecFact Solution |
|------|------------------|-------------------|
| **Work with existing code** ⭐ **PRIMARY** | ⚠️ **Not designed for** - Focuses on new feature authoring | ✅ **`import from-code`** ⭐ - Reverse-engineer existing code to plans (PRIMARY use case) |
| **Iterate on existing features** ⭐ **PRIMARY** | ⚠️ **Not designed for** - Focuses on new feature planning | ✅ **Auto-derive plans** ⭐ - Understand existing features from code (PRIMARY use case) |
| **Brownfield projects** ⭐ **PRIMARY** | ⚠️ **Not designed for** - Designed primarily for greenfield | ✅ **Brownfield analysis** ⭐ - Work with existing projects (PRIMARY use case) |
| **Team collaboration** | Manual sharing, no sync | **Shared structured plans** (automated bidirectional sync for team collaboration), automated deviation detection |
| **CI/CD integration** | Manual validation | Automated gates, proof bundles |
| **Production deployment** | Manual checklist | Automated quality gates |
| **Code review** | Manual review | Automated deviation detection |
| **Compliance** | Manual audit | Proof bundles, reproducible checks |

---

## 🌱 Brownfield Modernization with SpecFact + Spec-Kit

### **Best of Both Worlds for Legacy Code**

When modernizing legacy code, you can use **both tools together** for maximum value:

1. **Spec-Kit** for initial spec generation (fast, LLM-powered)
2. **SpecFact** for runtime contract enforcement (safety net)
3. **Spec-Kit** maintains documentation (living specs)
4. **SpecFact** prevents regressions (contract enforcement)

### **Workflow: Legacy Code → Modernized Code**

```bash
# Step 1: Use SpecFact to extract specs from legacy code
specfact import from-code --bundle customer-portal --repo ./legacy-app

# Output: Auto-generated project bundle from existing code
# ✅ Analyzed 47 Python files
# ✅ Extracted 23 features
# ✅ Generated 112 user stories
# ⏱️  Completed in 8.2 seconds
# 📁 Project bundle: .specfact/projects/customer-portal/

# Step 2: (Optional) Use Spec-Kit to refine specs interactively
# /speckit.specify --feature "Payment Processing"
# /speckit.plan --feature "Payment Processing"

# Step 3: Use SpecFact to add runtime contracts
# Add @icontract decorators to critical paths

# Step 4: Modernize safely with contract safety net
# Refactor knowing contracts will catch regressions

# Step 5: Keep both in sync
specfact sync bridge --adapter speckit --bundle customer-portal --repo . --bidirectional --watch
```

### **Why This Works**

- **SpecFact code2spec** extracts specs from undocumented legacy code automatically
- **Spec-Kit interactive authoring** refines specs with LLM assistance
- **SpecFact runtime contracts** prevent regressions during modernization
- **Spec-Kit documentation** maintains living specs for team

**Result:** Fast spec generation + runtime safety net = confident modernization

### **See Also**

- **[Brownfield Engineer Guide](brownfield-engineer.md)** - Complete brownfield workflow
- **[Brownfield Journey](brownfield-journey.md)** - Step-by-step modernization guide
- **[Spec-Kit Comparison](speckit-comparison.md)** - Detailed comparison

---

## 🚀 The Onboarding Journey

### **Stage 1: Discovery** ("What is SpecFact?")

**Time**: < 5 minutes

Learn how SpecFact complements Spec-Kit:

```bash
# See it in action
specfact --help

# Read the docs
cat docs/getting-started.md
```

**What you'll discover**:

- ✅ SpecFact imports your Spec-Kit artifacts automatically
- ✅ Automated enforcement (CI/CD gates, contract validation)
- ✅ **Shared plans** (bidirectional sync for team collaboration)
- ✅ **Code vs plan drift detection** (automated deviation detection)
- ✅ Production readiness (quality gates, proof bundles)

**Key insight**: SpecFact **preserves** your Spec-Kit workflow - you can use both tools together!

---

### **Stage 2: First Import** ("Try It Out")

**Time**: < 60 seconds

Import your Spec-Kit project to see what SpecFact adds:

```bash
# 1. Preview what will be imported
specfact import from-bridge --adapter speckit --repo ./my-speckit-project --dry-run

# 2. Execute import (one command) - bundle name will be auto-detected or you can specify with --bundle
specfact import from-bridge --adapter speckit --repo ./my-speckit-project --write

# 3. Review generated bundle using CLI commands
specfact plan review --bundle <bundle-name>
```

**What was created**:

- Modular project bundle at `.specfact/projects/<bundle-name>/` (multiple aspect files)
- `.specfact/protocols/workflow.protocol.yaml` (from FSM if detected)
- `.specfact/gates/config.yaml` (quality gates configuration)

**Note**: Use CLI commands to interact with bundles. Do not edit `.specfact` files directly.

**What happens**:

1. **Parses Spec-Kit artifacts**: `specs/[###-feature-name]/spec.md`, `plan.md`, `tasks.md`, `.specify/memory/constitution.md`
2. **Generates SpecFact plans**: Converts Spec-Kit features/stories → SpecFact models
3. **Creates enforcement config**: Quality gates, CI/CD integration
4. **Preserves Spec-Kit artifacts**: Your original files remain untouched

**Result**: Your Spec-Kit specs become production-ready contracts with automated quality gates!

---

### **Stage 3: Adoption** ("Use Both Together")

**Time**: Ongoing (automatic)

Keep using Spec-Kit interactively, sync automatically with SpecFact:

```bash
# Enable bidirectional sync (bridge-based, adapter-agnostic)
specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional --watch
```

**Workflow**:

```bash
# 1. Continue using Spec-Kit interactively (slash commands)
/speckit.specify --feature "User Authentication"
/speckit.plan --feature "User Authentication"
/speckit.tasks --feature "User Authentication"

# 2. SpecFact automatically syncs new artifacts (watch mode)
# → Detects changes in specs/[###-feature-name]/
# → Imports new spec.md, plan.md, tasks.md
# → Updates .specfact/projects/<bundle-name>/ aspect files
# → Enables shared plans for team collaboration

# 3. Detect code vs plan drift automatically
specfact plan compare --code-vs-plan
# → Compares intended design (manual plan = what you planned) vs actual implementation (code-derived plan = what's in your code)
# → Identifies deviations automatically (not just artifact consistency like Spec-Kit's /speckit.analyze)
# → Auto-derived plans come from `import from-code` (code analysis), so comparison IS "code vs plan drift"

# 4. Enable automated enforcement
specfact enforce stage --preset balanced

# 5. CI/CD automatically validates (GitHub Action)
# → Runs on every PR
# → Blocks HIGH severity issues
# → Generates proof bundles
```

**What you get**:

- ✅ **Interactive authoring** (Spec-Kit): Use slash commands for rapid prototyping
- ✅ **Automated enforcement** (SpecFact): CI/CD gates catch issues automatically
- ✅ **Team collaboration** (SpecFact): Shared plans, deviation detection
- ✅ **Production readiness** (SpecFact): Quality gates, proof bundles

**Best of both worlds**: Spec-Kit for authoring, SpecFact for enforcement!

---

### **Stage 4: Migration** ("Full SpecFact Workflow")

**Time**: Progressive (1-4 weeks)

**Optional**: Migrate to full SpecFact workflow (or keep using both tools together)

#### **Week 1: Import + Sync**

```bash
# Import existing Spec-Kit project
specfact import from-bridge --adapter speckit --repo . --write

# Enable bidirectional sync (bridge-based, adapter-agnostic)
specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional --watch
```

**Result**: Both tools working together seamlessly.

#### **Week 2-3: Enable Enforcement (Shadow Mode)**

```bash
# Start in shadow mode (observe only)
specfact enforce stage --preset minimal

# Set up CrossHair for contract exploration
specfact repro setup

# Review what would be blocked
specfact repro --verbose

# Apply auto-fixes for violations (if available)
specfact repro --fix --verbose
```

**Result**: See what SpecFact would catch, no blocking yet. Auto-fixes can be applied for Semgrep violations.

#### **Week 4: Enable Balanced Enforcement**

```bash
# Enable balanced mode (block HIGH, warn MEDIUM)
specfact enforce stage --preset balanced

# Test with real PR
git checkout -b test-enforcement
# Make a change that violates contracts
specfact repro  # Should block HIGH issues

# Or apply auto-fixes first
specfact repro --fix  # Apply Semgrep auto-fixes, then validate
```

**Result**: Automated enforcement catching critical issues. Auto-fixes can be applied before validation.

#### **Week 5+: Full SpecFact Workflow** (Optional)

```bash
# Enable strict enforcement
specfact enforce stage --preset strict

# Full automation (CI/CD, brownfield analysis, etc.)
# (CrossHair setup already done in Week 3)
specfact repro --budget 120 --verbose
```

**Result**: Complete SpecFact workflow - or keep using both tools together!

---

## 📋 Step-by-Step Migration

### **Step 1: Preview Migration**

```bash
# See what will be imported (safe - no changes)
specfact import from-bridge --adapter speckit --repo ./my-speckit-project --dry-run
```

**Expected Output**:

```bash
🔍 Analyzing Spec-Kit project via bridge adapter...
✅ Found .specify/ directory (modern format)
✅ Found specs/001-user-authentication/spec.md
✅ Found specs/001-user-authentication/plan.md
✅ Found specs/001-user-authentication/tasks.md
✅ Found .specify/memory/constitution.md

**💡 Tip**: If constitution is missing or minimal, run `specfact bridge constitution bootstrap --repo .` to auto-generate from repository analysis.

📊 Migration Preview:
  - Will create: .specfact/projects/<bundle-name>/ (modular project bundle)
  - Will create: .specfact/protocols/workflow.protocol.yaml (if FSM detected)
  - Will create: .specfact/gates/config.yaml
  - Will convert: Spec-Kit features → SpecFact Feature models
  - Will convert: Spec-Kit user stories → SpecFact Story models
  
🚀 Ready to migrate (use --write to execute)
```

### **Step 2: Execute Migration**

```bash
# Execute migration (creates SpecFact artifacts)
specfact import from-bridge \
  --adapter speckit \
  --repo ./my-speckit-project \
  --write \
  --report migration-report.md
```

**What it does**:

1. **Parses Spec-Kit artifacts** (via bridge adapter):
   - `specs/[###-feature-name]/spec.md` → Features, user stories, requirements
   - `specs/[###-feature-name]/plan.md` → Technical context, architecture
   - `specs/[###-feature-name]/tasks.md` → Tasks, story mappings
   - `.specify/memory/constitution.md` → Principles, constraints

2. **Generates SpecFact artifacts**:
   - `.specfact/projects/<bundle-name>/` - Modular project bundle (multiple aspect files)
   - `.specfact/protocols/workflow.protocol.yaml` - FSM protocol (if detected)
   - `.specfact/gates/config.yaml` - Quality gates configuration

3. **Preserves Spec-Kit artifacts**:
   - Original files remain untouched
   - Bidirectional sync keeps both aligned

### **Step 3: Review Generated Artifacts**

```bash
# Review plan bundle using CLI commands
specfact plan review --bundle <bundle-name>

# Review enforcement config using CLI commands
specfact enforce show-config

# Review migration report
cat migration-report.md
```

**Note**: Use CLI commands to interact with bundles. Do not edit `.specfact` files directly.

**What to check**:

- ✅ Features/stories correctly mapped from Spec-Kit
- ✅ Acceptance criteria preserved
- ✅ Business context extracted from constitution
- ✅ Enforcement config matches your needs

### **Step 4: Enable Shared Plans (Bidirectional Sync)**

**Shared structured plans** enable team collaboration with automated bidirectional sync. Unlike Spec-Kit's manual markdown sharing, SpecFact automatically keeps plans synchronized across team members.

```bash
# One-time sync
specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional

# Continuous watch mode (recommended for team collaboration)
specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional --watch --interval 5
```

**What it syncs**:

- **Spec-Kit → SpecFact**: New `spec.md`, `plan.md`, `tasks.md` → Updated `.specfact/projects/<bundle-name>/` aspect files
- **SpecFact → Spec-Kit**: Changes to `.specfact/projects/<bundle-name>/` → Updated Spec-Kit markdown with all required fields auto-generated:
  - **spec.md**: Frontmatter, INVSEST criteria, Scenarios (Primary, Alternate, Exception, Recovery)
  - **plan.md**: Constitution Check, Phases, Technology Stack (from constraints)
  - **tasks.md**: Phase organization, Story mappings ([US1], [US2]), Parallel markers
- **Team collaboration**: Multiple developers can work on the same plan with automated synchronization
- **No manual editing required**: All Spec-Kit fields are auto-generated - ready for `/speckit.analyze` without additional work

### **Step 5: Enable Enforcement**

```bash
# Week 1-2: Shadow mode (observe only)
specfact enforce stage --preset minimal

# Week 3-4: Balanced mode (block HIGH, warn MEDIUM)
specfact enforce stage --preset balanced

# Week 5+: Strict mode (block MEDIUM+)
specfact enforce stage --preset strict
```

### **Step 6: Validate**

```bash
# Set up CrossHair for contract exploration (one-time setup)
specfact repro setup

# Run all checks
specfact repro --verbose

# Check CI/CD integration
git push origin feat/specfact-migration
# → GitHub Action runs automatically
# → PR blocked if HIGH severity issues found
```

---

## 💡 Best Practices

### **1. Start in Shadow Mode**

```bash
# Always start with shadow mode (no blocking)
specfact enforce stage --preset minimal
specfact repro
```

**Why**: See what SpecFact would catch before enabling blocking.

### **2. Use Shared Plans (Bidirectional Sync)**

```bash
# Enable bidirectional sync for team collaboration
specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional --watch
```

**Why**: **Shared structured plans** enable team collaboration with automated bidirectional sync. Unlike Spec-Kit's manual markdown sharing, SpecFact automatically keeps plans synchronized across team members. Continue using Spec-Kit interactively, get SpecFact automation automatically.

### **3. Progressive Enforcement**

```bash
# Week 1: Shadow (observe)
specfact enforce stage --preset minimal

# Week 2-3: Balanced (block HIGH)
specfact enforce stage --preset balanced

# Week 4+: Strict (block MEDIUM+)
specfact enforce stage --preset strict
```

**Why**: Gradual adoption reduces disruption and builds team confidence.

### **4. Keep Spec-Kit Artifacts**

**Don't delete Spec-Kit files** - they're still useful:

- ✅ Interactive authoring (slash commands)
- ✅ Fallback if SpecFact has issues
- ✅ Team members who prefer Spec-Kit workflow

**Bidirectional sync** keeps both aligned automatically.

---

## ❓ FAQ

### **Q: Do I need to stop using Spec-Kit?**

**A**: No! SpecFact works **alongside** Spec-Kit. Use Spec-Kit for interactive authoring (new features), SpecFact for automated enforcement and existing code analysis.

### **Q: What happens to my Spec-Kit artifacts?**

**A**: They're **preserved** - SpecFact imports them but doesn't modify them. Bidirectional sync keeps both aligned.

### **Q: Can I export back to Spec-Kit?**

**A**: Yes! SpecFact can export back to Spec-Kit format. Your original files are never modified.

### **Q: What if I prefer Spec-Kit workflow?**

**A**: Keep using Spec-Kit! Bidirectional sync automatically keeps SpecFact artifacts updated. Use SpecFact for CI/CD enforcement and brownfield analysis.

### **Q: Does SpecFact replace Spec-Kit?**

**A**: No - they're **complementary**. Spec-Kit excels at interactive authoring for new features, SpecFact adds automation, enforcement, and brownfield analysis capabilities.

---

## 🔗 Related Documentation

- **[Getting Started](../getting-started/README.md)** - Quick setup guide
- **[Use Cases](use-cases.md)** - Detailed Spec-Kit migration use case
- **[Commands](../reference/commands.md)** - `import from-bridge` and `sync bridge` reference
- **[Architecture](../reference/architecture.md)** - How SpecFact integrates with Spec-Kit

---

**Next Steps**:

1. **Try it**: `specfact import from-bridge --adapter speckit --repo . --dry-run`
2. **Import**: `specfact import from-bridge --adapter speckit --repo . --write`
3. **Sync**: `specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional --watch`
4. **Enforce**: `specfact enforce stage --preset minimal` (start shadow mode)

---

> **Remember**: Spec-Kit and SpecFact are complementary. Use Spec-Kit for interactive authoring, add SpecFact for automated enforcement. Best of both worlds! 🚀
