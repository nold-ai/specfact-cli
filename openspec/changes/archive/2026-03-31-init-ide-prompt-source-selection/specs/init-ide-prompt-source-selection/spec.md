## ADDED Requirements

### Requirement: Init IDE Must Export All Prompt Sources By Default

`specfact init ide` SHALL export all available prompt sources by default.

#### Scenario: Default export includes core and installed modules across effective roots

- **WHEN** a user runs `specfact init ide` without restricting prompt sources
- **THEN** prompt export includes core prompts
- **AND** prompt export includes prompts from installed and enabled modules that provide prompt resources
- **AND** the catalog is built from the effective built-in, project, user, and configured custom module roots for that repository context.

### Requirement: Init IDE Must Discover Sources From Installed Module Roots Only

`specfact init ide` SHALL discover prompt and related module-owned resources from installed module roots and packaged resource directories. It SHALL not fetch module archives or treat the modules source repository as a runtime extraction source.

#### Scenario: Installed project-scope bundle contributes prompt resources

- **WHEN** a repository has an installed module under `<repo>/.specfact/modules`
- **THEN** `specfact init ide` can discover that module's packaged prompt resources for export in that repository.

#### Scenario: Installed user-scope bundle contributes prompt resources

- **WHEN** a user has installed a module under `~/.specfact/modules`
- **AND** no overriding project-scope copy shadows it
- **THEN** `specfact init ide` can discover that module's packaged prompt resources for export.

#### Scenario: Missing selected source does not trigger install work

- **WHEN** a selected prompt source is not installed or does not expose the required packaged resources
- **THEN** `specfact init ide` fails or warns with actionable guidance
- **AND** the guidance names the relevant scope and install/bootstrap command such as `specfact module init --scope project` or `specfact module install --scope user`
- **AND** the command does not download, install, or extract the module itself.

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

### Requirement: Exported Prompt Files Must Be IDE-Discoverable With Deterministic Single Sourcing

Exported prompts for VS Code / Copilot (under ``.github/prompts/``) and other multi-source IDE targets SHALL use a **flat** layout (no per-source subfolders) so editors and agents can discover ``specfact*.prompt.md`` (or equivalent) at the export root.

#### Scenario: Core defers to modules on overlapping template basenames

- **WHEN** `core` and one or more installed modules expose the same source filename (e.g. ``specfact.01-import.md``)
- **THEN** the prompt catalog SHALL list that basename only under the owning module source
- **AND** `core` SHALL NOT duplicate that basename so exports are single-sourced.

#### Scenario: Multiple module sources expose the same basename

- **WHEN** two installed modules expose the same template basename
- **THEN** the merged export uses a deterministic last-wins rule by sorted source id (later id overwrites earlier)
- **AND** the flat export contains exactly one file per output basename.
