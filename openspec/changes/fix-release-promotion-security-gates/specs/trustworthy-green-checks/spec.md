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
Every exact package pin SHALL include at least one syntactically valid SHA-256
artifact hash so the trust decision cannot accept an unhashed graph.

#### Scenario: Only a Code Review dependency file changes

- **WHEN** a commit stages `requirements/code-review/requirements.in` or `requirements/code-review/locked.txt`
- **THEN** the dependency-trust gate is selected
- **AND** it rejects stale input binding or a policy-blocked package present only in the Code Review lock

#### Scenario: A Code Review pin omits a valid artifact hash

- **WHEN** an exact package pin has no SHA-256 continuation or only a malformed digest
- **THEN** the pre-install dependency-trust gate rejects the isolated lock

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

### Requirement: Retained proof binds only active pytest plugin declarations

Static proof-input discovery SHALL treat import-time module bindings of
`pytest_plugins` as active pytest plugin declarations. Literal annotated
assignments SHALL be included, and active declarations that cannot be resolved
statically SHALL invalidate retained proof rather than silently omitting a
proof input. Function bodies, ordinary class-local bindings, and Python 3
comprehension iteration targets SHALL remain excluded because they do not bind
the surrounding module global. A class body that explicitly mutates the module
namespace through `globals()`, a `global pytest_plugins` declaration, or dynamic
execution SHALL fail closed because class bodies execute at import time.
Aliases derived from the active module namespace or from its namespace factory
SHALL receive the same treatment as direct access. Read-only class-body access
to unrelated module globals SHALL remain compatible.

#### Scenario: Helper function contains an inactive local assignment

- **WHEN** a test-support module assigns `pytest_plugins` only inside a function
- **THEN** those plugin modules are not added to retained proof inputs

#### Scenario: Module control flow conditionally assigns plugins

- **WHEN** a module-scope `if`, `try`, `with`, loop, or match branch assigns `pytest_plugins`
- **THEN** those plugin modules are included in retained proof inputs

#### Scenario: Active plugin declaration is annotated or computed

- **WHEN** module scope uses a literal annotated `pytest_plugins` assignment
- **THEN** those plugin modules are included in retained proof inputs
- **AND** a non-literal, import-bound, pattern-captured, or direct module-namespace assignment fails closed as invalid retained proof

#### Scenario: Definition expression binds the module global

- **WHEN** a function default, decorator, annotation, class base, or class keyword evaluated at import time binds `pytest_plugins`
- **THEN** retained proof fails closed instead of treating the nested definition as an inactive body

#### Scenario: Class body mutates the module namespace

- **WHEN** an import-time class body writes through `globals()`, declares `global pytest_plugins`, or invokes dynamic execution
- **THEN** retained proof fails closed instead of treating the operation as an ordinary class-local binding

#### Scenario: Namespace alias mutates the plugin binding

- **WHEN** module or class import-time code aliases the active namespace or its factory and the alias can write `pytest_plugins`
- **THEN** retained proof fails closed with the same result as a direct namespace mutation

#### Scenario: Class body reads unrelated module metadata

- **WHEN** an import-time class body only reads an unrelated key through `globals()`, its subscript form, or read-only `getattr`
- **THEN** retained proof remains valid because no module binding can be created

#### Scenario: Class body stores a deferred generator

- **WHEN** a class attribute stores an unconsumed generator whose deferred body references `globals()`
- **THEN** the deferred body is excluded while the generator's immediately evaluated outer iterable remains checked

#### Scenario: Comprehension target is local

- **WHEN** a list, set, dictionary, or generator comprehension uses `pytest_plugins` only as its iteration target
- **THEN** the target is ignored because Python 3 comprehension scope does not create the module global
