## ADDED Requirements

### Requirement: Lifecycle-Derived Requirements Gate

Core SHALL derive the required evidence maturity from the complete pull-request
or staged diff and repository policy rather than an author-declared phase. A
proposal-only change requires `planned` maturity and may pass without test
execution; its retained report SHALL explicitly state that implementation
evidence is not yet available. Test-only and production changes SHALL require
successively stronger accepted, red, and verified evidence.

#### Scenario: Proposal-only change passes readiness without execution

- **GIVEN** a changed OpenSpec proposal with a complete planned requirements
  mapping and no changed governed production or test path
- **WHEN** the gate evaluates the diff
- **THEN** it requires `planned` maturity
- **AND** it publishes a successful proposal-readiness report
- **AND** the report labels implementation evidence as not-yet-available
- **AND** it does not label the change executed, implemented, or verified.

#### Scenario: Mixed or production diff cannot be downgraded

- **GIVEN** a diff containing a proposal mapping and a governed test or
  production touchpoint
- **WHEN** the gate evaluates the diff
- **THEN** it requires the strongest maturity applicable to that touchpoint
- **AND** a proposal-only mapping cannot cause the product change to pass at
  `planned` maturity.

### Requirement: Accepted Mapping Before Automation

Core SHALL require acceptance evidence bound to the canonical mapping digest
before test automation or production implementation. Acceptance may originate
from a trusted reviewed base branch or a provider-neutral normalized review
record; proposal-only readiness SHALL expose pending acceptance without
blocking proposal review.

#### Scenario: Test-only change requires current acceptance

- **GIVEN** a test-only diff mapped to an active requirement source
- **WHEN** the gate evaluates the diff
- **THEN** it requires accepted mapping evidence whose digest matches the
  current mapping
- **AND** stale, rejected, or unverifiable review evidence blocks automation.

### Requirement: Git-Bound Failing-First Proof

Except for the bounded R07 migration described below, Core SHALL require a
runner-generated red proof from a test-only ancestor commit after the current
pull-request base before a governed production change can reach verified
maturity. The
proof SHALL bind the commit/tree, merge base, mapping digest, selectors,
test-file digests, JUnit digest, and toolchain identity. Core SHALL reject
proof when governed production changed before the red commit, including a
governed source renamed outside its prefix, or when any pytest-determining
input changed after it. Pytest-determining inputs are enumerated once, in the
retained-proof scenario of Safe Pull-Request Proof Execution; this requirement
SHALL NOT restate a partial list that could drift from it.
Before forwarding a prior-red report to the
released reconciliation command, core SHALL verify that its source commit is a
strict ancestor of the final source, the current pull-request base is an
ancestor of that source, and that the selected test files remain
unchanged since that source.
The prior-red JSON SHALL be accompanied by a retained JUnit XML artifact whose
digest matches the execution proof and whose cases contain a failure or error;
self-reported JSON without that artifact SHALL be rejected. Core SHALL also
reject prior-red JSON or JUnit committed in the pull-request tree; normal red
proof inputs SHALL come from runner-retained artifacts outside that tree.

For `requirements-07-runtime-proof-delivery` only, Core SHALL instead accept
the historical failing-first ledger from approved immutable commit
`69f075819be5e1ceca1446b026b0417f19e584ca` when its ledger digest is bound to
the current mapping and final-plan digests. Core SHALL use this exception only
during final reconciliation, SHALL reject a modified checkout ledger, and
SHALL NOT extend it to any other change.

#### Scenario: Production change follows valid red proof

- **GIVEN** a valid test-only ancestor and red proof for the exact mapping and
  selectors
- **WHEN** production code changes and the selectors pass at the current HEAD
- **THEN** the gate reports verified maturity
- **AND** it preserves both red and final execution provenance.

#### Scenario: Same-commit or stale red proof is rejected

- **GIVEN** tests and production code first appear in the same commit, or any
  pytest-determining input of a mapped selector changes after the red proof
- **WHEN** the gate evaluates a governed production diff
- **THEN** it fails with `tdd-order-unproven` or `stale-red-proof`
- **AND** retained-run discovery searches every completed-run page, skips
  invalid red artifacts, and continues to older eligible runs
- **AND** it retains diagnostic artifacts before enforcing the verdict.

### Requirement: Staged Scenario Proof Planning

The core pre-commit gate SHALL invoke only a verified released Requirements
module to produce and validate a proof plan from the staged Git index before
Code Review and contract tests. It SHALL keep local planning bounded and SHALL
NOT claim current-run execution proof without a result-reconciliation step.

#### Scenario: Staged product change has complete proof plan

- **GIVEN** staged requirement and product-interface changes map selected
  scenarios to valid touchpoints and exact test selectors
- **WHEN** pre-commit Block 2 runs
- **THEN** the gate retains the index-isolated plan and static evidence report
- **AND** it continues to ordinary Code Review and contract gates
- **AND** it does not mark any test executed or passed.

#### Scenario: Staged interface change lacks mapped proof

- **GIVEN** a staged relevant product-interface change with no governed
  scenario mapping or no valid exact test selector
- **WHEN** staged proof planning runs under strict policy
- **THEN** the gate retains remediation evidence and exits non-zero
- **AND** later review and contract gates do not run.

#### Scenario: Staged change has no requirement impact

- **GIVEN** the staged diff qualifies for a governed no-requirement-impact
  decision
- **WHEN** planning runs
- **THEN** it emits an explicit skipped report with the bounded reason and
  changed-path digest
- **AND** policy-designated product-interface, contract, requirement-source,
  and proof-test paths cannot use that skip
- **AND** it does not silently omit the Requirements gate.

### Requirement: Safe Pull-Request Proof Execution

Core CI SHALL validate a module-produced structured proof plan and execute only
supported exact test selectors in the frozen repository environment. It SHALL
pass selectors as process arguments without shell interpretation and SHALL
retain deterministic JUnit results for module-owned reconciliation.

#### Scenario: Valid exact selectors execute through an argument array

- **GIVEN** the verified module emits a supported bounded plan whose pytest
  selectors identify repository-contained exact test cases
- **WHEN** the CI executor runs the plan
- **THEN** it invokes the frozen pytest runner with selectors as argument-array
  values after the runner option boundary
- **AND** a repository-controlled result plugin records each exact collected
  pytest node ID as a canonical selector property in JUnit
- **AND** it writes JUnit to a fresh deterministic artifact path
- **AND** it does not use `eval`, shell expansion, or command text from the plan.

#### Scenario: Unsafe plan is rejected before test execution

- **GIVEN** a selector has an absolute or escaping path, option prefix,
  control/shell syntax, wildcard expansion, duplicate identity, unsupported
  runner, or exceeds a configured plan bound
- **WHEN** core validates the plan
- **THEN** it fails before starting a test process
- **AND** it retains bounded diagnostic evidence describing the rejected field.

#### Scenario: Test execution is incomplete or fails

- **GIVEN** a valid plan whose test process times out, fails, errors, skips a
  required test, or omits a required selector from JUnit
- **WHEN** core returns the plan and available JUnit to the verified module
- **THEN** the module-owned final report remains red or unproven
- **AND** core publishes all available artifacts before enforcing failure.

#### Scenario: Retained proof inputs or output are missing or stale

- **GIVEN** a retained red proof whose pytest-determining inputs change after
  the red source, or an executor run that leaves no non-empty JUnit artifact
- **AND** pytest-determining inputs are the selected test, every applicable
  `conftest.py`, every possible parent package initializer of either input
  including the repository-root initializer, the repository pytest
  configuration source in every implicit candidate the locked pytest version
  discovers beneath the repository root and every selector ancestor pytest
  searches upward through, each such candidate being bound whether or not it
  exists at the red source so that adding one afterwards invalidates the proof, every statically reachable repository-local import of
  those files after resolving verified `typing.TYPE_CHECKING` guards, including
  imports inside a function body, because pytest invokes test and fixture bodies
  during the run, while a package initializer keeps its bodies unbound until it
  invokes something while loading, and every
  module-level `pytest_plugins` declaration made by a pytest-considered module
  through its active or runtime-conditionally possible static bindings,
  including known values preserved across non-literal conditional assignments
- **AND** a dotted module name a reachable body hands to a call is bound when
  that module exists at the red source, because a dynamic import names its
  target in data rather than in the callee, so `importlib.import_module`,
  `__import__`, an alias, a wrapper, and a name read out of a literal group are
  covered without matching an import mechanism by name; a literal that is only
  written down, that names no committed module, or that is a bare word rather
  than a dotted name is not read as an import, because binding prose would fail
  valid proofs on edits to files pytest never loads
- **AND** a plugin early-loaded through a `-p` option is a proof input on the
  same terms as a declared plugin, whether the option comes from configured
  `addopts` or from the command the proof executor builds for every run, because
  a plugin the run always loads decides collection and report shape
- **AND** a committed file the resolved proof inputs read by literal path, either
  as a single string handed to a call or as literals joined onto a path root, is
  itself a proof input when it lies inside a directory the selected tests live
  in, because data under the test tree is harness the red-to-green change may not
  edit; a path outside that tree is what the change is expected to edit and stays
  unbound, and a path assembled at runtime binds nothing rather than failing the
  proof, because a harness that writes into a temporary directory is not evidence
  of anything stale
- **AND** a literal that cannot name a committed path, because it carries a
  control character or a traversal segment, is discarded before it becomes a Git
  argument, so an arbitrary string in a test fixture cannot raise out of the gate
- **AND** a join is resolved against the base it starts from, so a harness naming
  data beside itself through `__file__`, `.parent`, `.parents[n]`, `.resolve()`,
  or a name bound to any of them binds the file it actually reads, while a join
  from a base decided at runtime binds nothing rather than being read as though
  it started at the repository root
- **AND** a committed link a proof input reads is followed to its target, with
  every hop bound because editing any of them changes the bytes returned, and a
  link that leaves the checkout, cycles, or points at nothing is stale
- **AND** a lookup Git could not answer, including a timed-out one, is stale
  rather than absent, because treating an unanswered lookup as a missing file
  leaves the module and everything it imports untraversed
- **AND** the body of a test an exact selection does not run is not traversed,
  provided the selection resolves to functions defined in that module and the
  function's name appears nowhere else in it; fixtures are always traversed,
  because which ones a run activates depends on autouse declarations, indirect
  parametrization, conftest chains, and plugins, none of which this gate can
  decide from the module's syntax
- **AND** the resolved input set is measured against this repository so the rule
  family is held to what it must not bind as well as what it must: no product
  source is ever an input, every bound file outside the test tree is a recorded
  exception, and the set stays proportional to the selectors, because a rule that
  binds too much satisfies every positive expectation while rejecting valid proofs
- **AND** only the final possible `pytest_plugins` binding is bound, because an
  assignment a later one overwrites never loads, and a name bound only inside a
  function, lambda, or class body does not rebind a module-level guard
- **AND** a declared plugin is resolved against the repository root and every
  configured pytest `pythonpath` root, parsed as pytest parses a path list and
  normalized as pytest resolves it against the directory of the file declaring
  it, so a repository-contained root binds its plugins whether it is spelled
  relative to a nested configuration, with traversal segments, or as an absolute
  path inside the checkout, rather than being dropped, and
  a plugin loaded from such a root resolves its own imports against that root,
  while an input discovered at the repository root resolves ordinary imports
  there alone so governed production modules that a red-to-green change is
  expected to edit do not become proof inputs
- **WHEN** pull-request CI validates or executes the Requirements proof
- **THEN** the proof remains stale or unproven
- **AND** an active `pytest_plugins` declaration whose value cannot be resolved
  statically is treated as stale rather than silently ignored, including when a
  loop, context-manager, exception, match, or walrus target rebinds the
  constant it reads, when a mutation reaches the declaration through another
  name bound to the same object whether by method call, subscript or attribute
  write, augmented assignment, deletion, or being handed to a call that could
  mutate it, including a chained assignment whose targets share one object, when an executing class body creates the declaration through a
  `global` statement, or when the declaration is bound by an import whose value
  lives in another module
- **AND** a proof input or configuration source that exists at the red source
  but cannot be read or parsed, because it is oversized, malformed, unreadable
  through a failed or timed-out read, or a symlink whose executed bytes were
  never inspected, is treated as stale rather than skipped like an absent
  candidate, so an unreadable candidate is never mistaken for a missing one, and
  a symlink is recognized by its Git mode rather than by failing to parse,
  because a link text such as `support.py` is itself valid Python
- **AND** an import resolved through a symlinked directory is treated as stale,
  because Python follows the directory link while Git records the link rather
  than the target tree
- **AND** a typing guard is trusted only while unmutated, so an attribute write
  to its `TYPE_CHECKING` member, handing the guard module to any call that could
  rewrite that member including through a nested argument expression, copying
  the module into a second binding through which a write would be invisible, or
  a `global` rebinding from a class body drops it, a rebinding invalidates only
  the branches that follow it, and any literal branch condition is resolved by
  its truthiness
- **AND** module state is treated as unverifiable, failing closed for both the
  guard and the plugin declaration, when a module defines a function or lambda
  that can rebind a global, write a `TYPE_CHECKING` attribute, rewrite an
  attribute through `setattr`, hand the guard module to any call, or assign
  `pytest_plugins`, and also invokes anything while loading, where applying a
  decorator counts as an invocation even when it is a bare name
- **AND** a module that writes its own namespace mapping, as through
  `globals()` or `vars()`, is unverifiable on the same terms, because such a
  write creates the attribute pytest reads without binding any name
- **AND** a rewriter is recognized by the guard name it receives rather than by
  the callee's name, so an aliased or wrapped rewriter cannot evade the rule
- **AND** every rule that asks which name an expression touches resolves that
  name through attribute, subscript, and call chains, so a wrapped form such as
  a write through the module mapping cannot evade a rule its unwrapped
  equivalent triggers
- **AND** each fail-closed rule is bounded to the state this gate depends on, so
  ordinary module activity that cannot reach a guard or a plugin declaration
  leaves both resolvable
- **AND** a malformed report field, undecodable or oversized source, or Git
  timeout yields a deterministic finding rather than an unhandled error
- **AND** the Requirements evidence gate exits nonzero after retaining its
  diagnostic reports.

#### Scenario: A selected test path is a symlink

- **GIVEN** a retained red proof selects a symlink instead of a regular test file
- **WHEN** core validates its Git-bound execution inputs
- **THEN** core rejects the proof as invalid rather than hashing only the link target name.

### Requirement: Authoritative Reconciliation and Review Handoff

Core SHALL delegate scenario proof reconciliation to the same verified module
release that produced the plan. It SHALL pass only finalized Requirements proof
to the released Code Review context interface, preserve both reports and
verdicts separately, and run existing contract/full quality gates independently.

#### Scenario: Current-run proof passes and informs review

- **GIVEN** exact selected tests execute and pass and module reconciliation
  returns a finalized passing Requirements report
- **WHEN** CI starts Code Review
- **THEN** it supplies the finalized report as validated context
- **AND** retains Requirements and review provenance separately
- **AND** continues to existing independent contract and quality checks.

#### Scenario: Review passes while Requirements proof fails

- **GIVEN** the Requirements report is red and the separate review report is
  green
- **WHEN** delivery enforcement runs
- **THEN** the Requirements check remains blocking
- **AND** the review verdict does not replace or rewrite it.

#### Scenario: Requirements proof passes while another gate fails

- **GIVEN** the Requirements report is green but Code Review, contract tests,
  full tests, static analysis, or security checks fail
- **WHEN** delivery enforcement completes
- **THEN** those independent gates remain blocking
- **AND** targeted scenario proof is not treated as a replacement for them.

### Requirement: Always-Published Requirements Proof Decision

Pull-request CI SHALL produce a selected, failed, or explicit skipped
Requirements proof decision for every governed pull request and SHALL retain
the plan, JUnit when execution starts, final JSON/Markdown evidence, and concise
summary before enforcing a red verdict.

#### Scenario: Relevant product change cannot disappear through path filters

- **GIVEN** a pull request changes governed product, contract, test, or
  requirement-source paths
- **WHEN** workflows are scheduled
- **THEN** the Requirements proof decision runs even if no OpenSpec file changed
- **AND** branch protection receives a terminal result.

#### Scenario: No-impact pull request reports a governed skip

- **GIVEN** a pull request has no requirement impact under deterministic policy
- **WHEN** the Requirements proof decision runs
- **THEN** it publishes a skipped report and reason
- **AND** branch protection receives a successful terminal result rather than a
  missing check.
