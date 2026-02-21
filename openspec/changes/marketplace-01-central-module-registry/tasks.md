# Implementation Tasks: marketplace-01-central-module-registry

## TDD / SDD Order (Enforced)

Per config.yaml, tests MUST come before implementation for any behavior-changing task. Order:
1. Spec deltas (already created)
2. Tests from spec scenarios (expect failure)
3. Code implementation (until tests pass and behavior satisfies spec)

Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git worktree branch from dev

- [x] 1.1 Ensure on dev and up to date; create branch `feature/marketplace-01-central-module-registry`; verify
  - [x] 1.1.1 `git checkout dev && git pull origin dev`
  - [x] 1.1.2 `scripts/worktree.sh create feature/marketplace-01-central-module-registry`
  - [x] 1.1.3 `git branch --show-current`

## 2. Create nold-ai/specfact-cli-modules repository

- [x] 2.1 Create GitHub repository
  - [x] 2.1.1 Create repository via GitHub web UI or gh CLI
  - [x] 2.1.2 Set description: "Central module registry for SpecFact CLI marketplace"
  - [x] 2.1.3 Add MIT license
  - [x] 2.1.4 Create initial README.md

- [x] 2.2 Set up registry structure
  - [x] 2.2.1 Create registry/index.json with schema_version and empty modules array
  - [x] 2.2.2 Create registry/modules/ directory
  - [x] 2.2.3 Create registry/signatures/ directory
  - [x] 2.2.4 Create docs/ directory with module-publishing-guide.md template
  - [x] 2.2.5 Commit and push: "Initialize module registry structure"

## 3. Implement multi-location discovery (TDD)

- [x] 3.1 Write tests for multi-location discovery (expect failure)
  - [x] 3.1.1 Create tests/unit/registry/test_module_discovery.py
  - [x] 3.1.2 Test discover_all_modules() scans built-in path
  - [x] 3.1.3 Test discover_all_modules() scans marketplace path if exists
  - [x] 3.1.4 Test discover_all_modules() scans custom path if exists
  - [x] 3.1.5 Test built-in modules take priority over marketplace
  - [x] 3.1.6 Test graceful handling of missing marketplace/custom paths
  - [x] 3.1.7 Run tests (expect failures)

- [x] 3.2 Create module_discovery.py
  - [x] 3.2.1 Create src/specfact_cli/registry/module_discovery.py
  - [x] 3.2.2 Implement discover_all_modules() with multi-path scanning
  - [x] 3.2.3 Add contracts: @require paths are valid, @ensure returns list
  - [x] 3.2.4 Add @beartype decorators
  - [x] 3.2.5 Implement priority order (built-in → marketplace → custom)
  - [x] 3.2.6 Add source tracking to metadata
  - [x] 3.2.7 Verify tests pass

- [x] 3.3 Update module_packages.py to use multi-location discovery
  - [x] 3.3.1 Modify discover_package_metadata() to accept source parameter
  - [x] 3.3.2 Update registration to use discover_all_modules()
  - [x] 3.3.3 Store source in module metadata
  - [x] 3.3.4 Verify existing functionality preserved

## 4. Implement marketplace client (TDD)

- [x] 4.1 Write tests for marketplace client (expect failure)
  - [x] 4.1.1 Create tests/unit/registry/test_marketplace_client.py
  - [x] 4.1.2 Test fetch_registry_index() fetches and parses index.json
  - [x] 4.1.3 Test graceful handling of network unavailable
  - [x] 4.1.4 Test invalid JSON raises ValueError
  - [x] 4.1.5 Test download_module() downloads tarball
  - [x] 4.1.6 Test checksum verification
  - [x] 4.1.7 Test checksum mismatch raises SecurityError
  - [x] 4.1.8 Mock HTTP requests with responses library
  - [x] 4.1.9 Run tests (expect failures)

- [x] 4.2 Create marketplace_client.py
  - [x] 4.2.1 Create src/specfact_cli/registry/marketplace_client.py
  - [x] 4.2.2 Implement fetch_registry_index() with requests library
  - [x] 4.2.3 Add contracts: @ensure returns dict or None
  - [x] 4.2.4 Implement download_module() with checksum verification
  - [x] 4.2.5 Add contracts: @require module_id format, @ensure returns Path
  - [x] 4.2.6 Add @beartype decorators
  - [x] 4.2.7 Implement offline fallback (log warning, return None)
  - [x] 4.2.8 Verify tests pass

## 5. Implement module installer (TDD)

- [x] 5.1 Write tests for module installer (expect failure)
  - [x] 5.1.1 Create tests/unit/registry/test_module_installer.py
  - [x] 5.1.2 Test install_module() downloads, verifies, extracts, registers
  - [x] 5.1.3 Test install to ~/.specfact/marketplace-modules/
  - [x] 5.1.4 Test module already installed scenario
  - [x] 5.1.5 Test uninstall_module() removes marketplace module
  - [x] 5.1.6 Test uninstall built-in module raises error
  - [x] 5.1.7 Test core compatibility validation
  - [x] 5.1.8 Run tests (expect failures)

- [x] 5.2 Create module_installer.py
  - [x] 5.2.1 Create src/specfact_cli/registry/module_installer.py
  - [x] 5.2.2 Implement install_module() workflow (download → verify → extract → register)
  - [x] 5.2.3 Add contracts: @require valid module_id, @ensure module registered
  - [x] 5.2.4 Implement uninstall_module() with source check
  - [x] 5.2.5 Add contracts: @require module exists, @ensure removed if marketplace
  - [x] 5.2.6 Add @beartype decorators
  - [x] 5.2.7 Implement atomic install (rollback on failure)
  - [x] 5.2.8 Verify tests pass

## 6. Create module management CLI commands (TDD)

- [x] 6.1 Write tests for module commands (expect failure)
  - [x] 6.1.1 Create tests/unit/modules/module/test_commands.py
  - [x] 6.1.2 Test install command integration
  - [x] 6.1.3 Test uninstall command with source validation
  - [x] 6.1.4 Test search command filters registry
  - [x] 6.1.5 Test list command shows all sources
  - [x] 6.1.6 Test list --source filter
  - [x] 6.1.7 Test upgrade command
  - [x] 6.1.8 Mock CliRunner for Typer commands
  - [x] 6.1.9 Run tests (expect failures)

- [x] 6.2 Create module module structure
  - [x] 6.2.1 Create src/specfact_cli/modules/module/ directory
  - [x] 6.2.2 Create module-package.yaml with name, version, commands
  - [x] 6.2.3 Create src/ directory
  - [x] 6.2.4 Create __init__.py

- [x] 6.3 Implement module commands
  - [x] 6.3.1 Create src/commands.py with Typer app
  - [x] 6.3.2 Implement install command with module_id argument, version option
  - [x] 6.3.3 Implement uninstall command with source check
  - [x] 6.3.4 Implement search command with query argument
  - [x] 6.3.5 Implement list command with --source option
  - [x] 6.3.6 Implement upgrade command
  - [x] 6.3.7 Add @beartype to all commands
  - [x] 6.3.8 Use Rich Console for output formatting
  - [x] 6.3.9 Verify tests pass

## 6.4 Harmonize init/module lifecycle UX (TDD)

- [x] 6.4.1 Write tests first for compatibility + canonical UX
  - [x] 6.4.1.1 Add test: `specfact module --help` loads without relative-import errors in lazy loader path
  - [x] 6.4.1.2 Add test: `specfact init --list-modules` remains functional but emits deprecation guidance toward `specfact module list`
  - [x] 6.4.1.3 Add test: `specfact init --enable-module/--disable-module` remain functional aliases with deprecation guidance
  - [x] 6.4.1.4 Run tests and capture failing evidence in TDD_EVIDENCE.md

- [x] 6.4.2 Implement non-breaking harmonization
  - [x] 6.4.2.1 Use `module-registry` as module identity; keep command name `module`
  - [x] 6.4.2.2 Ensure module entrypoint imports are robust under lazy file-based loading
  - [x] 6.4.2.3 Keep init lifecycle flags as deprecated aliases; avoid behavior regressions
  - [x] 6.4.2.4 Add user-facing deprecation messaging and docs updates
  - [x] 6.4.2.5 Verify tests pass and update TDD_EVIDENCE.md with passing evidence

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
  - [x] 7.5.1 `openspec validate marketplace-01-central-module-registry --strict`
  - [x] 7.5.2 Fix any validation errors

## 8. Documentation research and review

- [x] 8.1 Identify affected documentation
  - [x] 8.1.1 Review docs/guides/ for module management docs
  - [x] 8.1.2 Review docs/reference/ for architecture docs
  - [x] 8.1.3 Review README.md for marketplace feature mention

- [x] 8.2 Create new guide: docs/guides/installing-modules.md
  - [x] 8.2.1 Add Jekyll front-matter (layout, title, permalink, description)
  - [x] 8.2.2 Write sections: Installing from Marketplace, Listing Modules, Uninstalling, Upgrading
  - [x] 8.2.3 Include command examples with output
  - [x] 8.2.4 Document offline behavior

- [x] 8.3 Create new guide: docs/guides/module-marketplace.md
  - [x] 8.3.1 Add Jekyll front-matter
  - [x] 8.3.2 Write sections: Marketplace Overview, Official Modules, Security Model, Custom Modules
  - [x] 8.3.3 Link to registry repository
  - [x] 8.3.4 Explain namespace system (specfact/*)

- [x] 8.4 Update docs/reference/architecture.md
  - [x] 8.4.1 Add "Module Marketplace" section
  - [x] 8.4.2 Document multi-location discovery pattern
  - [x] 8.4.3 Document registry client architecture
  - [x] 8.4.4 Include sequence diagram for install workflow

- [x] 8.5 Update sidebar navigation
  - [x] 8.5.1 Update docs/_layouts/default.html
  - [x] 8.5.2 Add "Installing Modules" under Guides
  - [x] 8.5.3 Add "Module Marketplace" under Guides

- [x] 8.6 Verify docs build
  - [x] 8.6.1 Test markdown formatting
  - [x] 8.6.2 Check all links work

## 9. Version and changelog

- [x] 9.1 Bump version
  - [x] 9.1.1 Determine version bump: minor (new feature)
  - [x] 9.1.2 Update pyproject.toml version
  - [x] 9.1.3 Update setup.py version
  - [x] 9.1.4 Update src/__init__.py version
  - [x] 9.1.5 Update src/specfact_cli/__init__.py version
  - [x] 9.1.6 Verify all versions match

- [x] 9.2 Update CHANGELOG.md
  - [x] 9.2.1 Add new section: [X.Y.Z] - YYYY-MM-DD
  - [x] 9.2.2 Add "Added" subsection with marketplace features
  - [x] 9.2.3 Reference GitHub issue if created

## 10. Create PR to dev

- [x] 10.1 Prepare commit
  - [x] 10.1.1 `git add .`
  - [x] 10.1.2 Create commit with conventional message format
  - [x] 10.1.3 Include Co-Authored-By: Claude Sonnet 4.5
  - [x] 10.1.4 `git push -u origin feature/marketplace-01-central-module-registry`

- [x] 10.2 Create PR body
  - [x] 10.2.1 Copy PR template to temp file
  - [x] 10.2.2 Fill in issue reference (if exists)
  - [x] 10.2.3 Add OpenSpec change ID
  - [x] 10.2.4 Describe marketplace infrastructure

- [x] 10.3 Create PR via gh CLI
  - [x] 10.3.1 `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/marketplace-01-central-module-registry --title "feat: Central Module Registry MVP for Official Modules" --body-file <file>`
  - [x] 10.3.2 Capture PR URL

- [x] 10.4 Link to project
  - [x] 10.4.1 `gh project item-add 1 --owner nold-ai --url <PR_URL>`

- [x] 10.5 Verify PR setup
  - [x] 10.5.1 Check PR shows correct base and head
  - [x] 10.5.2 Verify CI checks running
  - [x] 10.5.3 Verify project board shows PR

- [x] 10.6 Cleanup
  - [x] 10.6.1 Remove temp files
