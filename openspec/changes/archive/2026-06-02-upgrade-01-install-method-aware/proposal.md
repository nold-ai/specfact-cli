# Change: Install-method-aware `specfact upgrade`

## Why

Issue #538 reports that `specfact upgrade` assumes pip installation paths/commands, which fails or misleads when the CLI is installed via uv/uvx or other non-pip workflows.

## What Changes

- Extend installation method detection to identify uv-managed environments.
- Use uv-native upgrade commands when uv is detected.
- Preserve existing pip/pipx/uvx behavior.
- Add tests for uv detection and command selection.

## Source Tracking

- **GitHub Issue**: #538
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/538>
