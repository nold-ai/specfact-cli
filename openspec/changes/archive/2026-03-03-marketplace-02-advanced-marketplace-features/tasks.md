# Implementation Tasks: marketplace-02-advanced-marketplace-features

## TDD / SDD Order (Enforced)

Per config.yaml, tests MUST come before implementation for any behavior-changing task. Order:
1. Spec deltas (already created)
2. Tests from spec scenarios (expect failure)
3. Code implementation (until tests pass and behavior satisfies spec)

Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git worktree branch from dev

- [x] 1.1 Ensure on dev and up to date; create branch `feature/marketplace-02-advanced-marketplace-features`; verify
  - [x] 1.1.1 `git checkout dev && git pull origin dev`
  - [x] 1.1.2 `scripts/worktree.sh create feature/marketplace-02-advanced-marketplace-features`
  - [x] 1.1.3 `git branch --show-current`

## 2. Implement dependency resolution (TDD)

- [x] 2.1 Write tests for dependency resolver (expect failure)
  - [x] 2.1.1 Create tests/unit/registry/test_dependency_resolver.py
  - [x] 2.1.2 Test resolve_dependencies() aggregates pip_dependencies
  - [x] 2.1.3 Test resolution succeeds without conflicts
  - [x] 2.1.4 Test conflict detection with incompatible versions
  - [x] 2.1.5 Test fallback to basic resolver when pip-tools unavailable
  - [x] 2.1.6 Test clear error messages for conflicts
  - [x] 2.1.7 Mock pip-compile execution
  - [x] 2.1.8 Run tests (expect failures)

- [x] 2.2 Create dependency_resolver.py
  - [x] 2.2.1 Create src/specfact_cli/registry/dependency_resolver.py
  - [x] 2.2.2 Implement resolve_dependencies() with pip-compile integration
  - [x] 2.2.3 Add contracts: @require valid modules list, @ensure returns list or raises
  - [x] 2.2.4 Implement fallback to basic pip resolver
  - [x] 2.2.5 Implement conflict detection with clear error messages
  - [x] 2.2.6 Add @beartype decorators
  - [x] 2.2.7 Verify tests pass

- [x] 2.3 Extend install command with dependency resolution
  - [x] 2.3.1 Modify module_installer.py to call resolve_dependencies()
  - [x] 2.3.2 Add pre-flight check before download
  - [x] 2.3.3 Add --skip-deps flag to bypass resolution
  - [x] 2.3.4 Add --force flag to ignore conflicts
  - [x] 2.3.5 Verify integration tests pass

## 3. Implement alias system (TDD)

- [x] 3.1 Write tests for alias manager (expect failure)
  - [x] 3.1.1 Create tests/unit/registry/test_alias_manager.py
  - [x] 3.1.2 Test create_alias() stores mapping
  - [x] 3.1.3 Test list_aliases() returns all aliases
  - [x] 3.1.4 Test remove_alias() deletes mapping
  - [x] 3.1.5 Test resolve_command() checks aliases first
  - [x] 3.1.6 Test warning when alias shadows built-in
  - [x] 3.1.7 Run tests (expect failures)

- [x] 3.2 Create alias_manager.py
  - [x] 3.2.1 Create src/specfact_cli/registry/alias_manager.py
  - [x] 3.2.2 Implement create_alias() with JSON storage
  - [x] 3.2.3 Add contracts: @require valid alias and command_name (alias → command name, not module_id)
  - [x] 3.2.4 Implement list_aliases() and remove_alias()
  - [x] 3.2.5 Implement resolve_command() with alias lookup (returns stored command name for dispatch)
  - [x] 3.2.6 Add built-in shadowing detection with warning
  - [x] 3.2.7 Add @beartype decorators
  - [x] 3.2.8 Verify tests pass

- [x] 3.3 Add alias commands to module module
  - [x] 3.3.1 Add alias subcommand with create/list/remove
  - [x] 3.3.2 Integrate with command resolution in registry
  - [x] 3.3.3 Verify commands work end-to-end

## 4. Implement custom registries (TDD)

- [x] 4.1 
  - [x] 4.1.1 Create tests/unit/registry/test_custom_registries.py
  - [x] 4.1.2 Test add_registry() stores config
  - [x] 4.1.3 Test list_registries() returns all configured
  - [x] 4.1.4 Test remove_registry() deletes config
  - [x] 4.1.5 Test fetch_all_indexes() queries multiple registries
  - [x] 4.1.6 Test trust level enforcement
  - [x] 4.1.7 Mock HTTP requests for multiple registries
  - [x] 4.1.8 Run tests (expect failures)

- [x] 4.2 
  - [x] 4.2.1 Create src/specfact_cli/registry/custom_registries.py
  - [x] 4.2.2 Implement YAML config storage (~/.specfact/config/registries.yaml)
  - [x] 4.2.3 Implement add_registry() with priority and trust
  - [x] 4.2.4 Add contracts: @require valid URL and trust level
  - [x] 4.2.5 Implement list_registries() and remove_registry()
  - [x] 4.2.6 Implement fetch_all_indexes() with priority ordering
  - [x] 4.2.7 Add trust level enforcement (always/prompt/never)
  - [x] 4.2.8 Add @beartype decorators
  - [x] 4.2.9 Verify tests pass

- [x] 4.3 
  - [x] 4.3.1 Modify marketplace_client.py to use custom_registries
  - [x] 4.3.2 Update fetch_registry_index() to support registry parameter
  - [x] 4.3.3 Implement search across all registries
  - [x] 4.3.4 Verify integration with install/search commands

- [x] 4.4 
  - [x] 4.4.1 Add add-registry command
  - [x] 4.4.2 Add list-registries command
  - [x] 4.4.3 Add remove-registry command
  - [x] 4.4.4 Verify commands work end-to-end

## 5. Implement namespace enforcement (TDD)

- [x] 5.1 
  - [x] 5.1.1 Add tests to test_module_lifecycle_management.py
  - [x] 5.1.2 Test namespace format validation for marketplace modules
  - [x] 5.1.3 Test namespace collision detection
  - [x] 5.1.4 Test custom modules allowed with flat names
  - [x] 5.1.5 Run tests (expect failures)

- [x] 5.2 
  - [x] 5.2.1 Add namespace validation to module_installer.py
  - [x] 5.2.2 Enforce namespace/name format for marketplace modules
  - [x] 5.2.3 Add collision detection with clear error messages
  - [x] 5.2.4 Allow flat names for custom modules with warning
  - [x] 5.2.5 Verify tests pass

## 6. Create module publishing automation

- [x] 6.1 Create publish-module.py script
  - [x] 6.1.1 Create scripts/publish-module.py
  - [x] 6.1.2 Implement module structure validation
  - [x] 6.1.3 Implement tarball creation
  - [x] 6.1.4 Implement checksum generation
  - [x] 6.1.5 Add integration with arch-06 signing (if available)
  - [x] 6.1.6 Add index.json update logic
  - [x] 6.1.7 Add contracts and @beartype
  - [x] 6.1.8 Test script manually with sample module

- [x] 6.2 Create GitHub Actions workflow
  - [x] 6.2.1 Create .github/workflows/publish-modules.yml
  - [x] 6.2.2 Configure trigger on release tag pattern
  - [x] 6.2.3 Add validation, packaging, signing steps
  - [x] 6.2.4 Add index.json update and PR creation
  - [x] 6.2.5 Test workflow with test repository
  - Validation note: local end-to-end simulation verified publish -> index update -> registry branch commit flow using a temporary `specfact-cli-modules` test repository; PR creation path is wired via `gh pr create` in workflow and requires `SPECFACT_MODULES_REPO_TOKEN` in CI.

## 7. Quality gates

- [x] 7.1 Format code
  - [x] 7.1.1 `hatch run format`

- [x] 7.2 Type checking
  - [x] 7.2.1 `hatch run type-check`
  - [x] 7.2.2 Fix any type errors

- [x] 7.3 Contract-first testing
  - [x] 7.3.1 `hatch run contract-test`
  - [x] 7.3.2 Verify all contracts pass

- [x] 7.4 Full test suite
  - [x] 7.4.1 `hatch test --cover -v`
  - [x] 7.4.2 Verify >80% coverage for new code
  - [x] 7.4.3 Fix any failing tests

- [x] 7.5 OpenSpec validation
  - [x] 7.5.1 `openspec validate marketplace-02-advanced-marketplace-features --strict`
  - [x] 7.5.2 Fix any validation errors

## 8. Documentation research and review

- [x] 8.1 Identify affected documentation
  - [x] 8.1.1 Review docs/guides/ for marketplace docs
  - [x] 8.1.2 Review docs/reference/ for architecture docs

- [x] 8.2 Create new guide: docs/guides/publishing-modules.md
  - [x] 8.2.1 Add Jekyll front-matter
  - [x] 8.2.2 Write sections: Module Structure, Publishing Process, Automation, Best Practices
  - [x] 8.2.3 Include script usage examples
  - [x] 8.2.4 Document namespace requirements

- [x] 8.3 Create new guide: docs/guides/custom-registries.md
  - [x] 8.3.1 Add Jekyll front-matter
  - [x] 8.3.2 Write sections: Adding Registries, Trust Levels, Priority, Enterprise Use
  - [x] 8.3.3 Include command examples
  - [x] 8.3.4 Document security considerations

- [x] 8.4 Create new reference: docs/reference/dependency-resolution.md
  - [x] 8.4.1 Add Jekyll front-matter
  - [x] 8.4.2 Write sections: How It Works, Conflict Detection, Bypass Options
  - [x] 8.4.3 Include pip-compile integration details

- [x] 8.5 Update existing docs
  - [x] 8.5.1 Update docs/guides/installing-modules.md with dependency resolution, aliases
  - [x] 8.5.2 Update docs/reference/architecture.md with advanced features

- [x] 8.6 Update sidebar navigation
  - [x] 8.6.1 Update docs/_layouts/default.html
  - [x] 8.6.2 Add "Publishing Modules", "Custom Registries", "Dependency Resolution"

- [x] 8.7 Verify docs build
  - [x] 8.7.1 Test markdown formatting
  - [x] 8.7.2 Check all links work

## 9. Version and changelog

- [x] 9.1 Bump version
  - [x] 9.1.1 Determine version bump: minor (new features)
  - [x] 9.1.2 Update pyproject.toml version
  - [x] 9.1.3 Update setup.py version
  - [x] 9.1.4 Update src/__init__.py version
  - [x] 9.1.5 Update src/specfact_cli/__init__.py version
  - [x] 9.1.6 Verify all versions match

- [x] 9.2 Update CHANGELOG.md
  - [x] 9.2.1 Add new section: [X.Y.Z] - YYYY-MM-DD
  - [x] 9.2.2 Add "Added" subsection with advanced marketplace features
  - [x] 9.2.3 Reference GitHub issue if created

## 10. Create PR to dev

- [x] 10.1 Prepare commit
  - [x] 10.1.1 `git add .`
  - [x] 10.1.2 Create commit with conventional message format
  - [x] 10.1.3 Include Co-Authored-By: Claude Sonnet 4.5
  - [x] 10.1.4 `git push -u origin feature/marketplace-02-advanced-marketplace-features`

- [x] 10.2 Create PR body
  - [x] 10.2.1 Copy PR template to temp file
  - [x] 10.2.2 Fill in issue reference (if exists)
  - [x] 10.2.3 Add OpenSpec change ID
  - [x] 10.2.4 Describe advanced marketplace features

- [x] 10.3 Create PR via gh CLI
  - [x] 10.3.1 `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/marketplace-02-advanced-marketplace-features --title "feat: Advanced Marketplace Features for Production Readiness" --body-file <file>`
  - [x] 10.3.2 Capture PR URL (PR #318)

- [x] 10.4 Link to project
  - [x] 10.4.1 `gh project item-add 1 --owner nold-ai --url <PR_URL>` (done by maintainer)

- [x] 10.5 Verify PR setup
  - [x] 10.5.1 Check PR shows correct base and head
  - [x] 10.5.2 Verify CI checks running
  - [x] 10.5.3 Verify project board shows PR

- [x] 10.6 Cleanup
  - [x] 10.6.1 Remove temp files

## 11. Merge to dev and release to main

- [x] 11.1 Merge feature PR to dev
  - [x] 11.1.1 PR #318 merged to dev
  - [x] 11.1.2 P1 review fixes applied (add-registry `--id` type, alias → command name, install consults custom registries)
  - [x] 11.1.3 All changes pushed to dev

- [x] 11.2 Create release PR (dev → main)
  - [x] 11.2.1 Fill .github/pull_request_template.md for v0.38.0 release
  - [x] 11.2.2 `gh pr create --base main --head dev --title "Release v0.38.0: Advanced marketplace features (dev → main)" --body-file <file>`
  - [x] 11.2.3 PR #319 created: https://github.com/nold-ai/specfact-cli/pull/319

- [x] 11.3 Merge release PR to main (when ready)
  - [ ] 11.3.1 Merge PR #319 to main
  - [ ] 11.3.2 Tag release if applicable
  - [ ] 11.3.3 Verify PyPI/CI publish if configured
