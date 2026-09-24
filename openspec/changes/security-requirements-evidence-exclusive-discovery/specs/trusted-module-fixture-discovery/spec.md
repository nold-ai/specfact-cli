## ADDED Requirements

### Requirement: Trusted fixture discovery is exclusive

Security-sensitive delivery gates that execute a verified external module fixture SHALL restrict dynamic module discovery to the explicitly configured fixture roots while retaining bundled core commands.

#### Scenario: Prevent untrusted module shadowing

- **GIVEN** a verified Requirements fixture and an untrusted module with the same identity in a project, user, marketplace, custom, or legacy discovery root
- **WHEN** local or CI requirements evidence enforcement invokes the released command
- **THEN** dynamic module discovery uses only the explicit verified fixture root
- **AND** bundled core commands remain available
- **AND** no untrusted same-identity module is imported or executed.

#### Scenario: Preserve ordinary module discovery

- **GIVEN** an ordinary CLI invocation that does not request exclusive discovery
- **WHEN** SpecFact discovers dynamic modules
- **THEN** existing project, explicit, user, marketplace, custom, and legacy discovery behavior remains unchanged.
