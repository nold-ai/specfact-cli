# Enhanced Analysis Dependencies

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

### 1. pyan3 - Python Call Graph Analysis

**Purpose**: Extract function call graphs from Python code

**Package**: `pyan3>=1.2.0` (in optional-dependencies.enhanced-analysis)

**Usage**: The `graph_analyzer.py` module automatically detects if `pyan3` is available and gracefully falls back if not installed.

**Status**: ✅ **Available** - Install via `pip install -e ".[enhanced-analysis]"`

### 2. Syft - Software Bill of Materials (SBOM)

**Purpose**: Generate comprehensive SBOM of all dependencies (direct and transitive)

**Package**: `syft>=0.9.5` (in optional-dependencies.enhanced-analysis)

**Usage**: Will be integrated in `sbom_generator.py` (pending implementation)

**Status**: ✅ **Available** - Install via `pip install -e ".[enhanced-analysis]"`

### 3. Bearer - Data Flow Analysis

**Purpose**: Track sensitive data flow through codebase for security analysis

**Package**: `bearer>=3.1.0` (in optional-dependencies.enhanced-analysis)

**Note**: Bearer primarily supports Java, Ruby, JS/TS. For Python projects, we may need Python-specific alternatives.

**Status**: ✅ **Available** - Install via `pip install -e ".[enhanced-analysis]"`

## Summary

### Required Python Packages (in pyproject.toml dependencies)

- ✅ `networkx>=3.4.2` - Already configured
- ✅ `graphviz>=0.20.1` - Added to dependencies

### Optional Python Packages (in optional-dependencies.enhanced-analysis)

Install all with: `pip install -e ".[enhanced-analysis]"`

- ✅ `pyan3>=1.2.0` - Python call graph analysis
- ✅ `syft>=0.9.5` - Software Bill of Materials (SBOM) generation
- ✅ `bearer>=3.1.0` - Data flow analysis for security
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
# Install specific packages
pip install pyan3>=1.2.0
pip install syft>=0.9.5
pip install bearer>=3.1.0
pip install graphviz>=0.20.1
```

## Graceful Degradation

All graph analysis features are designed to work gracefully when optional tools are missing:

- **pyan3 missing**: Call graph extraction returns empty (no error)
- **graphviz missing**: Diagram generation skipped (no error)
- **syft missing**: SBOM generation skipped (no error)
- **bearer missing**: Data flow analysis skipped (no error)

The import command will continue to work with whatever tools are available, providing enhanced analysis when tools are present.
