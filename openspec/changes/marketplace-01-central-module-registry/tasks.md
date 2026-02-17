# Implementation Tasks: marketplace-01-central-module-registry

## TDD / SDD Order (Enforced)

Per config.yaml, tests MUST come before implementation for any behavior-changing task. Order:
1. Spec deltas (already created)
2. Tests from spec scenarios (expect failure)
3. Code implementation (until tests pass and behavior satisfies spec)

Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git worktree branch from dev

- [ ] 1.1 Ensure on dev and up to date; create branch `feature/marketplace-01-central-module-registry`; verify
  - [ ] 1.1.1 `git checkout dev && git pull origin dev`
  - [ ] 1.1.2 `scripts/worktree.sh create feature/marketplace-01-central-module-registry`
  - [ ] 1.1.3 `git branch --show-current`

## 2. Create nold-ai/specfact-cli-modules repository

- [ ] 2.1 Create GitHub repository
  - [ ] 2.1.1 Create repository via GitHub web UI or gh CLI
  - [ ] 2.1.2 Set description: "Central module registry for SpecFact CLI marketplace"
  - [ ] 2.1.3 Add MIT license
  - [ ] 2.1.4 Create initial README.md

- [ ] 2.2 Set up registry structure
  - [ ] 2.2.1 Create registry/index.json with schema_version and empty modules array
  - [ ] 2.2.2 Create registry/modules/ directory
  - [ ] 2.2.3 Create registry/signatures/ directory
  - [ ] 2.2.4 Create docs/ directory with module-publishing-guide.md template
  - [ ] 2.2.5 Commit and push: "Initialize module registry structure"

## 3. Implement multi-location discovery (TDD)

- [ ] 3.1 Write tests for multi-location discovery (expect failure)
  - [ ] 3.1.1 Create tests/unit/registry/test_module_discovery.py
  - [ ] 3.1.2 Test discover_all_modules() scans built-in path
  - [ ] 3.1.3 Test discover_all_modules() scans marketplace path if exists
  - [ ] 3.1.4 Test discover_all_modules() scans custom path if exists
  - [ ] 3.1.5 Test built-in modules take priority over marketplace
  - [ ] 3.1.6 Test graceful handling of missing marketplace/custom paths
  - [ ] 3.1.7 Run tests (expect failures)

- [ ] 3.2 Create module_discovery.py
  - [ ] 3.2.1 Create src/specfact_cli/registry/module_discovery.py
  - [ ] 3.2.2 Implement discover_all_modules() with multi-path scanning
  - [ ] 3.2.3 Add contracts: @require paths are valid, @ensure returns list
  - [ ] 3.2.4 Add @beartype decorators
  - [ ] 3.2.5 Implement priority order (built-in → marketplace → custom)
  - [ ] 3.2.6 Add source tracking to metadata
  - [ ] 3.2.7 Verify tests pass

- [ ] 3.3 Update module_packages.py to use multi-location discovery
  - [ ] 3.3.1 Modify discover_package_metadata() to accept source parameter
  - [ ] 3.3.2 Update registration to use discover_all_modules()
  - [ ] 3.3.3 Store source in module metadata
  - [ ] 3.3.4 Verify existing functionality preserved

## 4. Implement marketplace client (TDD)

- [ ] 4.1 Write tests for marketplace client (expect failure)
  - [ ] 4.1.1 Create tests/unit/registry/test_marketplace_client.py
  - [ ] 4.1.2 Test fetch_registry_index() fetches and parses index.json
  - [ ] 4.1.3 Test graceful handling of network unavailable
  - [ ] 4.1.4 Test invalid JSON raises ValueError
  - [ ] 4.1.5 Test download_module() downloads tarball
  - [ ] 4.1.6 Test checksum verification
  - [ ] 4.1.7 Test checksum mismatch raises SecurityError
  - [ ] 4.1.8 Mock HTTP requests with responses library
  - [ ] 4.1.9 Run tests (expect failures)

- [ ] 4.2 Create marketplace_client.py
  - [ ] 4.2.1 Create src/specfact_cli/registry/marketplace_client.py
  - [ ] 4.2.2 Implement fetch_registry_index() with requests library
  - [ ] 4.2.3 Add contracts: @ensure returns dict or None
  - [ ] 4.2.4 Implement download_module() with checksum verification
  - [ ] 4.2.5 Add contracts: @require module_id format, @ensure returns Path
  - [ ] 4.2.6 Add @beartype decorators
  - [ ] 4.2.7 Implement offline fallback (log warning, return None)
  - [ ] 4.2.8 Verify tests pass

## 5. Implement module installer (TDD)

- [ ] 5.1 Write tests for module installer (expect failure)
  - [ ] 5.1.1 Create tests/unit/registry/test_module_installer.py
  - [ ] 5.1.2 Test install_module() downloads, verifies, extracts, registers
  - [ ] 5.1.3 Test install to ~/.specfact/marketplace-modules/
  - [ ] 5.1.4 Test module already installed scenario
  - [ ] 5.1.5 Test uninstall_module() removes marketplace module
  - [ ] 5.1.6 Test uninstall built-in module raises error
  - [ ] 5.1.7 Test core compatibility validation
  - [ ] 5.1.8 Run tests (expect failures)

- [ ] 5.2 Create module_installer.py
  - [ ] 5.2.1 Create src/specfact_cli/registry/module_installer.py
  - [ ] 5.2.2 Implement install_module() workflow (download → verify → extract → register)
  - [ ] 5.2.3 Add contracts: @require valid module_id, @ensure module registered
  - [ ] 5.2.4 Implement uninstall_module() with source check
  - [ ] 5.2.5 Add contracts: @require module exists, @ensure removed if marketplace
  - [ ] 5.2.6 Add @beartype decorators
  - [ ] 5.2.7 Implement atomic install (rollback on failure)
  - [ ] 5.2.8 Verify tests pass

## 6. Create module management CLI commands (TDD)

- [ ] 6.1 Write tests for module commands (expect failure)
  - [ ] 6.1.1 Create tests/unit/modules/module/test_commands.py
  - [ ] 6.1.2 Test install command integration
  - [ ] 6.1.3 Test uninstall command with source validation
  - [ ] 6.1.4 Test search command filters registry
  - [ ] 6.1.5 Test list command shows all sources
  - [ ] 6.1.6 Test list --source filter
  - [ ] 6.1.7 Test upgrade command
  - [ ] 6.1.8 Mock CliRunner for Typer commands
  - [ ] 6.1.9 Run tests (expect failures)

- [ ] 6.2 Create module module structure
  - [ ] 6.2.1 Create src/specfact_cli/modules/module/ directory
  - [ ] 6.2.2 Create module-package.yaml with name, version, commands
  - [ ] 6.2.3 Create src/ directory
  - [ ] 6.2.4 Create __init__.py

- [ ] 6.3 Implement module commands
  - [ ] 6.3.1 Create src/commands.py with Typer app
  - [ ] 6.3.2 Implement install command with module_id argument, version option
  - [ ] 6.3.3 Implement uninstall command with source check
  - [ ] 6.3.4 Implement search command with query argument
  - [ ] 6.3.5 Implement list command with --source option
  - [ ] 6.3.6 Implement upgrade command
  - [ ] 6.3.7 Add @beartype to all commands
  - [ ] 6.3.8 Use Rich Console for output formatting
  - [ ] 6.3.9 Verify tests pass

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
  - [ ] 7.5.1 `openspec validate marketplace-01-central-module-registry --strict`
  - [ ] 7.5.2 Fix any validation errors

## 8. Documentation research and review

- [ ] 8.1 Identify affected documentation
  - [ ] 8.1.1 Review docs/guides/ for module management docs
  - [ ] 8.1.2 Review docs/reference/ for architecture docs
  - [ ] 8.1.3 Review README.md for marketplace feature mention

- [ ] 8.2 Create new guide: docs/guides/installing-modules.md
  - [ ] 8.2.1 Add Jekyll front-matter (layout, title, permalink, description)
  - [ ] 8.2.2 Write sections: Installing from Marketplace, Listing Modules, Uninstalling, Upgrading
  - [ ] 8.2.3 Include command examples with output
  - [ ] 8.2.4 Document offline behavior

- [ ] 8.3 Create new guide: docs/guides/module-marketplace.md
  - [ ] 8.3.1 Add Jekyll front-matter
  - [ ] 8.3.2 Write sections: Marketplace Overview, Official Modules, Security Model, Custom Modules
  - [ ] 8.3.3 Link to registry repository
  - [ ] 8.3.4 Explain namespace system (specfact/*)

- [ ] 8.4 Update docs/reference/architecture.md
  - [ ] 8.4.1 Add "Module Marketplace" section
  - [ ] 8.4.2 Document multi-location discovery pattern
  - [ ] 8.4.3 Document registry client architecture
  - [ ] 8.4.4 Include sequence diagram for install workflow

- [ ] 8.5 Update sidebar navigation
  - [ ] 8.5.1 Update docs/_layouts/default.html
  - [ ] 8.5.2 Add "Installing Modules" under Guides
  - [ ] 8.5.3 Add "Module Marketplace" under Guides

- [ ] 8.6 Verify docs build
  - [ ] 8.6.1 Test markdown formatting
  - [ ] 8.6.2 Check all links work

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
  - [ ] 9.2.2 Add "Added" subsection with marketplace features
  - [ ] 9.2.3 Reference GitHub issue if created

## 10. Create PR to dev

- [ ] 10.1 Prepare commit
  - [ ] 10.1.1 `git add .`
  - [ ] 10.1.2 Create commit with conventional message format
  - [ ] 10.1.3 Include Co-Authored-By: Claude Sonnet 4.5
  - [ ] 10.1.4 `git push -u origin feature/marketplace-01-central-module-registry`

- [ ] 10.2 Create PR body
  - [ ] 10.2.1 Copy PR template to temp file
  - [ ] 10.2.2 Fill in issue reference (if exists)
  - [ ] 10.2.3 Add OpenSpec change ID
  - [ ] 10.2.4 Describe marketplace infrastructure

- [ ] 10.3 Create PR via gh CLI
  - [ ] 10.3.1 `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/marketplace-01-central-module-registry --title "feat: Central Module Registry MVP for Official Modules" --body-file <file>`
  - [ ] 10.3.2 Capture PR URL

- [ ] 10.4 Link to project
  - [ ] 10.4.1 `gh project item-add 1 --owner nold-ai --url <PR_URL>`

- [ ] 10.5 Verify PR setup
  - [ ] 10.5.1 Check PR shows correct base and head
  - [ ] 10.5.2 Verify CI checks running
  - [ ] 10.5.3 Verify project board shows PR

- [ ] 10.6 Cleanup
  - [ ] 10.6.1 Remove temp files
