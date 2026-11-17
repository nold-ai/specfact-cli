# Change: Match analyzer exclusions within the repository

## Why

Python3.11 CI skipped a nested source feature. The analyzer matches exclusion
substrings against absolute paths, so repository names containing env, build
or dist suppress valid source files. The original test reproduces this result
under an env-named temporary parent.

## What changes

Match excluded directories as whole repository-relative components. Preserve
test-file naming rules, real excluded directories, public APIs and thresholds.
Add deterministic regression cases. No dependency or workflow changes.

## Impact

One analyzer method, its unit tests and one existing integration test.
Rollback is a normal revert. No module repository or signing-policy changes.
