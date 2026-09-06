## ADDED Requirements

### Requirement: Bundled module snapshots reference published release assets

The bundled-module publisher SHALL derive a tag-qualified GitHub release URL
from the validated module identity and version. It SHALL publish a reproducible
tarball and checksum from clean, already-signed bytes at an exact commit reachable
from `dev` or `main`, download the published tarball, and verify its checksum
before advancing the bundled registry snapshot. Existing release identities SHALL
be reused only when their exact source tag and assets verify; every mismatch SHALL
fail closed rather than overwrite an immutable module version.

#### Scenario: Publication precedes bundled snapshot advancement

- **GIVEN** a validated bundled module archive and checksum
- **WHEN** a tag, manual, or protected-branch automatic publication runs
- **THEN** the release tag SHALL be `{module-slug}-v{module-version}`
- **AND** the registry URL SHALL include that tag and the exact archive name
- **AND** the workflow SHALL publish and redownload the release asset before updating the snapshot
- **AND** a source outside `dev` or `main`, unsigned or dirty source bytes, a mismatched release identity, or a checksum mismatch SHALL stop publication before the snapshot changes
- **AND** retrying after an exact release was created SHALL verify and reuse that immutable release without replacing it.
