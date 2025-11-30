# Getting Started with SpecFact CLI

This guide will help you get started with SpecFact CLI in under 60 seconds.

> **Primary Use Case**: SpecFact CLI is designed for **brownfield code modernization** - reverse-engineering existing codebases into documented specs with runtime contract enforcement. See [First Steps](first-steps.md) for brownfield workflows.

## Installation

### Option 1: uvx (CLI-only Mode)

No installation required - run directly:

```bash
uvx specfact-cli@latest --help
```

**Best for**: Quick testing, CI/CD, one-off commands

**Limitations**: CLI-only mode uses AST-based analysis which may show 0 features for simple test cases. For better results, use interactive AI Assistant mode (Option 2).

### Option 2: pip (Interactive AI Assistant Mode)

**Required for**: IDE integration, slash commands, enhanced feature detection

```bash
# System-wide
pip install specfact-cli

# User install
pip install --user specfact-cli

# Virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install specfact-cli
```

**Optional**: For enhanced graph-based dependency analysis, see [Enhanced Analysis Dependencies](../installation/enhanced-analysis-dependencies.md).

**After installation**: Set up IDE integration for interactive mode:

```bash
# Navigate to your project
cd /path/to/your/project

# Initialize IDE integration (one-time per project)
specfact init

# Or specify IDE explicitly
specfact init --ide cursor
specfact init --ide vscode
```

**Note**: Interactive mode requires Python 3.11+ and automatically uses your IDE workspace (no `--repo .` needed in slash commands).

### Option 3: Container

```bash
# Docker
docker run --rm -v $(pwd):/workspace ghcr.io/nold-ai/specfact-cli:latest --help

# Podman
podman run --rm -v $(pwd):/workspace ghcr.io/nold-ai/specfact-cli:latest --help
```

### Option 4: GitHub Action

Create `.github/workflows/specfact.yml`:

```yaml
name: SpecFact CLI Validation

on:
  pull_request:
    branches: [main, dev]
  push:
    branches: [main, dev]
  workflow_dispatch:
    inputs:
      budget:
        description: "Time budget in seconds"
        required: false
        default: "90"
        type: string
      mode:
        description: "Enforcement mode (block, warn, log)"
        required: false
        default: "block"
        type: choice
        options:
          - block
          - warn
          - log

jobs:
  specfact-validation:
    name: Contract Validation
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      checks: write
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install SpecFact CLI
        run: pip install specfact-cli

      - name: Run Contract Validation
        run: specfact repro --verbose --budget 90

      - name: Generate PR Comment
        if: github.event_name == 'pull_request'
        run: python -m specfact_cli.utils.github_annotations
        env:
          SPECFACT_REPORT_PATH: .specfact/reports/enforcement/report-*.yaml
```

## First Steps

### Operational Modes

SpecFact CLI supports two operational modes:

- **CLI-only Mode** (uvx): Fast, AST-based analysis for automation
  - Works immediately with `uvx specfact-cli@latest`
  - No installation required
  - May show 0 features for simple test cases (AST limitations)
  - Best for: CI/CD, quick testing, one-off commands

- **Interactive AI Assistant Mode** (pip + specfact init): Enhanced semantic understanding
  - Requires `pip install specfact-cli` and `specfact init`
  - Better feature detection and semantic understanding
  - IDE integration with slash commands
  - Automatically uses IDE workspace (no `--repo .` needed)
  - Best for: Development, legacy code analysis, complex projects

**Mode Selection**:

```bash
# CLI-only mode (uvx - no installation)
uvx specfact-cli@latest import from-code my-project --repo .

# Interactive mode (pip + specfact init - recommended)
# After: pip install specfact-cli && specfact init
# Then use slash commands in IDE: /specfact.01-import legacy-api --repo .
```

**Note**: Mode is auto-detected based on whether `specfact` command is available and IDE integration is set up.

### For Greenfield Projects

Start a new contract-driven project:

```bash
specfact plan init --interactive
```

This will guide you through creating:

- Initial project idea and narrative
- Product themes and releases
- First features and stories
- Protocol state machine

**With IDE Integration (Interactive AI Assistant Mode):**

```bash
# Step 1: Install SpecFact CLI
pip install specfact-cli

# Step 2: Navigate to your project
cd /path/to/your/project

# Step 3: Initialize IDE integration (one-time per project)
specfact init
# Or specify IDE: specfact init --ide cursor

# Step 4: Use slash command in IDE chat
/specfact.02-plan init legacy-api
# Or use other plan operations: /specfact.02-plan add-feature --bundle legacy-api --key FEATURE-001 --title "User Auth"
```

**Important**:

- Interactive mode automatically uses your IDE workspace
- Slash commands use numbered format: `/specfact.01-import`, `/specfact.02-plan`, etc.
- Commands are numbered for natural workflow progression (01-import → 02-plan → 03-review → 04-sdd → 05-enforce → 06-sync)
- No `--repo .` parameter needed in interactive mode (uses workspace automatically)
- The AI assistant will prompt you for bundle names and other inputs if not provided

See [IDE Integration Guide](../guides/ide-integration.md) for detailed setup instructions.

### For Spec-Kit Migration

Convert an existing GitHub Spec-Kit project:

```bash
# Preview what will be migrated
specfact import from-bridge --adapter speckit --repo ./my-speckit-project --dry-run

# Execute migration (one-time import)
specfact import from-bridge \
  --adapter speckit \
  --repo ./my-speckit-project \
  --write

# Ongoing bidirectional sync (after migration)
specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional --watch
```

**Bidirectional Sync:**

Keep Spec-Kit and SpecFact artifacts synchronized:

```bash
# One-time sync
specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional

# Continuous watch mode
specfact sync bridge --adapter speckit --bundle <bundle-name> --repo . --bidirectional --watch
```

### For Brownfield Projects

Analyze existing code to generate specifications:

```bash
# Analyze repository (CI/CD mode - fast)
specfact import from-code my-project \
  --repo ./my-project \
  --shadow-only \
  --report analysis.md

# Analyze with CoPilot mode (enhanced prompts)
specfact --mode copilot import from-code my-project \
  --repo ./my-project \
  --confidence 0.7 \
  --report analysis.md

# Review generated plan
cat analysis.md
```

**With IDE Integration (Interactive AI Assistant Mode):**

```bash
# Step 1: Install SpecFact CLI
pip install specfact-cli

# Step 2: Navigate to your project
cd /path/to/your/project

# Step 3: Initialize IDE integration (one-time per project)
specfact init
# Or specify IDE: specfact init --ide cursor

# Step 4: Use slash command in IDE chat
/specfact.01-import legacy-api --repo .
# Or let the AI assistant prompt you for bundle name and other options
```

**Important**:

- Interactive mode automatically uses your IDE workspace (no `--repo .` needed in interactive mode)
- Slash commands use numbered format: `/specfact.01-import`, `/specfact.02-plan`, etc. (numbered for workflow ordering)
- Commands follow natural progression: 01-import → 02-plan → 03-review → 04-sdd → 05-enforce → 06-sync
- The AI assistant will prompt you for bundle names and confidence thresholds if not provided
- Better feature detection than CLI-only mode (semantic understanding vs AST-only)

See [IDE Integration Guide](../guides/ide-integration.md) for detailed setup instructions.

**Sync Changes:**

Keep plan artifacts updated as code changes:

```bash
# One-time sync
specfact sync repository --repo . --target .specfact

# Continuous watch mode
specfact sync repository --repo . --watch
```

## Next Steps

1. **Explore Commands**: See [Command Reference](../reference/commands.md)
2. **Learn Use Cases**: Read [Use Cases](../guides/use-cases.md)
3. **Understand Architecture**: Check [Architecture](../reference/architecture.md)
4. **Set Up IDE Integration**: See [IDE Integration Guide](../guides/ide-integration.md)

## Quick Tips

- **Python 3.11+ required**: SpecFact CLI requires Python 3.11 or higher
- **Start in shadow mode**: Use `--shadow-only` to observe without blocking
- **Use dry-run**: Always preview with `--dry-run` before writing changes
- **Check reports**: Generate reports with `--report <filename>` for review
- **Progressive enforcement**: Start with `minimal`, move to `balanced`, then `strict`
- **CLI-only vs Interactive**: Use `uvx` for quick testing, `pip install + specfact init` for better results
- **IDE integration**: Use `specfact init` to set up slash commands in IDE (requires pip install)
- **Slash commands**: Use numbered format `/specfact.01-import`, `/specfact.02-plan`, etc. (numbered for workflow ordering)
- **Global flags**: Place `--no-banner` before the command: `specfact --no-banner <command>`
- **Bidirectional sync**: Use `sync bridge --adapter <adapter>` or `sync repository` for ongoing change management
- **Semgrep (optional)**: Install `pip install semgrep` for async pattern detection in `specfact repro`

## Common Commands

```bash
# Check version
specfact --version

# Get help
specfact --help
specfact <command> --help

# Initialize plan (bundle name as positional argument)
specfact plan init my-project --interactive

# Add feature
specfact plan add-feature --key FEATURE-001 --title "My Feature"

# Validate everything
specfact repro

# Set enforcement level
specfact enforce stage --preset balanced
```

## Getting Help

- **Documentation**: [docs/](.)
- **Issues**: [GitHub Issues](https://github.com/nold-ai/specfact-cli/issues)
- **Discussions**: [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions)
- **Email**: [hello@noldai.com](mailto:hello@noldai.com)

## Development Setup

For contributors:

```bash
# Clone repository
git clone https://github.com/nold-ai/specfact-cli.git
cd specfact-cli

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
hatch run contract-test-full

# Format code
hatch run format

# Run linters
hatch run lint
```

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for detailed contribution guidelines.
