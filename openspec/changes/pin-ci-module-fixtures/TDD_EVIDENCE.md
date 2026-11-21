# Fixture checkout evidence

The test-only commit `cba5877dd97208b350f8b41a9e5c35420bc9c1c6` produced three expected checkout assertion failures, zero errors and zero skips. The Requirements evidence archive retained the original JUnit report and recorded `failing-first-proven`. [GitHub run 44846142327](https://github.com/nold-ai/specfact-cli/actions/runs/44846142327)

After pinning the reviewed repository and commits, 123 focused workflow tests passed locally, including the same three selectors. Ruff, Actionlint, strict OpenSpec validation and reproducible dependency checks passed. Hosted verification is tracked on the follow-up pull request.

## Semgrep dependency isolation

Before the implementation, both added scanner tests failed with the old profiles and workflow. A separate local view at the earlier test-only commit with the expanded test plan had five expected assertion failures, zero errors and zero skips.

On the split, 246 focused cases passed in the installed frozen shared environment, including the five selected tests, both lock boundaries and the telemetry tests. The built wheel and installed shared environment exclude Semgrep, MCP and wcmatch from the shared package graph. The shared, Code Review and runtime-smoke advisory audits passed with an empty exception register. The separate scanner audit rejected wcmatch CVE-2026-132276 before scanner installation. The scans, trust policies and existing expiry dates were retained. Hosted test-first evidence and final exact-head checks are pending.
