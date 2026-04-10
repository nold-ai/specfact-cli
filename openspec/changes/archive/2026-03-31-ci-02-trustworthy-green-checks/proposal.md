# Change: Trustworthy green checks for CI, pre-commit, and PR review

## Why

The repository has good coverage breadth across local hooks, workflow checks, contract validation, docs review, and AI review. The problem is enforcement consistency: several jobs that look authoritative are still advisory, local pre-commit behavior is stronger in the custom smart-check script than in `.pre-commit-config.yaml`, CodeRabbit auto-review is scoped to `dev` PRs but not `main`-bound release PRs, and the `dev -> main` fast path can skip validation for follow-up commits. Those gaps make it too easy for GitHub to show mostly green checks while some important signals are degraded or not enforced.

If maintainers cannot trust that "green" means the required checks really passed, the quality-gate surface becomes governance theater instead of a release control.

## What Changes

- **EXTEND** `.github/workflows/pr-orchestrator.yml` so required jobs fail on required tool failures instead of swallowing them behind warn-only shell patterns.
- **NEW** gate taxonomy and naming rules for CI jobs so advisory jobs are explicitly named and never masquerade as hard merge gates.
- **EXTEND** release PR validation semantics for `dev -> main` so test skipping is only allowed when commit parity is provable; otherwise release PRs must re-run the required validation set.
- **EXTEND** required-check triggering semantics so branch-protection checks always report on the
  latest PR head commit, even when a change is out of scope for the underlying validation, instead
  of being skipped entirely by workflow-level path filters.
- **EXTEND** workflow/static validation so `.github/workflows/**` changes always run mandatory workflow lint and shell validation in CI, not only via local tooling or bot review.
- **ALIGN** local pre-commit enforcement with the repository smart-check path so contributors who install the supported hooks get the same core gating semantics that CI expects.
- **EXTEND** AI review coverage so PRs targeting `main` receive the same automatic review posture as PRs targeting `dev` for the configured CodeRabbit review surface.
- **REMEDIATE** repo review findings in archived doc-frontmatter OpenSpec artifacts, docs,
  changelog entries, and helper tests so archived/main specs are publishable and markdown/config
  review findings are actually cleared rather than deferred.
- **HARDEN** code-review report handling and doc-frontmatter validation diagnostics so malformed review JSON and frontmatter parse failures surface actionable errors instead of being silently downgraded.

## Capabilities

### New Capabilities

- `trustworthy-green-checks`: the repository distinguishes blocking versus advisory signals explicitly and only reports required PR status as green when the required validation actually passed.

### Modified Capabilities

- `docs-review-gate`: remains a dedicated docs-only validation path, but its required/optional status must be explicit in repository policy and branch protection guidance.
- `code-review-module`: PR review output remains advisory unless explicitly promoted to a required gate; branch targets must not silently change auto-review coverage.

## Impact

- **Affected CI**: `.github/workflows/pr-orchestrator.yml`, `.github/workflows/pre-merge-check.yml`, and any newly added workflow-lint workflow or required job wiring.
- **Affected status policy**: branch-protection required-check selection and workflow/job naming consistency for checks emitted by `.github/workflows/pr-orchestrator.yml` and `.github/workflows/sign-modules.yml`.
- **Affected local tooling**: `.pre-commit-config.yaml`, `scripts/pre-commit-smart-checks.sh`, and associated developer setup/docs.
- **Affected review automation**: `.coderabbit.yaml` target-branch scope and review expectations for `dev` and `main`.
- **Affected docs/spec artifacts**: archived `doc-frontmatter-schema` artifacts, main OpenSpec specs, `CONTRIBUTING.md`, `docs/contributing/docs-sync.md`, and `CHANGELOG.md`.
- **Affected helper/runtime code**: `scripts/pre_commit_code_review.py`, `scripts/check_doc_frontmatter.py`, and associated tests/helpers.
- **User-facing impact**: none on CLI behavior; this is release-governance hardening for maintainers and contributors.
- **Branch protection impact**: required-check recommendations may need to be updated so only hard gates are marked required.

## Dependencies

- **Hard blocker**: `ci-01-pr-orchestrator-log-artifacts` baseline must remain intact because this change builds on the orchestrator job model rather than replacing it.
- **Hard blocker**: `code-review-08-review-run-integration` must remain the authoritative review-run integration surface.
- **Soft alignment**: `docs-04-docs-review-gate-and-link-integrity` informs the required/advisory treatment of docs-only checks but does not block this change.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #465
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/465>
- **Parent Feature**: #406
- **Parent Feature URL**: <https://github.com/nold-ai/specfact-cli/issues/406>
- **Last Synced Status**: open
- **Sanitized**: true
