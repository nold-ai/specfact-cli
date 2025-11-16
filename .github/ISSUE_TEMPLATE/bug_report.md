---
name: Bug report
about: Report a bug in SpecFact CLI
title: "[Bug] <Brief Description>"
labels: bug
assignees: ''

---

## Describe the Bug

A clear and concise description of what the bug is.

## To Reproduce

Steps to reproduce the behavior:

```bash
# Example command that triggers the bug
specfact <command> --options
```

**Example:**

```bash
specfact import from-code ./my-legacy-project --confidence 0.8
```

## Expected Behavior

A clear and concise description of what you expected to happen.

## Actual Behavior

What actually happened? Include error messages, stack traces, or unexpected output.

## Environment

- **OS**: [e.g., Linux, macOS, Windows]
- **Python Version**: [e.g., 3.11.5]
- **SpecFact CLI Version**: [e.g., 0.1.0 - run `specfact --version`]
- **Installation Method**: [e.g., pip, uvx, from source]

## Command Output

Include the full command output (with `--verbose` if applicable):

```markdown
Paste command output here
```

## Codebase Context (for brownfield issues)

If this bug occurs when analyzing legacy code:

- **Project Type**: [e.g., Django, Flask, FastAPI, plain Python]
- **Codebase Size**: [e.g., ~10K lines, ~100 files]
- **Python Version in Target Codebase**: [e.g., 3.8, 3.11]

## Additional Context

Add any other context about the problem here, such as:

- Related issues or PRs
- Workarounds you've found
- Impact on your workflow
