## MODIFIED Requirements

### Requirement: Enterprise Resolution Layers

Enterprise policy resolution SHALL link pushed or overridden values back to auditable actions.

#### Scenario: Resolved enterprise value references an audit event

- **GIVEN** a policy value came from a pushed or overridden enterprise rule
- **WHEN** resolution metadata is inspected
- **THEN** the metadata includes a stable audit-event reference
- **AND** the referenced event identifies the actor and role that changed the value.
