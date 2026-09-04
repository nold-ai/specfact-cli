# Change: Fix final Requirements review artifact handling

## Why

The final Requirements job intentionally exits its Code Review step successfully
when a pull request changes no Python files. Its following artifact upload is
unconditional and configured to fail when the review report is absent. A
metadata-only pull request therefore cannot satisfy the required Requirements
context even though no final Python review is expected.

The correction must distinguish an intentional no-review path from a required
review that failed to produce evidence. Missing artifacts for real Python
review targets must continue to fail closed.

## What Changes

- Have the final Code Review step publish an explicit output that records whether
  Python review targets exist.
- Upload the final Code Review artifact only when that authenticated step output
  says review was required.
- Preserve strict missing-artifact failure and review-verdict enforcement for
  every Python-changing pull request.
- Preserve the accepted R07 deleted-path filter: deletion-only changes have no
  file-oriented review target, while mixed changes still review every present
  Python target.
- Add workflow contract tests for both branches and the failure control.

## Capabilities

### Modified Capabilities

- `trustworthy-green-checks`

## Impact

- Affected workflow: `.github/workflows/requirements-evidence.yml`.
- Affected tests: focused workflow contract coverage only.
- Public CLI, API, dependency graph, package payload, and module artifacts are
  unchanged.
- No user documentation changes are needed because this is an internal CI
  control-flow correction.
- This fix joins the existing unreleased `0.55.4` transaction and must not
  consume another package version.
- Rollback is a normal revert of the workflow commit.

## Source Tracking

- **GitHub Issue**: #710
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/710>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: in progress
- **Parent Issue**: #692
- **Blocks**: #692, #706, #691
