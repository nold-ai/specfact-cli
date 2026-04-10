## MODIFIED Requirements

### Requirement: Pending Changes Must Align With The Ownership Decision

Pending OpenSpec changes that touch command surface, docs, prompts, migration cleanup, or issue planning SHALL align with the canonical post-migration ownership model instead of reintroducing monolithic `specfact-cli` module ownership by implication.

#### Scenario: Active change does not finalize conflicting import ownership

- **GIVEN** an active pending change updates grouped command paths or release-facing docs
- **WHEN** that change references brownfield import ownership
- **THEN** it references the canonical owner defined by this change
- **AND** it does not re-establish a conflicting public command path or subsystem owner by implication.

#### Scenario: Active proposal does not preserve obsolete in-repo module paths

- **GIVEN** an active proposal still describes implementation under `modules/<name>/` in `specfact-cli` for a capability now owned by a bundle in `specfact-cli-modules`
- **WHEN** maintainers reconcile the proposal against the current architecture
- **THEN** the proposal is updated to the correct repository and bundle ownership model
- **AND** any remaining core-repo scope is reduced to the shared runtime, contract, or integration surface that core still owns.
