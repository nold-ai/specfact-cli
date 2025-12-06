# Real-World Example: SpecFact CLI Analyzing Itself

> **TL;DR**: We ran SpecFact CLI on its own codebase in two ways: (1) **Brownfield analysis** discovered **19 features** and **49 stories** in **under 3 seconds**, found **24 deviations**, and blocked the merge (as configured). (2) **Contract enhancement** added beartype, icontract, and CrossHair contracts to our core telemetry module with **7-step validation** (all tests passed, code quality maintained). Total time: **< 10 seconds** for analysis, **~3 minutes** for contract enhancement. 🚀
> **Note**: "Dogfooding" is a well-known tech term meaning "eating your own dog food" - using your own product. It's a common practice in software development to validate that tools work in real-world scenarios.

**CLI-First Approach**: SpecFact works offline, requires no account, and integrates with your existing workflow. Works with VS Code, Cursor, GitHub Actions, pre-commit hooks, or any IDE. No platform to learn, no vendor lock-in.

---

## The Challenge

We built SpecFact CLI and wanted to validate that it actually works in the real world. So we did what every good developer does: **we dogfooded it**.

**Goal**: Analyze the SpecFact CLI codebase itself and demonstrate:

1. How fast brownfield analysis is
2. How enforcement actually blocks bad code
3. How the complete workflow works end-to-end
4. How contract enhancement works on real production code

---

## Step 1: Brownfield Analysis (3 seconds ⚡)

First, we analyzed the existing codebase to see what features it discovered:

```bash
specfact import from-code specfact-cli --repo . --confidence 0.5
```

**Output**:

```bash
🔍 Analyzing Python files...
✓ Found 19 features
✓ Detected themes: CLI, Validation
✓ Total stories: 49

✓ Analysis complete!
Project bundle written to: .specfact/projects/specfact-cli/
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

**Saved to**: `.specfact/projects/main/` (modular project bundle structure)

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

## Part 2: Contract Enhancement Workflow (Production Use Case) 🎯

After validating the brownfield analysis workflow, we took it a step further: **we used SpecFact CLI to enhance one of our own core modules with contracts**. This demonstrates the complete contract enhancement workflow in a real production scenario.

**Goal**: Add beartype, icontract, and CrossHair contracts to `src/specfact_cli/telemetry.py` - a core module that handles privacy-first telemetry.

---

## Step 7: Generate Contract Enhancement Prompt (1 second 📝)

First, we generated a structured prompt for our AI IDE (Cursor) to enhance the telemetry module:

```bash
specfact generate contracts-prompt src/specfact_cli/telemetry.py --bundle specfact-cli-test --apply all-contracts --no-interactive
```

**Output**:

```bash
✓ Analyzing file: src/specfact_cli/telemetry.py
✓ Generating prompt for: beartype, icontract, crosshair
✓ Prompt saved to: .specfact/projects/specfact-cli-test/prompts/enhance-telemetry-beartype-icontract-crosshair.md
```

**What happened**:

- CLI analyzed the telemetry module (543 lines)
- Generated a structured prompt with:
  - **CRITICAL REQUIREMENT**: Add contracts to ALL eligible functions (no asking the user)
  - Detailed instructions for each contract type (beartype, icontract, crosshair)
  - Code quality guidance (follow project formatting rules)
  - Step-by-step validation workflow
- Saved prompt to bundle-specific directory (prevents conflicts with multiple bundles)

---

## Step 8: AI IDE Enhancement (2-3 minutes 🤖)

We copied the prompt to Cursor (our AI IDE), which:

1. **Read the file** from the provided path
2. **Added contracts to ALL eligible functions**:
   - `@beartype` decorators on all functions/methods
   - `@require` and `@ensure` decorators where appropriate
   - CrossHair property-based test functions
3. **Wrote enhanced code** to `enhanced_telemetry.py` (temporary file)
4. **Ran validation** using SpecFact CLI (see Step 9)

**Key Point**: The AI IDE followed the prompt's **CRITICAL REQUIREMENT** and added contracts to all eligible functions automatically, without asking for confirmation.

---

## Step 9: Comprehensive Validation (7-step process ✅)

The AI IDE ran SpecFact CLI validation on the enhanced code:

```bash
specfact generate contracts-apply enhanced_telemetry.py --original src/specfact_cli/telemetry.py
```

### Validation Results

**Step 1/7: File Size Check** ✅

- Enhanced file: 678 lines (was 543 lines)
- Validation: Passed (enhanced file is larger, indicating contracts were added)

**Step 2/7: Syntax Validation** ✅

- Python syntax check: Passed
- File compiles successfully

**Step 3/7: AST Structure Comparison** ✅

- Original: 23 definitions (functions, classes, methods)
- Enhanced: 23 definitions preserved
- Validation: All definitions maintained (no functions removed)

**Step 4/7: Contract Imports Verification** ✅

- Required imports present:
  - `from beartype import beartype`
  - `from icontract import require, ensure`
- Validation: All imports verified

**Step 5/7: Code Quality Checks** ✅

- **Ruff linting**: Passed (1 tool checked, 1 passed)
- **Pylint**: Not available (skipped)
- **BasedPyright**: Not available (skipped)
- **MyPy**: Not available (skipped)
- Note: Tools run automatically if installed (non-blocking)

**Step 6/7: Test Execution** ✅

- **Scoped test run**: `pytest tests/unit/specfact_cli/test_telemetry.py`
- **Results**: 10/10 tests passed
- **Time**: Seconds (optimized scoped run, not full repository validation)
- Note: Tests always run for validation, even in `--dry-run` mode

**Step 7/7: Diff Preview** ✅

- Previewed changes before applying
- All validations passed

### Final Result

```bash
✓ All validations passed!
✓ Enhanced code applied to: src/specfact_cli/telemetry.py
✓ Temporary file cleaned up: enhanced_telemetry.py
```

**Total validation time**: < 10 seconds (7-step comprehensive validation)

---

## What We Achieved

### Contracts Applied

1. **beartype decorators**: Added `@beartype` to all eligible functions and methods
   - Regular functions, class methods, static methods, async functions
   - Runtime type checking for all public APIs

2. **icontract decorators**: Added `@require` and `@ensure` where appropriate
   - Preconditions for parameter validation and state checks
   - Postconditions for return value validation and guarantees

3. **CrossHair tests**: Added property-based test functions
   - `test_coerce_bool_property()` - Validates boolean coercion
   - `test_parse_headers_property()` - Validates header parsing
   - `test_telemetry_settings_from_env_property()` - Validates settings creation
   - `test_telemetry_manager_sanitize_property()` - Validates data sanitization
   - `test_telemetry_manager_normalize_value_property()` - Validates value normalization

### Validation Quality

- ✅ **File size check**: Ensured no code was removed
- ✅ **Syntax validation**: Python compilation successful
- ✅ **AST structure**: All 23 definitions preserved
- ✅ **Contract imports**: All required imports verified
- ✅ **Code quality**: Ruff linting passed
- ✅ **Tests**: 10/10 tests passed
- ✅ **Diff preview**: Changes reviewed before applying

### Production Value

This demonstrates **real production use**:

- Enhanced a **core module** (telemetry) used throughout the CLI
- Applied **all three contract types** (beartype, icontract, crosshair)
- **All tests passed** (10/10) - no regressions introduced
- **Code quality maintained** (ruff linting passed)
- **Fast validation** (< 10 seconds for comprehensive 7-step process)

---

## Complete Contract Enhancement Workflow

```bash
# 1. Generate prompt (1 second)
specfact generate contracts-prompt src/specfact_cli/telemetry.py \
  --bundle specfact-cli-test \
  --apply all-contracts \
  --no-interactive
# ✅ Prompt saved to: .specfact/projects/specfact-cli-test/prompts/

# 2. AI IDE enhancement (2-3 minutes)
# - Copy prompt to Cursor/CoPilot/etc.
# - AI IDE reads file and adds contracts
# - AI IDE writes to enhanced_telemetry.py

# 3. Validate and apply (10 seconds)
specfact generate contracts-apply enhanced_telemetry.py \
  --original src/specfact_cli/telemetry.py
# ✅ 7-step validation passed
# ✅ All tests passed (10/10)
# ✅ Code quality checks passed
# ✅ Changes applied to original file

# Total time: ~3 minutes (mostly AI IDE processing)
# Total value: Production-ready contract-enhanced code
```

---

## What We Learned (Part 2)

### 1. **Comprehensive Validation** 🛡️

The 7-step validation process caught potential issues:

- File size check prevents accidental code removal
- AST structure comparison ensures no functions are deleted
- Contract imports verification prevents missing dependencies
- Code quality checks (if tools available) catch linting issues
- Test execution validates functionality (10/10 passed)

### 2. **Production-Ready Workflow** 🚀

- **Fast**: Validation completes in < 10 seconds
- **Thorough**: 7-step comprehensive validation
- **Safe**: Only applies changes if all validations pass
- **Flexible**: Works with any AI IDE (Cursor, CoPilot, etc.)
- **Non-blocking**: Code quality tools optional (run if available)

### 3. **Real-World Validation** 💎

We enhanced a **real production module**:

- Core telemetry module (used throughout CLI)
- 543 lines → 678 lines (contracts added)
- All tests passing (10/10)
- Code quality maintained (ruff passed)
- No regressions introduced

### 4. **Self-Improvement** 🔄

This demonstrates **true dogfooding**:

- We used SpecFact CLI to enhance SpecFact CLI
- Validated the workflow on real production code
- Proved the tool works for its intended purpose
- Enhanced our own codebase with contracts

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
specfact import from-code specfact-cli --repo . --confidence 0.5
# ✅ Discovers 19 features, 49 stories

# 2. Set quality gates (1 second)
specfact enforce stage --preset balanced
# ✅ BLOCK HIGH, WARN MEDIUM, LOG LOW

# 3. Compare plans (5 seconds) - uses active plan or default bundle
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
hatch run python -c "import sys; sys.path.insert(0, 'src'); from specfact_cli.cli import app; app()" import from-code specfact-cli --repo . --confidence 0.5

# Set enforcement
hatch run python -c "import sys; sys.path.insert(0, 'src'); from specfact_cli.cli import app; app()" enforce stage --preset balanced

# Compare plans
hatch run python -c "import sys; sys.path.insert(0, 'src'); from specfact_cli.cli import app; app()" plan compare
```

### Learn More

- ⭐ **[Integration Showcases](integration-showcases/)** - Real bugs fixed via VS Code, Cursor, GitHub Actions integrations
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

SpecFact CLI **works**. We proved it by running it on itself in two real-world scenarios:

### Part 1: Brownfield Analysis

- ⚡ **Fast**: Analyzed 19 files → 19 features, 49 stories in **3 seconds**
- 🎯 **Accurate**: Found **24 real deviations** (naming inconsistencies, undocumented features)
- 🚫 **Blocks bad code**: Enforcement prevented merge with 2 HIGH violations
- 🔄 **CI/CD ready**: Standard exit codes, works everywhere

### Part 2: Contract Enhancement

- 🛡️ **Comprehensive**: 7-step validation process (file size, syntax, AST, imports, quality, tests, diff)
- ✅ **Production-ready**: Enhanced core telemetry module (543 → 678 lines)
- 🧪 **All tests passed**: 10/10 tests passed, no regressions
- 🚀 **Fast validation**: < 10 seconds for complete validation workflow

**Key Takeaways**:

1. ⚡ **Fast**: Analyze thousands of lines in seconds, validate contracts in < 10 seconds
2. 🎯 **Accurate**: Finds real deviations, not false positives
3. 🚫 **Blocks bad code**: Enforcement actually prevents merges
4. 🛡️ **Comprehensive validation**: 7-step process ensures code quality
5. 🔄 **CI/CD ready**: Standard exit codes, works everywhere
6. 🐕 **True dogfooding**: We use it on our own production code

**Try it yourself** and see how much time you save!

---

> **Built by dogfooding** - This example is real, not fabricated. We ran SpecFact CLI on itself in two ways: (1) brownfield analysis workflow, and (2) contract enhancement workflow on our core telemetry module. All results are actual, documented outcomes from production use.
