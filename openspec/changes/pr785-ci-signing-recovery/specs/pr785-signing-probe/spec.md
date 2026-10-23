## ADDED Requirements

### Requirement: Existing normal validation triggers are removed

The executor SHALL run only a manually dispatched probe on the fixed auxiliary branch for djm81 and the root-reviewed executor SHA, with job-only contents write, actions read and pull requests read. It SHALL reject other stages or contexts before writes.

#### Scenario: Existing normal validation triggers are removed

- **WHEN** the auxiliary workflow is inspected
- **THEN** only workflow_dispatch and one isolated probe job exist, with immutable action pins and no module, environment or deployment access

### Requirement: Context mismatch

The executor SHALL run only a manually dispatched probe on the fixed auxiliary branch for djm81 and the root-reviewed executor SHA, with job-only contents write, actions read and pull requests read. It SHALL reject other stages or contexts before writes.

#### Scenario: Context mismatch

- **WHEN** an actor, repository, event, ref, workflow, executor SHA, run or attempt differs
- **THEN** the probe refuses before creating any object

### Requirement: Ref or source drift

The executor SHALL create only a baseline commit and an inert workflow commit, each parented by fixed main. It SHALL pin the exact full source manifest and probe bytes/tree and permit only bounded tree and commit POSTs without custom attribution, date or signature.

#### Scenario: Ref or source drift

- **WHEN** main, PR head, open state, base, auto-merge state or immutable manifest differs before or after a write
- **THEN** the probe refuses and performs no subsequent write

### Requirement: Signature and identity verification

The executor SHALL create only a baseline commit and an inert workflow commit, each parented by fixed main. It SHALL pin the exact full source manifest and probe bytes/tree and permit only bounded tree and commit POSTs without custom attribution, date or signature.

The executor SHALL require author name `github-actions[bot]`, email `41898282+github-actions[bot]@users.noreply.github.com`, service login `github-actions[bot]`, numeric ID `41898282` and type `Bot`. It SHALL require committer name `GitHub`, email `noreply@github.com`, service login `web-flow`, numeric ID `19864447` and type `User`. Both create and independent Git readback metadata and signed payload headers SHALL match their exact role names and emails. The separate commit attribution readback SHALL match each role login, ID and type. A value from the other role SHALL NOT satisfy any identity field. All signature, context, intent, request and refusal guards remain required.

#### Scenario: Signature and identity verification

- **WHEN** a commit is created and independently reread
- **THEN** its SHA, tree, sole parent, message, valid signature/payload and exact separate author and committer identities match the probe intent

### Requirement: Signing refusal

The executor SHALL create only a baseline commit and an inert workflow commit, each parented by fixed main. It SHALL pin the exact full source manifest and probe bytes/tree and permit only bounded tree and commit POSTs without custom attribution, date or signature.

#### Scenario: Signing refusal

- **WHEN** the API returns unsigned, invalid, misattributed or mismatched data
- **THEN** the receipt records refusal and available raw JSON without token or error-body disclosure and no fallback or ref mutation occurs

### Requirement: Root acceptance remains pending

The executor SHALL persist receipts bound to the run ID, attempt, executor SHA and pinned manifest digest. It SHALL retain each successful raw API JSON response in order on success and failure, excluding credentials and API error bodies. It SHALL make no root-anchor or CI-anchor success claim. Context verification SHALL be explicit, including for an early refusal before the live run can be authenticated.

#### Scenario: Root acceptance remains pending

- **WHEN** both signed objects pass local verification
- **THEN** the persisted receipt reports both signed objects, exact verified execution identities, and pending root authentication and anchoring, with all successful raw API responses retained

### Requirement: Later refusal preserves earlier successful responses

The executor SHALL persist receipts bound to the run ID, attempt, executor SHA and pinned manifest digest. It SHALL retain each successful raw API JSON response in order on success and failure, excluding credentials and API error bodies. It SHALL make no root-anchor or CI-anchor success claim. Context verification SHALL be explicit, including for an early refusal before the live run can be authenticated.

#### Scenario: Later refusal preserves earlier successful responses

- **WHEN** one signed probe object is verified and a subsequent tree request is refused
- **THEN** a refusal receipt retains the exact execution identities and verified first object, all successful raw JSON remains available, and credentials and error bodies are absent

### Requirement: Early context refusal remains unauthenticated

The executor SHALL persist receipts bound to the run ID, attempt, executor SHA and pinned manifest digest. It SHALL retain each successful raw API JSON response in order on success and failure, excluding credentials and API error bodies. It SHALL make no root-anchor or CI-anchor success claim. Context verification SHALL be explicit, including for an early refusal before the live run can be authenticated.

#### Scenario: Early context refusal remains unauthenticated

- **WHEN** the observed context has an unapproved actor before API access
- **THEN** a refusal receipt retains the observed run, attempt and executor with the pinned manifest digest, marks context verification false, contains no signed object and makes no anchoring claim
