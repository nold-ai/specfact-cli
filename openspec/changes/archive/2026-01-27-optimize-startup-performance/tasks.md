# Tasks: Optimize Startup Performance

## 1. Create Git Branch

- [x] 1.1 Create feature branch `feature/optimize-startup-performance` from `dev` branch
  - [x] 1.1.1 Ensure we're on dev and up to date: `git checkout dev && git pull origin dev`
  - [x] 1.1.2 Create branch: `git checkout -b feature/optimize-startup-performance`
  - [x] 1.1.3 Verify branch was created: `git branch --show-current`

## 2. Create Metadata Management Module

- [x] 2.1 Create `src/specfact_cli/utils/metadata.py`
  - [x] 2.1.1 Implement `get_metadata_dir()` - Returns `~/.specfact/` path, creates if needed
  - [x] 2.1.2 Implement `get_metadata_file()` - Returns path to `metadata.json`
  - [x] 2.1.3 Implement `get_metadata()` - Reads and returns metadata dict, returns empty dict if file doesn't exist
  - [x] 2.1.4 Implement `update_metadata(**kwargs)` - Updates metadata file with provided key-value pairs
  - [x] 2.1.5 Implement `get_last_checked_version()` - Returns version string from metadata, None if not set
  - [x] 2.1.6 Implement `get_last_version_check_timestamp()` - Returns timestamp from metadata, None if not set
  - [x] 2.1.7 Add error handling for file corruption (graceful fallback to empty dict)
  - [x] 2.1.8 Add type hints and docstrings following project standards

- [x] 2.2 Create tests `tests/unit/utils/test_metadata.py`
  - [x] 2.2.1 Test metadata directory creation
  - [x] 2.2.2 Test metadata file reading/writing
  - [x] 2.2.3 Test version tracking
  - [x] 2.2.4 Test timestamp tracking
  - [x] 2.2.5 Test error handling (corrupted file, permission errors)
  - [x] 2.2.6 Run tests: `hatch test tests/unit/utils/test_metadata.py -v`

## 3. Optimize Startup Checks

- [x] 3.1 Modify `src/specfact_cli/utils/startup_checks.py`
  - [x] 3.1.1 Import metadata module: `from specfact_cli.utils.metadata import get_last_checked_version, get_last_version_check_timestamp, update_metadata, is_version_check_needed`
  - [x] 3.1.2 Modify `print_startup_checks()` to check metadata before running checks:
    - [x] 3.1.2.1 Check if template check should run: Compare current version with `get_last_checked_version()`, only run if different or None
    - [x] 3.1.2.2 Check if version check should run: Compare current time with `get_last_version_check_timestamp()`, only run if >= 24 hours ago or None
    - [x] 3.1.2.3 Update metadata after checks complete: `update_metadata(last_checked_version=__version__, last_version_check_timestamp=datetime.now().isoformat())`
  - [x] 3.1.3 Add `--skip-checks` flag support (for CI/CD environments)
  - [x] 3.1.4 Ensure backward compatibility (first-time users still get checks)

- [x] 3.2 Update tests `tests/unit/utils/test_startup_checks.py`
  - [x] 3.2.1 Test conditional template check execution (skip when version unchanged)
  - [x] 3.2.2 Test conditional version check execution (skip when < 24 hours)
  - [x] 3.2.3 Test metadata updates after checks
  - [x] 3.2.4 Test first-time user behavior (no metadata file)
  - [x] 3.2.5 Run tests: `hatch test tests/unit/utils/test_startup_checks.py -v`

## 4. Create Update Command

- [x] 4.1 Create `src/specfact_cli/commands/update.py`
  - [x] 4.1.1 Implement installation method detection:
    - [x] 4.1.1.1 Check `pip show specfact-cli` location
    - [x] 4.1.1.2 Check `uvx` usage patterns
    - [x] 4.1.1.3 Check `pipx` installation paths
    - [x] 4.1.1.4 Return detected method or None
  - [x] 4.1.2 Implement `check_update()` - Check PyPI for latest version, return update info (uses existing `check_pypi_version()`)
  - [x] 4.1.3 Implement `install_update(method)` - Install update using appropriate method with user confirmation
  - [x] 4.1.4 Create Typer command `update` with options:
    - [x] 4.1.4.1 `--check-only` - Only check, don't install
    - [x] 4.1.4.2 `--yes` - Skip confirmation prompt
  - [x] 4.1.5 Add rich console output for update status
  - [x] 4.1.6 Add error handling for installation failures

- [x] 4.2 Create tests `tests/unit/commands/test_update.py`
  - [x] 4.2.1 Test installation method detection (mocked)
  - [x] 4.2.2 Test update checking (mocked PyPI API)
  - [x] 4.2.3 Test update installation (mocked subprocess)
  - [x] 4.2.4 Test error handling
  - [x] 4.2.5 Run tests: `hatch test tests/unit/commands/test_update.py -v`

- [x] 4.3 Register update command in `src/specfact_cli/cli.py`
  - [x] 4.3.1 Import update module: `from specfact_cli.commands import update`
  - [x] 4.3.2 Register command: `app.add_typer(update.app, name="update")`
  - [x] 4.3.3 Verify command appears in help: `specfact --help`

## 5. Performance Profiling and Optimization

- [x] 5.1 Profile startup time
  - [x] 5.1.1 Use `python -X importtime` to profile imports (done in CHANGE_VALIDATION.md)
  - [x] 5.1.2 Use `cProfile` or `py-spy` to profile startup (done in CHANGE_VALIDATION.md)
  - [x] 5.1.3 Measure time for each startup operation (done in CHANGE_VALIDATION.md)
  - [x] 5.1.4 Identify operations taking > 100ms (startup checks identified as main bottleneck)

- [x] 5.2 Optimize identified bottlenecks
  - [x] 5.2.1 Lazy load heavy imports where possible (startup checks now conditional)
  - [x] 5.2.2 Optimize file system operations (template checks only after version change)
  - [x] 5.2.3 Optimize configuration loading (no changes needed)
  - [x] 5.2.4 Optimize progress bar initialization (no changes needed)

- [x] 5.3 Create integration tests `tests/integration/test_startup_performance.py`
  - [x] 5.3.1 Test startup time < 2 seconds
  - [x] 5.3.2 Test checks are skipped when appropriate
  - [x] 5.3.3 Test checks run when needed (version change, 24h elapsed)
  - [x] 5.3.4 Run tests: `hatch test tests/integration/test_startup_performance.py -v`

## 6. Quality Gates

- [x] 6.1 Run formatting: `hatch run format`
- [x] 6.2 Run type checking: `hatch run type-check`
- [x] 6.3 Run contract tests: `hatch run contract-test`
- [x] 6.4 Run full test suite: `hatch test --cover -v`
- [x] 6.5 Verify all tests pass and coverage >= 80%
- [x] 6.6 Fix any issues and repeat until all checks pass

## 7. Create Pull Request

- [x] 7.1 Prepare changes for commit
  - [x] 7.1.1 Ensure all changes are committed: `git add .`
  - [x] 7.1.2 Commit with conventional message: `git commit -m "perf: optimize startup performance with metadata tracking and update command"`
  - [x] 7.1.3 Push to remote: `git push origin feature/optimize-startup-performance`

- [x] 7.2 Create PR body from template
  - [x] 7.2.1 Create PR body file: `PR_BODY_FILE="/tmp/pr-body-optimize-startup-performance.md"`
  - [x] 7.2.2 Execute Python script to read template and fill in values (see workflow for script)
  - [x] 7.2.3 Verify PR body file was created: `cat "$PR_BODY_FILE"`

- [x] 7.3 Create Pull Request using gh CLI
  - [x] 7.3.1 Create PR: `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/optimize-startup-performance --title "perf: optimize startup performance" --body-file "$PR_BODY_FILE"`
  - [x] 7.3.2 Verify PR was created and capture PR number (PR #142)
  - [x] 7.3.3 Link PR to project: `gh project item-add 1 --owner nold-ai --url "https://github.com/nold-ai/specfact-cli/pull/<PR_NUMBER>"`
  - [x] 7.3.4 Update project status for PR to "In Progress"
  - [x] 7.3.5 Verify project link and Development link
  - [x] 7.3.6 Cleanup PR body file: `rm /tmp/pr-body-optimize-startup-performance.md`
