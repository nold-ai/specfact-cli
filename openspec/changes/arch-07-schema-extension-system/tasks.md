# Implementation Tasks: arch-07-schema-extension-system

## TDD / SDD Order (Enforced)

Per config.yaml, tests MUST come before implementation for any behavior-changing task. Order:
1. Spec deltas (already created)
2. Tests from spec scenarios (expect failure)
3. Code implementation (until tests pass and behavior satisfies spec)

Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git branch from dev

- [ ] 1.1 Ensure on dev and up to date; create branch `feature/arch-07-schema-extension-system`; verify
  - [ ] 1.1.1 `git checkout dev && git pull origin dev`
  - [ ] 1.1.2 `git checkout -b feature/arch-07-schema-extension-system`
  - [ ] 1.1.3 `git branch --show-current`

## 2. Add extensions field to core models (spec-first)

- [ ] 2.1 Write tests for Feature.extensions field (expect failure)
  - [ ] 2.1.1 Create `tests/unit/test_schema_extensions.py`
  - [ ] 2.1.2 Test Feature model includes extensions dict field with default empty dict
  - [ ] 2.1.3 Test extensions field serializes/deserializes with YAML and JSON
  - [ ] 2.1.4 Test backward compatibility: bundles without extensions load successfully
  - [ ] 2.1.5 Run tests: `hatch test -- tests/unit/test_schema_extensions.py -v` (expect failures)

- [ ] 2.2 Implement extensions field in Feature model (src/specfact_cli/models/plan.py)
  - [ ] 2.2.1 Add `extensions: dict[str, Any] = Field(default_factory=dict)` to Feature class
  - [ ] 2.2.2 Add contract: `@ensure(lambda self: self.extensions is not None)`
  - [ ] 2.2.3 Verify tests pass for Feature extensions

- [ ] 2.3 Write tests for ProjectBundle.extensions field (expect failure)
  - [ ] 2.3.1 Test ProjectBundle model includes extensions dict field
  - [ ] 2.3.2 Test serialization/deserialization with extensions
  - [ ] 2.3.3 Run tests (expect failures)

- [ ] 2.4 Implement extensions field in ProjectBundle model (src/specfact_cli/models/project.py)
  - [ ] 2.4.1 Add `extensions: dict[str, Any] = Field(default_factory=dict)` to ProjectBundle class
  - [ ] 2.4.2 Add contract: `@ensure(lambda self: self.extensions is not None)`
  - [ ] 2.4.3 Verify tests pass for ProjectBundle extensions

## 3. Implement type-safe extension accessors (TDD)

- [ ] 3.1 Write tests for get_extension() and set_extension() methods (expect failure)
  - [ ] 3.1.1 Test get_extension() with valid namespace returns value
  - [ ] 3.1.2 Test get_extension() with missing field returns default
  - [ ] 3.1.3 Test set_extension() stores value with namespace prefix
  - [ ] 3.1.4 Test invalid namespace format raises ValueError
  - [ ] 3.1.5 Test namespace format validation (no dots in module_name)
  - [ ] 3.1.6 Run tests (expect failures)

- [ ] 3.2 Implement get_extension() and set_extension() in Feature (src/specfact_cli/models/plan.py)
  - [ ] 3.2.1 Add `get_extension(module_name: str, field: str, default: Any = None) -> Any` method
  - [ ] 3.2.2 Add contract: `@require(lambda module_name: re.match(r'^[a-z][a-z0-9_-]*$', module_name))`
  - [ ] 3.2.3 Add contract: `@require(lambda field: re.match(r'^[a-z][a-z0-9_]*$', field))`
  - [ ] 3.2.4 Add `@beartype` decorator
  - [ ] 3.2.5 Implement: `return self.extensions.get(f"{module_name}.{field}", default)`
  - [ ] 3.2.6 Add `set_extension(module_name: str, field: str, value: Any) -> None` method
  - [ ] 3.2.7 Add same contracts as get_extension
  - [ ] 3.2.8 Add contract: `@ensure(lambda self, module_name, field: f"{module_name}.{field}" in self.extensions)`
  - [ ] 3.2.9 Implement: `self.extensions[f"{module_name}.{field}"] = value`
  - [ ] 3.2.10 Verify tests pass for Feature accessors

- [ ] 3.3 Implement get_extension() and set_extension() in ProjectBundle (src/specfact_cli/models/project.py)
  - [ ] 3.3.1 Add same methods with contracts as Feature
  - [ ] 3.3.2 Verify tests pass for ProjectBundle accessors

## 4. Extend module manifest schema (TDD)

- [ ] 4.1 Write tests for schema_extensions in ModulePackageMetadata (expect failure)
  - [ ] 4.1.1 Test manifest parses schema_extensions field
  - [ ] 4.1.2 Test schema extension includes target, field, type, description
  - [ ] 4.1.3 Test module without schema_extensions remains valid
  - [ ] 4.1.4 Run tests (expect failures)

- [ ] 4.2 Implement schema_extensions in ModulePackageMetadata (src/specfact_cli/models/module_package.py)
  - [ ] 4.2.1 Create `SchemaExtension` Pydantic model with: target (str), field (str), type_hint (str), description (str)
  - [ ] 4.2.2 Add contracts to SchemaExtension: `@require(lambda target: target in ["Feature", "ProjectBundle"])`
  - [ ] 4.2.3 Add contract: `@require(lambda field: re.match(r'^[a-z][a-z0-9_]*$', field))`
  - [ ] 4.2.4 Add `schema_extensions: list[SchemaExtension] = Field(default_factory=list)` to ModulePackageMetadata
  - [ ] 4.2.5 Verify tests pass

## 5. Implement extension registry (TDD)

- [ ] 5.1 Write tests for global extension registry (expect failure)
  - [ ] 5.1.1 Create `tests/unit/test_extension_registry.py`
  - [ ] 5.1.2 Test registry registers extension from module
  - [ ] 5.1.3 Test registry detects namespace collision
  - [ ] 5.1.4 Test registry is queryable for introspection
  - [ ] 5.1.5 Run tests (expect failures)

- [ ] 5.2 Create ExtensionRegistry class (src/specfact_cli/registry/extension_registry.py)
  - [ ] 5.2.1 Create new file with ExtensionRegistry class
  - [ ] 5.2.2 Add `_registry: dict[str, list[SchemaExtension]]` class attribute
  - [ ] 5.2.3 Implement `register(module_name: str, extensions: list[SchemaExtension]) -> None`
  - [ ] 5.2.4 Add contract: `@require(lambda module_name, extensions: not _has_collision(module_name, extensions))`
  - [ ] 5.2.5 Implement collision detection helper
  - [ ] 5.2.6 Implement `get_extensions(module_name: str) -> list[SchemaExtension]`
  - [ ] 5.2.7 Implement `list_all() -> dict[str, list[SchemaExtension]]`
  - [ ] 5.2.8 Add `@beartype` to all methods
  - [ ] 5.2.9 Verify tests pass

## 6. Extend module lifecycle registration (TDD)

- [ ] 6.1 Write tests for schema extension registration (expect failure)
  - [ ] 6.1.1 Test registration loads schema_extensions from manifest
  - [ ] 6.1.2 Test registration validates namespace uniqueness
  - [ ] 6.1.3 Test registration populates extension registry
  - [ ] 6.1.4 Test registration logs registered extensions
  - [ ] 6.1.5 Test registration skips invalid extension declarations
  - [ ] 6.1.6 Run tests (expect failures)

- [ ] 6.2 Implement schema extension loading in module_packages.py
  - [ ] 6.2.1 Modify `discover_package_metadata()` to parse schema_extensions
  - [ ] 6.2.2 Add validation: check SchemaExtension field format
  - [ ] 6.2.3 Import and call ExtensionRegistry.register() during registration
  - [ ] 6.2.4 Add error handling for namespace collisions
  - [ ] 6.2.5 Add debug logging: "Module X registered N schema extensions"
  - [ ] 6.2.6 Verify tests pass

## 7. Quality gates

- [ ] 7.1 Format code
  - [ ] 7.1.1 `hatch run format`

- [ ] 7.2 Type checking
  - [ ] 7.2.1 `hatch run type-check`
  - [ ] 7.2.2 Fix any type errors

- [ ] 7.3 Contract-first testing
  - [ ] 7.3.1 `hatch run contract-test`
  - [ ] 7.3.2 Verify all contracts pass

- [ ] 7.4 Full test suite
  - [ ] 7.4.1 `hatch test --cover -v`
  - [ ] 7.4.2 Verify >80% coverage for new code
  - [ ] 7.4.3 Fix any failing tests

- [ ] 7.5 OpenSpec validation
  - [ ] 7.5.1 `openspec validate arch-07-schema-extension-system --strict`
  - [ ] 7.5.2 Fix any validation errors

## 8. Documentation research and review

- [ ] 8.1 Identify affected documentation
  - [ ] 8.1.1 Review docs/reference/ for architecture/module docs
  - [ ] 8.1.2 Review docs/guides/ for developer guides
  - [ ] 8.1.3 Review README.md for high-level feature mentions
  - [ ] 8.1.4 Review docs/index.md for landing page updates

- [ ] 8.2 Create new guide: docs/guides/extending-projectbundle.md
  - [ ] 8.2.1 Add Jekyll front-matter: layout (default), title, permalink, description
  - [ ] 8.2.2 Write guide sections: Overview, Declaring Extensions, Using Extensions, Best Practices
  - [ ] 8.2.3 Include code examples for get_extension() and set_extension()
  - [ ] 8.2.4 Include manifest example with schema_extensions
  - [ ] 8.2.5 Document namespace rules and collision detection

- [ ] 8.3 Update docs/reference/architecture.md
  - [ ] 8.3.1 Add "Schema Extension System" section
  - [ ] 8.3.2 Document extension registry pattern
  - [ ] 8.3.3 Explain namespace enforcement and collision detection

- [ ] 8.4 Update sidebar navigation in docs/_layouts/default.html
  - [ ] 8.4.1 Add "Extending ProjectBundle" link under Guides section
  - [ ] 8.4.2 Verify link points to correct permalink

- [ ] 8.5 Verify docs build locally
  - [ ] 8.5.1 Test Jekyll build if available, or verify markdown formatting
  - [ ] 8.5.2 Check all links work

## 9. Version and changelog

- [ ] 9.1 Bump version
  - [ ] 9.1.1 Determine version bump: minor (new feature)
  - [ ] 9.1.2 Update pyproject.toml version
  - [ ] 9.1.3 Update setup.py version
  - [ ] 9.1.4 Update src/__init__.py version
  - [ ] 9.1.5 Update src/specfact_cli/__init__.py version
  - [ ] 9.1.6 Verify all versions match

- [ ] 9.2 Update CHANGELOG.md
  - [ ] 9.2.1 Add new section: [X.Y.Z] - YYYY-MM-DD
  - [ ] 9.2.2 Add "Added" subsection with schema extension system features
  - [ ] 9.2.3 Reference GitHub issue if available

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
