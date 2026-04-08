## MODIFIED Requirements

### Requirement: One primary fast-start path

The central entry points SHALL provide one primary "start here now" path before branching into more
specialized persona or workflow guidance. The fast-start path SHALL be inline on the homepage — it
SHALL NOT require the user to navigate to a separate page to obtain the first working command.
The primary command in the fast-start path SHALL be `specfact code review run` invoked via uvx,
as this is the highest-value, lowest-friction entry point for the broadest new-user audience.

#### Scenario: Vibe coder arrives at the homepage

- **WHEN** a first-time visitor who heard "validate your vibe code with specfact" lands on the
  homepage
- **THEN** the page SHALL display the 2-command uvx sequence as the first actionable content:
  `uvx specfact-cli init --profile solo-developer` followed by
  `uvx specfact-cli code review run --path . --scope full`
- **AND** the sequence SHALL appear before path cards, module navigation, or architecture content
- **AND** the expected result (score + categorised findings) SHALL be described so the user knows
  what "success" looks like

#### Scenario: User can complete the first run without leaving the homepage

- **WHEN** a first-time visitor reads the homepage without clicking any link
- **THEN** they SHALL find all commands needed to run their first code review
- **AND** no navigation to installation.md, quickstart.md, or modules.specfact.io SHALL be required
  to obtain and run those commands

### Requirement: Choose-your-path guidance follows the first-run path

After the primary fast-start path, entry points SHALL route users into the most relevant next step
for their intent. Path options SHALL be described as user outcomes in plain language that a
non-Python-expert can understand.

#### Scenario: User needs the right next path

- **WHEN** the user completes or reviews the first-run path
- **THEN** the entry point SHALL offer clear next-step options including at least:
  - reviewing existing code immediately (the `code review run` path)
  - setting up IDE slash-command workflows with a supported copilot
  - enabling a pre-commit or CI validation gate
- **AND** each card heading SHALL describe what the user will do or get, not a product persona
  or internal module taxonomy
- **AND** card descriptions SHALL use vocabulary understandable without Python or CLI expertise
