# Sidecar Dependency Installation Guide

**Date**: 2026-01-12  
**Status**: ✅ **COMPLETE**  
**Purpose**: Documentation for sidecar dependency installation process

---

## Overview

Sidecar validation creates an isolated virtual environment (venv) and installs all required dependencies to ensure validation tools can execute application code correctly.

## Automatic Installation Process

### Step 1: Venv Creation

Sidecar validation automatically creates an isolated venv at `.specfact/venv/`:

```bash
# Venv is created automatically during sidecar initialization
specfact validate sidecar init <bundle-name> <repo-path>
```

**Venv Location**: `<repo-path>/.specfact/venv/`

**Venv Configuration**:
- Uses `symlinks=False` to avoid libpython shared library issues
- Includes pip by default
- Validates venv Python can actually run (detects broken venvs)

### Step 2: Framework Dependencies

Framework-specific dependencies are installed automatically:

| Framework | Dependencies |
|-----------|-------------|
| **Flask** | `flask`, `werkzeug` |
| **FastAPI** | `fastapi`, `uvicorn`, `pydantic` |
| **Django** | `django` |
| **DRF** | `django`, `djangorestframework` |
| **All** | `crosshair-tool`, `beartype`, `icontract` |

**Installation Order**:
1. Framework dependencies (Flask, FastAPI, etc.)
2. CrossHair tool (for contract validation)
3. Harness dependencies (beartype, icontract)

### Step 3: Project Dependencies

Project dependencies are detected and installed based on environment manager:

#### Pip (requirements.txt)

```bash
# Automatically detected and installed
.specfact/venv/bin/pip install -r requirements.txt
```

#### Hatch (pyproject.toml)

```bash
# Installs in editable mode to get all dependencies
.specfact/venv/bin/pip install -e .
# Falls back to requirements.txt if editable install fails
```

#### Poetry (pyproject.toml + poetry.lock)

```bash
# Exports requirements and installs
poetry export --format requirements.txt --output - | \
  .specfact/venv/bin/pip install -r -
```

#### UV (pyproject.toml or requirements.txt)

```bash
# Uses uv pip install
uv pip install --system -r requirements.txt
# Or: uv pip install --system -e .
```

### Step 4: Environment Configuration

After installation, the sidecar configuration is updated:

- **PYTHONPATH**: Set to include venv site-packages
- **python_cmd**: Set to venv Python executable
- **Framework Detection**: Framework type is detected and stored

## Manual Installation

If automatic installation fails, you can manually install dependencies:

### Step 1: Create Venv

```bash
cd /path/to/repo
python3 -m venv .specfact/venv --copies
```

**Note**: Use `--copies` flag to avoid libpython shared library issues.

### Step 2: Install Framework Dependencies

```bash
# Flask
.specfact/venv/bin/pip install flask werkzeug crosshair-tool beartype icontract

# FastAPI
.specfact/venv/bin/pip install fastapi uvicorn pydantic crosshair-tool beartype icontract

# Django
.specfact/venv/bin/pip install django crosshair-tool beartype icontract
```

### Step 3: Install Project Dependencies

```bash
# From requirements.txt
.specfact/venv/bin/pip install -r requirements.txt

# Or from pyproject.toml (editable)
.specfact/venv/bin/pip install -e .
```

### Step 4: Verify Installation

```bash
# Test Flask import
.specfact/venv/bin/python -c "import flask; print(f'Flask {flask.__version__}')"

# Test CrossHair
.specfact/venv/bin/python -m crosshair --version

# Test harness dependencies
.specfact/venv/bin/python -c "import beartype, icontract; print('OK')"
```

## Troubleshooting

### Venv Creation Fails

**Issue**: Venv creation fails with permission errors

**Solutions**:
- Check directory permissions
- Ensure sufficient disk space
- Try creating venv in a different location

### Libpython Error

**Issue**: `error while loading shared libraries: libpython3.12.so.1.0: cannot open shared object file`

**Cause**: Venv was created with Python 3.12, but system Python is 3.11 (version mismatch)

**Solution**: The code automatically detects and recreates broken venvs. If manual fix is needed:

```bash
# Delete broken venv
rm -rf .specfact/venv

# Recreate with system Python
python3 -m venv .specfact/venv --copies

# Re-run validation (will reinstall dependencies)
specfact validate sidecar run <bundle-name> <repo-path>
```

### Dependencies Not Installing

**Issue**: Dependencies fail to install from requirements.txt

**Solutions**:
- Check requirements.txt format
- Verify network connectivity
- Check for conflicting dependencies
- Try installing manually to see error messages

### CrossHair Not Found in Venv

**Issue**: CrossHair not available in venv

**Solutions**:
- Verify CrossHair is in framework dependencies
- Check installation logs for errors
- Manually install: `.specfact/venv/bin/pip install crosshair-tool`

### Flask Import Fails

**Issue**: `ModuleNotFoundError: No module named 'flask'` during validation

**Solutions**:
- Verify Flask is installed: `.specfact/venv/bin/pip list | grep -i flask`
- Check PYTHONPATH includes venv site-packages
- Reinstall Flask: `.specfact/venv/bin/pip install flask`

## Environment Manager Detection

Sidecar validation automatically detects the project's dependency manager:

### Detection Order

1. **Hatch**: Checks for `pyproject.toml` with `[build-system]` using `hatchling`
2. **Poetry**: Checks for `poetry.lock` or `pyproject.toml` with `[tool.poetry]`
3. **UV**: Checks for `uv.lock` or `pyproject.toml` with `[project]` dependencies
4. **Pip**: Falls back to `requirements.txt` if no other manager detected

### Detection Logic

```python
# Detection happens in specfact_cli/utils/env_manager.py
env_info = detect_env_manager(repo_path)
# Returns: EnvInfo(manager=EnvManager.HATCH, command_prefix="hatch run")
```

## Venv Validation

The sidecar validation automatically validates venv health:

### Validation Checks

1. **Venv Exists**: Checks if `.specfact/venv/` directory exists
2. **Python Executable**: Verifies venv Python exists
3. **Python Can Run**: Tests if venv Python can execute (catches libpython errors)
4. **Recreation**: Automatically recreates broken venvs

### Validation Code

```python
# In dependency_installer.py
if venv_path.exists():
    venv_python = _get_venv_python(venv_path)
    if venv_python and venv_python.exists():
        # Test if Python can actually run
        result = subprocess.run(
            [str(venv_python), "--version"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0:
            # Venv works, skip recreation
            return True
    # Venv exists but is broken, remove it
    shutil.rmtree(venv_path)
```

## Best Practices

### Venv Management

1. **Isolated Environments**: Always use isolated venv (`.specfact/venv/`)
2. **Version Matching**: Ensure venv Python version matches system Python
3. **Regular Cleanup**: Delete and recreate venv if issues occur

### Dependency Management

1. **Pin Versions**: Use `requirements.txt` with pinned versions for reproducibility
2. **Separate Dependencies**: Keep framework and project dependencies separate
3. **Test Installation**: Verify dependencies install correctly before validation

### Error Handling

1. **Check Logs**: Review installation logs for errors
2. **Manual Verification**: Test imports manually if validation fails
3. **Recreate Venv**: Delete and recreate venv if persistent issues

## Related Documentation

- [Flask Sidecar Usage](./FLASK-SIDECAR-USAGE.md) - Flask-specific guide
- [Contract Strengthening Guidelines](./CONTRACT-STRENGTHENING.md) - Contract design
- [Sidecar Execution Guide](./SIDECAR-EXECUTION-GUIDE.md) - Execution workflow

---

**Rulesets Applied**: SpecFact CLI rules, Python GitHub rules, Clean Code principles  
**AI Provider**: Claude (Sonnet 4.5)
