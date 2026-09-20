## MODIFIED Requirements

### Requirement: Protected consumer SHALL independently verify C14 range evidence

The protected core consumer SHALL accept only an approved signed schema 1.7 producer
report whose `assurance_kind` is `range_candidate`. It SHALL independently
derive the unique merge base, complete governed selection, changed-line, Git
status/deletion/rename/object-type/mode manifests, target-tip policy/config and
project-runtime identities, approved suppression-catalog digest, signed
producer/package/profile/toolchain/checkpoint identities, and protected
workflow/artifact provenance. It SHALL compare those values to the producer
report without treating producer-derived expected values as authority. This
replaces the C14 schema 1.6-only acceptance rule after C15 adoption; the remaining
C14 authority, trusted-context and provenance requirements remain unchanged.
Schema 1.6 MAY be read only in the documented shadow compatibility path for one
migration release and SHALL NOT satisfy protected blocking enforcement.

#### Scenario: Complete trusted candidate is promoted

- **GIVEN** the approved signed schema 1.7 producer report declares `range_candidate`
- **AND** every independently derived identity and manifest exactly matches
- **WHEN** the protected core verifier evaluates the report
- **THEN** it emits a separate verifier envelope with
  `effective_assurance_kind=pr_range`
- **AND** the envelope binds every compared identity, manifest digest, producer
  report digest, protected-context digest, decision, and reason code.

#### Scenario: Merge base is ambiguous or mismatched

- **GIVEN** the protected verifier derives zero or multiple best merge bases,
  or its unique merge base differs from the producer claim
- **WHEN** it evaluates the report
- **THEN** the effective assurance status is `UNKNOWN`
- **AND** it does not emit effective `pr_range`.

#### Scenario: Governed input evidence is incomplete or mismatched

- **GIVEN** governed selection, changed lines, diff, rename, deletion, Git
  object type, or Git mode evidence is omitted or differs
- **WHEN** the protected verifier compares the manifests
- **THEN** it records the specific mismatch as `UNKNOWN`
- **AND** the protected check cannot report success in enforce mode.

#### Scenario: Older schema cannot satisfy protected C15 enforcement

- **GIVEN** a schema 1.6 report with otherwise complete C14 provenance
- **WHEN** protected blocking policy requires schema 1.7 after C15 adoption
- **THEN** it cannot satisfy the required check or be inferred to contain missing C15 fields
- **AND** any permitted shadow read retains its actual schema and non-enforcing status.
