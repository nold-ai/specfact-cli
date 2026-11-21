# Fixture checkout evidence

The test-only commit `cba5877dd97208b350f8b41a9e5c35420bc9c1c6` produced three expected checkout assertion failures, zero errors and zero skips. The Requirements evidence archive retained the original JUnit report and recorded `failing-first-proven`. [GitHub run 44846142327](https://github.com/nold-ai/specfact-cli/actions/runs/44846142327)

After pinning the reviewed repository and commits, 123 focused workflow tests passed locally, including the same three selectors. Ruff, Actionlint, strict OpenSpec validation and reproducible dependency checks passed. Hosted verification is tracked on the follow-up pull request.
