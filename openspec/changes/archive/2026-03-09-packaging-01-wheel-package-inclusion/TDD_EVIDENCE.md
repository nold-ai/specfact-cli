# TDD Evidence

## Failing Evidence

### 2026-03-06 installed artifact inspection

Commands:

```bash
python - <<'PY'
import site, pathlib
root = pathlib.Path(site.getusersitepackages()) / 'specfact_cli'
print('cli.py exists:', (root / 'cli.py').exists())
print('__init__.py exists:', (root / '__init__.py').exists())
PY
```

Observed failure summary:
- installed `specfact_cli` package contained only `modules/` and `resources/`
- `specfact_cli/cli.py` missing from installed `0.40.0` wheel payload
- console script `specfact-cli` failed with `ModuleNotFoundError: No module named 'specfact_cli.cli'`

### 2026-03-06 pre-fix regression test

Command:

```bash
HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/unit/packaging/test_core_package_includes.py -q
```

Observed failure summary:
- `test_pyproject_wheel_explicitly_maps_src_package_root` failed because wheel config lacked explicit `only-include` / `sources` mapping for `src/specfact_cli`

## Passing Evidence

### 2026-03-06 post-fix regression test

Command:

```bash
HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch run pytest tests/unit/packaging/test_core_package_includes.py -q
```

Result:
- `6 passed`

### 2026-03-06 built wheel artifact verification

Commands:

```bash
HATCH_DATA_DIR=/tmp/hatch-data HATCH_CACHE_DIR=/tmp/hatch-cache VIRTUALENV_OVERRIDE_APP_DATA=/tmp/virtualenv-appdata hatch build -t wheel
python - <<'PY'
import zipfile
from pathlib import Path
wheel = Path('dist/specfact_cli-0.40.1-py3-none-any.whl')
with zipfile.ZipFile(wheel) as zf:
    assert 'specfact_cli/__init__.py' in zf.namelist()
    assert 'specfact_cli/cli.py' in zf.namelist()
    print(zf.read('specfact_cli-0.40.0.dist-info/entry_points.txt').decode('utf-8'))
PY
python - <<'PY'
import sys
sys.path.insert(0, 'dist/specfact_cli-0.40.1-py3-none-any.whl')
import specfact_cli.cli as cli
print(cli.__file__)
print(hasattr(cli, 'cli_main'))
PY
```

Result summary:
- built wheel contains `specfact_cli/__init__.py`
- built wheel contains `specfact_cli/cli.py`
- entry points include both `specfact` and `specfact-cli` targeting `specfact_cli.cli:cli_main`
- importing `specfact_cli.cli` from the wheel succeeds

### 2026-03-06 clean install command verification

Commands:

```bash
python -m venv /tmp/specfact-cli-wheel-verify --system-site-packages
/tmp/specfact-cli-wheel-verify/bin/pip install --force-reinstall --no-deps dist/specfact_cli-0.40.1-py3-none-any.whl
/tmp/specfact-cli-wheel-verify/bin/specfact -v
/tmp/specfact-cli-wheel-verify/bin/specfact-cli -v
```

Result summary:
- installed wheel exposes `specfact`
- installed wheel exposes `specfact-cli`
- both commands return `SpecFact CLI version 0.40.1`
