## ADDED Requirements

### Requirement: Frozen source and live authority

The signer SHALL strictly decode the intent, authenticate S to T, prove the
complete exact dev-to-T leaf delta and verify every frozen execution identity
and ref before any write. It SHALL reject production, auxiliary signer and workflow changes in D and every
unknown, duplicate, malformed or incomplete input. The allowlist applies only
to changed leaves. Authenticated unchanged production and executable leaves
and directory entries remain valid parts of the complete trees. Dispatch
expectations and context SHALL independently agree with live observations.

#### Scenario: Exact reviewed source

- **GIVEN** a digest-bound valid intent and complete matching source/tree/delta
- **WHEN** all live run and ref guards agree
- **THEN** signing may proceed using T and sole parent dev

#### Scenario: Precondition failure

- **GIVEN** any intent, source, delta, identity, run, ref or completeness mismatch
- **WHEN** publication is requested
- **THEN** the receipt is refused and there are zero writes

### Requirement: Two create-only writes

The signer SHALL create exactly one GitHub verified service commit, validate
response/readback/signed payload and attribution, then create the absent fixed
ref. It SHALL recheck guards around both writes and verify the final objects.

#### Scenario: Successful creation

- **WHEN** both POSTs return definite creation and every verification agrees
- **THEN** the only writes are commit creation followed by ref creation
- **AND** the receipt preserves the exact intent/run/signature evidence

#### Scenario: Invalid service signature or attribution

- **GIVEN** a known commit with wrong roles, payload, verification or readback
- **WHEN** the commit is checked
- **THEN** the receipt is object_only and no ref write occurs

### Requirement: Truthful partial outcomes

The signer SHALL never retry a write or convert an uncertain write into
success from subsequent observations. It SHALL retain known partial effects
and SHALL NOT patch, delete, clean up or construct trees.

#### Scenario: Ambiguous write

- **WHEN** either POST times out or returns an ambiguous response
- **THEN** the receipt is uncertain_commit or uncertain_ref respectively
- **AND** no write is repeated even if the object/ref becomes observable

#### Scenario: Drift after a write

- **WHEN** a guard changes after known commit creation
- **THEN** the receipt is object_only and there is no ref write
- **WHEN** a guard changes after known ref creation
- **THEN** the receipt is created_ref_with_drift and never published

#### Scenario: Known commit and ambiguous ref response

- **GIVEN** commit creation and verification succeeded
- **WHEN** the ref creation response is ambiguous
- **THEN** uncertain_ref retains the known commit SHA without another write

#### Scenario: Final verification fails

- **GIVEN** both creation responses succeeded
- **WHEN** final ref, signature, payload, attribution or live authority checks fail
- **THEN** created_ref_with_drift retains known creation effects without another write
