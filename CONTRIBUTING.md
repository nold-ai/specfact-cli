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

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** following the coding standards below
4. **Test your changes**: Run `hatch test --cover -v` to ensure all tests pass
5. **Commit your changes**: Use [Conventional Commits](https://www.conventionalcommits.org/) format
6. **Push to your fork**: `git push origin feature/your-feature-name`
7. **Create a Pull Request**: Provide a clear description of your changes

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
- **Docstrings**: Follow Google Python Style Guide

### Pre-commit Checks

```bash
# Format code
hatch run format

# Type check
hatch run type-check

# Lint code
hatch run lint

# Run contract-first tests
hatch run contract-test-full
```

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

## Documentation

### Updating Documentation

- Update relevant documentation when adding features
- Include code examples where appropriate
- Follow the existing documentation style
- Test documentation examples

### Documentation Structure

- `README.md`: Project overview and quick start
- `AGENTS.md`: Repository guidelines and development patterns
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
