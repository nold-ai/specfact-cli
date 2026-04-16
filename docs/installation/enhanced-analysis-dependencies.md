---
layout: default
title: Enhanced Analysis Dependencies
permalink: /installation/enhanced-analysis-dependencies/
---

## Python Package Dependencies

### Already in `pyproject.toml`

✅ **NetworkX** (`networkx>=3.4.2`) - Already in main dependencies

- Used for: Dependency graph building and analysis
- Status: ✅ Already configured

✅ **Graphviz** (`graphviz>=0.20.1`) - Added to main dependencies and optional-dependencies

- Used for: Architecture diagram generation
- **Important**: Requires system Graphviz to be installed:
  - Debian/Ubuntu: `apt-get install graphviz`
  - macOS: `brew install graphviz`
  - The Python `graphviz` package is a wrapper that requires the system package

### Quick Setup

```bash
# Install Python dependencies
pip install -e ".[enhanced-analysis]"

# Install system dependencies (required for graphviz)
# Debian/Ubuntu:
sudo apt-get install graphviz

# macOS:
brew install graphviz
```

## Optional Python Packages

These packages are available via pip and can be installed with:

```bash
pip install -e ".[enhanced-analysis]"
# or
hatch install -e ".[enhanced-analysis]"
```

### 1. pycg - Python Call Graph Analysis

**Purpose**: Extract function call graphs from Python code

**Package**: `pycg>=0.0.7` (in optional-dependencies.enhanced-analysis)

**License**: MIT

**Usage**: The `graph_analyzer.py` module automatically detects if `pycg` is available
and gracefully falls back to an empty call graph if not installed.

**Status**: ✅ **Available** - Install via `pip install -e ".[enhanced-analysis]"` or `pip install pycg`

> **Migration note**: `pyan3` (GPL-2.0) was replaced by `pycg` (MIT) to comply with the
> Apache-2.0 license of specfact-cli. The CLI changed from DOT format to JSON;
> no user-facing behaviour change.

### 2. Bandit - SAST Security Scanner

**Purpose**: Static application security testing to detect common security issues in Python code

**Package**: `bandit>=1.7.0` (in optional-dependencies.dev)

**License**: MIT (Apache-2.0 umbrella — Apache Software Foundation project)

**Usage**: Run with `hatch run bandit-scan` or `bandit -r src/ -ll`

**Status**: ✅ **Available** in dev extras

> **Migration note**: `bearer>=3.1.0` was removed — the PyPI `bearer` package is an HTTP
> auth SaaS client, not the Bearer security scanner CLI. `bandit` is the correct Python SAST tool.

## Summary

### Required Python Packages (in pyproject.toml dependencies)

- ✅ `networkx>=3.4.2` - Already configured
- ✅ `graphviz>=0.20.1` - Added to dependencies

### Optional Python Packages (in optional-dependencies.enhanced-analysis)

Install all with: `pip install -e ".[enhanced-analysis]"`

- ✅ `pycg>=0.0.7` - Python call graph analysis (MIT; replaces GPL pyan3)
- ✅ `graphviz>=0.20.1` - Graph visualization (also in main dependencies)

### System Dependencies (Required for graphviz)

- ⏳ `graphviz` (system package) - `apt-get install graphviz` or `brew install graphviz`
  - The Python `graphviz` package is a wrapper that requires the system package

## Installation Guide

### Quick Install (All Enhanced Analysis Tools)

```bash
# Install Python dependencies
pip install -e ".[enhanced-analysis]"

# Install system Graphviz (required for graphviz Python package)
# Debian/Ubuntu:
sudo apt-get install graphviz

# macOS:
brew install graphviz
```

### Individual Package Installation

```bash
pip install "pycg>=0.0.7"
pip install "graphviz>=0.20.1"
```

## Graceful Degradation

All graph analysis features are designed to work gracefully when optional tools are missing:

- **pycg missing**: Call graph extraction returns empty (no error)
- **graphviz missing**: Diagram generation skipped (no error)

The import command will continue to work with whatever tools are available, providing enhanced analysis when tools are present.
