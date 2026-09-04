# Change: Isolate CI tests from pull-request routing state

## Why

GitHub Actions exposes `GITHUB_BASE_REF` to pull-request jobs so workflows can
select the correct comparison branch. The Python 3.12 and Python 3.11 test
suites currently pass that routing variable into every test process. Tests that
create synthetic Git repositories can therefore observe the outer pull request
instead of their fixture history and fail for reasons unrelated to the behavior
under test.

The correction belongs at the test-process boundary. Test helpers should not
each need to know which GitHub routing variables exist, while release,
signature, diff-selection, and other workflow steps must retain the genuine
pull-request base.

## What Changes

- Remove `GITHUB_BASE_REF` inside only the primary and compatibility Bash test
  steps, immediately before their Python launchers execute.
- Preserve the normal GitHub-provided value for all non-test workflow steps.
- Add workflow regression coverage proving both boundaries.
- Keep the version-source production check and its test helpers unchanged.

## Capabilities

### Modified Capabilities

- `test-suite-stabilization`

## Impact

- Affected workflow: `.github/workflows/pr-orchestrator.yml`.
- Affected tests: focused workflow contract coverage only.
- Public CLI, API, dependency graph, module payload, and package behavior are
  unchanged.
- No user documentation changes are needed because this is internal CI
  isolation. Contributor-facing evidence stays in this OpenSpec change and its
  pull request.
- This fix joins the existing unreleased `0.55.4` transaction; it must not
  consume another package version.
- Rollback is a normal revert of the workflow commit.

## Source Tracking

- **GitHub Issue**: #708
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/708>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: in progress
- **Parent Issue**: #692
- **Related Long-Term Design**: #675 / `requirements-08-bounded-red-green-proof`
