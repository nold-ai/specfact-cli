# packaging-01-wheel-package-inclusion

## Summary

Fix the released `specfact-cli` wheel so a plain `pip install specfact-cli` installs the core `specfact_cli` Python package, including `specfact_cli.cli`, and both declared console scripts can start successfully.

## Problem

The published `0.40.0` artifact installs console script wrappers but the wheel payload omits the actual `specfact_cli` package code. The installed site-packages directory contains only force-included `modules/` and `resources/`, causing:

- `specfact` missing or unusable after install
- `specfact-cli` wrapper failing with `ModuleNotFoundError: No module named 'specfact_cli.cli'`

## Scope

- Correct wheel packaging configuration for core package inclusion
- Add regression coverage that inspects the built wheel contents
- Verify the built wheel contains `specfact_cli/cli.py` and both console scripts resolve to `specfact_cli.cli:cli_main`

## Out of Scope

- Broader release automation changes
- Marketplace/module bundle behavior changes
