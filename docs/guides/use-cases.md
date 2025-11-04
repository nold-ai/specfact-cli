# Use Cases

Detailed use cases and examples for SpecFact CLI.

## Use Case 1: GitHub Spec-Kit Migration

**Problem**: You have a Spec-Kit project but need team collaboration, production deployment, and quality assurance.

**Solution**: Migrate to SpecFact CLI for contract-driven development.

### Steps

#### 1. Preview Migration

```bash
specfact import from-spec-kit --repo ./spec-kit-project --dry-run
```

**Expected Output:**

```bash
🔍 Analyzing Spec-Kit project...
✅ Found .specify/ directory (modern format)
✅ Found specs/001-user-authentication/spec.md
✅ Found specs/001-user-authentication/plan.md
✅ Found specs/001-user-authentication/tasks.md
✅ Found .specify/memory/constitution.md

📊 Migration Preview:
  - Will create: .specfact/plans/main.bundle.yaml
  - Will create: .specfact/protocols/workflow.protocol.yaml (if FSM detected)
  - Will create: .specfact/enforcement/config.yaml
  - Will convert: Spec-Kit features → SpecFact Feature models
  - Will convert: Spec-Kit user stories → SpecFact Story models
  
🚀 Ready to migrate (use --write to execute)
```

#### 2. Execute Migration

```bash
specfact import from-spec-kit \
  --repo ./spec-kit-project \
  --write \
  --out-branch feat/specfact-migration \
  --report migration-report.md
```

#### 3. Review Generated Contracts

```bash
git checkout feat/specfact-migration
git diff main
```

Review:

- `.specfact/plans/main.bundle.yaml` - Plan bundle (converted from Spec-Kit artifacts)
- `.specfact/protocols/workflow.protocol.yaml` - FSM definition (if protocol detected)
- `.specfact/enforcement/config.yaml` - Quality gates configuration
- `.semgrep/async-anti-patterns.yaml` - Anti-pattern rules (if async patterns detected)
- `.github/workflows/specfact-gate.yml` - CI workflow (optional)

#### 4. Enable Bidirectional Sync (Optional)

Keep Spec-Kit and SpecFact synchronized:

```bash
# One-time bidirectional sync
specfact sync spec-kit --repo . --bidirectional

# Continuous watch mode
specfact sync spec-kit --repo . --bidirectional --watch --interval 5
```

**What it syncs:**

- `specs/[###-feature-name]/spec.md`, `plan.md`, `tasks.md` ↔ `.specfact/plans/*.yaml`
- `.specify/memory/constitution.md` ↔ SpecFact business context
- `specs/[###-feature-name]/research.md`, `data-model.md`, `quickstart.md` ↔ SpecFact supporting artifacts
- `specs/[###-feature-name]/contracts/*.yaml` ↔ SpecFact protocol definitions
- Automatic conflict resolution with priority rules

#### 5. Enable Enforcement

```bash
# Start in shadow mode (observe only)
specfact enforce stage --preset minimal

# After stabilization, enable warnings
specfact enforce stage --preset balanced

# For production, enable strict mode
specfact enforce stage --preset strict
```

#### 6. Validate

```bash
specfact repro --verbose
```

### Expected Timeline

- **Preview**: < 1 minute
- **Migration**: 2-5 minutes
- **Review**: 15-30 minutes
- **Stabilization**: 1-2 weeks (shadow mode)
- **Production**: After validation passes

---

## Use Case 2: Brownfield Code Hardening

**Problem**: Existing codebase with no specs, need to add quality gates incrementally. Spec-Kit focuses on new feature authoring, while this use case requires analyzing existing code.

**Solution**: Analyze code to generate specifications, then progressively enforce.

### Steps (Use Case 2)

#### 1. Analyze Code

```bash
# CI/CD mode (fast, deterministic)
specfact import from-code \
  --repo . \
  --shadow-only \
  --confidence 0.7 \
  --report analysis.md

# CoPilot mode (enhanced prompts, interactive)
specfact --mode copilot import from-code \
  --repo . \
  --confidence 0.7 \
  --report analysis.md
```

**With IDE Integration:**

```bash
# First, initialize IDE integration
specfact init --ide cursor

# Then use slash command in IDE chat
/specfact-import-from-code --repo . --confidence 0.7
```

See [IDE Integration Guide](ide-integration.md) for setup instructions.

**What it analyzes (AI-First / CoPilot Mode):**

- Semantic understanding of codebase (LLM)
- Multi-language support (Python, TypeScript, JavaScript, PowerShell, etc.)
- Actual priorities, constraints, unknowns from code context
- Meaningful scenarios from acceptance criteria
- High-quality Spec-Kit compatible artifacts

**What it analyzes (AST-Based / CI/CD Mode):**

- Module dependency graph (Python-only)
- Commit history for feature boundaries
- Test files for acceptance criteria
- Type hints for API surfaces
- Async patterns for anti-patterns

**CoPilot Enhancement:**

- Context injection (current file, selection, workspace)
- Enhanced prompts for semantic understanding
- Interactive assistance for complex codebases
- Multi-language analysis support

#### 2. Review Auto-Generated Plan

```bash
cat analysis.md
```

**Expected sections:**

- **Features Detected** - With confidence scores
- **Stories Inferred** - From commit messages
- **API Surface** - Public functions/classes
- **Async Patterns** - Detected issues
- **State Machine** - Inferred from code flow

#### 3. Sync Repository Changes (Optional)

Keep plan artifacts updated as code changes:

```bash
# One-time sync
specfact sync repository --repo . --target .specfact

# Continuous watch mode
specfact sync repository --repo . --watch --interval 5
```

**What it tracks:**

- Code changes → Plan artifact updates
- Deviations from manual plans
- Feature/story extraction from code

#### 4. Compare with Manual Plan (if exists)

```bash
specfact plan compare \
  --manual .specfact/plans/main.bundle.yaml \
  --auto .specfact/plans/my-project-*.bundle.yaml \
  --format markdown \
  --out .specfact/reports/comparison/deviation-report.md
```

**With CoPilot:**

```bash
# Use slash command in IDE chat (after specfact init)
/specfact-plan-compare --manual main.bundle.yaml --auto auto.bundle.yaml
```

**CoPilot Enhancement:**

- Deviation explanations
- Fix suggestions
- Interactive deviation review

**Output:**

```markdown
# Deviation Report

## Missing Features (in manual but not in auto)

- FEATURE-003: User notifications
  - Confidence: N/A (not detected in code)
  - Recommendation: Implement or remove from manual plan

## Extra Features (in auto but not in manual)

- FEATURE-AUTO-001: Database migrations
  - Confidence: 0.85
  - Recommendation: Add to manual plan

## Mismatched Stories

- STORY-001: User login
  - Manual acceptance: "OAuth 2.0 support"
  - Auto acceptance: "Basic auth only"
  - Severity: HIGH
  - Recommendation: Update implementation or manual plan
```

#### 5. Fix High-Severity Deviations

Focus on:

- **Async anti-patterns** - Blocking I/O in async functions
- **Missing contracts** - APIs without validation
- **State machine gaps** - Unreachable states
- **Test coverage** - Missing acceptance tests

#### 6. Progressive Enforcement

```bash
# Week 1-2: Shadow mode (observe)
specfact enforce stage --preset minimal

# Week 3-4: Balanced mode (warn on medium, block high)
specfact enforce stage --preset balanced

# Week 5+: Strict mode (block medium+)
specfact enforce stage --preset strict
```

### Expected Timeline (Use Case 2)

- **Analysis**: 2-5 minutes
- **Review**: 1-2 hours
- **High-severity fixes**: 1-3 days
- **Shadow mode**: 1-2 weeks
- **Production enforcement**: After validation stabilizes

---

## Use Case 3: Greenfield Spec-First Development

**Problem**: Starting a new project, want contract-driven development from day 1.

**Solution**: Use SpecFact CLI for spec-first planning and strict enforcement.

### Steps (Use Case 3)

#### 1. Create Plan Interactively

```bash
# Standard interactive mode
specfact plan init --interactive

# CoPilot mode (enhanced prompts)
specfact --mode copilot plan init --interactive
```

**With CoPilot (IDE Integration):**

```bash
# Use slash command in IDE chat (after specfact init)
/specfact-plan-init --idea idea.yaml
```

**Interactive prompts:**

```bash
🎯 SpecFact CLI - Plan Initialization

What's your idea title?
> Real-time collaboration platform

What's the narrative? (high-level vision)
> Enable teams to collaborate in real-time with contract-driven quality

What are the product themes? (comma-separated)
> Developer Experience, Real-time Sync, Quality Assurance

What's the first release name?
> v0.1

What are the release objectives? (comma-separated)
> WebSocket server, Client SDK, Basic presence

✅ Plan initialized: .specfact/plans/main.bundle.yaml
```

#### 2. Add Features and Stories

```bash
# Add feature
specfact plan add-feature \
  --key FEATURE-001 \
  --title "WebSocket Server" \
  --outcomes "Handle 1000 concurrent connections" \
  --outcomes "< 100ms message latency" \
  --acceptance "Given client connection, When message sent, Then delivered within 100ms"

# Add story
specfact plan add-story \
  --feature FEATURE-001 \
  --key STORY-001 \
  --title "Connection handling" \
  --acceptance "Accept WebSocket connections" \
  --acceptance "Maintain heartbeat every 30s" \
  --acceptance "Graceful disconnect cleanup"
```

#### 3. Define Protocol

Create `contracts/protocols/workflow.protocol.yaml`:

```yaml
states:
  - DISCONNECTED
  - CONNECTING
  - CONNECTED
  - RECONNECTING
  - DISCONNECTING

start: DISCONNECTED

transitions:
  - from_state: DISCONNECTED
    on_event: connect
    to_state: CONNECTING

  - from_state: CONNECTING
    on_event: connection_established
    to_state: CONNECTED
    guard: handshake_valid

  - from_state: CONNECTED
    on_event: connection_lost
    to_state: RECONNECTING
    guard: should_reconnect

  - from_state: RECONNECTING
    on_event: reconnect_success
    to_state: CONNECTED

  - from_state: CONNECTED
    on_event: disconnect
    to_state: DISCONNECTING
```

#### 4. Enable Strict Enforcement

```bash
specfact enforce stage --preset strict
```

#### 5. Validate Continuously

```bash
# During development
specfact repro

# In CI/CD
specfact repro --budget 120 --verbose
```

### Expected Timeline Use Case 3

- **Planning**: 1-2 hours
- **Protocol design**: 30 minutes
- **Implementation**: Per feature/story
- **Validation**: Continuous (< 90s per check)

---

## Use Case 4: CI/CD Integration

**Problem**: Need automated quality gates in pull requests.

**Solution**: Add SpecFact GitHub Action to PR workflow.

### Steps Use Case 4

#### 1. Add GitHub Action

Create `.github/workflows/specfact-gate.yml`:

```yaml
name: SpecFact Quality Gate
on:
  pull_request:
    branches: [main, dev]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      
      - name: Install SpecFact
        run: pip install specfact-cli
      
      - name: Run SpecFact
        run: specfact repro --budget 120 --verbose
      
      - name: Upload report
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: specfact-report
          path: .specfact/report.md
```

#### 2. Configure Enforcement

Create `.specfact.yaml`:

```yaml
version: "1.0"

enforcement:
  preset: balanced  # Block HIGH, warn MEDIUM

repro:
  budget: 120
  parallel: true
  fail_fast: false

analysis:
  confidence_threshold: 0.7
  exclude_patterns:
    - "**/__pycache__/**"
    - "**/node_modules/**"
```

#### 3. Test Locally

```bash
# Before pushing
specfact repro

# If issues found
specfact enforce stage --preset minimal  # Temporarily allow
# Fix issues
specfact enforce stage --preset balanced  # Re-enable
```

#### 4. Monitor PR Checks

The GitHub Action will:

- Run contract validation
- Check for async anti-patterns
- Validate state machine transitions
- Generate deviation reports
- Block PR if HIGH severity issues found

### Expected Results

- **Clean PRs**: Pass in < 90s
- **Blocked PRs**: Clear deviation report
- **False positives**: < 5% (use override mechanism)

---

## Use Case 5: Multi-Repository Consistency

**Problem**: Multiple microservices need consistent contract enforcement.

**Solution**: Share common plan bundle and enforcement config.

### Steps Use Case 5

#### 1. Create Shared Plan Bundle

In a shared repository:

```bash
# Create shared plan
specfact plan init --interactive

# Add common features
specfact plan add-feature \
  --key FEATURE-COMMON-001 \
  --title "API Standards" \
  --outcomes "Consistent REST patterns" \
  --outcomes "Standardized error responses"
```

#### 2. Distribute to Services

```bash
# In each microservice
git submodule add https://github.com/org/shared-contracts contracts/shared

# Or copy files
cp ../shared-contracts/plan.bundle.yaml contracts/shared/
```

#### 3. Validate Against Shared Plan

```bash
# In each service
specfact plan compare \
  --manual contracts/shared/plan.bundle.yaml \
  --auto contracts/service/plan.bundle.yaml \
  --format markdown
```

#### 4. Enforce Consistency

```bash
# Add to CI
specfact repro
specfact plan compare --manual contracts/shared/plan.bundle.yaml --auto .
```

### Expected Benefits

- **Consistency**: All services follow same patterns
- **Reusability**: Shared contracts and protocols
- **Maintainability**: Update once, apply everywhere

---

See [Commands](../reference/commands.md) for detailed command reference and [Getting Started](../getting-started/README.md) for quick setup.
