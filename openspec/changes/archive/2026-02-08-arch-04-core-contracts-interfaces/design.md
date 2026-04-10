# Design: Core Contracts and Module Interface Formalization

## Context

The modular architecture introduced in arch-01/02/03 (v0.27-0.29) provides:

- CommandRegistry with lazy loading (arch-01)
- Module package separation with boundary guards (arch-02)
- Module lifecycle management with dependency validation (arch-03)

However, the core IO contract (ProjectBundle) lacks formal protocol definitions, and while boundary guards prevent cross-module imports, there's no enforcement preventing core code from importing modules. This creates coupling that would block marketplace adoption where 3rd-party modules must be truly pluggable without core modifications.

**Current state:**

- ProjectBundle defined in `src/specfact_cli/models/project.py` as Pydantic BaseModel
- Modules consume/produce ProjectBundle informally
- No explicit `ModuleIOContract` protocol
- Boundary guards only prevent module→module coupling (via `test_module_boundary_imports.py`)
- Core can still import from modules (no static analysis prevention)

**Foundation for marketplace:** This change establishes the contract-first foundation that phases arch-05 (Bridge Registry), arch-06 (Security), arch-07 (Schema Extensions), and marketplace-01/02 depend on.

## Goals / Non-Goals

**Goals:**

- Define formal `ModuleIOContract` protocol that all modules must implement
- Enforce ProjectBundle as the ONLY IO contract between core and modules
- Add static analysis to prevent core→module imports (inversion-of-control enforcement)
- Update existing 5 modules (backlog, sync, plan, generate, enforce) to implement protocol
- Document ProjectBundle schema and module contract requirements for 3rd-party developers

**Non-Goals:**

- Schema extension mechanism (deferred to arch-07)
- Bridge registry for schema conversions (deferred to arch-05)
- Cryptographic module signing (deferred to arch-06)
- Marketplace infrastructure (deferred to marketplace-01/02)
- Breaking changes to existing module interfaces (backward compatible formalization)

## Decisions

### Decision 1: Protocol over Abstract Base Class

**Choice:** Use `typing.Protocol` for `ModuleIOContract` instead of ABC

**Rationale:**

- Structural subtyping: Modules don't need explicit inheritance
- Duck typing: Existing modules work without modification (opt-in formalization)
- Static type checking: basedpyright verifies compliance without runtime overhead
- Flexibility: Modules can implement subset of operations (e.g., sync-only modules)

**Alternatives considered:**

- ABC with abstract methods: Requires explicit inheritance, breaks existing modules
- No protocol: Informal contracts are error-prone and block marketplace verification

### Decision 2: Four Core Operations

**Choice:** Define 4 required operations: `import_to_bundle`, `export_from_bundle`, `sync_with_bundle`, `validate_bundle`

**Rationale:**

- **import_to_bundle**: External format → ProjectBundle (e.g., ADO work items → features)
- **export_from_bundle**: ProjectBundle → External format (e.g., features → ADO work items)
- **sync_with_bundle**: Bidirectional sync with conflict resolution
- **validate_bundle**: Module-specific validation rules (e.g., backlog module validates feature IDs exist in ADO)

**Alternatives considered:**

- Single `transform()` method: Too generic, loses operation semantics
- Separate read/write protocols: Overcomplicates simple unidirectional modules

### Decision 3: AST-Based Static Analysis for Core Isolation

**Choice:** Parse core directory ASTs and fail if any `import specfact_cli.modules.*` found

**Rationale:**

- Compile-time enforcement: Catches violations before PR merge
- Zero runtime overhead: AST parsing in tests only
- Clear error messages: Pinpoint file and line number of violation
- CI-enforceable: Blocks PRs that add core→module coupling

**Alternatives considered:**

- Runtime inspection: Overhead, detects after deployment
- Import hooks: Complex, fragile, runtime cost
- Manual code review: Error-prone, doesn't scale

**Implementation:**

```python
# tests/unit/test_core_module_isolation.py
def test_core_has_no_module_imports():
    core_dirs = [
        Path("src/specfact_cli/cli.py"),
        Path("src/specfact_cli/registry/"),
        Path("src/specfact_cli/models/"),
        Path("src/specfact_cli/utils/"),
        Path("src/specfact_cli/contracts/"),
    ]
    for file_path in collect_python_files(core_dirs):
        tree = ast.parse(file_path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module = get_module_name(node)
                if module.startswith("specfact_cli.modules."):
                    violations.append(f"{file_path}:{node.lineno} imports {module}")
    assert not violations, "Core imports module code"
```

### Decision 4: Gradual Module Migration

**Choice:** Update 5 existing modules incrementally, mark protocol as optional initially

**Rationale:**

- Non-breaking: Existing modules work without immediate changes
- Incremental: Update backlog first (simplest), then sync, plan, generate, enforce
- Validation: Module registration can check protocol compliance and warn if missing

**Alternatives considered:**

- Big-bang migration: Risky, blocks PRs across modules
- Never enforce: Defeats purpose, marketplace modules wouldn't be verifiable

### Decision 5: ProjectBundle Schema Versioning

**Choice:** Add `schema_version` field to ProjectBundle, document in reference docs

**Rationale:**

- Forward compatibility: Future schema changes don't break old modules
- Marketplace safety: 3rd-party modules declare compatible schema versions
- Migration path: Old modules continue working, new modules use versioned features

**Schema:**

```python
class ProjectBundle(BaseModel):
    schema_version: str = "1.0"  # NEW
    manifest: BundleManifest
    bundle_name: str
    idea: str
    # ... existing fields
```

**Alternatives considered:**

- No versioning: Schema changes break modules silently
- Separate version file: Requires extra file management, error-prone

## Risks / Trade-offs

### Risk 1: Module Migration Effort

**Risk:** Updating 5 modules to implement protocol is time-consuming

**Mitigation:**

- Start with simplest module (backlog) as template
- Protocol is opt-in initially; registration warns but doesn't fail
- Tasks include module-by-module migration with test validation

### Risk 2: False Positives in Static Analysis

**Risk:** AST parsing might flag valid imports (e.g., type hints, if TYPE_CHECKING)

**Mitigation:**

- Exclude `if TYPE_CHECKING:` blocks from analysis
- Allow specific exceptions via config file if needed
- Test against current codebase before enforcement

### Risk 3: ProjectBundle Schema Evolution

**Risk:** Future schema changes could break existing modules

**Mitigation:**

- Schema versioning from day 1
- Extension fields (arch-07) allow backward-compatible additions
- Deprecation policy for removals (2 minor versions notice)

### Risk 4: Performance Overhead from Protocol Checks

**Risk:** Runtime protocol validation adds overhead

**Mitigation:**

- Protocol is static type checking only (zero runtime cost)
- Opt-in runtime checks via `isinstance(module, ModuleIOContract)` only in registration
- CrossHair symbolic execution finds contract violations at CI time

## Contract Enforcement Strategy

Per project's contract-first philosophy:

1. **Static Analysis (Compile Time)**
   - AST parsing prevents core→module imports
   - basedpyright verifies ModuleIOContract compliance

2. **Registration Time**
   - Check if module implements protocol (warn if not)
   - Validate ProjectBundle schema version compatibility

3. **Runtime (via @icontract)**
   - `@require` preconditions on protocol methods (e.g., valid Path, non-empty config)
   - `@ensure` postconditions (e.g., returned ProjectBundle has required fields)
   - `@beartype` type validation

4. **CI/CD**
   - `hatch run contract-test` runs CrossHair symbolic execution
   - `hatch run type-check` enforces protocol adherence
   - `pytest tests/unit/test_core_module_isolation.py` blocks core→module imports

## Migration Plan

**Phase 1: Foundation (Week 1, Days 1-2)**

- Create `src/specfact_cli/contracts/module_interface.py` with protocol
- Add `tests/unit/test_core_module_isolation.py` static analysis test
- Add CI enforcement in `.github/workflows/tests.yml`

**Phase 2: Core Updates (Week 1, Days 3-4)**

- Add `schema_version` to ProjectBundle
- Update module registration to check protocol compliance (warn only)
- Document in `docs/reference/projectbundle-schema.md`

**Phase 3: Module Migration (Week 1, Days 4-5)**

- Update backlog module (template for others)
- Update sync, plan, generate, enforce modules
- Validate with contract-first tests

**Phase 4: Documentation (Week 1, Day 5)**

- Create `docs/reference/module-contracts.md` for 3rd-party developers
- Update architecture docs with contract-first patterns
- Update `docs/_layouts/default.html` navigation

**Rollback Strategy:**

- Protocol is opt-in initially; disabling warnings reverts to pre-change behavior
- Static analysis test can be skipped via `pytest -k "not test_core_module_isolation"` if needed
- No breaking changes to existing module interfaces

## Open Questions

**Q1:** Should protocol methods raise specific exceptions (e.g., `ModuleImportError`, `ModuleExportError`)?

**Answer:** Yes, define custom exceptions in `contracts/module_interface.py` for clear error semantics. Follow-up task to add exception hierarchy.

**Q2:** How do modules declare which operations they support (e.g., import-only)?

**Answer:** Optional protocol methods via `hasattr()` checks. Module registration inspects and logs supported operations. Full solution in arch-05 (bridge registry).

**Q3:** Should ProjectBundle schema version be semver (e.g., "1.0.0") or simple (e.g., "1")?

**Answer:** Simple integer version (e.g., "1") initially. Semver for schema extensions in arch-07. Keeps initial implementation minimal.

## Sequence Diagram: Module Registration with Protocol Validation

```
┌─────────┐         ┌──────────────┐         ┌────────────┐         ┌──────────┐
│ CLI Init│         │ Registry     │         │ Module Pkg │         │ Protocol │
└────┬────┘         └──────┬───────┘         └─────┬──────┘         └────┬─────┘
     │                     │                        │                     │
     │ discover_packages() │                        │                     │
     ├────────────────────>│                        │                     │
     │                     │ load manifest          │                     │
     │                     ├───────────────────────>│                     │
     │                     │                        │                     │
     │                     │ check protocol impl    │                     │
     │                     ├────────────────────────┼────────────────────>│
     │                     │                        │                     │
     │                     │<──────────────────────────── hasattr() checks│
     │                     │                        │                     │
     │                     │ [if protocol missing]  │                     │
     │                     │ log warning            │                     │
     │                     │                        │                     │
     │                     │ [if protocol present]  │                     │
     │                     │ validate schema_version│                     │
     │                     ├───────────────────────>│                     │
     │                     │                        │                     │
     │                     │ register module        │                     │
     │<────────────────────┤                        │                     │
     │                     │                        │                     │
```

## Plugin Registry Extensibility

This change maintains compatibility with the existing Plugin Registry pattern:

- **Before:** Modules registered via manifest, no contract validation
- **After:** Modules registered via manifest, protocol compliance checked at registration
- **Future (arch-05):** Bridge registry extends protocol with schema converters
- **Future (marketplace-01):** Marketplace modules validated for protocol compliance before approval

No changes required to existing `src/specfact_cli/registry/module_packages.py` registry pattern; this adds validation layer on top.
