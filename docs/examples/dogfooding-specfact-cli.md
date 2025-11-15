# Real-World Example: SpecFact CLI Analyzing Itself

> **TL;DR**: We ran SpecFact CLI on its own codebase. It discovered **19 features** and **49 stories** in **under 3 seconds**. When we compared the auto-derived plan against our manual plan, it found **24 deviations** and blocked the merge (as configured). Total time: **< 10 seconds**. 🚀
> **Note**: "Dogfooding" is a well-known tech term meaning "eating your own dog food" - using your own product. It's a common practice in software development to validate that tools work in real-world scenarios.

---

## The Challenge

We built SpecFact CLI and wanted to validate that it actually works in the real world. So we did what every good developer does: **we dogfooded it**.

**Goal**: Analyze the SpecFact CLI codebase itself and demonstrate:

1. How fast brownfield analysis is
2. How enforcement actually blocks bad code
3. How the complete workflow works end-to-end

---

## Step 1: Brownfield Analysis (3 seconds ⚡)

First, we analyzed the existing codebase to see what features it discovered:

```bash
specfact import from-code --repo . --confidence 0.5
```

**Output**:

```bash
🔍 Analyzing Python files...
✓ Found 19 features
✓ Detected themes: CLI, Validation
✓ Total stories: 49

✓ Analysis complete!
Plan bundle written to: .specfact/plans/specfact-cli.2025-10-30T16-57-51.bundle.yaml
```

### What It Discovered

The brownfield analysis extracted **19 features** from our codebase:

| Feature | Stories | Confidence | What It Does |
|---------|---------|------------|--------------|
| Enforcement Config | 3 | 0.9 | Configuration for contract enforcement and quality gates |
| Code Analyzer | 2 | 0.7 | Analyzes Python code to auto-derive plan bundles |
| Plan Comparator | 1 | 0.7 | Compares two plan bundles to detect deviations |
| Report Generator | 3 | 0.9 | Generator for validation and deviation reports |
| Protocol Generator | 3 | 0.9 | Generator for protocol YAML files |
| Plan Generator | 3 | 0.9 | Generator for plan bundle YAML files |
| FSM Validator | 3 | 1.0 | FSM validator for protocol validation |
| Schema Validator | 2 | 0.7 | Schema validator for plan bundles and protocols |
| Git Operations | 5 | 1.0 | Helper class for Git operations |
| Logger Setup | 3 | 1.0 | Utility class for standardized logging setup |
| ... and 9 more | 21 | - | Supporting utilities and infrastructure |

**Total**: **49 user stories** auto-generated with Fibonacci story points (1, 2, 3, 5, 8, 13...)

### Sample Auto-Generated Story

Here's what the analyzer extracted from our `EnforcementConfig` class:

```yaml
- key: STORY-ENFORCEMENTCONFIG-001
  title: As a developer, I can configure Enforcement Config
  acceptance:
    - Configuration functionality works as expected
  tags: []
  story_points: 2
  value_points: 3
  tasks:
    - __init__()
  confidence: 0.6
  draft: false
```

**Time taken**: ~3 seconds for 19 Python files

> **💡 How does it work?** SpecFact CLI uses **AI-first approach** (LLM) in CoPilot mode for semantic understanding and multi-language support, with **AST-based fallback** in CI/CD mode for fast, deterministic Python-only analysis. [Read the technical deep dive →](../technical/code2spec-analysis-logic.md)

---

## Step 2: Set Enforcement Rules (1 second 🎯)

Next, we configured quality gates to block HIGH severity violations:

```bash
specfact enforce stage --preset balanced
```

**Output**:

```bash
Setting enforcement mode: balanced
  Enforcement Mode:  
      BALANCED       
┏━━━━━━━━━━┳━━━━━━━━┓
┃ Severity ┃ Action ┃
┡━━━━━━━━━━╇━━━━━━━━┩
│ HIGH     │ BLOCK  │
│ MEDIUM   │ WARN   │
│ LOW      │ LOG    │
└──────────┴────────┘

✓ Enforcement mode set to balanced
Configuration saved to: .specfact/gates/config/enforcement.yaml
```

**What this means**:

- 🚫 **HIGH** severity deviations → **BLOCK** the merge (exit code 1)
- ⚠️ **MEDIUM** severity deviations → **WARN** but allow (exit code 0)
- 📝 **LOW** severity deviations → **LOG** silently (exit code 0)

---

## Step 3: Create Manual Plan (30 seconds ✍️)

We created a minimal manual plan with just 2 features we care about:

```yaml
features:
  - key: FEATURE-ENFORCEMENT
    title: Contract Enforcement System
    outcomes:
      - Developers can set and enforce quality gates
      - Automated blocking of contract violations
    stories:
      - key: STORY-ENFORCEMENT-001
        title: As a developer, I want to set enforcement presets
        story_points: 5
        value_points: 13

  - key: FEATURE-BROWNFIELD
    title: Brownfield Code Analysis
    outcomes:
      - Automatically derive plans from existing codebases
      - Identify features and stories from Python code
    stories:
      - key: STORY-BROWNFIELD-001
        title: As a developer, I want to analyze existing code
        story_points: 8
        value_points: 21
```

**Saved to**: `.specfact/plans/main.bundle.yaml`

---

## Step 4: Compare Plans with Enforcement (5 seconds 🔍)

Now comes the magic - compare the manual plan against what's actually implemented:

```bash
specfact plan compare
```

### Results

**Deviations Found**: 24 total

- 🔴 **HIGH**: 2 (Missing features from manual plan)
- 🟡 **MEDIUM**: 19 (Extra implementations found in code)
- 🔵 **LOW**: 3 (Metadata mismatches)

### Detailed Breakdown

#### 🔴 HIGH Severity (BLOCKED)

```table
┃ 🔴 HIGH   │ Missing Feature     │ Feature 'FEATURE-ENFORCEMENT'      │ features[FEATURE-E… │
┃           │                     │ (Contract Enforcement System)      │                     │
┃           │                     │ in manual plan but not implemented │                     │
```

**Wait, what?** We literally just built the enforcement feature! 🤔

**Explanation**: The brownfield analyzer found `FEATURE-ENFORCEMENTCONFIG` (the model class), but our manual plan calls it `FEATURE-ENFORCEMENT` (the complete system). This is a **real deviation** - our naming doesn't match!

#### ⚠️ MEDIUM Severity (WARNED)

```table
┃ 🟡 MEDIUM │ Extra Implementation │ Feature 'FEATURE-YAMLUTILS'       │ features[FEATURE-Y… │
┃           │                      │ (Y A M L Utils) found in code     │                     │
┃           │                      │ but not in manual plan            │                     │
```

**Explanation**: We have 19 utility features (YAML utils, Git operations, validators, etc.) that exist in code but aren't documented in our minimal manual plan.

**Value**: This is exactly what we want! It shows us **undocumented features** that should either be:

1. Added to the manual plan, or
2. Removed if they're not needed

#### 📝 LOW Severity (LOGGED)

```table
┃ 🔵 LOW    │ Mismatch            │ Idea title differs:               │ idea.title          │
┃           │                     │ manual='SpecFact CLI',            │                     │
┃           │                     │ auto='Unknown  Project'           │                     │
```

**Explanation**: Brownfield analysis couldn't detect our project name, so it used "Unknown Project". Minor metadata issue.

---

## Step 5: Enforcement In Action 🚫

Here's where it gets interesting. With **balanced enforcement** enabled:

### Enforcement Report

```bash
============================================================
Enforcement Rules
============================================================

Using enforcement config: .specfact/gates/config/enforcement.yaml

📝 [LOW] mismatch: LOG
📝 [LOW] mismatch: LOG
📝 [LOW] mismatch: LOG
🚫 [HIGH] missing_feature: BLOCK
🚫 [HIGH] missing_feature: BLOCK
⚠️ [MEDIUM] extra_implementation: WARN
⚠️ [MEDIUM] extra_implementation: WARN
⚠️ [MEDIUM] extra_implementation: WARN
... (16 more MEDIUM warnings)

❌ Enforcement BLOCKED: 2 deviation(s) violate quality gates
Fix the blocking deviations or adjust enforcement config
```

**Exit Code**: 1 (BLOCKED) ❌

**What happened**: The 2 HIGH severity deviations violated our quality gate, so the command **blocked** execution.

**In CI/CD**: This would **fail the PR** and prevent the merge until we fix the deviations or update the enforcement config.

---

## Step 6: Switch to Minimal Enforcement (1 second 🔄)

Let's try again with **minimal enforcement** (never blocks):

```bash
specfact enforce stage --preset minimal
specfact plan compare
```

### New Enforcement Report

```bash
============================================================
Enforcement Rules
============================================================

Using enforcement config: .specfact/gates/config/enforcement.yaml

📝 [LOW] mismatch: LOG
📝 [LOW] mismatch: LOG
📝 [LOW] mismatch: LOG
⚠️ [HIGH] missing_feature: WARN  ← Changed from BLOCK
⚠️ [HIGH] missing_feature: WARN  ← Changed from BLOCK
⚠️ [MEDIUM] extra_implementation: WARN
... (all 24 deviations)

✅ Enforcement PASSED: No blocking deviations
```

**Exit Code**: 0 (PASSED) ✅

**Same deviations, different outcome**: With minimal enforcement, even HIGH severity issues are downgraded to warnings. Perfect for exploration phase!

---

## What We Learned

### 1. **Speed** ⚡

| Task | Time |
|------|------|
| Analyze 19 Python files | 3 seconds |
| Set enforcement | 1 second |
| Compare plans | 5 seconds |
| **Total** | **< 10 seconds** |

### 2. **Accuracy** 🎯

- Discovered **19 features** we actually built
- Generated **49 user stories** with meaningful titles
- Calculated story points using Fibonacci (1, 2, 3, 5, 8...)
- Detected real naming inconsistencies (e.g., `FEATURE-ENFORCEMENT` vs `FEATURE-ENFORCEMENTCONFIG`)

### 3. **Enforcement Works** 🚫

- **Balanced mode**: Blocked execution due to 2 HIGH deviations (exit 1)
- **Minimal mode**: Passed with warnings (exit 0)
- **CI/CD ready**: Exit codes work perfectly with GitHub Actions, GitLab CI, etc.

### 4. **Real Value** 💎

The tool found **real issues**:

1. **Naming inconsistency**: Manual plan uses `FEATURE-ENFORCEMENT`, but code has `FEATURE-ENFORCEMENTCONFIG`
2. **Undocumented features**: 19 utility features exist in code but aren't in the manual plan
3. **Documentation gap**: Should we document all utilities, or are they internal implementation details?

These are **actual questions** that need answers, not false positives!

---

## Complete Workflow (< 10 seconds)

```bash
# 1. Analyze existing codebase (3 seconds)
specfact import from-code --repo . --confidence 0.5
# ✅ Discovers 19 features, 49 stories

# 2. Set quality gates (1 second)
specfact enforce stage --preset balanced
# ✅ BLOCK HIGH, WARN MEDIUM, LOG LOW

# 3. Compare plans (5 seconds)
specfact plan compare
# ✅ Finds 24 deviations
# ❌ BLOCKS execution (2 HIGH violations)

# Total time: < 10 seconds
# Total value: Priceless 💎
```

---

## Use Cases Demonstrated

### ✅ Brownfield Analysis

**Problem**: "We have 10,000 lines of code and no documentation"

**Solution**: Run `import from-code` → get instant plan bundle with features and stories

**Time**: Seconds, not days

### ✅ Quality Gates

**Problem**: "How do I prevent bad code from merging?"

**Solution**: Set enforcement preset → configure CI to run `plan compare`

**Result**: PRs blocked automatically if they violate contracts

### ✅ CI/CD Integration

**Problem**: "I need consistent exit codes for automation"

**Solution**: SpecFact CLI uses standard exit codes:

- 0 = success (no blocking deviations)
- 1 = failure (enforcement blocked)

**Integration**: Works with any CI system (GitHub Actions, GitLab, Jenkins, etc.)

---

## Next Steps

### Try It Yourself

```bash
# Clone SpecFact CLI
git clone https://github.com/nold-ai/specfact-cli.git
cd specfact-cli

# Run the same analysis
hatch run python -c "import sys; sys.path.insert(0, 'src'); from specfact_cli.cli import app; app()" import from-code --repo . --confidence 0.5

# Set enforcement
hatch run python -c "import sys; sys.path.insert(0, 'src'); from specfact_cli.cli import app; app()" enforce stage --preset balanced

# Compare plans
hatch run python -c "import sys; sys.path.insert(0, 'src'); from specfact_cli.cli import app; app()" plan compare
```

### Learn More

- 🔧 [How Code2Spec Works](../technical/code2spec-analysis-logic.md) - Deep dive into AST-based analysis
- 📖 [Getting Started Guide](../getting-started/README.md)
- 📋 [Command Reference](../reference/commands.md)
- 💡 [More Use Cases](../guides/use-cases.md)

---

## Files Generated

All artifacts are stored in `.specfact/`:

```shell
.specfact/
├── plans/
│   └── main.bundle.yaml                 # Manual plan (versioned)
├── reports/
│   ├── brownfield/
│   │   ├── auto-derived.2025-10-30T16-57-51.bundle.yaml  # Auto-derived plan
│   │   └── report-2025-10-30-16-57.md                    # Analysis report
│   └── comparison/
│       └── report-2025-10-30-16-58.md                    # Deviation report
└── gates/
    └── config/
        └── enforcement.yaml              # Enforcement config (versioned)
```

**Versioned** (commit to git): `plans/`, `gates/config/`

**Gitignored** (ephemeral): `reports/`

---

## Conclusion

SpecFact CLI **works**. We proved it by running it on itself and finding real issues in **under 10 seconds**.

**Key Takeaways**:

1. ⚡ **Fast**: Analyze thousands of lines in seconds
2. 🎯 **Accurate**: Finds real deviations, not false positives
3. 🚫 **Blocks bad code**: Enforcement actually prevents merges
4. 🔄 **CI/CD ready**: Standard exit codes, works everywhere

**Try it yourself** and see how much time you save!

---

> **Built by dogfooding** - This example is real, not fabricated. We ran SpecFact CLI on itself and documented the actual results.
