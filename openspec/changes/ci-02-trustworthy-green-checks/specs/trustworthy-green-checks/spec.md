## ADDED Requirements

### Requirement: Required CI jobs fail on required tool failures

Workflow jobs classified as required merge gates SHALL exit non-zero when their underlying required tool fails, and SHALL NOT suppress the failure behind warn-only shell patterns or broad continue-on-error handling.

#### Scenario: Required compatibility or contract job encounters a tool failure

- **WHEN** a required job in `pr-orchestrator.yml` runs a compatibility, contract, lint, or equivalent required validation command
- **AND** the underlying command exits non-zero
- **THEN** the workflow job exits non-zero
- **AND** the GitHub check does not report success for that job

### Requirement: Advisory jobs are explicit and non-deceptive

Non-blocking validation jobs SHALL be labeled and documented as advisory so maintainers can distinguish useful warnings from required merge gates.

#### Scenario: Repository keeps a warn-only validation job

- **WHEN** a workflow contains a non-blocking validation step or job
- **THEN** the job name or step output clearly marks it as advisory
- **AND** branch protection guidance does not rely on that advisory check as evidence that required validation passed

### Requirement: Main-bound release PRs only skip tests when parity is provable

`dev -> main` pull requests SHALL skip the full required validation set only when the workflow can prove the PR head is already-covered by the validated `dev` commit set without additional follow-up commits affecting release safety.

#### Scenario: Release PR contains follow-up commits after the last validated dev merge tip

- **WHEN** a `dev -> main` pull request includes additional commits beyond the already-validated merge tip from `dev`
- **THEN** the workflow does not use the fast-path skip
- **AND** the required validation set runs again for the release PR

### Requirement: Workflow changes trigger mandatory workflow lint validation

Changes under `.github/workflows/**` SHALL trigger mandatory CI validation for workflow syntax and supported shell/static checks so workflow regressions cannot rely solely on local tooling or bot review.

#### Scenario: Pull request modifies a GitHub Actions workflow

- **WHEN** a pull request changes one or more files under `.github/workflows/`
- **THEN** CI runs mandatory workflow validation for those changes
- **AND** a workflow-lint failure blocks the required check from reporting success

### Requirement: Supported local pre-commit installation matches core CI gate semantics

The repository-supported pre-commit installation path SHALL enforce the same core gate semantics that CI relies on for changed files, rather than leaving stronger checks only in an optional wrapper unknown to standard contributors.

#### Scenario: Contributor installs the documented local hooks

- **WHEN** a contributor follows the repository-supported hook installation path
- **THEN** staged Python, workflow, Markdown, and module-signature relevant changes receive the documented local gate coverage
- **AND** the contributor is not relying on a weaker default `.pre-commit` path than the one CI and maintainer guidance assume

### Requirement: Automatic PR review coverage includes both active protected targets

Automatic repository review configuration SHALL cover pull requests targeting both `dev` and `main` when both branches are active protected integration targets.

#### Scenario: Release-forward pull request targets main

- **WHEN** a pull request targets `main`
- **THEN** the configured automatic review system applies the same target-branch auto-review policy used for `dev`
- **AND** release PRs do not silently lose their default automated review pass
