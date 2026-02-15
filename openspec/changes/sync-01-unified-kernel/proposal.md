# Change: Sync Kernel — Unified Session-Based Sync Engine

## Why




Sync between backlog, requirements, specs, and code is currently adapter-specific with no unified session management, conflict resolution, or offline support. Each adapter implements its own sync logic, leading to inconsistent behavior: some silently overwrite, some fail on conflict, none provides session resumability. A central, deterministic sync kernel that orchestrates sessions, computes patches, handles conflicts, and queues offline writes gives every sync operation the same safety guarantees — never silent overwrites, always preview first, always resumable.

## Module Package Structure

```
modules/sync-kernel/
  module-package.yaml          # name: sync-kernel; commands: sync, sync resolve, sync status
  src/sync_kernel/
    __init__.py
    main.py                    # typer.Typer app — sync command group
    engine/
      session.py               # Session management (session_id, cursor, resume)
      patch_computer.py        # 3-way merge, JSON Patch (RFC 6902) generation
      conflict_detector.py     # Field-level conflict detection
      conflict_resolver.py     # Interactive + auto resolution strategies
      offline_queue.py         # Offline journal: .specfact/sync/journal/
    models/
      sync_session.py          # SyncSession, SyncPatch, ConflictRecord models
      sync_event.py            # CloudEvents-compatible envelope for interop
    providers/
      provider_protocol.py     # SyncProviderProtocol — adapters implement this
    concurrency/
      etag_manager.py          # Optimistic concurrency via ETags / If-Match
    commands/
      preview.py               # specfact sync --preview
      apply.py                 # specfact sync --apply
      resolve.py               # specfact sync resolve --session <id>
      status.py                # specfact sync status (show active sessions)
```

**`module-package.yaml` declares:**
- `name: sync-kernel`
- `version: 0.1.0`
- `commands: [sync, sync resolve, sync status]` (`--preview` and `--apply` are flags on `sync`)
- `dependencies: [patch-mode-01-preview-apply]` (uses preview/apply write-safety semantics)
- `publisher:` + `integrity:` — arch-06 marketplace readiness

## Module Package Structure

```
modules/sync-kernel/
  module-package.yaml          # name: sync-kernel; commands: sync, sync resolve, sync status
  src/sync_kernel/
    __init__.py
    main.py                    # typer.Typer app — sync command group
    engine/
      session.py               # Session management (session_id, cursor, resume)
      patch_computer.py        # 3-way merge, JSON Patch (RFC 6902) generation
      conflict_detector.py     # Field-level conflict detection
      conflict_resolver.py     # Interactive + auto resolution strategies
      offline_queue.py         # Offline journal: .specfact/sync/journal/
    models/
      sync_session.py          # SyncSession, SyncPatch, ConflictRecord models
      sync_event.py            # CloudEvents-compatible envelope for interop
    providers/
      provider_protocol.py     # SyncProviderProtocol — adapters implement this
    concurrency/
      etag_manager.py          # Optimistic concurrency via ETags / If-Match
    commands/
      preview.py               # specfact sync --preview
      apply.py                 # specfact sync --apply
      resolve.py               # specfact sync resolve --session <id>
      status.py                # specfact sync status (show active sessions)
```

**`module-package.yaml` declares:**
- `name: sync-kernel`
- `version: 0.1.0`
- `commands: [sync, sync resolve, sync status]` (`--preview` and `--apply` are flags on `sync`)
- `dependencies: [patch-mode-01-preview-apply]` (uses preview/apply write-safety semantics)
- `publisher:` + `integrity:` — arch-06 marketplace readiness

## What Changes




- **NEW**: Sync kernel in `modules/sync-kernel/` — central orchestrator for all sync operations
- **NEW**: Session management — each sync has `session_id`, cursor, and can be resumed after interruption or conflict
- **NEW**: 3-way merge with JSON Patch (RFC 6902) computation for structured data
- **NEW**: Field-level conflict detection: when both local and remote changed the same field, flag as conflict (never silent overwrite)
- **NEW**: Conflict resolution strategies: auto-resolve for non-overlapping fields, interactive for text conflicts, explicit resolve command for deferred conflicts
- **NEW**: Optimistic concurrency via ETags / If-Match for all upstream writes — fail-fast on stale data
- **NEW**: Offline journal at `.specfact/sync/journal/` — queue writes when upstream is unavailable, apply on next `sync --apply`
- **NEW**: CloudEvents-compatible event envelope for interoperability with external systems
- **NEW**: `SyncProviderProtocol` — adapters (backlog, requirements, architecture) implement this protocol to participate in sync sessions
- **NEW**: CLI commands: `specfact sync --preview` (dry-run patch), `specfact sync --apply` (execute patches), `specfact sync resolve --session <id>` (resolve pending conflicts), `specfact sync status` (show active sessions)
- **EXTEND**: Existing sync module behavior preserved — the kernel wraps existing adapter-specific sync calls with session management and conflict detection

## Capabilities
### New Capabilities

- `sync-kernel`: Unified session-based sync engine with 3-way merge, JSON Patch (RFC 6902), optimistic concurrency (ETags), field-level conflict detection, offline journal, and CloudEvents-compatible event model. Provides SyncProviderProtocol for adapter integration.

### Modified Capabilities

- `devops-sync`: Existing sync behavior wrapped with kernel session management; no breaking changes to current sync commands


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #243
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/243>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: 7a3f40973f815382 -->