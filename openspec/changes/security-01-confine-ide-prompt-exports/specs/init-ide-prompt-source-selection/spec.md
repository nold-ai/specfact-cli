## ADDED Requirements

### Requirement: IDE prompt exports are repository confined

The CLI SHALL perform IDE prompt cleanup and export only through a non-symlink
export root whose resolved path is contained beneath the resolved target
repository. It SHALL NOT delete or write through an unsafe export root and
SHALL preserve unrelated team-owned directories.

#### Scenario: Repository-controlled export root targets an external directory

- **GIVEN** an IDE prompt export root in the target repository is a symlink to a writable external directory
- **WHEN** IDE prompt initialization attempts cleanup and export
- **THEN** the CLI rejects the unsafe export root before deleting or writing any external content

#### Scenario: Normal repository-contained export

- **GIVEN** an IDE prompt export root is a real directory beneath the target repository
- **WHEN** IDE prompt initialization cleans legacy SpecFact exports and writes selected prompts
- **THEN** the CLI completes the export while leaving unrelated team-owned directories intact
