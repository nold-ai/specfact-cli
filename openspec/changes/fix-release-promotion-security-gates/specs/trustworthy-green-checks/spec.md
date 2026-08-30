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
Any module-scope attribute store or deletion targeting `pytest_plugins` SHALL
also fail closed unless the receiver is statically proven not to be the active
module; obtaining the active module through `importlib.import_module(__name__)`,
`__import__(__name__, ...)`, an alias, or a computed equivalent SHALL not bypass
that boundary.
Aliases derived from the active module namespace or from its namespace factory
SHALL receive the same treatment as direct access, including aliases introduced
by fixed or starred destructuring, loops, eager comprehensions, context-manager
bindings, match captures, nested authority-bearing containers, and bound
namespace-mutator methods. Mapping-pattern captures SHALL retain their
statically corresponding subject values and fail closed when an opaque subject
can contain the active namespace. Qualified or aliased access to the built-in
dynamic executors, including chained aliases and `getattr` access through an
imported `builtins` expression, aliases of `__import__`, and executor lookup
through the imported module mapping, SHALL receive the same treatment as a
direct `exec` or `eval` call. A generator expression whose outer iterable is
statically empty SHALL remain compatible because none of its deferred clauses
can execute. Definite later assignments SHALL replace earlier alias bindings in
statement order only when their replacement value is statically proven to carry
no namespace or dynamic-execution authority. Unresolved computed values and
conditional assignments SHALL remain fail-closed. Statically proven standard-
library owners with unrelated `exec` or `eval` methods, read-only class-body
access to unrelated module globals, and compound bindings over ordinary
mappings SHALL remain compatible.

#### Scenario: An augmented union mutates a module-namespace alias

- **WHEN** module scope or an import-time class body applies `|=` to an alias of the active module namespace with a mapping that can bind `pytest_plugins`
- **THEN** retained proof fails closed rather than omitting the dynamically registered plugin
- **AND** the same operation over an ordinary mapping or with statically unrelated keys remains compatible

#### Scenario: Indirect binding forms retain namespace and executor authority

- **WHEN** starred destructuring binds the active module namespace, a mapping pattern captures from an opaque namespace-bearing subject, or `getattr` selects an executor from `__import__("builtins")`
- **THEN** retained proof fails closed rather than omitting the dynamically registered plugin
- **AND** positionally ordinary starred targets, opaque subjects without namespace authority, and non-executor builtins attributes remain compatible

#### Scenario: Indirect authority remains active through containers and bound methods

- **WHEN** import-time code reaches the active namespace through a nested authority-bearing container or invokes a bound alias of `update`, `setdefault`, `__setitem__`, or `__ior__`
- **THEN** a call that can bind `pytest_plugins` invalidates retained proof
- **AND** ordinary mappings, uninvoked method aliases, and calls with statically unrelated keys remain compatible

#### Scenario: Statically empty generator defers namespace mutation forever

- **WHEN** module import creates a generator whose outer iterable is statically empty and whose deferred clauses could otherwise mutate the active namespace
- **THEN** retained proof remains valid because no deferred clause can execute
- **AND** mutation in the eagerly evaluated outer iterable still invalidates retained proof

#### Scenario: Helper function contains an inactive local assignment

- **WHEN** a test-support module assigns `pytest_plugins` only inside a function
- **THEN** those plugin modules are not added to retained proof inputs
- **AND** if module import directly invokes that local function or class and its body can bind the module plugin global, retained proof fails closed

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

- **WHEN** module or class import-time code aliases the active namespace, its `__dict__`, `vars(...)` mapping view, or its factory and the alias can write `pytest_plugins`
- **THEN** retained proof fails closed with the same result as a direct namespace mutation

#### Scenario: Compound binding aliases the module namespace

- **WHEN** an import-time destructuring assignment, loop, eager comprehension, context-manager binding, or match capture resolves a target to the active module namespace
- **AND** the scoped target can write `pytest_plugins`
- **THEN** retained proof fails closed without treating unrelated positional targets or later shadowing assignments as namespace aliases

#### Scenario: Qualified built-in executor mutates plugin state

- **WHEN** import-time code reaches `exec` or `eval` through `builtins`, an import alias, `getattr`, `__builtins__`, `__import__("builtins")`, an alias of `__import__`, or the imported module's mapping
- **THEN** retained proof fails closed with the same result as a bare dynamic-execution call

#### Scenario: Imported builtins module is re-aliased

- **WHEN** import-time code assigns the imported `builtins` module through one or more aliases
- **AND** the final alias invokes `exec` or `eval`
- **THEN** retained proof fails closed with the same result as direct `builtins.exec` or `builtins.eval`

#### Scenario: Mapping pattern captures the module namespace

- **WHEN** an import-time mapping pattern captures a subject value that is the active module namespace
- **AND** the captured name can write `pytest_plugins`
- **THEN** retained proof fails closed without treating a capture of an ordinary mapping value as the module namespace

#### Scenario: Definite assignment shadows an alias

- **WHEN** import-time code definitely replaces a namespace, builtins-module, or dynamic-executor alias before using that name
- **THEN** the replacement is evaluated in statement order and a statically proven ordinary replacement remains compatible
- **AND** mutation before the replacement, re-aliasing after it, an unresolved computed owner, or a merely conditional replacement remains fail-closed
- **AND** a statically proven standard-library owner with an unrelated `exec` or `eval` method remains compatible

#### Scenario: Class body reads unrelated module metadata

- **WHEN** an import-time class body only reads an unrelated key through `globals()`, its subscript form, or read-only `getattr`
- **THEN** retained proof remains valid because no module binding can be created

#### Scenario: Class body stores a deferred generator

- **WHEN** a class attribute stores an unconsumed generator whose deferred body references `globals()`
- **THEN** the deferred body is excluded while the generator's immediately evaluated outer iterable remains checked

#### Scenario: Comprehension target is local

- **WHEN** a list, set, dictionary, or generator comprehension uses `pytest_plugins` only as its iteration target
- **THEN** the target is ignored because Python 3 comprehension scope does not create the module global

#### Scenario: Module attribute hook can synthesize a plugin declaration

- **WHEN** an applicable pytest support module defines or assigns module-level `__getattr__` that can synthesize `pytest_plugins`
- **THEN** retained proof fails closed instead of treating the function body as an inactive local scope

#### Scenario: Custom module type can synthesize a plugin declaration

- **WHEN** an applicable pytest support module replaces its current module `__class__` with a custom type that can override attribute lookup
- **THEN** retained proof fails closed before the custom `__getattribute__` or descriptor path can synthesize `pytest_plugins`
- **AND** an unrelated object's class assignment remains compatible when it cannot change the executing support module

#### Scenario: Module registry replacement can substitute plugin declarations

- **WHEN** an applicable pytest support module mutates `sys.modules` during import
- **THEN** retained proof fails closed because the mutation can substitute the executing module or another executable proof input
- **AND** read-only access to `sys.modules` remains compatible

#### Scenario: Builtin attribute lookup can synthesize a plugin declaration

- **WHEN** an applicable pytest support module mutates `builtins.getattr` through an attribute or mapping view
- **THEN** retained proof fails closed before pytest can observe a hidden `pytest_plugins` value through the modified lookup function
- **AND** an unrelated builtins attribute assignment remains compatible

#### Scenario: A pytest hook loads a plugin imperatively

- **WHEN** an applicable pytest support module calls `config.pluginmanager.import_plugin` with a literal repository module
- **THEN** that module remains a frozen executable proof input
- **AND** retained proof fails closed when the plugin target cannot be resolved statically

#### Scenario: A higher-order callable performs a plugin namespace mutation

- **WHEN** an applicable pytest support module passes active-module namespace authority to an eagerly invoked higher-order setter or callable factory
- **THEN** retained proof fails closed instead of treating the higher-order call as unrelated
- **AND** a higher-order setter bound only to an unrelated object remains compatible

#### Scenario: A higher-order callable performs a repository import

- **WHEN** an applicable pytest support module passes import-loader authority to an eagerly invoked higher-order callable using a literal repository target
- **THEN** the imported repository module remains a frozen executable proof input
- **AND** retained proof fails closed when the wrapped import target cannot be resolved statically

#### Scenario: Pytest configuration changes after red proof

- **WHEN** a repository pytest configuration file is added, removed, renamed, or changed after the retained red source
- **THEN** retained proof is stale because pytest options can load plugins or otherwise change the selected-test harness

#### Scenario: Compact pytest plugin options retain plugin inputs

- **WHEN** red-time pytest configuration loads a repository plugin with `-pMODULE` or `-p=MODULE`
- **THEN** that plugin and its transitive imports remain retained proof inputs
- **AND** changing the plugin after red makes retained proof stale

#### Scenario: Current-module imports mutate the plugin binding

- **WHEN** module-scope code obtains the executing support module through `importlib.import_module(__name__)`, `__import__(__name__, ...)`, or an equivalent alias and writes its `pytest_plugins` attribute
- **THEN** retained proof fails closed instead of omitting the dynamically registered plugin
- **AND** an ordinary local or class attribute with that spelling remains compatible when it cannot bind the module global

#### Scenario: Ordinary object stores a similarly named attribute

- **WHEN** module-scope code assigns `pytest_plugins` on an instance of a provably inert local class or standard-library namespace
- **THEN** retained proof accepts the ordinary object attribute because it cannot bind the executing module global
- **AND** an unresolved object owner still fails closed

### Requirement: Retained proof binds the complete executable pytest harness

Retained red proof SHALL bind every repository-controlled input that can change
the selected pytest execution between the red source and final head. The bound
set SHALL include the core proof executor and explicit proof plugin, the frozen
dependency lock installed for proof execution, every selected test and
applicable conftest plus their parent package initializers, and every
repository-local module reached through static or resolvable dynamic imports.
An import-time dynamic loader target that cannot be resolved safely SHALL fail
closed instead of silently omitting a possible harness input. The proof
executor SHALL resolve installed pytest without allowing a repository-root
`pytest.py` or `pytest` package to shadow it.

#### Scenario: Core proof producer or frozen graph changes after red

- **WHEN** the proof executor, explicit proof plugin, or `uv.lock` changes after the retained red source
- **THEN** retained proof is stale because the final evidence producer or its frozen environment changed
- **AND** the explicit proof plugin's parent package initializers remain bound because Python executes them before loading the plugin

#### Scenario: Selected input executes through a package initializer

- **WHEN** a selected test or applicable conftest is imported through one or more repository packages
- **THEN** every candidate parent `__init__.py` remains a retained proof input
- **AND** adding, removing, renaming, or changing one after red makes retained proof stale

#### Scenario: Selected input dynamically imports a repository helper

- **WHEN** selected proof code uses a literal or statically resolvable `importlib.import_module`, `__import__`, or equivalent supported loader target
- **THEN** the repository module and its parent package initializers remain retained proof inputs
- **AND** an unresolved import-time target fails closed while a resolved external module remains compatible

#### Scenario: Dynamic loader is selected through a literal attribute lookup

- **WHEN** selected proof code calls or aliases `getattr(importlib, "import_module")` with a statically resolvable repository target
- **THEN** the target and its package initializers remain retained proof inputs
- **AND** a computed loader attribute or unresolved target fails closed
- **AND** literal `__call__`, nested `getattr`, `vars(importlib)`, and
  `importlib.__dict__` selections cannot hide the same loader
- **AND** aliases of those namespace mappings plus literal `get` and
  `__getitem__` selections cannot hide the same loader
- **AND** aliases and literal `__call__` wrappers of those mapping methods
  cannot hide the same loader
- **AND** a computed mapping selector or key fails closed

#### Scenario: Repository root contains a pytest shadow

- **WHEN** the proof executor starts installed pytest from a repository containing `pytest.py` or `pytest/__main__.py`
- **THEN** Python safe-path mode prevents the repository shadow from replacing installed pytest
- **AND** the existing exact selector, explicit plugin, sanitized-environment, no-shell, timeout, and JUnit-destination controls remain unchanged

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

#### Scenario: Exact external amendment authority permits one self-authored producer boundary

- **WHEN** unedited repository MEMBER comment `5464938148` is unexpired and binds the exact repository, issue, pull request, branch, green commit and tree, red commit and tree, workflow runs, artifacts, content digests, mapping, plan, selectors, and expected outcomes for pull request `#698`
- **THEN** the workflow may accept that exact green commit even though it changed an evidence producer
- **AND** the capability bypasses only the self-authored evidence-producer predicate
- **AND** live comment, expiry, run, artifact, digest, ancestry, linear-history, verified-green, and test-only red-prefix checks remain mandatory before binding and before reuse
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
