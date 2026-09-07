## ADDED Requirements

### Requirement: Marketplace installation authenticates official artifacts before side effects

The marketplace installer SHALL authenticate an extracted official module artifact before treating any manifest-declared dependency as installation input.

#### Scenario: Unsigned official module cannot trigger dependency installation

- **GIVEN** a downloaded marketplace archive is requested with a module ID in the `nold-ai` namespace
- **AND** the extracted artifact is missing valid signed integrity metadata
- **WHEN** the installer processes the archive
- **THEN** installation SHALL fail before resolving or installing bundle dependencies
- **AND** installation SHALL fail before resolving or installing pip dependencies
- **AND** the module SHALL NOT be placed in the installation root

#### Scenario: Verified official module retains dependency installation

- **GIVEN** a downloaded marketplace archive is requested with a module ID in the `nold-ai` namespace
- **AND** the extracted artifact has valid integrity metadata and a valid signature from trusted key material
- **WHEN** the installer processes the archive
- **THEN** verification SHALL complete before dependency processing begins
- **AND** the existing dependency resolution and atomic placement behavior SHALL continue
