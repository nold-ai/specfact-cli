# Design: Central Module Registry MVP

## Context

The modular architecture (arch-01 through arch-07) provides strong encapsulation for module development, but all modules remain bundled with the CLI. To enable ecosystem growth and allow users to install/uninstall modules independently, we need marketplace infrastructure.

**Current State:**
- All modules in `src/specfact_cli/modules/` (built-in)
- Module discovery scans single location
- No installation/uninstallation capability
- No external module registry

**Constraints:**
- Must remain offline-first (marketplace access is optional, not required)
- Must support built-in modules for offline usage
- Must verify module integrity (checksums from arch-06)
- Must maintain backward compatibility (existing installs work unchanged)
- Must support future custom module sources

## Goals / Non-Goals

**Goals:**
- Enable module installation from central registry (official NOLD AI modules)
- Support multi-location discovery (built-in, marketplace, custom)
- Implement checksum verification on install
- Create CLI commands for module management (install/uninstall/search/list/upgrade)
- Establish registry infrastructure foundation (index.json schema)

**Non-Goals:**
- Third-party publishing (marketplace-01 is official modules only)
- Dependency resolution (deferred to marketplace-02)
- Module sandboxing or permissions (future enhancement)
- Automatic updates (explicit upgrade command only)
- Web UI or marketplace portal (CLI-first approach)

## Decisions

### Decision 1: Registry Location and Schema

**Options:**
- **A**: GitHub repository with index.json (static files, no backend)
- **B**: Dedicated registry service with API
- **C**: PyPI-style package index

**Choice: A (GitHub repository)**

**Rationale:**
- Simple, no infrastructure overhead
- Aligns with offline-first philosophy (registry is optional)
- Version control for registry changes
- GitHub CDN for downloads
- Easy to mirror or fork

**Trade-offs:**
- No search API (client-side filtering)
- Manual publishing workflow (acceptable for MVP with official modules only)
- Download rate limits (GitHub raw content)

**Schema:**
```json
{
  "schema_version": "1.0",
  "modules": [
    {
      "id": "specfact/backlog",
      "namespace": "specfact",
      "name": "backlog",
      "description": "...",
      "latest_version": "0.29.0",
      "core_compatibility": ">=0.28.0,<1.0.0",
      "download_url": "https://raw.githubusercontent.com/.../backlog-0.29.0.tar.gz",
      "checksum_sha256": "abc123...",
      "signature_url": "...",
      "tier": "community",
      "tags": ["backlog", "agile"]
    }
  ]
}
```

### Decision 2: Module Installation Paths

**Options:**
- **A**: ~/.specfact/marketplace-modules/ (separate from built-in)
- **B**: ~/.local/share/specfact-cli/modules/ (XDG standard)
- **C**: Same location as built-in (site-packages/specfact_cli/modules/)

**Choice: A (separate marketplace path)**

**Rationale:**
- Clear separation: built-in vs marketplace vs custom
- No conflicts with package manager (pip/uvx)
- Easy uninstall (delete directory)
- Preserves built-in modules on CLI upgrade

**Paths:**
- Built-in: `{site-packages}/specfact_cli/modules/`
- Marketplace: `~/.specfact/marketplace-modules/`
- Custom: `~/.specfact/custom-modules/`

### Decision 3: Multi-Location Discovery Order

**Options:**
- **A**: Built-in → Marketplace → Custom (priority order)
- **B**: Marketplace → Built-in → Custom (marketplace takes precedence)
- **C**: Scan all, warn on duplicates

**Choice: A (built-in first)**

**Rationale:**
- Guarantees core functionality even if marketplace unreachable
- Offline-first: built-in modules always available
- Predictable: built-in modules can't be shadowed
- Users can override with custom path if needed

**Discovery Algorithm:**
```python
def discover_all_modules():
    discovered = {}

    # 1. Built-in (highest priority)
    for module in scan(builtin_path):
        discovered[module.name] = module

    # 2. Marketplace (if exists)
    for module in scan(marketplace_path):
        if module.name not in discovered:
            discovered[module.name] = module

    # 3. Custom (lowest priority)
    for module in scan(custom_path):
        if module.name not in discovered:
            discovered[module.name] = module

    return list(discovered.values())
```

### Decision 4: Installation Workflow

**Options:**
- **A**: Download → Verify → Extract → Register (single-step)
- **B**: Download → Verify → Prompt → Extract → Register (confirm before install)
- **C**: Download → Extract → Verify → Register (verify after extraction)

**Choice: A (verify before extract)**

**Rationale:**
- Fail fast on integrity issues
- No partial installs (atomic operation)
- Matches arch-06 security model
- Simpler rollback

**Workflow:**
```
1. Fetch index.json from registry
2. Look up module by ID
3. Download tarball to temp directory
4. Verify checksum (arch-06 infrastructure)
5. Extract to ~/.specfact/marketplace-modules/{module-name}/
6. Load module-package.yaml and validate
7. Register module (update ~/.specfact/registry/modules.json)
8. Cleanup temp files
```

### Decision 5: Offline Behavior

**Options:**
- **A**: Fail on network unavailable
- **B**: Warn and continue with cached index
- **C**: Warn and continue with built-in modules only

**Choice: C (graceful degradation)**

**Rationale:**
- Offline-first philosophy
- Built-in modules remain functional
- User can install from local tarball (future: `specfact module install ./module.tar.gz`)

**Fallback Strategy:**
- Network unavailable → log warning, use built-in modules
- Index fetch fails → log warning, use cached index if available
- Module download fails → error, suggest offline installation

### Decision 6: Module Namespace Enforcement

**Options:**
- **A**: Enforce namespace prefix (specfact/*, acme-corp/*)
- **B**: Allow flat names (backlog, sync)
- **C**: Enforce for marketplace, allow flat for custom

**Choice: C (enforce for marketplace)**

**Rationale:**
- Official modules use `specfact/*` namespace
- Custom modules can use flat names (user responsibility)
- Future-proof for third-party publishing

## Risks / Trade-offs

### Risk 1: Registry unavailable (network outage, GitHub down)
**Mitigation**: Offline-first design, built-in modules remain functional, cached index support (future)

### Risk 2: Malicious modules in marketplace
**Mitigation**: Official modules only (MVP scope), checksum verification (arch-06), signature verification (arch-06)

### Risk 3: Module conflicts (name collision)
**Mitigation**: Namespace enforcement (specfact/*), discovery order (built-in first)

### Risk 4: Incomplete uninstall (orphaned files)
**Mitigation**: Modules in isolated directories, uninstall removes entire directory, no shared dependencies (MVP)

### Risk 5: Version compatibility issues
**Mitigation**: core_compatibility field in index.json, skip incompatible modules during discovery

### Risk 6: Large download sizes
**Trade-off**: Acceptable for MVP (official modules are small), future: delta updates

## Migration Plan

### Phase 1: Repository Setup
1. Create `nold-ai/specfact-cli-modules` repository
2. Set up registry/ structure (index.json, modules/, signatures/)
3. Add publishing scripts

### Phase 2: CLI Implementation
1. Implement multi-location discovery
2. Create `module` module with commands
3. Implement marketplace client
4. Implement module installer

### Phase 3: Built-in Module Packaging
1. Package existing modules as tarballs
2. Generate checksums
3. Update index.json

### Phase 4: Testing and Documentation
1. Test install/uninstall workflows
2. Test offline behavior
3. Write user guides

### Rollback
If critical issues arise:
1. Disable marketplace client (feature flag)
2. Revert to built-in-only discovery
3. Modules already installed remain functional

## Open Questions

**Q1: Should we cache the registry index locally?**
- **Recommendation**: Yes (future enhancement) - cache with TTL, refresh on `module search`
- **MVP**: Fetch on every operation, fail gracefully if offline

**Q2: How to handle module upgrades with breaking changes?**
- **Recommendation**: core_compatibility field prevents incompatible installs
- **Future**: Warn on major version upgrades

**Q3: Should uninstall require confirmation?**
- **Recommendation**: Yes for built-in modules (error: can't uninstall), No for marketplace/custom
- **MVP**: Simple uninstall, no confirmation

**Q4: How to handle module dependencies (module A requires module B)?**
- **Recommendation**: Deferred to marketplace-02 (dependency resolution)
- **MVP**: module_dependencies field exists but not enforced during install


### Decision 7: Lifecycle UX Harmonization (init vs module command)

**Context:** `specfact init` already owns module enable/disable/list lifecycle flags from prior architecture changes. This marketplace change introduces a new canonical module management command group (`specfact module ...`), creating potential UX duplication.

**Choice:** Keep `init` lifecycle flags as backward-compatible aliases while standardizing user guidance and documentation on `specfact module` as canonical lifecycle surface.

**Rationale:**
- Avoids breaking existing automation and user workflows built on `specfact init --enable-module/--disable-module/--list-modules`.
- Preserves behavior required by existing canonical specs and tests while still reducing UX ambiguity.
- Enables phased deprecation instead of disruptive removal.

**Implementation constraints:**
- No hard removal of init lifecycle flags in this change.
- Alias behavior must remain functionally equivalent for state management operations.
- Help text and docs should steer new users to `specfact module` lifecycle commands.
