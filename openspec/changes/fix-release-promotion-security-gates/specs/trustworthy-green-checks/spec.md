## ADDED Requirements

### Requirement: Privileged companion-module execution does not persist dependency caches

Default-branch jobs that can execute code from a companion-module fixture SHALL NOT restore or save a persistent dependency cache that the fixture can modify. Immutable repository, commit, and tree verification SHALL remain mandatory before fixture execution.

#### Scenario: Approved fixture executes in a default-branch job

- **WHEN** a scheduled, pull-request, protected-branch, or release job verifies and then executes the approved companion-module fixture
- **THEN** the job neither restores nor saves a persistent dependency cache across workflow runs
- **AND** the fixture remains bound to the committed full SHA and expected tree before execution

#### Scenario: Pull-request fixture attempts to influence a later trusted run

- **WHEN** companion-module code executes during pull-request validation
- **THEN** no cache written by that execution can be restored by a later protected-branch or release job

#### Scenario: Manual compatibility dispatch selects an unprotected ref

- **WHEN** an actor attempts to manually dispatch the PR Orchestrator against a selected branch revision
- **THEN** the workflow has no manual-dispatch trigger
- **AND** the schedule-only compatibility job verifies both the fixture commit and tree before exporting its module path

#### Scenario: Requirements evidence executes module-owned code before Code Review setup

- **WHEN** the Requirements workflow runs verified module-owned evidence code and then prepares Code Review tools
- **THEN** the later Node setup does not register a persistent npm cache restore or save hook

### Requirement: Dependency review exceptions remain bound to their declared environment

The license gate SHALL accept an environment-scoped exception only while
scanning the environment named by that exception. A Code Review-only exception
SHALL be rejected by the primary installed-environment scan and by module
manifest scans.

#### Scenario: Pylint metadata appears in the primary environment

- **WHEN** the primary environment reports the Pylint GPL metadata that is reviewed only for the isolated Code Review environment
- **THEN** the license gate reports a violation
- **AND** the Code Review-only exception does not suppress it

#### Scenario: Pylint metadata appears in the frozen Code Review environment

- **WHEN** the separately hash-locked Code Review interpreter is scanned
- **THEN** the exact reviewed Pylint version and license metadata may use the Code Review-only exception

### Requirement: Local dependency trust reacts to every frozen review input

The dependency-trust pre-commit gate SHALL run when either the Code Review
input requirements or its frozen lock changes. It SHALL bind the lock to the
exact input and apply the blocked-release, prohibited-package, and reviewed
security-floor policy to the isolated graph before its tools are installed.
Every exact package pin SHALL continue to and include at least one syntactically
valid SHA-256 artifact hash on the same logical requirement so the trust
decision cannot accept an unhashed graph or credit a detached digest.

#### Scenario: Only a Code Review dependency file changes

- **WHEN** a commit stages `requirements/code-review/requirements.in` or `requirements/code-review/locked.txt`
- **THEN** the dependency-trust gate is selected
- **AND** it rejects stale input binding or a policy-blocked package present only in the Code Review lock

#### Scenario: A Code Review pin omits a valid artifact hash

- **WHEN** an exact package pin has no SHA-256 continuation or only a malformed digest
- **THEN** the pre-install dependency-trust gate rejects the isolated lock

#### Scenario: A valid digest is detached from its package pin

- **WHEN** an uncontinued exact pin is followed by a standalone valid SHA-256 hash line
- **THEN** the pre-install dependency-trust gate rejects both the unhashed pin and the unattached digest

#### Scenario: A continued pin is interrupted before its digest

- **WHEN** a blank or comment-only physical line separates a continued exact pin from a valid SHA-256 hash line
- **THEN** the pre-install dependency-trust gate follows pip logical-line semantics and rejects both the unhashed pin and the unattached digest

### Requirement: Frozen static analysis uses a non-vulnerable MCP binding

The frozen development-tool graph SHALL select a Semgrep release whose declared
MCP dependency is at or above every reviewed advisory fix floor. Once such a
compatible release exists, the repository SHALL NOT retain an exception for the
older vulnerable MCP binding.

#### Scenario: Upstream Semgrep permits the fixed MCP line

- **WHEN** Semgrep 1.175.0 declares `mcp==1.29.0`
- **THEN** every repository-owned Semgrep constraint selects Semgrep 1.175.0 or newer
- **AND** the frozen lock and hash-protected export select `mcp==1.29.0`
- **AND** the pre-install frozen-lock policy rejects MCP releases below `1.28.1`
- **AND** the vulnerability exception register contains no MCP exception
- **AND** Semgrep remains development/scanning tooling rather than a core runtime dependency

### Requirement: Active OpenSpec authoring is not mistaken for archival deletion

The staged active-change deletion guard and branch-diff Requirements selector
SHALL require a complete native archive move only when an active change leaves
the active namespace entirely. Every base file SHALL have a byte-identical,
regular-file destination at the same relative path in one dated archive, and
the archive SHALL contain no additional files. A fabricated, rewritten,
partial, or split archive SHALL leave the change governed, and non-planned work
without one uniquely selected active change SHALL fail rather than fall back to
unrelated review evidence. The guards SHALL permit a file removal or rename
while other files for the same active change remain in the staged or committed
tree.

#### Scenario: Author removes one obsolete active-change file

- **WHEN** one file is deleted and other tracked files remain under the same active change
- **THEN** the archive-deletion guard passes

#### Scenario: Author renames a file within the same active change

- **WHEN** the staged rename destination remains under the same active change
- **THEN** the archive-deletion guard passes

### Requirement: Stateful staged-index hooks execute once per commit

A pre-commit hook that discovers the staged index itself and can update that
index SHALL execute once per hook run rather than once per filename batch.

#### Scenario: Markdown auto-fix updates multiple staged files

- **WHEN** multiple Markdown files are staged for one commit
- **THEN** the Markdown auto-fix hook receives no filename batches from pre-commit
- **AND** one hook process discovers and safely updates the staged Markdown set
- **AND** concurrent hook processes cannot contend for the Git index lock

### Requirement: Retained red proof denies same-process post-red mutation

Retained red proof SHALL inspect the path changes made by every commit from the
red source through the final source, rather than attempting to interpret the
runtime behavior of selected Python. Every repository path touched anywhere in
that history SHALL make the retained proof stale unless it is an exact evidence
producer authenticated by the existing external producer authority.
The history SHALL include both endpoints of renames and copies and paths changed
and later restored. Any `mutable_after_red: true` mapping value SHALL fail closed
with `prior-red-proof-invalid` while execution uses stock pytest, because tests,
conftests, fixtures, plugins, and imported SUT share one interpreter. A future
runner MAY authorize mutation only after it places an immutable harness and the
mutable SUT in separate process and filesystem domains and exposes a bounded,
non-executable protocol.
The exact archive-regression Bash/Git protocol SHALL remain freshness-bound and
SHALL NOT create a general external-process exception. Because the provenance
producer is one of the four frozen anchors, replacement validator bytes after
the authenticated red source SHALL require a live, unedited, expiring MEMBER
authority that binds the exact approved commit and tree, external-amendment
digest, and Git blob identity of every changed evidence producer path. A
descendant may reuse that authority only while the approved commit remains its
ancestor and the complete changed producer-path set and every approved blob
remain identical. This exception SHALL NOT create a fifth anchor or authorize
any selected test, mapped `test_file`, non-producer configuration, application
SUT, or unlisted producer path.

Eligible producer paths SHALL be limited to these exact regular Git files:
`.github/workflows/pr-orchestrator.yml`,
`.github/workflows/requirements-evidence.yml`,
`scripts/check_doc_frontmatter.py`, `scripts/check_license_compliance.py`,
`scripts/license_scope_policy.py`, `scripts/requirements_amendment_bootstrap.py`,
`scripts/requirements_bootstrap_authority.py`,
`scripts/requirements_cycle_base.py`,
`scripts/requirements_evidence_delivery_gate.py`,
`scripts/requirements_proof_executor.py`,
`scripts/requirements_proof_provenance.py`,
`scripts/requirements_proof_pytest_plugin.py`, and
`scripts/requirements_red_run_normalizer.py`. Each SHALL have Git mode `100644`
or `100755` at both the approved and final commit. A symlink, gitlink, tree,
unknown `scripts/requirements_*` path, or any other path SHALL fail closed.
Selector and mapped `test_file` locators SHALL use their canonical repository
path spelling; aliases such as a leading `./` SHALL fail closed before producer
collision comparison.

#### Scenario: Same-process mutable SUT authority fails closed

- **GIVEN** an owner-approved mapping marks an existing exact regular-file SUT touchpoint `mutable_after_red: true`
- **WHEN** retained proof uses the stock pytest execution model
- **THEN** validation fails with `prior-red-proof-invalid` before granting path authority

#### Scenario: A path is restored or moved after red

- **GIVEN** a red-to-final history changes a path and later restores its red bytes, or renames or copies a path
- **WHEN** retained proof evaluates the complete commit history
- **THEN** the original path and every rename or copy endpoint remain touched
- **AND** retained proof fails with `stale-red-proof`

#### Scenario: Proof authority and test inputs remain frozen

- **GIVEN** any repository test, support input, non-authorized configuration, plugin, SUT, proof producer, lockfile, or package initializer
- **WHEN** that path is added, removed, renamed, copied, or changed after red
- **THEN** retained proof fails with `stale-red-proof`, or `prior-red-proof-invalid` if a mapping attempts to mark it mutable, unless the path is an exact evidence producer covered by the final-producer authority

#### Scenario: Exact final producer bytes receive external authority

- **GIVEN** the fixed external amendment capability and a later candidate that changes its evidence producer
- **WHEN** one live, unedited, unexpired repository MEMBER comment binds the exact approved commit and tree, external capability digest, and complete changed producer-path blob map
- **THEN** only those exact producer bytes may cross the retained-red boundary
- **AND** a missing, edited, expired, mismatched, additional, or subsequently modified producer path fails closed
- **AND** a non-regular producer mode or path outside the finite producer set fails closed

#### Scenario: Any mutable mapping authority fails closed

- **GIVEN** any mapping touchpoint declares `mutable_after_red: true`
- **WHEN** retained proof evaluates mutable SUT authority
- **THEN** the mapping is rejected without authorizing any path

#### Scenario: Unmapped production path changes after red

- **GIVEN** a path is not an eligible exact `mutable_after_red: true` SUT touchpoint
- **WHEN** any red-to-final commit touches that path
- **THEN** retained proof fails with `stale-red-proof`

### Requirement: Mapped proof execution is isolated from trusted evidence production

The blocking Requirements workflow SHALL execute mapped pytest selectors and
all of their descendants in a transient Linux service under a separate
unprivileged identity, mount namespace, and dedicated control group. The
checkout, selected tests and plugin, proof plan and producers, frozen module
fixture, canonical evidence destinations, and later verifier inputs SHALL NOT
be writable by that service; repository Git metadata, runner credentials, and
unrelated runner-home content SHALL be inaccessible. The service SHALL have no
network access, privilege-gain path, ambient capability, or persistent writable
state. It MAY write only to a private temporary filesystem and one fresh raw
JUnit handoff directory.

The trusted runner process SHALL wait until the transient service is inactive
and its complete control group has been terminated before reading the handoff.
Only then SHALL it parse the bounded raw JUnit as untrusted input, canonicalize
the exact planned selectors and identities, and publish canonical JUnit to a
runner-owned destination. Proof stdout and stderr SHALL NOT be replayed as
unframed GitHub workflow commands. The blocking workflow MAY satisfy this
property by routing both streams to null
inside the transient service and using canonical JUnit as the only proof-data
handoff. Blocking proof SHALL fail closed when any required isolation, output
suppression, or teardown property cannot be established. A direct local
command-runner test seam SHALL NOT satisfy the blocking workflow boundary.

#### Scenario: Detached proof descendant targets trusted inputs

- **GIVEN** a mapped test or SUT starts a detached descendant that outlives the pytest main process
- **WHEN** that descendant attempts to modify the plan, checkout, proof producer, module fixture, Git metadata, canonical JUnit, or later artifact input
- **THEN** the write is denied by the separate identity and mount boundary
- **AND** the entire service control group is terminated before the trusted runner reads raw JUnit
- **AND** no descendant can survive to modify later reconciliation, review, or upload inputs

#### Scenario: Proof output resembles a workflow command

- **GIVEN** a mapped test writes GitHub workflow-command syntax to stdout or stderr
- **WHEN** the transient proof service executes that test
- **THEN** the service routes both streams to null rather than the workflow command parser
- **AND** proof bytes cannot set outputs, environment, masks, annotations, or command-processing state

#### Scenario: Legitimate mapped tests use isolated scratch behavior

- **GIVEN** an approved mapped test creates temporary files or an isolated Git repository and invokes installed Bash or Git directly
- **WHEN** the blocking Requirements workflow executes that selector
- **THEN** the test can read the frozen checkout and module fixture and write within its private temporary filesystem
- **AND** the proof service still has no network, credential, persistent-cache, checkout-write, or canonical-artifact-write access

#### Scenario: Isolation backend is unavailable

- **WHEN** the hosted Linux runner cannot establish every required identity, mount, network, capability, runtime, and control-group property
- **THEN** mapped proof execution fails before canonical evidence is published
- **AND** the workflow does not fall back to same-identity pytest execution

### Requirement: Repository path operands cannot become command options

Repository file paths passed to command-line discovery tools SHALL be separated
from tool options so an attacker-controlled filename cannot select another
option or preprocessor.

#### Scenario: Document ownership scan receives repository paths

- **WHEN** the document ownership helper invokes ripgrep for a batch of repository files
- **THEN** the command terminates option parsing before the first file operand

### Requirement: Requirements proof supports verified pull-request amendment cycles

The Requirements workflow SHALL allow a pull request targeting `dev` or `main`
to start another test-first behavior cycle after an earlier head passed verified
Requirements evidence. The workflow SHALL select only a successful, completed
Requirements run for the same repository, pull request, and head branch whose
head is a strict ancestor of the current head. The selected run SHALL bind a
passing verified artifact whose final execution source is that ancestor. The
workflow SHALL derive red-versus-final maturity from changes after that verified
cycle base while continuing to plan the complete active OpenSpec change against
the pull-request base. If no eligible verified cycle base exists, the
pull-request base SHALL remain the cycle base. Each amendment cycle SHALL be a
linear, merge-free chain from the authenticated cycle base through the red
source to the final head; a side-branch red commit merged after independently
authored production SHALL NOT establish test-first order.

#### Scenario: A review finding starts another red-to-green cycle

- **WHEN** a non-default-branch pull request has a verified green head and a later commit adds only specification and test evidence for a review finding
- **THEN** the later commit is eligible to retain red proof relative to the verified green head without creating another pull request
- **AND** a following implementation commit can reconcile that proof on the same pull request
- **AND** both commits descend linearly from that verified green head

#### Scenario: An untrusted cycle base cannot hide production-before-red changes

- **WHEN** a candidate cycle base belongs to another pull request or branch, has not completed successfully, lacks a passing verified final artifact, is not a strict ancestor, or is supplied without matching GitHub run metadata
- **THEN** the candidate is rejected and cannot narrow the production-before-red history boundary
- **AND** a candidate that changed the Requirements workflow, installed SpecFact CLI package, project or frozen dependency inputs, pinned module fixture, or Requirements proof commands cannot authenticate its own green artifact
- **AND** production changes between the accepted cycle base and the red source still invalidate retained proof
- **AND** a merge that combines an independently authored production parent with a red-proof parent is rejected

#### Scenario: Red history is bound to one authenticated OpenSpec change

- **WHEN** an amendment red segment contains declarative OpenSpec artifacts beside its test evidence
- **THEN** the workflow preselects exactly one syntactically valid active change ID and passes it into every bootstrap, cycle-base, and provenance validator
- **AND** only test paths and the declared artifact allowlist below that exact `openspec/changes/<change-id>/` directory are eligible for the red segment
- **AND** a missing, malformed, mismatched, ambiguous, or additional change directory is rejected as production-before-red
- **AND** the exact external PR `#698` capability remains bound to its existing immutable change ID

#### Scenario: Exact external amendment authority permits one stale-producer boundary

- **WHEN** an unedited repository MEMBER comment at the configured immutable locator is unexpired and binds the exact repository, issue, pull request, branch, green commit and tree, red commit and tree, workflow runs, artifacts, content digests, mapping, plan, selectors, and expected outcomes for pull request `#698`
- **AND** both bound producer reports fail only with the exact `Red proof provenance rejected: stale-red-proof` diagnostic after the evidence producer changed
- **AND** each bound plan is validated independently, the green raw JUnit has every green-plan selector passing, and the red raw JUnit has only the exact approved failures with all remaining red-plan selectors passing
- **THEN** the workflow may use that exact raw green/red boundary even though its producer is self-authored and did not emit a verified-final successful report
- **AND** the capability replaces only those stale producer-authorship and producer-verdict predicates with the exact bound raw plan and JUnit outcomes
- **AND** live comment, expiry, run, artifact, digest, ancestry, linear-history, raw plan and JUnit integrity, and test-only red-prefix checks remain mandatory before binding and before reuse
- **AND** an edited, expired, mismatched, raw, or differently located authority remains rejected

#### Scenario: Externally authorized green starts a later ordinary amendment cycle

- **WHEN** the exact externally authorized cycle reaches a successful verified green head and a later review fix begins with specification and tests only
- **THEN** the later cycle may use that verified green head as its ordinary cycle base on the same pull request
- **AND** the green artifact must bind the same live-revalidated external authority receipt, including its approved root green/red commits, trees, runs, artifacts, and digests, before only the self-authored producer predicate is bypassed
- **AND** the later red-to-final ancestry, linear-history, test-only prefix, artifact, digest, and proof-freshness checks remain mandatory
- **AND** the ordinary cycle authority retains the external digest solely for live revalidation of that exact receipt and the candidate green run, artifact, tree, and execution-proof chain
- **AND** ordinary authority reuse re-fetches the unedited comment and exact
  external run/artifact inputs and rechecks expiry before trusting that digest
- **AND** a candidate artifact that merely copies the public external digest without the exact live receipt and approved proof chain is rejected
- **AND** probing unrelated failed runs cannot overwrite the fixed external bootstrap proof used by the final fallback
- **AND** any evidence-producer change after the approved red source requires the exact live final-producer authority described above
