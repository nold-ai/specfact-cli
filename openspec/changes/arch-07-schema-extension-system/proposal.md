# Change: Schema Extension System for Modular ProjectBundle Extensions

## Why

Modules need a mechanism to extend ProjectBundle with custom fields without modifying core models, enabling marketplace-ready interoperability where external services (ADO, Jira, Linear) can persist metadata without core coupling. Without this, modules either duplicate schema logic or introduce tight coupling, blocking parallel development and ecosystem growth.

## What Changes

- **NEW**: Add `extensions` field to `Feature` and `ProjectBundle` models with namespace-prefixed accessors/mutators
- **NEW**: Create `src/specfact_cli/models/dynamic_extensions.py` for Pydantic dynamic model creation
- **MODIFY**: Extend module manifest schema (`module-package.yaml`) with `schema_extensions` declaration
- **MODIFY**: Extend module lifecycle registration to load and validate schema extensions from manifests
- **NEW**: Add namespace enforcement (module-prefixed fields) with static analysis guards
- **NEW**: Add documentation for extending ProjectBundle and best practices

## Capabilities

### New Capabilities

- `schema-extension-system`: Contract-driven mechanism for modules to declare and safely extend core data models with namespaced custom fields

### Modified Capabilities

- `module-packages`: Extend manifest schema with `schema_extensions` metadata for declarative field registration
- `module-lifecycle-management`: Extend registration flow to load, validate, and apply schema extensions from module manifests

## Impact

- **Affected code**:
  - `src/specfact_cli/models/project.py` (add extensions field to Feature)
  - `src/specfact_cli/models/plan.py` (add extensions field to Feature)
  - `src/specfact_cli/models/dynamic_extensions.py` (new)
  - `src/specfact_cli/registry/module_packages.py` (load schema_extensions)
- **Affected specs**: New spec for `schema-extension-system`; delta specs for `module-packages` and `module-lifecycle-management`
- **Affected documentation**:
  - `docs/guides/extending-projectbundle.md` (new)
  - `docs/reference/architecture.md` (schema extension pattern)
  - `docs/_layouts/default.html` (navigation update)
- **Integration points**: Module manifest parsing, ProjectBundle serialization/deserialization, module registration
- **Backward compatibility**: Fully backward compatible (extensions field defaults to empty dict)
- **Dependencies**: Requires arch-04 (ModuleIOContract) foundation
- **Rollback plan**: Remove extensions field, disable schema_extensions parsing in manifests

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #213
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/213>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
- **Sanitized**: false
