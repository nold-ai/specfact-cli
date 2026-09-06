## Context

IDE export paths are repository-relative configuration values, but resolving an
attacker-controlled symlink turns the effective cleanup and write target into
an external directory. Child-relative checks cannot establish repository
containment after the root has already escaped.

## Decision

Validate the unresolved export root before any filesystem mutation. The root
must not be a symlink and its resolved path must be strictly beneath the
resolved repository path. Cleanup helpers return without side effects when the
root is unsafe, while export entry points raise a clear error before creating
or writing files.

Cleanup remains narrowly limited to existing SpecFact legacy naming and flat
`specfact*` output patterns; unrelated directories are not ownership evidence
and remain untouched.

## Alternatives Considered

- Persist ownership markers for every exported path. This would support more
  exact cleanup but adds migration state beyond the minimal security fix.
- Resolve the root and check only its children. Rejected because it validates
  containment relative to an already escaped root rather than the repository.

## Risks and Rollback

Repositories that intentionally symlink IDE export roots outside themselves
will now fail closed. That compatibility break is required to preserve the
repository boundary. A rollback must not occur without an alternative
ownership- and containment-safe export design.

