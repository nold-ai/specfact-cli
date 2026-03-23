# Capability: docs-cross-site-link-check

Automated validation of cross-site links between core and modules docs.

## Scenarios

### Scenario: Valid cross-site link passes

Given a core docs page links to https://modules.specfact.io/bundles/backlog/overview/
When the link validation runs
Then the URL resolves (200 or redirect to 200)
And the check passes

### Scenario: Broken cross-site link fails

Given a core docs page links to https://modules.specfact.io/nonexistent-page/
When the link validation runs
Then the URL returns 404
And the check reports the broken link with source file and line number
