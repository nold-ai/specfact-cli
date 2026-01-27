# Change: Optimize Startup Performance

## Why

SpecFact CLI startup is currently slow (several seconds delay) due to automated checks for IDE templates and version updates running on every invocation. This degrades user experience and makes the CLI feel unresponsive. Users expect CLI tools to respond within 1-2 seconds maximum.

The current implementation:

- Checks IDE templates on every startup (file system operations, hash comparisons)
- Checks PyPI for version updates on every startup (network requests)
- Both checks block startup until completion

This change optimizes startup performance by:

1. Only checking IDE templates after version updates are detected (via metadata tracking)
2. Checking PyPI for updates only once per day (not every startup)
3. Adding a dedicated `update` command for manual update checking and installation
4. Profiling and optimizing any other startup blockers

## What Changes

- **NEW**: `src/specfact_cli/utils/metadata.py` - Metadata management module for tracking version and check timestamps in `~/.specfact/metadata.json`
- **MODIFY**: `src/specfact_cli/utils/startup_checks.py` - Optimize `print_startup_checks()` to check metadata before running checks, add conditional execution logic
- **NEW**: `src/specfact_cli/commands/update.py` - New `specfact update` command for manual update checking and installation
- **MODIFY**: `src/specfact_cli/cli.py` - Register update command, ensure startup checks use optimized logic
- **NEW**: `tests/unit/utils/test_metadata.py` - Tests for metadata management
- **MODIFY**: `tests/unit/utils/test_startup_checks.py` - Update tests for conditional check execution
- **NEW**: `tests/unit/commands/test_update.py` - Tests for update command
- **NEW**: `tests/integration/test_startup_performance.py` - Integration tests for startup performance

## Impact

**Affected Specs**: None (performance optimization, no spec changes)

**Affected Code**:

- `src/specfact_cli/utils/startup_checks.py` - Core optimization logic
- `src/specfact_cli/cli.py` - Command registration
- New modules: `metadata.py`, `update.py`

**Integration Points**:

- Metadata file: `~/.specfact/metadata.json` (user's home directory)
- PyPI API: Version checking (now rate-limited to once per day)
- Installation detection: pip, uvx, pipx detection for update command

**Breaking Changes**: None (backward compatible)

**Performance Impact**:

- Startup time: Reduced from several seconds to < 1-2 seconds
- Network requests: Reduced from every startup to once per day
- File system operations: Reduced from every startup to only after version changes

## Source Tracking

- **GitHub Issue**: #140
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/140>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
