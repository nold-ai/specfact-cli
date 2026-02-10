# Design: Advanced Marketplace Features

## Context

marketplace-01 provides basic module installation but doesn't handle:
- Dependency conflicts between modules (e.g., module A needs requests>=2.28, module B needs requests<2.27)
- Namespace collisions (multiple "backlog" modules from different publishers)
- Custom enterprise registries
- Command aliases for user convenience

**Current State:**
- Single registry (official NOLD AI)
- No dependency resolution (modules install their pip_dependencies independently)
- Flat command names (no namespace support)
- No custom registry support

**Constraints:**
- Must detect conflicts before installation (don't break existing installs)
- Must remain offline-first (dependency resolution optional)
- Must support multiple registries with trust levels
- Must preserve backward compatibility with marketplace-01

## Goals / Non-Goals

**Goals:**
- Resolve pip dependency conflicts across all modules
- Support module aliases (user shortcuts)
- Enable custom registries for enterprises
- Enforce namespace requirements for marketplace modules
- Provide module publishing automation

**Non-Goals:**
- Module sandboxing or permissions (future)
- Per-module virtualenvs (too heavy for MVP)
- Automatic dependency updates (explicit only)
- Dependency version pinning enforcement (advisory only)

## Decisions

### Decision 1: Dependency Resolution Strategy

**Options:**
- **A**: pip-tools (pip-compile) integration
- **B**: Poetry resolver integration
- **C**: Custom constraint solver

**Choice: A (pip-tools with fallback)**

**Rationale:**
- pip-compile is standard Python tooling
- Handles PEP 440 specifiers correctly
- Fallback to basic pip resolver if pip-tools unavailable
- Familiar workflow for Python developers

**Trade-offs:**
- External dependency (mitigated by optional fallback)
- Conflict detection adds install time (acceptable for safety)

### Decision 2: Alias Storage and Resolution

**Options:**
- **A**: JSON file (~/.specfact/registry/aliases.json)
- **B**: YAML in config
- **C**: Database (SQLite)

**Choice: A (JSON file)**

**Rationale:**
- Simple, human-readable
- Easy to edit manually
- Fast lookups (small dataset)
- Consistent with existing registry storage

**Format:**
```json
{
  "backlog": "acme-corp/backlog-pro",
  "generate": "specfact/generate"
}
```

### Decision 3: Custom Registry Configuration

**Options:**
- **A**: YAML config file with registry list
- **B**: Command-based registration (like git remote)
- **C**: Registry discovery via DNS

**Choice: Hybrid (A + B)**

**Rationale:**
- YAML for persistence (~/.specfact/config/registries.yaml)
- Commands for user-friendly management
- Priority ordering for conflict resolution

**Schema:**
```yaml
registries:
  - id: official
    url: https://raw.githubusercontent.com/.../index.json
    priority: 1
    trust: always
  - id: enterprise
    url: https://registry.company.com/index.json
    priority: 2
    trust: prompt
```

### Decision 4: Namespace Enforcement

**Options:**
- **A**: Enforce namespace/name format for all modules
- **B**: Enforce for marketplace only, allow flat for custom
- **C**: Advisory only (warn but allow)

**Choice: B (enforce marketplace, allow custom)**

**Rationale:**
- Marketplace modules must use namespace (prevent collisions)
- Custom modules can use flat names (user responsibility)
- Backward compatible with built-in modules

**Validation:**
- marketplace modules: MUST match `^[a-z][a-z0-9-]+/[a-z][a-z0-9-]+$`
- custom modules: MAY use flat names
- Collision detection: warn if flat name conflicts with namespaced module

### Decision 5: Dependency Resolution Timing

**Options:**
- **A**: Resolve before install (dry-run first)
- **B**: Resolve during install (fail midway if conflict)
- **C**: Resolve on demand (user triggers)

**Choice: A (resolve before install)**

**Rationale:**
- Fail fast (don't start install if conflict)
- User can abort without partial state
- Clear error messages before changes

**Workflow:**
1. User runs `specfact module install X`
2. Download module metadata (not tarball yet)
3. Simulate: all_modules = current + X
4. Resolve dependencies → detect conflicts
5. If conflicts: display error, suggest resolutions, exit
6. If OK: proceed with download and install

### Decision 6: Publishing Pipeline

**Options:**
- **A**: Manual (user runs script, commits to registry repo)
- **B**: GitHub Actions (automated on release tag)
- **C**: Dedicated registry service

**Choice: B (GitHub Actions automation)**

**Rationale:**
- Automated on git tag (e.g., `backlog-v0.29.0`)
- Validation, packaging, signing all in CI
- Index.json updated automatically
- Pull request workflow for review

## Risks / Trade-offs

### Risk 1: Dependency conflicts too restrictive (false positives)
**Mitigation**: Allow --force flag to bypass, log warning, provide clear conflict messages

### Risk 2: pip-compile unavailable
**Mitigation**: Fallback to basic pip resolver (less sophisticated but functional)

### Risk 3: Custom registry security (malicious modules)
**Mitigation**: Trust levels (always/prompt/never), checksum verification, signature verification

### Risk 4: Alias collisions (user creates alias that shadows built-in)
**Mitigation**: Warn when alias shadows built-in, require confirmation

### Risk 5: Publishing pipeline complexity
**Trade-off**: Manual fallback available (scripts/publish-module.py can run locally)

## Migration Plan

### Phase 1: Dependency Resolution
1. Add dependency_resolver.py with pip-compile integration
2. Extend install command to resolve dependencies
3. Add --skip-deps flag for bypass

### Phase 2: Alias System
1. Add alias_manager.py
2. Extend module commands: alias, alias list, alias remove
3. Update command resolution to check aliases first

### Phase 3: Custom Registries
1. Add custom_registries.py
2. Extend module commands: add-registry, list-registries, remove-registry
3. Update fetch_registry_index() to support multiple registries

### Phase 4: Namespace Enforcement
1. Add namespace validation to module_installer.py
2. Enforce for marketplace modules
3. Add collision detection

### Phase 5: Publishing Pipeline
1. Create scripts/publish-module.py
2. Add .github/workflows/publish-modules.yml
3. Document publishing process

### Rollback
If issues arise:
1. Disable dependency resolver (--skip-deps becomes default)
2. Remove aliases.json (revert to direct resolution)
3. Revert registries.yaml (single registry)

## Open Questions

**Q1: Should dependency resolution be opt-in or default?**
- **Recommendation**: Default (with --skip-deps for bypass)
- Safer to resolve by default

**Q2: How to handle conflicting aliases from team members?**
- **Recommendation**: Aliases are local (~/.specfact/), not version controlled
- Teams can share recommended aliases in docs

**Q3: Should custom registries support authentication?**
- **Recommendation**: Yes (future enhancement) - support API keys in registries.yaml
- MVP: Public registries only
