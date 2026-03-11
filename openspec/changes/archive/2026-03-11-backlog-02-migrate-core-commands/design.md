# Design: Migrate backlog-core commands to specfact-backlog

## Context

The `backlog-core` module was deleted in commit 978cc82, removing 9 command implementations:
- `add` (27KB - interactive/non-interactive item creation)
- `analyze_deps` (dependency graph analysis)
- `sync` (bidirectional backlog sync)
- `delta` (delta analysis subcommands)
- `diff` (backlog state comparison)
- `promote` (hierarchy promotion)
- `verify_readiness` (DoR validation)
- `trace_impact` (impact analysis)
- `generate_release_notes` (release notes generation)

Source code exists in:
- Worktree: `specfact-cli-worktrees/feature/agile-01-feature-hierarchy/modules/backlog-core/`
- Git history: `git show 978cc82^:modules/backlog-core/`

Target location: `specfact-cli-modules/packages/specfact-backlog/src/specfact_backlog/`

## Goals / Non-Goals

**Goals:**
- Recover all deleted command implementations
- Integrate commands into specfact-backlog bundle structure
- Maintain backward-compatible CLI surface (`specfact backlog add`, etc.)
- Preserve existing tests and add integration coverage
- Add ceremony aliases for high-impact commands

**Non-Goals:**
- Re-implement from scratch (use existing code)
- Modify command behavior (migration only, no feature changes)
- Support backlog-core as standalone module (bundle-only)

## Decisions

### 1. Source Recovery Strategy

**Decision**: Copy from worktree (most recent) rather than git history.

**Rationale**: Worktree `feature/agile-01-feature-hierarchy` contains the latest backlog-core code before deletion, including any fixes applied during backlog-core-07 work.

### 2. Code Organization

**Decision**: Structure under `backlog/commands/` with submodules:
```
specfact_backlog/backlog/commands/
  add.py
  sync.py
  delta.py
  analyze_deps.py
  diff.py
  promote.py
  verify.py
  release_notes.py
  trace_impact.py
```

**Rationale**: Keeps commands organized and consistent with specfact-backlog's existing structure.

### 3. Integration Pattern

**Decision**: Register commands via existing `commands.py` app, following same pattern as `daily`/`refine`:
```python
@app.command()
def add(...): ...
```

**Rationale**: Consistent with specfact-backlog's current command registration. No new Typer apps needed.

### 4. Ceremony Aliases

**Decision**: Add ceremony aliases for high-frequency commands:
- `backlog ceremony add` → `backlog add`
- `backlog ceremony sync` → `backlog sync`

**Rationale**: Aligns with existing ceremony pattern (standup → daily, refinement → refine).

### 5. Import Path Updates

**Decision**: Update imports from `backlog_core.*` to `specfact_backlog.backlog.*`.

**Rationale**: Required for bundle integration. May require moving shared utilities to common locations.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Import dependencies on deleted core modules | Audit and replace with specfact-backlog equivalents |
| Test dependencies on backlog-core structure | Update test imports and fixtures |
| Duplicate code with specfact-backlog utilities | Refactor to use shared utilities where possible |
| Command ordering conflicts | Use `_BacklogCommandGroup` `_ORDER_PRIORITY` |

## Implementation Sequence

1. Copy command files from worktree to specfact-backlog
2. Update imports and fix dependency issues
3. Register commands in main `commands.py`
4. Add ceremony aliases
5. Copy and adapt tests
6. Run quality gates
7. Validate with `openspec validate`
