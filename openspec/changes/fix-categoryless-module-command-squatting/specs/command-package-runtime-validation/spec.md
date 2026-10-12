## ADDED Requirements

### Requirement: Permanent Core Commands Cannot Be Extended By External Packages

The system SHALL reserve `init`, `module` and `upgrade` for packages whose resolved path belongs to the
effective built-in module tree selected by the operator-controlled discovery configuration. External packages SHALL NOT
register or extend these commands in either command
registry, regardless of category, grouping mode, discovery source label or manifest name.

#### Scenario: Workspace package impersonates a core category

- **GIVEN** a workspace package declares `category: core` and a permanent core command
- **WHEN** package commands are registered and the existing root command is invoked
- **THEN** the original built-in loader SHALL remain unchanged
- **AND** no external loader SHALL be registered or executed for that command

#### Scenario: Forged source and symlink cannot grant core authority

- **GIVEN** an external package claims a built-in source or is symlinked from the built-in tree
- **WHEN** its resolved path is outside the built-in tree and it declares a permanent core command
- **THEN** both registries SHALL reject that external command in either grouping mode
- **AND** legitimate built-in commands SHALL continue to load

#### Scenario: Explicit repository root preserves legitimate built-ins

- **GIVEN** the operator sets SPECFACT_REPO_ROOT to another checkout containing built-in modules
- **WHEN** discovery loads a permanent core package from that effective root
- **THEN** resolved contained packages SHALL retain core authority
- **AND** a symlink escaping that root SHALL NOT gain core authority

### Requirement: Workspace Packages Cannot Supply Official Category Roots

Project packages SHALL NOT supply official category root command names in either mode, regardless of
claimed category, bundle or source fields in their manifest. Rejected packages SHALL cause no registration
side effects, including category-builder imports or app initialization during eligibility checks. Eligible
non-project installed bundles SHALL retain their category roots.

#### Scenario: Workspace manifest impersonates an official category root

- **GIVEN** a project package declares any official category root command
- **WHEN** package commands are registered in either grouping mode
- **THEN** the entire package SHALL be rejected before registration side effects
- **AND** existing category root loaders SHALL remain unchanged
- **AND** the rejected package SHALL NOT create a category mount through bundle metadata
