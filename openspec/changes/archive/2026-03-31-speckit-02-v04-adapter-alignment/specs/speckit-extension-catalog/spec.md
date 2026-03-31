## ADDED Requirements

### Requirement: Extension catalog detection

The system SHALL detect spec-kit extension catalogs in a target repository by scanning for `extensions/catalog.community.json` and `extensions/catalog.core.json` files relative to the repository root or `.specify/` directory.

#### Scenario: Detect community extension catalog

- **GIVEN** a repository with `.specify/` directory and `extensions/catalog.community.json`
- **WHEN** `SpecKitScanner.scan_extensions()` is called
- **THEN** the scanner returns a list of extension metadata objects parsed from the catalog JSON
- **AND** each extension object contains at minimum `name`, `commands`, and `version` fields

#### Scenario: Detect core extension catalog

- **GIVEN** a repository with `extensions/catalog.core.json`
- **WHEN** `SpecKitScanner.scan_extensions()` is called
- **THEN** the scanner parses both core and community catalogs
- **AND** core extensions are included alongside community extensions in the result

#### Scenario: No extension catalog present

- **GIVEN** a repository with `.specify/` directory but no `extensions/` directory
- **WHEN** `SpecKitScanner.scan_extensions()` is called
- **THEN** the scanner returns an empty list
- **AND** no error is raised

#### Scenario: Malformed extension catalog

- **GIVEN** a repository with `extensions/catalog.community.json` containing invalid JSON
- **WHEN** `SpecKitScanner.scan_extensions()` is called
- **THEN** the scanner logs a warning
- **AND** returns an empty list for that catalog
- **AND** does not raise an exception

### Requirement: Extension command extraction

The system SHALL extract slash commands provided by each detected extension, making them available in `ToolCapabilities.extension_commands`.

#### Scenario: Extract commands from extension metadata

- **GIVEN** a parsed extension catalog with entries containing `commands` arrays
- **WHEN** `SpecKitAdapter.get_capabilities()` processes extension metadata
- **THEN** `ToolCapabilities.extension_commands` contains a dict mapping extension name to its command list
- **AND** each command is a string (e.g., `"/speckit.reconcile.run"`, `"/speckit.sync.detect"`)

#### Scenario: Extension with no commands

- **GIVEN** a parsed extension catalog with an entry that has an empty `commands` array
- **WHEN** extension commands are extracted
- **THEN** that extension is included in `ToolCapabilities.extensions` but has an empty command list in `extension_commands`

### Requirement: Extension ignore support

The system SHALL respect `.extensionignore` files when reporting active extensions.

#### Scenario: Extension excluded by extensionignore

- **GIVEN** a repository with `extensions/catalog.community.json` containing extension "verify"
- **AND** a `.extensionignore` file containing the line "verify"
- **WHEN** `SpecKitScanner.scan_extensions()` is called
- **THEN** the "verify" extension is excluded from the returned list

#### Scenario: No extensionignore file

- **GIVEN** a repository with extensions but no `.extensionignore` file
- **WHEN** `SpecKitScanner.scan_extensions()` is called
- **THEN** all extensions from the catalogs are included in the result
