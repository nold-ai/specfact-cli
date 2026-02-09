# Design: Schema Extension System

## Context

The modular architecture (arch-01/02/03) enables independent module development, but modules currently cannot persist custom metadata in ProjectBundle without modifying core models. This blocks marketplace scenarios where backlog modules need to track external IDs (ADO work item IDs, Jira issue keys) or sync modules need to store last-sync timestamps.

**Current State:**
- `Feature` and `ProjectBundle` models are fixed-schema Pydantic classes
- Modules duplicating schema logic or introducing core-module coupling
- No mechanism for modules to declare schema extensions in manifests

**Constraints:**
- Must preserve backward compatibility (existing bundles remain valid)
- Must prevent namespace collisions between modules
- Must maintain type safety with Pydantic validation
- Must work with contract-first approach (@icontract, @beartype)
- Must support serialization/deserialization (YAML, JSON)

## Goals / Non-Goals

**Goals:**
- Enable modules to extend Feature and ProjectBundle with custom fields
- Provide type-safe accessors/mutators with namespace enforcement
- Support declarative extension registration via module manifests
- Maintain backward compatibility with existing bundles
- Prevent module namespace collisions through prefixed field names

**Non-Goals:**
- Dynamic model creation at bundle load time (extensions are optional metadata)
- Schema migration for existing bundles (extensions default to empty dict)
- Runtime type coercion beyond Pydantic's native capabilities
- Validation of extension field values (module responsibility)

## Decisions

### Decision 1: Extensions as dict field vs. dynamic model generation

**Options:**
- **A**: Add `extensions: dict[str, Any]` field with namespace-prefixed keys
- **B**: Use `pydantic.create_model()` to dynamically extend models at registration time
- **C**: Use Python descriptors for field access interception

**Choice: A (dict field with namespace enforcement)**

**Rationale:**
- Simpler serialization (standard Pydantic dict handling)
- Backward compatible (field defaults to empty dict)
- Type safety via accessor methods with @beartype validation
- No runtime model generation complexity
- Easier debugging (extensions visible in model repr)

**Trade-offs:**
- Extensions not part of IDE autocomplete (acceptable for dynamic fields)
- Requires explicit accessor calls vs. attribute access
- No Pydantic Field() validation for extension values (module responsibility)

### Decision 2: Namespace format

**Options:**
- **A**: `module.field` (dot-separated)
- **B**: `module__field` (double-underscore)
- **C**: `module/field` (slash-separated)

**Choice: A (dot-separated)**

**Rationale:**
- Consistent with Python package naming conventions
- Human-readable and clear ownership
- Easy to parse and validate
- Example: `backlog.ado_work_item_id`, `sync.last_sync_timestamp`

### Decision 3: Extension declaration in manifest

**Options:**
- **A**: Declarative in `module-package.yaml` (static metadata)
- **B**: Programmatic via registration function (runtime)
- **C**: Hybrid (manifest + runtime validation)

**Choice: A (declarative in manifest)**

**Rationale:**
- Aligns with existing manifest pattern (commands, bridges, dependencies)
- Static analysis possible (detect conflicts before installation)
- Documentation-first approach (manifest is source of truth)
- No code execution required to discover extensions

**Example:**
```yaml
schema_extensions:
  - target: Feature
    fields:
      ado_work_item_id:
        type: string | None
        description: "Azure DevOps work item ID"
      jira_issue_key:
        type: string | None
        description: "Jira issue key"
```

### Decision 4: Accessor/mutator pattern

**Options:**
- **A**: Direct dict access: `feature.extensions["backlog.ado_id"]`
- **B**: Helper methods: `feature.get_extension("backlog", "ado_id")`
- **C**: Attribute-style proxy: `feature.ext.backlog.ado_id`

**Choice: B (helper methods)**

**Rationale:**
- Type-safe with @beartype validation
- Clear separation from core fields
- Explicit namespace handling (prevents typos)
- Consistent with Pydantic BaseModel patterns
- Enables future validation hooks

**API:**
```python
def get_extension(self, module_name: str, field: str, default: Any = None) -> Any:
    return self.extensions.get(f"{module_name}.{field}", default)

def set_extension(self, module_name: str, field: str, value: Any) -> None:
    self.extensions[f"{module_name}.{field}"] = value
```

## Risks / Trade-offs

### Risk 1: Namespace collisions between modules
**Mitigation**: Static analysis test validates no duplicate `module.field` keys across all installed modules. Registration fails if collision detected.

### Risk 2: Type safety weaker than core fields
**Trade-off**: Extensions use `Any` type since modules define their own schemas. Modules responsible for validating extension values. Acceptable for marketplace extensibility.

### Risk 3: Extension fields not discoverable in IDE
**Trade-off**: IDE autocomplete won't suggest extension fields. Acceptable given dynamic nature. Documentation and manifest declarations serve as reference.

### Risk 4: Performance overhead of dict lookups
**Mitigation**: Extensions are optional metadata, accessed only when needed. No impact on core bundle operations. Profile if concerns arise.

### Risk 5: Backward compatibility with old bundles
**Mitigation**: `extensions` field defaults to empty dict. Old bundles without extensions remain valid. Serialization preserves extensions when present.

## Migration Plan

### Phase 1: Add extensions field to models
1. Add `extensions: dict[str, Any] = Field(default_factory=dict)` to Feature (plan.py and project.py)
2. Add `extensions: dict[str, Any] = Field(default_factory=dict)` to ProjectBundle
3. Add `get_extension()` and `set_extension()` methods to both models
4. Add contracts (@require namespace format: `module_name.field_name`)

### Phase 2: Manifest schema extension
1. Extend `ModulePackageMetadata` with `schema_extensions: list[SchemaExtension]`
2. Add `SchemaExtension` model (target, fields dict)
3. Update manifest parser to load schema_extensions

### Phase 3: Registration-time validation
1. Extend module registration to collect schema_extensions from manifests
2. Build global extension registry (module → extensions mapping)
3. Validate no namespace collisions at registration time
4. Log registered extensions for debugging

### Phase 4: Documentation and testing
1. Add guide: `docs/guides/extending-projectbundle.md`
2. Add tests for namespace enforcement, accessor/mutator, serialization
3. Update architecture docs with extension pattern

### Rollback
If critical issues arise:
1. Remove `extensions` field from models (breaking for modules using extensions)
2. OR: Keep field but disable manifest parsing (extensions become inert)
3. Existing bundles without extensions remain unaffected

## Open Questions

**Q1: Should extension values be validated at bundle save time?**
- Current: No validation (module responsibility)
- Alternative: Optional JSON Schema validation per module manifest
- **Decision**: Defer to future enhancement (YAGNI principle)

**Q2: Should extensions be indexed for fast lookup?**
- Current: Flat dict with `module.field` keys
- Alternative: Nested dict `{"module": {"field": value}}`
- **Decision**: Keep flat (simpler, sufficient for expected scale)

**Q3: Should core provide extension migration helpers?**
- Current: Modules handle their own extension schema evolution
- Alternative: Core provides version-aware migration framework
- **Decision**: Defer to future (modules use standard Pydantic migration patterns)
