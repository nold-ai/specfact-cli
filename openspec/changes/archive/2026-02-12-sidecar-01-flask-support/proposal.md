# Change: Sidecar — Flask Framework Support

## Why

During validation of Microblog (a Flask application), we discovered that **Flask route extraction is not implemented** in SpecFact CLI's sidecar validation. The framework detector finds Flask imports but returns `PURE_PYTHON`, and there's no `FlaskExtractor` class to extract routes from Flask applications.

**Current State**:

- Framework detector detects Flask but returns `PURE_PYTHON` (see `framework_detector.py:96-97`)
- No `FrameworkType.FLASK` in enum
- No `FlaskExtractor` class in `frameworks/` directory
- `get_extractor()` returns `None` for `PURE_PYTHON` framework type
- Result: **0 routes extracted** from Flask applications

**Impact**:

- Cannot validate Flask applications using sidecar validation
- Microblog validation blocked (Phase B cannot complete)
- Missing support for a major Python web framework

**Solution**: Implement Flask framework support following the same pattern as FastAPI and Django extractors.

## Scope Note (Module Architecture)

This change affects the **sidecar validation module** (`src/specfact_cli/validators/sidecar/` or `modules/sidecar/`). The sidecar module exists as part of the core CLI. If it has been migrated to a module package, the paths below should be updated accordingly — otherwise they remain in the core validators.

The sidecar validation is a **core framework capability**, not a new marketplace module. Flask support is a parity fix that brings Flask to the same level as FastAPI and Django.

## Scope Note (Module Architecture)

This change affects the **sidecar validation module** (`src/specfact_cli/validators/sidecar/` or `modules/sidecar/`). The sidecar module exists as part of the core CLI. If it has been migrated to a module package, the paths below should be updated accordingly — otherwise they remain in the core validators.

The sidecar validation is a **core framework capability**, not a new marketplace module. Flask support is a parity fix that brings Flask to the same level as FastAPI and Django.

## What Changes

- **NEW**: Add `FLASK = "flask"` to `FrameworkType` enum in `src/specfact_cli/validators/sidecar/models.py`
- **NEW**: Create `FlaskExtractor` class in `src/specfact_cli/validators/sidecar/frameworks/flask.py` implementing:
  - `detect()` method: Check for Flask imports and `Flask()` instantiation
  - `extract_routes()` method: Extract routes from `@app.route()` and `@bp.route()` decorators
  - `extract_schemas()` method: Extract request/response schemas (can be enhanced later)
  - Helper methods for AST parsing and path parameter conversion
- **MODIFY**: Update `framework_detector.py` to return `FrameworkType.FLASK` when Flask is detected (instead of `PURE_PYTHON`)
- **MODIFY**: Update `orchestrator.py` `get_extractor()` to return `FlaskExtractor` for Flask framework type
- **MODIFY**: Update `frameworks/__init__.py` to export `FlaskExtractor`
- **NEW**: Create unit tests in `tests/unit/validators/sidecar/frameworks/test_flask.py` with ≥80% coverage

## Capabilities

- **sidecar-validation** (Flask): Flask route extraction (`@app.route()`, `@bp.route()`); `FrameworkType.FLASK` detection; parity with FastAPI and Django extractors.

---

## Source Tracking

### Repository: nold-ai/specfact-cli

- **GitHub Issue**: #102
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/102>
- **Last Synced Status**: proposed
- **Sanitized**: false

---

### Repository: dominikusnold/SpecFact CLI (ADO)

- **ADO Issue**: #125
- **Issue URL**: <https://dev.azure.com/dominikusnold/69b5d0c2-2400-470d-b937-b5205503a679/_workitems/edit/125>
- **Last Synced Status**: proposed
