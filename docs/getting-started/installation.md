# Getting Started with SpecFact CLI

This guide will help you get started with SpecFact CLI in under 60 seconds.

## Installation

### Option 1: uvx (Recommended)

No installation required - run directly:

```bash
uvx --from specfact-cli specfact --help
```

### Option 2: pip

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

### Option 3: Container

```bash
# Docker
docker run --rm -v $(pwd):/workspace ghcr.io/nold-ai/specfact-cli:latest --help

# Podman
podman run --rm -v $(pwd):/workspace ghcr.io/nold-ai/specfact-cli:latest --help
```

### Option 4: GitHub Action

```yaml
# .github/workflows/specfact-gate.yml
name: SpecFact Quality Gate
on: [pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run SpecFact
        uses: nold-ai/specfact-action@v1
        with:
          preset: balanced
```

## First Steps

### Operational Modes

SpecFact CLI supports two modes:

- **CI/CD Mode (Default)**: Fast, deterministic execution for automation
- **CoPilot Mode**: Interactive assistance with enhanced prompts for IDEs

Mode is auto-detected, or use `--mode` to override:

```bash
# Auto-detect (default)
specfact plan init --interactive

# Force CI/CD mode
specfact --mode cicd plan init --interactive

# Force CoPilot mode (if available)
specfact --mode copilot plan init --interactive
```

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

**With IDE Integration:**

```bash
# Initialize IDE integration
specfact init --ide cursor

# Use slash command in IDE chat
/specfact-plan-init --idea idea.yaml
```

See [IDE Integration Guide](../guides/ide-integration.md) for setup instructions.

### For Spec-Kit Migration

Convert an existing GitHub Spec-Kit project:

```bash
# Preview what will be migrated
specfact import from-spec-kit --repo ./my-speckit-project --dry-run

# Execute migration (one-time import)
specfact import from-spec-kit \
  --repo ./my-speckit-project \
  --write \
  --out-branch feat/specfact-migration

# Ongoing bidirectional sync (after migration)
specfact sync spec-kit --repo . --bidirectional --watch
```

**Bidirectional Sync:**

Keep Spec-Kit and SpecFact artifacts synchronized:

```bash
# One-time sync
specfact sync spec-kit --repo . --bidirectional

# Continuous watch mode
specfact sync spec-kit --repo . --bidirectional --watch
```

### For Brownfield Projects

Analyze existing code to generate specifications:

```bash
# Analyze repository (CI/CD mode - fast)
specfact import from-code \
  --repo ./my-project \
  --shadow-only \
  --report analysis.md

# Analyze with CoPilot mode (enhanced prompts)
specfact --mode copilot import from-code \
  --repo ./my-project \
  --confidence 0.7 \
  --report analysis.md

# Review generated plan
cat analysis.md
```

**With IDE Integration:**

```bash
# Initialize IDE integration
specfact init --ide cursor

# Use slash command in IDE chat
/specfact-import-from-code --repo . --confidence 0.7
```

See [IDE Integration Guide](../guides/ide-integration.md) for setup instructions.

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

- **Start in shadow mode**: Use `--shadow-only` to observe without blocking
- **Use dry-run**: Always preview with `--dry-run` before writing changes
- **Check reports**: Generate reports with `--report <filename>` for review
- **Progressive enforcement**: Start with `minimal`, move to `balanced`, then `strict`
- **Mode selection**: Auto-detects CoPilot mode; use `--mode` to override
- **IDE integration**: Use `specfact init` to set up slash commands in IDE
- **Bidirectional sync**: Use `sync spec-kit` or `sync repository` for ongoing change management

## Common Commands

```bash
# Check version
specfact --version

# Get help
specfact --help
specfact <command> --help

# Initialize plan
specfact plan init --interactive

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
