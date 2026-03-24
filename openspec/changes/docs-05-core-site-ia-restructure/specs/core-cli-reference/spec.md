# Capability: core-cli-reference

Dedicated reference pages for each core CLI command (init, module, upgrade).

## Scenarios

### Scenario: Init reference page documents all subcommands and options

Given the docs/core-cli/init.md page exists
When a user reads the page
Then it documents: specfact init, init --profile, init --install, init ide, init --install-deps
And all documented commands match the actual --help output

### Scenario: Module reference page documents all subcommands

Given the docs/core-cli/module.md page exists
When a user reads the page
Then it documents: module install, module uninstall, module list, module show, module search, module upgrade, module alias, module add-registry, module list-registries, module remove-registry, module enable, module disable
And all documented commands match the actual --help output

### Scenario: Upgrade reference page documents the command

Given the docs/core-cli/upgrade.md page exists
When a user reads the page
Then it documents the specfact upgrade command and its options
