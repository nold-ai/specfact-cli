# Implementation Tasks: arch-07-schema-extension-system

## TDD / SDD Order (Enforced)

Per config.yaml, tests MUST come before implementation for any behavior-changing task. Order:
1. Spec deltas (already created)
2. Tests from spec scenarios (expect failure)
3. Code implementation (until tests pass and behavior satisfies spec)

Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git branch from dev

- [x] 1.1 Ensure on dev and up to date; create branch `feature/arch-07-schema-extension-system`; verify
  - [x] 1.1.1 `git checkout dev && git pull origin dev`
  - [x] 1.1.2 `git checkout -b feature/arch-07-schema-extension-system`
  - [x] 1.1.3 `git branch --show-current`

## 2. Add extensions field to core models (spec-first)

- [x] 2.1 Write tests for Feature.extensions field (expect failure)
  - [ ] 2.1.1 Create `tests/unit/test_schema_extensions.py`
  - [ ] 2.1.2 Test Feature model includes extensions dict field with default empty dict
  - [ ] 2.1.3 Test extensions field serializes/deserializes with YAML and JSON
  - [ ] 2.1.4 Test backward compatibility: bundles without extensions load successfully
  - [x] 2.1.5 Run tests: `hatch test -- tests/unit/test_schema_extensions.py -v` (expect failures)

- [x] 2.2 Implement extensions field in Feature model (src/specfact_cli/models/plan.py)
  - [x] 2.2.1 Add `extensions: dict[str, Any] = Field(default_factory=dict)` to Feature class
  - [x] 2.2.2 Add contract: `@ensure(lambda self: self.extensions is not None)`
  - [x] 2.2.3 Verify tests pass for Feature extensions

- [x] 2.3 Write tests for ProjectBundle.extensions field (expect failure)
  - [x] 2.3.1 Test ProjectBundle model includes extensions dict field
  - [x] 2.3.2 Test serialization/deserialization with extensions
  - [x] 2.3.3 Run tests (expect failures)

- [x] 2.4 Implement extensions field in ProjectBundle model (src/specfact_cli/models/project.py)
  - [x] 2.4.1 Add `extensions: dict[str, Any] = Field(default_factory=dict)` to ProjectBundle class
  - [x] 2.4.2 Add contract: `@ensure(lambda self: self.extensions is not None)`
  - [x] 2.4.3 Verify tests pass for ProjectBundle extensions

## 3. Implement type-safe extension accessors (TDD)

- [x] 3.1 Write tests for get_extension() and set_extension() methods (expect failure)
  - [ ] 3.1.1 Test get_extension() with valid namespace returns value
  - [ ] 3.1.2 Test get_extension() with missing field returns default
  - [ ] 3.1.3 Test set_extension() stores value with namespace prefix
  - [ ] 3.1.4 Test invalid namespace format raises ValueError
  - [ ] 3.1.5 Test namespace format validation (no dots in module_name)
  - [x] 3.1.6 Run tests (expect failures)

- [x] 3.2 Implement get_extension() and set_extension() in Feature (src/specfact_cli/models/plan.py)
  - [x] 3.2.1–3.2.10 (accessors with contracts and beartype)

- [x] 3.3 Implement get_extension() and set_extension() in ProjectBundle (src/specfact_cli/models/project.py)
  - [x] 3.3.1–3.3.2

## 4. Extend module manifest schema (TDD)

- [x] 4.1 Write tests for schema_extensions in ModulePackageMetadata (expect failure)
- [x] 4.2 Implement schema_extensions in ModulePackageMetadata (src/specfact_cli/models/module_package.py)
  - [x] 4.2.1–4.2.5 (SchemaExtension model, ModulePackageMetadata.schema_extensions)

## 5. Implement extension registry (TDD)

- [x] 5.1 Write tests for global extension registry (expect failure)
- [x] 5.2 Create ExtensionRegistry class (src/specfact_cli/registry/extension_registry.py)
  - [x] 5.2.1–5.2.9

## 6. Extend module lifecycle registration (TDD)

- [x] 6.1 Write tests for schema extension registration (expect failure)
- [x] 6.2 Implement schema extension loading in module_packages.py
  - [x] 6.2.1–6.2.6

## 7. Quality gates

- [x] 7.1 Format code
  - [x] 7.1.1 `hatch run format`

- [x] 7.2 Type checking
- [x] 7.3 Contract-first testing
- [x] 7.4 Full test suite (models + registry: 252 passed, 1 skipped)
- [x] 7.5 OpenSpec validation

## 8. Documentation research and review

- [x] 8.1 Identify affected documentation
- [x] 8.2 Create new guide: docs/guides/extending-projectbundle.md
- [x] 8.3 Update docs/reference/architecture.md (Schema Extension System section)
- [x] 8.4 Update sidebar navigation in docs/_layouts/default.html
- [x] 8.5 Verify docs (markdown and links)

## 9. Version and changelog

- [x] 9.1 Bump version to 0.32.0 (pyproject.toml, setup.py, src/__init__.py, src/specfact_cli/__init__.py)
- [x] 9.2 Update CHANGELOG.md ([0.32.0] - 2026-02-16, Added schema extension system, #213)

## 10. Create PR to dev

- [ ] 10.1 Prepare commit
  - [ ] 10.1.1 `git add .`
  - [ ] 10.1.2 `git commit -m "$(cat <<'EOF'`
    ```
    feat: add schema extension system for modular ProjectBundle extensions

    Enables modules to extend Feature and ProjectBundle with namespaced custom
    fields without modifying core models, supporting marketplace-ready
    interoperability.

    - Add extensions dict field to Feature and ProjectBundle models
    - Implement type-safe get/set extension accessors with namespace enforcement
    - Extend module manifest schema with schema_extensions declaration
    - Add ExtensionRegistry for collision detection and introspection
    - Extend module lifecycle registration to load and validate extensions

    OpenSpec Change: arch-07-schema-extension-system

    Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
    EOF
    )"`
  - [ ] 10.1.3 `git push -u origin feature/arch-07-schema-extension-system`

- [ ] 10.2 Create PR body from template
  - [ ] 10.2.1 Copy `.github/pull_request_template.md` to `/tmp/pr-body-arch-07.md`
  - [ ] 10.2.2 Fill in: Fixes nold-ai/specfact-cli#<issue-number> (if exists)
  - [ ] 10.2.3 Add OpenSpec change ID: arch-07-schema-extension-system
  - [ ] 10.2.4 Describe changes, testing, and documentation updates

- [ ] 10.3 Create PR via gh CLI
  - [ ] 10.3.1 `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/arch-07-schema-extension-system --title "feat: Schema Extension System for Modular ProjectBundle Extensions" --body-file /tmp/pr-body-arch-07.md`
  - [ ] 10.3.2 Capture PR URL from output

- [ ] 10.4 Link to project
  - [ ] 10.4.1 `gh project item-add 1 --owner nold-ai --url <PR_URL>`

- [ ] 10.5 Verify PR setup
  - [ ] 10.5.1 Check PR shows correct base (dev) and head branch
  - [ ] 10.5.2 Verify CI checks are running
  - [ ] 10.5.3 Verify project board shows PR

- [ ] 10.6 Cleanup
  - [ ] 10.6.1 `rm /tmp/pr-body-arch-07.md`
