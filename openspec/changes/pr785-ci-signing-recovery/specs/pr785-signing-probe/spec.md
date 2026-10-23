## ADDED Requirements

### Requirement: Existing normal validation triggers are removed

The executor SHALL run only a manually dispatched probe or prefix7 stage on the fixed auxiliary branch for djm81 and the root-reviewed executor SHA, with job-only contents write, actions read and pull requests read. It SHALL reject other stages or contexts before writes. The stage defaults to probe. Both operations SHALL require their matching validated context before any request.

#### Scenario: Existing normal validation triggers are removed

- **WHEN** the auxiliary workflow is inspected
- **THEN** only workflow_dispatch and one isolated probe job exist, with immutable action pins and no module, environment or deployment access

### Requirement: Context mismatch

The executor SHALL run only a manually dispatched probe or prefix7 stage on the fixed auxiliary branch for djm81 and the root-reviewed executor SHA, with job-only contents write, actions read and pull requests read. It SHALL reject other stages or contexts before writes. The stage defaults to probe. Both operations SHALL require their matching validated context before any request.

#### Scenario: Context mismatch

- **WHEN** an actor, repository, event, ref, workflow, executor SHA, run or attempt differs
- **THEN** the probe refuses before creating any object

### Requirement: Ref or source drift

The probe operation SHALL create only a baseline commit and an inert workflow commit, each parented by fixed main. It SHALL pin the exact full source manifest and probe bytes/tree and permit only the two bounded commit POSTs without custom attribution, date or signature.

The owner SHALL prepare the exact unreferenced inert tree separately. Before either commit, CI SHALL read only the pinned root, linked `.github`, and linked `workflows` tree through three bounded nonrecursive GET requests. Each response SHALL have the exact expected SHA, explicit `truncated` equal to boolean false, and a list of unique, correctly typed direct entries. The required child entries SHALL match the pinned tree identities and tree mode. The inert workflow SHALL be a `100644` blob with its Git hash derived from the exact manifest bytes. Missing, unavailable, malformed, truncated or mismatched data SHALL refuse before any commit. CI SHALL NOT create trees or mutate refs. No caller input SHALL select a prepared SHA, manifest digest, success flag, path, content, ref or API endpoint.

#### Scenario: Ref or source drift

- **WHEN** main, PR head, open state, base, auto-merge state or immutable manifest differs before or after a write
- **THEN** the probe refuses and performs no subsequent write

### Requirement: Signature and identity verification

The probe operation SHALL create only a baseline commit and an inert workflow commit, each parented by fixed main. It SHALL pin the exact full source manifest and probe bytes/tree and permit only the two bounded commit POSTs without custom attribution, date or signature.

The executor SHALL require author name `github-actions[bot]`, email `41898282+github-actions[bot]@users.noreply.github.com`, service login `github-actions[bot]`, numeric ID `41898282` and type `Bot`. It SHALL require committer name `GitHub`, email `noreply@github.com`, service login `web-flow`, numeric ID `19864447` and type `User`. Both create and independent Git readback metadata and signed payload headers SHALL match their exact role names and emails. The separate commit attribution readback SHALL match each role login, ID and type. A value from the other role SHALL NOT satisfy any identity field. All signature, context, intent, request and refusal guards remain required.

#### Scenario: Signature and identity verification

- **WHEN** a commit is created and independently reread
- **THEN** its SHA, tree, sole parent, message, valid signature/payload and exact separate author and committer identities match the probe intent

### Requirement: Signing refusal

The probe operation SHALL create only a baseline commit and an inert workflow commit, each parented by fixed main. It SHALL pin the exact full source manifest and probe bytes/tree and permit only the two bounded commit POSTs without custom attribution, date or signature.

The CLI SHALL write the already sanitized, program-authored `ProbeRefusalError` reason to stderr on refusal. HTTP refusals SHALL expose only the sanitized status diagnostic, never the HTTP error body, reason phrase, credentials or chained traceback. A caught local `OSError` SHALL produce only the fixed stderr message `Probe refused: Local I/O failure`, without interpolating the exception. These diagnostics SHALL NOT add receipt fields or alter refusal, persistence, signature, identity, context, ref or transport guards.

#### Scenario: Signing refusal

- **WHEN** the API returns unsigned, invalid, misattributed or mismatched data, a policy check refuses, or a caught local I/O operation fails
- **THEN** the receipt records refusal and available raw JSON without token or error-body disclosure and no fallback or ref mutation occurs; stderr contains the safe policy reason or the fixed generic local I/O diagnostic without secrets, error bodies or traceback disclosure

### Requirement: Root acceptance remains pending

The executor SHALL persist receipts bound to the run ID, attempt, executor SHA and pinned manifest digest. It SHALL retain each successful raw API JSON response in order on success and failure, excluding credentials and API error bodies. It SHALL make no root-anchor or CI-anchor success claim. Context verification SHALL be explicit, including for an early refusal before the live run can be authenticated.

#### Scenario: Root acceptance remains pending

- **WHEN** both signed objects pass local verification
- **THEN** the persisted receipt reports both signed objects, exact verified execution identities, and pending root authentication and anchoring, with all successful raw API responses retained

### Requirement: Later refusal preserves earlier successful responses

The executor SHALL persist receipts bound to the run ID, attempt, executor SHA and pinned manifest digest. It SHALL retain each successful raw API JSON response in order on success and failure, excluding credentials and API error bodies. It SHALL make no root-anchor or CI-anchor success claim. Context verification SHALL be explicit, including for an early refusal before the live run can be authenticated.

#### Scenario: Later refusal preserves earlier successful responses

- **WHEN** one signed probe object is verified and the second commit request is refused
- **THEN** a refusal receipt retains the exact execution identities and verified first object, all successful raw JSON remains available, and credentials and error bodies are absent

### Requirement: Early context refusal remains unauthenticated

The executor SHALL persist receipts bound to the run ID, attempt, executor SHA and pinned manifest digest. It SHALL retain each successful raw API JSON response in order on success and failure, excluding credentials and API error bodies. It SHALL make no root-anchor or CI-anchor success claim. Context verification SHALL be explicit, including for an early refusal before the live run can be authenticated.

#### Scenario: Early context refusal remains unauthenticated

- **WHEN** the observed context has an unapproved actor before API access
- **THEN** a refusal receipt retains the observed run, attempt and executor with the pinned manifest digest, marks context verification false, contains no signed object and makes no anchoring claim

## Prefix7 extension

The existing eight requirements also govern Prefix7. Probe retains its exact receipt keys, two objects, messages, fixed-main parents and success-only return contract. Prefix7 SHALL use a separate stage=prefix7 journal with status refused until all seven steps verify, then prefix7_verified. The journal SHALL retain current context, manifest digest, accepted probe witness and its verified fact, sources_verified, and only fully verified steps. Newly generated CI and root anchor facts SHALL remain false.

The `accepted_probe` object SHALL have exactly `executor` (string), `run` (integer), `attempt` (integer), `artifact` (integer), `zip_sha256` (string) and `objects` (ordered list). Booleans SHALL NOT satisfy integer fields. The list SHALL contain exactly two records in baseline then inert-workflow order, each with exactly string `label`, `sha`, `tree` and `ref` fields. Baseline tree SHALL be `4c9ba46b2ace65cd8df0fcd5a77c2b14a42f599c`; inert-workflow tree SHALL be `4b2cf05809c1cf687e4eae17a770cd33c97eff72`. Each record SHALL associate its exact label, accepted SHA, tree and full `refs/heads/codex/pr785-signing-recovery/<manifest>/probe-<label>` ref. This complete fixed historical witness SHALL remain present even when `accepted_probe_verified` is false.

After local validation, Prefix7 SHALL authenticate the current live run, then the accepted probe, then all seven sources, in that order. The boolean facts `context_verified`, `accepted_probe_verified` and `sources_verified` SHALL become true only after their complete boundary succeeds. Current-run refusal SHALL retain false/false/false; accepted-probe refusal true/false/false; source refusal true/true/false; subsequent guard, write, readback, attribution or raw-response persistence refusal true/true/true. Every persisted refusal SHALL retain exact observed context, pinned manifest digest, only preceding fully verified steps and false new anchor facts. Invalid environment before authentication SHALL produce the distinct Prefix7 refusal journal with false/false/false, zero steps and zero API calls. Failed final storage SHALL NOT imply a persisted refusal journal.

Before writes, the manifest loader SHALL validate all ten records, unique identities, exact original single-parent continuity from fixed main, final old head/tree and seventh old RED head/tree. Prefix7 SHALL freshly read exactly the first seven source commits and require exact SHA, tree, sole original parent and subject. All seven source GETs SHALL precede every POST. No live production source read or signing operation for ordinals eight through ten is authorized.

Prefix7 SHALL reverify the fixed accepted probe witness. Run 39936325185, attempt 1, executor 88dc8c40c7a1e852c539d0668238b94da5ca32b2, artifact 12494410796 and ZIP SHA-256 7fc151d4549bc6c47e09764106339b8cb52e227cfcc9848ee65373b34f36bb51 bind baseline db02837c1922eaa191e10238606ac83571c4f228 and inert-workflow 837a9d68fe62bb13e9b272f0c6f11634894ae0fb. Each exact heads/codex/pr785-signing-recovery/<manifest>/probe-<label> ref SHALL identify the expected commit. Both objects SHALL match their original Probe intent, trees, signatures and separate service roles. Historical artifact and fetch authentication is retained root provenance, not a fresh CI claim.

Exactly seven POST git/commits calls SHALL contain only message, tree and one parent. Each tree equals the corresponding reviewed source tree. Parent one equals fixed main; each later parent equals the last newly verified signed SHA. Every intent SHALL contain the reviewed subject and Stage, Source, Ordinal, Manifest, actual Executor, Run and Attempt. Every step SHALL serialize ordinal, source_sha, source_tree, source_parent, subject and the verified signed object fields. Original source, auxiliary executor, fixed main, accepted probe and reused new identities SHALL be refused. The seventh tree SHALL equal the old RED tree. No eighth POST, arbitrary range or input-supplied evidence or success claim is permitted.

Both operations SHALL guard refs before each write and after success, denial, uncertain transport or raw-response persistence failure. A failed postguard SHALL NOT replace an earlier sanitized operation failure. A refused write or verification SHALL stop subsequent writes and retain only preceding complete mappings. Lost responses may leave an unaccepted object; no retry, rollback or partial adoption is implied.

The first Prefix7 preguard SHALL freshly check main and PR after the seventh source read and before the first POST. Main or PR drift introduced after that read SHALL refuse with all seven source reads complete and zero POSTs, even when an earlier startup guard passed.

Final evidence serialization TypeError or ValueError SHALL produce fixed Evidence serialization failed stderr and exit 1. Final receipt creation/write OSError SHALL produce fixed Local I/O failure stderr and exit 1. Arbitrary exception text SHALL remain absent. Missing or incomplete receipts SHALL NOT be represented as persisted refusal or successful stage evidence. The CLI SHALL NOT overwrite or retry partial evidence.

The workflow SHALL retain default probe and add only prefix7 to its choices. Its artifact name SHALL be pr785-${{ inputs.stage }}-${{ github.run_id }}-${{ github.run_attempt }}-${{ github.sha }}. Existing pins, permissions, bootstrap, fixed output path and one job remain unchanged. Advisory9, final10, empty and injected stage inputs remain refused. Actual Prefix7 CI authentication, immutable root anchors, fetching and genuine native 33-case RED remain root-owned gates before production signing.
