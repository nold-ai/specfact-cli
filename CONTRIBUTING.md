# Contributing to SpecFact CLI

Thank you for your interest in contributing to SpecFact CLI! This document provides guidelines for contributing to the project.

## Code of Conduct

This project adheres to the [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

- Use the GitHub issue tracker
- Include detailed steps to reproduce the bug
- Provide system information and error logs
- Check if the issue has already been reported

### Suggesting Enhancements

- Use the GitHub issue tracker with the "enhancement" label
- Describe the feature and its benefits clearly
- Consider the impact on existing functionality
- **Spec-Driven Development (SDD)**: All feature requests should ideally be accompanied by a spec update in the [`openspec/`](./openspec/) folder
  - Review existing specs in [`openspec/specs/`](./openspec/specs/) to understand current capabilities
  - Create a change proposal in [`openspec/changes/`](./openspec/changes/) following the [OpenSpec OPSX workflow](docs/openspec-opsx-migration.md) (or legacy [openspec/AGENTS.md](./openspec/AGENTS.md) if present)
  - This ensures clear requirements, scenarios, and implementation guidance before coding begins

### Code Contributions

1. **Fork the repository**
2. **Review OpenSpec specs**: Check [`openspec/specs/`](./openspec/specs/) to understand existing capabilities
3. **Create spec proposal** (if needed): For new features, create a change proposal in [`openspec/changes/`](./openspec/changes/) following the [OpenSpec OPSX workflow](docs/openspec-opsx-migration.md) (or legacy [openspec/AGENTS.md](./openspec/AGENTS.md) if present)
4. **Create a feature branch**: `git checkout -b feature/your-feature-name`
5. **Make your changes** following the coding standards below
6. **Update specs**: Ensure [`openspec/specs/`](./openspec/specs/) reflects your changes
7. **Test your changes**: Run `hatch test --cover -v` to ensure all tests pass
8. **Commit your changes**: Use [Conventional Commits](https://www.conventionalcommits.org/) format
9. **Push to your fork**: `git push origin feature/your-feature-name`
10. **Create a Pull Request**: Provide a clear description of your changes and reference any OpenSpec change proposals

## Development Setup

### Prerequisites

- Python 3.10+
- Docker (for containerized development)
- Git

### Local Development

```bash
# Clone the repository
git clone https://github.com/nold-ai/specfact-cli.git
cd specfact-cli

# Install dependencies
pip install -e ".[dev]"

# Run contract-first tests
hatch run contract-test-full

# Run all tests
hatch test --cover -v
```

### Code Quality Standards

- **Python**: Follow PEP 8 style guidelines
- **Contracts**: All public APIs must have `@icontract` decorators
- **Type Hints**: Use type hints with `@beartype` runtime checking
- **Testing**: Contract-first testing with scenario tests
- **Documentation**: Update relevant documentation
- **Docs site (`docs/`)**: Jekyll pages keep existing frontmatter (`layout`, `title`, `permalink`, …).
  Pages listed in `docs/.doc-frontmatter-enforced` must include `doc_owner`, `tracks`,
  `last_reviewed`, and `exempt`; `exempt_reason` is required only when `exempt: true`. See
  [docs/contributing/docs-sync.md](docs/contributing/docs-sync.md).
- **Docstrings**: Follow Google Python Style Guide

### Pre-commit Checks

Local hooks use **`fail_fast: true`** and a **modular layout** aligned with `specfact-cli-modules`:
branch-aware module verify (skip if no staged module tree changes; `--allow-unsigned` except on
  `main`, where `--require-signature`) → sync version files when those paths are staged → format (always) →
YAML / Markdown / workflow lint when matching paths are staged → **`hatch run lint`** when Python
is staged → Block 2 (scoped code review + contract tests, with a safe-change short-circuit for
docs-only and similar commits). See `.pre-commit-config.yaml` and `scripts/pre-commit-quality-checks.sh`.

```bash
# Install framework hooks (recommended; matches CI-style stages)
pre-commit install

# Optional: copy raw script into .git/hooks/pre-commit (runs full `all` pipeline via shim)
scripts/setup-git-hooks.sh

# Manual full pipeline (same as shim)
hatch run pre-commit-checks

# Format code
hatch run format

# Type check
hatch run type-check

# Lint code
hatch run lint

# Run contract-first tests
hatch run contract-test-full
```

The supported local hook path is the repo-owned smart-check wrapper installed by the commands
above. It keeps local semantics aligned with CI:

- Merge-blocking local gates: module signature verification (branch-aware; see `scripts/pre-commit-verify-modules.sh`), formatter safety, Markdown/YAML checks,
  workflow lint for staged workflow changes, and contract-test fast feedback when code changes.
- Review gate behavior: `specfact code review run` reviews staged Python files and blocks the
  commit only on `FAIL`. `PASS_WITH_ADVISORY` remains green but still prints the JSON report path for
  remediation in Copilot/Cursor.
- Advisory review surfaces: CodeRabbit and other PR review comments remain advisory unless a branch
  protection rule explicitly promotes a check to required.
- Workflow linting requires `actionlint` on `PATH` or a Docker-enabled environment. CI installs a
  pinned `actionlint` release explicitly; local contributors should install it globally, for example
  with `go install github.com/rhysd/actionlint/cmd/actionlint@v1.7.11`.

## Contributor License Agreement (CLA)

Before we can accept your pull request, you need to agree to our [Contributor License Agreement](./CLA.md). By opening a pull request, you acknowledge that you've read and agreed to the terms.

### Why a CLA?

The CLA ensures that:

- SpecFact CLI can use your contributions in any way needed
- You're not liable for your contributions
- The project can relicense code if necessary
- Enterprise users can trust the codebase

## Third-Party Dependencies

This project uses various third-party libraries listed in `pyproject.toml`. Each library retains its original license. For license information on specific dependencies, please refer to the individual package documentation.

## Testing Guidelines

### Running Tests

```bash
# Run contract validation
hatch run contract-test-contracts

# Run contract exploration (CrossHair)
hatch run contract-test-exploration

# Run scenario tests
hatch run contract-test-scenarios

# Run all contract-first tests
hatch run contract-test-full

# Run specific test file
hatch test --cover -v tests/unit/specfact_cli/test_cli.py
```

### Writing Tests

- Write contracts (`@icontract` decorators) for all new public APIs
- Add property-based tests with Hypothesis for complex logic
- Write scenario tests for CLI command workflows
- Use descriptive test names following `test_<command>_<scenario>` pattern
- Ensure tests are deterministic and fast

## Spec-Driven Development (SDD)

SpecFact CLI uses **Spec-Driven Development (SDD)** via [OpenSpec](./openspec/) to ensure clear requirements and maintainable code.

### OpenSpec Workflow

1. **Review existing specs**: Check [`openspec/specs/`](./openspec/specs/) to understand current capabilities
2. **Create change proposals**: For new features or significant changes, create proposals in [`openspec/changes/`](./openspec/changes/)
3. **Follow OpenSpec guidelines**: See [OPSX migration](docs/openspec-opsx-migration.md) and optionally [`openspec/AGENTS.md`](./openspec/AGENTS.md) for workflow instructions
4. **Update specs**: When implementing changes, update the relevant spec files to reflect the new behavior

### When to Create Spec Proposals

**Create a spec proposal when:**

- Adding new features or functionality
- Making breaking changes (API, schema)
- Changing architecture or patterns
- Optimizing performance (changes behavior)
- Updating security patterns

**Skip spec proposals for:**

- Bug fixes (restore intended behavior)
- Typos, formatting, comments
- Dependency updates (non-breaking)
- Configuration changes
- Tests for existing behavior

### OpenSpec Resources

- **Project config (OPSX)**: [`openspec/config.yaml`](./openspec/config.yaml) - Schema, context, and per-artifact rules (primary)
- **Project overview (legacy)**: [`openspec/project.md`](./openspec/project.md) - High-level conventions (fallback if no config.yaml)
- **Workflow guide**: [OPSX migration](docs/openspec-opsx-migration.md); optionally [`openspec/AGENTS.md`](./openspec/AGENTS.md) if present
- **Current specs**: [`openspec/specs/`](./openspec/specs/) - Specifications for all capabilities
- **Active changes**: [`openspec/changes/`](./openspec/changes/) - Proposed changes and implementations

## Documentation

### Updating Documentation

- Update relevant documentation when adding features
- Include code examples where appropriate
- Follow the existing documentation style
- Test documentation examples
- **Update OpenSpec specs**: When implementing features, ensure [`openspec/specs/`](./openspec/specs/) reflects the new behavior

### Entry-Point Messaging Hierarchy

The repository README, `docs/index.md`, and other first-contact surfaces must preserve the same
first-contact story.

When editing those surfaces, make sure a new visitor can quickly answer:

- **What is SpecFact?**
- **Why does it exist?**
- **Why should I use it?**
- **What do I get?**
- **How do I get started?**

Keep the hierarchy in this order:

1. Product identity
2. Why it exists
3. User value
4. How to get started
5. Deeper topology and cross-site handoff

For first-contact pages, define SpecFact as the validation and alignment layer for software delivery
and present “keep backlog, specs, tests, and code in sync” as the user-visible outcome of that
positioning.

GitHub-facing repo metadata must reinforce the same story. Keep the repository description, topics,
and other above-the-fold cues aligned with the README hero so visitors see the same product
identity before and after opening the repository.

### Documentation Structure

- `README.md`: Project overview and quick start
- `AGENTS.md`: Repository guidelines and development patterns
- `openspec/`: Spec-Driven Development (SDD) specifications and change proposals
  - `openspec/config.yaml`: OPSX project config (schema, context, rules)
  - `openspec/project.md`: Legacy project conventions (used if no config.yaml)
  - `openspec/AGENTS.md`: Legacy workflow instructions (optional after OPSX)
  - `openspec/specs/`: Current capability specifications
  - `openspec/changes/`: Proposed changes and implementations
- `.cursor/rules/`: Cursor AI development rules
- `CONTRIBUTING.md`: Contribution guidelines and workflow

## Release Process

### Version Management

- Follow [Semantic Versioning](https://semver.org/)
- Update `CHANGELOG.md` with all changes
- Update version in `pyproject.toml` and `setup.py`

### Release Checklist

- [ ] All tests pass
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] Version numbers are updated
- [ ] Release notes are prepared

## Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Documentation**: Check the [README.md](./README.md) first
- **Discussions**: Use GitHub Discussions for questions
- **Email**: [hello@noldai.com](mailto:hello@noldai.com)

## Recognition

Contributors will be recognized in:

- The [CHANGELOG.md](CHANGELOG.md)
- The project README (for significant contributions)
- Release notes

Thank you for contributing to SpecFact CLI!

---

Copyright (c) 2025 Nold AI (Owner: Dominikus Nold)
