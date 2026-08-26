# Design: Producer-bound retained red proof

## Context

`specfact requirements reconcile` is supplied by the immutable modules fixture and
produces the lifecycle report. Core owns Git access, pytest execution, artifact
retention, and historical validation. Core's validator correctly requires more
provenance than the released module currently emits, but the workflow has no step
that adds those core-owned facts before upload.

## Security boundary

The binding operation accepts only an untracked red report/JUnit pair that already
has a passing red reconciliation state, valid plan/mapping digests, exact selectors,
a source commit, and a digest-matching failing JUnit artifact. It derives:

1. the source tree and merge base from committed Git objects;
2. each selected test digest from the named blob at the recorded source commit; and
3. runner, Python, and pytest identities from properties emitted by the same proof
   subprocess into every selected JUnit case.

The binder writes no facts for final reports and does not infer a missing failure,
selector, source commit, or toolchain value from ambient mutable state.

## Decisions

### Extend the existing provenance utility

Keep binding and validation in one core-owned module so both paths share strict
shape, digest, selector, and Git helpers. Add a distinct CLI mode for binding while
preserving the existing validation invocation used by retained-run discovery.

### Bind toolchain identity through JUnit

The executor already loads a core-owned pytest plugin with third-party plugin
autoload disabled. Add canonical toolchain properties there and require exactly one
consistent value for every executed selector. Reading the ambient interpreter only
after execution would not prove which process produced the JUnit.

### Bind only after successful red reconciliation

The workflow calls the binder after the module writes the red report and before the
artifact fallback/terminal decision. Binding failure changes the workflow outcome
to non-zero and retains diagnostics; incomplete evidence is never uploaded as an
apparently usable red proof.

## Alternatives rejected

- **Relax validator fields**: weakens the security boundary and would accept the
  structurally incomplete artifacts the validator was designed to reject.
- **Retrofit old artifacts during final runs**: derives facts after the historical
  execution and cannot establish the original toolchain identity.
- **Change the pinned modules fixture**: expands scope into modules PR #436 and an
  independent signed release; the missing facts are core-owned.

## Failure modes and mitigations

- **Toolchain property spoofing or inconsistency**: require the exact property set
  on every selected case and one consistent non-empty value per field.
- **Mutable worktree test bytes**: hash immutable blobs at `source_ref`, never the
  current filesystem.
- **Partial report rewrite**: validate the complete input first and replace the JSON
  atomically only after all bindings are available.
- **Binding after a passing/final run**: reject every state except reconciled red
  evidence with a retained failure/error JUnit.
