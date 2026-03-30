# Design: trustworthy-green-checks

## Context

The current quality surface has four enforcement layers:

1. Local git hooks and smart checks
2. GitHub Actions workflows
3. PR review automation (CodeRabbit)
4. OpenSpec/process evidence

The main weakness is not missing tools; it is inconsistent semantics between these layers. A hard-fail signal in one layer can be advisory in another, and some checks look blocking in the UI even though their shell commands intentionally suppress failure.

## Design goals

- Make required signals unambiguous.
- Preserve advisory signals where they are useful, but name and wire them as advisory.
- Minimize duplicate logic across local hooks and CI.
- Keep release-forward PRs fast only when fast-path safety is provable.

## Enforcement model

### 1. Gate taxonomy

Each workflow check must be classified as one of:

- **Required gate**: failure exits non-zero and must block merge.
- **Advisory gate**: failure is surfaced as warning/log/report but does not block merge.

The implementation should avoid mixed semantics such as required-looking jobs that use `|| echo`, broad `continue-on-error`, or "warning-only" shell wrappers without an explicit advisory job name.

### 2. Release PR parity

`dev -> main` can skip re-running the full suite only if the release PR head is exactly the already-validated commit set from `dev`, with no follow-up commits that change workflow/config/spec/release metadata after the validated merge tip.

If parity cannot be proven cheaply and deterministically, the workflow must run the required validation set again.

### 3. Workflow-change enforcement

Changes under `.github/workflows/**` must trigger mandatory CI validation for:

- workflow syntax and actionlint rules
- shell fragments used by workflow `run:` steps where supported

This closes the current gap where workflow correctness depends too heavily on local tooling or bot analysis.

### 4. Local-vs-CI parity

The supported pre-commit installation path must expose the same core enforcement semantics as CI for:

- module signature verification
- formatter safety
- Python review gate for changed Python files
- workflow/static config validation when relevant files are staged

The exact implementation can either expand `.pre-commit-config.yaml` or ensure the repo-supported setup always installs the smart-check wrapper as the authoritative hook path.

### 5. Review automation coverage

CodeRabbit should not silently treat `dev` and `main` differently for automatic review coverage when both are active PR targets. The change only standardizes review coverage and expectations; it does not by itself turn CodeRabbit findings into a merge blocker.

## Out of scope

- Replacing CodeRabbit with a different review system
- Rewriting the full orchestrator into reusable workflows
- Changing production CLI behavior
- Reworking OpenSpec governance schemas
