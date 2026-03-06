## ADDED Requirements

### Requirement: Init IDE Must Export All Prompt Sources By Default

`specfact init ide` SHALL export all available prompt sources by default.

#### Scenario: Default export includes core and installed modules
- **WHEN** a user runs `specfact init ide` without restricting prompt sources
- **THEN** prompt export includes core prompts
- **AND** prompt export includes prompts from installed and enabled modules that provide prompt resources.

### Requirement: Init IDE Must Support Interactive Prompt Source Selection

Interactive `specfact init ide` SHALL allow users to choose prompt sources from installed options.

#### Scenario: Interactive picker shows available sources
- **WHEN** `specfact init ide` runs in interactive mode
- **THEN** it shows a multi-select source picker containing `core` and installed module ids with prompt resources
- **AND** the selected sources determine which prompt resources are copied.

### Requirement: Init IDE Must Support Non-Interactive Prompt Source Selection

Non-interactive `specfact init ide` SHALL accept a comma-separated prompt source selector.

#### Scenario: Non-interactive selector accepts core and module ids
- **WHEN** a user runs `specfact init ide --prompts core,nold-ai/specfact-backlog`
- **THEN** core prompts and the selected installed module prompts are copied
- **AND** unrelated prompt sources are not copied.

#### Scenario: Invalid or unavailable module source is rejected
- **WHEN** a user passes a prompt source token that is not `all`, not `core`, and not an installed module id with prompt resources
- **THEN** the command fails with actionable guidance describing the invalid token and the available prompt sources.
