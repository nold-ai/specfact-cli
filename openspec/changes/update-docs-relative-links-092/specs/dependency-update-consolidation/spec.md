## ADDED Requirements

### Requirement: The documentation build uses reviewed relative links

The frozen documentation bundle SHALL install the reviewed Jekyll relative-links
0.9.2 artifact and preserve support for root and prefixed deployments.

#### Scenario: The documentation build uses reviewed relative links

- **GIVEN** the documentation bundle is frozen for the CI platform
- **WHEN** the compatibility job installs the reviewed plugin and builds the site
- **THEN** the lock and artifact digest identify the same 0.9.2 release
- **AND** titled and unresolved links preserve their intended behavior at both deployment paths.
