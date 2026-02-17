# Implementation Tasks: marketplace-02-advanced-marketplace-features

## TDD / SDD Order (Enforced)

Per config.yaml, tests MUST come before implementation for any behavior-changing task. Order:
1. Spec deltas (already created)
2. Tests from spec scenarios (expect failure)
3. Code implementation (until tests pass and behavior satisfies spec)

Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git worktree branch from dev

- [ ] 1.1 Ensure on dev and up to date; create branch `feature/marketplace-02-advanced-marketplace-features`; verify
  - [ ] 1.1.1 `git checkout dev && git pull origin dev`
  - [ ] 1.1.2 `scripts/worktree.sh create feature/marketplace-02-advanced-marketplace-features`
  - [ ] 1.1.3 `git branch --show-current`

## 2. Implement dependency resolution (TDD)

- [ ] 2.1 Write tests for dependency resolver (expect failure)
  - [ ] 2.1.1 Create tests/unit/registry/test_dependency_resolver.py
  - [ ] 2.1.2 Test resolve_dependencies() aggregates pip_dependencies
  - [ ] 2.1.3 Test resolution succeeds without conflicts
  - [ ] 2.1.4 Test conflict detection with incompatible versions
  - [ ] 2.1.5 Test fallback to basic resolver when pip-tools unavailable
  - [ ] 2.1.6 Test clear error messages for conflicts
  - [ ] 2.1.7 Mock pip-compile execution
  - [ ] 2.1.8 Run tests (expect failures)

- [ ] 2.2 Create dependency_resolver.py
  - [ ] 2.2.1 Create src/specfact_cli/registry/dependency_resolver.py
  - [ ] 2.2.2 Implement resolve_dependencies() with pip-compile integration
  - [ ] 2.2.3 Add contracts: @require valid modules list, @ensure returns list or raises
  - [ ] 2.2.4 Implement fallback to basic pip resolver
  - [ ] 2.2.5 Implement conflict detection with clear error messages
  - [ ] 2.2.6 Add @beartype decorators
  - [ ] 2.2.7 Verify tests pass

- [ ] 2.3 Extend install command with dependency resolution
  - [ ] 2.3.1 Modify module_installer.py to call resolve_dependencies()
  - [ ] 2.3.2 Add pre-flight check before download
  - [ ] 2.3.3 Add --skip-deps flag to bypass resolution
  - [ ] 2.3.4 Add --force flag to ignore conflicts
  - [ ] 2.3.5 Verify integration tests pass

## 3. Implement alias system (TDD)

- [ ] 3.1 Write tests for alias manager (expect failure)
  - [ ] 3.1.1 Create tests/unit/registry/test_alias_manager.py
  - [ ] 3.1.2 Test create_alias() stores mapping
  - [ ] 3.1.3 Test list_aliases() returns all aliases
  - [ ] 3.1.4 Test remove_alias() deletes mapping
  - [ ] 3.1.5 Test resolve_command() checks aliases first
  - [ ] 3.1.6 Test warning when alias shadows built-in
  - [ ] 3.1.7 Run tests (expect failures)

- [ ] 3.2 Create alias_manager.py
  - [ ] 3.2.1 Create src/specfact_cli/registry/alias_manager.py
  - [ ] 3.2.2 Implement create_alias() with JSON storage
  - [ ] 3.2.3 Add contracts: @require valid alias and module_id format
  - [ ] 3.2.4 Implement list_aliases() and remove_alias()
  - [ ] 3.2.5 Implement resolve_command() with alias lookup
  - [ ] 3.2.6 Add built-in shadowing detection with warning
  - [ ] 3.2.7 Add @beartype decorators
  - [ ] 3.2.8 Verify tests pass

- [ ] 3.3 Add alias commands to module module
  - [ ] 3.3.1 Add alias subcommand with create/list/remove
  - [ ] 3.3.2 Integrate with command resolution in registry
  - [ ] 3.3.3 Verify commands work end-to-end

## 4. Implement custom registries (TDD)

- [ ] 4.1 Write tests for custom registries (expect failure)
  - [ ] 4.1.1 Create tests/unit/registry/test_custom_registries.py
  - [ ] 4.1.2 Test add_registry() stores config
  - [ ] 4.1.3 Test list_registries() returns all configured
  - [ ] 4.1.4 Test remove_registry() deletes config
  - [ ] 4.1.5 Test fetch_all_indexes() queries multiple registries
  - [ ] 4.1.6 Test trust level enforcement
  - [ ] 4.1.7 Mock HTTP requests for multiple registries
  - [ ] 4.1.8 Run tests (expect failures)

- [ ] 4.2 Create custom_registries.py
  - [ ] 4.2.1 Create src/specfact_cli/registry/custom_registries.py
  - [ ] 4.2.2 Implement YAML config storage (~/.specfact/config/registries.yaml)
  - [ ] 4.2.3 Implement add_registry() with priority and trust
  - [ ] 4.2.4 Add contracts: @require valid URL and trust level
  - [ ] 4.2.5 Implement list_registries() and remove_registry()
  - [ ] 4.2.6 Implement fetch_all_indexes() with priority ordering
  - [ ] 4.2.7 Add trust level enforcement (always/prompt/never)
  - [ ] 4.2.8 Add @beartype decorators
  - [ ] 4.2.9 Verify tests pass

- [ ] 4.3 Extend marketplace client for multi-registry
  - [ ] 4.3.1 Modify marketplace_client.py to use custom_registries
  - [ ] 4.3.2 Update fetch_registry_index() to support registry parameter
  - [ ] 4.3.3 Implement search across all registries
  - [ ] 4.3.4 Verify integration with install/search commands

- [ ] 4.4 Add registry commands to module module
  - [ ] 4.4.1 Add add-registry command
  - [ ] 4.4.2 Add list-registries command
  - [ ] 4.4.3 Add remove-registry command
  - [ ] 4.4.4 Verify commands work end-to-end

## 5. Implement namespace enforcement (TDD)

- [ ] 5.1 Write tests for namespace validation (expect failure)
  - [ ] 5.1.1 Add tests to test_module_lifecycle_management.py
  - [ ] 5.1.2 Test namespace format validation for marketplace modules
  - [ ] 5.1.3 Test namespace collision detection
  - [ ] 5.1.4 Test custom modules allowed with flat names
  - [ ] 5.1.5 Run tests (expect failures)

- [ ] 5.2 Implement namespace enforcement
  - [ ] 5.2.1 Add namespace validation to module_installer.py
  - [ ] 5.2.2 Enforce namespace/name format for marketplace modules
  - [ ] 5.2.3 Add collision detection with clear error messages
  - [ ] 5.2.4 Allow flat names for custom modules with warning
  - [ ] 5.2.5 Verify tests pass

## 6. Create module publishing automation

- [ ] 6.1 Create publish-module.py script
  - [ ] 6.1.1 Create scripts/publish-module.py
  - [ ] 6.1.2 Implement module structure validation
  - [ ] 6.1.3 Implement tarball creation
  - [ ] 6.1.4 Implement checksum generation
  - [ ] 6.1.5 Add integration with arch-06 signing (if available)
  - [ ] 6.1.6 Add index.json update logic
  - [ ] 6.1.7 Add contracts and @beartype
  - [ ] 6.1.8 Test script manually with sample module

- [ ] 6.2 Create GitHub Actions workflow
  - [ ] 6.2.1 Create .github/workflows/publish-modules.yml
  - [ ] 6.2.2 Configure trigger on release tag pattern
  - [ ] 6.2.3 Add validation, packaging, signing steps
  - [ ] 6.2.4 Add index.json update and PR creation
  - [ ] 6.2.5 Test workflow with test repository

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
  - [ ] 7.5.1 `openspec validate marketplace-02-advanced-marketplace-features --strict`
  - [ ] 7.5.2 Fix any validation errors

## 8. Documentation research and review

- [ ] 8.1 Identify affected documentation
  - [ ] 8.1.1 Review docs/guides/ for marketplace docs
  - [ ] 8.1.2 Review docs/reference/ for architecture docs

- [ ] 8.2 Create new guide: docs/guides/publishing-modules.md
  - [ ] 8.2.1 Add Jekyll front-matter
  - [ ] 8.2.2 Write sections: Module Structure, Publishing Process, Automation, Best Practices
  - [ ] 8.2.3 Include script usage examples
  - [ ] 8.2.4 Document namespace requirements

- [ ] 8.3 Create new guide: docs/guides/custom-registries.md
  - [ ] 8.3.1 Add Jekyll front-matter
  - [ ] 8.3.2 Write sections: Adding Registries, Trust Levels, Priority, Enterprise Use
  - [ ] 8.3.3 Include command examples
  - [ ] 8.3.4 Document security considerations

- [ ] 8.4 Create new reference: docs/reference/dependency-resolution.md
  - [ ] 8.4.1 Add Jekyll front-matter
  - [ ] 8.4.2 Write sections: How It Works, Conflict Detection, Bypass Options
  - [ ] 8.4.3 Include pip-compile integration details

- [ ] 8.5 Update existing docs
  - [ ] 8.5.1 Update docs/guides/installing-modules.md with dependency resolution, aliases
  - [ ] 8.5.2 Update docs/reference/architecture.md with advanced features

- [ ] 8.6 Update sidebar navigation
  - [ ] 8.6.1 Update docs/_layouts/default.html
  - [ ] 8.6.2 Add "Publishing Modules", "Custom Registries", "Dependency Resolution"

- [ ] 8.7 Verify docs build
  - [ ] 8.7.1 Test markdown formatting
  - [ ] 8.7.2 Check all links work

## 9. Version and changelog

- [ ] 9.1 Bump version
  - [ ] 9.1.1 Determine version bump: minor (new features)
  - [ ] 9.1.2 Update pyproject.toml version
  - [ ] 9.1.3 Update setup.py version
  - [ ] 9.1.4 Update src/__init__.py version
  - [ ] 9.1.5 Update src/specfact_cli/__init__.py version
  - [ ] 9.1.6 Verify all versions match

- [ ] 9.2 Update CHANGELOG.md
  - [ ] 9.2.1 Add new section: [X.Y.Z] - YYYY-MM-DD
  - [ ] 9.2.2 Add "Added" subsection with advanced marketplace features
  - [ ] 9.2.3 Reference GitHub issue if created

## 10. Create PR to dev

- [ ] 10.1 Prepare commit
  - [ ] 10.1.1 `git add .`
  - [ ] 10.1.2 Create commit with conventional message format
  - [ ] 10.1.3 Include Co-Authored-By: Claude Sonnet 4.5
  - [ ] 10.1.4 `git push -u origin feature/marketplace-02-advanced-marketplace-features`

- [ ] 10.2 Create PR body
  - [ ] 10.2.1 Copy PR template to temp file
  - [ ] 10.2.2 Fill in issue reference (if exists)
  - [ ] 10.2.3 Add OpenSpec change ID
  - [ ] 10.2.4 Describe advanced marketplace features

- [ ] 10.3 Create PR via gh CLI
  - [ ] 10.3.1 `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/marketplace-02-advanced-marketplace-features --title "feat: Advanced Marketplace Features for Production Readiness" --body-file <file>`
  - [ ] 10.3.2 Capture PR URL

- [ ] 10.4 Link to project
  - [ ] 10.4.1 `gh project item-add 1 --owner nold-ai --url <PR_URL>`

- [ ] 10.5 Verify PR setup
  - [ ] 10.5.1 Check PR shows correct base and head
  - [ ] 10.5.2 Verify CI checks running
  - [ ] 10.5.3 Verify project board shows PR

- [ ] 10.6 Cleanup
  - [ ] 10.6.1 Remove temp files
