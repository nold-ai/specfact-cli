## ADDED Requirements

### Requirement: Frozen source and live authority

The signer SHALL strictly decode the intent, authenticate S to T, prove the
complete exact dev-to-T leaf delta and verify every frozen execution identity
and ref before any write. S SHALL have exactly the fixed reviewed PR786 head
as its sole parent. At each existing guard boundary PR786 SHALL be open,
non-draft, without auto-merge, at that exact head/ref/repository and the frozen
dev base/ref/repository.

#### Scenario: Exact reviewed source

- **GIVEN** a digest-bound valid intent and complete matching source/tree/delta
- **AND** the exact reviewed allowlist contains 19 test/SPEC-only paths and applies
  only to changed leaves, with frozen dev/main guards and complete dev-to-T comparison
- **AND** authenticated unchanged production and executable leaves and directory
  entries remain valid parts of the complete trees
- **WHEN** all live run and ref guards agree
- **AND** dispatch expectations and context independently agree with live observations
- **THEN** signing may proceed using T and sole reviewed parent
  `4ae6175a4d337296d0347e73b66c9da1f0e43f7f`

#### Scenario: Precondition failure

- **GIVEN** any intent, source, delta, identity, run, ref or completeness mismatch
- **OR** production, auxiliary signer or workflow changes in D, or any unknown,
  duplicate, malformed or incomplete input
- **WHEN** publication is requested
- **THEN** the receipt is refused and there are zero writes

### Requirement: Two create-only writes

The signer SHALL create exactly one GitHub verified service commit, validate
response/readback/signed payload and attribution, then create the absent fixed
ref. The created commit and signed payload SHALL use the same fixed reviewed
parent as S; the old dev parent SHALL refuse even with a consistent signature.
It SHALL recheck guards around both writes and verify the final objects.

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

### Requirement: Bounded observation after acknowledged ref creation

Only after an exact HTTP201 ref response, the signer SHALL allow a first
definite HTTP404 observation to be followed by one 60-second wait and exactly
one additional read of the same ref. It SHALL still require the exact commit,
final signature and attribution verification, and every final live guard.
It SHALL NOT repeat a write or change any prior operation's receipt.

#### Scenario: Ref becomes observable within the finite window

- **GIVEN** exact acknowledged creation and a first missing-ref observation
- **WHEN** the one additional read observes the exact expected commit
- **THEN** publication succeeds only after all final verification and guards
- **AND** there is one wait and no additional write

#### Scenario: Ref stays missing or the observation is invalid

- **WHEN** the second read stays missing, or any read returns a wrong commit,
  malformed object, non404 error or exception
- **THEN** known effects remain in a failed receipt without another write
- **AND** a wrong or invalid first observation receives no wait or second read

#### Scenario: Write uncertainty and late drift remain failures

- **WHEN** the ref POST is uncertain or final authority changes during the wait
- **THEN** the existing uncertain or drift outcome remains failed
- **AND** subsequent observations never promote a consumed operation
