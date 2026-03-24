# Capability: docs-command-validation

Automated validation that documentation command examples match actual CLI implementations.

## Scenarios

### Scenario: Valid command example passes validation

Given a docs page contains a code block with `specfact backlog ceremony standup`
When the validation script runs
Then it finds a matching command registration in the backlog module source
And the check passes

### Scenario: Invalid command example fails validation

Given a docs page contains a code block with `specfact backlog nonexistent-command`
When the validation script runs
Then it reports the unmatched command with file path and line number
And the check fails with a non-zero exit code

### Scenario: CI blocks PR with broken command examples

Given a PR modifies docs/ files
When the docs-review workflow runs
Then the command validation step executes
And a failing check prevents merge
